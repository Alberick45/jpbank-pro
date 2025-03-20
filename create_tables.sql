-- Create User Roles Table
CREATE TABLE tbl_user_roles_086 (
    role_id INT IDENTITY(1,1) PRIMARY KEY,
    role_name VARCHAR(10),
    role_sht_name VARCHAR(10),
    role_created_date DATETIME,
    role_edited_date DATETIME
);

-- Create Employees Table
CREATE TABLE tbl_employees_086 (
    emp_idpk INT IDENTITY(1,1) PRIMARY KEY,
    emp_firstname VARCHAR(15) NOT NULL,
    emp_lastname VARCHAR(15),
    emp_othernames VARCHAR(50),
    emp_dob DATE NOT NULL,
    emp_gender_idfk INT,
    emp_nationality_idfk INT,
    emp_work_status_idfk INT,
    emp_marital_status_idfk INT,
    emp_email VARCHAR(100),
    emp_phone_nos VARCHAR(20),
    emp_address_idfk INT,
    emp_loyalty_point INT,
    emp_job_title_idfk INT,
    emp_created_on DATETIME,
    emp_edited_on DATETIME,
    emp_created_by_user_idfk VARCHAR(10),
    emp_edited_by_user_idfk VARCHAR(10)
);

-- Create Users Table
CREATE TABLE tbl_users_086 (
    usr_idpk INT IDENTITY(1,1) PRIMARY KEY,
    usr_username VARCHAR(50) NOT NULL UNIQUE,
    usr_password VARCHAR(256) NOT NULL,
    usr_empidfk INT REFERENCES tbl_employees_086(emp_idpk),
    usr_roleidfk INT REFERENCES tbl_user_roles_086(role_id),
    usr_start_date DATETIME,
    usr_end_date DATETIME,
    usr_created_by_userid INT,
    usr_edited_by_userid INT,
    usr_created_on DATETIME,
    usr_edited_on DATETIME
);

-- Create Customers Table
CREATE TABLE tbl_customers_086 (
    cus_id INT IDENTITY(1,1) PRIMARY KEY,
    cus_firstname VARCHAR(15) NOT NULL,
    cus_lastname VARCHAR(15) NOT NULL,
    cus_othernames VARCHAR(50) NOT NULL,
    cus_dob DATE NOT NULL,
    cus_gender_idfk INT,
    cus_nationality_idfk INT,
    cus_marital_status_idfk INT,
    cus_occupation VARCHAR(30),
    cus_email VARCHAR(100) NOT NULL,
    cus_phone_nos VARCHAR(20),
    cus_address TEXT NOT NULL,
    cus_loyalty_points INT,
    cus_created_on DATETIME,
    cus_edited_on DATETIME,
    cus_created_by_user_idfk VARCHAR(10),
    cus_edited_by_user_idfk VARCHAR(10)
);

-- Create Account Details Table
CREATE TABLE tbl_account_details_086 (
    acc_account_number INT IDENTITY(1,1) PRIMARY KEY,
    acc_customer_id INT NOT NULL,
    acc_account_type VARCHAR(20),
    acc_balance DECIMAL(15, 2) NOT NULL
);

-- Create KYC Table
CREATE TABLE tbl_kyc_086 (
    kyc_id INT IDENTITY(1,1) PRIMARY KEY,
    kyc_customer_id INT NOT NULL UNIQUE,
    kyc_id_type VARCHAR(20),
    kyc_id_number VARCHAR(50) NOT NULL UNIQUE,
    kyc_document_url VARCHAR(255),
    kyc_verified_by INT,
    kyc_verified_at DATETIME
);

-- Create Transactions Table
CREATE TABLE tbl_transactions_086 (
    tst_transaction_id INT IDENTITY(1,1) PRIMARY KEY,
    tst_account_number INT NOT NULL,
    tst_amount DECIMAL(15, 2) NOT NULL,
    tst_transaction_type VARCHAR(20),
    tst_created_by_user_id INT,
    tst_created_on DATETIME
);

-- Create Security Logs Table
CREATE TABLE tbl_security_logs_086 (
    log_id INT IDENTITY(1,1) PRIMARY KEY,
    log_customer_account_number INT,
    log_employee_id INT,
    log_action VARCHAR(255),
    log_timestamp DATETIME DEFAULT GETDATE(),
    success BIT DEFAULT 1
);

-- Add backup procedures
CREATE PROCEDURE spc_BackupDatabase_086
    @backup_path VARCHAR(255)
AS
BEGIN
    DECLARE @backup_name VARCHAR(255)
    SET @backup_name = @backup_path + '\jpbank_086_' + 
                      CONVERT(VARCHAR(8), GETDATE(), 112) + '.bak'
    
    BACKUP DATABASE jpbank_086
    TO DISK = @backup_name
    WITH INIT, NAME = 'jpbank_086-Full Database Backup'
END
GO

