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

# SQL statements to add new columns
add_columns_sql = """
-- User preferences
IF NOT EXISTS(SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('TblUsers086') AND name = 'usr_language')
    ALTER TABLE TblUsers086 ADD usr_language VARCHAR(10) DEFAULT 'en';

IF NOT EXISTS(SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('TblUsers086') AND name = 'usr_timezone')
    ALTER TABLE TblUsers086 ADD usr_timezone VARCHAR(50) DEFAULT 'UTC';

IF NOT EXISTS(SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('TblUsers086') AND name = 'usr_theme')
    ALTER TABLE TblUsers086 ADD usr_theme VARCHAR(20) DEFAULT 'light';

IF NOT EXISTS(SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('TblUsers086') AND name = 'usr_font_size')
    ALTER TABLE TblUsers086 ADD usr_font_size VARCHAR(10) DEFAULT 'medium';

-- Dashboard preferences
IF NOT EXISTS(SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('TblUsers086') AND name = 'usr_show_quick_actions')
    ALTER TABLE TblUsers086 ADD usr_show_quick_actions BIT DEFAULT 1;

IF NOT EXISTS(SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('TblUsers086') AND name = 'usr_show_recent')
    ALTER TABLE TblUsers086 ADD usr_show_recent BIT DEFAULT 1;

IF NOT EXISTS(SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('TblUsers086') AND name = 'usr_show_stats')
    ALTER TABLE TblUsers086 ADD usr_show_stats BIT DEFAULT 1;

-- Security settings
IF NOT EXISTS(SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('TblUsers086') AND name = 'usr_2fa_enabled')
    ALTER TABLE TblUsers086 ADD usr_2fa_enabled BIT DEFAULT 0;

IF NOT EXISTS(SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('TblUsers086') AND name = 'usr_2fa_secret')
    ALTER TABLE TblUsers086 ADD usr_2fa_secret VARCHAR(32);

-- Notification preferences
IF NOT EXISTS(SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('TblUsers086') AND name = 'usr_notify_security')
    ALTER TABLE TblUsers086 ADD usr_notify_security BIT DEFAULT 1;

IF NOT EXISTS(SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('TblUsers086') AND name = 'usr_notify_system')
    ALTER TABLE TblUsers086 ADD usr_notify_system BIT DEFAULT 1;

IF NOT EXISTS(SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('TblUsers086') AND name = 'usr_notify_marketing')
    ALTER TABLE TblUsers086 ADD usr_notify_marketing BIT DEFAULT 0;

IF NOT EXISTS(SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('TblUsers086') AND name = 'usr_notify_transactions')
    ALTER TABLE TblUsers086 ADD usr_notify_transactions BIT DEFAULT 1;

IF NOT EXISTS(SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('TblUsers086') AND name = 'usr_notify_login')
    ALTER TABLE TblUsers086 ADD usr_notify_login BIT DEFAULT 1;

IF NOT EXISTS(SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('TblUsers086') AND name = 'usr_notify_system_alerts')
    ALTER TABLE TblUsers086 ADD usr_notify_system_alerts BIT DEFAULT 1;

-- Integration settings
IF NOT EXISTS(SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('TblUsers086') AND name = 'usr_calendar_integration')
    ALTER TABLE TblUsers086 ADD usr_calendar_integration BIT DEFAULT 0;

IF NOT EXISTS(SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('TblUsers086') AND name = 'usr_email_integration')
    ALTER TABLE TblUsers086 ADD usr_email_integration BIT DEFAULT 0;

IF NOT EXISTS(SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('TblUsers086') AND name = 'usr_analytics_integration')
    ALTER TABLE TblUsers086 ADD usr_analytics_integration BIT DEFAULT 0;
"""

def run_migration():
    try:
        with engine.connect() as connection:
            connection.execute(text(add_columns_sql))
            connection.commit()
            print("Successfully added new columns to TblUsers086")
    except Exception as e:
        print(f"Error running migration: {str(e)}")

if __name__ == '__main__':
    run_migration()
