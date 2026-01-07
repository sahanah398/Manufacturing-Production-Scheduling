"""
Unit Controller
Handles HTTP requests for unit management operations (CRUD)
All routes require JWT authentication via @token_required decorator
"""
from flask import Blueprint, request
from units.unit_service import *
from utils.jwt_utils import token_required
from utils.response_utils import success_response, error_response

# Create blueprint for unit management routes
unit_bp = Blueprint("unit", __name__)

@unit_bp.route("/unit/create", methods=["POST"])
@token_required  # Requires valid JWT token in Authorization header
def create():
    """
    Create a new unit
    Accepts: JSON with 'unitName', 'description', 'unitSymbol'
    Returns: Standardized response with status, message, and created unit data
    """
    try:
        created_unit = create_unit(request.json, request.user_id)  # request.user_id set by token_required
        return success_response(
            message="Unit created successfully",
            data=created_unit,
            status_code=201
        )
    except Exception as e:
        return error_response(
            message="Failed to create unit",
            data={"error": str(e)},
            status_code=400
        )


@unit_bp.route("/unit/list", methods=["POST"])
@token_required  # Requires valid JWT token in Authorization header
def list_units_api():
    """
    Get list of active units with pagination and sorting
    Request body (optional): {
        "page": 1,
        "per_page": 10,
        "sort_by": "unitName",
        "sort_order": "ASC"
    }
    Returns: Standardized response with units data, pagination info
    """
    try:
        # Get pagination and sorting parameters from request (body is optional)
        req_data = request.get_json(force=True, silent=True) or {}
        search = req_data.get("search")
        page = req_data.get("page", 1)
        per_page = req_data.get("per_page", 10)
        sort_by = req_data.get("sort_by", "unitName")
        sort_order = req_data.get("sort_order", "ASC")
        
        # Validate pagination parameters
        page = max(1, int(page)) if isinstance(page, (int, str)) else 1
        per_page = max(1, min(100, int(per_page))) if isinstance(per_page, (int, str)) else 10
        
        # Fetch units with pagination and sorting (and optional search)
        if search:
            result = search_units(search=search, page=page, per_page=per_page, sort_by=sort_by, sort_order=sort_order)
        else:
            result = get_units(page=page, per_page=per_page, sort_by=sort_by, sort_order=sort_order)
        
        return success_response(
            message="Units retrieved successfully",
            data=result,
            status_code=200
        )
    except Exception as e:
        return error_response(
            message="Failed to retrieve units",
            data={"error": str(e)},
            status_code=500
        )


@unit_bp.route("/unit/get", methods=["POST"])
@token_required  # Requires valid JWT token in Authorization header
def get_by_id():
    """
    Get a single unit by ID
    Accepts: JSON with 'id'
    Returns: Standardized response with unit data
    """
    try:
        unit_id = request.json.get("id")
        if not unit_id:
            return error_response(
                message="Unit ID is required",
                data=None,
                status_code=400
            )
        
        unit = get_unit_by_id(unit_id)
        if not unit:
            return error_response(
                message="Unit not found",
                data=None,
                status_code=404
            )
        
        return success_response(
            message="Unit retrieved successfully",
            data=unit,
            status_code=200
        )
    except Exception as e:
        return error_response(
            message="Failed to retrieve unit",
            data={"error": str(e)},
            status_code=500
        )


@unit_bp.route("/unit/update", methods=["POST"])
@token_required  # Requires valid JWT token in Authorization header
def update():
    """
    Update an existing unit
    Accepts: JSON with 'id', 'unitName', 'description', 'unitSymbol'
    Returns: Standardized response with status, message, and updated unit data
    """
    try:
        updated_unit = update_unit(request.json, request.user_id)  # request.user_id set by token_required
        return success_response(
            message="Unit updated successfully",
            data=updated_unit,
            status_code=200
        )
    except Exception as e:
        return error_response(
            message="Failed to update unit",
            data={"error": str(e)},
            status_code=400
        )


@unit_bp.route("/unit/delete", methods=["POST"])
@token_required  # Requires valid JWT token in Authorization header
def delete():
    """
    Soft delete a unit (toggles isActive status)
    Accepts: JSON with 'id'
    Returns: Standardized response with status, message, and deleted unit data
    """
    try:
        unit_id = request.json.get("id")
        deleted_unit = delete_unit(unit_id, request.user_id)  # request.user_id set by token_required
        return success_response(
            message="Unit deleted successfully",
            data=deleted_unit,
            status_code=200
        )
    except Exception as e:
        msg = str(e)
        if "already deleted" in msg.lower():
            return error_response(
                message="Unit already deleted",
                data=None,
                status_code=400
            )
        if "not found" in msg.lower():
            return error_response(
                message="Unit not found",
                data=None,
                status_code=404
            )
        return error_response(
            message="Failed to delete unit",
            data={"error": msg},
            status_code=400
        )
