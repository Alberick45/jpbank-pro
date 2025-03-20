from sqlalchemy import create_engine, inspect
import os
from dotenv import load_dotenv
from urllib.parse import quote_plus

load_dotenv()

# Database connection parameters
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

engine = create_engine(f"mssql+pyodbc:///?odbc_connect={params}")
inspector = inspect(engine)

def check_tables():
    print("\nChecking database tables...")
    tables = inspector.get_table_names()
    print("\nExisting tables:")
    for table in tables:
        print(f"\nTable: {table}")
        columns = inspector.get_columns(table)
        print("Columns:")
        for column in columns:
            print(f"  - {column['name']}: {column['type']}")

if __name__ == '__main__':
    check_tables()
