"""
Process Service
Contains business logic and database operations for process management
Uses stored procedures for all database operations
"""
from database.db import execute_stored_procedure

def create_process(data, user_id):
    """
    Create a new process with optional technical values
    Args:
        data: Dictionary with:
            - 'processName': required
            - 'description': optional
            - 'workstationId': required
            - 'processTime': required (min/piece)
            - 'setupTime': required (min)
            - 'technicalValues': optional list of {name, value, unitId}
        user_id: ID of the user creating the process
    Returns:
        Dictionary with created process data including technical values
    """
    conn = None
    try:
        # Insert into Processes table
        fallback_sql = """
            INSERT INTO Processes
            (processName, description, workstationId, processTime, setupTime, isActive, CreatedBy, UpdatedBy, createdAt, updatedAt)
            VALUES (?, ?, ?, ?, ?, 1, ?, ?, SYSDATETIMEOFFSET(), SYSDATETIMEOFFSET())
        """
        cursor, conn = execute_stored_procedure(
            "sp_Process_Create",
            (
                data["processName"],
                data.get("description"),
                data["workstationId"],
                data["processTime"],
                data["setupTime"],
                user_id,
                user_id
            ),
            fallback_sql=fallback_sql
        )
        
        # Get the created process ID
        get_process_sql = """
            SELECT TOP 1 id, processName, description, workstationId, processTime, setupTime, 
                   isActive, CreatedBy, UpdatedBy, createdAt, updatedAt 
            FROM Processes 
            WHERE CreatedBy = ? 
            ORDER BY createdAt DESC
        """
        cursor, conn = execute_stored_procedure(None, (user_id,), commit=False, fallback_sql=get_process_sql)
        columns = [column[0] for column in cursor.description]
        row = cursor.fetchone()
        
        if not row:
            raise Exception("Failed to retrieve created process")
        
        process = dict(zip(columns, row))
        process_id = process["id"]
        
        # Insert technical values if provided
        technical_values = []
        if "technicalValues" in data and data["technicalValues"]:
            for tech_val in data["technicalValues"]:
                tech_sql = """
                    INSERT INTO ProcessTechnicals
                    (processId, unitId, name, value, isActive, CreatedBy, UpdatedBy, createdAt, updatedAt)
                    VALUES (?, ?, ?, ?, 1, ?, ?, SYSDATETIMEOFFSET(), SYSDATETIMEOFFSET())
                """
                tech_cursor, tech_conn = execute_stored_procedure(
                    "sp_ProcessTechnical_Create",
                    (
                        process_id,
                        tech_val.get("unitId"),
                        tech_val.get("name"),
                        tech_val.get("value"),
                        user_id,
                        user_id
                    ),
                    fallback_sql=tech_sql
                )
                
                # Get created technical value
                get_tech_sql = """
                    SELECT TOP 1 id, processId, unitId, name, value, isActive, CreatedBy, UpdatedBy, createdAt, updatedAt
                    FROM ProcessTechnicals
                    WHERE processId = ? AND CreatedBy = ?
                    ORDER BY createdAt DESC
                """
                tech_cursor, tech_conn = execute_stored_procedure(
                    None,
                    (process_id, user_id),
                    commit=False,
                    fallback_sql=get_tech_sql
                )
                tech_columns = [col[0] for col in tech_cursor.description]
                tech_row = tech_cursor.fetchone()
                if tech_row:
                    technical_values.append(dict(zip(tech_columns, tech_row)))
                if tech_conn:
                    tech_conn.close()
        
        # Add technical values to process response
        process["technicalValues"] = technical_values
        
        return process
    finally:
        if conn:
            conn.close()


