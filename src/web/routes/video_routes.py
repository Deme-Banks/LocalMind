"""
Video routes - Handle video generation endpoints
"""

from typing import Dict, Any
from flask import Flask, request, jsonify
import logging

from .base import error_response, success_response

logger = logging.getLogger(__name__)


def setup_video_routes(app: Flask, server_instance):
    """
    Setup video-related routes
    
    Args:
        app: Flask application
        server_instance: WebServer instance
    """
    
    @app.route("/api/video/models", methods=["GET"])
    def api_list_video_models():
        """List all available video models"""
        try:
            if not hasattr(server_instance, 'video_loader'):
                return jsonify(error_response("Video loader not initialized", status_code=500)), 500
            
            backends = server_instance.video_loader.list_backends()
            all_models = server_instance.video_loader.list_all_models()
            
            # Format response
            models_list = []
            for backend_name, models in all_models.items():
                backend = server_instance.video_loader.get_backend(backend_name)
                backend_info = backend.get_backend_info() if backend else {}
                
                for model in models:
                    models_list.append({
                        "id": f"{backend_name}:{model}",
                        "backend": backend_name,
                        "model": model,
                        "display_name": f"{backend_name.capitalize()} - {model}",
                        "backend_info": backend_info
                    })
            
            return jsonify(success_response({
                "backends": backends,
                "models": models_list,
                "models_by_backend": all_models
            }))
        except Exception as e:
            logger.error(f"Error listing video models: {e}", exc_info=True)
            return jsonify(error_response(str(e), status_code=500)), 500
    
    @app.route("/api/video/generate", methods=["POST"])
    def api_generate_video():
        """Generate video from text prompt"""
        try:
            if not hasattr(server_instance, 'video_loader'):
                return jsonify(error_response("Video loader not initialized", status_code=500)), 500
            
            data = request.get_json() or {}
            prompt = data.get("prompt")
            model_id = data.get("model")  # Format: "backend:model" or just "model"
            duration = data.get("duration")
            aspect_ratio = data.get("aspect_ratio")
            resolution = data.get("resolution")
            
            if not prompt:
                return jsonify(error_response("Prompt required", status_code=400, error_type="validation")), 400
            
            if not model_id:
                return jsonify(error_response("Model required", status_code=400, error_type="validation")), 400
            
            # Parse model_id (format: "backend:model" or just "model")
            if ":" in model_id:
                backend_name, model = model_id.split(":", 1)
            else:
                # Try to find model in any backend
                all_models = server_instance.video_loader.list_all_models()
                backend_name = None
                model = model_id
                for bname, models in all_models.items():
                    if model_id in models:
                        backend_name = bname
                        break
                
                if not backend_name:
                    return jsonify(error_response(f"Model '{model_id}' not found", status_code=404)), 404
            
            # Check cache first
            if hasattr(server_instance, 'video_cache'):
                cached_result = server_instance.video_cache.get(
                    prompt=prompt,
                    backend=backend_name,
                    model=model,
                    duration=duration,
                    aspect_ratio=aspect_ratio,
                    resolution=resolution,
                    **data.get("extra_params", {})
                )
                
                if cached_result:
                    logger.info(f"Cache hit for video generation: {cached_result.get('cache_key', 'unknown')[:16]}...")
                    return jsonify(success_response({
                        "video": cached_result,
                        "cached": True
                    }))
            
            # Use video queue if available
            if hasattr(server_instance, 'video_queue'):
                import asyncio
                from .video_websocket import emit_video_progress, emit_video_complete, emit_video_error
                
                # Add to queue
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # Create callbacks that capture video_id
                def create_callbacks(vid_id):
                    return (
                        lambda p: emit_video_progress(vid_id, p, "processing"),
                        lambda r: emit_video_complete(vid_id, r),
                        lambda e: emit_video_error(vid_id, e)
                    )
                
                # We need to add first, then set callbacks
                # For now, add without callbacks and emit manually
                video_id = loop.run_until_complete(
                    server_instance.video_queue.add(
                        prompt=prompt,
                        backend_name=backend_name,
                        model=model,
                        duration=duration,
                        aspect_ratio=aspect_ratio,
                        resolution=resolution,
                        metadata=data.get("extra_params", {})
                    )
                )
                loop.close()
                
                # Set up periodic status checking for WebSocket updates
                # The queue processor will handle the actual generation
                # We'll emit progress updates via status polling or direct callbacks
                
                return jsonify(success_response({
                    "video": {
                        "id": video_id,
                        "status": "pending",
                        "progress": 0.0,
                        "message": "Video generation queued"
                    }
                }))
            
            # Fallback to direct generation
            result = server_instance.video_loader.generate_video(
                prompt=prompt,
                backend_name=backend_name,
                model=model,
                duration=duration,
                aspect_ratio=aspect_ratio,
                resolution=resolution,
                **data.get("extra_params", {})
            )
            
            if result.status == "failed":
                return jsonify(error_response(result.error or "Video generation failed", status_code=500)), 500
            
            # Save to video manager
            video_id = None
            if hasattr(server_instance, 'video_manager'):
                try:
                    video_id = server_instance.video_manager.create_video(
                        prompt=prompt,
                        model=model,
                        backend=backend_name,
                        video_url=result.video_url,
                        video_path=result.video_path,
                        video_id=result.video_id,
                        duration=duration,
                        aspect_ratio=aspect_ratio,
                        resolution=resolution,
                        metadata=result.metadata
                    )
                except Exception as e:
                    logger.error(f"Error saving video to manager: {e}")
            
            # Save to shared context
            if hasattr(server_instance, 'shared_context'):
                try:
                    server_instance.shared_context.add_video_prompt(
                        prompt=prompt,
                        video_id=video_id or result.video_id,
                        metadata={
                            "model": model,
                            "backend": backend_name,
                            "duration": duration,
                            "aspect_ratio": aspect_ratio,
                            "resolution": resolution,
                            "video_url": result.video_url
                        }
                    )
                except Exception as e:
                    logger.debug(f"Could not save to shared context: {e}")
            
            return jsonify(success_response({
                "video": {
                    "url": result.video_url,
                    "path": result.video_path,
                    "id": video_id or result.video_id,
                    "status": result.status,
                    "progress": result.progress,
                    "model": result.model,
                    "prompt": result.prompt,
                    "metadata": result.metadata
                }
            }))
        except Exception as e:
            logger.error(f"Error generating video: {e}", exc_info=True)
            return jsonify(error_response(str(e), status_code=500)), 500
    
    @app.route("/api/video/status/<video_id>", methods=["GET"])
    def api_get_video_status(video_id: str):
        """Get status of a video generation"""
        try:
            # Check queue first
            if hasattr(server_instance, 'video_queue'):
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                queue_status = loop.run_until_complete(
                    server_instance.video_queue.get_status(video_id)
                )
                loop.close()
                
                if queue_status:
                    return jsonify(success_response({"video": queue_status}))
            
            # Fallback to video manager
            if hasattr(server_instance, 'video_manager'):
                video = server_instance.video_manager.get_video(video_id)
                if video:
                    return jsonify(success_response({"video": video}))
            
            return jsonify(error_response("Video not found", status_code=404, error_type="not_found")), 404
        except Exception as e:
            logger.error(f"Error getting video status: {e}", exc_info=True)
            return jsonify(error_response(str(e), status_code=500)), 500
    
    @app.route("/api/videos", methods=["GET"])
    def api_list_videos():
        """List all generated videos"""
        try:
            if not hasattr(server_instance, 'video_manager'):
                return jsonify(error_response("Video manager not initialized", status_code=500)), 500
            
            search = request.args.get("search", None)
            limit = request.args.get("limit", type=int)
            backend = request.args.get("backend", None)
            status = request.args.get("status", None)
            
            videos = server_instance.video_manager.list_videos(
                limit=limit,
                search=search,
                backend=backend,
                status=status
            )
            
            return jsonify(success_response({"videos": videos}))
        except Exception as e:
            logger.error(f"Error listing videos: {e}", exc_info=True)
            return jsonify(error_response(str(e), status_code=500)), 500
    
    @app.route("/api/videos/<video_id>", methods=["GET"])
    def api_get_video(video_id: str):
        """Get a video by ID"""
        try:
            if not hasattr(server_instance, 'video_manager'):
                return jsonify(error_response("Video manager not initialized", status_code=500)), 500
            
            video = server_instance.video_manager.get_video(video_id)
            if not video:
                return jsonify(error_response("Video not found", status_code=404, error_type="not_found")), 404
            
            return jsonify(success_response({"video": video}))
        except Exception as e:
            logger.error(f"Error getting video: {e}", exc_info=True)
            return jsonify(error_response(str(e), status_code=500)), 500
    
    @app.route("/api/videos/<video_id>", methods=["DELETE"])
    def api_delete_video(video_id: str):
        """Delete a video"""
        try:
            if not hasattr(server_instance, 'video_manager'):
                return jsonify(error_response("Video manager not initialized", status_code=500)), 500
            
            success = server_instance.video_manager.delete_video(video_id)
            if not success:
                return jsonify(error_response("Video not found", status_code=404, error_type="not_found")), 404
            
            return jsonify(success_response({"message": "Video deleted"}))
        except Exception as e:
            logger.error(f"Error deleting video: {e}", exc_info=True)
            return jsonify(error_response(str(e), status_code=500)), 500
    
    @app.route("/api/video/templates", methods=["GET"])
    def api_list_templates():
        """List video generation templates"""
        try:
            if not hasattr(server_instance, 'video_templates'):
                return jsonify(error_response("Video templates not initialized", status_code=500)), 500
            
            category = request.args.get("category", None)
            tags = request.args.getlist("tags")
            search = request.args.get("search", None)
            
            templates = server_instance.video_templates.list_templates(
                category=category,
                tags=tags if tags else None,
                search=search
            )
            
            return jsonify(success_response({
                "templates": [t.to_dict() for t in templates],
                "categories": server_instance.video_templates.get_categories(),
                "tags": server_instance.video_templates.get_tags()
            }))
        except Exception as e:
            logger.error(f"Error listing templates: {e}", exc_info=True)
            return jsonify(error_response(str(e), status_code=500)), 500
    
    @app.route("/api/video/templates/<template_id>", methods=["GET"])
    def api_get_template(template_id: str):
        """Get a specific template"""
        try:
            if not hasattr(server_instance, 'video_templates'):
                return jsonify(error_response("Video templates not initialized", status_code=500)), 500
            
            template = server_instance.video_templates.get_template(template_id)
            if not template:
                return jsonify(error_response("Template not found", status_code=404, error_type="not_found")), 404
            
            return jsonify(success_response({"template": template.to_dict()}))
        except Exception as e:
            logger.error(f"Error getting template: {e}", exc_info=True)
            return jsonify(error_response(str(e), status_code=500)), 500
    
    @app.route("/api/video/cache/stats", methods=["GET"])
    def api_get_cache_stats():
        """Get video cache statistics"""
        try:
            if not hasattr(server_instance, 'video_cache'):
                return jsonify(error_response("Video cache not initialized", status_code=500)), 500
            
            stats = server_instance.video_cache.get_stats()
            return jsonify(success_response({"stats": stats}))
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}", exc_info=True)
            return jsonify(error_response(str(e), status_code=500)), 500
    
    @app.route("/api/video/cache/clear", methods=["POST"])
    def api_clear_cache():
        """Clear video cache"""
        try:
            if not hasattr(server_instance, 'video_cache'):
                return jsonify(error_response("Video cache not initialized", status_code=500)), 500
            
            clear_all = request.args.get("all", "false").lower() == "true"
            
            if clear_all:
                server_instance.video_cache.clear_all()
                return jsonify(success_response({"message": "All cache cleared"}))
            else:
                server_instance.video_cache.clear_expired()
                return jsonify(success_response({"message": "Expired cache cleared"}))
        except Exception as e:
            logger.error(f"Error clearing cache: {e}", exc_info=True)
            return jsonify(error_response(str(e), status_code=500)), 500

