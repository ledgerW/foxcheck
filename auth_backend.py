from starlette.authentication import AuthenticationBackend, AuthCredentials, SimpleUser
from jose import JWTError, jwt
from config import settings
from fastapi import Request
import logging

logger = logging.getLogger(__name__)

class JWTAuthBackend(AuthenticationBackend):
    async def authenticate(self, request: Request):
        if "Authorization" not in request.headers:
            return None

        auth = request.headers["Authorization"]
        try:
            scheme, token = auth.split()
            if scheme.lower() != 'bearer':
                return None
            
            # Verify the token
            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
                username: str = payload.get("sub")
                if username is None:
                    return None
                
                return AuthCredentials(["authenticated"]), SimpleUser(username)
            except JWTError as e:
                logger.error(f"JWT validation error: {e}")
                return None
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return None
