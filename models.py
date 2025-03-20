from sqlalchemy import Column, Integer, String, DateTime, Date, Text, Numeric, ForeignKey, Boolean
from sqlalchemy.orm import relationship, declarative_base, backref
from flask_login import UserMixin
from datetime import datetime

Base = declarative_base()

class TblEmployees086(Base):
    __tablename__ = 'TblEmployees086'

    emp_idpk = Column(Integer, primary_key=True)
    emp_firstname = Column(String(50), nullable=False)
    emp_lastname = Column(String(50), nullable=False)
    emp_email = Column(String(100), nullable=False)
    emp_phone = Column(String(20))
    emp_address = Column(String(200))
    emp_department = Column(String(50))
    emp_dob = Column(Date, nullable=False)
    emp_photo = Column(String(255))
    emp_created_on = Column(DateTime, nullable=False, default=datetime.utcnow)
    emp_updated_on = Column(DateTime, onupdate=datetime.utcnow)

    # Relationship
    users = relationship('TblUsers086', back_populates='employee')

class TblUserRoles086(Base):
    __tablename__ = 'TblUserRoles086'

    role_id = Column(Integer, primary_key=True)
    role_name = Column(String(50), nullable=False, unique=True)
    role_description = Column(String(200))
    role_created_on = Column(DateTime, nullable=False, default=datetime.utcnow)
    role_updated_on = Column(DateTime, onupdate=datetime.utcnow)

    # Relationship
    users = relationship('TblUsers086', back_populates='role')

class TblUsers086(Base, UserMixin):
    __tablename__ = 'TblUsers086'

    usr_idpk = Column(Integer, primary_key=True)
    usr_username = Column(String(50), nullable=False, unique=True)
    usr_password = Column(String(255), nullable=False)
    usr_empidfk = Column(Integer, ForeignKey('TblEmployees086.emp_idpk'))
    usr_roleidfk = Column(Integer, ForeignKey('TblUserRoles086.role_id'))
    usr_start_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    usr_end_date = Column(DateTime)
    usr_created_on = Column(DateTime, nullable=False, default=datetime.utcnow)
    usr_updated_on = Column(DateTime, onupdate=datetime.utcnow)

    # User preferences
    usr_language = Column(String(10), default='en')
    usr_timezone = Column(String(50), default='UTC')
    usr_theme = Column(String(20), default='light')
    usr_font_size = Column(String(10), default='medium')

    # Dashboard preferences
    usr_show_quick_actions = Column(Boolean, default=True)
    usr_show_recent = Column(Boolean, default=True)
    usr_show_stats = Column(Boolean, default=True)

    # Security settings
    usr_2fa_enabled = Column(Boolean, default=False)
    usr_2fa_secret = Column(String(32))

    # Notification preferences
    usr_notify_security = Column(Boolean, default=True)
    usr_notify_system = Column(Boolean, default=True)
    usr_notify_marketing = Column(Boolean, default=False)
    usr_notify_transactions = Column(Boolean, default=True)
    usr_notify_login = Column(Boolean, default=True)
    usr_notify_system_alerts = Column(Boolean, default=True)

    # Integration settings
    usr_calendar_integration = Column(Boolean, default=False)
    usr_email_integration = Column(Boolean, default=False)
    usr_analytics_integration = Column(Boolean, default=False)

    # Relationships
    employee = relationship('TblEmployees086', back_populates='users')
    role = relationship('TblUserRoles086', back_populates='users')

    def get_id(self):
        return str(self.usr_idpk)

class TblCustomers086(Base):
    __tablename__ = 'tbl_customers_086'

    cus_id = Column(Integer, primary_key=True, autoincrement=True)
    cus_firstname = Column(String(15), nullable=False)
    cus_lastname = Column(String(15), nullable=False)
    cus_othernames = Column(String(50))
    cus_dob = Column(Date, nullable=False)
    cus_gender_idfk = Column(Integer)
    cus_nationality_idfk = Column(Integer)
    cus_marital_status_idfk = Column(Integer)
    cus_occupation = Column(String(30))
    cus_email = Column(String(100), nullable=False)
    cus_phone_nos = Column(String(20))
    cus_address = Column(Text, nullable=False)
    cus_loyalty_points = Column(Integer)
    cus_created_on = Column(DateTime)
    cus_edited_on = Column(DateTime)
    cus_created_by_user_idfk = Column(String(10))
    cus_edited_by_user_idfk = Column(String(10))

    # Relationships
    accounts = relationship('TblAccountDetails086', back_populates='customer')
    kyc = relationship('TblKyc086', back_populates='customer', uselist=False)
    service_requests = relationship('TblServiceRequests086', back_populates='customer')

