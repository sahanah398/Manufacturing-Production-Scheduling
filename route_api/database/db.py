"""
Database Connection Module
Handles connection to SQL database using pyodbc
"""
import pyodbc

def get_available_driver():
    """
    Automatically detect and return an available ODBC driver
    Tries multiple driver versions in order of preference
    Returns:
        Name of available driver
    Raises:
        Exception if no driver is found
    """
    # List of ODBC drivers to try (in order of preference)
    drivers = [
        "ODBC Driver 18 for SQL Server",
        "ODBC Driver 17 for SQL Server",
        "ODBC Driver 13 for SQL Server",
        "SQL Server Native Client 11.0",
        "SQL Server"
    ]
    
    # Find which drivers are installed on the system
    available_drivers = [d for d in pyodbc.drivers() if d in drivers]
    if available_drivers:
        # Return the first available driver (preferred version)
        return available_drivers[0]
    
    # If no driver found, raise exception with helpful error message
    raise Exception(f"No ODBC driver found. Available drivers: {pyodbc.drivers()}")

def get_db_connection():
    """
    Create and return a connection to SQL database
    Returns:
        pyodbc connection object
    """
    # Get available ODBC driver
    driver = get_available_driver()
    
    # Build connection string for SQL database
    connection_string = (
        f"DRIVER={{{driver}}};"                    # ODBC driver name
        "SERVER=hiqserver.database.windows.net,1433;"  # Database server address and port
        "DATABASE=iERP;"                            # Database name
        "UID=hiquser;"                              # Username
        "PWD=Hiqsql@52;"                            # Password
        "Encrypt=yes;"                              # Enable encryption
        "TrustServerCertificate=no;"                # Verify server certificate
        "Connection Timeout=30;"                    # Connection timeout in seconds
    )
    
    # Create and return connection
    return pyodbc.connect(connection_string)

def execute_stored_procedure(procedure_name, params=None, commit=True, fallback_sql=None):
    """
    Execute a stored procedure and return cursor and connection
    Falls back to direct SQL if stored procedure doesn't exist
    Args:
        procedure_name: Name of the stored procedure (e.g., 'sp_Unit_Create')
        params: List or tuple of parameters to pass to the stored procedure
        commit: Whether to commit the transaction (True for INSERT/UPDATE/DELETE, False for SELECT)
        fallback_sql: SQL query to use if stored procedure doesn't exist (optional)
    Returns:
        Tuple of (cursor, connection) - caller is responsible for closing connection
    """
    conn = None
    try:
        # Get database connection
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Build the stored procedure call with parameters
        if params:
            # Create parameter placeholders (?, ?, ?) for each parameter
            placeholders = ', '.join(['?' for _ in params])
            sql = f"EXEC {procedure_name} {placeholders}"
            cursor.execute(sql, params)
        else:
            # No parameters - execute stored procedure directly
            cursor.execute(f"EXEC {procedure_name}")
        
        # Commit transaction if it's a write operation (INSERT, UPDATE, DELETE)
        if commit:
            conn.commit()
        
        # Return both cursor and connection so caller can fetch results and close connection
        return cursor, conn
    except pyodbc.ProgrammingError as e:
        # Check if error is "stored procedure not found" (error code 2812 or 42000)
        error_code = str(e.args[0]) if e.args else ""
        if "2812" in error_code or "Could not find stored procedure" in str(e):
            # Stored procedure doesn't exist - try fallback SQL if provided
            if fallback_sql:
                if conn:
                    conn.close()
                # Retry with direct SQL
                conn = get_db_connection()
                cursor = conn.cursor()
                if params:
                    cursor.execute(fallback_sql, params)
                else:
                    cursor.execute(fallback_sql)
                if commit:
                    conn.commit()
                return cursor, conn
            else:
                # No fallback provided - raise original error
                if conn:
                    conn.close()
                raise Exception(f"Stored procedure '{procedure_name}' not found and no fallback SQL provided")
        else:
            # Different error - re-raise
            if conn:
                conn.close()
            raise e
    except Exception as e:
        # Close connection on error
        if conn:
            conn.close()
        raise e


