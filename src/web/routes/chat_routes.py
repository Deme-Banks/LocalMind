"""
Chat routes - Handle chat and conversation endpoints
"""

from typing import Dict, Any, Tuple
from flask import Flask, request, jsonify, Response, stream_with_context
import logging
import time
import json
import requests

from .base import error_response, success_response, get_project_root

logger = logging.getLogger(__name__)


def setup_chat_routes(app: Flask, server_instance):
    """
    Setup chat-related routes
    
    Args:
        app: Flask application
        server_instance: WebServer instance (for access to managers)
    """
    
    @app.route("/api/chat", methods=["POST"])
    def api_chat():
        """Chat with a model"""
        start_time = time.time()
        
        # Rate limiting
        client_ip = request.remote_addr or "unknown"
        is_allowed, error_msg = server_instance.rate_limiter.is_allowed(client_ip)
        # Audit log
        from ...core.audit_logger import AuditEventType
        
        if not is_allowed:
            server_instance.audit_logger.log(
                AuditEventType.SECURITY_VIOLATION,
                ip_address=client_ip,
                details={"reason": "rate_limit_exceeded"},
                success=False
            )
            return jsonify(error_response(error_msg, status_code=429, error_type="rate_limit")), 429
        server_instance.audit_logger.log(
            AuditEventType.CONVERSATION_ACCESS,
            ip_address=client_ip,
            details={"action": "chat_request"}
        )
        
        try:
            data = request.get_json()
            prompt = data.get("prompt")
            model = data.get("model")
            system_prompt = data.get("system_prompt")
            temperature = data.get("temperature", 0.7)
            stream = data.get("stream", False)
            conv_id = data.get("conversation_id")
            
            # Get unrestricted mode setting
            config = server_instance.config_manager.get_config()
            request_unrestricted = data.get("unrestricted_mode")
            if request_unrestricted is not None:
                unrestricted_mode = request_unrestricted
                disable_safety_filters = request_unrestricted
            else:
                unrestricted_mode = getattr(config, 'unrestricted_mode', True)
                disable_safety_filters = getattr(config, 'disable_safety_filters', True)
            
            if not prompt:
                return jsonify(error_response("Prompt required", status_code=400, error_type="validation")), 400
            
            # Create conversation if not provided
            if not conv_id:
                conv_id = server_instance.conversation_manager.create_conversation(model=model)
            
            # Load conversation history
            conversation = server_instance.conversation_manager.get_conversation(conv_id)
            conversation_messages = []
            if conversation:
                conversation_messages = conversation.get("messages", [])
            
            # Convert to Message objects
            from ...core.context_manager import Message
            history_messages = server_instance.context_manager.get_conversation_history(conversation_messages)
            
            # Add current user message
            current_user_message = Message(role="user", content=prompt)
            history_messages.append(current_user_message)
            
            # Try module processing
            module_response = None
            preferred_module = data.get("module")
            
            try:
                module_response = server_instance.module_loader.process_prompt(
                    prompt,
                    model_loader=server_instance.model_loader,
                    context={
                        "model": model,
                        "messages": conversation_messages,
                        "conversation_id": conv_id
                    },
                    preferred_module=preferred_module,
                    model=model,
                    temperature=temperature
                )
            except Exception as e:
                logger.warning(f"Module processing failed: {e}")
                module_response = None
            
            # If module handled it, use module response
            if module_response and module_response.success and module_response.content:
                server_instance.conversation_manager.save_message(
                    conv_id,
                    "assistant",
                    module_response.content,
                    metadata={
                        "model": model,
                        "temperature": temperature,
                        "module": module_response.metadata.get("module")
                    }
                )
                
                return jsonify(success_response({
                    "response": module_response.content,
                    "model": model,
                    "metadata": {
                        **module_response.metadata,
                        "module_used": True
                    },
                    "conversation_id": conv_id
                }))
            
            # Build context
            processed_messages, context_metadata = server_instance.context_manager.build_context(
                history_messages,
                model=model,
                system_prompt=system_prompt
            )
            
            # Determine backend type
            backend_name, backend_type = server_instance._get_backend_for_model(model)
            if not backend_type:
                backend_type = "ollama"
            
            # Check local-only mode
            if backend_name:
                is_allowed, error_msg = server_instance.local_only_mode.is_allowed(backend_name)
                if not is_allowed:
                    from ...core.audit_logger import AuditEventType
                    server_instance.audit_logger.log(
                        AuditEventType.SECURITY_VIOLATION,
                        ip_address=client_ip,
                        details={"reason": "local_only_mode_violation", "backend": backend_name},
                        success=False
                    )
                    return jsonify(error_response(error_msg, status_code=403, error_type="local_only_mode")), 403
            
            # Format messages for backend
            if backend_type in ["openai", "anthropic", "google", "mistral-ai", "cohere", "groq"]:
                formatted_messages = server_instance.context_manager.format_messages_for_backend(
                    processed_messages, backend_type
                )
                prompt_text = "\n".join([f"{m['role']}: {m['content']}" for m in formatted_messages if m.get('role') != 'system'])
            else:
                prompt_text = server_instance.context_manager.format_messages_for_backend(
                    processed_messages, "ollama"
                )
            
            # Save user message
            server_instance.conversation_manager.save_message(
                conv_id,
                "user",
                prompt,
                metadata={"model": model, "temperature": temperature, "system_prompt": system_prompt}
            )
            
            # Add to shared context for video generation
            if hasattr(server_instance, 'shared_context'):
                server_instance.shared_context.add_chat_prompt(
                    prompt=prompt,
                    conversation_id=conv_id,
                    metadata={"model": model}
                )
            
            # Trigger webhook
            from ...core.webhook_manager import WebhookEvent
            server_instance.webhook_manager.trigger_webhook(
                    WebhookEvent.CHAT_MESSAGE,
                    {
                        "conversation_id": conv_id,
                        "role": "user",
                        "model": model,
                        "prompt": prompt
                    }
                )
            
            if stream:
                # Streaming response
                def generate():
                    try:
                        # Get the appropriate backend
                        backend = server_instance.model_loader.backends.get(backend_name)
                        if not backend:
                            yield f"data: {json.dumps({'error': f'Backend {backend_name} not available'})}\n\n"
                            return
                        
                        # For Ollama, use direct API call
                        if backend_type == "ollama":
                            url = f"{backend.base_url}/api/generate"
                            payload = {
                                "model": model or server_instance.config_manager.get_config().default_model,
                                "prompt": prompt_text,
                                "stream": True,
                                "options": {"temperature": temperature}
                            }
                            
                            final_system_prompt = system_prompt
                            for msg in processed_messages:
                                if msg.role == "system" and "[Previous conversation summary:" in msg.content:
                                    if final_system_prompt:
                                        final_system_prompt = f"{final_system_prompt}\n\n{msg.content}"
                                    else:
                                        final_system_prompt = msg.content
                            
                            if final_system_prompt:
                                payload["system"] = final_system_prompt
                            
                            full_response = ""
                            try:
                                with requests.post(url, json=payload, stream=True, timeout=getattr(backend, 'timeout', 300)) as r:
                                    r.raise_for_status()
                                    for line in r.iter_lines():
                                        if line:
                                            try:
                                                data = json.loads(line)
                                                if "response" in data:
                                                    chunk = data['response']
                                                    full_response += chunk
                                                    yield f"data: {json.dumps({'chunk': chunk})}\n\n"
                                                if data.get("done", False):
                                                    # Save assistant message
                                                    server_instance.conversation_manager.save_message(
                                                        conv_id,
                                                        "assistant",
                                                        full_response,
                                                        metadata={"model": model, "temperature": temperature}
                                                    )
                                                    
                                                    # Trigger webhook
                                                    from ...core.webhook_manager import WebhookEvent
                                                    server_instance.webhook_manager.trigger_webhook(
                                                        WebhookEvent.CHAT_COMPLETE,
                                                        {
                                                            "conversation_id": conv_id,
                                                            "model": model,
                                                            "prompt": prompt,
                                                            "response_length": len(full_response)
                                                        }
                                                    )
                                                    
                                                    yield f"data: {json.dumps({'done': True, 'conversation_id': conv_id})}\n\n"
                                                    break
                                            except (json.JSONDecodeError, UnicodeDecodeError):
                                                continue
                            except Exception as e:
                                logger.error(f"Ollama streaming error: {e}")
                                yield f"data: {json.dumps({'error': str(e)})}\n\n"
                        else:
                            # For other backends, use the backend's generate method with streaming
                            # Fallback to non-streaming for now if backend doesn't support streaming
                            logger.warning(f"Streaming not fully supported for {backend_type}, using non-streaming")
                            response = backend.generate(
                                prompt=prompt_text,
                                model=model,
                                system_prompt=system_prompt,
                                temperature=temperature,
                                disable_safety_filters=disable_safety_filters
                            )
                            
                            # Simulate streaming by sending chunks
                            text = response.text
                            chunk_size = 10
                            for i in range(0, len(text), chunk_size):
                                chunk = text[i:i+chunk_size]
                                yield f"data: {json.dumps({'chunk': chunk})}\n\n"
                            
                            # Save assistant message
                            server_instance.conversation_manager.save_message(
                                conv_id,
                                "assistant",
                                text,
                                metadata={"model": model, "temperature": temperature}
                            )
                            
                            # Trigger webhook
                            from ...core.webhook_manager import WebhookEvent
                            server_instance.webhook_manager.trigger_webhook(
                                WebhookEvent.CHAT_COMPLETE,
                                {
                                    "conversation_id": conv_id,
                                    "model": model,
                                    "prompt": prompt,
                                    "response_length": len(text)
                                }
                            )
                            
                            yield f"data: {json.dumps({'done': True, 'conversation_id': conv_id})}\n\n"
                    except Exception as e:
                        logger.error(f"Streaming error: {e}", exc_info=True)
                        yield f"data: {json.dumps({'error': str(e)})}\n\n"
                
                return Response(stream_with_context(generate()), mimetype='text/event-stream')
            else:
                # Non-streaming response
                backend = server_instance.model_loader.backends.get(backend_name)
                if not backend:
                    return jsonify(error_response(f"Backend '{backend_name}' not available", status_code=404)), 404
                
                response = backend.generate(
                    prompt=prompt_text,
                    model=model,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    disable_safety_filters=disable_safety_filters
                )
                
                # Save assistant message
                server_instance.conversation_manager.save_message(
                    conv_id,
                    "assistant",
                    response.text,
                    metadata={"model": model, "temperature": temperature}
                )
                
                # Trigger webhook
                server_instance.webhook_manager.trigger_webhook(
                    WebhookEvent.CHAT_COMPLETE,
                    {
                        "conversation_id": conv_id,
                        "model": model,
                        "prompt": prompt,
                        "response_length": len(response.text)
                    }
                )
                
                # Track usage
                response_time = time.time() - start_time
                metadata = response.metadata or {}
                prompt_tokens = metadata.get("prompt_tokens", 0)
                completion_tokens = metadata.get("completion_tokens", 0)
                
                server_instance.usage_tracker.record_usage(
                    backend=backend_name or "unknown",
                    model=model,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    response_time=response_time,
                    success=True
                )
                
                elapsed_time = time.time() - start_time
                response_length = len(response.text)
                tokens_per_second = response_length / elapsed_time if elapsed_time > 0 else 0
                
                response_metadata = response.metadata.copy()
                response_metadata.update(context_metadata)
                response_metadata.update({
                    "response_time": round(elapsed_time, 2),
                    "response_length": response_length,
                    "tokens_per_second": round(tokens_per_second, 2)
                })
                
                return jsonify(success_response({
                    "response": response.text,
                    "model": response.model,
                    "metadata": response_metadata,
                    "conversation_id": conv_id
                }))
        
        except Exception as e:
            logger.error(f"Error in chat: {e}", exc_info=True)
            
            response_time = time.time() - start_time
            backend_name, _ = server_instance._get_backend_for_model(model)
            server_instance.usage_tracker.record_usage(
                backend=backend_name or "unknown",
                model=model or "unknown",
                prompt_tokens=0,
                completion_tokens=0,
                response_time=response_time,
                success=False,
                error=str(e)
            )
            
            return jsonify(error_response(str(e), status_code=500)), 500

