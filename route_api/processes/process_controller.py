"""
Process Controller
Handles HTTP requests for process management operations (CRUD)
All routes require JWT authentication via @token_required decorator
"""
from flask import Blueprint, request
from processes.process_service import *
from utils.jwt_utils import token_required
from utils.response_utils import success_response, error_response

# Create blueprint for process management routes
process_bp = Blueprint("process", __name__)

@process_bp.route("/process/create", methods=["POST"])
@token_required
def create():
    """
    Create a new process
    Accepts: JSON with 'processName', 'description', 'workstationId', 'processTime', 'setupTime', 'technicalValues'
    Returns: Standardized response with created process data
    """
    try:
        created_process = create_process(request.json, request.user_id)
        return success_response(
            message="Process created successfully",
            data=created_process,
            status_code=201
        )
    except Exception as e:
        return error_response(
            message="Failed to create process",
            data={"error": str(e)},
            status_code=400
        )


@process_bp.route("/process/list", methods=["POST", "GET"])
@token_required
def list_processes_api():
    """
    Get list of active processes with pagination and sorting
    Request body (optional): {
        "page": 1,
        "per_page": 10,
        "sort_by": "processName",
        "sort_order": "ASC"
    }
    Returns: Standardized response with processes data, pagination info
    """
    try:
        # Get pagination and sorting parameters from request (body is optional)
        req_data = request.get_json(force=True, silent=True) or {}
        search = req_data.get("search")
        page = req_data.get("page", 1)
        per_page = req_data.get("per_page", 10)
        sort_by = req_data.get("sort_by", "processName")
        sort_order = req_data.get("sort_order", "ASC")
        
        # Validate pagination parameters
        page = max(1, int(page)) if isinstance(page, (int, str)) else 1
        per_page = max(1, min(100, int(per_page))) if isinstance(per_page, (int, str)) else 10
        
        # Fetch processes with pagination and sorting (and optional search)
        if search:
            result = search_processes(search=search, page=page, per_page=per_page, sort_by=sort_by, sort_order=sort_order)
        else:
            result = get_processes(page=page, per_page=per_page, sort_by=sort_by, sort_order=sort_order)
        
        return success_response(
            message="Processes retrieved successfully",
            data=result,
            status_code=200
        )
    except Exception as e:
        return error_response(
            message="Failed to retrieve processes",
            data={"error": str(e)},
            status_code=500
        )


@process_bp.route("/process/get", methods=["POST"])
@token_required
def get_by_id():
    """
    Get a single process by ID
    Accepts: JSON with 'id'
    Returns: Standardized response with process data including technical values
    """
    try:
        process_id = request.json.get("id")
        if not process_id:
            return error_response(
                message="Process ID is required",
                data=None,
                status_code=400
            )
        
        process = get_process_by_id(process_id)
        if not process:
            return error_response(
                message="Process not found",
                data=None,
                status_code=404
            )
        
        return success_response(
            message="Process retrieved successfully",
            data=process,
            status_code=200
        )
    except Exception as e:
        return error_response(
            message="Failed to retrieve process",
            data={"error": str(e)},
            status_code=500
        )


@process_bp.route("/process/update", methods=["POST"])
@token_required
def update():
    """
    Update an existing process
    Accepts: JSON with 'id', 'processName', 'description', 'workstationId', 'processTime', 'setupTime'
    Returns: Standardized response with updated process data
    """
    try:
        updated_process = update_process(request.json, request.user_id)
        return success_response(
            message="Process updated successfully",
            data=updated_process,
            status_code=200
        )
    except Exception as e:
        return error_response(
            message="Failed to update process",
            data={"error": str(e)},
            status_code=400
        )


@process_bp.route("/process/delete", methods=["POST"])
@token_required
def delete():
    """
    Soft delete a process (sets isActive = 0)
    Accepts: JSON with 'id'
    Returns: Standardized response with deleted process data
    """
    try:
        process_id = request.json.get("id")
        deleted_process = delete_process(process_id, request.user_id)
        return success_response(
            message="Process deleted successfully",
            data=deleted_process,
            status_code=200
        )
    except Exception as e:
        msg = str(e)
        if "already deleted" in msg.lower():
            return error_response(
                message="Process already deleted",
                data=None,
                status_code=400
            )
        if "not found" in msg.lower():
            return error_response(
                message="Process not found",
                data=None,
                status_code=404
            )
        return error_response(
            message="Failed to delete process",
            data={"error": msg},
            status_code=400
        )

