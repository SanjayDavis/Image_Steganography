from cryptography.fernet import Fernet


def generate_key() -> str:
    return Fernet.generate_key().decode()


def encrypt_bytes(data: bytes, key: str) -> str:
    fernet = Fernet(key.encode())
    return fernet.encrypt(data).decode()


def decrypt_to_bytes(data_encrypted: bytes, key: str) -> bytes:
    fernet = Fernet(key.encode())
    return fernet.decrypt(data_encrypted)


