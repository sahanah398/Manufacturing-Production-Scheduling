"""
Response Utility Functions
Standardized API response format
"""
from flask import jsonify

def success_response(message="Success", data=None, status_code=200):
    """
    Create a standardized success response
    Args:
        message: Success message
        data: Response data (can be dict, list, or None)
        status_code: HTTP status code (default: 200)
    Returns:
        JSON response with status, message, and data
    """
    response = {
        "status": "success",
        "message": message,
        "data": data
    }
    return jsonify(response), status_code

def error_response(message="Error", data=None, status_code=400):
    """
    Create a standardized error response
    Args:
        message: Error message
        data: Additional error data (optional)
        status_code: HTTP status code (default: 400)
    Returns:
        JSON response with status, message, and data
    """
    response = {
        "status": "error",
        "message": message,
        "data": data
    }
    return jsonify(response), status_code





