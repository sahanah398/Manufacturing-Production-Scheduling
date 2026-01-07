"""
Unit Service
Contains business logic and database operations for unit management
Uses stored procedures for all database operations
"""
from database.db import execute_stored_procedure

from database.db import execute_stored_procedure

def create_unit(data, user_id):
    """
    Create a new unit
    Prevents duplicate unitName + unitSymbol
    """

    conn = None
    try:
        unit_name = data["unitName"].strip()
        unit_symbol = data["unitSymbol"].strip()
        description = data.get("description")

        # 🔹 1. CHECK DUPLICATE
        check_sql = """
            SELECT 1
            FROM Units
            WHERE unitName = ?
              AND unitSymbol = ?
              AND isActive = 1
        """

        cursor, conn = execute_stored_procedure(
            None,
            (unit_name, unit_symbol),
            commit=False,
            fallback_sql=check_sql
        )

        if cursor.fetchone():
            return {
                 "status": "error",
                 "message": "A unit with the specified name and symbol already exists."
                 }



        # 🔹 2. INSERT (SP OR FALLBACK)
        fallback_insert_sql = """
            INSERT INTO Units
            (unitName, description, unitSymbol, isActive, CreatedBy, createdAt, updatedAt)
            VALUES (?, ?, ?, 1, ?, SYSDATETIMEOFFSET(), SYSDATETIMEOFFSET())
        """

        execute_stored_procedure(
            "sp_Unit_Create",
            (unit_name, description, unit_symbol, user_id),
            fallback_sql=fallback_insert_sql
        )

        # 🔹 3. RETURN CREATED RECORD
        fetch_sql = """
            SELECT TOP 1
                id, unitName, description, unitSymbol,
                isActive, CreatedBy, UpdatedBy,
                createdAt, updatedAt
            FROM Units
            WHERE CreatedBy = ?
            ORDER BY createdAt DESC
        """

        cursor, conn = execute_stored_procedure(
            None,
            (user_id,),
            commit=False,
            fallback_sql=fetch_sql
        )

        columns = [col[0] for col in cursor.description]
        row = cursor.fetchone()

        return dict(zip(columns, row))

    finally:
        if conn:
            conn.close()



def get_units(page=1, per_page=10, sort_by="unitName", sort_order="ASC"):
    """
    Retrieve active units with pagination and sorting
    Args:
        page: Page number (default 1)
        per_page: Results per page (default 10)
        sort_by: Column to sort by (unitName, id, description, unitSymbol) - default unitName
        sort_order: ASC or DESC - default ASC
    Returns:
        Dictionary with units list, total count, page info
    """
    conn = None
    try:
        # Validate sort parameters to prevent SQL injection
        allowed_columns = ["unitName", "id", "description", "unitSymbol"]
        if sort_by not in allowed_columns:
            sort_by = "unitName"
        if sort_order.upper() not in ["ASC", "DESC"]:
            sort_order = "ASC"
        
        # Calculate offset
        offset = (page - 1) * per_page
        
        # Get total count
        count_sql = "SELECT COUNT(*) as total FROM Units WHERE isActive = 1"
        cursor, conn = execute_stored_procedure(None, commit=False, fallback_sql=count_sql)
        total = cursor.fetchone()[0]
        
        # Get paginated and sorted units
        fallback_sql = f"""
            SELECT id, unitName, unitSymbol, description 
            FROM Units 
            WHERE isActive = 1 
            ORDER BY {sort_by} {sort_order}
            OFFSET {offset} ROWS
            FETCH NEXT {per_page} ROWS ONLY
        """
        cursor, conn = execute_stored_procedure("sp_Unit_GetAll", commit=False, fallback_sql=fallback_sql)
        
        # Get column names from query result
        columns = [column[0] for column in cursor.description]
        rows = cursor.fetchall()
        
        # Convert database rows to dictionaries
        data = []
        for row in rows:
            data.append(dict(zip(columns, row)))
        
        # Calculate total pages
        total_pages = (total + per_page - 1) // per_page
        
        return {
            "units": data,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages
        }
    finally:
        # Always close connection, even if error occurs
        if conn:
            conn.close()


def search_units(search, page=1, per_page=10, sort_by="unitName", sort_order="ASC"):
    """
    Search active units by name, description, or symbol with pagination.
    Args:
        search: search string
        page: page number
        per_page: items per page
    Returns:
        Dictionary with units list and pagination info
    """
    conn = None
    try:
        if not search:
            return get_units(page=page, per_page=per_page, sort_by=sort_by, sort_order=sort_order)

        allowed_columns = ["unitName", "id", "description", "unitSymbol"]
        if sort_by not in allowed_columns:
            sort_by = "unitName"
        if sort_order.upper() not in ["ASC", "DESC"]:
            sort_order = "ASC"

        offset = (page - 1) * per_page
        like = f"%{search}%"

        count_sql = """
            SELECT COUNT(*) as total FROM Units
            WHERE isActive = 1 AND (unitName LIKE ? OR description LIKE ? OR unitSymbol LIKE ?)
        """
        cursor, conn = execute_stored_procedure(
            None,
            (like, like, like),
            commit=False,
            fallback_sql=count_sql
        )
        total = cursor.fetchone()[0]

        fallback_sql = f"""
            SELECT id, unitName, unitSymbol, description
            FROM Units
            WHERE isActive = 1
              AND (unitName LIKE ? OR description LIKE ? OR unitSymbol LIKE ?)
            ORDER BY {sort_by} {sort_order}
            OFFSET {offset} ROWS
            FETCH NEXT {per_page} ROWS ONLY
        """
        cursor, conn = execute_stored_procedure(
            None,
            (like, like, like),
            commit=False,
            fallback_sql=fallback_sql
        )
        columns = [column[0] for column in cursor.description]
        rows = cursor.fetchall()
        data = [dict(zip(columns, row)) for row in rows]

        total_pages = (total + per_page - 1) // per_page
        return {
            "units": data,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
        }
    finally:
        if conn:
            conn.close()

