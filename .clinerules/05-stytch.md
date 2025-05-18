# Stytch Authentication

Stytch is a developer platform for authentication and user management that provides flexible, secure, and user-friendly authentication solutions.

## Key Features

- **Passwordless Authentication**: Email magic links, SMS passcodes, WhatsApp passcodes
- **OAuth**: Social login with Google, Apple, Microsoft, GitHub, etc.
- **Biometric Authentication**: WebAuthn/Passkeys support
- **Multi-factor Authentication (MFA)**: Add additional security layers
- **Session Management**: Secure, configurable sessions
- **User Management**: Create, update, delete users and manage their authentication methods
- **Organizations**: B2B features for team-based access

## Project Usage Patterns

In our project, Stytch is used for:

1. User authentication via email magic links
2. Multi-layered session management with cookies, localStorage, and Authorization headers
3. User profile management
4. Secure access control to protected routes
5. JWT and session token validation

## Common Patterns

### Email Magic Link Authentication

```python
import stytch
from fastapi import APIRouter, Request, Response

router = APIRouter()

# Initialize Stytch client
client = stytch.Client(
    project_id="project-live-123",
    secret="secret-live-456",
)

@router.post("/login")
async def login(request: Request):
    data = await request.json()
    email = data.get("email")
    
    try:
        # Send a magic link to the user's email
        response = client.magic_links.email.login_or_create(
            email=email,
            login_magic_link_url="https://example.com/authenticate",
            signup_magic_link_url="https://example.com/authenticate",
        )
        return {"success": True, "message": "Magic link sent"}
    except Exception as e:
        return {"error": str(e)}

@router.get("/authenticate")
async def authenticate(request: Request, response: Response, token: str):
    try:
        # Authenticate the magic link token
        auth_response = client.magic_links.authenticate(token=token)
        
        # Set session cookie
        response.set_cookie(
            key="stytch_session",
            value=auth_response.session_token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=86400,  # 24 hours
        )
        
        return {"success": True, "user_id": auth_response.user_id}
    except Exception as e:
        return {"error": str(e)}
```

### Multi-Layered Session Management

Our application uses a robust multi-layered approach to session management:

```python
async def get_authenticated_user(request: Request):
    """
    Get the authenticated user from the session.
    
    Checks multiple sources for the authentication token:
    1. Cookies
    2. Request state (set by AuthHeaderMiddleware from Authorization header)
    
    Returns None if the user is not authenticated.
    """
    # First check if we have a token in the cookies
    stytch_session = request.cookies.get(STYTCH_COOKIE_NAME)
    
    # If no cookie, check Authorization header (set by client-side JavaScript)
    if not stytch_session and hasattr(request.state, 'auth_token'):
        stytch_session = request.state.auth_token
    
    if not stytch_session:
        return None

    try:
        # Try session token authentication
        if stytch_session.startswith('session-'):
            resp = stytch_client.sessions.authenticate(session_token=stytch_session)
        else:
            # Try JWT authentication as fallback
            resp = stytch_client.sessions.authenticate_jwt(session_jwt=stytch_session)
        
        return resp.user
    except StytchError:
        # Handle authentication errors
        return None
```

### Authorization Header Middleware

```python
class AuthHeaderMiddleware(BaseHTTPMiddleware):
    """
    Middleware to check for Authorization header and set the token in request state.
    
    This helps bridge the gap between localStorage token storage and server-side authentication.
    """
    
    async def dispatch(self, request: Request, call_next):
        # Check if there's an Authorization header
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            # Extract the token and store it in request state
            token = auth_header.replace('Bearer ', '')
            request.state.auth_token = token
        
        # Continue processing the request
        response = await call_next(request)
        return response
```

### OAuth Integration

