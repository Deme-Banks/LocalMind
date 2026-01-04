"""
Privacy Audit Tools - Audit privacy compliance and data handling
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
import logging

from .privacy_manager import PrivacyManager
from .audit_logger import AuditLogger, AuditEventType

logger = logging.getLogger(__name__)


class PrivacyAuditor:
    """Audits privacy compliance and data handling"""
    
    def __init__(
        self,
        privacy_manager: PrivacyManager,
        audit_logger: AuditLogger,
        conversations_dir: Optional[Path] = None
    ):
        """
        Initialize privacy auditor
        
        Args:
            privacy_manager: PrivacyManager instance
            audit_logger: AuditLogger instance
            conversations_dir: Directory containing conversations
        """
        self.privacy_manager = privacy_manager
        self.audit_logger = audit_logger
        self.conversations_dir = conversations_dir
    
    def audit_conversations(
        self,
        limit: Optional[int] = None,
        check_encryption: bool = True,
        check_anonymization: bool = True
    ) -> Dict[str, Any]:
        """
        Audit conversations for privacy compliance
        
        Args:
            limit: Maximum number of conversations to audit
            check_encryption: Check if conversations are encrypted
            check_anonymization: Check if conversations contain sensitive data
            
        Returns:
            Audit results dictionary
        """
        if not self.conversations_dir or not self.conversations_dir.exists():
            return {
                "status": "error",
                "message": "Conversations directory not found"
            }
        
        results = {
            "total_checked": 0,
            "encrypted": 0,
            "unencrypted": 0,
            "has_sensitive_data": 0,
            "compliant": 0,
            "non_compliant": 0,
            "issues": []
        }
        
        # Get conversation files
        conversation_files = list(self.conversations_dir.glob("*.json"))
        if limit:
            conversation_files = conversation_files[:limit]
        
        results["total_checked"] = len(conversation_files)
        
        for conv_file in conversation_files:
            try:
                # Check encryption (basic check - encrypted files might have different extension)
                is_encrypted = conv_file.suffix == ".enc" or ".encrypted" in conv_file.name
                if is_encrypted:
                    results["encrypted"] += 1
                else:
                    results["unencrypted"] += 1
                    if check_encryption:
                        results["issues"].append({
                            "type": "unencrypted",
                            "file": str(conv_file.name),
                            "severity": "medium"
                        })
                
                # Check for sensitive data
                if check_anonymization:
                    with open(conv_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    compliance = self.privacy_manager.check_privacy_compliance(content)
                    if not compliance["compliant"]:
                        results["has_sensitive_data"] += 1
                        results["non_compliant"] += 1
                        results["issues"].append({
                            "type": "sensitive_data",
                            "file": str(conv_file.name),
                            "findings": compliance["findings"],
                            "severity": "high"
                        })
                    else:
                        results["compliant"] += 1
                else:
                    results["compliant"] += 1
                    
            except Exception as e:
                logger.error(f"Error auditing conversation {conv_file}: {e}")
                results["issues"].append({
                    "type": "error",
                    "file": str(conv_file.name),
                    "error": str(e),
                    "severity": "low"
                })
        
        # Calculate compliance percentage
        if results["total_checked"] > 0:
            results["compliance_percentage"] = round(
                (results["compliant"] / results["total_checked"]) * 100, 2
            )
        else:
            results["compliance_percentage"] = 0.0
        
        return results
    
    def audit_api_keys(self, key_manager) -> Dict[str, Any]:
        """
        Audit API key storage
        
        Args:
            key_manager: KeyManager instance
            
        Returns:
            Audit results
        """
        results = {
            "total_keys": 0,
            "encrypted": 0,
            "unencrypted": 0,
            "providers": []
        }
        
        providers = key_manager.list_providers()
        results["total_keys"] = len(providers)
        
        for provider in providers:
            has_key = key_manager.has_key(provider)
            if has_key:
                results["encrypted"] += 1
                results["providers"].append({
                    "provider": provider,
                    "encrypted": True
                })
            else:
                results["unencrypted"] += 1
                results["providers"].append({
                    "provider": provider,
                    "encrypted": False
                })
        
        return results
    
    def audit_access_logs(
        self,
        days: int = 30,
        check_suspicious: bool = True
    ) -> Dict[str, Any]:
        """
        Audit access logs for privacy concerns
        
        Args:
            days: Number of days to audit
            check_suspicious: Check for suspicious activity
            
        Returns:
            Audit results
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get audit logs
        events = self.audit_logger.query(start_date=start_date, end_date=end_date, limit=10000)
        
        results = {
            "total_events": len(events),
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "by_type": {},
            "unique_ips": set(),
            "suspicious_activity": []
        }
        
        # Analyze events
        for event in events:
            event_type = event.get("event_type", "unknown")
            results["by_type"][event_type] = results["by_type"].get(event_type, 0) + 1
            
            ip = event.get("ip_address")
            if ip and ip != "unknown":
                results["unique_ips"].add(ip)
            
            # Check for suspicious activity
            if check_suspicious:
                if event_type == "security_violation":
                    results["suspicious_activity"].append({
                        "type": "security_violation",
                        "timestamp": event.get("timestamp"),
                        "ip": event.get("ip_address"),
                        "details": event.get("details", {})
                    })
                elif event.get("success") is False and event_type in ["api_key_access", "config_change"]:
                    results["suspicious_activity"].append({
                        "type": "failed_action",
                        "timestamp": event.get("timestamp"),
                        "ip": event.get("ip_address"),
                        "event_type": event_type
                    })
        
        results["unique_ips"] = list(results["unique_ips"])
        results["unique_ip_count"] = len(results["unique_ips"])
        
        return results
    
    def generate_privacy_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive privacy audit report
        
        Returns:
            Privacy audit report
        """
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "conversations": {},
            "api_keys": {},
            "access_logs": {},
            "recommendations": []
        }
        
        # Audit conversations
        try:
            report["conversations"] = self.audit_conversations()
            
            # Add recommendations
            if report["conversations"].get("unencrypted", 0) > 0:
                report["recommendations"].append({
                    "type": "encryption",
                    "priority": "high",
                    "message": f"{report['conversations']['unencrypted']} conversations are not encrypted. Consider enabling conversation encryption."
                })
            
            if report["conversations"].get("has_sensitive_data", 0) > 0:
                report["recommendations"].append({
                    "type": "anonymization",
                    "priority": "high",
                    "message": f"{report['conversations']['has_sensitive_data']} conversations contain sensitive data. Consider anonymizing before storage."
                })
        except Exception as e:
            logger.error(f"Error auditing conversations: {e}")
            report["conversations"] = {"error": str(e)}
        
        # Audit access logs
        try:
            report["access_logs"] = self.audit_access_logs(days=30)
            
            if report["access_logs"].get("suspicious_activity"):
                report["recommendations"].append({
                    "type": "security",
                    "priority": "high",
                    "message": f"{len(report['access_logs']['suspicious_activity'])} suspicious activities detected. Review access logs."
                })
        except Exception as e:
            logger.error(f"Error auditing access logs: {e}")
            report["access_logs"] = {"error": str(e)}
        
        return report

