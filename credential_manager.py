# credential_manager.py
import os
import logging
import getpass
from pathlib import Path
import json
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Path to store encrypted credentials
CREDENTIALS_FILE = Path("secure_credentials.enc")
SALT_FILE = Path("salt.bin")

def generate_key(password, salt=None):
    """Generate encryption key from password and salt"""
    if salt is None:
        salt = os.urandom(16)
        with open(SALT_FILE, "wb") as f:
            f.write(salt)
    
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key, salt

def encrypt_credentials(credentials, master_password):
    """Encrypt credentials dictionary with master password"""
    try:
        key, salt = generate_key(master_password)
        fernet = Fernet(key)
        encrypted_data = fernet.encrypt(json.dumps(credentials).encode())
        
        with open(CREDENTIALS_FILE, "wb") as f:
            f.write(encrypted_data)
        
        logger.info("Credentials encrypted and saved successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to encrypt credentials: {str(e)}")
        return False

def decrypt_credentials(master_password):
    """Decrypt credentials using master password"""
    try:
        if not CREDENTIALS_FILE.exists() or not SALT_FILE.exists():
            logger.error("Credential files not found")
            return None
        
        with open(SALT_FILE, "rb") as f:
            salt = f.read()
        
        key, _ = generate_key(master_password, salt)
        fernet = Fernet(key)
        
        with open(CREDENTIALS_FILE, "rb") as f:
            encrypted_data = f.read()
        
        decrypted_data = fernet.decrypt(encrypted_data)
        return json.loads(decrypted_data)
    except Exception as e:
        logger.error(f"Failed to decrypt credentials: {str(e)}")
        return None

def get_outlook_credentials():
    """Get Outlook credentials securely"""
    # First try to get from environment (for development/testing)
    email = os.getenv('OUTLOOK_EMAIL')
    
    # Try to get from encrypted storage
    if CREDENTIALS_FILE.exists():
        # In a real app, you'd prompt for master password
        # For this example, we'll use a default one
        master_password = getpass.getpass("Enter master password: ")
        creds = decrypt_credentials(master_password)
        if creds and 'outlook_password' in creds:
            return email, creds['outlook_password']
    
    # If not available, prompt user
    if not email:
        email = input("Enter Outlook email: ")
    password = getpass.getpass("Enter Outlook password: ")
    
    # Save for future use
    save = input("Save credentials for future use? (y/n): ").lower() == 'y'
    if save:
        master_password = getpass.getpass("Create master password: ")
        encrypt_credentials({'outlook_password': password}, master_password)
    
    return email, password

def setup_credentials():
    """Initial setup for credentials"""
    print("Setting up secure credentials storage")
    email = input("Enter Outlook email: ")
    password = getpass.getpass("Enter Outlook password: ")
    master_password = getpass.getpass("Create master password: ")
    
    credentials = {
        'outlook_password': password
    }
    
    if encrypt_credentials(credentials, master_password):
        print("Credentials securely stored. You'll need your master password to access them.")
        # Update .env with email only
        update_env_email(email)
    else:
        print("Failed to store credentials securely.")

def update_env_email(email):
    """Update .env file with email only"""
    env_path = Path(".env")
    if env_path.exists():
        with open(env_path, "r") as f:
            lines = f.readlines()
        
        with open(env_path, "w") as f:
            for line in lines:
                if line.startswith("OUTLOOK_EMAIL="):
                    f.write(f"OUTLOOK_EMAIL={email}\n")
                elif not line.startswith("OUTLOOK_PASSWORD="):
                    f.write(line)
        
        logger.info("Updated .env file with email only")

if __name__ == "__main__":
    # Run this file directly to set up credentials
    setup_credentials()