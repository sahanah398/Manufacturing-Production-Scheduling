"""
Route Service
Contains business logic and database operations for route management
Uses stored procedures for all database operations
"""
from database.db import execute_stored_procedure

def create_route(data, user_id):
    """
    Create a new route with process sequence
    Args:
        data: Dictionary with:
            - 'routeName': required
            - 'description': optional
            - 'isMainRoute': required (boolean - true for Main Route, false for Sub Route)
            - 'processSequence': optional list of process IDs in order [{processId: 1, processOrder: 1}, ...]
        user_id: ID of the user creating the route
    Returns:
        Dictionary with created route data including process sequence
    """
    conn = None
    try:
        # Insert into Routes table
        fallback_sql = """
            INSERT INTO Routes
            (routeName, description, isMainRoute, isActive, CreatedBy, UpdatedBy, createdAt, updatedAt)
            VALUES (?, ?, ?, 1, ?, ?, SYSDATETIMEOFFSET(), SYSDATETIMEOFFSET())
        """
        cursor, conn = execute_stored_procedure(
            "sp_Route_Create",
            (
                data["routeName"],
                data.get("description"),
                1 if data.get("isMainRoute", True) else 0,  # Convert boolean to bit
                user_id,
                user_id
            ),
            fallback_sql=fallback_sql
        )
        
        # Get the created route ID
        get_route_sql = """
            SELECT TOP 1 id, routeName, description, isMainRoute, isActive, CreatedBy, UpdatedBy, createdAt, updatedAt
            FROM Routes
            WHERE CreatedBy = ?
            ORDER BY createdAt DESC
        """
        cursor, conn = execute_stored_procedure(None, (user_id,), commit=False, fallback_sql=get_route_sql)
        columns = [column[0] for column in cursor.description]
        row = cursor.fetchone()
        
        if not row:
            raise Exception("Failed to retrieve created route")
        
        route = dict(zip(columns, row))
        route_id = route["id"]
        
        # Insert process sequence if provided
        process_sequence = []
        if "processSequence" in data and data["processSequence"]:
            for process_item in data["processSequence"]:
                # Support both formats: {processId, processOrder} or just processId (auto-increment order)
                process_id = process_item.get("processId") if isinstance(process_item, dict) else process_item
                process_order = process_item.get("processOrder") if isinstance(process_item, dict) else len(process_sequence) + 1
                
                route_process_sql = """
                    INSERT INTO RouteProcess
                    (routeId, processId, processOrder, isActive)
                    VALUES (?, ?, ?, 1)
                """
                route_process_cursor, route_process_conn = execute_stored_procedure(
                    "sp_RouteProcess_Create",
                    (route_id, process_id, process_order),
                    fallback_sql=route_process_sql
                )
                
                # Get created route process
                get_route_process_sql = """
                    SELECT TOP 1 id, routeId, processId, processOrder, isActive
                    FROM RouteProcess
                    WHERE routeId = ? AND processId = ? AND processOrder = ?
                    ORDER BY id DESC
                """
                route_process_cursor, route_process_conn = execute_stored_procedure(
                    None,
                    (route_id, process_id, process_order),
                    commit=False,
                    fallback_sql=get_route_process_sql
                )
                route_process_columns = [col[0] for col in route_process_cursor.description]
                route_process_row = route_process_cursor.fetchone()
                if route_process_row:
                    process_sequence.append(dict(zip(route_process_columns, route_process_row)))
                if route_process_conn:
                    route_process_conn.close()
        
        # Add process sequence to route response
        route["processSequence"] = process_sequence
        
        return route
    finally:
        if conn:
            conn.close()


