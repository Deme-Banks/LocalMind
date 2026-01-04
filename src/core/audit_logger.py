"""
Audit Logger - Logs all security-relevant events
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class AuditEventType(Enum):
    """Types of audit events"""
    LOGIN = "login"
    LOGOUT = "logout"
    API_KEY_ACCESS = "api_key_access"
    API_KEY_CREATE = "api_key_create"
    API_KEY_UPDATE = "api_key_update"
    API_KEY_DELETE = "api_key_delete"
    CONFIG_CHANGE = "config_change"
    MODEL_DOWNLOAD = "model_download"
    MODEL_DELETE = "model_delete"
    CONVERSATION_ACCESS = "conversation_access"
    CONVERSATION_DELETE = "conversation_delete"
    ADMIN_ACTION = "admin_action"
    ERROR = "error"
    SECURITY_VIOLATION = "security_violation"


class AuditLogger:
    """Logs security and audit events"""
    
    def __init__(self, audit_dir: Optional[Path] = None):
        """
        Initialize audit logger
        
        Args:
            audit_dir: Directory for audit logs (default: ~/.localmind/audit)
        """
        if audit_dir is None:
            audit_dir = Path.home() / ".localmind" / "audit"
        
        self.audit_dir = audit_dir
        self.audit_dir.mkdir(parents=True, exist_ok=True)
        self.audit_dir.chmod(0o700)  # Restrict permissions
    
    def log(
        self,
        event_type: AuditEventType,
        user: Optional[str] = None,
        ip_address: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        success: bool = True
    ):
        """
        Log an audit event
        
        Args:
            event_type: Type of event
            user: User identifier (optional)
            ip_address: IP address (optional)
            details: Additional event details
            success: Whether the action was successful
        """
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type.value,
            "user": user or "system",
            "ip_address": ip_address or "unknown",
            "success": success,
            "details": details or {}
        }
        
        # Write to daily log file
        today = datetime.utcnow().date()
        log_file = self.audit_dir / f"audit_{today.isoformat()}.jsonl"
        
        try:
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(event) + '\n')
            
            # Also log to standard logger
            logger.info(f"Audit: {event_type.value} - {user or 'system'} - {ip_address or 'unknown'} - Success: {success}")
        except Exception as e:
            logger.error(f"Error writing audit log: {e}")
    
    def query(
        self,
        event_type: Optional[AuditEventType] = None,
        user: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Query audit logs
        
        Args:
            event_type: Filter by event type
            user: Filter by user
            start_date: Start date for query
            end_date: End date for query
            limit: Maximum number of results
            
        Returns:
            List of audit events
        """
        events = []
        
        # Determine date range
        if start_date:
            start_date = start_date.date()
        if end_date:
            end_date = end_date.date()
        
        # Iterate through log files
        for log_file in sorted(self.audit_dir.glob("audit_*.jsonl"), reverse=True):
            file_date = datetime.strptime(log_file.stem.split('_')[1], '%Y-%m-%d').date()
            
            # Skip if outside date range
            if start_date and file_date < start_date:
                continue
            if end_date and file_date > end_date:
                continue
            
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if len(events) >= limit:
                            break
                        
                        event = json.loads(line.strip())
                        
                        # Apply filters
                        if event_type and event.get("event_type") != event_type.value:
                            continue
                        if user and event.get("user") != user:
                            continue
                        
                        events.append(event)
            except Exception as e:
                logger.error(f"Error reading audit log {log_file}: {e}")
        
        return events[:limit]
    
    def get_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get audit log statistics
        
        Args:
            start_date: Start date
            end_date: End date
            
        Returns:
            Statistics dictionary
        """
        events = self.query(start_date=start_date, end_date=end_date, limit=10000)
        
        stats = {
            "total_events": len(events),
            "by_type": {},
            "by_user": {},
            "successful": 0,
            "failed": 0
        }
        
        for event in events:
            # Count by type
            event_type = event.get("event_type", "unknown")
            stats["by_type"][event_type] = stats["by_type"].get(event_type, 0) + 1
            
            # Count by user
            user = event.get("user", "unknown")
            stats["by_user"][user] = stats["by_user"].get(user, 0) + 1
            
            # Count success/failure
            if event.get("success", True):
                stats["successful"] += 1
            else:
                stats["failed"] += 1
        
        return stats

