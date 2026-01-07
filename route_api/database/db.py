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
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        if procedure_name:
            if params:
                placeholders = ', '.join(['?' for _ in params])
                cursor.execute(f"EXEC {procedure_name} {placeholders}", params)
            else:
                cursor.execute(f"EXEC {procedure_name}")
        else:
            cursor.execute(fallback_sql, params or [])

        if commit:
            conn.commit()

        return cursor, conn

    except pyodbc.ProgrammingError as e:
        # ONLY fallback if procedure truly does not exist
        msg = str(e)
        if fallback_sql and "Could not find stored procedure" in msg:
            conn.close()
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(fallback_sql, params or [])
            if commit:
                conn.commit()
            return cursor, conn

        conn.close()
        raise Exception(msg)

    except pyodbc.Error as e:
        conn.close()
        raise Exception(e.args[1] if len(e.args) > 1 else str(e))
