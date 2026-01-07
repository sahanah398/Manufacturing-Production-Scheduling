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
    Raises:
        Exception: If shift already exists (name + startTime + endTime combination)
    """
    import pyodbc
    
    conn = None
    try:
        # Check for duplicate before inserting (for fallback SQL)
        check_sql = """
            SELECT id FROM MasterShifts 
            WHERE name = ? AND startTime = ? AND endTime = ? AND isActive = 1
        """
        check_cursor, check_conn = execute_stored_procedure(
            None,
            (data["name"], data.get("startTime"), data.get("endTime")),
            commit=False,
            fallback_sql=check_sql
        )
        if check_cursor.fetchone():
            if check_conn:
                check_conn.close()
            raise Exception("Shift already exists")
        if check_conn:
            check_conn.close()
        
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


def search_shifts(search, page=1, per_page=10, sort_by="name", sort_order="ASC"):
    """
    Search active shifts by name or color code with pagination.
    """
    conn = None
    try:
        if not search:
            return get_shifts(page=page, per_page=per_page, sort_by=sort_by, sort_order=sort_order)

        allowed_columns = ["name", "id", "startTime", "endTime", "duration", "colorCode"]
        if sort_by not in allowed_columns:
            sort_by = "name"
        if sort_order.upper() not in ["ASC", "DESC"]:
            sort_order = "ASC"

        offset = (page - 1) * per_page
        like = f"%{search}%"

        count_sql = """
            SELECT COUNT(*) as total
            FROM MasterShifts
            WHERE isActive = 1
              AND (name LIKE ? OR colorCode LIKE ?)
        """
        cursor, conn = execute_stored_procedure(
            None,
            (like, like),
            commit=False,
            fallback_sql=count_sql
        )
        total = cursor.fetchone()[0]

        fallback_sql = f"""
            SELECT id, name, startTime, endTime, duration, colorCode, isActive, CreatedBy, UpdatedBy
            FROM MasterShifts
            WHERE isActive = 1
              AND (name LIKE ? OR colorCode LIKE ?)
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
        data = [dict(zip(columns, row)) for row in rows]

        total_pages = (total + per_page - 1) // per_page
        return {
            "shifts": data,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
        }
    finally:
        if conn:
            conn.close()


def get_shift_by_id(shift_id):
    """
    Get a single shift by ID
    Args:
        shift_id: ID of the shift to retrieve
    Returns:
        Dictionary with shift data, or None if not found
    """
    conn = None
    try:
        cursor, conn = execute_stored_procedure(
            "sp_Shift_GetById",
            (shift_id,),
            commit=False,
            fallback_sql="""
                SELECT id, name, startTime, endTime, duration, colorCode, isActive, CreatedBy, UpdatedBy, createdAt, updatedAt
                FROM MasterShifts 
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


def update_shift(data, user_id):
    """
    Update an existing shift
    Only allows update if isActive = 1
    Args:
        data: Dictionary with 'id', 'name', 'startTime', 'endTime', 'duration', 'colorCode'
        user_id: ID of the user updating the shift
    Returns:
        Dictionary with updated shift data
    """
    conn = None
    try:
        # Check if shift exists and is active
        check_sql = "SELECT isActive FROM MasterShifts WHERE id = ?"
        cursor, conn = execute_stored_procedure(None, (data["id"],), commit=False, fallback_sql=check_sql)
        check_row = cursor.fetchone()
        
        if not check_row:
            raise Exception("Shift not found")
        
        if not check_row[0]:  # isActive is False (0)
            raise Exception("Cannot update inactive shift")
        
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
    Soft delete a shift (sets isActive = 0).
    Only allows delete once; if already deleted (isActive = 0), raises an error.
    Args:
        shift_id: ID of the shift to delete
        user_id: ID of the user performing the deletion
    Returns:
        Dictionary with updated shift data
    """
    conn = None
    try:
        # Get updated shift data
        fallback_get_sql = "SELECT id, name, startTime, endTime, duration, colorCode, isActive, CreatedBy, UpdatedBy, createdAt, updatedAt FROM MasterShifts WHERE id = ?"
        cursor, conn = execute_stored_procedure(None, (shift_id,), commit=False, fallback_sql=fallback_get_sql)
        columns = [column[0] for column in cursor.description]
        row = cursor.fetchone()

        if not row:
            raise Exception("Shift not found")

        current = dict(zip(columns, row))
        if not current.get("isActive"):
            raise Exception("Shift already deleted")

        # Soft delete: set isActive = 0
        fallback_delete_sql = """
            UPDATE MasterShifts
            SET isActive = 0, UpdatedBy = ?, updatedAt = SYSDATETIMEOFFSET()
            WHERE id = ?
        """
        cursor, conn = execute_stored_procedure(
            "sp_Shift_Delete",
            (user_id, shift_id),
            fallback_sql=fallback_delete_sql
        )

        # Get updated shift data
        cursor, conn = execute_stored_procedure(None, (shift_id,), commit=False, fallback_sql=fallback_get_sql)
        columns = [column[0] for column in cursor.description]
        row = cursor.fetchone()
        
        if row:
            return dict(zip(columns, row))
        return {"id": shift_id}
    finally:
        if conn:
            conn.close()
