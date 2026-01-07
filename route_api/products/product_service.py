"""
Product Service
Contains business logic and database operations for product management
Uses stored procedures for all database operations
"""
from database.db import execute_stored_procedure

def create_product(data, user_id):
    """
    Create a new product
    Args:
        data: Dictionary with:
            - 'productName': required
            - 'description': optional
            - 'mainRouteId': required (ID of the main route)
        user_id: ID of the user creating the product
    Returns:
        Dictionary with created product data
    """
    conn = None
    try:
        # Insert into Products table
        fallback_sql = """
            INSERT INTO Products
            (productName, description, mainRouteId, isActive, CreatedBy, UpdatedBy, createdAt, updatedAt)
            VALUES (?, ?, ?, 1, ?, ?, SYSDATETIMEOFFSET(), SYSDATETIMEOFFSET())
        """
        cursor, conn = execute_stored_procedure(
            "sp_Product_Create",
            (
                data["productName"],
                data.get("description"),
                data["mainRouteId"],
                user_id,
                user_id
            ),
            fallback_sql=fallback_sql
        )
        
        # Get the created product ID
        get_product_sql = """
            SELECT TOP 1 id, productName, description, mainRouteId, isActive, CreatedBy, UpdatedBy, createdAt, updatedAt
            FROM Products
            WHERE CreatedBy = ?
            ORDER BY createdAt DESC
        """
        cursor, conn = execute_stored_procedure(None, (user_id,), commit=False, fallback_sql=get_product_sql)
        columns = [column[0] for column in cursor.description]
        row = cursor.fetchone()
        
        if not row:
            raise Exception("Failed to retrieve created product")
        
        return dict(zip(columns, row))
    finally:
        if conn:
            conn.close()


def get_products(page=1, per_page=10, sort_by="productName", sort_order="ASC"):
    """
    Get list of products with pagination and sorting
    Args:
        page: Page number (default: 1)
        per_page: Items per page (default: 10)
        sort_by: Column to sort by (default: "productName")
        sort_order: Sort order "ASC" or "DESC" (default: "ASC")
    Returns:
        Dictionary with products list and pagination info
    """
    conn = None
    try:
        # Validate sort parameters
        allowed_columns = ["productName", "id", "mainRouteId", "createdAt"]
        if sort_by not in allowed_columns:
            sort_by = "productName"
        if sort_order.upper() not in ["ASC", "DESC"]:
            sort_order = "ASC"
        
        # Calculate offset
        offset = (page - 1) * per_page
        
        # Get total count
        count_sql = "SELECT COUNT(*) as total FROM Products WHERE isActive = 1"
        cursor, conn = execute_stored_procedure(None, commit=False, fallback_sql=count_sql)
        total = cursor.fetchone()[0]
        
        # Get paginated and sorted products
        fallback_sql = f"""
            SELECT id, productName, description, mainRouteId, isActive, CreatedBy, UpdatedBy, createdAt, updatedAt
            FROM Products
            WHERE isActive = 1
            ORDER BY {sort_by} {sort_order}
            OFFSET {offset} ROWS
            FETCH NEXT {per_page} ROWS ONLY
        """
        cursor, conn = execute_stored_procedure("sp_Product_GetAll", commit=False, fallback_sql=fallback_sql)
        
        columns = [column[0] for column in cursor.description]
        rows = cursor.fetchall()
        
        # Convert to dictionaries
        products = []
        for row in rows:
            products.append(dict(zip(columns, row)))
        
        # Calculate total pages
        total_pages = (total + per_page - 1) // per_page
        
        return {
            "products": products,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages
        }
    finally:
        if conn:
            conn.close()


def search_products(search, page=1, per_page=10, sort_by="productName", sort_order="ASC"):
    """
    Search active products by name or description with pagination.
    """
    conn = None
    try:
        if not search:
            return get_products(page=page, per_page=per_page, sort_by=sort_by, sort_order=sort_order)

        allowed_columns = ["productName", "id", "mainRouteId", "createdAt"]
        if sort_by not in allowed_columns:
            sort_by = "productName"
        if sort_order.upper() not in ["ASC", "DESC"]:
            sort_order = "ASC"

        offset = (page - 1) * per_page
        like = f"%{search}%"

        count_sql = """
            SELECT COUNT(*) as total
            FROM Products
            WHERE isActive = 1
              AND (productName LIKE ? OR description LIKE ?)
        """
        cursor, conn = execute_stored_procedure(
            None,
            (like, like),
            commit=False,
            fallback_sql=count_sql
        )
        total = cursor.fetchone()[0]

        fallback_sql = f"""
            SELECT id, productName, description, mainRouteId, isActive, CreatedBy, UpdatedBy, createdAt, updatedAt
            FROM Products
            WHERE isActive = 1
              AND (productName LIKE ? OR description LIKE ?)
            ORDER BY {sort_by} {sort_order}
            OFFSET {offset} ROWS
            FETCH NEXT {per_page} ROWS ONLY
        """
        cursor, conn = execute_stored_procedure(
            None,
            (like, like),
            commit=False,
            fallback_sql=fallback_sql
        )
        columns = [column[0] for column in cursor.description]
        rows = cursor.fetchall()
        products = [dict(zip(columns, row)) for row in rows]

        total_pages = (total + per_page - 1) // per_page
        return {
            "products": products,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
        }
    finally:
        if conn:
            conn.close()

