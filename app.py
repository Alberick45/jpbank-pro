from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, Response
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from urllib.parse import urlparse, quote_plus
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
from models import Base, TblUsers086, TblEmployees086, TblUserRoles086, TblCustomers086, TblTransactions086, TblAccountDetails086, TblSecurityLogs086, TblServiceRequests086
import time
import io
import csv
from sqlalchemy import or_
from flask_wtf import FlaskForm
from wtforms import StringField, DateField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Email

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key')
app.config['UPLOAD_FOLDER'] = './static/uploads'

# Database configuration
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

# Configure SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = f"mssql+pyodbc:///?odbc_connect={params}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Initialize Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return db.session.query(TblUsers086).get(int(user_id))

def role_required(role_name):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('login'))
            role = db.session.query(TblUserRoles086).filter_by(role_name=role_name).first()
            if current_user.usr_roleidfk != role.role_id:
                flash('You do not have permission to access this page.', 'error')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.role or current_user.role.role_name != 'Admin':
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# Common choices for forms
NATIONALITY_CHOICES = [
    (1, 'Ghanaian'),
    (2, 'Nigerian'),
    (3, 'Ivorian'),
    (4, 'Togolese'),
    (5, 'Beninese'),
    (6, 'Other')
]

class CustomerRegistrationForm(FlaskForm):
    firstname = StringField('First Name', validators=[DataRequired()])
    lastname = StringField('Last Name', validators=[DataRequired()])
    othernames = StringField('Other Names')
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone_nos = StringField('Phone Number', validators=[DataRequired()])
    dob = DateField('Date of Birth', validators=[DataRequired()])
    gender = SelectField('Gender', choices=[(1, 'Male'), (2, 'Female')], validators=[DataRequired()], coerce=int)
    nationality = SelectField('Nationality', choices=NATIONALITY_CHOICES, validators=[DataRequired()], coerce=int)
    marital_status = SelectField('Marital Status', 
                               choices=[(1, 'Single'), (2, 'Married'), (3, 'Divorced'), (4, 'Widowed')], 
                               validators=[DataRequired()],
                               coerce=int)
    occupation = StringField('Occupation', validators=[DataRequired()])
    address = TextAreaField('Address', validators=[DataRequired()])
    id_type = SelectField('ID Type', 
                         choices=[('passport', 'Passport'), 
                                ('drivers_license', "Driver's License"), 
                                ('national_id', 'National ID')], 
                         validators=[DataRequired()])
    id_number = StringField('ID Number', validators=[DataRequired()])

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Please enter both username and password.', 'danger')
            return render_template('login.html')
        
        user = db.session.query(TblUsers086).filter_by(usr_username=username).first()
        
        if user and check_password_hash(user.usr_password, password):
            if user.usr_end_date:
                flash('Your account has been deactivated. Please contact an administrator.', 'danger')
                return render_template('login.html')
            
            login_user(user)
            next_page = request.args.get('next')
            
            flash(f'Welcome back, {user.employee.emp_firstname}!', 'success')
            
            if next_page and urlparse(next_page).netloc == '':
                return redirect(next_page)
            return redirect(url_for('index'))
        
        flash('Invalid username or password.', 'danger')
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        try:
            # Get form data
            username = request.form.get('username')
            password = request.form.get('password')
            firstname = request.form.get('firstname')
            lastname = request.form.get('lastname')
            email = request.form.get('email')
            dob = request.form.get('dob')
            role = request.form.get('role')
            
            # Create employee record
            employee = TblEmployees086(
                emp_firstname=firstname,
                emp_lastname=lastname,
                emp_email=email,
                emp_dob=datetime.strptime(dob, '%Y-%m-%d'),
                emp_created_on=datetime.now()
            )
            db.session.add(employee)
            db.session.flush()
            
            # Get selected role
            selected_role = db.session.query(TblUserRoles086).filter_by(role_name=role).first()
            if not selected_role:
                flash('Invalid role selected.', 'danger')
                roles = db.session.query(TblUserRoles086).all()
                return render_template('signup.html', now=datetime.now(), timedelta=timedelta, roles=roles)
            
            # Create user record
            user = TblUsers086(
                usr_username=username,
                usr_password=generate_password_hash(password),
                usr_empidfk=employee.emp_idpk,
                usr_roleidfk=selected_role.role_id,
                usr_start_date=datetime.now(),
                usr_created_on=datetime.now()
            )
            db.session.add(user)
            db.session.commit()
            
            flash('Account created successfully! Please login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred while creating your account: {str(e)}', 'danger')
            roles = db.session.query(TblUserRoles086).all()
            return render_template('signup.html', now=datetime.now(), timedelta=timedelta, roles=roles)
    
    # Get all available roles for the dropdown
    roles = db.session.query(TblUserRoles086).all()
    return render_template('signup.html', now=datetime.now(), timedelta=timedelta, roles=roles)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# Teller Operations Routes
@app.route('/teller/transactions')
@login_required
@role_required('Teller')
def teller_transactions():
    # Get all transactions for display
    transactions = db.session.query(TblTransactions086)\
        .order_by(TblTransactions086.tst_created_on.desc())\
        .all()
    return render_template('teller/transactions.html', transactions=transactions)

