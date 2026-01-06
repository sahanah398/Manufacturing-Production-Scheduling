"""
Shift Service
Contains business logic and database operations for shift management
Uses stored procedures for all database operations
"""
from database.db import execute_stored_procedure

def create_shift(data, user_id):
    """
    Create a new shift in the database
    Args:
        data: Dictionary with 'name', 'startTime', 'endTime', 'duration', 'colorCode'
        user_id: ID of the user creating the shift
    Returns:
        Dictionary with created shift data
    """
    conn = None
    try:
        # Call stored procedure: sp_Shift_Create
        # Parameters: @name, @startTime, @endTime, @duration, @colorCode, @createdBy
        fallback_sql = """
            INSERT INTO MasterShifts
            (name, startTime, endTime, duration, colorCode, isActive, CreatedBy, createdAt, updatedAt)
            VALUES (?, ?, ?, ?, ?, 1, ?, SYSDATETIMEOFFSET(), SYSDATETIMEOFFSET())
        """
        cursor, conn = execute_stored_procedure(
            "sp_Shift_Create",
            (
                data["name"],
                data.get("startTime"),
                data.get("endTime"),
                data.get("duration"),
                data.get("colorCode"),
                user_id
            ),
            fallback_sql=fallback_sql
        )
        
        # Get the last inserted shift and return shift data
        fallback_get_sql = "SELECT TOP 1 id, name, startTime, endTime, duration, colorCode, isActive, CreatedBy, ISNULL(UpdatedBy, CreatedBy) as UpdatedBy, createdAt, updatedAt FROM MasterShifts WHERE CreatedBy = ? ORDER BY createdAt DESC"
        cursor, conn = execute_stored_procedure(None, (user_id,), commit=False, fallback_sql=fallback_get_sql)
        columns = [column[0] for column in cursor.description]
        row = cursor.fetchone()
        
        if row:
            return dict(zip(columns, row))
        return {"name": data["name"]}
    finally:
        if conn:
            conn.close()


def get_shifts(page=1, per_page=10, sort_by="name", sort_order="ASC"):
    """
    Retrieve active shifts with pagination and sorting
    Args:
        page: Page number (default 1)
        per_page: Results per page (default 10)
        sort_by: Column to sort by (name, id, startTime, endTime, duration, colorCode) - default name
        sort_order: ASC or DESC - default ASC
    Returns:
        Dictionary with shifts list, total count, page info
    """
    conn = None
    try:
        # Validate sort parameters to prevent SQL injection
        allowed_columns = ["name", "id", "startTime", "endTime", "duration", "colorCode"]
        if sort_by not in allowed_columns:
            sort_by = "name"
        if sort_order.upper() not in ["ASC", "DESC"]:
            sort_order = "ASC"
        
        # Calculate offset
        offset = (page - 1) * per_page
        
        # Get total count
        count_sql = "SELECT COUNT(*) as total FROM MasterShifts WHERE isActive = 1"
        cursor, conn = execute_stored_procedure(None, commit=False, fallback_sql=count_sql)
        total = cursor.fetchone()[0]
        
        # Get paginated and sorted shifts
        fallback_sql = f"""
            SELECT id, name, startTime, endTime, duration, colorCode, isActive, CreatedBy, UpdatedBy
            FROM MasterShifts 
            WHERE isActive = 1 
            ORDER BY {sort_by} {sort_order}
            OFFSET {offset} ROWS
            FETCH NEXT {per_page} ROWS ONLY
        """
        cursor, conn = execute_stored_procedure("sp_Shift_GetAll", commit=False, fallback_sql=fallback_sql)
        
        columns = [column[0] for column in cursor.description]
        rows = cursor.fetchall()
        
        # Convert database rows to dictionaries
        data = []
        for row in rows:
            data.append(dict(zip(columns, row)))
        
        # Calculate total pages
        total_pages = (total + per_page - 1) // per_page
        
        return {
            "shifts": data,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages
        }
    finally:
        if conn:
            conn.close()


def update_shift(data, user_id):
    """
    Update an existing shift
    Args:
        data: Dictionary with 'id', 'name', 'startTime', 'endTime', 'duration', 'colorCode'
        user_id: ID of the user updating the shift
    Returns:
        Dictionary with updated shift data
    """
    conn = None
    try:
        # Call stored procedure: sp_Shift_Update
        fallback_sql = """
            UPDATE MasterShifts
            SET name = ?, startTime = ?, endTime = ?, duration = ?, colorCode = ?,
                UpdatedBy = ?, updatedAt = SYSDATETIMEOFFSET()
            WHERE id = ?
        """
        cursor, conn = execute_stored_procedure(
            "sp_Shift_Update",
            (
                data["name"],
                data.get("startTime"),
                data.get("endTime"),
                data.get("duration"),
                data.get("colorCode"),
                user_id,
                data["id"]
            ),
            fallback_sql=fallback_sql
        )
        
        # Get updated shift data
        fallback_get_sql = "SELECT id, name, startTime, endTime, duration, colorCode, isActive, CreatedBy, UpdatedBy, createdAt, updatedAt FROM MasterShifts WHERE id = ?"
        cursor, conn = execute_stored_procedure(None, (data["id"],), commit=False, fallback_sql=fallback_get_sql)
        columns = [column[0] for column in cursor.description]
        row = cursor.fetchone()
        
        if row:
            return dict(zip(columns, row))
        return {"id": data["id"]}
    finally:
        if conn:
            conn.close()


def delete_shift(shift_id, user_id):
    """
    Soft delete a shift (toggles isActive status)
    Args:
        shift_id: ID of the shift to delete
        user_id: ID of the user performing the deletion
    Returns:
        Dictionary with updated shift data
    """
    conn = None
    try:
        # Delete the shift (toggle isActive)
        fallback_delete_sql = """
            UPDATE MasterShifts
            SET isActive = CASE WHEN isActive = 1 THEN 0 ELSE 1 END, UpdatedBy = ?, updatedAt = SYSDATETIMEOFFSET()
            WHERE id = ?
        """
        cursor, conn = execute_stored_procedure(
            "sp_Shift_Delete",
            (user_id, shift_id),
            fallback_sql=fallback_delete_sql
        )
        
        # Get updated shift data
        fallback_get_sql = "SELECT id, name, startTime, endTime, duration, colorCode, isActive, CreatedBy, UpdatedBy, createdAt, updatedAt FROM MasterShifts WHERE id = ?"
        cursor, conn = execute_stored_procedure(None, (shift_id,), commit=False, fallback_sql=fallback_get_sql)
        columns = [column[0] for column in cursor.description]
        row = cursor.fetchone()
        
        if row:
            return dict(zip(columns, row))
        return {"id": shift_id}
    finally:
        if conn:
            conn.close()
