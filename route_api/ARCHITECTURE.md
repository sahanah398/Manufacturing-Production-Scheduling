# API Architecture Documentation

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      Client Application                      │
│                    (Web/Mobile/Postman)                      │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           │ HTTP Requests
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                    Flask Application                        │
│                      (app.py)                               │
│                                                              │
│  ┌──────────────────┐         ┌──────────────────┐          │
│  │  Auth Blueprint  │         │  Unit Blueprint  │          │
│  │  (auth_bp)      │         │  (unit_bp)       │          │
│  └────────┬────────┘         └────────┬─────────┘          │
│           │                            │                     │
│           │                            │                     │
└───────────┼────────────────────────────┼─────────────────────┘
            │                            │
            │                            │
┌───────────▼────────────┐   ┌──────────▼─────────────┐
│  Auth Controller        │   │  Unit Controller      │
│  (auth_controller.py)   │   │  (unit_controller.py) │
│                         │   │                       │
│  - /login               │   │  - /unit/create       │
│                         │   │  - /unit/list         │
│                         │   │  - /unit/update       │
│                         │   │  - /unit/delete       │
└──────────┬─────────────┘   └──────────┬────────────┘
           │                             │
           │                             │
┌──────────▼─────────────┐   ┌──────────▼─────────────┐
│  Auth Service           │   │  Unit Service          │
│  (auth_service.py)      │   │  (unit_service.py)     │
│                         │   │                        │
│  - login_user()         │   │  - create_unit()        │
│                         │   │  - get_units()          │
│                         │   │  - update_unit()        │
│                         │   │  - delete_unit()        │
└──────────┬─────────────┘   └──────────┬─────────────┘
           │                             │
           │                             │
           └──────────────┬──────────────┘
                          │
                          │
           ┌──────────────▼──────────────┐
           │   Database Layer            │
           │   (database/db.py)          │
           │                             │
           │  - get_db_connection()       │
           │  - execute_stored_procedure()│
           │    (with SQL fallback)      │
           └──────────────┬──────────────┘
                          │
                          │
           ┌──────────────▼──────────────┐
           │   SQL Database              │
           │   (iERP Database)           │
           │                             │
           │  - Units Table              │
           │  - Stored Procedures        │
           │    (optional)               │
           └─────────────────────────────┘
```

## Authentication Flow

```
┌─────────┐
│ Client  │
└────┬────┘
     │
     │ 1. POST /login
     │    {username, password}
     │
┌────▼────────────────────────────────────┐
│  Auth Controller                       │
│  - Receives credentials                │
└────┬───────────────────────────────────┘
     │
     │ 2. Calls login_user()
     │
┌────▼────────────────────────────────────┐
│  Auth Service                          │
│  - Validates credentials               │
│  - Calls database (sp_User_Login)      │
└────┬───────────────────────────────────┘
     │
     │ 3. Database query
     │
┌────▼────────────────────────────────────┐
│  Database                              │
│  - Returns user_id if valid            │
└────┬───────────────────────────────────┘
     │
     │ 4. user_id returned
     │
┌────▼────────────────────────────────────┐
│  JWT Utils                             │
│  - generate_token(user_id)             │
│  - Creates JWT with 2hr expiration     │
└────┬───────────────────────────────────┘
     │
     │ 5. JWT Token
     │
┌────▼────────────────────────────────────┐
│  Response to Client                    │
│  {token: "eyJhbGci..."}                │
└────────────────────────────────────────┘
```

## Protected Route Flow

```
┌─────────┐
│ Client  │
└────┬────┘
     │
     │ 1. POST /unit/create
     │    Header: Authorization: <token>
     │
┌────▼────────────────────────────────────┐
│  @token_required Decorator             │
│  - Extracts token from header          │
│  - Validates token                     │
│  - Sets request.user_id                │
└────┬───────────────────────────────────┘
     │
     │ 2. Token valid, proceed
     │
┌────▼────────────────────────────────────┐
│  Unit Controller                       │
│  - Receives request                    │
│  - Extracts request.user_id            │
│  - Calls service                       │
└────┬───────────────────────────────────┘
     │
     │ 3. Calls create_unit()
     │
┌────▼────────────────────────────────────┐
│  Unit Service                          │
│  - Prepares data                       │
│  - Calls database                      │
└────┬───────────────────────────────────┘
     │
     │ 4. Execute stored procedure
     │
