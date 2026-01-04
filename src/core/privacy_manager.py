"""
Privacy Manager - Data anonymization and privacy features
"""

import re
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class AnonymizationRule:
    """Rule for anonymizing data"""
    pattern: str  # Regex pattern
    replacement: str  # Replacement string
    description: str  # Description of what this anonymizes


class PrivacyManager:
    """Manages privacy features including data anonymization"""
    
    def __init__(self):
        """Initialize privacy manager"""
        # Default anonymization rules
        self.anonymization_rules = [
            AnonymizationRule(
                pattern=r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
                replacement='[SSN_REDACTED]',
                description='Social Security Numbers'
            ),
            AnonymizationRule(
                pattern=r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',  # Credit card
                replacement='[CARD_REDACTED]',
                description='Credit card numbers'
            ),
            AnonymizationRule(
                pattern=r'\b\d{3}-\d{3}-\d{4}\b',  # Phone
                replacement='[PHONE_REDACTED]',
                description='Phone numbers'
            ),
            AnonymizationRule(
                pattern=r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
                replacement='[EMAIL_REDACTED]',
                description='Email addresses'
            ),
            AnonymizationRule(
                pattern=r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',  # IP address
                replacement='[IP_REDACTED]',
                description='IP addresses'
            ),
            AnonymizationRule(
                pattern=r'\b[A-Z]{2}\d{6,}\b',  # Passport/ID numbers
                replacement='[ID_REDACTED]',
                description='ID numbers'
            ),
        ]
    
    def anonymize(self, text: str, custom_rules: Optional[List[AnonymizationRule]] = None) -> str:
        """
        Anonymize sensitive data in text
        
        Args:
            text: Text to anonymize
            custom_rules: Optional custom anonymization rules
            
        Returns:
            Anonymized text
        """
        if not text:
            return text
        
        rules = custom_rules or self.anonymization_rules
        anonymized = text
        
        for rule in rules:
            try:
                anonymized = re.sub(rule.pattern, rule.replacement, anonymized, flags=re.IGNORECASE)
            except Exception as e:
                logger.warning(f"Error applying anonymization rule '{rule.description}': {e}")
        
        return anonymized
    
    def add_rule(self, pattern: str, replacement: str, description: str):
        """
        Add custom anonymization rule
        
        Args:
            pattern: Regex pattern to match
            replacement: Replacement string
            description: Description of what this anonymizes
        """
        rule = AnonymizationRule(pattern=pattern, replacement=replacement, description=description)
        self.anonymization_rules.append(rule)
        logger.info(f"Added anonymization rule: {description}")
    
    def remove_rule(self, description: str) -> bool:
        """
        Remove anonymization rule by description
        
        Args:
            description: Description of rule to remove
            
        Returns:
            True if rule was removed
        """
        original_count = len(self.anonymization_rules)
        self.anonymization_rules = [
            rule for rule in self.anonymization_rules if rule.description != description
        ]
        removed = len(self.anonymization_rules) < original_count
        if removed:
            logger.info(f"Removed anonymization rule: {description}")
        return removed
    
    def get_rules(self) -> List[Dict[str, str]]:
        """Get list of anonymization rules"""
        return [
            {
                "pattern": rule.pattern,
                "replacement": rule.replacement,
                "description": rule.description
            }
            for rule in self.anonymization_rules
        ]
    
    def check_privacy_compliance(self, text: str) -> Dict[str, Any]:
        """
        Check if text contains potentially sensitive information
        
        Args:
            text: Text to check
            
        Returns:
            Dictionary with compliance information
        """
        findings = []
        
        for rule in self.anonymization_rules:
            matches = re.findall(rule.pattern, text, flags=re.IGNORECASE)
            if matches:
                findings.append({
                    "type": rule.description,
                    "count": len(matches),
                    "pattern": rule.pattern
                })
        
        return {
            "compliant": len(findings) == 0,
            "findings": findings,
            "recommendation": "Anonymize data before sharing" if findings else "No sensitive data detected"
        }
    
    def anonymize_conversation(self, conversation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Anonymize a conversation
        
        Args:
            conversation: Conversation dictionary
            
        Returns:
            Anonymized conversation
        """
        anonymized = conversation.copy()
        
        # Anonymize messages
        if "messages" in anonymized:
            anonymized["messages"] = [
                {
                    **msg,
                    "content": self.anonymize(msg.get("content", ""))
                }
                for msg in anonymized["messages"]
            ]
        
        # Anonymize metadata
        if "metadata" in anonymized:
            metadata = anonymized["metadata"].copy()
            for key, value in metadata.items():
                if isinstance(value, str):
                    metadata[key] = self.anonymize(value)
            anonymized["metadata"] = metadata
        
        return anonymized

