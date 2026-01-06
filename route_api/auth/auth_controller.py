"""
Authentication Controller
Handles HTTP requests for user authentication (login)
"""
from flask import Blueprint, request
from auth.auth_service import login_user
from utils.response_utils import success_response, error_response

# Create blueprint for authentication routes
auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login", methods=["POST"])
def login():
    """
    User login endpoint
    Accepts: JSON with 'username' and 'password'
    Returns: Standardized response with status, message, and data (token)
    """
    try:
        # Validate request has JSON data
        if not request.json:
            return error_response(
                message="Request body is required",
                data=None,
                status_code=400
            )
        
        # Get credentials from request body
        token = login_user(request.json)
        
        # If login fails, return error
        if not token:
            return error_response(
                message="Invalid credentials",
                data=None,
                status_code=401
            )

        # Return JWT token on successful login
        return success_response(
            message="Login successful",
            data={"token": token},
            status_code=200
        )
    except Exception as e:
        return error_response(
            message="Login failed",
            data={"error": str(e)},
            status_code=401
        )
