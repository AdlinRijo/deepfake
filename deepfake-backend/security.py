import os
import json
import secrets
from fastapi import Security, HTTPException, status
from fastapi.security.api_key import APIKeyHeader

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

API_KEYS_FILE = "api_keys.json"

def load_keys():
    if not os.path.exists(API_KEYS_FILE):
        return {}
    try:
        with open(API_KEYS_FILE, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

def save_keys(keys_data):
    with open(API_KEYS_FILE, 'w') as f:
        json.dump(keys_data, f, indent=4)

def generate_api_key_for_company(company_name: str) -> str:
    """Generate a high entropy API key and store it."""
    # Prefix helps easily identify the key type
    new_key = f"df_{secrets.token_urlsafe(32)}"
    
    keys_data = load_keys()
    keys_data[new_key] = {
        "company": company_name,
        "active": True
    }
    save_keys(keys_data)
    return new_key

async def verify_api_key(api_key: str = Security(api_key_header)):
    """FastAPI Dependency for validating the X-API-Key header."""
    if api_key is None:
         raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-API-Key header",
        )
        
    keys_data = load_keys()
    
    # In a real enterprise app we would hash the keys in the DB.
    # For this project, storing raw in JSON is enough.
    key_info = keys_data.get(api_key)
    if not key_info or not key_info.get("active"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or revoked API Key",
        )
        
    return key_info["company"]
