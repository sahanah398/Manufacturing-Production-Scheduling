"""
Workstation Service
Contains business logic and database operations for workstation management
Uses stored procedures for all database operations
"""
from database.db import execute_stored_procedure


def create_workstation(data, user_id):
    """
    Create a new workstation with optional shift assignments
    Args:
        data: dict with:
          - 'workstationName': required
          - 'description': optional
          - 'shifts': optional list of {shiftId, startDate, endDate}
        user_id: ID of the user creating the workstation
    Returns:
        dict with created workstation and shifts data
    """
    conn = None
    try:
        fallback_sql = """
            INSERT INTO Workstations
            (workstationName, description, isActive, CreatedBy, UpdatedBy, createdAt, updatedAt)
            VALUES (?, ?, 1, ?, ?, SYSDATETIMEOFFSET(), SYSDATETIMEOFFSET())
        """
        cursor, conn = execute_stored_procedure(
            "sp_Workstation_Create",
            (
                data["workstationName"],
                data.get("description"),
                user_id,
                user_id
            ),
            fallback_sql=fallback_sql
        )

        # Fetch the created workstation
        fallback_get_sql = "SELECT TOP 1 id, workstationName, description, isActive, CreatedBy, UpdatedBy, createdAt, updatedAt FROM Workstations WHERE CreatedBy = ? ORDER BY createdAt DESC"
        cursor, conn = execute_stored_procedure(None, (user_id,), commit=False, fallback_sql=fallback_get_sql)
        columns = [column[0] for column in cursor.description]
        row = cursor.fetchone()

        if not row:
            return {"workstationName": data.get("workstationName")}

        workstation = dict(zip(columns, row))
        workstation_id = workstation["id"]

        # Insert shift assignments if provided
        shifts_list = []
        if "shifts" in data and data["shifts"]:
            for shift in data["shifts"]:
                # Validate shift exists to avoid FK constraint errors
                check_shift_sql = "SELECT id FROM MasterShifts WHERE id = ? AND isActive = 1"
                check_cursor, _ = execute_stored_procedure(None, (shift["shiftId"],), commit=False, fallback_sql=check_shift_sql)
                if not check_cursor.fetchone():
                    raise Exception(f"Invalid shiftId: {shift['shiftId']}")
                shift_insert_sql = """
                    INSERT INTO WorkstationShifts
                    (workstationId, shiftId, startDate, endDate, isActive, createdAt, updatedAt)
                    VALUES (?, ?, ?, ?, 1, SYSDATETIMEOFFSET(), SYSDATETIMEOFFSET())
                """
                shift_cursor, _ = execute_stored_procedure(
                    "sp_WorkstationShift_Create",
                    (
                        workstation_id,
                        shift["shiftId"],
                        shift["startDate"],
                        shift["endDate"]
                    ),
                    fallback_sql=shift_insert_sql
                )

                # Fetch the created shift assignment with shift details
                shift_fetch_sql = """
                    SELECT ws.id as shiftAssignmentId, ms.id as shiftId, ms.name as shiftName, 
                           ws.startDate, ws.endDate
                    FROM WorkstationShifts ws
                    INNER JOIN MasterShifts ms ON ws.shiftId = ms.id
                    WHERE ws.workstationId = ? AND ws.shiftId = ?
                    ORDER BY ws.createdAt DESC
                """
                shift_cursor, _ = execute_stored_procedure(None, (workstation_id, shift["shiftId"]), commit=False, fallback_sql=shift_fetch_sql)
                shift_cols = [col[0] for col in shift_cursor.description]
                shift_row = shift_cursor.fetchone()
                if shift_row:
                    shifts_list.append(dict(zip(shift_cols, shift_row)))

        workstation["shifts"] = shifts_list
        return workstation
    finally:
        if conn:
            conn.close()


