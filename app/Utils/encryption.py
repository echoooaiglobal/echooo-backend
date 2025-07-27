# app/Utils/encryption.py
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import os
from config.settings import settings

class TokenEncryption:
    """Utility class for encrypting and decrypting OAuth tokens"""
    
    def __init__(self):
        self.key = self._get_encryption_key()
        self.cipher = Fernet(self.key)
    
    def _get_encryption_key(self) -> bytes:
        """Generate or retrieve encryption key"""
        # In production, store this securely (e.g., environment variable, key management service)
        password = settings.SECRET_KEY.encode()
        salt = b'salt_for_oauth_tokens'  # In production, use a random salt stored securely
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        return key
    
    def encrypt(self, token: str) -> str:
        """Encrypt a token"""
        if not token:
            return None
        encrypted_token = self.cipher.encrypt(token.encode())
        return base64.urlsafe_b64encode(encrypted_token).decode()
    
    def decrypt(self, encrypted_token: str) -> str:
        """Decrypt a token"""
        if not encrypted_token:
            return None
        try:
            decoded_token = base64.urlsafe_b64decode(encrypted_token.encode())
            decrypted_token = self.cipher.decrypt(decoded_token)
            return decrypted_token.decode()
        except Exception as e:
            # Log error and return None for invalid tokens
            from app.Utils.Logger import logger
            logger.error(f"Failed to decrypt token: {str(e)}")
            return None

# Global instance
_encryption = TokenEncryption()

def encrypt_token(token: str) -> str:
    """Encrypt a token string"""
    return _encryption.encrypt(token)

def decrypt_token(encrypted_token: str) -> str:
    """Decrypt an encrypted token string"""
    return _encryption.decrypt(encrypted_token)