-- Add restore procedure
CREATE PROCEDURE spc_RestoreDatabase_086
    @backup_path VARCHAR(255)
AS
BEGIN
    ALTER DATABASE jpbank_086 SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    
    RESTORE DATABASE jpbank_086
    FROM DISK = @backup_path
    WITH REPLACE, RECOVERY;
    
    ALTER DATABASE jpbank_086 SET MULTI_USER;
END
GO

-- Add audit trigger for sensitive operations
CREATE TRIGGER trg_AuditSensitiveOperations_086
ON DATABASE
FOR DDL_DATABASE_LEVEL_EVENTS
AS
BEGIN
    DECLARE @eventData XML = EVENTDATA();
    
    INSERT INTO tbl_security_logs_086 (
        log_employee_id,
        log_action,
        log_timestamp
    )
    VALUES (
        SYSTEM_USER,
        @eventData.value('(/EVENT_INSTANCE/TSQLCommand/CommandText)[1]','nvarchar(max)'),
        GETDATE()
    );
END
GO

-- Grant backup permissions to Admin role
GRANT BACKUP DATABASE TO Admin;
GRANT RESTORE DATABASE TO Admin;

-- Get account balance history
CREATE FUNCTION fcn_GetAccountBalanceHistory_086(
    @AccountNumber INT,
    @StartDate DATE,
    @EndDate DATE
)
RETURNS TABLE
AS
RETURN
    SELECT 
        tst_transaction_id,
        tst_amount,
        tst_transaction_type,
        tst_created_on
    FROM tbl_transactions_086
    WHERE tst_account_number = @AccountNumber
    AND tst_created_on BETWEEN @StartDate AND @EndDate
GO

-- Get customer activity summary
CREATE FUNCTION fcn_GetCustomerActivitySummary_086(
    @CustomerId INT
)
RETURNS TABLE
AS
RETURN
    SELECT 
        t.tst_transaction_type,
        COUNT(*) as transaction_count,
        SUM(t.tst_amount) as total_amount
    FROM tbl_transactions_086 t
    JOIN tbl_account_details_086 a ON t.tst_account_number = a.acc_account_number
    WHERE a.acc_customer_id = @CustomerId
    GROUP BY t.tst_transaction_type
GO

-- Add procedure to generate monthly statement
CREATE PROCEDURE spc_GenerateMonthlyStatement_086
    @CustomerId INT,
    @Month INT,
    @Year INT
AS
BEGIN
    SELECT 
        c.cus_firstname + ' ' + c.cus_lastname as customer_name,
        a.acc_account_number,
        a.acc_account_type,
        t.tst_transaction_type,
        t.tst_amount,
        t.tst_created_on
    FROM tbl_customers_086 c
    JOIN tbl_account_details_086 a ON c.cus_id = a.acc_customer_id
    JOIN tbl_transactions_086 t ON a.acc_account_number = t.tst_account_number
    WHERE c.cus_id = @CustomerId
    AND MONTH(t.tst_created_on) = @Month
    AND YEAR(t.tst_created_on) = @Year
    ORDER BY t.tst_created_on
END
GO

-- Add procedure to check account status
CREATE PROCEDURE spc_CheckAccountStatus_086
    @AccountNumber INT
AS
BEGIN
    SELECT 
        a.acc_account_number,
        a.acc_account_type,
        a.acc_balance,
        c.cus_firstname + ' ' + c.cus_lastname as account_holder,
        c.cus_email,
        c.cus_phone_nos,
        c.cus_loyalty_points
    FROM tbl_account_details_086 a
    JOIN tbl_customers_086 c ON a.acc_customer_id = c.cus_id
    WHERE a.acc_account_number = @AccountNumber
END
GO


-- Add reference tables for IDs
CREATE TABLE tbl_gender_086 (id INT PRIMARY KEY IDENTITY(1,1), name VARCHAR(10));
CREATE TABLE tbl_nationality_086 (id INT PRIMARY KEY IDENTITY(1,1), name VARCHAR(50));
CREATE TABLE tbl_work_status_086 (id INT PRIMARY KEY IDENTITY(1,1), status VARCHAR(20));
CREATE TABLE tbl_marital_status_086 (id INT PRIMARY KEY IDENTITY(1,1), status VARCHAR(20));
CREATE TABLE tbl_job_title_086 (id INT PRIMARY KEY IDENTITY(1,1), title VARCHAR(50));

-- Insert basic reference data
INSERT INTO tbl_gender_086 (name) VALUES ('Male'), ('Female');
INSERT INTO tbl_nationality_086 (name) VALUES ('USA'), ('UK'), ('Canada');
INSERT INTO tbl_work_status_086 (status) VALUES ('Active'), ('Inactive');
INSERT INTO tbl_marital_status_086 (status) VALUES ('Single'), ('Married');
INSERT INTO tbl_job_title_086 (title) VALUES ('Manager'), ('Teller'), ('Supervisor');