"""
JWT Utility Functions
Handles JWT token generation and validation for authentication
"""
import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request
from utils.response_utils import error_response

# Secret key for signing and verifying JWT tokens
# TODO: Move to environment variable for production
SECRET_KEY = "super_secret_key"

def generate_token(user_id):
    """
    Generate a JWT token for authenticated user
    Args:
        user_id: ID of the user to encode in token
    Returns:
        Encoded JWT token string
    """
    # Create token payload with user ID and expiration time (2 hours)
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(hours=2)
    }
    # Encode and return JWT token
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def token_required(f):
    """
    Decorator to protect routes that require authentication
    Validates JWT token from Authorization header and sets request.user_id
    Usage: @token_required above route function
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        # Get token from Authorization header
        token = request.headers.get("Authorization")

        # Return error if no token provided
        if not token:
            return error_response(
                message="Token required",
                data=None,
                status_code=401
            )

        try:
            # Decode and verify token
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            # Attach user_id to request object for use in route handler
            request.user_id = data["user_id"]
        except:
            # Return error if token is invalid or expired
            return error_response(
                message="Invalid or expired token",
                data=None,
                status_code=401
            )

        # Call the original route function if token is valid
        return f(*args, **kwargs)
    return wrapper