@app.route('/teller/customer-service')
@login_required
@role_required('Teller')
def customer_service():
    try:
        # Get all customers for the quick action modal
        customers = db.session.query(TblCustomers086)\
            .order_by(TblCustomers086.cus_lastname)\
            .all()
        
        # Get recent service requests for the interactions table
        recent_requests = db.session.query(TblServiceRequests086)\
            .join(TblCustomers086)\
            .order_by(TblServiceRequests086.created_at.desc())\
            .limit(10)\
            .all()
        
        return render_template('teller/customer_service.html', 
                            customers=customers, 
                            recent_requests=recent_requests)
    except Exception as e:
        flash(f'Error loading customer service dashboard: {str(e)}', 'danger')
        return redirect(url_for('index'))

@app.route('/teller/account-management')
@login_required
@role_required('Teller')
def teller_account_management():
    accounts = db.session.query(TblAccountDetails086).join(TblCustomers086).all()
    customers = db.session.query(TblCustomers086).all()
    return render_template('teller/account_management.html', accounts=accounts, customers=customers)

@app.route('/teller/create-account', methods=['POST'])
@login_required
@role_required('Teller')
def create_account():
    if request.method == 'POST':
        customer_id = request.form['customer_id']
        account_type = request.form['account_type']
        initial_deposit = float(request.form['initial_deposit'])
        
        db = db.session
        try:
            # Create new account
            new_account = TblAccountDetails086(
                acc_customer_id=customer_id,
                acc_account_type=account_type,
                acc_balance=initial_deposit,
                acc_created_on=datetime.now()
            )
            db.add(new_account)
            db.flush()  # Get the new account number
            
            # Create initial deposit transaction
            transaction = TblTransactions086(
                tst_account_number=new_account.acc_account_number,
                tst_transaction_type='DEPOSIT',
                tst_amount=initial_deposit,
                tst_description='Initial deposit',
                tst_status='COMPLETED',
                tst_processing_time=0.0
            )
            db.add(transaction)
            db.commit()
            
            flash('Account created successfully!', 'success')
        except Exception as e:
            db.rollback()
            flash(f'Error creating account: {str(e)}', 'danger')
        finally:
            db.close()
            
    return redirect(url_for('teller_account_management'))

