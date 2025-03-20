import pyodbc
from datetime import datetime, date
import bcrypt
import os
import uuid
from urllib.parse import quote_plus

# Database configuration
driver = 'ODBC Driver 17 for SQL Server'
server = 'localhost'
database = 'jpbank_086'
trusted_connection = 'yes'

# Create connection string
conn_str = f'DRIVER={driver};SERVER={server};DATABASE={database};Trusted_Connection={trusted_connection}'

# Helper function to hash passwords
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

# Helper function to generate transaction reference
def generate_reference():
    return f"TRX{uuid.uuid4().hex[:8].upper()}"

# Connect to database
conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

# Check if role exists before inserting
def role_exists(cursor, role_name):
    cursor.execute("SELECT COUNT(*) FROM tbl_user_roles_086 WHERE role_name = ?", (role_name,))
    return cursor.fetchone()[0] > 0

# Check if customer exists before inserting
def customer_exists(cursor, email):
    cursor.execute("SELECT COUNT(*) FROM tbl_customers_086 WHERE cus_email = ?", (email,))
    return cursor.fetchone()[0] > 0

try:
    # Only insert roles if they don't exist
    roles = [
        ('Manager', 'MGR', datetime.now(), datetime.now()),
        ('Supervisor', 'SUP', datetime.now(), datetime.now()),
        ('Teller', 'TLR', datetime.now(), datetime.now())
    ]
    
    for role in roles:
        if not role_exists(cursor, role[0]):
            cursor.execute("""
            INSERT INTO tbl_user_roles_086 (role_name, role_sht_name, role_created_date, role_edited_date)
            VALUES (?, ?, ?, ?)
            """, role)
            conn.commit()

    # Insert customers
    customers = [
        ('John', 'Smith', 'Robert', date(1990, 5, 15), 1, 1, 1, 'Engineer', 'john.s@email.com', 
         '+1234567890', '123 Main St', 100, datetime.now(), datetime.now(), 'ADM1', 'ADM1'),
        ('Sarah', 'Johnson', 'Marie', date(1985, 8, 20), 2, 1, 2, 'Teacher', 'sarah.j@email.com', 
         '+1234567891', '456 Oak Ave', 50, datetime.now(), datetime.now(), 'ADM1', 'ADM1')
    ]

    for customer in customers:
        if not customer_exists(cursor, customer[8]):  # Check email
            cursor.execute("""
            INSERT INTO tbl_customers_086 (cus_firstname, cus_lastname, cus_othernames, cus_dob, 
            cus_gender_idfk, cus_nationality_idfk, cus_marital_status_idfk, cus_occupation, 
            cus_email, cus_phone_nos, cus_address, cus_loyalty_points, cus_created_on, 
            cus_edited_on, cus_created_by_user_idfk, cus_edited_by_user_idfk)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, customer)
            conn.commit()

    # Get customer IDs for accounts
    cursor.execute("SELECT cus_id FROM tbl_customers_086")
    customer_ids = [row[0] for row in cursor.fetchall()]

    # Insert accounts for each customer
    for cus_id in customer_ids:
        cursor.execute("""
        INSERT INTO tbl_account_details_086 (acc_customer_id, acc_account_type, acc_balance)
        VALUES (?, ?, ?)
        """, (cus_id, 'Savings', 1000.00))
        conn.commit()

    # Get account numbers for transactions
    cursor.execute("SELECT acc_account_number FROM tbl_account_details_086")
    account_numbers = [row[0] for row in cursor.fetchall()]

    # Insert transactions
        # Insert transactions
    for acc_num in account_numbers:
        cursor.execute("""
        INSERT INTO tbl_transactions_086 (tst_reference, tst_account_number, tst_amount, 
        tst_transaction_type, tst_created_by_user_id, tst_created_on)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (generate_reference(), acc_num, 1000.00, 'Deposit', 1, datetime.now()))
        conn.commit()

except pyodbc.Error as e:
    print(f"An error occurred: {e}")
    conn.rollback()
finally:
    conn.close()