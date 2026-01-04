"""
Key Manager - Secure API key storage and encryption
"""

import os
import base64
from pathlib import Path
from typing import Optional, Dict, Any
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import logging

logger = logging.getLogger(__name__)


class KeyManager:
    """Manages secure storage and encryption of API keys"""
    
    def __init__(self, keys_dir: Optional[Path] = None):
        """
        Initialize key manager
        
        Args:
            keys_dir: Directory for storing encrypted keys (default: ~/.localmind/keys)
        """
        if keys_dir is None:
            keys_dir = Path.home() / ".localmind" / "keys"
        
        self.keys_dir = keys_dir
        self.keys_dir.mkdir(parents=True, exist_ok=True)
        self.keys_dir.chmod(0o700)  # Restrict permissions
        
        # Get or create encryption key
        self._encryption_key = self._get_or_create_encryption_key()
        self._cipher = Fernet(self._encryption_key)
    
    def _get_or_create_encryption_key(self) -> bytes:
        """
        Get or create encryption key for API keys
        
        Returns:
            Fernet encryption key
        """
        key_file = self.keys_dir / ".master_key"
        
        if key_file.exists():
            try:
                with open(key_file, 'rb') as f:
                    return f.read()
            except Exception as e:
                logger.warning(f"Error reading master key: {e}, creating new one")
        
        # Create new key
        key = Fernet.generate_key()
        try:
            with open(key_file, 'wb') as f:
                f.write(key)
            key_file.chmod(0o600)  # Restrict permissions
        except Exception as e:
            logger.error(f"Error saving master key: {e}")
        
        return key
    
    def _derive_key_from_password(self, password: str, salt: bytes) -> bytes:
        """Derive encryption key from password"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
    
    def encrypt_key(self, api_key: str, provider: str) -> bool:
        """
        Encrypt and store API key
        
        Args:
            api_key: API key to encrypt
            provider: Provider name (e.g., 'openai', 'anthropic')
            
        Returns:
            True if successful
        """
        try:
            encrypted = self._cipher.encrypt(api_key.encode())
            key_file = self.keys_dir / f"{provider}.key"
            
            with open(key_file, 'wb') as f:
                f.write(encrypted)
            key_file.chmod(0o600)  # Restrict permissions
            
            logger.info(f"Encrypted API key for {provider}")
            return True
        except Exception as e:
            logger.error(f"Error encrypting key for {provider}: {e}")
            return False
    
    def decrypt_key(self, provider: str) -> Optional[str]:
        """
        Decrypt and retrieve API key
        
        Args:
            provider: Provider name
            
        Returns:
            Decrypted API key or None if not found/error
        """
        key_file = self.keys_dir / f"{provider}.key"
        
        if not key_file.exists():
            return None
        
        try:
            with open(key_file, 'rb') as f:
                encrypted = f.read()
            
            decrypted = self._cipher.decrypt(encrypted)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Error decrypting key for {provider}: {e}")
            return None
    
    def delete_key(self, provider: str) -> bool:
        """
        Delete encrypted API key
        
        Args:
            provider: Provider name
            
        Returns:
            True if successful
        """
        key_file = self.keys_dir / f"{provider}.key"
        
        if key_file.exists():
            try:
                key_file.unlink()
                logger.info(f"Deleted API key for {provider}")
                return True
            except Exception as e:
                logger.error(f"Error deleting key for {provider}: {e}")
                return False
        
        return False
    
    def has_key(self, provider: str) -> bool:
        """Check if encrypted key exists for provider"""
        key_file = self.keys_dir / f"{provider}.key"
        return key_file.exists()
    
    def list_providers(self) -> list[str]:
        """List all providers with encrypted keys"""
        providers = []
        for key_file in self.keys_dir.glob("*.key"):
            if key_file.name != ".master_key":
                providers.append(key_file.stem)
        return providers
    
    def migrate_from_config(self, config: Dict[str, Any]) -> int:
        """
        Migrate API keys from config to encrypted storage
        
        Args:
            config: Configuration dictionary with backends
            
        Returns:
            Number of keys migrated
        """
        migrated = 0
        
        for backend_name, backend_config in config.get("backends", {}).items():
            api_key = backend_config.get("settings", {}).get("api_key")
            if api_key and not self.has_key(backend_name):
                if self.encrypt_key(api_key, backend_name):
                    migrated += 1
                    # Remove from config (optional - keep for backward compatibility)
                    # backend_config["settings"].pop("api_key", None)
        
        if migrated > 0:
            logger.info(f"Migrated {migrated} API keys to encrypted storage")
        
        return migrated