def get_processes(page=1, per_page=10, sort_by="processName", sort_order="ASC"):
    """
    Get list of processes with pagination and sorting
    Args:
        page: Page number (default: 1)
        per_page: Items per page (default: 10)
        sort_by: Column to sort by (default: "processName")
        sort_order: Sort order "ASC" or "DESC" (default: "ASC")
    Returns:
        Dictionary with processes list and pagination info
    """
    conn = None
    try:
        # Validate sort parameters
        allowed_columns = ["processName", "id", "processTime", "setupTime", "createdAt"]
        if sort_by not in allowed_columns:
            sort_by = "processName"
        if sort_order.upper() not in ["ASC", "DESC"]:
            sort_order = "ASC"
        
        # Calculate offset
        offset = (page - 1) * per_page
        
        # Get total count
        count_sql = "SELECT COUNT(*) as total FROM Processes WHERE isActive = 1"
        cursor, conn = execute_stored_procedure(None, commit=False, fallback_sql=count_sql)
        total = cursor.fetchone()[0]
        
        # Get paginated and sorted processes
        fallback_sql = f"""
            SELECT id, processName, description, workstationId, processTime, setupTime, 
                   isActive, CreatedBy, UpdatedBy, createdAt, updatedAt
            FROM Processes 
            WHERE isActive = 1 
            ORDER BY {sort_by} {sort_order}
            OFFSET {offset} ROWS
            FETCH NEXT {per_page} ROWS ONLY
        """
        cursor, conn = execute_stored_procedure("sp_Process_GetAll", commit=False, fallback_sql=fallback_sql)
        
        columns = [column[0] for column in cursor.description]
        rows = cursor.fetchall()
        
        # Convert to dictionaries
        processes = []
        for row in rows:
            process = dict(zip(columns, row))
            # Get technical values for each process
            tech_cursor, tech_conn = execute_stored_procedure(
                "sp_ProcessTechnical_GetByProcessId",
                (process["id"],),
                commit=False,
                fallback_sql="""
                    SELECT id, processId, unitId, name, value, isActive, CreatedBy, UpdatedBy, createdAt, updatedAt
                    FROM ProcessTechnicals
                    WHERE processId = ? AND isActive = 1
                """
            )
            tech_columns = [col[0] for col in tech_cursor.description]
            tech_rows = tech_cursor.fetchall()
            process["technicalValues"] = [dict(zip(tech_columns, tech_row)) for tech_row in tech_rows]
            if tech_conn:
                tech_conn.close()
            processes.append(process)
        
        # Calculate total pages
        total_pages = (total + per_page - 1) // per_page
        
        return {
            "processes": processes,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages
        }
    finally:
        if conn:
            conn.close()


