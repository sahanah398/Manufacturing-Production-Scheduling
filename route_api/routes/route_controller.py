"""
Route Controller
Handles HTTP requests for route management operations (CRUD)
All routes require JWT authentication via @token_required decorator
"""
from flask import Blueprint, request
from routes.route_service import *
from utils.jwt_utils import token_required
from utils.response_utils import success_response, error_response

# Create blueprint for route management routes
route_bp = Blueprint("route", __name__)

@route_bp.route("/route/create", methods=["POST"])
@token_required
def create():
    """
    Create a new route
    Accepts: JSON with 'routeName', 'description', 'isMainRoute', 'processSequence'
    Returns: Standardized response with created route data
    """
    try:
        created_route = create_route(request.json, request.user_id)
        return success_response(
            message="Route created successfully",
            data=created_route,
            status_code=201
        )
    except Exception as e:
        return error_response(
            message="Failed to create route",
            data={"error": str(e)},
            status_code=400
        )


@route_bp.route("/route/list", methods=["POST"])
@token_required
def list_routes_api():
    """
    Get list of active routes with pagination and sorting
    Request body (optional): {
        "page": 1,
        "per_page": 10,
        "sort_by": "routeName",
        "sort_order": "ASC"
    }
    Returns: Standardized response with routes data, pagination info
    """
    try:
        # Get pagination and sorting parameters from request (body is optional)
        req_data = request.get_json(force=True, silent=True) or {}
        search = req_data.get("search")
        page = req_data.get("page", 1)
        per_page = req_data.get("per_page", 10)
        sort_by = req_data.get("sort_by", "routeName")
        sort_order = req_data.get("sort_order", "ASC")
        
        # Validate pagination parameters
        page = max(1, int(page)) if isinstance(page, (int, str)) else 1
        per_page = max(1, min(100, int(per_page))) if isinstance(per_page, (int, str)) else 10
        
        # Fetch routes with pagination and sorting (and optional search)
        if search:
            result = search_routes(search=search, page=page, per_page=per_page, sort_by=sort_by, sort_order=sort_order)
        else:
            result = get_routes(page=page, per_page=per_page, sort_by=sort_by, sort_order=sort_order)
        
        return success_response(
            message="Routes retrieved successfully",
            data=result,
            status_code=200
        )
    except Exception as e:
        return error_response(
            message="Failed to retrieve routes",
            data={"error": str(e)},
            status_code=500
        )


@route_bp.route("/route/get", methods=["POST"])
@token_required
def get_by_id():
    """
    Get a single route by ID
    Accepts: JSON with 'id'
    Returns: Standardized response with route data including process sequence
    """
    try:
        route_id = request.json.get("id")
        if not route_id:
            return error_response(
                message="Route ID is required",
                data=None,
                status_code=400
            )
        
        route = get_route_by_id(route_id)
        if not route:
            return error_response(
                message="Route not found",
                data=None,
                status_code=404
            )
        
        return success_response(
            message="Route retrieved successfully",
            data=route,
            status_code=200
        )
    except Exception as e:
        return error_response(
            message="Failed to retrieve route",
            data={"error": str(e)},
            status_code=500
        )


@route_bp.route("/route/update", methods=["POST"])
@token_required
def update():
    """
    Update an existing route
    Accepts: JSON with 'id', 'routeName', 'description', 'isMainRoute'
    Returns: Standardized response with updated route data
    """
    try:
        updated_route = update_route(request.json, request.user_id)
        return success_response(
            message="Route updated successfully",
            data=updated_route,
            status_code=200
        )
    except Exception as e:
        return error_response(
            message="Failed to update route",
            data={"error": str(e)},
            status_code=400
        )


@route_bp.route("/route/delete", methods=["POST"])
@token_required
def delete():
    """
    Soft delete a route (sets isActive = 0)
    Accepts: JSON with 'id'
    Returns: Standardized response with deleted route data
    """
    try:
        route_id = request.json.get("id")
        deleted_route = delete_route(route_id, request.user_id)
        return success_response(
            message="Route deleted successfully",
            data=deleted_route,
            status_code=200
        )
    except Exception as e:
        msg = str(e)
        # Specific messages for repeated or invalid deletes
        if "already deleted" in msg.lower():
            return error_response(
                message="Route already deleted",
                data=None,
                status_code=400
            )
        if "not found" in msg.lower():
            return error_response(
                message="Route not found",
                data=None,
                status_code=404
            )
        return error_response(
            message="Failed to delete route",
            data={"error": msg},
            status_code=400
        )


