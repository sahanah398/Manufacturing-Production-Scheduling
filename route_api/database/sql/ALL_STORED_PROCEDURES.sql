-- =============================================
-- ALL STORED PROCEDURES FOR ROUTE API
-- Run this entire script in SQL Server Management Studio (SSMS)
-- Database: iERP
-- =============================================

SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

USE iERP;
GO

-- =============================================
-- UNITS STORED PROCEDURES
-- =============================================

-- sp_Unit_Create
IF OBJECT_ID('dbo.sp_Unit_Create', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_Unit_Create;
GO

CREATE PROCEDURE dbo.sp_Unit_Create
    @unitName NVARCHAR(255),
    @description NVARCHAR(MAX) = NULL,
    @unitSymbol NVARCHAR(50) = NULL,
    @createdBy INT
AS
BEGIN
    SET NOCOUNT ON;
    
    INSERT INTO Units
    (unitName, description, unitSymbol, isActive, CreatedBy, UpdatedBy, createdAt, updatedAt)
    VALUES
    (@unitName, @description, @unitSymbol, 1, @createdBy, 1, SYSDATETIMEOFFSET(), SYSDATETIMEOFFSET());
    
    SELECT id, unitName, unitSymbol, description, isActive, CreatedBy, UpdatedBy, createdAt, updatedAt
    FROM Units
    WHERE id = SCOPE_IDENTITY();
END;
GO

-- sp_Unit_GetAll
IF OBJECT_ID('dbo.sp_Unit_GetAll', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_Unit_GetAll;
GO

CREATE PROCEDURE dbo.sp_Unit_GetAll
    @page INT = 1,
    @per_page INT = 10,
    @sort_by NVARCHAR(50) = 'unitName',
    @sort_order NVARCHAR(4) = 'ASC'
AS
BEGIN
    SET NOCOUNT ON;
    
    IF @page < 1 SET @page = 1;
    IF @per_page < 1 SET @per_page = 10;
    
    DECLARE @offset INT = (@page - 1) * @per_page;
    DECLARE @sql NVARCHAR(MAX);
    
    SET @sql = N'
        SELECT id, unitName, unitSymbol, description, isActive, CreatedBy, UpdatedBy, createdAt, updatedAt
        FROM Units
        WHERE isActive = 1
        ORDER BY ' + QUOTENAME(@sort_by) + ' ' + @sort_order + '
        OFFSET ' + CAST(@offset AS NVARCHAR(10)) + ' ROWS
        FETCH NEXT ' + CAST(@per_page AS NVARCHAR(10)) + ' ROWS ONLY';
    
    EXEC sp_executesql @sql;
END;
GO

-- sp_Unit_GetById
IF OBJECT_ID('dbo.sp_Unit_GetById', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_Unit_GetById;
GO

CREATE PROCEDURE dbo.sp_Unit_GetById
    @id INT
AS
BEGIN
    SET NOCOUNT ON;
    
    SELECT id, unitName, unitSymbol, description, isActive, CreatedBy, UpdatedBy, createdAt, updatedAt
    FROM Units
    WHERE id = @id AND isActive = 1;
END;
GO

-- sp_Unit_Update
IF OBJECT_ID('dbo.sp_Unit_Update', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_Unit_Update;
GO

CREATE PROCEDURE dbo.sp_Unit_Update
    @id INT,
    @unitName NVARCHAR(255),
    @description NVARCHAR(MAX) = NULL,
    @unitSymbol NVARCHAR(50) = NULL,
    @updatedBy INT
AS
BEGIN
    SET NOCOUNT ON;
    
    UPDATE Units
    SET unitName = @unitName,
        description = @description,
        unitSymbol = @unitSymbol,
        UpdatedBy = @updatedBy,
        updatedAt = SYSDATETIMEOFFSET()
    WHERE id = @id;
    
    SELECT id, unitName, unitSymbol, description, isActive, CreatedBy, UpdatedBy, createdAt, updatedAt
    FROM Units
    WHERE id = @id;
END;
GO

-- sp_Unit_Delete
IF OBJECT_ID('dbo.sp_Unit_Delete', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_Unit_Delete;
GO

CREATE PROCEDURE dbo.sp_Unit_Delete
    @id INT,
    @updatedBy INT
AS
BEGIN
    SET NOCOUNT ON;
    
    UPDATE Units
    SET isActive = 0,
        UpdatedBy = @updatedBy,
        updatedAt = SYSDATETIMEOFFSET()
    WHERE id = @id;
    
    SELECT id, unitName, unitSymbol, description, isActive, CreatedBy, UpdatedBy, createdAt, updatedAt
    FROM Units
    WHERE id = @id;
END;
GO

-- =============================================
-- SHIFTS STORED PROCEDURES
-- =============================================

-- sp_Shift_Create
IF OBJECT_ID('dbo.sp_Shift_Create', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_Shift_Create;
GO

CREATE PROCEDURE dbo.sp_Shift_Create
    @name NVARCHAR(255),
    @startTime TIME,
    @endTime TIME,
    @duration FLOAT = NULL,
    @colorCode NVARCHAR(50) = NULL,
    @createdBy INT
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Duplicate validation
    IF EXISTS (
        SELECT 1 FROM MasterShifts
        WHERE name = @name
          AND startTime = @startTime
          AND endTime = @endTime
          AND isActive = 1
    )
    BEGIN
        THROW 50001, 'Shift already exists', 1;
    END
    
    INSERT INTO MasterShifts
    (name, startTime, endTime, duration, colorCode, isActive, CreatedBy, UpdatedBy, createdAt, updatedAt)
    VALUES
    (@name, @startTime, @endTime, @duration, @colorCode, 1, @createdBy, @createdBy, SYSDATETIMEOFFSET(), SYSDATETIMEOFFSET());
    
    SELECT id, name, startTime, endTime, duration, colorCode, isActive, CreatedBy, UpdatedBy, createdAt, updatedAt
    FROM MasterShifts
    WHERE id = SCOPE_IDENTITY();
END;
GO

-- sp_Shift_GetAll
IF OBJECT_ID('dbo.sp_Shift_GetAll', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_Shift_GetAll;
GO

CREATE PROCEDURE dbo.sp_Shift_GetAll
    @page INT = 1,
    @per_page INT = 10,
    @sort_by NVARCHAR(50) = 'name',
    @sort_order NVARCHAR(4) = 'ASC'
AS
BEGIN
    SET NOCOUNT ON;
    
    IF @page < 1 SET @page = 1;
    IF @per_page < 1 SET @per_page = 10;
    
    DECLARE @offset INT = (@page - 1) * @per_page;
    DECLARE @sql NVARCHAR(MAX);
    
    SET @sql = N'
        SELECT id, name, startTime, endTime, duration, colorCode, isActive, CreatedBy, UpdatedBy, createdAt, updatedAt
        FROM MasterShifts
        WHERE isActive = 1
        ORDER BY ' + QUOTENAME(@sort_by) + ' ' + @sort_order + '
        OFFSET ' + CAST(@offset AS NVARCHAR(10)) + ' ROWS
        FETCH NEXT ' + CAST(@per_page AS NVARCHAR(10)) + ' ROWS ONLY';
    
    EXEC sp_executesql @sql;
END;
GO

-- sp_Shift_GetById
IF OBJECT_ID('dbo.sp_Shift_GetById', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_Shift_GetById;
GO

CREATE PROCEDURE dbo.sp_Shift_GetById
    @id INT
AS
BEGIN
    SET NOCOUNT ON;
    
    SELECT id, name, startTime, endTime, duration, colorCode, isActive, CreatedBy, UpdatedBy, createdAt, updatedAt
    FROM MasterShifts
    WHERE id = @id AND isActive = 1;
END;
GO

-- sp_Shift_Update
IF OBJECT_ID('dbo.sp_Shift_Update', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_Shift_Update;
GO

CREATE PROCEDURE dbo.sp_Shift_Update
    @id INT,
    @name NVARCHAR(255),
    @startTime TIME,
    @endTime TIME,
    @duration FLOAT = NULL,
    @colorCode NVARCHAR(50) = NULL,
    @updatedBy INT
AS
BEGIN
    SET NOCOUNT ON;
    
    UPDATE MasterShifts
    SET name = @name,
        startTime = @startTime,
        endTime = @endTime,
        duration = @duration,
        colorCode = @colorCode,
        UpdatedBy = @updatedBy,
        updatedAt = SYSDATETIMEOFFSET()
    WHERE id = @id;
    
    SELECT id, name, startTime, endTime, duration, colorCode, isActive, CreatedBy, UpdatedBy, createdAt, updatedAt
    FROM MasterShifts
    WHERE id = @id;
END;
GO

-- sp_Shift_Delete
IF OBJECT_ID('dbo.sp_Shift_Delete', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_Shift_Delete;
GO

CREATE PROCEDURE dbo.sp_Shift_Delete
    @id INT,
    @updatedBy INT
AS
BEGIN
    SET NOCOUNT ON;
    
    UPDATE MasterShifts
    SET isActive = 0,
        UpdatedBy = @updatedBy,
        updatedAt = SYSDATETIMEOFFSET()
    WHERE id = @id;
    
    SELECT id, name, startTime, endTime, duration, colorCode, isActive, CreatedBy, UpdatedBy, createdAt, updatedAt
    FROM MasterShifts
    WHERE id = @id;
END;
GO

-- =============================================
-- PROCESSES STORED PROCEDURES
-- =============================================

-- sp_Process_Create
IF OBJECT_ID('dbo.sp_Process_Create', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_Process_Create;
GO

CREATE PROCEDURE dbo.sp_Process_Create
    @processName NVARCHAR(255),
    @description NVARCHAR(MAX) = NULL,
    @workstationId INT,
    @processTime FLOAT,
    @setupTime FLOAT,
    @createdBy INT
AS
BEGIN
    SET NOCOUNT ON;
    
    INSERT INTO Processes
    (processName, description, workstationId, processTime, setupTime, isActive, CreatedBy, UpdatedBy, createdAt, updatedAt)
    VALUES
    (@processName, @description, @workstationId, @processTime, @setupTime, 1, @createdBy, @createdBy, SYSDATETIMEOFFSET(), SYSDATETIMEOFFSET());
    
    SELECT id, processName, description, workstationId, processTime, setupTime, isActive, CreatedBy, UpdatedBy, createdAt, updatedAt
    FROM Processes
    WHERE id = SCOPE_IDENTITY();
END;
GO

-- sp_Process_GetAll
IF OBJECT_ID('dbo.sp_Process_GetAll', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_Process_GetAll;
GO

CREATE PROCEDURE dbo.sp_Process_GetAll
    @page INT = 1,
    @per_page INT = 10,
    @sort_by NVARCHAR(50) = 'processName',
    @sort_order NVARCHAR(4) = 'ASC'
AS
BEGIN
    SET NOCOUNT ON;
    
    IF @page < 1 SET @page = 1;
    IF @per_page < 1 SET @per_page = 10;
    
    DECLARE @offset INT = (@page - 1) * @per_page;
    DECLARE @sql NVARCHAR(MAX);
    
    SET @sql = N'
        SELECT id, processName, description, workstationId, processTime, setupTime, isActive, CreatedBy, UpdatedBy, createdAt, updatedAt
        FROM Processes
        WHERE isActive = 1
        ORDER BY ' + QUOTENAME(@sort_by) + ' ' + @sort_order + '
        OFFSET ' + CAST(@offset AS NVARCHAR(10)) + ' ROWS
        FETCH NEXT ' + CAST(@per_page AS NVARCHAR(10)) + ' ROWS ONLY';
    
    EXEC sp_executesql @sql;
END;
GO

-- sp_Process_GetById
IF OBJECT_ID('dbo.sp_Process_GetById', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_Process_GetById;
GO

CREATE PROCEDURE dbo.sp_Process_GetById
    @id INT
AS
BEGIN
    SET NOCOUNT ON;
    
    SELECT id, processName, description, workstationId, processTime, setupTime, isActive, CreatedBy, UpdatedBy, createdAt, updatedAt
    FROM Processes
    WHERE id = @id AND isActive = 1;
END;
GO

-- sp_Process_Update
IF OBJECT_ID('dbo.sp_Process_Update', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_Process_Update;
GO

CREATE PROCEDURE dbo.sp_Process_Update
    @id INT,
    @processName NVARCHAR(255),
    @description NVARCHAR(MAX) = NULL,
    @workstationId INT,
    @processTime FLOAT,
    @setupTime FLOAT,
    @updatedBy INT
AS
BEGIN
    SET NOCOUNT ON;
    
    UPDATE Processes
    SET processName = @processName,
        description = @description,
        workstationId = @workstationId,
        processTime = @processTime,
        setupTime = @setupTime,
        UpdatedBy = @updatedBy,
        updatedAt = SYSDATETIMEOFFSET()
    WHERE id = @id;
    
    SELECT id, processName, description, workstationId, processTime, setupTime, isActive, CreatedBy, UpdatedBy, createdAt, updatedAt
    FROM Processes
    WHERE id = @id;
END;
GO

-- sp_Process_Delete
IF OBJECT_ID('dbo.sp_Process_Delete', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_Process_Delete;
GO

CREATE PROCEDURE dbo.sp_Process_Delete
    @id INT,
    @updatedBy INT
AS
BEGIN
    SET NOCOUNT ON;
    
    UPDATE Processes
    SET isActive = 0,
        UpdatedBy = @updatedBy,
        updatedAt = SYSDATETIMEOFFSET()
    WHERE id = @id;
    
    SELECT id, processName, description, workstationId, processTime, setupTime, isActive, CreatedBy, UpdatedBy, createdAt, updatedAt
    FROM Processes
    WHERE id = @id;
END;
GO

-- =============================================
-- PROCESS TECHNICALS STORED PROCEDURES
-- =============================================

-- sp_ProcessTechnical_Create
IF OBJECT_ID('dbo.sp_ProcessTechnical_Create', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_ProcessTechnical_Create;
GO

CREATE PROCEDURE dbo.sp_ProcessTechnical_Create
    @processId INT,
    @unitId INT = NULL,
    @name NVARCHAR(255),
    @value NVARCHAR(255),
    @createdBy INT
AS
BEGIN
    SET NOCOUNT ON;
    
    INSERT INTO ProcessTechnicals
    (processId, unitId, name, value, isActive, CreatedBy, UpdatedBy, createdAt, updatedAt)
    VALUES
    (@processId, @unitId, @name, @value, 1, @createdBy, @createdBy, SYSDATETIMEOFFSET(), SYSDATETIMEOFFSET());
    
    SELECT id, processId, unitId, name, value, isActive, CreatedBy, UpdatedBy, createdAt, updatedAt
    FROM ProcessTechnicals
    WHERE id = SCOPE_IDENTITY();
END;
GO

-- sp_ProcessTechnical_GetByProcessId
IF OBJECT_ID('dbo.sp_ProcessTechnical_GetByProcessId', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_ProcessTechnical_GetByProcessId;
GO

CREATE PROCEDURE dbo.sp_ProcessTechnical_GetByProcessId
    @processId INT
AS
BEGIN
    SET NOCOUNT ON;
    
    SELECT id, processId, unitId, name, value, isActive, CreatedBy, UpdatedBy, createdAt, updatedAt
    FROM ProcessTechnicals
    WHERE processId = @processId AND isActive = 1;
END;
GO

-- =============================================
-- USER LOGIN STORED PROCEDURE
-- =============================================

-- sp_User_Login
IF OBJECT_ID('dbo.sp_User_Login', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_User_Login;
GO

CREATE PROCEDURE dbo.sp_User_Login
    @username NVARCHAR(255),
    @password NVARCHAR(255)
AS
BEGIN
    SET NOCOUNT ON;
    
    SELECT id
    FROM Users
    WHERE username = @username
      AND password = @password
      AND isActive = 1;
END;
GO

-- =============================================
-- ROUTES STORED PROCEDURES
-- =============================================

-- sp_Route_Create
IF OBJECT_ID('dbo.sp_Route_Create', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_Route_Create;
GO

CREATE PROCEDURE dbo.sp_Route_Create
    @routeName NVARCHAR(255),
    @description NVARCHAR(MAX) = NULL,
    @isMainRoute BIT,
    @createdBy INT
AS
BEGIN
    SET NOCOUNT ON;
    
    INSERT INTO Routes
    (routeName, description, isMainRoute, isActive, CreatedBy, UpdatedBy, createdAt, updatedAt)
    VALUES
    (@routeName, @description, @isMainRoute, 1, @createdBy, @createdBy, SYSDATETIMEOFFSET(), SYSDATETIMEOFFSET());
    
    SELECT id, routeName, description, isMainRoute, isActive, CreatedBy, UpdatedBy, createdAt, updatedAt
    FROM Routes
    WHERE id = SCOPE_IDENTITY();
END;
GO

-- sp_Route_GetAll
IF OBJECT_ID('dbo.sp_Route_GetAll', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_Route_GetAll;
GO

CREATE PROCEDURE dbo.sp_Route_GetAll
    @page INT = 1,
    @per_page INT = 10,
    @sort_by NVARCHAR(50) = 'routeName',
    @sort_order NVARCHAR(4) = 'ASC'
AS
BEGIN
    SET NOCOUNT ON;
    
    IF @page < 1 SET @page = 1;
    IF @per_page < 1 SET @per_page = 10;
    
    DECLARE @offset INT = (@page - 1) * @per_page;
    DECLARE @sql NVARCHAR(MAX);
    
    SET @sql = N'
        SELECT id, routeName, description, isMainRoute, isActive, CreatedBy, UpdatedBy, createdAt, updatedAt
        FROM Routes
        WHERE isActive = 1
        ORDER BY ' + QUOTENAME(@sort_by) + ' ' + @sort_order + '
        OFFSET ' + CAST(@offset AS NVARCHAR(10)) + ' ROWS
        FETCH NEXT ' + CAST(@per_page AS NVARCHAR(10)) + ' ROWS ONLY';
    
    EXEC sp_executesql @sql;
END;
GO

-- sp_Route_GetById
IF OBJECT_ID('dbo.sp_Route_GetById', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_Route_GetById;
GO

CREATE PROCEDURE dbo.sp_Route_GetById
    @id INT
AS
BEGIN
    SET NOCOUNT ON;
    
    SELECT id, routeName, description, isMainRoute, isActive, CreatedBy, UpdatedBy, createdAt, updatedAt
    FROM Routes
    WHERE id = @id AND isActive = 1;
END;
GO

-- sp_Route_Update
IF OBJECT_ID('dbo.sp_Route_Update', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_Route_Update;
GO

CREATE PROCEDURE dbo.sp_Route_Update
    @id INT,
    @routeName NVARCHAR(255),
    @description NVARCHAR(MAX) = NULL,
    @isMainRoute BIT,
    @updatedBy INT
AS
BEGIN
    SET NOCOUNT ON;
    
    UPDATE Routes
    SET routeName = @routeName,
        description = @description,
        isMainRoute = @isMainRoute,
        UpdatedBy = @updatedBy,
        updatedAt = SYSDATETIMEOFFSET()
    WHERE id = @id;
    
    SELECT id, routeName, description, isMainRoute, isActive, CreatedBy, UpdatedBy, createdAt, updatedAt
    FROM Routes
    WHERE id = @id;
END;
GO

-- sp_Route_Delete
IF OBJECT_ID('dbo.sp_Route_Delete', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_Route_Delete;
GO

CREATE PROCEDURE dbo.sp_Route_Delete
    @id INT,
    @updatedBy INT
AS
BEGIN
    SET NOCOUNT ON;
    
    UPDATE Routes
    SET isActive = 0,
        UpdatedBy = @updatedBy,
        updatedAt = SYSDATETIMEOFFSET()
    WHERE id = @id;
    
    SELECT id, routeName, description, isMainRoute, isActive, CreatedBy, UpdatedBy, createdAt, updatedAt
    FROM Routes
    WHERE id = @id;
END;
GO

-- =============================================
-- ROUTE PROCESS STORED PROCEDURES
-- =============================================

-- sp_RouteProcess_Create
IF OBJECT_ID('dbo.sp_RouteProcess_Create', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_RouteProcess_Create;
GO

CREATE PROCEDURE dbo.sp_RouteProcess_Create
    @routeId INT,
    @processId INT,
    @processOrder INT
AS
BEGIN
    SET NOCOUNT ON;
    
    INSERT INTO RouteProcess
    (routeId, processId, processOrder, isActive)
    VALUES
    (@routeId, @processId, @processOrder, 1);
    
    SELECT id, routeId, processId, processOrder, isActive
    FROM RouteProcess
    WHERE id = SCOPE_IDENTITY();
END;
GO

-- sp_RouteProcess_GetByRouteId
IF OBJECT_ID('dbo.sp_RouteProcess_GetByRouteId', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_RouteProcess_GetByRouteId;
GO

CREATE PROCEDURE dbo.sp_RouteProcess_GetByRouteId
    @routeId INT
AS
BEGIN
    SET NOCOUNT ON;
    
    SELECT id, routeId, processId, processOrder, isActive
    FROM RouteProcess
    WHERE routeId = @routeId AND isActive = 1
    ORDER BY processOrder;
END;
GO

-- =============================================
-- PRODUCTS STORED PROCEDURES
-- =============================================

-- sp_Product_Create
IF OBJECT_ID('dbo.sp_Product_Create', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_Product_Create;
GO

CREATE PROCEDURE dbo.sp_Product_Create
    @productName NVARCHAR(255),
    @description NVARCHAR(MAX) = NULL,
    @mainRouteId INT,
    @createdBy INT
AS
BEGIN
    SET NOCOUNT ON;
    
    INSERT INTO Products
    (productName, description, mainRouteId, isActive, CreatedBy, UpdatedBy, createdAt, updatedAt)
    VALUES
    (@productName, @description, @mainRouteId, 1, @createdBy, @createdBy, SYSDATETIMEOFFSET(), SYSDATETIMEOFFSET());
    
    SELECT id, productName, description, mainRouteId, isActive, CreatedBy, UpdatedBy, createdAt, updatedAt
    FROM Products
    WHERE id = SCOPE_IDENTITY();
END;
GO

-- sp_Product_GetAll
IF OBJECT_ID('dbo.sp_Product_GetAll', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_Product_GetAll;
GO

CREATE PROCEDURE dbo.sp_Product_GetAll
    @page INT = 1,
    @per_page INT = 10,
    @sort_by NVARCHAR(50) = 'productName',
    @sort_order NVARCHAR(4) = 'ASC'
AS
BEGIN
    SET NOCOUNT ON;
    
    IF @page < 1 SET @page = 1;
    IF @per_page < 1 SET @per_page = 10;
    
    DECLARE @offset INT = (@page - 1) * @per_page;
    DECLARE @sql NVARCHAR(MAX);
    
    SET @sql = N'
        SELECT id, productName, description, mainRouteId, isActive, CreatedBy, UpdatedBy, createdAt, updatedAt
        FROM Products
        WHERE isActive = 1
        ORDER BY ' + QUOTENAME(@sort_by) + ' ' + @sort_order + '
        OFFSET ' + CAST(@offset AS NVARCHAR(10)) + ' ROWS
        FETCH NEXT ' + CAST(@per_page AS NVARCHAR(10)) + ' ROWS ONLY';
    
    EXEC sp_executesql @sql;
END;
GO

-- sp_Product_GetById
IF OBJECT_ID('dbo.sp_Product_GetById', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_Product_GetById;
GO

CREATE PROCEDURE dbo.sp_Product_GetById
    @id INT
AS
BEGIN
    SET NOCOUNT ON;
    
    SELECT id, productName, description, mainRouteId, isActive, CreatedBy, UpdatedBy, createdAt, updatedAt
    FROM Products
    WHERE id = @id AND isActive = 1;
END;
GO

-- sp_Product_Update
IF OBJECT_ID('dbo.sp_Product_Update', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_Product_Update;
GO

CREATE PROCEDURE dbo.sp_Product_Update
    @id INT,
    @productName NVARCHAR(255),
    @description NVARCHAR(MAX) = NULL,
    @mainRouteId INT,
    @updatedBy INT
AS
BEGIN
    SET NOCOUNT ON;
    
    UPDATE Products
    SET productName = @productName,
        description = @description,
        mainRouteId = @mainRouteId,
        UpdatedBy = @updatedBy,
        updatedAt = SYSDATETIMEOFFSET()
    WHERE id = @id;
    
    SELECT id, productName, description, mainRouteId, isActive, CreatedBy, UpdatedBy, createdAt, updatedAt
    FROM Products
    WHERE id = @id;
END;
GO

-- sp_Product_Delete
IF OBJECT_ID('dbo.sp_Product_Delete', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_Product_Delete;
GO

CREATE PROCEDURE dbo.sp_Product_Delete
    @id INT,
    @updatedBy INT
AS
BEGIN
    SET NOCOUNT ON;
    
    UPDATE Products
    SET isActive = 0,
        UpdatedBy = @updatedBy,
        updatedAt = SYSDATETIMEOFFSET()
    WHERE id = @id;
    
    SELECT id, productName, description, mainRouteId, isActive, CreatedBy, UpdatedBy, createdAt, updatedAt
    FROM Products
    WHERE id = @id;
END;
GO

-- =============================================
-- COMPLETION MESSAGE
-- =============================================
PRINT 'All stored procedures created successfully!';
GO