def get_routes(page=1, per_page=10, sort_by="routeName", sort_order="ASC"):
    """
    Get list of routes with pagination and sorting
    Args:
        page: Page number (default: 1)
        per_page: Items per page (default: 10)
        sort_by: Column to sort by (default: "routeName")
        sort_order: Sort order "ASC" or "DESC" (default: "ASC")
    Returns:
        Dictionary with routes list and pagination info
    """
    conn = None
    try:
        # Validate sort parameters
        allowed_columns = ["routeName", "id", "isMainRoute", "createdAt"]
        if sort_by not in allowed_columns:
            sort_by = "routeName"
        if sort_order.upper() not in ["ASC", "DESC"]:
            sort_order = "ASC"
        
        # Calculate offset
        offset = (page - 1) * per_page
        
        # Get total count
        count_sql = "SELECT COUNT(*) as total FROM Routes WHERE isActive = 1"
        cursor, conn = execute_stored_procedure(None, commit=False, fallback_sql=count_sql)
        total = cursor.fetchone()[0]
        
        # Get paginated and sorted routes
        fallback_sql = f"""
            SELECT id, routeName, description, isMainRoute, isActive, CreatedBy, UpdatedBy, createdAt, updatedAt
            FROM Routes
            WHERE isActive = 1
            ORDER BY {sort_by} {sort_order}
            OFFSET {offset} ROWS
            FETCH NEXT {per_page} ROWS ONLY
        """
        cursor, conn = execute_stored_procedure("sp_Route_GetAll", commit=False, fallback_sql=fallback_sql)
        
        columns = [column[0] for column in cursor.description]
        rows = cursor.fetchall()
        
        # Convert to dictionaries
        routes = []
        for row in rows:
            route = dict(zip(columns, row))
            # Get process sequence for each route
            route_process_cursor, route_process_conn = execute_stored_procedure(
                "sp_RouteProcess_GetByRouteId",
                (route["id"],),
                commit=False,
                fallback_sql="""
                    SELECT id, routeId, processId, processOrder, isActive
                    FROM RouteProcess
                    WHERE routeId = ? AND isActive = 1
                    ORDER BY processOrder
                """
            )
            route_process_columns = [col[0] for col in route_process_cursor.description]
            route_process_rows = route_process_cursor.fetchall()
            route["processSequence"] = [dict(zip(route_process_columns, rp_row)) for rp_row in route_process_rows]
            if route_process_conn:
                route_process_conn.close()
            routes.append(route)
        
        # Calculate total pages
        total_pages = (total + per_page - 1) // per_page
        
        return {
            "routes": routes,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages
        }
    finally:
        if conn:
            conn.close()


