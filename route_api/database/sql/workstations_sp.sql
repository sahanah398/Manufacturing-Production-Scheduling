-- Workstations stored procedures
-- Run these in SQL Server to enable SP paths used by the app

SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

IF OBJECT_ID('dbo.sp_Workstation_Create', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_Workstation_Create
GO
CREATE PROCEDURE dbo.sp_Workstation_Create
    @workstationName nvarchar(510),
    @description nvarchar(MAX) = NULL,
    @createdBy int
AS
BEGIN
    SET NOCOUNT ON;
    INSERT INTO Workstations (workstationName, description, isActive, CreatedBy, createdAt, updatedAt)
    VALUES (@workstationName, @description, 1, @createdBy, SYSUTCDATETIME(), SYSUTCDATETIME());
    DECLARE @id int = SCOPE_IDENTITY();
    SELECT id, workstationName, description, isActive, CreatedBy, ISNULL(UpdatedBy, CreatedBy) AS UpdatedBy, createdAt, updatedAt
    FROM Workstations WHERE id = @id;
END
GO

IF OBJECT_ID('dbo.sp_Workstation_GetAll', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_Workstation_GetAll
GO
CREATE PROCEDURE dbo.sp_Workstation_GetAll
    @page int = 1,
    @per_page int = 10,
    @sort_by nvarchar(50) = N'workstationName',
    @sort_order nvarchar(4) = N'ASC'
AS
BEGIN
    SET NOCOUNT ON;
    IF @page < 1 SET @page = 1;
    IF @per_page < 1 SET @per_page = 10;
    DECLARE @orderColumn nvarchar(50);
    IF @sort_by IN (N'workstationName', N'id', N'description')
        SET @orderColumn = @sort_by;
    ELSE
        SET @orderColumn = N'workstationName';
    IF UPPER(@sort_order) NOT IN (N'ASC', N'DESC') SET @sort_order = N'ASC';
    DECLARE @offset int = (@page - 1) * @per_page;
    SELECT COUNT(*) AS total FROM Workstations WHERE isActive = 1;
    DECLARE @sql nvarchar(max) = N'
        SELECT id, workstationName, description, isActive, CreatedBy, UpdatedBy
        FROM Workstations
        WHERE isActive = 1
        ORDER BY ' + QUOTENAME(@orderColumn) + ' ' + @sort_order + '
        OFFSET @offset ROWS
        FETCH NEXT @per_page ROWS ONLY;';
    EXEC sp_executesql @sql, N'@offset int, @per_page int', @offset = @offset, @per_page = @per_page;
END
GO

IF OBJECT_ID('dbo.sp_Workstation_Update', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_Workstation_Update
GO
CREATE PROCEDURE dbo.sp_Workstation_Update
    @workstationName nvarchar(510),
    @description nvarchar(MAX) = NULL,
    @updatedBy int,
    @id int
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE Workstations
    SET workstationName = @workstationName,
        description = @description,
        UpdatedBy = @updatedBy,
        updatedAt = SYSUTCDATETIME()
    WHERE id = @id;
    SELECT id, workstationName, description, isActive, CreatedBy, UpdatedBy, createdAt, updatedAt FROM Workstations WHERE id = @id;
END
GO

IF OBJECT_ID('dbo.sp_Workstation_Delete', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_Workstation_Delete
GO
CREATE PROCEDURE dbo.sp_Workstation_Delete
    @updatedBy int,
    @id int
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE Workstations
    SET isActive = CASE WHEN isActive = 1 THEN 0 ELSE 1 END,
        UpdatedBy = @updatedBy,
        updatedAt = SYSUTCDATETIME()
    WHERE id = @id;
    SELECT id, workstationName, description, isActive, CreatedBy, UpdatedBy, createdAt, updatedAt FROM Workstations WHERE id = @id;
END
GO