def get_workstations(page=1, per_page=10, sort_by="workstationName", sort_order="ASC"):
    """
    Retrieve active workstations with pagination, sorting, and assigned shifts
    Returns dict with workstations list (each with shifts) and pagination metadata
    """
    conn = None
    try:
        allowed_columns = ["workstationName", "id", "description"]
        if sort_by not in allowed_columns:
            sort_by = "workstationName"
        if sort_order.upper() not in ["ASC", "DESC"]:
            sort_order = "ASC"

        offset = (page - 1) * per_page

        count_sql = "SELECT COUNT(*) as total FROM Workstations WHERE isActive = 1"
        cursor, conn = execute_stored_procedure(None, commit=False, fallback_sql=count_sql)
        total = cursor.fetchone()[0]

        # Get paginated workstations
        fallback_sql = f"""
            SELECT id, workstationName, description, isActive, CreatedBy, UpdatedBy
            FROM Workstations
            WHERE isActive = 1
            ORDER BY {sort_by} {sort_order}
            OFFSET {offset} ROWS
            FETCH NEXT {per_page} ROWS ONLY
        """
        cursor, conn = execute_stored_procedure("sp_Workstation_GetAll", commit=False, fallback_sql=fallback_sql)

        columns = [column[0] for column in cursor.description]
        rows = cursor.fetchall()
        workstations = [dict(zip(columns, row)) for row in rows]

        # Fetch shifts for each workstation
        for ws in workstations:
            ws_id = ws["id"]
            shifts_sql = """
                SELECT ws.id as shiftAssignmentId, ms.id as shiftId, ms.name as shiftName, 
                       ws.startDate, ws.endDate
                FROM WorkstationShifts ws
                INNER JOIN MasterShifts ms ON ws.shiftId = ms.id
                WHERE ws.workstationId = ? AND ws.isActive = 1
            """
            shift_cursor, _ = execute_stored_procedure(None, (ws_id,), commit=False, fallback_sql=shifts_sql)
            shift_columns = [col[0] for col in shift_cursor.description]
            shift_rows = shift_cursor.fetchall()
            ws["shifts"] = [dict(zip(shift_columns, row)) for row in shift_rows]

        total_pages = (total + per_page - 1) // per_page
        return {
            "workstations": workstations,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages
        }
    finally:
        if conn:
            conn.close()


def search_workstations(search, page=1, per_page=10, sort_by="workstationName", sort_order="ASC"):
    """
    Search active workstations by name or description with pagination.
    """
    conn = None
    try:
        if not search:
            return get_workstations(page=page, per_page=per_page, sort_by=sort_by, sort_order=sort_order)

        allowed_columns = ["workstationName", "id", "description"]
        if sort_by not in allowed_columns:
            sort_by = "workstationName"
        if sort_order.upper() not in ["ASC", "DESC"]:
            sort_order = "ASC"

        offset = (page - 1) * per_page
        like = f"%{search}%"

        count_sql = """
            SELECT COUNT(*) as total
            FROM Workstations
            WHERE isActive = 1
              AND (workstationName LIKE ? OR description LIKE ?)
        """
        cursor, conn = execute_stored_procedure(
            None,
            (like, like),
            commit=False,
            fallback_sql=count_sql
        )
        total = cursor.fetchone()[0]

        # Get paginated workstations
        fallback_sql = f"""
            SELECT id, workstationName, description, isActive, CreatedBy, UpdatedBy
            FROM Workstations
            WHERE isActive = 1
              AND (workstationName LIKE ? OR description LIKE ?)
            ORDER BY {sort_by} {sort_order}
            OFFSET {offset} ROWS
            FETCH NEXT {per_page} ROWS ONLY
        """
        cursor, conn = execute_stored_procedure(
            "sp_Workstation_GetAll",
            (like, like),
            commit=False,
            fallback_sql=fallback_sql
        )

        columns = [column[0] for column in cursor.description]
        rows = cursor.fetchall()
        workstations = [dict(zip(columns, row)) for row in rows]

        # Fetch shifts for each workstation
        for ws in workstations:
            ws_id = ws["id"]
            shifts_sql = """
                SELECT ws.id as shiftAssignmentId, ms.id as shiftId, ms.name as shiftName, 
                       ws.startDate, ws.endDate
                FROM WorkstationShifts ws
                INNER JOIN MasterShifts ms ON ws.shiftId = ms.id
                WHERE ws.workstationId = ? AND ws.isActive = 1
            """
            shifts_cursor, _ = execute_stored_procedure(
                None,
                (ws_id,),
                commit=False,
                fallback_sql=shifts_sql
            )
            shift_cols = [col[0] for col in shifts_cursor.description]
            shift_rows = shifts_cursor.fetchall()
            ws["shifts"] = [dict(zip(shift_cols, r)) for r in shift_rows]

        total_pages = (total + per_page - 1) // per_page

        return {
            "workstations": workstations,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
        }
    finally:
        if conn:
            conn.close()


