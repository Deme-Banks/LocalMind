"""
Webhook Manager - handles webhook notifications for integrations
"""

import json
import requests
import threading
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class WebhookEvent(str, Enum):
    """Webhook event types"""
    CHAT_MESSAGE = "chat.message"
    CHAT_COMPLETE = "chat.complete"
    CONVERSATION_CREATED = "conversation.created"
    CONVERSATION_UPDATED = "conversation.updated"
    CONVERSATION_DELETED = "conversation.deleted"
    MODEL_SELECTED = "model.selected"
    MODEL_DOWNLOADED = "model.downloaded"
    ERROR_OCCURRED = "error.occurred"
    BUDGET_EXCEEDED = "budget.exceeded"
    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"


class WebhookManager:
    """Manages webhook subscriptions and notifications"""
    
    def __init__(self, webhooks_file: Optional[Path] = None):
        """
        Initialize webhook manager
        
        Args:
            webhooks_file: Path to webhooks configuration file
        """
        if webhooks_file is None:
            webhooks_file = Path(__file__).parent.parent.parent / "webhooks.json"
        
        self.webhooks_file = webhooks_file
        self.webhooks_file.parent.mkdir(parents=True, exist_ok=True)
        self.webhooks: List[Dict[str, Any]] = self._load_webhooks()
        self.enabled = True
    
    def _load_webhooks(self) -> List[Dict[str, Any]]:
        """Load webhooks from file"""
        if self.webhooks_file.exists():
            try:
                with open(self.webhooks_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading webhooks: {e}")
                return []
        return []
    
    def _save_webhooks(self):
        """Save webhooks to file"""
        try:
            with open(self.webhooks_file, 'w', encoding='utf-8') as f:
                json.dump(self.webhooks, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving webhooks: {e}")
    
    def add_webhook(self, url: str, events: List[str], secret: Optional[str] = None, 
                    enabled: bool = True, description: Optional[str] = None) -> str:
        """
        Add a new webhook subscription
        
        Args:
            url: Webhook URL
            events: List of event types to subscribe to
            secret: Optional secret for webhook authentication
            enabled: Whether webhook is enabled
            description: Optional description
            
        Returns:
            Webhook ID
        """
        import uuid
        webhook_id = str(uuid.uuid4())
        
        webhook = {
            "id": webhook_id,
            "url": url,
            "events": events,
            "secret": secret,
            "enabled": enabled,
            "description": description,
            "created_at": datetime.now().isoformat(),
            "last_triggered": None,
            "success_count": 0,
            "failure_count": 0
        }
        
        self.webhooks.append(webhook)
        self._save_webhooks()
        
        logger.info(f"Added webhook: {webhook_id} -> {url}")
        return webhook_id
    
    def remove_webhook(self, webhook_id: str) -> bool:
        """
        Remove a webhook subscription
        
        Args:
            webhook_id: Webhook ID to remove
            
        Returns:
            True if removed, False if not found
        """
        initial_count = len(self.webhooks)
        self.webhooks = [w for w in self.webhooks if w.get("id") != webhook_id]
        
        if len(self.webhooks) < initial_count:
            self._save_webhooks()
            logger.info(f"Removed webhook: {webhook_id}")
            return True
        return False
    
    def update_webhook(self, webhook_id: str, **kwargs) -> bool:
        """
        Update webhook configuration
        
        Args:
            webhook_id: Webhook ID to update
            **kwargs: Fields to update (url, events, secret, enabled, description)
            
        Returns:
            True if updated, False if not found
        """
        for webhook in self.webhooks:
            if webhook.get("id") == webhook_id:
                for key, value in kwargs.items():
                    if key in webhook:
                        webhook[key] = value
                self._save_webhooks()
                logger.info(f"Updated webhook: {webhook_id}")
                return True
        return False
    
    def get_webhook(self, webhook_id: str) -> Optional[Dict[str, Any]]:
        """Get webhook by ID"""
        for webhook in self.webhooks:
            if webhook.get("id") == webhook_id:
                return webhook
        return None
    
    def list_webhooks(self, enabled_only: bool = False) -> List[Dict[str, Any]]:
        """
        List all webhooks
        
        Args:
            enabled_only: Only return enabled webhooks
            
        Returns:
            List of webhook configurations
        """
        if enabled_only:
            return [w for w in self.webhooks if w.get("enabled", True)]
        return self.webhooks.copy()
    
    def trigger_webhook(self, event: str, data: Dict[str, Any], webhook_id: Optional[str] = None):
        """
        Trigger webhooks for an event
        
        Args:
            event: Event type
            data: Event data payload
            webhook_id: Optional specific webhook ID to trigger (otherwise triggers all matching)
        """
        if not self.enabled:
            return
        
        # Find matching webhooks
        webhooks_to_trigger = []
        if webhook_id:
            webhook = self.get_webhook(webhook_id)
            if webhook and webhook.get("enabled", True) and event in webhook.get("events", []):
                webhooks_to_trigger.append(webhook)
        else:
            for webhook in self.webhooks:
                if webhook.get("enabled", True) and event in webhook.get("events", []):
                    webhooks_to_trigger.append(webhook)
        
        # Trigger webhooks asynchronously
        for webhook in webhooks_to_trigger:
            self._send_webhook(webhook, event, data)
    
    def _send_webhook(self, webhook: Dict[str, Any], event: str, data: Dict[str, Any]):
        """
        Send webhook notification (async)
        
        Args:
            webhook: Webhook configuration
            event: Event type
            data: Event data
        """
        def send():
            try:
                payload = {
                    "event": event,
                    "timestamp": datetime.now().isoformat(),
                    "data": data
                }
                
                headers = {
                    "Content-Type": "application/json",
                    "User-Agent": "LocalMind/1.0"
                }
                
                # Add secret to headers if present
                secret = webhook.get("secret")
                if secret:
                    headers["X-Webhook-Secret"] = secret
                
                # Add webhook ID
                headers["X-Webhook-ID"] = webhook.get("id", "")
                
                response = requests.post(
                    webhook["url"],
                    json=payload,
                    headers=headers,
                    timeout=10
                )
                
                # Update statistics
                webhook["last_triggered"] = datetime.now().isoformat()
                if response.status_code >= 200 and response.status_code < 300:
                    webhook["success_count"] = webhook.get("success_count", 0) + 1
                else:
                    webhook["failure_count"] = webhook.get("failure_count", 0) + 1
                    logger.warning(f"Webhook {webhook.get('id')} returned status {response.status_code}")
                
                self._save_webhooks()
                
            except requests.exceptions.Timeout:
                webhook["failure_count"] = webhook.get("failure_count", 0) + 1
                logger.warning(f"Webhook {webhook.get('id')} timed out")
                self._save_webhooks()
            except Exception as e:
                webhook["failure_count"] = webhook.get("failure_count", 0) + 1
                logger.error(f"Error sending webhook {webhook.get('id')}: {e}")
                self._save_webhooks()
        
        # Send in background thread
        thread = threading.Thread(target=send, daemon=True)
        thread.start()
    
    def test_webhook(self, webhook_id: str) -> Dict[str, Any]:
        """
        Test a webhook by sending a test event
        
        Args:
            webhook_id: Webhook ID to test
            
        Returns:
            Test results
        """
        webhook = self.get_webhook(webhook_id)
        if not webhook:
            return {"success": False, "error": "Webhook not found"}
        
        test_data = {
            "test": True,
            "message": "This is a test webhook from LocalMind"
        }
        
        try:
            self.trigger_webhook(WebhookEvent.SYSTEM_STARTUP, test_data, webhook_id)
            return {"success": True, "message": "Test webhook sent"}
        except Exception as e:
            return {"success": False, "error": str(e)}