def search_processes(search, page=1, per_page=10, sort_by="processName", sort_order="ASC"):
    """
    Search active processes by name or description with pagination.
    """
    conn = None
    try:
        if not search:
            return get_processes(page=page, per_page=per_page, sort_by=sort_by, sort_order=sort_order)

        allowed_columns = ["processName", "id", "processTime", "setupTime", "createdAt"]
        if sort_by not in allowed_columns:
            sort_by = "processName"
        if sort_order.upper() not in ["ASC", "DESC"]:
            sort_order = "ASC"

        offset = (page - 1) * per_page
        like = f"%{search}%"

        count_sql = """
            SELECT COUNT(*) as total
            FROM Processes
            WHERE isActive = 1
              AND (processName LIKE ? OR description LIKE ?)
        """
        cursor, conn = execute_stored_procedure(
            None,
            (like, like),
            commit=False,
            fallback_sql=count_sql
        )
        total = cursor.fetchone()[0]

        fallback_sql = f"""
            SELECT id, processName, description, workstationId, processTime, setupTime,
                   isActive, CreatedBy, UpdatedBy, createdAt, updatedAt
            FROM Processes
            WHERE isActive = 1
              AND (processName LIKE ? OR description LIKE ?)
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
        processes = [dict(zip(columns, row)) for row in rows]

        total_pages = (total + per_page - 1) // per_page
        return {
            "processes": processes,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
        }
    finally:
        if conn:
            conn.close()

def get_process_by_id(process_id):
    """
    Get a single process by ID with its technical values
    Args:
        process_id: ID of the process to retrieve
    Returns:
        Dictionary with process data including technical values, or None if not found
    """
    conn = None
    try:
        cursor, conn = execute_stored_procedure(
            "sp_Process_GetById",
            (process_id,),
            commit=False,
            fallback_sql="""
                SELECT id, processName, description, workstationId, processTime, setupTime, 
                       isActive, CreatedBy, UpdatedBy, createdAt, updatedAt
                FROM Processes 
                WHERE id = ? AND isActive = 1
            """
        )
        columns = [column[0] for column in cursor.description]
        row = cursor.fetchone()
        
        if not row:
            return None
        
        process = dict(zip(columns, row))
        
        # Get technical values for the process
        tech_sql = """
            SELECT id, processId, unitId, name, value, isActive, CreatedBy, UpdatedBy, createdAt, updatedAt
            FROM ProcessTechnicals
            WHERE processId = ? AND isActive = 1
        """
        tech_cursor, tech_conn = execute_stored_procedure(
            None,
            (process_id,),
            commit=False,
            fallback_sql=tech_sql
        )
        tech_columns = [col[0] for col in tech_cursor.description]
        tech_rows = tech_cursor.fetchall()
        process["technicalValues"] = [dict(zip(tech_columns, tech_row)) for tech_row in tech_rows]
        if tech_conn:
            tech_conn.close()
        
        return process
    finally:
        if conn:
            conn.close()


def update_process(data, user_id):
    """
    Update an existing process
    Only allows update if isActive = 1
    Args:
        data: Dictionary with 'id', 'processName', 'description', 'workstationId', 'processTime', 'setupTime'
        user_id: ID of the user updating the process
    Returns:
        Dictionary with updated process data
    """
    conn = None
    try:
        # Get existing process to preserve values not provided in update and check isActive
        get_existing_sql = """
            SELECT processName, description, workstationId, processTime, setupTime, isActive
            FROM Processes 
            WHERE id = ?
        """
        cursor, conn = execute_stored_procedure(None, (data["id"],), commit=False, fallback_sql=get_existing_sql)
        existing = cursor.fetchone()
        
        if not existing:
            raise Exception("Process not found")
        
        existing_columns = [column[0] for column in cursor.description]
        existing_dict = dict(zip(existing_columns, existing))
        
        if not existing_dict.get("isActive"):  # isActive is False (0)
            raise Exception("Cannot update inactive process")
        
        # Use provided values or keep existing ones
        process_name = data.get("processName", existing_dict.get("processName"))
        description = data.get("description") if "description" in data else existing_dict.get("description")
        workstation_id = data.get("workstationId", existing_dict.get("workstationId"))
        process_time = data.get("processTime", existing_dict.get("processTime"))
        setup_time = data.get("setupTime", existing_dict.get("setupTime"))
        
        fallback_sql = """
            UPDATE Processes
            SET processName = ?, description = ?, workstationId = ?, processTime = ?, setupTime = ?,
                UpdatedBy = ?, updatedAt = SYSDATETIMEOFFSET()
            WHERE id = ?
        """
        cursor, conn = execute_stored_procedure(
            "sp_Process_Update",
            (
                process_name,
                description,
                workstation_id,
                process_time,
                setup_time,
                user_id,
                data["id"]
            ),
            fallback_sql=fallback_sql
        )
        
        # Get updated process data
        get_sql = """
            SELECT id, processName, description, workstationId, processTime, setupTime, 
                   isActive, CreatedBy, UpdatedBy, createdAt, updatedAt
            FROM Processes 
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


def delete_process(process_id, user_id):
    """
    Soft delete a process (sets isActive = 0).
    Only allows delete once; if already deleted (isActive = 0), raises an error.
    Args:
        process_id: ID of the process to delete
        user_id: ID of the user performing the deletion
    Returns:
        Dictionary with updated process data
    """
    conn = None
    try:
        # Get updated process data
        get_sql = """
            SELECT id, processName, description, workstationId, processTime, setupTime, 
                   isActive, CreatedBy, UpdatedBy, createdAt, updatedAt
            FROM Processes 
            WHERE id = ?
        """
        cursor, conn = execute_stored_procedure(None, (process_id,), commit=False, fallback_sql=get_sql)
        columns = [column[0] for column in cursor.description]
        row = cursor.fetchone()

        if not row:
            raise Exception("Process not found")

        current = dict(zip(columns, row))
        if not current.get("isActive"):
            raise Exception("Process already deleted")

        # Soft delete: set isActive = 0
        fallback_sql = """
            UPDATE Processes
            SET isActive = 0, UpdatedBy = ?, updatedAt = SYSDATETIMEOFFSET()
            WHERE id = ?
        """
        cursor, conn = execute_stored_procedure(
            "sp_Process_Delete",
            (user_id, process_id),
            fallback_sql=fallback_sql
        )

        # Get updated process data
        cursor, conn = execute_stored_procedure(None, (process_id,), commit=False, fallback_sql=get_sql)
        columns = [column[0] for column in cursor.description]
        row = cursor.fetchone()
        
        if row:
            return dict(zip(columns, row))
        return {"id": process_id}
    finally:
        if conn:
            conn.close()

