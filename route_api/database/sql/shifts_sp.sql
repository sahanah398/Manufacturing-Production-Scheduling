-- MasterShifts stored procedures
-- Run these in your SQL Server database (e.g., via SSMS)

SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

-- sp_Shift_Create: inserts a shift and returns the created row
IF OBJECT_ID('dbo.sp_Shift_Create', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_Shift_Create
GO
CREATE PROCEDURE dbo.sp_Shift_Create
    @name nvarchar(510),
    @startTime time = NULL,
    @endTime time = NULL,
    @duration float = NULL,
    @colorCode nvarchar(510) = NULL,
    @createdBy int
AS
BEGIN
    SET NOCOUNT ON;

    INSERT INTO MasterShifts (name, startTime, endTime, duration, colorCode, isActive, CreatedBy, createdAt, updatedAt)
    VALUES (@name, @startTime, @endTime, @duration, @colorCode, 1, @createdBy, SYSUTCDATETIME(), SYSUTCDATETIME());

    DECLARE @id int = SCOPE_IDENTITY();

    SELECT id, name, startTime, endTime, duration, colorCode, isActive, CreatedBy, ISNULL(UpdatedBy, CreatedBy) AS UpdatedBy, createdAt, updatedAt
    FROM MasterShifts
    WHERE id = @id;
END
GO

-- sp_Shift_GetAll: paginated, sortable select
IF OBJECT_ID('dbo.sp_Shift_GetAll', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_Shift_GetAll
GO
CREATE PROCEDURE dbo.sp_Shift_GetAll
    @page int = 1,
    @per_page int = 10,
    @sort_by nvarchar(50) = N'name',
    @sort_order nvarchar(4) = N'ASC'
AS
BEGIN
    SET NOCOUNT ON;

    IF @page < 1 SET @page = 1;
    IF @per_page < 1 SET @per_page = 10;

    DECLARE @orderColumn nvarchar(50);
    IF @sort_by IN (N'name', N'id', N'startTime', N'endTime', N'duration', N'colorCode')
        SET @orderColumn = @sort_by;
    ELSE
        SET @orderColumn = N'name';

    IF UPPER(@sort_order) NOT IN (N'ASC', N'DESC') SET @sort_order = N'ASC';

    DECLARE @offset int = (@page - 1) * @per_page;

    SELECT COUNT(*) AS total FROM MasterShifts WHERE isActive = 1;

    DECLARE @sql nvarchar(max) = N'
        SELECT id, name, startTime, endTime, duration, colorCode, isActive, CreatedBy, UpdatedBy
        FROM MasterShifts
        WHERE isActive = 1
        ORDER BY ' + QUOTENAME(@orderColumn) + ' ' + @sort_order + '
        OFFSET @offset ROWS
        FETCH NEXT @per_page ROWS ONLY;';

    EXEC sp_executesql @sql,
        N'@offset int, @per_page int',
        @offset = @offset, @per_page = @per_page;
END
GO

-- sp_Shift_Update: update fields and return updated row
IF OBJECT_ID('dbo.sp_Shift_Update', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_Shift_Update
GO
CREATE PROCEDURE dbo.sp_Shift_Update
    @name nvarchar(510),
    @startTime time = NULL,
    @endTime time = NULL,
    @duration float = NULL,
    @colorCode nvarchar(510) = NULL,
    @updatedBy int,
    @id int
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
        updatedAt = SYSUTCDATETIME()
    WHERE id = @id;

    SELECT id, name, startTime, endTime, duration, colorCode, isActive, CreatedBy, UpdatedBy, createdAt, updatedAt
    FROM MasterShifts
    WHERE id = @id;
END
GO

-- sp_Shift_Delete: toggle isActive and return updated row
IF OBJECT_ID('dbo.sp_Shift_Delete', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_Shift_Delete
GO
CREATE PROCEDURE dbo.sp_Shift_Delete
    @updatedBy int,
    @id int
AS
BEGIN
    SET NOCOUNT ON;

    UPDATE MasterShifts
    SET isActive = CASE WHEN isActive = 1 THEN 0 ELSE 1 END,
        UpdatedBy = @updatedBy,
        updatedAt = SYSUTCDATETIME()
    WHERE id = @id;

    SELECT id, name, startTime, endTime, duration, colorCode, isActive, CreatedBy, UpdatedBy, createdAt, updatedAt
    FROM MasterShifts
    WHERE id = @id;
END
GO