def get_unit_by_id(unit_id):
    """
    Get a single unit by ID
    Args:
        unit_id: ID of the unit to retrieve
    Returns:
        Dictionary with unit data, or None if not found
    """
    conn = None
    try:
        cursor, conn = execute_stored_procedure(
            "sp_Unit_GetById",
            (unit_id,),
            commit=False,
            fallback_sql="""
                SELECT id, unitName, unitSymbol, description, isActive, CreatedBy, UpdatedBy, createdAt, updatedAt
                FROM Units 
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


def update_unit(data, user_id):
    """
    Update an existing unit in the database using stored procedure (falls back to direct SQL if SP doesn't exist)
    Only allows update if isActive = 1
    Args:
        data: Dictionary with 'id', 'unitName', 'description', 'unitSymbol'
        user_id: ID of the user updating the unit
    Returns:
        Dictionary with updated unit data
    """
    conn = None
    try:
        # Check if unit exists and is active
        check_sql = "SELECT isActive FROM Units WHERE id = ?"
        cursor, conn = execute_stored_procedure(None, (data["id"],), commit=False, fallback_sql=check_sql)
        check_row = cursor.fetchone()
        
        if not check_row:
            raise Exception("Unit not found")
        
        if not check_row[0]:  # isActive is False (0)
            raise Exception("Cannot update inactive unit")
        
        # Call stored procedure: sp_Unit_Update
        # Parameters: @unitName, @description, @unitSymbol, @updatedBy, @id
        # Fallback SQL if stored procedure doesn't exist
        fallback_sql = """
            UPDATE Units
            SET unitName = ?, description = ?, unitSymbol = ?,
                UpdatedBy = ?, updatedAt = SYSDATETIMEOFFSET()
            WHERE id = ?
        """
        cursor, conn = execute_stored_procedure(
            "sp_Unit_Update",
            (
                data["unitName"],
                data.get("description"),
                data.get("unitSymbol"),
                user_id,
                data["id"]
            ),
            fallback_sql=fallback_sql
        )
        
        # Get updated unit data
        fallback_get_sql = "SELECT id, unitName, unitSymbol, description, isActive, UpdatedBy, updatedAt FROM Units WHERE id = ?"
        cursor, conn = execute_stored_procedure(None, (data["id"],), commit=False, fallback_sql=fallback_get_sql)
        columns = [column[0] for column in cursor.description]
        row = cursor.fetchone()
        
        if row:
            return dict(zip(columns, row))
        return {"id": data["id"]}
    finally:
        # Always close connection, even if error occurs
        if conn:
            conn.close()


def delete_unit(unit_id, user_id):
    """
    Soft delete a unit (sets isActive = 0).
    Only allows delete once; if already deleted (isActive = 0), raises an error.
    Args:
        unit_id: ID of the unit to delete
        user_id: ID of the user performing the deletion
    Returns:
        Dictionary with updated unit data
    """
    conn = None
    try:
        # Get current unit data before deletion
        fallback_get_sql = "SELECT id, unitName, unitSymbol, description, isActive FROM Units WHERE id = ?"
        cursor, conn = execute_stored_procedure(None, (unit_id,), commit=False, fallback_sql=fallback_get_sql)
        columns = [column[0] for column in cursor.description]
        row = cursor.fetchone()

        if not row:
            raise Exception("Unit not found")

        current = dict(zip(columns, row))
        if not current.get("isActive"):
            raise Exception("Unit already deleted")

        # Soft delete: set isActive = 0
        fallback_delete_sql = """
            UPDATE Units
            SET isActive = 0, UpdatedBy = ?, updatedAt = SYSDATETIMEOFFSET()
            WHERE id = ?
        """
        cursor, conn = execute_stored_procedure(
            "sp_Unit_Delete",
            (user_id, unit_id),
            fallback_sql=fallback_delete_sql
        )

        # Get updated unit data
        cursor, conn = execute_stored_procedure(None, (unit_id,), commit=False, fallback_sql=fallback_get_sql)
        columns = [column[0] for column in cursor.description]
        row = cursor.fetchone()

        if row:
            return dict(zip(columns, row))
        return {"id": unit_id}
    finally:
        # Always close connection, even if error occurs
        if conn:
            conn.close()