class TblAccountDetails086(Base):
    __tablename__ = 'TblAccountDetails086'

    acc_account_number = Column(Integer, primary_key=True)
    acc_customer_id = Column(Integer, ForeignKey('tbl_customers_086.cus_id'), nullable=False)
    acc_account_type = Column(String(20))
    acc_balance = Column(Numeric(15, 2), nullable=False)
    acc_created_on = Column(DateTime, nullable=False, default=datetime.utcnow)
    acc_updated_on = Column(DateTime, onupdate=datetime.utcnow)
    
    # Relationships
    customer = relationship('TblCustomers086', back_populates='accounts')
    transactions = relationship('TblTransactions086', back_populates='account')

class TblKyc086(Base):
    __tablename__ = 'TblKyc086'

    kyc_id = Column(Integer, primary_key=True)
    kyc_customer_id = Column(Integer, ForeignKey('tbl_customers_086.cus_id'), nullable=False, unique=True)
    kyc_id_type = Column(String(20))
    kyc_id_number = Column(String(50), nullable=False, unique=True)
    kyc_document_url = Column(String(255))
    kyc_verified = Column(Boolean, default=False)
    
    # Relationship
    customer = relationship('TblCustomers086', back_populates='kyc')

class TblTransactions086(Base):
    __tablename__ = 'TblTransactions086'

    # Transaction types
    TRANSACTION_TYPE_DEPOSIT = 'DEPOSIT'
    TRANSACTION_TYPE_WITHDRAWAL = 'WITHDRAWAL'
    TRANSACTION_TYPE_TRANSFER = 'TRANSFER'
    TRANSACTION_TYPE_ACCOUNT_OPEN = 'ACCOUNT_OPEN'
    TRANSACTION_TYPE_ACCOUNT_CLOSE = 'ACCOUNT_CLOSE'

    tst_transaction_id = Column(Integer, primary_key=True)
    tst_account_number = Column(Integer, ForeignKey('TblAccountDetails086.acc_account_number'), nullable=False)
    tst_amount = Column(Numeric(15, 2), nullable=False)
    tst_transaction_type = Column(String(20))
    tst_created_by_user_id = Column(Integer, ForeignKey('TblUsers086.usr_idpk'))
    tst_created_on = Column(DateTime, nullable=False, default=datetime.utcnow)
    tst_description = Column(String(200))
    tst_status = Column(String(20), default='COMPLETED')  # PENDING, COMPLETED, FAILED
    tst_processing_time = Column(Numeric(10, 2))  # Time in seconds
    
    # Relationships
    account = relationship('TblAccountDetails086', back_populates='transactions')
    created_by = relationship('TblUsers086')

class TblAddress086(Base):
    __tablename__ = 'tbl_address_086'
    adr_address_idpk = Column(Integer, primary_key=True, autoincrement=True)
    adr_address = Column(String(50))

class TblCountry086(Base):
    __tablename__ = 'tbl_country_086'
    cty_idpk = Column(Integer, primary_key=True, autoincrement=True)
    cty_name = Column(String(50))
    cty_shortname = Column(String(6))
    cty_nationality = Column(String(50))
    cty_created_by_user_idfk = Column(Integer)
    cty_edited_by_user_idfk = Column(Integer)
    cty_created_on = Column(DateTime)
    cty_edited_on = Column(DateTime)

class TblGender086(Base):
    __tablename__ = 'tbl_gender_086'
    gnd_gender_idpk = Column(Integer, primary_key=True, autoincrement=True)
    gnd_geder_type = Column(String(50))

class TblMaritalStatus086(Base):
    __tablename__ = 'tbl_marital_status_086'
    mts_marital_status_idpk = Column(Integer, primary_key=True, autoincrement=True)
    mts_marital_status_type = Column(String(50))

class TblSecurityLogs086(Base):
    __tablename__ = 'tbl_security_logs_086'
    log_id = Column(Integer, primary_key=True, autoincrement=True)
    log_customer_account_number = Column(Integer)
    log_employee_id = Column(Integer, nullable=False)
    log_action = Column(String(255), nullable=False)
    log_ip_address = Column(String(50))
    log_device_info = Column(String(255))
    log_timestamp = Column(DateTime)
    success = Column(Integer, nullable=False)

class TblServiceRequests086(Base):
    __tablename__ = 'tbl_service_requests_086'
    request_id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey('tbl_customers_086.cus_id'), nullable=False)
    request_type = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    priority = Column(String(10), default='Medium')
    status = Column(String(20), default='Pending')
    created_by = Column(Integer, ForeignKey('TblUsers086.usr_idpk'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_by = Column(Integer, ForeignKey('TblUsers086.usr_idpk'))
    completed_at = Column(DateTime)
    
    # Relationships
    customer = relationship('TblCustomers086', back_populates='service_requests')
    creator = relationship('TblUsers086', foreign_keys=[created_by], backref='created_requests')
    completer = relationship('TblUsers086', foreign_keys=[completed_by], backref='completed_requests')