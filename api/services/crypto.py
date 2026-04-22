import os
import base64
from cryptography.fernet import Fernet
from pathlib import Path
import re

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ENV_PATH = PROJECT_ROOT / ".env"

def _ensure_secret_key() -> bytes:
    """Ensure AEGIS_SECRET_KEY exists in .env, generate if not, and return it."""
    # First, try to get from environment
    secret = os.getenv("AEGIS_SECRET_KEY")
    if secret:
        return secret.encode()
        
    # Second, try to read from .env file directly (if not loaded yet)
    env_content = ""
    if ENV_PATH.exists():
        env_content = ENV_PATH.read_text()
        match = re.search(r"^AEGIS_SECRET_KEY=(.*)$", env_content, re.MULTILINE)
        if match:
            secret = match.group(1).strip()
            os.environ["AEGIS_SECRET_KEY"] = secret
            return secret.encode()
            
    # Third, generate a new key and append to .env
    new_key = Fernet.generate_key().decode()
    
    if env_content and not env_content.endswith("\n"):
        env_content += "\n"
    env_content += f"AEGIS_SECRET_KEY={new_key}\n"
    
    ENV_PATH.write_text(env_content)
    os.environ["AEGIS_SECRET_KEY"] = new_key
    
    return new_key.encode()

# Initialize Fernet suite globally for the process
_fernet = Fernet(_ensure_secret_key())

def encrypt_key(plain_key: str) -> str:
    """Encrypt a plaintext API key."""
    if not plain_key:
        return plain_key
    return _fernet.encrypt(plain_key.encode()).decode()

def decrypt_key(encrypted_key: str) -> str:
    """Decrypt an encrypted API key."""
    if not encrypted_key:
        return encrypted_key
    try:
        return _fernet.decrypt(encrypted_key.encode()).decode()
    except Exception:
        # If decryption fails, it might be a plaintext key (migration) or invalid
        return encrypted_key
