"""
Workstation Controller
Handles HTTP requests for workstation management operations (CRUD)
All routes require JWT authentication via @token_required decorator
"""
from flask import Blueprint, request
from workstations.workstation_service import *
from utils.jwt_utils import token_required
from utils.response_utils import success_response, error_response

workstation_bp = Blueprint("workstation", __name__)


@workstation_bp.route("/workstation/create", methods=["POST"])
@token_required
def create():
    """
    Create a new workstation
    Accepts: JSON with 'workstationName', 'description'
    Returns: created workstation data
    """
    try:
        created = create_workstation(request.json, request.user_id)
        return success_response(
            message="Workstation created successfully",
            data=created,
            status_code=201
        )
    except Exception as e:
        return error_response(
            message="Failed to create workstation",
            data={"error": str(e)},
            status_code=400
        )


@workstation_bp.route("/workstation/list", methods=["POST"])
@token_required
def list_workstations_api():
    """
    List workstations with optional pagination and sorting
    Body optional: { page, per_page, sort_by, sort_order }
    """
    try:
        req_data = request.get_json(force=True, silent=True) or {}
        search = req_data.get("search")
        page = req_data.get("page", 1)
        per_page = req_data.get("per_page", 10)
        sort_by = req_data.get("sort_by", "workstationName")
        sort_order = req_data.get("sort_order", "ASC")

        page = max(1, int(page)) if isinstance(page, (int, str)) else 1
        per_page = max(1, min(100, int(per_page))) if isinstance(per_page, (int, str)) else 10

        if search:
            result = search_workstations(search=search, page=page, per_page=per_page, sort_by=sort_by, sort_order=sort_order)
        else:
            result = get_workstations(page=page, per_page=per_page, sort_by=sort_by, sort_order=sort_order)
        return success_response(
            message="Workstations retrieved successfully",
            data=result,
            status_code=200
        )
    except Exception as e:
        return error_response(
            message="Failed to retrieve workstations",
            data={"error": str(e)},
            status_code=500
        )


@workstation_bp.route("/workstation/update", methods=["POST"])
@token_required
def update():
    try:
        updated = update_workstation(request.json, request.user_id)
        return success_response(
            message="Workstation updated successfully",
            data=updated,
            status_code=200
        )
    except Exception as e:
        return error_response(
            message="Failed to update workstation",
            data={"error": str(e)},
            status_code=400
        )



@workstation_bp.route("/workstation/delete", methods=["POST"])
@token_required
def delete():
    """
    Toggle isActive for a workstation
    Accepts JSON with 'id'
    """
    try:
        workstation_id = request.json.get("id")
        deleted = delete_workstation(workstation_id, request.user_id)
        return success_response(
            message="Workstation deleted successfully",
            data=deleted,
            status_code=200
        )
    except Exception as e:
        return error_response(
            message="Failed to delete workstation",
            data={"error": str(e)},
            status_code=400
        )
