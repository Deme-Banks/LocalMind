"""
Additional routes - Routes that don't fit into main categories
"""

from typing import Dict, Any, Tuple
from flask import Flask, request, jsonify
from pathlib import Path
import logging
import platform
import sys
from datetime import datetime

from .base import error_response, success_response, get_project_root

logger = logging.getLogger(__name__)


def setup_additional_routes(app: Flask, server_instance):
    """
    Setup additional routes (status, modules, advanced features)
    
    Args:
        app: Flask application
        server_instance: WebServer instance
    """
    
    @app.route("/api/changelog", methods=["GET"])
    def api_changelog():
        """Get changelog content"""
        try:
            changelog_path = get_project_root() / "docs" / "CHANGELOG.md"
            if changelog_path.exists():
                with open(changelog_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                return jsonify(success_response({"changelog": content}))
            else:
                return jsonify(error_response("Changelog not found", status_code=404, error_type="not_found")), 404
        except Exception as e:
            logger.error(f"Error reading changelog: {e}", exc_info=True)
            return jsonify(error_response(str(e), status_code=500)), 500
    
    @app.route("/api/status", methods=["GET"])
    def api_status():
        """Get system status"""
        try:
            backends_status = {}
            for backend_name, backend in server_instance.model_loader.backends.items():
                backends_status[backend_name] = {
                    "available": backend.is_available(),
                    "models": backend.list_models()
                }
            
            modules_status = {}
            for module_name, module in server_instance.module_loader.modules.items():
                modules_status[module_name] = {
                    "enabled": module.enabled if hasattr(module, 'enabled') else True,
                    "description": getattr(module, 'description', '')
                }
            
            system_info = {
                "platform": platform.system(),
                "platform_version": platform.version(),
                "python_version": sys.version.split()[0],
                "architecture": platform.machine(),
                "processor": platform.processor() if platform.system() != "Windows" else "N/A"
            }
            
            return jsonify(success_response({
                "backends": backends_status,
                "modules": modules_status,
                "default_model": server_instance.config_manager.get_config().default_model,
                "system": system_info
            }))
        except Exception as e:
            logger.error(f"Error getting status: {e}")
            return jsonify(error_response(str(e), status_code=500)), 500
    
    @app.route("/api/modules", methods=["GET"])
    def api_list_modules() -> Tuple[Dict[str, Any], int]:
        """List all available modules."""
        try:
            modules = server_instance.module_loader.list_modules()
            return jsonify(success_response({"modules": modules}))
        except Exception as e:
            logger.error(f"Error listing modules: {e}")
            return jsonify(error_response(str(e), status_code=500)), 500
    
    # Advanced chat features
    @app.route("/api/chat/compare", methods=["POST"])
    def api_compare_models() -> Tuple[Dict[str, Any], int]:
        """Compare responses from multiple models"""
        try:
            data = request.get_json()
            if not data:
                return jsonify(error_response("No data provided", status_code=400, error_type="validation")), 400
            
            prompt = data.get("prompt")
            models = data.get("models", [])
            
            if not prompt:
                return jsonify(error_response("Prompt required", status_code=400, error_type="validation")), 400
            
            if len(models) < 2:
                return jsonify(error_response("At least 2 models required", status_code=400, error_type="validation")), 400
            
            results = server_instance.ab_tester.compare_models(
                prompt=prompt,
                models=models,
                temperature=data.get("temperature", 0.7)
            )
            
            return jsonify(success_response(results))
        except Exception as e:
            logger.error(f"Error comparing models: {e}", exc_info=True)
            return jsonify(error_response(str(e), status_code=500)), 500
    
    @app.route("/api/chat/ensemble", methods=["POST"])
    def api_ensemble_chat() -> Tuple[Dict[str, Any], int]:
        """Get ensemble response from multiple models"""
        try:
            data = request.get_json()
            if not data:
                return jsonify(error_response("No data provided", status_code=400, error_type="validation")), 400
            
            prompt = data.get("prompt")
            models = data.get("models", [])
            strategy = data.get("strategy", "majority")
            
            if not prompt:
                return jsonify(error_response("Prompt required", status_code=400, error_type="validation")), 400
            
            if not models:
                return jsonify(error_response("At least one model required", status_code=400, error_type="validation")), 400
            
            result = server_instance.ensemble_processor.process(
                prompt=prompt,
                models=models,
                strategy=strategy,
                temperature=data.get("temperature", 0.7)
            )
            
            return jsonify(success_response(result))
        except Exception as e:
            logger.error(f"Error in ensemble chat: {e}", exc_info=True)
            return jsonify(error_response(str(e), status_code=500)), 500
    
    @app.route("/api/chat/route", methods=["POST"])
    def api_route_chat() -> Tuple[Dict[str, Any], int]:
        """Route chat to best model based on task"""
        try:
            data = request.get_json()
            if not data:
                return jsonify(error_response("No data provided", status_code=400, error_type="validation")), 400
            
            prompt = data.get("prompt")
            task_type = data.get("task_type")
            
            if not prompt:
                return jsonify(error_response("Prompt required", status_code=400, error_type="validation")), 400
            
            # Get available models
            available_models = server_instance.model_loader.list_available_models()
            
            # Route to best model
            recommended_model, detected_task, confidence = server_instance.model_router.route_to_model(
                prompt=prompt,
                available_models=available_models,
                task_type=task_type
            )
            
            return jsonify(success_response({
                "recommended_model": recommended_model,
                "detected_task": detected_task,
                "confidence": confidence
            }))
        except Exception as e:
            logger.error(f"Error routing chat: {e}", exc_info=True)
            return jsonify(error_response(str(e), status_code=500)), 500
    
    # Quality and testing
    @app.route("/api/quality/score", methods=["POST"])
    def api_score_quality() -> Tuple[Dict[str, Any], int]:
        """Score response quality"""
        try:
            data = request.get_json()
            if not data:
                return jsonify(error_response("No data provided", status_code=400, error_type="validation")), 400
            
            response = data.get("response")
            prompt = data.get("prompt")
            
            if not response:
                return jsonify(error_response("Response required", status_code=400, error_type="validation")), 400
            
            score = server_instance.quality_scorer.score(response, prompt=prompt)
            
            return jsonify(success_response(score))
        except Exception as e:
            logger.error(f"Error scoring quality: {e}", exc_info=True)
            return jsonify(error_response(str(e), status_code=500)), 500
    
    @app.route("/api/ab-test", methods=["POST"])
    def api_ab_test() -> Tuple[Dict[str, Any], int]:
        """Run A/B test between two models"""
        try:
            data = request.get_json()
            if not data:
                return jsonify(error_response("No data provided", status_code=400, error_type="validation")), 400
            
            prompt = data.get("prompt")
            model_a = data.get("model_a")
            model_b = data.get("model_b")
            
            if not all([prompt, model_a, model_b]):
                return jsonify(error_response("prompt, model_a, and model_b required", status_code=400, error_type="validation")), 400
            
            result = server_instance.ab_tester.test(
                prompt=prompt,
                model_a=model_a,
                model_b=model_b,
                temperature=data.get("temperature", 0.7)
            )
            
            return jsonify(success_response(result))
        except Exception as e:
            logger.error(f"Error in A/B test: {e}", exc_info=True)
            return jsonify(error_response(str(e), status_code=500)), 500
    
    # Usage and resources
    @app.route("/api/usage/statistics", methods=["GET"])
    def api_usage_statistics() -> Tuple[Dict[str, Any], int]:
        """Get usage statistics"""
        try:
            backend = request.args.get("backend")
            model = request.args.get("model")
            
            stats = server_instance.usage_tracker.get_statistics(
                backend=backend,
                model=model
            )
            
            return jsonify(success_response(stats))
        except Exception as e:
            logger.error(f"Error getting usage statistics: {e}", exc_info=True)
            return jsonify(error_response(str(e), status_code=500)), 500
    
    @app.route("/api/resource/monitor", methods=["GET"])
    def api_resource_monitor() -> Tuple[Dict[str, Any], int]:
        """Get resource monitoring data"""
        try:
            metrics = server_instance.resource_monitor.get_metrics()
            return jsonify(success_response(metrics))
        except Exception as e:
            logger.error(f"Error getting resource metrics: {e}", exc_info=True)
            return jsonify(error_response(str(e), status_code=500)), 500
    
    @app.route("/api/resource/cleanup", methods=["POST"])
    def api_resource_cleanup() -> Tuple[Dict[str, Any], int]:
        """Run resource cleanup"""
        try:
            data = request.get_json() or {}
            cleanup_types = data.get("types", ["cache", "logs", "temp"])
            
            result = server_instance.resource_cleanup.cleanup(cleanup_types)
            
            return jsonify(success_response(result))
        except Exception as e:
            logger.error(f"Error running cleanup: {e}", exc_info=True)
            return jsonify(error_response(str(e), status_code=500)), 500
    
    # Privacy and security
    @app.route("/api/privacy/anonymize", methods=["POST"])
    def api_anonymize() -> Tuple[Dict[str, Any], int]:
        """Anonymize text"""
        try:
            data = request.get_json()
            if not data:
                return jsonify(error_response("No data provided", status_code=400, error_type="validation")), 400
            
            text = data.get("text")
            if not text:
                return jsonify(error_response("Text required", status_code=400, error_type="validation")), 400
            
            anonymized = server_instance.privacy_manager.anonymize(text)
            
            return jsonify(success_response({
                "original": text,
                "anonymized": anonymized
            }))
        except Exception as e:
            logger.error(f"Error anonymizing text: {e}", exc_info=True)
            return jsonify(error_response(str(e), status_code=500)), 500
    
    @app.route("/api/privacy/check", methods=["POST"])
    def api_check_privacy() -> Tuple[Dict[str, Any], int]:
        """Check privacy compliance"""
        try:
            data = request.get_json()
            if not data:
                return jsonify(error_response("No data provided", status_code=400, error_type="validation")), 400
            
            text = data.get("text")
            if not text:
                return jsonify(error_response("Text required", status_code=400, error_type="validation")), 400
            
            compliance = server_instance.privacy_manager.check_privacy_compliance(text)
            
            return jsonify(success_response(compliance))
        except Exception as e:
            logger.error(f"Error checking privacy: {e}", exc_info=True)
            return jsonify(error_response(str(e), status_code=500)), 500
    
    @app.route("/api/local-only-mode", methods=["GET"])
    def api_get_local_only_mode() -> Tuple[Dict[str, Any], int]:
        """Get local-only mode status"""
        try:
            return jsonify(success_response({
                "enabled": server_instance.local_only_mode.enabled,
                "allowed_backends": server_instance.local_only_mode.get_allowed_backends(),
                "blocked_backends": server_instance.local_only_mode.get_blocked_backends()
            }))
        except Exception as e:
            logger.error(f"Error getting local-only mode: {e}", exc_info=True)
            return jsonify(error_response(str(e), status_code=500)), 500
    
    @app.route("/api/local-only-mode", methods=["POST"])
    def api_set_local_only_mode() -> Tuple[Dict[str, Any], int]:
        """Enable/disable local-only mode"""
        try:
            data = request.get_json()
            if data is None:
                return jsonify(error_response("No data provided", status_code=400, error_type="validation")), 400
            
            enabled = data.get("enabled", False)
            
            if enabled:
                server_instance.local_only_mode.enable()
            else:
                server_instance.local_only_mode.disable()
            
            # Save to config
            config = server_instance.config_manager.get_config()
            config.local_only_mode = enabled
            server_instance.config_manager.config = config
            server_instance.config_manager.save_config()
            
            # Audit log
            from ...core.audit_logger import AuditEventType
            server_instance.audit_logger.log(
                AuditEventType.CONFIG_CHANGE,
                ip_address=request.remote_addr or "unknown",
                details={"action": "local_only_mode", "enabled": enabled}
            )
            
            return jsonify(success_response({
                "enabled": enabled,
                "message": "Local-only mode updated"
            }))
        except Exception as e:
            logger.error(f"Error setting local-only mode: {e}", exc_info=True)
            return jsonify(error_response(str(e), status_code=500)), 500
    
    @app.route("/api/privacy/audit", methods=["POST"])
    def api_privacy_audit() -> Tuple[Dict[str, Any], int]:
        """Run privacy audit"""
        try:
            data = request.get_json() or {}
            audit_type = data.get("type", "full")  # full, conversations, api_keys, access_logs
            
            if audit_type == "conversations" or audit_type == "full":
                conversations_audit = server_instance.privacy_auditor.audit_conversations(
                    limit=data.get("limit"),
                    check_encryption=data.get("check_encryption", True),
                    check_anonymization=data.get("check_anonymization", True)
                )
            else:
                conversations_audit = {}
            
            if audit_type == "api_keys" or audit_type == "full":
                api_keys_audit = server_instance.privacy_auditor.audit_api_keys(server_instance.key_manager)
            else:
                api_keys_audit = {}
            
            if audit_type == "access_logs" or audit_type == "full":
                access_logs_audit = server_instance.privacy_auditor.audit_access_logs(
                    days=data.get("days", 30),
                    check_suspicious=data.get("check_suspicious", True)
                )
            else:
                access_logs_audit = {}
            
            if audit_type == "full":
                report = server_instance.privacy_auditor.generate_privacy_report()
                return jsonify(success_response(report))
            else:
                return jsonify(success_response({
                    "conversations": conversations_audit,
                    "api_keys": api_keys_audit,
                    "access_logs": access_logs_audit
                }))
        except Exception as e:
            logger.error(f"Error running privacy audit: {e}", exc_info=True)
            return jsonify(error_response(str(e), status_code=500)), 500
    
    # Audit logs
    @app.route("/api/audit/logs", methods=["GET"])
    def api_get_audit_logs() -> Tuple[Dict[str, Any], int]:
        """Get audit logs"""
        try:
            from datetime import datetime, timedelta
            from ...core.audit_logger import AuditEventType
            
            start_date = request.args.get("start_date")
            end_date = request.args.get("end_date")
            event_type = request.args.get("event_type")
            limit = request.args.get("limit", type=int, default=100)
            
            if start_date:
                start_date = datetime.fromisoformat(start_date)
            else:
                start_date = datetime.utcnow() - timedelta(days=7)
            
            if end_date:
                end_date = datetime.fromisoformat(end_date)
            else:
                end_date = datetime.utcnow()
            
            event_type_enum = None
            if event_type:
                try:
                    event_type_enum = AuditEventType(event_type)
                except ValueError:
                    pass
            
            logs = server_instance.audit_logger.query(
                start_date=start_date,
                end_date=end_date,
                event_type=event_type_enum,
                limit=limit
            )
            
            return jsonify(success_response({"logs": logs, "count": len(logs)}))
        except Exception as e:
            logger.error(f"Error getting audit logs: {e}", exc_info=True)
            return jsonify(error_response(str(e), status_code=500)), 500
    
    # Fine-tuning
    @app.route("/api/finetuning/datasets", methods=["GET"])
    def api_list_datasets() -> Tuple[Dict[str, Any], int]:
        """List training datasets"""
        try:
            datasets = server_instance.finetuning_manager.list_datasets()
            return jsonify(success_response({"datasets": datasets}))
        except Exception as e:
            logger.error(f"Error listing datasets: {e}", exc_info=True)
            return jsonify(error_response(str(e), status_code=500)), 500
    
    @app.route("/api/finetuning/datasets", methods=["POST"])
    def api_create_dataset() -> Tuple[Dict[str, Any], int]:
        """Create training dataset"""
        try:
            data = request.get_json()
            if not data:
                return jsonify(error_response("No data provided", status_code=400, error_type="validation")), 400
            
            name = data.get("name")
            entries = data.get("entries", [])
            
            if not name:
                return jsonify(error_response("Dataset name required", status_code=400, error_type="validation")), 400
            
            from ...core.finetuning import TrainingData
            training_data = [
                TrainingData(
                    prompt=entry.get("prompt", ""),
                    completion=entry.get("completion", ""),
                    metadata=entry.get("metadata", {})
                )
                for entry in entries
            ]
            
            dataset_path = server_instance.finetuning_manager.create_training_dataset(name, training_data)
            
            return jsonify(success_response({
                "name": name,
                "path": str(dataset_path),
                "entries": len(training_data)
            }))
        except Exception as e:
            logger.error(f"Error creating dataset: {e}", exc_info=True)
            return jsonify(error_response(str(e), status_code=500)), 500
    
    @app.route("/api/finetuning/jobs", methods=["GET"])
    def api_list_finetuning_jobs() -> Tuple[Dict[str, Any], int]:
        """List fine-tuning jobs"""
        try:
            jobs = server_instance.finetuning_manager.list_jobs()
            return jsonify(success_response({"jobs": jobs}))
        except Exception as e:
            logger.error(f"Error listing jobs: {e}", exc_info=True)
            return jsonify(error_response(str(e), status_code=500)), 500
    
    @app.route("/api/finetuning/jobs", methods=["POST"])
    def api_create_finetuning_job() -> Tuple[Dict[str, Any], int]:
        """Create fine-tuning job"""
        try:
            data = request.get_json()
            if not data:
                return jsonify(error_response("No data provided", status_code=400, error_type="validation")), 400
            
            model = data.get("model")
            base_model = data.get("base_model")
            training_data_path = Path(data.get("training_data_path"))
            
            if not all([model, base_model, training_data_path]):
                return jsonify(error_response("model, base_model, and training_data_path required", status_code=400, error_type="validation")), 400
            
            job = server_instance.finetuning_manager.create_finetuning_job(model, base_model, training_data_path)
            
            return jsonify(success_response({
                "job_id": job.job_id,
                "model": job.model,
                "base_model": job.base_model,
                "status": job.status
            }))
        except Exception as e:
            logger.error(f"Error creating fine-tuning job: {e}", exc_info=True)
            return jsonify(error_response(str(e), status_code=500)), 500
    
    # Model versioning
    @app.route("/api/models/versions", methods=["GET"])
    def api_list_model_versions() -> Tuple[Dict[str, Any], int]:
        """List model versions"""
        try:
            model_name = request.args.get("model")
            if model_name:
                versions = server_instance.model_version_manager.get_versions(model_name)
                latest = server_instance.model_version_manager.get_latest_version(model_name)
                return jsonify(success_response({
                    "model": model_name,
                    "versions": [
                        {
                            "version": v.version,
                            "created_at": v.created_at.isoformat(),
                            "metadata": v.metadata
                        }
                        for v in versions
                    ],
                    "latest": {
                        "version": latest.version,
                        "created_at": latest.created_at.isoformat()
                    } if latest else None
                }))
            else:
                # List all models with versions
                all_models = {}
                for model_name in server_instance.model_version_manager.versions.keys():
                    versions = server_instance.model_version_manager.get_versions(model_name)
                    latest = server_instance.model_version_manager.get_latest_version(model_name)
                    all_models[model_name] = {
                        "version_count": len(versions),
                        "latest_version": latest.version if latest else None
                    }
                return jsonify(success_response({"models": all_models}))
        except Exception as e:
            logger.error(f"Error listing model versions: {e}", exc_info=True)
            return jsonify(error_response(str(e), status_code=500)), 500




