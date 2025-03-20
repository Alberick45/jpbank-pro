import pyodbc

conn_str = (
    "Driver={ODBC Driver 17 for SQL Server};"
    "Server=localhost;"
    "Database=jpbank_086;"
    "Trusted_Connection=yes;"
)

conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

# Check each table's data
tables = [
    'tbl_user_roles_086',
    'tbl_employees_086',
    'tbl_users_086',
    'tbl_customers_086',
    'tbl_account_details_086',
    'tbl_kyc_086',
    'tbl_transactions_086',
    'tbl_gender_086',
    'tbl_nationality_086',
    'tbl_work_status_086',
    'tbl_marital_status_086',
    'tbl_job_title_086'
]

for table in tables:
    print(f"\nContents of {table}:")
    cursor.execute(f"SELECT * FROM {table}")
    rows = cursor.fetchall()
    if rows:
        # Print column names
        print([column[0] for column in cursor.description])
        # Print first 5 rows
        for row in rows[:5]:
            print(row)
    else:
        print("No data found")
    print("-" * 80)

conn.close()