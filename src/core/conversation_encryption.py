"""
Conversation Encryption - Encrypt conversations at rest
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import logging

from .key_manager import KeyManager

logger = logging.getLogger(__name__)


class ConversationEncryption:
    """Encrypts and decrypts conversations"""
    
    def __init__(self, key_manager: Optional[KeyManager] = None):
        """
        Initialize conversation encryption
        
        Args:
            key_manager: Optional KeyManager instance (uses its encryption key)
        """
        if key_manager:
            self.key_manager = key_manager
            # Use the same encryption key as API keys
            self._cipher = Fernet(key_manager._encryption_key)
        else:
            # Create standalone encryption
            self.key_manager = KeyManager()
            self._cipher = Fernet(self.key_manager._encryption_key)
    
    def encrypt_conversation(self, conversation: Dict[str, Any]) -> bytes:
        """
        Encrypt a conversation
        
        Args:
            conversation: Conversation dictionary
            
        Returns:
            Encrypted bytes
        """
        try:
            # Serialize to JSON
            json_data = json.dumps(conversation, ensure_ascii=False)
            
            # Encrypt
            encrypted = self._cipher.encrypt(json_data.encode('utf-8'))
            
            return encrypted
        except Exception as e:
            logger.error(f"Error encrypting conversation: {e}")
            raise
    
    def decrypt_conversation(self, encrypted_data: bytes) -> Dict[str, Any]:
        """
        Decrypt a conversation
        
        Args:
            encrypted_data: Encrypted bytes
            
        Returns:
            Decrypted conversation dictionary
        """
        try:
            # Decrypt
            decrypted = self._cipher.decrypt(encrypted_data)
            
            # Deserialize from JSON
            conversation = json.loads(decrypted.decode('utf-8'))
            
            return conversation
        except Exception as e:
            logger.error(f"Error decrypting conversation: {e}")
            raise
    
    def save_encrypted(self, conversation: Dict[str, Any], file_path: Path) -> bool:
        """
        Save encrypted conversation to file
        
        Args:
            conversation: Conversation dictionary
            file_path: Path to save encrypted file
            
        Returns:
            True if successful
        """
        try:
            encrypted = self.encrypt_conversation(conversation)
            
            with open(file_path, 'wb') as f:
                f.write(encrypted)
            
            # Restrict permissions
            file_path.chmod(0o600)
            
            logger.info(f"Saved encrypted conversation to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving encrypted conversation: {e}")
            return False
    
    def load_encrypted(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        Load and decrypt conversation from file
        
        Args:
            file_path: Path to encrypted file
            
        Returns:
            Decrypted conversation or None if error
        """
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'rb') as f:
                encrypted = f.read()
            
            conversation = self.decrypt_conversation(encrypted)
            return conversation
        except Exception as e:
            logger.error(f"Error loading encrypted conversation: {e}")
            return None

