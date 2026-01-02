from datetime import datetime, timedelta
from typing import Optional
# from jose import jwt
# from passlib.context import CryptContext

# MOCKING AUTH LIBS to avoid pip install issues in restricted env
# In a real app, user must run `pip install python-jose[cryptography] passlib[bcrypt]`

class AuthService:
    # SECRET_KEY = "SECRET"
    # ALGORITHM = "HS256"
    
    @staticmethod
    def verify_password(plain_password, hashed_password):
        return plain_password == hashed_password # Mock!

    @staticmethod
    def get_password_hash(password):
        return password # Mock!

    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
        # Mock Token
        import json
        import base64
        # Create a fake JWT looking string
        return f"mock-token.{base64.b64encode(json.dumps(data).encode()).decode()}"

    @staticmethod
    def decode_token(token: str):
        if not token.startswith("mock-token."): return None
        import json
        import base64
        try:
            payload = token.split(".")[1]
            return json.loads(base64.b64decode(payload).decode())
        except:
            return None
