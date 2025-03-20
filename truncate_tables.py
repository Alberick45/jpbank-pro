import pyodbc

# Database configuration
driver = 'ODBC Driver 17 for SQL Server'
server = 'localhost'
database = 'jpbank_086'
trusted_connection = 'yes'

# Create connection string
conn_str = f'DRIVER={driver};SERVER={server};DATABASE={database};Trusted_Connection={trusted_connection}'

try:
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    # Disable foreign key constraints
    cursor.execute("EXEC sp_MSforeachtable 'ALTER TABLE ? NOCHECK CONSTRAINT ALL'")

    # Truncate tables in reverse order of dependencies
    tables = [
        'tbl_transactions_086',
        'tbl_account_details_086',
        'tbl_kyc_086',
        'tbl_customers_086',
        'tbl_users_086',
        'tbl_employees_086',
        'tbl_user_roles_086'
    ]

    for table in tables:
        cursor.execute(f"TRUNCATE TABLE {table}")
        print(f"Truncated {table}")

    # Re-enable foreign key constraints
    cursor.execute("EXEC sp_MSforeachtable 'ALTER TABLE ? CHECK CONSTRAINT ALL'")
    
    conn.commit()
    print("All tables truncated successfully")

except pyodbc.Error as e:
    print(f"An error occurred: {e}")
    conn.rollback()
finally:
    conn.close()