def update_workstation(data, user_id):
    if not data:
        raise Exception("Request body is required")

    workstation_id = data.get("id")
    workstation_name = data.get("workstationName")
    description = data.get("description")

    if not workstation_id:
        raise Exception("id is required")
    if not workstation_name:
        raise Exception("workstationName is required")

    conn = None
    try:
        # Check if workstation exists and is active
        check_sql = "SELECT isActive FROM Workstations WHERE id = ?"
        cursor, conn = execute_stored_procedure(None, (workstation_id,), commit=False, fallback_sql=check_sql)
        check_row = cursor.fetchone()
        
        if not check_row:
            raise Exception("Workstation not found")
        
        if not check_row[0]:  # isActive is False (0)
            raise Exception("Cannot update inactive workstation")
        
        fallback_sql = """
            UPDATE Workstations
            SET workstationName = ?,
                description = ?,
                UpdatedBy = ?,
                updatedAt = SYSDATETIMEOFFSET()
            WHERE id = ?
        """

        execute_stored_procedure(
            "sp_Workstation_Update",
            (
                workstation_name,
                description,
                user_id,
                workstation_id
            ),
            fallback_sql=fallback_sql
        )

        # Fetch updated record
        fetch_sql = """
            SELECT id, workstationName, description, isActive,
                   CreatedBy, UpdatedBy, createdAt, updatedAt
            FROM Workstations
            WHERE id = ?
        """
        cursor, conn = execute_stored_procedure(
            None,
            (workstation_id,),
            commit=False,
            fallback_sql=fetch_sql
        )

        row = cursor.fetchone()
        if not row:
            raise Exception("Workstation not found")

        columns = [c[0] for c in cursor.description]
        return dict(zip(columns, row))

    finally:
        if conn:
            conn.close()



def delete_workstation(workstation_id, user_id):
    """
    Toggle isActive on Workstations and return updated row
    """
    conn = None
    try:
        fallback_sql = """
            UPDATE Workstations
            SET isActive = CASE WHEN isActive = 1 THEN 0 ELSE 1 END, UpdatedBy = ?, updatedAt = SYSDATETIMEOFFSET()
            WHERE id = ?
        """
        cursor, conn = execute_stored_procedure(
            "sp_Workstation_Delete",
            (user_id, workstation_id),
            fallback_sql=fallback_sql
        )

        fallback_get_sql = "SELECT id, workstationName, description, isActive, CreatedBy, UpdatedBy, createdAt, updatedAt FROM Workstations WHERE id = ?"
        cursor, conn = execute_stored_procedure(None, (workstation_id,), commit=False, fallback_sql=fallback_get_sql)
        columns = [column[0] for column in cursor.description]
        row = cursor.fetchone()
        if row:
            return dict(zip(columns, row))
        return {"id": workstation_id}
    finally:
        if conn:
            conn.close()