def search_routes(search, page=1, per_page=10, sort_by="routeName", sort_order="ASC"):
    """
    Search active routes by name or description with pagination.
    """
    conn = None
    try:
        if not search:
            return get_routes(page=page, per_page=per_page, sort_by=sort_by, sort_order=sort_order)

        allowed_columns = ["routeName", "id", "isMainRoute", "createdAt"]
        if sort_by not in allowed_columns:
            sort_by = "routeName"
        if sort_order.upper() not in ["ASC", "DESC"]:
            sort_order = "ASC"

        offset = (page - 1) * per_page
        like = f"%{search}%"

        count_sql = """
            SELECT COUNT(*) as total
            FROM Routes
            WHERE isActive = 1
              AND (routeName LIKE ? OR description LIKE ?)
        """
        cursor, conn = execute_stored_procedure(
            None,
            (like, like),
            commit=False,
            fallback_sql=count_sql
        )
        total = cursor.fetchone()[0]

        fallback_sql = f"""
            SELECT id, routeName, description, isMainRoute, isActive, CreatedBy, UpdatedBy, createdAt, updatedAt
            FROM Routes
            WHERE isActive = 1
              AND (routeName LIKE ? OR description LIKE ?)
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
        routes = [dict(zip(columns, row)) for row in rows]

        total_pages = (total + per_page - 1) // per_page
        return {
            "routes": routes,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
        }
    finally:
        if conn:
            conn.close()

def get_route_by_id(route_id):
    """
    Get a single route by ID with its process sequence
    Args:
        route_id: ID of the route to retrieve
    Returns:
        Dictionary with route data including process sequence, or None if not found
    """
    conn = None
    try:
        cursor, conn = execute_stored_procedure(
            "sp_Route_GetById",
            (route_id,),
            commit=False,
            fallback_sql="""
                SELECT id, routeName, description, isMainRoute, isActive, CreatedBy, UpdatedBy, createdAt, updatedAt
                FROM Routes
                WHERE id = ? AND isActive = 1
            """
        )
        columns = [column[0] for column in cursor.description]
        row = cursor.fetchone()
        
        if not row:
            return None
        
        route = dict(zip(columns, row))
        
        # Get process sequence for the route
        route_process_cursor, route_process_conn = execute_stored_procedure(
            "sp_RouteProcess_GetByRouteId",
            (route_id,),
            commit=False,
            fallback_sql="""
                SELECT id, routeId, processId, processOrder, isActive
                FROM RouteProcess
                WHERE routeId = ? AND isActive = 1
                ORDER BY processOrder
            """
        )
        route_process_columns = [col[0] for col in route_process_cursor.description]
        route_process_rows = route_process_cursor.fetchall()
        route["processSequence"] = [dict(zip(route_process_columns, rp_row)) for rp_row in route_process_rows]
        if route_process_conn:
            route_process_conn.close()
        
        return route
    finally:
        if conn:
            conn.close()


def update_route(data, user_id):
    """
    Update an existing route
    Only allows update if isActive = 1
    Args:
        data: Dictionary with 'id', 'routeName', 'description', 'isMainRoute'
        user_id: ID of the user updating the route
    Returns:
        Dictionary with updated route data
    """
    conn = None
    try:
        # Get existing route to preserve values not provided in update and check isActive
        get_existing_sql = """
            SELECT routeName, description, isMainRoute, isActive
            FROM Routes
            WHERE id = ?
        """
        cursor, conn = execute_stored_procedure(None, (data["id"],), commit=False, fallback_sql=get_existing_sql)
        existing = cursor.fetchone()
        
        if not existing:
            raise Exception("Route not found")
        
        existing_columns = [column[0] for column in cursor.description]
        existing_dict = dict(zip(existing_columns, existing))
        
        if not existing_dict.get("isActive"):  # isActive is False (0)
            raise Exception("Cannot update inactive route")
        
        # Use provided values or keep existing ones
        route_name = data.get("routeName", existing_dict.get("routeName"))
        description = data.get("description") if "description" in data else existing_dict.get("description")
        is_main_route = data.get("isMainRoute") if "isMainRoute" in data else existing_dict.get("isMainRoute")
        
        fallback_sql = """
            UPDATE Routes
            SET routeName = ?, description = ?, isMainRoute = ?,
                UpdatedBy = ?, updatedAt = SYSDATETIMEOFFSET()
            WHERE id = ?
        """
        cursor, conn = execute_stored_procedure(
            "sp_Route_Update",
            (
                route_name,
                description,
                1 if is_main_route else 0,
                user_id,
                data["id"]
            ),
            fallback_sql=fallback_sql
        )
        
        # Get updated route data
        get_sql = """
            SELECT id, routeName, description, isMainRoute, isActive, CreatedBy, UpdatedBy, createdAt, updatedAt
            FROM Routes
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


def delete_route(route_id, user_id):
    """
    Soft delete a route (sets isActive = 0).
    Only allows delete once; if already deleted (isActive = 0), raises an error.
    Args:
        route_id: ID of the route to delete
        user_id: ID of the user performing the deletion
    Returns:
        Dictionary with updated route data
    """
    conn = None
    try:
        # Get current route data
        get_sql = """
            SELECT id, routeName, description, isMainRoute, isActive, CreatedBy, UpdatedBy, createdAt, updatedAt
            FROM Routes
            WHERE id = ?
        """
        cursor, conn = execute_stored_procedure(
            None,
            (route_id,),
            commit=False,
            fallback_sql=get_sql
        )
        columns = [column[0] for column in cursor.description]
        row = cursor.fetchone()

        if not row:
            raise Exception("Route not found")

        current = dict(zip(columns, row))
        if not current.get("isActive"):
            raise Exception("Route already deleted")

        # Soft delete: set isActive = 0
        fallback_sql = """
            UPDATE Routes
            SET isActive = 0, UpdatedBy = ?, updatedAt = SYSDATETIMEOFFSET()
            WHERE id = ?
        """
        cursor, conn = execute_stored_procedure(
            "sp_Route_Delete",
            (user_id, route_id),
            fallback_sql=fallback_sql
        )

        # Get updated route data
        cursor, conn = execute_stored_procedure(
            None,
            (route_id,),
            commit=False,
            fallback_sql=get_sql
        )
        columns = [column[0] for column in cursor.description]
        row = cursor.fetchone()

        if row:
            return dict(zip(columns, row))
        return {"id": route_id}
    finally:
        if conn:
            conn.close()

