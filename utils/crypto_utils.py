"""
Cryptographic utilities using Fernet symmetric encryption.
"""

from cryptography.fernet import Fernet


def generate_key() -> str:
    """Generate a new Fernet encryption key (URL-safe base-64 encoded)."""
    return Fernet.generate_key().decode()


def encrypt_bytes(data: bytes, key: str) -> str:
    """
    Encrypt raw bytes with a Fernet key.

    Args:
        data: Raw bytes to encrypt.
        key:  Fernet key string (from :func:`generate_key`).

    Returns:
        Base-64 encoded ciphertext string.
    """
    fernet = Fernet(key.encode())
    return fernet.encrypt(data).decode()


def decrypt_to_bytes(data_encrypted: bytes, key: str) -> bytes:
    """
    Decrypt ciphertext produced by :func:`encrypt_bytes`.

    Args:
        data_encrypted: Ciphertext bytes or string.
        key:            Fernet key string.

    Returns:
        Decrypted raw bytes.
    """
    fernet = Fernet(key.encode())
    return fernet.decrypt(data_encrypted)
