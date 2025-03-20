from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv
from urllib.parse import quote_plus

load_dotenv()

# Database configuration
server = os.getenv('DB_SERVER', 'localhost')
database = os.getenv('DB_NAME', 'jpbank_086')
driver = os.getenv('DB_DRIVER', 'ODBC Driver 17 for SQL Server')
trusted_connection = os.getenv('DB_TRUSTED_CONNECTION', 'yes')

# Create connection string
params = quote_plus(
    f'DRIVER={driver};'
    f'SERVER={server};'
    f'DATABASE={database};'
    f'Trusted_Connection={trusted_connection}'
)

# Create engine
engine = create_engine(f"mssql+pyodbc:///?odbc_connect={params}")

# SQL statements to create tables
create_tables_sql = """
-- Create TblEmployees086
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'TblEmployees086') AND type in (N'U'))
BEGIN
    CREATE TABLE TblEmployees086 (
        emp_idpk INT IDENTITY(1,1) PRIMARY KEY,
        emp_firstname VARCHAR(50) NOT NULL,
        emp_lastname VARCHAR(50) NOT NULL,
        emp_email VARCHAR(100) NOT NULL,
        emp_phone VARCHAR(20),
        emp_address VARCHAR(200),
        emp_department VARCHAR(50),
        emp_dob DATE NOT NULL,
        emp_photo VARCHAR(255),
        emp_created_on DATETIME NOT NULL DEFAULT GETDATE(),
        emp_updated_on DATETIME
    )
END;

-- Create TblUserRoles086
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'TblUserRoles086') AND type in (N'U'))
BEGIN
    CREATE TABLE TblUserRoles086 (
        role_id INT IDENTITY(1,1) PRIMARY KEY,
        role_name VARCHAR(50) NOT NULL UNIQUE,
        role_description VARCHAR(200),
        role_created_on DATETIME NOT NULL DEFAULT GETDATE(),
        role_updated_on DATETIME
    )
END;

-- Create TblUsers086
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'TblUsers086') AND type in (N'U'))
BEGIN
    CREATE TABLE TblUsers086 (
        usr_idpk INT IDENTITY(1,1) PRIMARY KEY,
        usr_username VARCHAR(50) NOT NULL UNIQUE,
        usr_password VARCHAR(255) NOT NULL,
        usr_empidfk INT FOREIGN KEY REFERENCES TblEmployees086(emp_idpk),
        usr_roleidfk INT FOREIGN KEY REFERENCES TblUserRoles086(role_id),
        usr_start_date DATETIME NOT NULL DEFAULT GETDATE(),
        usr_end_date DATETIME,
        usr_created_on DATETIME NOT NULL DEFAULT GETDATE(),
        usr_updated_on DATETIME,
        -- User preferences
        usr_language VARCHAR(10) DEFAULT 'en',
        usr_timezone VARCHAR(50) DEFAULT 'UTC',
        usr_theme VARCHAR(20) DEFAULT 'light',
        usr_font_size VARCHAR(10) DEFAULT 'medium',
        -- Dashboard preferences
        usr_show_quick_actions BIT DEFAULT 1,
        usr_show_recent BIT DEFAULT 1,
        usr_show_stats BIT DEFAULT 1,
        -- Security settings
        usr_2fa_enabled BIT DEFAULT 0,
        usr_2fa_secret VARCHAR(32),
        -- Notification preferences
        usr_notify_security BIT DEFAULT 1,
        usr_notify_system BIT DEFAULT 1,
        usr_notify_marketing BIT DEFAULT 0,
        usr_notify_transactions BIT DEFAULT 1,
        usr_notify_login BIT DEFAULT 1,
        usr_notify_system_alerts BIT DEFAULT 1,
        -- Integration settings
        usr_calendar_integration BIT DEFAULT 0,
        usr_email_integration BIT DEFAULT 0,
        usr_analytics_integration BIT DEFAULT 0
    )
END;

-- Create TblCustomers086
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'TblCustomers086') AND type in (N'U'))
BEGIN
    CREATE TABLE TblCustomers086 (
        cust_idpk INT IDENTITY(1,1) PRIMARY KEY,
        cust_firstname VARCHAR(50) NOT NULL,
        cust_lastname VARCHAR(50) NOT NULL,
        cust_email VARCHAR(100),
        cust_phone VARCHAR(20),
        cust_address VARCHAR(200),
        cust_dob DATE NOT NULL,
        cust_created_on DATETIME NOT NULL DEFAULT GETDATE(),
        cust_updated_on DATETIME
    )
END;

-- Create TblAccountDetails086
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'TblAccountDetails086') AND type in (N'U'))
BEGIN
    CREATE TABLE TblAccountDetails086 (
        acc_account_number INT IDENTITY(1,1) PRIMARY KEY,
        acc_customer_id INT NOT NULL FOREIGN KEY REFERENCES TblCustomers086(cust_idpk),
        acc_account_type VARCHAR(20),
        acc_balance DECIMAL(15, 2) NOT NULL DEFAULT 0.00
    )
END;

-- Create TblKyc086
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'TblKyc086') AND type in (N'U'))
BEGIN
    CREATE TABLE TblKyc086 (
        kyc_id INT IDENTITY(1,1) PRIMARY KEY,
        kyc_customer_id INT NOT NULL UNIQUE FOREIGN KEY REFERENCES TblCustomers086(cust_idpk),
        kyc_id_type VARCHAR(20),
        kyc_id_number VARCHAR(50) NOT NULL UNIQUE,
        kyc_document_url VARCHAR(255),
        kyc_verified BIT DEFAULT 0
    )
END;

-- Create TblTransactions086
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'TblTransactions086') AND type in (N'U'))
BEGIN
    CREATE TABLE TblTransactions086 (
        tst_transaction_id INT IDENTITY(1,1) PRIMARY KEY,
        tst_account_number INT NOT NULL FOREIGN KEY REFERENCES TblAccountDetails086(acc_account_number),
        tst_amount DECIMAL(15, 2) NOT NULL,
        tst_transaction_type VARCHAR(20),
        tst_created_by_user_id INT FOREIGN KEY REFERENCES TblUsers086(usr_idpk),
        tst_created_on DATETIME NOT NULL DEFAULT GETDATE(),
        tst_description VARCHAR(200)
    )
END;

-- Create TblServiceRequests086
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'TblServiceRequests086') AND type in (N'U'))
BEGIN
    CREATE TABLE TblServiceRequests086 (
        request_id INT IDENTITY(1,1) PRIMARY KEY,
        customer_id INT NOT NULL FOREIGN KEY REFERENCES TblCustomers086(cust_idpk),
        request_type VARCHAR(50) NOT NULL,
        description TEXT NOT NULL,
        priority VARCHAR(20) NOT NULL DEFAULT 'Medium',
        status VARCHAR(20) NOT NULL DEFAULT 'Pending',
        notes TEXT,
        created_by INT NOT NULL FOREIGN KEY REFERENCES TblUsers086(usr_idpk),
        created_at DATETIME NOT NULL DEFAULT GETDATE(),
        completed_by INT FOREIGN KEY REFERENCES TblUsers086(usr_idpk),
        completed_at DATETIME,
        updated_at DATETIME
    )
END;

-- Insert default roles if they don't exist
IF NOT EXISTS (SELECT * FROM TblUserRoles086 WHERE role_name = 'Admin')
BEGIN
    INSERT INTO TblUserRoles086 (role_name, role_description)
    VALUES 
        ('Admin', 'System administrator with full access'),
        ('Manager', 'Branch manager with employee management access'),
        ('Teller', 'Bank teller with customer service access')
END;
"""

def create_tables():
    try:
        with engine.connect() as connection:
            connection.execute(text(create_tables_sql))
            connection.commit()
            print("Successfully created database tables and inserted default roles")
    except Exception as e:
        print(f"Error creating tables: {str(e)}")

if __name__ == '__main__':
    create_tables()
