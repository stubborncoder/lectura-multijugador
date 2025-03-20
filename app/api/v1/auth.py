from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, EmailStr
from typing import Optional
import logging
import traceback
from app.database import supabase
from app.auth.auth import get_current_user
from gotrue.errors import AuthApiError

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

# Models for authentication
class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserRegistration(BaseModel):
    email: EmailStr
    password: str
    nombre: Optional[str] = None
    apellidos: Optional[str] = None

class UserResponse(BaseModel):
    id: str
    email: str
    nombre: Optional[str] = None
    apellidos: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    email_confirmed: bool = False
    message: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"

class RefreshToken(BaseModel):
    refresh_token: str

# Endpoints
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserRegistration):
    """
    Register a new user.
    """
    try:
        logger.info(f"Attempting to register user with email: {user_data.email}")
        
        # Prepare user metadata
        user_metadata = {}
        if user_data.nombre:
            user_metadata["nombre"] = user_data.nombre
        if user_data.apellidos:
            user_metadata["apellidos"] = user_data.apellidos
        
        logger.info(f"User metadata: {user_metadata}")
        
        # Create registration data following the exact format from the example
        registration_data = {
            'email': user_data.email,
            'password': user_data.password
        }
        
        # Only add options if we have metadata
        if user_metadata:
            registration_data['options'] = {
                'data': user_metadata
            }
        
        logger.info(f"Registration data: {registration_data}")
        
        # Register the user with Supabase
        auth_response = supabase.auth.sign_up(registration_data)
        
        logger.info("Auth response received")
        
        if not auth_response.user:
            logger.error("No user returned in auth response")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se pudo registrar el usuario"
            )
        
        # Return user information and tokens
        result = {
            "id": auth_response.user.id,
            "email": auth_response.user.email,
            "nombre": user_metadata.get("nombre"),
            "apellidos": user_metadata.get("apellidos"),
            "access_token": auth_response.session.access_token if auth_response.session else None,
            "refresh_token": auth_response.session.refresh_token if auth_response.session else None,
            "email_confirmed": auth_response.user.email_confirmed_at is not None,
            "message": "Usuario registrado correctamente. Por favor, confirma tu correo electrónico antes de iniciar sesión."
        }
        logger.info(f"Registration successful for user: {result['email']}")
        return result
    except Exception as e:
        logger.error(f"Error registering user: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al registrar usuario: {str(e)}"
        )

@router.post("/login", response_model=UserResponse)
def login(user_data: UserLogin):
    """
    Login with email and password.
    """
    try:
        logger.info(f"Attempting to login user with email: {user_data.email}")
        
        # Create login data following the same format
        login_data = {
            'email': user_data.email,
            'password': user_data.password
        }
        
        logger.info(f"Login data: {login_data}")
        
        try:
            # Sign in with Supabase
            auth_response = supabase.auth.sign_in_with_password(login_data)
            
            logger.info("Auth response received")
            
            if not auth_response.user:
                logger.error("No user returned in auth response")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Credenciales inválidas"
                )
            
            user_metadata = auth_response.user.user_metadata or {}
            
            result = {
                "id": auth_response.user.id,
                "email": auth_response.user.email,
                "nombre": user_metadata.get("nombre"),
                "apellidos": user_metadata.get("apellidos"),
                "access_token": auth_response.session.access_token,
                "refresh_token": auth_response.session.refresh_token,
                "email_confirmed": True
            }
            logger.info(f"Login successful for user: {result['email']}")
            return result
            
        except AuthApiError as e:
            if "Email not confirmed" in str(e):
                logger.warning(f"Login attempt with unconfirmed email: {user_data.email}")
                
                # Try to get user info without authentication
                user = None
                try:
                    # We can't get user info without being authenticated, so we'll return a partial response
                    result = {
                        "id": "",
                        "email": user_data.email,
                        "email_confirmed": False,
                        "message": "Por favor, confirma tu correo electrónico antes de iniciar sesión."
                    }
                    return result
                except Exception as inner_e:
                    logger.error(f"Error getting user info: {str(inner_e)}")
                    
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Por favor, confirma tu correo electrónico antes de iniciar sesión."
                )
            else:
                raise e
                
    except AuthApiError as e:
        logger.error(f"Auth API error during login: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Error al iniciar sesión: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error logging in: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Error al iniciar sesión: {str(e)}"
        )

@router.post("/refresh-token", response_model=TokenResponse)
def refresh_token(token_data: RefreshToken):
    """
    Refresh the access token using a refresh token.
    """
    try:
        logger.info("Attempting to refresh token")
        
        # Refresh the session with Supabase
        auth_response = supabase.auth.refresh_session(token_data.refresh_token)
        
        logger.info("Auth response received")
        
        if not auth_response.session:
            logger.error("No session returned in auth response")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No se pudo refrescar el token"
            )
        
        result = {
            "access_token": auth_response.session.access_token,
            "refresh_token": auth_response.session.refresh_token,
            "token_type": "bearer"
        }
        logger.info("Token refresh successful")
        return result
    except Exception as e:
        logger.error(f"Error refreshing token: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Error al refrescar el token: {str(e)}"
        )

@router.post("/logout")
def logout(user = Depends(get_current_user)):
    """
    Logout the current user.
    """
    try:
        logger.info(f"Attempting to logout user: {user.get('email')}")
        
        # Sign out with Supabase
        supabase.auth.sign_out()
        
        logger.info("Logout successful")
        return {"message": "Sesión cerrada correctamente"}
    except Exception as e:
        logger.error(f"Error logging out: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al cerrar sesión: {str(e)}"
        )

@router.get("/me", response_model=dict)
def get_me(user = Depends(get_current_user)):
    """
    Get current user information.
    """
    logger.info(f"Getting user information for: {user.get('email')}")
    return user
