"""
Product Controller
Handles HTTP requests for product management operations (CRUD)
All routes require JWT authentication via @token_required decorator
"""
from flask import Blueprint, request
from products.product_service import *
from utils.jwt_utils import token_required
from utils.response_utils import success_response, error_response

# Create blueprint for product management routes
product_bp = Blueprint("product", __name__)

@product_bp.route("/product/create", methods=["POST"])
@token_required
def create():
    """
    Create a new product
    Accepts: JSON with 'productName', 'description', 'mainRouteId'
    Returns: Standardized response with created product data
    """
    try:
        created_product = create_product(request.json, request.user_id)
        return success_response(
            message="Product created successfully",
            data=created_product,
            status_code=201
        )
    except Exception as e:
        return error_response(
            message="Failed to create product",
            data={"error": str(e)},
            status_code=400
        )


@product_bp.route("/product/list", methods=["POST"])
@token_required
def list_products_api():
    """
    Get list of active products with pagination and sorting
    Request body (optional): {
        "page": 1,
        "per_page": 10,
        "sort_by": "productName",
        "sort_order": "ASC"
    }
    Returns: Standardized response with products data, pagination info
    """
    try:
        # Get pagination and sorting parameters from request (body is optional)
        req_data = request.get_json(force=True, silent=True) or {}
        search = req_data.get("search")
        page = req_data.get("page", 1)
        per_page = req_data.get("per_page", 10)
        sort_by = req_data.get("sort_by", "productName")
        sort_order = req_data.get("sort_order", "ASC")
        
        # Validate pagination parameters
        page = max(1, int(page)) if isinstance(page, (int, str)) else 1
        per_page = max(1, min(100, int(per_page))) if isinstance(per_page, (int, str)) else 10
        
        # Fetch products with pagination and sorting (and optional search)
        if search:
            result = search_products(search=search, page=page, per_page=per_page, sort_by=sort_by, sort_order=sort_order)
        else:
            result = get_products(page=page, per_page=per_page, sort_by=sort_by, sort_order=sort_order)
        
        return success_response(
            message="Products retrieved successfully",
            data=result,
            status_code=200
        )
    except Exception as e:
        return error_response(
            message="Failed to retrieve products",
            data={"error": str(e)},
            status_code=500
        )


@product_bp.route("/product/get", methods=["POST"])
@token_required
def get_by_id():
    """
    Get a single product by ID
    Accepts: JSON with 'id'
    Returns: Standardized response with product data
    """
    try:
        product_id = request.json.get("id")
        if not product_id:
            return error_response(
                message="Product ID is required",
                data=None,
                status_code=400
            )
        
        product = get_product_by_id(product_id)
        if not product:
            return error_response(
                message="Product not found",
                data=None,
                status_code=404
            )
        
        return success_response(
            message="Product retrieved successfully",
            data=product,
            status_code=200
        )
    except Exception as e:
        return error_response(
            message="Failed to retrieve product",
            data={"error": str(e)},
            status_code=500
        )


@product_bp.route("/product/update", methods=["POST"])
@token_required
def update():
    """
    Update an existing product
    Accepts: JSON with 'id', 'productName', 'description', 'mainRouteId'
    Returns: Standardized response with updated product data
    """
    try:
        updated_product = update_product(request.json, request.user_id)
        return success_response(
            message="Product updated successfully",
            data=updated_product,
            status_code=200
        )
    except Exception as e:
        return error_response(
            message="Failed to update product",
            data={"error": str(e)},
            status_code=400
        )


@product_bp.route("/product/delete", methods=["POST"])
@token_required
def delete():
    """
    Soft delete a product (sets isActive = 0)
    Accepts: JSON with 'id'
    Returns: Standardized response with deleted product data
    """
    try:
        product_id = request.json.get("id")
        deleted_product = delete_product(product_id, request.user_id)
        return success_response(
            message="Product deleted successfully",
            data=deleted_product,
            status_code=200
        )
    except Exception as e:
        msg = str(e)
        if "already deleted" in msg.lower():
            return error_response(
                message="Product already deleted",
                data=None,
                status_code=400
            )
        if "not found" in msg.lower():
            return error_response(
                message="Product not found",
                data=None,
                status_code=404
            )
        return error_response(
            message="Failed to delete product",
            data={"error": msg},
            status_code=400
        )