```python
@router.get("/oauth/start")
async def start_oauth(request: Request, provider: str):
    try:
        # Start OAuth flow
        redirect_url = client.oauth.start(
            provider=provider,
            redirect_url="https://example.com/oauth/callback",
        )
        return {"redirect_url": redirect_url}
    except Exception as e:
        return {"error": str(e)}

@router.get("/oauth/callback")
async def oauth_callback(request: Request, response: Response, token: str):
    try:
        # Authenticate the OAuth token
        auth_response = client.oauth.authenticate(token=token)
        
        # Set session cookie
        response.set_cookie(
            key="stytch_session",
            value=auth_response.session_token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=86400,  # 24 hours
        )
        
        return {"success": True, "user_id": auth_response.user_id}
    except Exception as e:
        return {"error": str(e)}
```

### Client-Side Token Management

```javascript
// Add auth token to fetch requests
function addAuthTokenToFetch() {
    // Store the original fetch function
    const originalFetch = window.fetch;
    
    // Override the fetch function
    window.fetch = function(url, options = {}) {
        // Create headers if they don't exist
        options.headers = options.headers || {};
        
        // If we have an auth token in localStorage, add it to the request headers
        const authToken = localStorage.getItem('stytch_session_token');
        if (authToken) {
            // Add Authorization header with Bearer token
            if (!(options.headers instanceof Headers)) {
                const headers = new Headers(options.headers);
                headers.append('Authorization', `Bearer ${authToken}`);
                options.headers = headers;
            } else {
                options.headers.append('Authorization', `Bearer ${authToken}`);
            }
        }
        
        // Include credentials to send cookies with the request
        options.credentials = 'include';
        
        // Call the original fetch with the modified options
        return originalFetch(url, options);
    };
}
```

### Comprehensive Logout

```python
@router.get("/logout")
async def logout(response: Response) -> RedirectResponse:
    # Clear HTTP-only cookie
    cookie_clear_settings = {
        "key": STYTCH_COOKIE_NAME,
        "path": "/",
        "samesite": "lax"
    }
    
    # Clear JS-accessible cookie
    js_cookie_clear_settings = {
        "key": STYTCH_SESSION_JS_COOKIE_NAME,
        "path": "/",
        "samesite": "lax"
    }
    
    # Add secure setting in production
    if is_production():
        cookie_clear_settings["secure"] = True
        js_cookie_clear_settings["secure"] = True
    
    # Clear cookies
    response.delete_cookie(**cookie_clear_settings)
    response.delete_cookie(**js_cookie_clear_settings)
    
    # Add script to clear localStorage session data
    logout_script = """
    <script>
        // Clear session data from localStorage
        localStorage.removeItem('pathlight_session');
        localStorage.removeItem('pathlight_session_created');
        localStorage.removeItem('pathlight_user_id');
        localStorage.removeItem('pathlight_user_email');
        localStorage.removeItem('stytch_session_token');
    </script>
    """
    
    # Create response with the logout script
    response = RedirectResponse(url="/")
    response.headers["HX-Trigger"] = logout_script
    return response
```

## Best Practices Implemented

1. **Multi-Layered Authentication**:
   - HTTP-only cookies for secure token storage
   - localStorage for client-side awareness of authentication state
   - Authorization headers for API requests
   - Fallback mechanisms when one method fails

2. **Environment-Specific Security**:
   - `secure=True` for cookies in production (HTTPS) environments
   - `samesite="lax"` to allow cookies to be sent with same-site navigations
   - Consistent cookie settings throughout the authentication flow

3. **Robust Error Handling**:
   - Detailed logging for troubleshooting
   - Graceful degradation when authentication fails
   - User-friendly error messages
   - Recovery mechanisms for expired sessions

4. **Enhanced User Experience**:
   - Automatic session checking
   - Smart redirects based on authentication state
   - Clean loading spinner during authentication
   - Seamless token renewal

## Documentation Links

- [Stytch Documentation](https://stytch.com/docs)
- [Stytch API Reference](https://stytch.com/docs/api)
- [Stytch Python SDK](https://github.com/stytchauth/stytch-python)
- [Stytch Magic Links](https://stytch.com/docs/api/magic-links-overview)
- [Stytch OAuth](https://stytch.com/docs/api/oauth-overview)
- [Stytch Sessions](https://stytch.com/docs/api/session-management)
