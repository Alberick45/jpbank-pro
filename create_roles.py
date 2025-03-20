from datetime import datetime
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, TblUserRoles086

load_dotenv()

# Database connection parameters
server = os.getenv('DB_SERVER', 'localhost')
database = os.getenv('DB_NAME', 'jpbank_086')
trusted_connection = os.getenv('DB_TRUSTED_CONNECTION', 'yes')
driver = os.getenv('DB_DRIVER', 'ODBC Driver 17 for SQL Server')

# Create the connection string
connection_string = f'mssql+pyodbc://@{server}/{database}?driver={driver}&Trusted_Connection={trusted_connection}'
engine = create_engine(connection_string)

# Create a session
Session = sessionmaker(bind=engine)
session = Session()

def create_default_roles():
    # Define default roles
    default_roles = [
        {
            'name': 'Admin',
            'short_name': 'ADM'
        },
        {
            'name': 'Manager',
            'short_name': 'MGR'
        },
        {
            'name': 'Teller',
            'short_name': 'TLR'
        }
    ]
    
    try:
        # Create each role if it doesn't exist
        for role in default_roles:
            existing_role = session.query(TblUserRoles086).filter_by(role_name=role['name']).first()
            if not existing_role:
                new_role = TblUserRoles086(
                    role_name=role['name'],
                    role_sht_name=role['short_name'],
                    role_created_date=datetime.now()
                )
                session.add(new_role)
        
        session.commit()
        print("Default roles created successfully!")
        
    except Exception as e:
        session.rollback()
        print(f"Error creating roles: {str(e)}")
    finally:
        session.close()

if __name__ == '__main__':
    create_default_roles()