def get_product_by_id(product_id):
    """
    Get a single product by ID
    Args:
        product_id: ID of the product to retrieve
    Returns:
        Dictionary with product data, or None if not found
    """
    conn = None
    try:
        cursor, conn = execute_stored_procedure(
            "sp_Product_GetById",
            (product_id,),
            commit=False,
            fallback_sql="""
                SELECT id, productName, description, mainRouteId, isActive, CreatedBy, UpdatedBy, createdAt, updatedAt
                FROM Products
                WHERE id = ? AND isActive = 1
            """
        )
        columns = [column[0] for column in cursor.description]
        row = cursor.fetchone()
        
        if row:
            return dict(zip(columns, row))
        return None
    finally:
        if conn:
            conn.close()


def update_product(data, user_id):
    """
    Update an existing product
    Only allows update if isActive = 1
    Args:
        data: Dictionary with 'id', 'productName', 'description', 'mainRouteId'
        user_id: ID of the user updating the product
    Returns:
        Dictionary with updated product data
    """
    conn = None
    try:
        # Get existing product to preserve values not provided in update and check isActive
        get_existing_sql = """
            SELECT productName, description, mainRouteId, isActive
            FROM Products
            WHERE id = ?
        """
        cursor, conn = execute_stored_procedure(None, (data["id"],), commit=False, fallback_sql=get_existing_sql)
        existing = cursor.fetchone()
        
        if not existing:
            raise Exception("Product not found")
        
        existing_columns = [column[0] for column in cursor.description]
        existing_dict = dict(zip(existing_columns, existing))
        
        if not existing_dict.get("isActive"):  # isActive is False (0)
            raise Exception("Cannot update inactive product")
        
        # Use provided values or keep existing ones
        product_name = data.get("productName", existing_dict.get("productName"))
        description = data.get("description") if "description" in data else existing_dict.get("description")
        main_route_id = data.get("mainRouteId", existing_dict.get("mainRouteId"))
        
        fallback_sql = """
            UPDATE Products
            SET productName = ?, description = ?, mainRouteId = ?,
                UpdatedBy = ?, updatedAt = SYSDATETIMEOFFSET()
            WHERE id = ?
        """
        cursor, conn = execute_stored_procedure(
            "sp_Product_Update",
            (
                product_name,
                description,
                main_route_id,
                user_id,
                data["id"]
            ),
            fallback_sql=fallback_sql
        )
        
        # Get updated product data
        get_sql = """
            SELECT id, productName, description, mainRouteId, isActive, CreatedBy, UpdatedBy, createdAt, updatedAt
            FROM Products
            WHERE id = ?
        """
        cursor, conn = execute_stored_procedure(None, (data["id"],), commit=False, fallback_sql=get_sql)
        columns = [column[0] for column in cursor.description]
        row = cursor.fetchone()
        
        if row:
            return dict(zip(columns, row))
        return {"id": data["id"]}
    finally:
        if conn:
            conn.close()


def delete_product(product_id, user_id):
    """
    Soft delete a product (sets isActive = 0).
    Only allows delete once; if already deleted (isActive = 0), raises an error.
    Args:
        product_id: ID of the product to delete
        user_id: ID of the user performing the deletion
    Returns:
        Dictionary with updated product data
    """
    conn = None
    try:
        # Get updated product data
        get_sql = """
            SELECT id, productName, description, mainRouteId, isActive, CreatedBy, UpdatedBy, createdAt, updatedAt
            FROM Products
            WHERE id = ?
        """
        cursor, conn = execute_stored_procedure(None, (product_id,), commit=False, fallback_sql=get_sql)
        columns = [column[0] for column in cursor.description]
        row = cursor.fetchone()

        if not row:
            raise Exception("Product not found")

        current = dict(zip(columns, row))
        if not current.get("isActive"):
            raise Exception("Product already deleted")

        # Soft delete: set isActive = 0
        fallback_sql = """
            UPDATE Products
            SET isActive = 0, UpdatedBy = ?, updatedAt = SYSDATETIMEOFFSET()
            WHERE id = ?
        """
        cursor, conn = execute_stored_procedure(
            "sp_Product_Delete",
            (user_id, product_id),
            fallback_sql=fallback_sql
        )

        # Get updated product data
        cursor, conn = execute_stored_procedure(None, (product_id,), commit=False, fallback_sql=get_sql)
        columns = [column[0] for column in cursor.description]
        row = cursor.fetchone()
        
        if row:
            return dict(zip(columns, row))
        return {"id": product_id}
    finally:
        if conn:
            conn.close()



