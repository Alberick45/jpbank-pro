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

def verify_roles():
    with engine.connect() as conn:
        result = conn.execute("SELECT role_id, role_name, role_sht_name FROM tbl_user_roles_086")
        print("\nExisting roles:")
        for row in result:
            print(f"ID: {row[0]}, Name: {row[1]}, Short Name: {row[2]}")

if __name__ == '__main__':
    verify_roles()
