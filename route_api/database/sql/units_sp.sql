-- Units stored procedures
-- Run these in your SQL Server database (e.g., via SSMS)

SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

-- sp_Unit_Create: inserts a unit and returns the created row
IF OBJECT_ID('dbo.sp_Unit_Create', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_Unit_Create
GO
CREATE PROCEDURE dbo.sp_Unit_Create
    @unitName nvarchar(100),
    @description nvarchar(500) = NULL,
    @unitSymbol nvarchar(10) = NULL,
    @createdBy int
AS
BEGIN
    SET NOCOUNT ON;

    INSERT INTO Units (unitName, description, unitSymbol, isActive, CreatedBy, createdAt, updatedAt)
    VALUES (@unitName, @description, @unitSymbol, 1, @createdBy, SYSUTCDATETIME(), SYSUTCDATETIME());

    DECLARE @id int = SCOPE_IDENTITY();

    SELECT id, unitName, unitSymbol, description, isActive, CreatedBy, ISNULL(UpdatedBy, CreatedBy) AS UpdatedBy, createdAt, updatedAt
    FROM Units
    WHERE id = @id;
END
GO

-- sp_Unit_GetAll: paginated, sortable select
IF OBJECT_ID('dbo.sp_Unit_GetAll', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_Unit_GetAll
GO
CREATE PROCEDURE dbo.sp_Unit_GetAll
    @page int = 1,
    @per_page int = 10,
    @sort_by nvarchar(50) = N'unitName',
    @sort_order nvarchar(4) = N'ASC'
AS
BEGIN
    SET NOCOUNT ON;

    -- Validate inputs
    IF @page < 1 SET @page = 1;
    IF @per_page < 1 SET @per_page = 10;

    -- Whitelist allowed sort columns to avoid SQL injection
    DECLARE @orderColumn nvarchar(50);
    IF @sort_by IN (N'unitName', N'id', N'description', N'unitSymbol')
        SET @orderColumn = @sort_by;
    ELSE
        SET @orderColumn = N'unitName';

    IF UPPER(@sort_order) NOT IN (N'ASC', N'DESC') SET @sort_order = N'ASC';

    DECLARE @offset int = (@page - 1) * @per_page;

    -- Total count
    SELECT COUNT(*) AS total FROM Units WHERE isActive = 1;

    -- Use dynamic SQL for ORDER BY safely
    DECLARE @sql nvarchar(max) = N'
        SELECT id, unitName, unitSymbol, description, isActive
        FROM Units
        WHERE isActive = 1
        ORDER BY ' + QUOTENAME(@orderColumn) + ' ' + @sort_order + '
        OFFSET @offset ROWS
        FETCH NEXT @per_page ROWS ONLY;';

    EXEC sp_executesql @sql,
        N'@offset int, @per_page int',
        @offset = @offset, @per_page = @per_page;
END
GO

-- sp_Unit_Update: update fields and return updated row
IF OBJECT_ID('dbo.sp_Unit_Update', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_Unit_Update
GO
CREATE PROCEDURE dbo.sp_Unit_Update
    @unitName nvarchar(100),
    @description nvarchar(500) = NULL,
    @unitSymbol nvarchar(10) = NULL,
    @updatedBy int,
    @id int
AS
BEGIN
    SET NOCOUNT ON;

    UPDATE Units
    SET unitName = @unitName,
        description = @description,
        unitSymbol = @unitSymbol,
        UpdatedBy = @updatedBy,
        updatedAt = SYSUTCDATETIME()
    WHERE id = @id;

    SELECT id, unitName, unitSymbol, description, isActive, CreatedBy, ISNULL(UpdatedBy, CreatedBy) AS UpdatedBy, createdAt, updatedAt
    FROM Units
    WHERE id = @id;
END
GO

-- sp_Unit_Delete: toggle isActive and return updated row
IF OBJECT_ID('dbo.sp_Unit_Delete', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_Unit_Delete
GO
CREATE PROCEDURE dbo.sp_Unit_Delete
    @updatedBy int,
    @id int
AS
BEGIN
    SET NOCOUNT ON;

    UPDATE Units
    SET isActive = CASE WHEN isActive = 1 THEN 0 ELSE 1 END,
        UpdatedBy = @updatedBy,
        updatedAt = SYSUTCDATETIME()
    WHERE id = @id;

    SELECT id, unitName, unitSymbol, description, isActive, CreatedBy, ISNULL(UpdatedBy, CreatedBy) AS UpdatedBy, createdAt, updatedAt
    FROM Units
    WHERE id = @id;
END
GO
