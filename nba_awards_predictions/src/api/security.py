#src/api/security.py

from fastapi import HTTPException, Security
from fastapi.security.api_key import APIKeyHeader
from dotenv import load_dotenv
import os

API_KEY_NAME = "X-API-Key"
API_KEY = os.getenv("API_SECRET_KEY")

api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def verify_api_key(api_key: str = Security(api_key_header)):
    """
    Function for adding security checks to main.py 

    Args:
        api_key (str, optional): The API key needed for the app Defaults to Security(api_key_header).

    Raises:
        HTTPException: Key not configured
        HTTPException: Unauthorized use of app
    """
    if API_KEY is None:
        raise HTTPException(status_code=500, detail="API key not configured.")
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Unauthorized")
