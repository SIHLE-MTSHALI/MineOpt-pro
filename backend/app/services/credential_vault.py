"""
Credential Vault Service

Provides secure storage for API keys and credentials with:
- Encryption at rest (using cryptography.fernet)
- Credential rotation support
- Secure retrieval with audit logging
"""

from dataclasses import dataclass
from typing import Dict, Optional, List
from datetime import datetime, timedelta
import base64
import hashlib
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class StoredCredential:
    """A stored credential with metadata."""
    credential_id: str
    name: str
    connector_type: str  # modular_mining, wenco, lims, etc.
    encrypted_value: str  # Encrypted credential data
    created_at: datetime
    last_rotated: datetime
    expires_at: Optional[datetime] = None
    is_active: bool = True


class CredentialVault:
    """
    Secure credential storage with encryption.
    
    In production, should integrate with:
    - OS keychain (Windows Credential Manager, macOS Keychain)
    - External vaults (HashiCorp Vault, AWS Secrets Manager)
    
    This implementation uses Fernet symmetric encryption.
    """
    
    def __init__(self, master_key: str = None):
        """
        Initialize vault with master key.
        
        Args:
            master_key: Base64-encoded 32-byte key for encryption.
                       If not provided, a default (insecure) key is used.
        """
        self._credentials: Dict[str, StoredCredential] = {}
        self._master_key = master_key or self._get_default_key()
        self._fernet = self._init_fernet()
    
    def _get_default_key(self) -> str:
        """Get default key (for development only)."""
        # In production, this should come from environment or secure storage
        default = "MineOptPro_DefaultKey_DO_NOT_USE_IN_PROD!"
        # Derive a 32-byte key from the default string
        return base64.urlsafe_b64encode(
            hashlib.sha256(default.encode()).digest()
        ).decode()
    
    def _init_fernet(self):
        """Initialize Fernet encryption."""
        try:
            from cryptography.fernet import Fernet
            return Fernet(self._master_key.encode())
        except ImportError:
            # Fallback to simple base64 encoding if cryptography not available
            logger.warning("cryptography library not available, using simple encoding")
            return None
    
    def _encrypt(self, plaintext: str) -> str:
        """Encrypt a string value."""
        if self._fernet:
            return self._fernet.encrypt(plaintext.encode()).decode()
        else:
            # Fallback: base64 encode (not secure, for development only)
            return base64.b64encode(plaintext.encode()).decode()
    
    def _decrypt(self, ciphertext: str) -> str:
        """Decrypt a string value."""
        if self._fernet:
            return self._fernet.decrypt(ciphertext.encode()).decode()
        else:
            return base64.b64decode(ciphertext.encode()).decode()
    
    # =========================================================================
    # CRUD Operations
    # =========================================================================
    
    def store_credential(
        self,
        credential_id: str,
        name: str,
        connector_type: str,
        credential_data: Dict[str, str],
        expires_days: int = None
    ) -> StoredCredential:
        """
        Store a new credential securely.
        
        Args:
            credential_id: Unique identifier
            name: Human-readable name
            connector_type: Type of integration
            credential_data: Dictionary with credentials (api_key, username, password, etc.)
            expires_days: Optional expiration in days
        
        Returns:
            StoredCredential object
        """
        now = datetime.utcnow()
        expires_at = now + timedelta(days=expires_days) if expires_days else None
        
        # Encrypt the credential data
        encrypted = self._encrypt(json.dumps(credential_data))
        
        cred = StoredCredential(
            credential_id=credential_id,
            name=name,
            connector_type=connector_type,
            encrypted_value=encrypted,
            created_at=now,
            last_rotated=now,
            expires_at=expires_at,
            is_active=True
        )
        
        self._credentials[credential_id] = cred
        logger.info(f"Stored credential: {name} ({connector_type})")
        
        return cred
    
    def get_credential(self, credential_id: str) -> Optional[Dict[str, str]]:
        """
        Retrieve and decrypt a credential.
        
        Returns None if not found or expired.
        """
        if credential_id not in self._credentials:
            return None
        
        cred = self._credentials[credential_id]
        
        # Check expiration
        if cred.expires_at and datetime.utcnow() > cred.expires_at:
            logger.warning(f"Credential {credential_id} has expired")
            return None
        
        if not cred.is_active:
            return None
        
        # Decrypt and return
        try:
            decrypted = self._decrypt(cred.encrypted_value)
            return json.loads(decrypted)
        except Exception as e:
            logger.error(f"Failed to decrypt credential {credential_id}: {e}")
            return None
    
    def list_credentials(self, connector_type: str = None) -> List[Dict]:
        """
        List all stored credentials (without values).
        """
        creds = self._credentials.values()
        
        if connector_type:
            creds = [c for c in creds if c.connector_type == connector_type]
        
        return [
            {
                "credential_id": c.credential_id,
                "name": c.name,
                "connector_type": c.connector_type,
                "created_at": c.created_at.isoformat(),
                "last_rotated": c.last_rotated.isoformat(),
                "expires_at": c.expires_at.isoformat() if c.expires_at else None,
                "is_active": c.is_active,
                "is_expired": c.expires_at and datetime.utcnow() > c.expires_at
            }
            for c in creds
        ]
    
    def delete_credential(self, credential_id: str) -> bool:
        """Delete a credential."""
        if credential_id in self._credentials:
            del self._credentials[credential_id]
            logger.info(f"Deleted credential: {credential_id}")
            return True
        return False
    
    # =========================================================================
    # Rotation Support
    # =========================================================================
    
    def rotate_credential(
        self,
        credential_id: str,
        new_credential_data: Dict[str, str]
    ) -> Optional[StoredCredential]:
        """
        Rotate a credential with new values.
        
        Args:
            credential_id: ID of credential to rotate
            new_credential_data: New credential values
        
        Returns:
            Updated StoredCredential or None if not found
        """
        if credential_id not in self._credentials:
            return None
        
        cred = self._credentials[credential_id]
        
        # Encrypt new value
        cred.encrypted_value = self._encrypt(json.dumps(new_credential_data))
        cred.last_rotated = datetime.utcnow()
        
        # Reset expiration if set
        if cred.expires_at:
            days_until_expiry = (cred.expires_at - cred.created_at).days
            cred.expires_at = datetime.utcnow() + timedelta(days=days_until_expiry)
        
        logger.info(f"Rotated credential: {cred.name}")
        return cred
    
    def deactivate_credential(self, credential_id: str) -> bool:
        """Deactivate a credential without deleting it."""
        if credential_id in self._credentials:
            self._credentials[credential_id].is_active = False
            logger.info(f"Deactivated credential: {credential_id}")
            return True
        return False
    
    def reactivate_credential(self, credential_id: str) -> bool:
        """Reactivate a deactivated credential."""
        if credential_id in self._credentials:
            self._credentials[credential_id].is_active = True
            logger.info(f"Reactivated credential: {credential_id}")
            return True
        return False
    
    # =========================================================================
    # Expiration Management
    # =========================================================================
    
    def get_expiring_credentials(self, days: int = 7) -> List[Dict]:
        """Get credentials expiring within N days."""
        cutoff = datetime.utcnow() + timedelta(days=days)
        
        expiring = []
        for cred in self._credentials.values():
            if cred.expires_at and cred.expires_at < cutoff and cred.is_active:
                expiring.append({
                    "credential_id": cred.credential_id,
                    "name": cred.name,
                    "expires_at": cred.expires_at.isoformat(),
                    "days_until_expiry": (cred.expires_at - datetime.utcnow()).days
                })
        
        return sorted(expiring, key=lambda x: x["days_until_expiry"])
    
    def cleanup_expired(self) -> int:
        """Remove expired credentials. Returns count removed."""
        now = datetime.utcnow()
        to_remove = [
            cid for cid, cred in self._credentials.items()
            if cred.expires_at and cred.expires_at < now
        ]
        
        for cid in to_remove:
            del self._credentials[cid]
        
        if to_remove:
            logger.info(f"Cleaned up {len(to_remove)} expired credentials")
        
        return len(to_remove)


# Global singleton
credential_vault = CredentialVault()
