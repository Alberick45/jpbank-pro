import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()

# Database configuration
server = os.getenv('DB_SERVER', 'localhost')
database = os.getenv('DB_NAME', 'jpbank_086')
driver = os.getenv('DB_DRIVER', 'ODBC Driver 17 for SQL Server')
trusted_connection = os.getenv('DB_TRUSTED_CONNECTION', 'yes')

# Create connection string
params = quote_plus(f'DRIVER={{{driver}}};SERVER={server};DATABASE={database};Trusted_Connection={trusted_connection}')
SQLALCHEMY_DATABASE_URI = f"mssql+pyodbc:///?odbc_connect={params}"

def upgrade():
    engine = create_engine(SQLALCHEMY_DATABASE_URI)
    
    with engine.connect() as connection:
        # Add created_on column if it doesn't exist
        connection.execute(text("""
            IF NOT EXISTS (
                SELECT * FROM sys.columns 
                WHERE object_id = OBJECT_ID('TblAccountDetails086') 
                AND name = 'acc_created_on'
            )
            BEGIN
                ALTER TABLE TblAccountDetails086
                ADD acc_created_on DATETIME DEFAULT GETDATE()
            END
        """))
        
        # Add updated_on column if it doesn't exist
        connection.execute(text("""
            IF NOT EXISTS (
                SELECT * FROM sys.columns 
                WHERE object_id = OBJECT_ID('TblAccountDetails086') 
                AND name = 'acc_updated_on'
            )
            BEGIN
                ALTER TABLE TblAccountDetails086
                ADD acc_updated_on DATETIME NULL
            END
        """))
        
        connection.commit()

def downgrade():
    engine = create_engine(SQLALCHEMY_DATABASE_URI)
    
    with engine.connect() as connection:
        # Remove the columns if they exist
        connection.execute(text("""
            IF EXISTS (
                SELECT * FROM sys.columns 
                WHERE object_id = OBJECT_ID('TblAccountDetails086') 
                AND name = 'acc_created_on'
            )
            BEGIN
                ALTER TABLE TblAccountDetails086
                DROP COLUMN acc_created_on
            END
        """))
        
        connection.execute(text("""
            IF EXISTS (
                SELECT * FROM sys.columns 
                WHERE object_id = OBJECT_ID('TblAccountDetails086') 
                AND name = 'acc_updated_on'
            )
            BEGIN
                ALTER TABLE TblAccountDetails086
                DROP COLUMN acc_updated_on
            END
        """))
        
        connection.commit()

if __name__ == '__main__':
    upgrade()
