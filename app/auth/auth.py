from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from app.database import supabase

# Set up the HTTP Bearer authentication scheme
security = HTTPBearer()

class AuthError(Exception):
    """Exception raised for authentication errors."""
    def __init__(self, message: str, status_code: int = 401):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Verify JWT token and return user information.
    Raises HTTPException if token is invalid.
    """
    try:
        token = credentials.credentials
        
        # Verify the JWT token with Supabase
        # This will throw an exception if the token is invalid
        user_response = supabase.auth.get_user(token)
        
        if not user_response or not user_response.user:
            raise AuthError("Invalid authentication credentials")
        
        return user_response.user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_optional_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[dict]:
    """
    Similar to get_current_user but doesn't raise an exception if no token is provided.
    Returns None if no valid token is provided.
    """
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None
