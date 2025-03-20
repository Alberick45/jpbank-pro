import pyodbc
import os
from dotenv import load_dotenv

load_dotenv()

# Database connection parameters
server = os.getenv('DB_SERVER', 'localhost')
database = os.getenv('DB_NAME', 'jpbank_086')
trusted_connection = os.getenv('DB_TRUSTED_CONNECTION', 'yes')

# Create connection string
conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection={trusted_connection}'

def verify_table_structure():
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        # Get column information for tbl_employees_086
        cursor.execute("""
            SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = 'tbl_employees_086'
            ORDER BY ORDINAL_POSITION;
        """)
        
        print("\nColumns in tbl_employees_086:")
        columns = cursor.fetchall()
        for col in columns:
            print(f"Column: {col[0]}, Type: {col[1]}", end='')
            if col[2]:
                print(f"({col[2]})")
            else:
                print()
                
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    verify_table_structure()
