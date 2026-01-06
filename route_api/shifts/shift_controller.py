"""
Shift Controller
Handles HTTP requests for shift management operations (CRUD)
All routes require JWT authentication via @token_required decorator
"""
from flask import Blueprint, request
from shifts.shift_service import *
from utils.jwt_utils import token_required
from utils.response_utils import success_response, error_response

# Create blueprint for shift management routes
shift_bp = Blueprint("shift", __name__)

@shift_bp.route("/shift/create", methods=["POST"])
@token_required
def create():
    """
    Create a new shift
    Accepts: JSON with 'name', 'startTime', 'endTime', 'duration', 'colorCode'
    Returns: Standardized response with created shift data
    """
    try:
        created_shift = create_shift(request.json, request.user_id)
        return success_response(
            message="Shift created successfully",
            data=created_shift,
            status_code=201
        )
    except Exception as e:
        return error_response(
            message="Failed to create shift",
            data={"error": str(e)},
            status_code=400
        )


@shift_bp.route("/shift/list", methods=["POST", "GET"])
@token_required
def list_shifts_api():
    """
    Get list of active shifts with pagination and sorting
    Request body (optional): {
        "page": 1,
        "per_page": 10,
        "sort_by": "name",
        "sort_order": "ASC"
    }
    Returns: Standardized response with shifts data, pagination info
    """
    try:
        # Get pagination and sorting parameters from request (body is optional)
        req_data = request.get_json(force=True, silent=True) or {}
        page = req_data.get("page", 1)
        per_page = req_data.get("per_page", 10)
        sort_by = req_data.get("sort_by", "name")
        sort_order = req_data.get("sort_order", "ASC")
        
        # Validate pagination parameters
        page = max(1, int(page)) if isinstance(page, (int, str)) else 1
        per_page = max(1, min(100, int(per_page))) if isinstance(per_page, (int, str)) else 10
        
        # Fetch shifts with pagination and sorting
        result = get_shifts(page=page, per_page=per_page, sort_by=sort_by, sort_order=sort_order)
        
        return success_response(
            message="Shifts retrieved successfully",
            data=result,
            status_code=200
        )
    except Exception as e:
        return error_response(
            message="Failed to retrieve shifts",
            data={"error": str(e)},
            status_code=500
        )


@shift_bp.route("/shift/update", methods=["POST"])
@token_required
def update():
    """
    Update an existing shift
    Accepts: JSON with 'id', 'name', 'startTime', 'endTime', 'duration', 'colorCode'
    Returns: Standardized response with updated shift data
    """
    try:
        updated_shift = update_shift(request.json, request.user_id)
        return success_response(
            message="Shift updated successfully",
            data=updated_shift,
            status_code=200
        )
    except Exception as e:
        return error_response(
            message="Failed to update shift",
            data={"error": str(e)},
            status_code=400
        )


@shift_bp.route("/shift/delete", methods=["POST"])
@token_required
def delete():
    """
    Soft delete a shift (toggles isActive status)
    Accepts: JSON with 'id'
    Returns: Standardized response with deleted shift data
    """
    try:
        shift_id = request.json.get("id")
        deleted_shift = delete_shift(shift_id, request.user_id)
        return success_response(
            message="Shift deleted successfully",
            data=deleted_shift,
            status_code=200
        )
    except Exception as e:
        return error_response(
            message="Failed to delete shift",
            data={"error": str(e)},
            status_code=400
        )