@app.route('/teller/register-customer', methods=['GET', 'POST'])
@login_required
@role_required('Teller')
def register_customer():
    form = CustomerRegistrationForm()
    
    if request.method == 'POST' and form.validate_on_submit():
        try:
            customer = TblCustomers086(
                cus_firstname=form.firstname.data,
                cus_lastname=form.lastname.data,
                cus_othernames=form.othernames.data,
                cus_dob=form.dob.data,
                cus_gender_idfk=form.gender.data,
                cus_nationality_idfk=form.nationality.data,
                cus_marital_status_idfk=form.marital_status.data,
                cus_email=form.email.data,
                cus_phone_nos=form.phone_nos.data,
                cus_address=form.address.data,
                cus_occupation=form.occupation.data,
                cus_created_on=datetime.now(),
                cus_created_by_user_idfk=current_user.usr_username
            )
            db.session.add(customer)
            db.session.flush()

            kyc = TblKyc086(
                kyc_customer_id=customer.cus_id,
                kyc_id_type=form.id_type.data,
                kyc_id_number=form.id_number.data,
                kyc_verified_by=current_user.usr_idpk,
                kyc_verified_at=datetime.now()
            )
            db.session.add(kyc)
            db.session.commit()

            flash('Customer registered successfully!', 'success')
            return redirect(url_for('customer_service'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error registering customer: {str(e)}', 'danger')
            return render_template('teller/register_customer.html', form=form)

    return render_template('teller/register_customer.html', form=form)

@app.route('/teller/make-deposit', methods=['POST'])
@login_required
@role_required('Teller')
def make_deposit():
    if request.method == 'POST':
        account_number = request.form['account_number']
        amount = float(request.form['amount'])
        description = request.form['description']
        
        db = db.session
        try:
            account = db.query(TblAccountDetails086).filter_by(acc_account_number=account_number).first()
            if not account:
                raise ValueError('Account not found')
                
            # Update account balance
            account.acc_balance += amount
            account.acc_updated_on = datetime.now()
            
            # Create transaction record
            transaction = TblTransactions086(
                tst_account_number=account_number,
                tst_transaction_type='DEPOSIT',
                tst_amount=amount,
                tst_description=description,
                tst_status='COMPLETED',
                tst_processing_time=0.0
            )
            db.add(transaction)
            db.commit()
            
            flash('Deposit completed successfully!', 'success')
        except Exception as e:
            db.rollback()
            flash(f'Error processing deposit: {str(e)}', 'danger')
        finally:
            db.close()
            
    return redirect(url_for('teller_account_management'))

@app.route('/teller/make-withdrawal', methods=['POST'])
@login_required
@role_required('Teller')
def make_withdrawal():
    if request.method == 'POST':
        account_number = request.form['account_number']
        amount = float(request.form['amount'])
        description = request.form['description']
        
        db = db.session
        try:
            account = db.query(TblAccountDetails086).filter_by(acc_account_number=account_number).first()
            if not account:
                raise ValueError('Account not found')
            
            if account.acc_balance < amount:
                raise ValueError('Insufficient funds')
                
            # Update account balance
            account.acc_balance -= amount
            account.acc_updated_on = datetime.now()
            
            # Create transaction record
            transaction = TblTransactions086(
                tst_account_number=account_number,
                tst_transaction_type='WITHDRAWAL',
                tst_amount=amount,
                tst_description=description,
                tst_status='COMPLETED',
                tst_processing_time=0.0
            )
            db.add(transaction)
            db.commit()
            
            flash('Withdrawal completed successfully!', 'success')
        except Exception as e:
            db.rollback()
            flash(f'Error processing withdrawal: {str(e)}', 'danger')
        finally:
            db.close()
            
    return redirect(url_for('teller_account_management'))

@app.route('/teller/transfer-funds', methods=['POST'])
@login_required
@role_required('Teller')
def transfer_funds():
    if request.method == 'POST':
        from_account = request.form['from_account']
        to_account = request.form['to_account']
        amount = float(request.form['amount'])
        description = request.form['description']
        
        db = db.session
        try:
            # Get source and destination accounts
            from_acc = db.query(TblAccountDetails086).filter_by(acc_account_number=from_account).first()
            to_acc = db.query(TblAccountDetails086).filter_by(acc_account_number=to_account).first()
            
            if not from_acc or not to_acc:
                raise ValueError('One or both accounts not found')
            
            if from_acc.acc_balance < amount:
                raise ValueError('Insufficient funds in source account')
                
            # Update account balances
            from_acc.acc_balance -= amount
            to_acc.acc_balance += amount
            from_acc.acc_updated_on = datetime.now()
            to_acc.acc_updated_on = datetime.now()
            
            # Create withdrawal transaction
            withdrawal = TblTransactions086(
                tst_account_number=from_account,
                tst_transaction_type='TRANSFER_OUT',
                tst_amount=amount,
                tst_description=f"Transfer to {to_account}: {description}",
                tst_status='COMPLETED',
                tst_processing_time=0.0
            )
            
            # Create deposit transaction
            deposit = TblTransactions086(
                tst_account_number=to_account,
                tst_transaction_type='TRANSFER_IN',
                tst_amount=amount,
                tst_description=f"Transfer from {from_account}: {description}",
                tst_status='COMPLETED',
                tst_processing_time=0.0
            )
            
            db.add(withdrawal)
            db.add(deposit)
            db.commit()
            
            flash('Transfer completed successfully!', 'success')
        except Exception as e:
            db.rollback()
            flash(f'Error processing transfer: {str(e)}', 'danger')
        finally:
            db.close()
            
    return redirect(url_for('teller_account_management'))

@app.route('/customer-service/search', methods=['GET'])
@login_required
@role_required('Teller')
def search_customers():
    try:
        search_term = request.args.get('search', '')
        
        if search_term:
            # Search across multiple fields using OR conditions
            search_filter = or_(
                TblCustomers086.cus_firstname.ilike(f'%{search_term}%'),
                TblCustomers086.cus_lastname.ilike(f'%{search_term}%'),
                TblCustomers086.cus_email.ilike(f'%{search_term}%'),
                TblCustomers086.cus_phone_nos.ilike(f'%{search_term}%')
            )
            customers = db.session.query(TblCustomers086)\
                .filter(search_filter)\
                .order_by(TblCustomers086.cus_lastname)\
                .all()
        else:
            customers = []

        # Get all customers for the quick action modal
        all_customers = db.session.query(TblCustomers086)\
            .order_by(TblCustomers086.cus_lastname)\
            .all()
        
        # Get recent service requests for the interactions table
        recent_requests = db.session.query(TblServiceRequests086)\
            .join(TblCustomers086)\
            .order_by(TblServiceRequests086.created_at.desc())\
            .limit(5)\
            .all()
        
        return render_template('teller/search_customers.html', 
                            customers=customers, 
                            all_customers=all_customers,
                            recent_requests=recent_requests,
                            search_term=search_term)
    except Exception as e:
        flash(f'Error searching customers: {str(e)}', 'danger')
        return redirect(url_for('customer_service'))

@app.route('/customer-service/customers/<int:customer_id>')
@login_required
@role_required('Teller')
def view_customer(customer_id):
    try:
        customer = db.session.get(TblCustomers086, customer_id)
        if not customer:
            flash('Customer not found.', 'danger')
            return redirect(url_for('search_customers'))

        # Get customer's recent service requests
        service_requests = db.session.query(TblServiceRequests086)\
            .filter_by(customer_id=customer_id)\
            .order_by(TblServiceRequests086.created_at.desc())\
            .all()

        return render_template('teller/customer_details.html', 
                            customer=customer,
                            service_requests=service_requests)
    except Exception as e:
        flash(f'Error viewing customer details: {str(e)}', 'danger')
        return redirect(url_for('search_customers'))

@app.route('/customer-service/customers/<int:customer_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('Teller')
def edit_customer(customer_id):
    try:
        customer = db.session.get(TblCustomers086, customer_id)
        if not customer:
            flash('Customer not found.', 'danger')
            return redirect(url_for('search_customers'))

        if request.method == 'POST':
            # Update customer information
            customer.cus_firstname = request.form['firstname']
            customer.cus_lastname = request.form['lastname']
            customer.cus_email = request.form['email']
            customer.cus_phone_nos = request.form['phone']
            customer.cus_address = request.form['address']
            customer.cus_occupation = request.form['occupation']
            
            try:
                db.session.commit()
                flash('Customer information updated successfully.', 'success')
                return redirect(url_for('view_customer', customer_id=customer_id))
            except Exception as e:
                db.session.rollback()
                flash(f'Error updating customer: {str(e)}', 'danger')

        return render_template('teller/edit_customer.html', customer=customer)
    except Exception as e:
        flash(f'Error accessing customer edit form: {str(e)}', 'danger')
        return redirect(url_for('search_customers'))

@app.route('/customer-service/requests')
@login_required
@role_required('Teller')
def customer_service_requests():
    try:
        # Get filter parameters
        status = request.args.get('status', 'all')
        priority = request.args.get('priority', 'all')
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')

        # Base query
        query = db.session.query(TblServiceRequests086)\
            .join(TblCustomers086)

        # Apply filters
        if status != 'all':
            query = query.filter(TblServiceRequests086.status == status)
        if priority != 'all':
            query = query.filter(TblServiceRequests086.priority == priority)

        # Apply sorting
        if sort_by == 'created_at':
            order_col = TblServiceRequests086.created_at
        elif sort_by == 'priority':
            order_col = TblServiceRequests086.priority
        else:
            order_col = TblServiceRequests086.created_at

        if sort_order == 'desc':
            query = query.order_by(order_col.desc())
        else:
            query = query.order_by(order_col.asc())

        requests = query.all()
        
        # Get all customers for the quick action modal
        customers = db.session.query(TblCustomers086)\
            .order_by(TblCustomers086.cus_lastname)\
            .all()
        
        return render_template('teller/service_requests.html', 
                            requests=requests, 
                            customers=customers,
                            current_status=status,
                            current_priority=priority,
                            current_sort=sort_by,
                            current_order=sort_order)
    except Exception as e:
        flash(f'Error loading service requests: {str(e)}', 'danger')
        return redirect(url_for('customer_service'))

@app.route('/customer-service/requests/<int:request_id>/update', methods=['POST'])
@login_required
@role_required('Teller')
def update_service_request(request_id):
    try:
        service_request = db.session.get(TblServiceRequests086, request_id)
        if not service_request:
            return jsonify({'success': False, 'error': 'Service request not found'})

        new_status = request.form.get('status')
        notes = request.form.get('notes', '').strip()

        if not new_status:
            return jsonify({'success': False, 'error': 'Status is required'})

        # Update request status
        service_request.status = new_status
        
        # Add notes if provided
        if notes:
            current_notes = service_request.notes or ''
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            new_note = f'[{timestamp}] {current_user.employee.emp_firstname} {current_user.employee.emp_lastname}: {notes}'
            service_request.notes = f'{current_notes}\n{new_note}' if current_notes else new_note

        # If status is completed, update completion details
        if new_status == 'Completed':
            service_request.completed_by = current_user.usr_idpk
            service_request.completed_at = datetime.now()

        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/customer-service/requests/search', methods=['GET'])
@login_required
@role_required('Teller')
def search_service_requests():
    try:
        search_term = request.args.get('q', '').strip()
        if not search_term:
            return jsonify({'success': False, 'error': 'Search term is required'})

        # Search in customer names and request details
        requests = db.session.query(TblServiceRequests086)\
            .join(TblCustomers086)\
            .filter(
                or_(
                    TblCustomers086.cus_firstname.ilike(f'%{search_term}%'),
                    TblCustomers086.cus_lastname.ilike(f'%{search_term}%'),
                    TblServiceRequests086.request_type.ilike(f'%{search_term}%'),
                    TblServiceRequests086.description.ilike(f'%{search_term}%')
                )
            ).all()

        results = [{
            'id': req.request_id,
            'customer_name': f'{req.customer.cus_firstname} {req.customer.cus_lastname}',
            'request_type': req.request_type,
            'priority': req.priority,
            'status': req.status,
            'created_at': req.created_at.strftime('%Y-%m-%d %H:%M:%S')
        } for req in requests]

        return jsonify({'success': True, 'results': results})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/customer-service/requests/<int:request_id>')
@login_required
@role_required('Teller')
def view_customer_service_request(request_id):
    try:
        service_request = db.session.get(TblServiceRequests086, request_id)
        if not service_request:
            flash('Service request not found.', 'danger')
            return redirect(url_for('customer_service_requests'))
            
        return render_template('teller/view_service_request.html', request=service_request)
    except Exception as e:
        flash(f'Error viewing service request: {str(e)}', 'danger')
        return redirect(url_for('customer_service_requests'))

@app.route('/customer-service/requests/<int:request_id>/complete', methods=['POST'])
@login_required
@role_required('Teller')
def complete_customer_service_request(request_id):
    try:
        service_request = db.session.get(TblServiceRequests086, request_id)
        if not service_request:
            return jsonify({'success': False, 'error': 'Service request not found'})

        service_request.status = 'Completed'
        service_request.completed_by = current_user.usr_idpk
        service_request.completed_at = datetime.now()
        db.session.commit()

        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/customer-service/requests/quick-action', methods=['POST'])
@login_required
@role_required('Teller')
def quick_customer_service_request():
    try:
        action_type = request.form.get('action_type')
        customer_id = request.form.get('customer_id')
        description = request.form.get('description', '')

        if not all([action_type, customer_id]):
            flash('Please select a customer and action type.', 'warning')
            return redirect(url_for('customer_service'))

        # Map action types to priorities
        priority_map = {
            'Lost Card': 'High',
            'PIN Reset': 'High',
            'Card Issue': 'Medium',
            'Contact Update': 'Low'
        }

        new_request = TblServiceRequests086(
            customer_id=customer_id,
            request_type=action_type,
            description=description,
            priority=priority_map.get(action_type, 'Medium'),
            status='Pending',
            created_by=current_user.usr_idpk,
            created_at=datetime.now()
        )
        db.session.add(new_request)
        db.session.commit()

        flash('Service request created successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error creating service request: {str(e)}', 'danger')

    return redirect(url_for('customer_service'))

# Manager Routes
@app.route('/manager/reports')
@login_required
@role_required('Manager')
def manager_reports():
    # Get current week's data
    week_start = datetime.now().date() - timedelta(days=datetime.now().weekday())
    week_end = week_start + timedelta(days=6)
    
    # Get weekly transactions
    weekly_transactions = db.session.query(TblTransactions086)\
        .filter(TblTransactions086.tst_created_on >= week_start)\
        .filter(TblTransactions086.tst_created_on <= week_end)\
        .all()
    
    # Count new account openings (transactions with type 'ACCOUNT_OPEN')
    new_accounts = db.session.query(TblTransactions086)\
        .filter(TblTransactions086.tst_created_on >= week_start)\
        .filter(TblTransactions086.tst_created_on <= week_end)\
        .filter(TblTransactions086.tst_transaction_type == TblTransactions086.TRANSACTION_TYPE_ACCOUNT_OPEN)\
        .count()
    
    # Calculate daily transaction counts for the chart
    daily_counts = []
    daily_new_accounts = []
    
    for i in range(7):
        day = week_start + timedelta(days=i)
        day_end = day + timedelta(days=1)
        
        # Count transactions for this day
        trans_count = db.session.query(TblTransactions086)\
            .filter(TblTransactions086.tst_created_on >= day)\
            .filter(TblTransactions086.tst_created_on < day_end)\
            .count()
        daily_counts.append(trans_count)
        
        # Count new accounts for this day
        acc_count = db.session.query(TblTransactions086)\
            .filter(TblTransactions086.tst_created_on >= day)\
            .filter(TblTransactions086.tst_created_on < day_end)\
            .filter(TblTransactions086.tst_transaction_type == TblTransactions086.TRANSACTION_TYPE_ACCOUNT_OPEN)\
            .count()
        daily_new_accounts.append(acc_count)
    
    # Calculate average processing time for completed transactions
    processing_times = db.session.query(TblTransactions086.tst_processing_time)\
        .filter(TblTransactions086.tst_created_on >= week_start)\
        .filter(TblTransactions086.tst_created_on <= week_end)\
        .filter(TblTransactions086.tst_status == 'COMPLETED')\
        .filter(TblTransactions086.tst_processing_time != None)\
        .all()
    
    avg_processing_time = 0
    if processing_times:
        avg_processing_time = sum(time[0] for time in processing_times) / len(processing_times)
        # Convert to minutes
        avg_processing_time = round(avg_processing_time / 60, 1)
    
    return render_template('manager/reports.html',
                         weekly_transaction_count=len(weekly_transactions),
                         new_accounts_count=new_accounts,
                         avg_satisfaction=4.8,  # This would come from a customer feedback table
                         avg_processing_time=avg_processing_time,
                         daily_transaction_counts=daily_counts,
                         daily_new_accounts=daily_new_accounts,
                         week_start=week_start,
                         week_end=week_end)

@app.route('/manager/employee-management')
@login_required
@role_required('Manager')
def manager_employee_management():
    # Get all employees with their roles
    employees = db.session.query(TblEmployees086)\
        .join(TblUsers086)\
        .join(TblUserRoles086)\
        .all()
    return render_template('manager/employee_management.html', employees=employees)

@app.route('/manager/branch-operations')
@login_required
@role_required('Manager')
def manager_branch_operations():
    # Get daily transaction summary
    daily_transactions = db.session.query(TblTransactions086)\
        .filter(TblTransactions086.tst_created_on >= datetime.now().date())\
        .all()
    return render_template('manager/branch_operations.html', daily_transactions=daily_transactions)

# Admin Additional Routes
@app.route('/admin/manage-users')
@login_required
@admin_required
def admin_manage_users():
    users = db.session.query(TblUsers086).all()
    roles = db.session.query(TblUserRoles086).all()
    employees = db.session.query(TblEmployees086).all()
    return render_template('admin/manage_users.html', users=users, roles=roles, employees=employees)

@app.route('/admin/manage-roles')
@login_required
@admin_required
def admin_manage_roles():
    roles = db.session.query(TblUserRoles086).all()
    return render_template('admin/manage_roles.html', roles=roles)

@app.route('/admin/add-user', methods=['POST'])
@login_required
@admin_required
def admin_add_user():
    username = request.form.get('username')
    password = request.form.get('password')
    employee_id = request.form.get('employee_id')
    role_id = request.form.get('role_id')

    # Check if username already exists
    if db.session.query(TblUsers086).filter_by(usr_username=username).first():
        flash('Username already exists', 'danger')
        return redirect(url_for('admin_manage_users'))

    # Create new user
    new_user = TblUsers086(
        usr_username=username,
        usr_password=generate_password_hash(password),
        usr_empidfk=employee_id,
        usr_roleidfk=role_id,
        usr_start_date=datetime.now()
    )
    db.session.add(new_user)
    db.session.commit()

    flash('User added successfully', 'success')
    return redirect(url_for('admin_manage_users'))

@app.route('/admin/edit-user', methods=['POST'])
@login_required
@admin_required
def admin_edit_user():
    user_id = request.form.get('user_id')
    username = request.form.get('username')
    role_id = request.form.get('role_id')

    user = db.session.query(TblUsers086).get(user_id)
    if not user:
        flash('User not found', 'danger')
        return redirect(url_for('admin_manage_users'))

    # Check if new username is taken by another user
    existing_user = db.session.query(TblUsers086).filter_by(usr_username=username).first()
    if existing_user and existing_user.usr_idpk != int(user_id):
        flash('Username already exists', 'danger')
        return redirect(url_for('admin_manage_users'))

    user.usr_username = username
    user.usr_roleidfk = role_id
    user.usr_updated_on = datetime.now()
    db.session.commit()

    flash('User updated successfully', 'success')
    return redirect(url_for('admin_manage_users'))

@app.route('/api/users/<int:user_id>')
@login_required
@admin_required
def get_user(user_id):
    user = db.session.query(TblUsers086).get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify({
        'usr_idpk': user.usr_idpk,
        'usr_username': user.usr_username,
        'usr_roleidfk': user.usr_roleidfk
    })

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_user(user_id):
    user = db.session.query(TblUsers086).get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Don't allow deleting the last admin user
    if user.role.role_name == 'Admin':
        admin_count = db.session.query(TblUsers086)\
            .join(TblUserRoles086)\
            .filter(TblUserRoles086.role_name == 'Admin')\
            .count()
        if admin_count <= 1:
            return jsonify({'error': 'Cannot delete the last admin user'}), 400

    db.session.delete(user)
    db.session.commit()
    return '', 204

@app.route('/admin/add-role', methods=['POST'])
@login_required
@admin_required
def admin_add_role():
    role_name = request.form.get('role_name')
    role_description = request.form.get('role_description')

    # Check if role name already exists
    if db.session.query(TblUserRoles086).filter_by(role_name=role_name).first():
        flash('Role name already exists', 'danger')
        return redirect(url_for('admin_manage_roles'))

    # Create new role
    new_role = TblUserRoles086(
        role_name=role_name,
        role_description=role_description,
        role_created_on=datetime.now()
    )
    db.session.add(new_role)
    db.session.commit()

    flash('Role added successfully', 'success')
    return redirect(url_for('admin_manage_roles'))

@app.route('/admin/edit-role', methods=['POST'])
@login_required
@admin_required
def admin_edit_role():
    role_id = request.form.get('role_id')
    role_name = request.form.get('role_name')
    role_description = request.form.get('role_description')

    role = db.session.query(TblUserRoles086).get(role_id)
    if not role:
        flash('Role not found', 'danger')
        return redirect(url_for('admin_manage_roles'))

    # Check if new role name is taken by another role
    existing_role = db.session.query(TblUserRoles086).filter_by(role_name=role_name).first()
    if existing_role and existing_role.role_id != int(role_id):
        flash('Role name already exists', 'danger')
        return redirect(url_for('admin_manage_roles'))

    role.role_name = role_name
    role.role_description = role_description
    role.role_updated_on = datetime.now()
    db.session.commit()

    flash('Role updated successfully', 'success')
    return redirect(url_for('admin_manage_roles'))

@app.route('/api/roles/<int:role_id>')
@login_required
@admin_required
def get_role(role_id):
    role = db.session.query(TblUserRoles086).get(role_id)
    if not role:
        return jsonify({'error': 'Role not found'}), 404
    return jsonify({
        'role_id': role.role_id,
        'role_name': role.role_name,
        'role_description': role.role_description
    })

@app.route('/api/roles/<int:role_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_role(role_id):
    role = db.session.query(TblUserRoles086).get(role_id)
    if not role:
        return jsonify({'error': 'Role not found'}), 404

    # Don't allow deleting roles that have users
    if role.users:
        return jsonify({'error': 'Cannot delete role with assigned users'}), 400

    # Don't allow deleting the Admin role
    if role.role_name == 'Admin':
        return jsonify({'error': 'Cannot delete the Admin role'}), 400

    db.session.delete(role)
    db.session.commit()
    return '', 204

@app.route('/admin/system-settings')
@login_required
@admin_required
def admin_system_settings():
    return render_template('admin/system_settings.html')

@app.route('/admin/audit-logs')
@login_required
@admin_required
def admin_audit_logs():
    # Get security logs
    logs = db.session.query(TblSecurityLogs086)\
        .order_by(TblSecurityLogs086.log_timestamp.desc())\
        .limit(100)\
        .all()
    return render_template('admin/audit_logs.html', logs=logs)

# API Routes
@app.route('/api/reports/performance')
@login_required
@role_required('Manager')
def api_reports_performance():
    timeframe = request.args.get('timeframe', 'weekly')
    
    if timeframe == 'daily':
        start_date = datetime.now().date()
        end_date = start_date + timedelta(days=1)
    elif timeframe == 'monthly':
        today = datetime.now().date()
        start_date = today.replace(day=1)
        if today.month == 12:
            end_date = today.replace(year=today.year + 1, month=1, day=1)
        else:
            end_date = today.replace(month=today.month + 1, day=1)
    else:  # weekly
        start_date = datetime.now().date() - timedelta(days=datetime.now().weekday())
        end_date = start_date + timedelta(days=7)
    
    # Get transactions for the period
    transactions = db.session.query(TblTransactions086)\
        .filter(TblTransactions086.tst_created_on >= start_date)\
        .filter(TblTransactions086.tst_created_on < end_date)\
        .all()
    
    # Get new accounts for the period
    new_accounts = db.session.query(TblAccountDetails086)\
        .filter(TblAccountDetails086.acc_created_on >= start_date)\
        .filter(TblAccountDetails086.acc_created_on < end_date)\
        .count()
    
    # Calculate daily data points
    days = (end_date - start_date).days
    daily_transactions = []
    daily_new_accounts = []
    
    for i in range(days):
        day = start_date + timedelta(days=i)
        next_day = day + timedelta(days=1)
        
        # Count transactions for this day
        trans_count = db.session.query(TblTransactions086)\
            .filter(TblTransactions086.tst_created_on >= day)\
            .filter(TblTransactions086.tst_created_on < next_day)\
            .count()
        daily_transactions.append(trans_count)
        
        # Count new accounts for this day
        acc_count = db.session.query(TblAccountDetails086)\
            .filter(TblAccountDetails086.acc_created_on >= day)\
            .filter(TblAccountDetails086.acc_created_on < next_day)\
            .count()
        daily_new_accounts.append(acc_count)
    
    return jsonify({
        'transactions': daily_transactions,
        'new_accounts': daily_new_accounts,
        'total_transactions': len(transactions),
        'satisfaction': 4.8,  # This would come from actual ratings
        'processing_time': 3.2  # This would come from actual processing times
    })

@app.route('/api/reports/download')
@login_required
@role_required('Manager')
def api_reports_download():
    timeframe = request.args.get('timeframe', 'weekly')
    
    # Create a CSV file with report data
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Date', 'Transactions', 'New Accounts', 'Processing Time'])
    
    # Get data based on timeframe
    if timeframe == 'daily':
        start_date = datetime.now().date()
        end_date = start_date + timedelta(days=1)
    elif timeframe == 'monthly':
        start_date = datetime.now().date().replace(day=1)
        if datetime.now().month == 12:
            end_date = datetime.now().date().replace(year=datetime.now().year + 1, month=1, day=1)
        else:
            end_date = datetime.now().date().replace(month=datetime.now().month + 1, day=1)
    else:  # weekly
        start_date = datetime.now().date() - timedelta(days=datetime.now().weekday())
        end_date = start_date + timedelta(days=7)
    
    # Get transactions for each day
    current_date = start_date
    while current_date < end_date:
        next_date = current_date + timedelta(days=1)
        
        # Get transaction count
        trans_count = db.session.query(TblTransactions086)\
            .filter(TblTransactions086.tst_created_on >= current_date)\
            .filter(TblTransactions086.tst_created_on < next_date)\
            .count()
        
        # Get new accounts count
        acc_count = db.session.query(TblAccountDetails086)\
            .filter(TblAccountDetails086.acc_created_on >= current_date)\
            .filter(TblAccountDetails086.acc_created_on < next_date)\
            .count()
        
        writer.writerow([
            current_date.strftime('%Y-%m-%d'),
            trans_count,
            acc_count,
            '3.2'  # This would be actual processing time
        ])
        
        current_date = next_date
    
    # Create response
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename=report_{timeframe}_{datetime.now().strftime("%Y%m%d")}.csv'
        }
    )

# User Profile Routes
@app.route('/user/profile')
@login_required
def user_profile():
    # Get user's employee details
    employee = current_user.employee
    
    # Get user's recent transactions
    recent_transactions = db.session.query(TblTransactions086)\
        .filter(TblTransactions086.tst_created_by_user_id == current_user.usr_idpk)\
        .order_by(TblTransactions086.tst_created_on.desc())\
        .limit(5)\
        .all()
    
    # Get user's role and permissions
    role = current_user.role
    
    # Get user's last login time from session
    last_login = session.get('last_login', 'Unknown')
    
    # Get account activity statistics
    total_transactions = db.session.query(TblTransactions086)\
        .filter(TblTransactions086.tst_created_by_user_id == current_user.usr_idpk)\
        .count()
    
    return render_template('user/profile.html',
                         user=current_user,
                         employee=employee,
                         recent_transactions=recent_transactions,
                         role=role,
                         last_login=last_login,
                         total_transactions=total_transactions)

@app.route('/user/settings')
@login_required
def user_settings():
    # Get available languages and timezones
    languages = [
        ('en', 'English'),
        ('es', 'Spanish'),
        ('fr', 'French')
    ]
    
    timezones = [
        ('UTC', 'UTC'),
        ('US/Pacific', 'Pacific Time'),
        ('US/Eastern', 'Eastern Time'),
        ('Europe/London', 'London'),
        ('Asia/Tokyo', 'Tokyo')
    ]
    
    return render_template('user/settings.html',
                         user=current_user,
                         employee=current_user.employee,
                         role=current_user.role,
                         languages=languages,
                         timezones=timezones)

@app.route('/user/update_profile', methods=['POST'])
@login_required
def update_profile():
    try:
        employee = current_user.employee
        
        # Update employee details
        employee.emp_firstname = request.form.get('firstname')
        employee.emp_lastname = request.form.get('lastname')
        employee.emp_email = request.form.get('email')
        employee.emp_phone = request.form.get('phone')
        employee.emp_address = request.form.get('address')
        
        # Handle profile photo upload
        if 'photo' in request.files:
            file = request.files['photo']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                employee.emp_photo = filename
        
        # Update user preferences
        current_user.usr_language = request.form.get('language', 'en')
        current_user.usr_timezone = request.form.get('timezone', 'UTC')
        current_user.usr_theme = request.form.get('theme', 'light')
        current_user.usr_font_size = request.form.get('font_size', 'medium')
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating profile: {str(e)}', 'error')
    
    return redirect(url_for('user_profile'))

@app.route('/user/update_settings', methods=['POST'])
@login_required
def update_settings():
    try:
        # Update notification preferences
        current_user.usr_notify_security = 'notify_security' in request.form
        current_user.usr_notify_system = 'notify_system' in request.form
        current_user.usr_notify_marketing = 'notify_marketing' in request.form
        current_user.usr_notify_transactions = 'notify_transactions' in request.form
        current_user.usr_notify_login = 'notify_login' in request.form
        current_user.usr_notify_system_alerts = 'notify_system_alerts' in request.form
        
        # Update dashboard preferences
        current_user.usr_show_quick_actions = 'show_quick_actions' in request.form
        current_user.usr_show_recent = 'show_recent' in request.form
        current_user.usr_show_stats = 'show_stats' in request.form
        
        # Update integration settings
        current_user.usr_calendar_integration = 'calendar_integration' in request.form
        current_user.usr_email_integration = 'email_integration' in request.form
        current_user.usr_analytics_integration = 'analytics_integration' in request.form
        
        db.session.commit()
        flash('Settings updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating settings: {str(e)}', 'error')
    
    return redirect(url_for('user_settings'))

@app.route('/user/change_password', methods=['POST'])
@login_required
def change_password():
    try:
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Verify current password
        if not check_password_hash(current_user.usr_password, current_password):
            flash('Current password is incorrect', 'error')
            return redirect(url_for('user_settings'))
        
        # Verify new password matches confirmation
        if new_password != confirm_password:
            flash('New passwords do not match', 'error')
            return redirect(url_for('user_settings'))
        
        # Update password
        current_user.usr_password = generate_password_hash(new_password)
        db.session.commit()
        flash('Password changed successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error changing password: {str(e)}', 'error')
    
    return redirect(url_for('user_settings'))

@app.route('/user/toggle_2fa', methods=['POST'])
@login_required
def toggle_2fa():
    try:
        current_user.usr_2fa_enabled = not current_user.usr_2fa_enabled
        if current_user.usr_2fa_enabled:
            # Generate and store new 2FA secret
            current_user.usr_2fa_secret = generate_2fa_secret()
        else:
            current_user.usr_2fa_secret = None
        
        db.session.commit()
        status = 'enabled' if current_user.usr_2fa_enabled else 'disabled'
        flash(f'Two-factor authentication {status} successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error toggling 2FA: {str(e)}', 'error')
    
    return redirect(url_for('user_settings'))

def generate_2fa_secret():
    # This is a placeholder - implement proper 2FA secret generation
    import secrets
    return secrets.token_hex(16)

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

if __name__ == '__main__':
    with app.app_context():
        # Create default roles if they don't exist
        admin_role = db.session.query(TblUserRoles086).filter_by(role_name='Admin').first()
        if not admin_role:
            admin_role = TblUserRoles086(
                role_name='Admin',
                role_sht_name='ADM',
                role_created_date=datetime.utcnow()
            )
            db.session.add(admin_role)
        
        teller_role = db.session.query(TblUserRoles086).filter_by(role_name='Teller').first()
        if not teller_role:
            teller_role = TblUserRoles086(
                role_name='Teller',
                role_sht_name='TLR',
                role_created_date=datetime.utcnow()
            )
            db.session.add(teller_role)
        
        manager_role = db.session.query(TblUserRoles086).filter_by(role_name='Manager').first()
        if not manager_role:
            manager_role = TblUserRoles086(
                role_name='Manager',
                role_sht_name='MGR',
                role_created_date=datetime.utcnow()
            )
            db.session.add(manager_role)
        
        db.session.commit()
    
    app.run(debug=True)