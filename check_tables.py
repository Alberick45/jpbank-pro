import pyodbc
from datetime import datetime, date

# Database configuration
driver = 'ODBC Driver 17 for SQL Server'
server = 'localhost'
database = 'jpbank_086'
trusted_connection = 'yes'

# Create connection string
conn_str = f'DRIVER={driver};SERVER={server};DATABASE={database};Trusted_Connection={trusted_connection}'

conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

try:
    # Check tables and their columns
    tables = [
        'tbl_user_roles_086',
        'tbl_employees_086',
        'tbl_users_086',
        'tbl_customers_086',
        'tbl_account_details_086',
        'tbl_kyc_086',
        'tbl_transactions_086'
    ]

    for table in tables:
        print(f"\nChecking table: {table}")
        cursor.execute(f"""
        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = '{table}'
        ORDER BY ORDINAL_POSITION
        """)
        columns = cursor.fetchall()
        for col in columns:
            print(f"Column: {col[0]}, Type: {col[1]}, Nullable: {col[2]}, Default: {col[3]}")

        # Check foreign keys
        cursor.execute(f"""
        SELECT 
            OBJECT_NAME(f.parent_object_id) AS TableName,
            COL_NAME(fc.parent_object_id, fc.parent_column_id) AS ColumnName,
            OBJECT_NAME(f.referenced_object_id) AS ReferenceTableName,
            COL_NAME(fc.referenced_object_id, fc.referenced_column_id) AS ReferenceColumnName
        FROM sys.foreign_keys AS f
        INNER JOIN sys.foreign_key_columns AS fc
            ON f.object_id = fc.constraint_object_id
        WHERE OBJECT_NAME(f.parent_object_id) = '{table}'
        """)
        fks = cursor.fetchall()
        if fks:
            print("\nForeign Keys:")
            for fk in fks:
                print(f"{fk[0]}.{fk[1]} -> {fk[2]}.{fk[3]}")

except Exception as e:
    print(f"An error occurred: {str(e)}")

finally:
    conn.close()
