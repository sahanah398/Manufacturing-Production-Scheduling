"""
Unit Service
Contains business logic and database operations for unit management
Uses stored procedures for all database operations
"""
from database.db import execute_stored_procedure

def create_unit(data, user_id):
    """
    Create a new unit in the database using stored procedure (falls back to direct SQL if SP doesn't exist)
    Args:
        data: Dictionary with 'unitName', 'description', 'unitSymbol'
        user_id: ID of the user creating the unit
    Returns:
        Dictionary with created unit data
    """
    conn = None
    try:
        # Call stored procedure: sp_Unit_Create
        # Parameters: @unitName, @description, @unitSymbol, @createdBy
        # Fallback SQL if stored procedure doesn't exist
        fallback_sql = """
            INSERT INTO Units
            (unitName, description, unitSymbol, isActive, CreatedBy, createdAt, updatedAt)
            VALUES (?, ?, ?, 1, ?, SYSDATETIMEOFFSET(), SYSDATETIMEOFFSET())
        """
        cursor, conn = execute_stored_procedure(
            "sp_Unit_Create",
            (
                data["unitName"],
                data.get("description"),
                data.get("unitSymbol"),
                user_id
            ),
            fallback_sql=fallback_sql
        )
        
        # Get the last inserted unit ID and return unit data
        fallback_get_sql = "SELECT TOP 1 id, unitName, unitSymbol, description, isActive, CreatedBy, ISNULL(UpdatedBy, CreatedBy) as UpdatedBy, createdAt, updatedAt FROM Units WHERE CreatedBy = ? ORDER BY createdAt DESC"
        cursor, conn = execute_stored_procedure(None, (user_id,), commit=False, fallback_sql=fallback_get_sql)
        columns = [column[0] for column in cursor.description]
        row = cursor.fetchone()
        
        if row:
            return dict(zip(columns, row))
        return {"unitName": data["unitName"]}
    finally:
        # Always close connection, even if error occurs
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


def update_unit(data, user_id):
    """
    Update an existing unit in the database using stored procedure (falls back to direct SQL if SP doesn't exist)
    Args:
        data: Dictionary with 'id', 'unitName', 'description', 'unitSymbol'
        user_id: ID of the user updating the unit
    Returns:
        Dictionary with updated unit data
    """
    conn = None
    try:
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
    Soft delete a unit using stored procedure (falls back to direct SQL if SP doesn't exist)
    Toggles isActive status - if 1 becomes 0, if 0 becomes 1
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
        
        # Delete the unit (toggle isActive)
        fallback_delete_sql = """
            UPDATE Units
            SET isActive = CASE WHEN isActive = 1 THEN 0 ELSE 1 END, UpdatedBy = ?, updatedAt = SYSDATETIMEOFFSET()
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
