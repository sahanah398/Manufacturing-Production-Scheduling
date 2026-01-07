# Route API - Flask REST API Documentation

## 📋 Table of Contents
- [Project Overview](#project-overview)
- [Project Structure](#project-structure)
- [Technology Stack](#technology-stack)
- [Setup Instructions](#setup-instructions)
- [API Endpoints](#api-endpoints)
- [Authentication](#authentication)
- [Database Configuration](#database-configuration)
- [Code Architecture](#code-architecture)
- [Stored Procedures](#stored-procedures)

---

## 🎯 Project Overview

This is a Flask-based REST API for managing units with JWT authentication. The API provides endpoints for user authentication and CRUD operations on units. The system uses SQL database and implements stored procedures with automatic fallback to direct SQL queries.

**Key Features:**
- JWT-based authentication
- Unit management (Create, Read, Update, Delete)
- Stored procedure support with SQL fallback
- SQL database integration
- RESTful API design

---

## 📁 Project Structure

```
route_api/
│
├── app.py                      # Main Flask application entry point
├── requirements.txt            # Python dependencies
├── README.md                   # This documentation file
│
├── database/
│   ├── __init__.py            # Package initialization
│   └── db.py                  # Database connection and stored procedure execution
│
├── auth/
│   ├── __init__.py            # Package initialization
│   ├── auth_controller.py     # Authentication HTTP request handlers
│   └── auth_service.py         # Authentication business logic
│
├── units/
│   ├── __init__.py            # Package initialization
│   ├── unit_controller.py    # Unit management HTTP request handlers
│   └── unit_service.py        # Unit management business logic
│
└── utils/
    ├── __init__.py            # Package initialization
    └── jwt_utils.py           # JWT token generation and validation utilities
```

---

## 🛠 Technology Stack

- **Framework:** Flask 2.3.3
- **Database:** SQL Database (via pyodbc)
- **Authentication:** JWT (PyJWT 2.8.0)
- **Python Version:** 3.12+

---

## 🚀 Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Database Configuration

Update the database connection details in `database/db.py`:
- Configure your database server, database name, username, and password
- The connection uses pyodbc for database connectivity

### 3. Run the Application

```bash
python app.py
```

The API will be available at: `http://localhost:5000`

---

## 📡 API Endpoints

### Authentication Endpoints

#### 1. Login
- **URL:** `/login`
- **Method:** `POST`
- **Authentication:** Not required
- **Request Body:**
  ```json
  {
    "username": "admin",
    "password": "admin123"
  }
  ```
- **Response (Success):**
  ```json
  {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
  ```
- **Response (Error):**
  ```json
  {
    "message": "Invalid credentials"
  }
  ```
- **Status Codes:** 200 (Success), 401 (Unauthorized)

---

### Unit Management Endpoints

All unit endpoints require JWT authentication. Include the token in the `Authorization` header.

#### 1. Create Unit
- **URL:** `/unit/create`
- **Method:** `POST`
- **Authentication:** Required (JWT Token)
- **Request Headers:**
  ```
  Authorization: <JWT_TOKEN>
  ```
- **Request Body:**
  ```json
  {
    "unitName": "Kilogram",
    "description": "Unit of mass",
    "unitSymbol": "kg"
  }
  ```
- **Response:**
  ```json
  {
    "message": "Unit created"
  }
  ```
- **Status Codes:** 200 (Success), 401 (Unauthorized)

#### 2. List Units
- **URL:** `/unit/list`
- **Method:** `POST`
- **Authentication:** Required (JWT Token)
- **Request Headers:**
  ```
  Authorization: <JWT_TOKEN>
  ```
- **Response:**
  ```json
  [
    {
      "id": 1,
      "unitName": "Kilogram",
      "unitSymbol": "kg",
      "description": "Unit of mass"
    },
    {
      "id": 2,
      "unitName": "Meter",
      "unitSymbol": "m",
      "description": "Unit of length"
    }
  ]
  ```
- **Status Codes:** 200 (Success), 401 (Unauthorized)

#### 3. Update Unit
- **URL:** `/unit/update`
- **Method:** `POST`
- **Authentication:** Required (JWT Token)
- **Request Headers:**
  ```
  Authorization: <JWT_TOKEN>
  ```
- **Request Body:**
  ```json
  {
    "id": 1,
    "unitName": "Kilogram Updated",
    "description": "Updated description",
    "unitSymbol": "kg"
  }
  ```
- **Response:**
  ```json
  {
    "message": "Unit updated"
  }
  ```
- **Status Codes:** 200 (Success), 401 (Unauthorized)

#### 4. Delete Unit
- **URL:** `/unit/delete`
- **Method:** `POST`
- **Authentication:** Required (JWT Token)
- **Request Headers:**
  ```
  Authorization: <JWT_TOKEN>
  ```
- **Request Body:**
  ```json
  {
    "id": 1
  }
  ```
- **Response:**
  ```json
  {
    "message": "Unit deleted"
  }
  ```
- **Status Codes:** 200 (Success), 401 (Unauthorized)

---

## 🔐 Authentication

### JWT Token Flow

1. **Login:** User sends credentials to `/login` endpoint
2. **Token Generation:** Server validates credentials and generates JWT token
3. **Token Usage:** Client includes token in `Authorization` header for protected routes
4. **Token Validation:** `@token_required` decorator validates token on each request
5. **Token Expiration:** Tokens expire after 2 hours

### Token Structure

```json
{
  "user_id": 1,
  "exp": 1234567890
}
```

### Using the Token

Include the JWT token in the request header:
```
Authorization: <your_jwt_token>
```

---

## 🗄 Database Configuration

### Connection Details

The database connection is configured in `database/db.py`:
- **Driver Detection:** Automatically detects available ODBC drivers
- **Connection String:** Configured for SQL database with encryption support
- **Connection Pooling:** Each request creates a new connection (closed after use)

### Database Schema

#### Units Table
```sql
CREATE TABLE Units (
    id INT PRIMARY KEY IDENTITY(1,1),
    unitName NVARCHAR(255) NOT NULL,
    description NVARCHAR(MAX),
    unitSymbol NVARCHAR(50),
    isActive BIT DEFAULT 1,
    CreatedBy INT,
    createdAt DATETIMEOFFSET,
    UpdatedBy INT,
    updatedAt DATETIMEOFFSET
);
```

---

## 🏗 Code Architecture

### Architecture Pattern

The project follows a **Controller-Service-Data Access** pattern:

```
Controller (HTTP Layer)
    ↓
Service (Business Logic)
    ↓
Database (Data Access)
```

### Module Descriptions

#### 1. `app.py`
- **Purpose:** Flask application initialization
- **Responsibilities:**
  - Create Flask app instance
  - Register blueprints (route modules)
  - Start development server

#### 2. `database/db.py`
- **Purpose:** Database connection and stored procedure execution
- **Key Functions:**
  - `get_available_driver()`: Detects available ODBC driver
  - `get_db_connection()`: Creates database connection
  - `execute_stored_procedure()`: Executes stored procedures with SQL fallback

#### 3. `auth/auth_controller.py`
- **Purpose:** Handle HTTP requests for authentication
- **Endpoints:**
  - `/login` - User login

#### 4. `auth/auth_service.py`
- **Purpose:** Authentication business logic
- **Functions:**
  - `login_user()`: Validates credentials and generates JWT token

#### 5. `units/unit_controller.py`
- **Purpose:** Handle HTTP requests for unit management
- **Endpoints:**
  - `/unit/create` - Create unit
  - `/unit/list` - List all units
  - `/unit/update` - Update unit
  - `/unit/delete` - Delete unit

#### 6. `units/unit_service.py`
- **Purpose:** Unit management business logic
- **Functions:**
  - `create_unit()`: Create new unit
  - `get_units()`: Retrieve all active units
  - `update_unit()`: Update existing unit
  - `delete_unit()`: Soft delete unit

#### 7. `utils/jwt_utils.py`
- **Purpose:** JWT token utilities
- **Functions:**
  - `generate_token()`: Create JWT token
  - `token_required()`: Decorator for protecting routes

---

## 📝 Stored Procedures

The system is designed to use stored procedures but includes automatic fallback to direct SQL queries if stored procedures don't exist.

### Required Stored Procedures

When you're ready to implement stored procedures, create these in your database:

#### 1. `sp_Unit_Create`
```sql
CREATE PROCEDURE sp_Unit_Create
    @unitName NVARCHAR(255),
    @description NVARCHAR(MAX),
    @unitSymbol NVARCHAR(50),
    @createdBy INT
AS
BEGIN
    INSERT INTO Units (unitName, description, unitSymbol, isActive, CreatedBy, createdAt, updatedAt)
    VALUES (@unitName, @description, @unitSymbol, 1, @createdBy, SYSDATETIMEOFFSET(), SYSDATETIMEOFFSET())
END
```

#### 2. `sp_Unit_GetAll`
```sql
CREATE PROCEDURE sp_Unit_GetAll
AS
BEGIN
    SELECT id, unitName, unitSymbol, description 
    FROM Units 
    WHERE isActive = 1
END
```

#### 3. `sp_Unit_Update`
```sql
CREATE PROCEDURE sp_Unit_Update
    @id INT,
    @unitName NVARCHAR(255),
    @description NVARCHAR(MAX),
    @unitSymbol NVARCHAR(50),
    @updatedBy INT
AS
BEGIN
    UPDATE Units
    SET unitName = @unitName,
        description = @description,
        unitSymbol = @unitSymbol,
        UpdatedBy = @updatedBy,
        updatedAt = SYSDATETIMEOFFSET()
    WHERE id = @id
END
```

#### 4. `sp_Unit_Delete`
```sql
CREATE PROCEDURE sp_Unit_Delete
    @id INT,
    @updatedBy INT
AS
BEGIN
    UPDATE Units
    SET isActive = 0,
        UpdatedBy = @updatedBy,
        updatedAt = SYSDATETIMEOFFSET()
    WHERE id = @id
END
```

#### 5. `sp_User_Login`
```sql
CREATE PROCEDURE sp_User_Login
    @username VARCHAR(255),
    @password VARCHAR(255)
AS
BEGIN
    SELECT id 
    FROM Users 
    WHERE username = @username 
      AND password = @password 
      AND isActive = 1
END
```

### Fallback Mechanism

If stored procedures don't exist, the system automatically uses direct SQL queries. No code changes are needed when you add stored procedures later - the system will automatically detect and use them.

---

## 🔄 Request Flow Example

### Example: Creating a Unit

1. **Client Request:**
   ```
   POST /unit/create
   Headers: Authorization: <JWT_TOKEN>
   Body: {"unitName": "Kilogram", "unitSymbol": "kg"}
   ```

2. **Controller (`unit_controller.py`):**
   - Validates JWT token via `@token_required` decorator
   - Extracts `request.user_id` from token
   - Calls service function

3. **Service (`unit_service.py`):**
   - Calls `create_unit()` function
   - Prepares data for database

4. **Database (`db.py`):**
   - Tries to execute `sp_Unit_Create` stored procedure
   - Falls back to direct SQL if SP doesn't exist
   - Returns result

5. **Response:**
   ```json
   {"message": "Unit created"}
   ```

---

## 🧪 Testing the API

### Using cURL

#### Login
```bash
curl -X POST http://localhost:5000/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

#### Create Unit (with token)
```bash
curl -X POST http://localhost:5000/unit/create \
  -H "Content-Type: application/json" \
  -H "Authorization: <YOUR_JWT_TOKEN>" \
  -d '{"unitName":"Kilogram","unitSymbol":"kg","description":"Unit of mass"}'
```

#### List Units (with token)
```bash
curl -X POST http://localhost:5000/unit/list \
  -H "Content-Type: application/json" \
  -H "Authorization: <YOUR_JWT_TOKEN>"
```

### Using Postman

1. **Login Request:**
   - Method: POST
   - URL: `http://localhost:5000/login`
   - Body (raw JSON):
     ```json
     {
       "username": "admin",
       "password": "admin123"
     }
     ```

2. **Protected Requests:**
   - Copy the token from login response
   - Add header: `Authorization: <token>`
   - Make requests to unit endpoints

---

## 📊 Error Handling

### Common Error Responses

#### 401 Unauthorized
```json
{
  "message": "Token required"
}
```
or
```json
{
  "message": "Invalid or expired token"
}
```

#### 400 Bad Request
```json
{
  "message": "Invalid credentials"
}
```

---

## 🔒 Security Considerations

1. **JWT Secret Key:** Currently hardcoded in `utils/jwt_utils.py`. Should be moved to environment variables in production.

2. **Database Credentials:** Currently hardcoded in `database/db.py`. Should use environment variables or secure configuration.

3. **Password Storage:** Current implementation uses plain text. Should use hashing (bcrypt) in production.

4. **HTTPS:** Use HTTPS in production to encrypt data in transit.

---

## 📈 Future Enhancements

- [ ] Environment variable configuration
- [ ] Password hashing (bcrypt)
- [ ] User registration endpoint
- [ ] Password reset functionality
- [ ] API rate limiting
- [ ] Logging and monitoring
- [ ] Unit tests
- [ ] API documentation (Swagger/OpenAPI)

---

## 👥 Contact & Support

For questions or issues, please contact the development team.

---

**Last Updated:** 2024
**Version:** 1.0.0

