"""
Authentication Service
Contains business logic for user authentication
Uses stored procedures for database operations (falls back to direct SQL or temporary validation)
"""
from utils.jwt_utils import generate_token
from database.db import execute_stored_procedure

def login_user(data):
    """
    Authenticate user and generate JWT token using stored procedure
    Falls back to direct SQL or temporary hardcoded validation if SP doesn't exist
    Args:
        data: Dictionary containing 'username' and 'password'
    Returns:
        JWT token string if credentials are valid, None otherwise
    """
    # Extract credentials from request data
    username = data.get("username")
    password = data.get("password")

    conn = None
    try:
        # Call stored procedure: sp_User_Login
        # Parameters: @username, @password
        # Returns: user_id if credentials are valid, NULL otherwise
        # commit=False because this is a SELECT/validation operation
        # Fallback SQL if stored procedure doesn't exist
        # Note: Update this SQL to match your Users table structure
        fallback_sql = "SELECT id FROM Users WHERE username = ? AND password = ? AND isActive = 1"
        cursor, conn = execute_stored_procedure(
            "sp_User_Login",
            (username, password),
            commit=False,
            fallback_sql=fallback_sql
        )
        
        # Fetch the result (should return user_id or None)
        result = cursor.fetchone()
        
        if result and result[0]:  # Check if user_id was returned
            user_id = result[0]
            # Generate and return JWT token with user ID
            return generate_token(user_id=user_id)
        
        # If database query returns no result, fall back to hardcoded validation
        # TODO: Remove this once Users table and stored procedure are set up
        if username == "admin" and password == "admin123":
            return generate_token(user_id=1)
        
        # Return None if credentials are invalid
        return None
    except Exception:
        # If database query fails with exception, fall back to temporary hardcoded validation
        # TODO: Remove this once Users table and stored procedure are set up
        if username == "admin" and password == "admin123":
            return generate_token(user_id=1)
        return None
    finally:
        # Always close connection, even if error occurs
        if conn:
            conn.close()
