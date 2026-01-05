"""
Code execution routes - Handle code execution endpoints
"""

from typing import Dict, Any
from flask import Flask, request, jsonify
import logging

from .base import error_response, success_response

logger = logging.getLogger(__name__)


def setup_code_execution_routes(app: Flask, server_instance):
    """
    Setup code execution-related routes
    
    Args:
        app: Flask application
        server_instance: WebServer instance
    """
    
    @app.route("/api/code/execute", methods=["POST"])
    def api_execute_code():
        """Execute code in a sandboxed environment"""
        try:
            if not hasattr(server_instance, 'code_execution_manager'):
                return jsonify(error_response("Code execution manager not initialized", status_code=500)), 500
            
            data = request.get_json() or {}
            code = data.get("code")
            language = data.get("language")
            timeout = data.get("timeout", 30)
            
            if not code:
                return jsonify(error_response("Code is required", status_code=400, error_type="validation")), 400
            
            # Auto-detect language if not provided
            if not language:
                language = server_instance.code_execution_manager.detect_language(code)
                if not language:
                    return jsonify(error_response(
                        "Could not detect programming language. Please specify 'language' parameter.",
                        status_code=400,
                        error_type="validation"
                    )), 400
            
            # Execute code
            result = server_instance.code_execution_manager.execute_code(
                code=code,
                language=language,
                timeout=timeout
            )
            
            # Format response
            response_data = {
                "status": result.status.value,
                "output": result.output,
                "error": result.error,
                "execution_time": result.execution_time,
                "language": result.language,
                "code": result.code,
                "metadata": result.metadata
            }
            
            if result.status.value == "success":
                return jsonify(success_response(response_data))
            else:
                return jsonify(error_response(
                    result.error or "Code execution failed",
                    status_code=400,
                    details=response_data
                )), 400
                
        except Exception as e:
            logger.error(f"Error executing code: {e}", exc_info=True)
            return jsonify(error_response(str(e), status_code=500)), 500
    
    @app.route("/api/code/languages", methods=["GET"])
    def api_list_code_languages():
        """List available code execution languages"""
        try:
            if not hasattr(server_instance, 'code_execution_manager'):
                return jsonify(error_response("Code execution manager not initialized", status_code=500)), 500
            
            languages = server_instance.code_execution_manager.list_executors()
            executors_info = []
            
            for lang in languages:
                executor = server_instance.code_execution_manager.get_executor(lang)
                if executor:
                    executors_info.append(executor.get_executor_info())
            
            return jsonify(success_response({
                "languages": languages,
                "executors": executors_info
            }))
        except Exception as e:
            logger.error(f"Error listing code languages: {e}", exc_info=True)
            return jsonify(error_response(str(e), status_code=500)), 500
    
    @app.route("/api/code/detect", methods=["POST"])
    def api_detect_language():
        """Detect programming language from code"""
        try:
            if not hasattr(server_instance, 'code_execution_manager'):
                return jsonify(error_response("Code execution manager not initialized", status_code=500)), 500
            
            data = request.get_json() or {}
            code = data.get("code")
            
            if not code:
                return jsonify(error_response("Code is required", status_code=400, error_type="validation")), 400
            
            detected = server_instance.code_execution_manager.detect_language(code)
            
            return jsonify(success_response({
                "language": detected,
                "code": code[:100] + "..." if len(code) > 100 else code  # Preview
            }))
        except Exception as e:
            logger.error(f"Error detecting language: {e}", exc_info=True)
            return jsonify(error_response(str(e), status_code=500)), 500
    
    @app.route("/api/code/stats", methods=["GET"])
    def api_code_execution_stats():
        """Get code execution statistics"""
        try:
            if not hasattr(server_instance, 'code_execution_manager'):
                return jsonify(error_response("Code execution manager not initialized", status_code=500)), 500
            
            executors = server_instance.code_execution_manager.list_executors()
            executor_info = []
            
            for lang in executors:
                executor = server_instance.code_execution_manager.get_executor(lang)
                if executor:
                    info = executor.get_executor_info()
                    executor_info.append({
                        "language": lang,
                        "name": info.get("name"),
                        "available": info.get("available", False),
                        "timeout": info.get("timeout", 30),
                        "max_memory": info.get("max_memory")
                    })
            
            return jsonify(success_response({
                "total_languages": len(executors),
                "available_languages": [lang for lang in executors if server_instance.code_execution_manager.get_executor(lang).is_available()],
                "executors": executor_info
            }))
        except Exception as e:
            logger.error(f"Error getting code execution stats: {e}", exc_info=True)
            return jsonify(error_response(str(e), status_code=500)), 500