┌────▼────────────────────────────────────┐
│  Database Layer                        │
│  - Try: sp_Unit_Create                 │
│  - Fallback: Direct SQL if SP missing   │
└────┬───────────────────────────────────┘
     │
     │ 5. Success
     │
┌────▼────────────────────────────────────┐
│  Response                              │
│  {message: "Unit created"}             │
└────────────────────────────────────────┘
```

## Database Access Pattern

```
┌─────────────────────────────────────────┐
│  Service Function                      │
│  (e.g., create_unit())                 │
└──────────────┬──────────────────────────┘
               │
               │ Calls execute_stored_procedure()
               │
┌──────────────▼──────────────────────────┐
│  execute_stored_procedure()            │
│                                         │
│  1. Try: EXEC sp_Unit_Create           │
│     └─► Success? Return result        │
│                                         │
│  2. Error: SP not found?               │
│     └─► Use fallback_sql               │
│         └─► Execute direct SQL         │
│             └─► Return result           │
└──────────────┬──────────────────────────┘
               │
               │ Result returned
               │
┌──────────────▼──────────────────────────┐
│  Service Function                      │
│  - Processes result                    │
│  - Returns to controller               │
└─────────────────────────────────────────┘
```

## Data Flow Layers

### Layer 1: HTTP Layer (Controllers)
- **Purpose:** Handle HTTP requests/responses
- **Responsibilities:**
  - Parse request data
  - Validate authentication
  - Call service layer
  - Format JSON responses
- **Files:** `auth_controller.py`, `unit_controller.py`

### Layer 2: Business Logic (Services)
- **Purpose:** Implement business rules
- **Responsibilities:**
  - Process business logic
  - Validate data
  - Call database layer
  - Transform data
- **Files:** `auth_service.py`, `unit_service.py`

### Layer 3: Data Access (Database)
- **Purpose:** Database operations
- **Responsibilities:**
  - Manage connections
  - Execute queries/stored procedures
  - Handle errors
  - Close connections
- **Files:** `db.py`

### Layer 4: Utilities
- **Purpose:** Shared utilities
- **Responsibilities:**
  - JWT token generation/validation
  - Common helper functions
- **Files:** `jwt_utils.py`

## Security Layers

```
┌─────────────────────────────────────┐
│  Request                            │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  JWT Token Validation              │
│  (@token_required decorator)       │
│  - Validates token signature       │
│  - Checks expiration               │
│  - Extracts user_id                │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Controller                         │
│  - Receives validated request       │
│  - request.user_id available        │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Service                            │
│  - Uses user_id for audit trail     │
│  - Enforces business rules          │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Database                           │
│  - Parameterized queries            │
│  - SQL injection protection         │
└─────────────────────────────────────┘
```

## Component Responsibilities

### Controllers
- ✅ Handle HTTP requests
- ✅ Validate request format
- ✅ Call service layer
- ✅ Return JSON responses
- ❌ No business logic
- ❌ No direct database access

### Services
- ✅ Business logic
- ✅ Data validation
- ✅ Data transformation
- ✅ Call database layer
- ❌ No HTTP handling
- ❌ No direct SQL queries

### Database Layer
- ✅ Connection management
- ✅ Query execution
- ✅ Error handling
- ✅ Connection cleanup
- ❌ No business logic
- ❌ No HTTP handling

## Error Handling Strategy

```
Request
   │
   ▼
┌─────────────────────┐
│  Try: Execute SP    │
└─────────┬───────────┘
          │
          ├─► Success ──► Return Result
          │
          └─► Error: SP Not Found
                  │
                  ▼
          ┌─────────────────────┐
          │  Fallback: Direct SQL│
          └─────────┬────────────┘
                    │
                    ├─► Success ──► Return Result
                    │
                    └─► Error ──► Return Error Response
```

## Benefits of This Architecture

1. **Separation of Concerns:** Each layer has a single responsibility
2. **Maintainability:** Easy to modify one layer without affecting others
3. **Testability:** Each layer can be tested independently
4. **Scalability:** Can add new features by adding new controllers/services
5. **Flexibility:** Stored procedure fallback allows gradual migration
6. **Security:** JWT authentication at controller level
7. **Code Reusability:** Services can be reused across different controllers

