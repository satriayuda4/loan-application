# app.py
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///loans.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your-secret-key'  # Change this to a random secret key

db = SQLAlchemy(app)

# Models
class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    unique_id = db.Column(db.String(50), unique=True)
    date_of_birth = db.Column(db.Date)
    employment_type = db.Column(db.String(20))
    pincode = db.Column(db.String(10))
    shared_mobile = db.Column(db.Boolean, default=False)
    shared_aadhar = db.Column(db.Boolean, default=False)
    shared_pan = db.Column(db.Boolean, default=False)
    shared_voter = db.Column(db.Boolean, default=False)
    shared_dl = db.Column(db.Boolean, default=False)
    shared_passport = db.Column(db.Boolean, default=False)
    customer_type = db.Column(db.String(10))  # Primary or Secondary
    loans = db.relationship('Loan', backref='customer', lazy=True)

class Loan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    amount_disbursed = db.Column(db.Float)
    asset_cost = db.Column(db.Float)
    loan_to_value = db.Column(db.Float)
    branch = db.Column(db.String(100))
    vehicle_dealer = db.Column(db.String(100))
    vehicle_manufacturer = db.Column(db.String(50))
    disbursement_date = db.Column(db.Date)
    disbursement_state = db.Column(db.String(50))
    employee_name = db.Column(db.String(100))
    emi_amount = db.Column(db.Float)
    is_secondary = db.Column(db.Boolean, default=False)

class CreditBureau(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    bureau_score = db.Column(db.Integer)
    bureau_description = db.Column(db.String(200))
    total_loans = db.Column(db.Integer)
    active_loans = db.Column(db.Integer)
    default_accounts = db.Column(db.Integer)
    principal_outstanding = db.Column(db.Float)
    total_sanctioned = db.Column(db.Float)
    total_disbursed = db.Column(db.Float)
    is_secondary = db.Column(db.Boolean, default=False)

class LoanHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    first_emi_default = db.Column(db.Boolean, default=False)
    new_loans_last_6m = db.Column(db.Integer)
    defaults_last_6m = db.Column(db.Integer)
    avg_loan_tenure = db.Column(db.Float)
    time_since_first_loan = db.Column(db.Integer)  # In months
    loan_enquiries = db.Column(db.Integer)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/loan-application', methods=['GET', 'POST'])
def loan_application():
    if request.method == 'POST':
        try:
            # Primary Customer Information
            primary_customer = Customer(
                unique_id=request.form.get('primary_unique_id'),
                date_of_birth=datetime.strptime(request.form.get('primary_dob'), '%Y-%m-%d'),
                employment_type=request.form.get('primary_employment_type'),
                pincode=request.form.get('primary_pincode'),
                shared_mobile=bool(request.form.get('primary_shared_mobile')),
                shared_aadhar=bool(request.form.get('primary_shared_aadhar')),
                shared_pan=bool(request.form.get('primary_shared_pan')),
                shared_voter=bool(request.form.get('primary_shared_voter')),
                shared_dl=bool(request.form.get('primary_shared_dl')),
                shared_passport=bool(request.form.get('primary_shared_passport')),
                customer_type='Primary'
            )
            db.session.add(primary_customer)
            db.session.flush()  # Get the ID without committing
            
            # Secondary Customer Information (if provided)
            if request.form.get('has_secondary_customer'):
                secondary_customer = Customer(
                    unique_id=request.form.get('secondary_unique_id'),
                    date_of_birth=datetime.strptime(request.form.get('secondary_dob'), '%Y-%m-%d'),
                    employment_type=request.form.get('secondary_employment_type'),
                    pincode=request.form.get('secondary_pincode'),
                    shared_mobile=bool(request.form.get('secondary_shared_mobile')),
                    shared_aadhar=bool(request.form.get('secondary_shared_aadhar')),
                    shared_pan=bool(request.form.get('secondary_shared_pan')),
                    shared_voter=bool(request.form.get('secondary_shared_voter')),
                    shared_dl=bool(request.form.get('secondary_shared_dl')),
                    shared_passport=bool(request.form.get('secondary_shared_passport')),
                    customer_type='Secondary'
                )
                db.session.add(secondary_customer)
                db.session.flush()
            
            # Loan Details
            loan = Loan(
                customer_id=primary_customer.id,
                amount_disbursed=float(request.form.get('loan_amount')),
                asset_cost=float(request.form.get('asset_cost')),
                loan_to_value=float(request.form.get('loan_amount')) / float(request.form.get('asset_cost')) * 100,
                branch=request.form.get('branch'),
                vehicle_dealer=request.form.get('vehicle_dealer'),
                vehicle_manufacturer=request.form.get('vehicle_manufacturer'),
                disbursement_date=datetime.strptime(request.form.get('disbursement_date'), '%Y-%m-%d'),
                disbursement_state=request.form.get('disbursement_state'),
                employee_name=request.form.get('employee_name'),
                emi_amount=float(request.form.get('primary_emi_amount'))
            )
            db.session.add(loan)
            
            # Credit Bureau Information - Primary
            credit_bureau = CreditBureau(
                customer_id=primary_customer.id,
                bureau_score=int(request.form.get('primary_bureau_score', 0)),
                bureau_description=request.form.get('primary_bureau_description', ''),
                total_loans=int(request.form.get('primary_total_loans', 0)),
                active_loans=int(request.form.get('primary_active_loans', 0)),
                default_accounts=int(request.form.get('primary_default_accounts', 0)),
                principal_outstanding=float(request.form.get('primary_outstanding_amount', 0)),
                total_sanctioned=float(request.form.get('primary_total_sanctioned', 0)),
                total_disbursed=float(request.form.get('primary_total_disbursed', 0)),
                is_secondary=False
            )
            db.session.add(credit_bureau)
            
            # Credit Bureau Information - Secondary (if applicable)
            if request.form.get('has_secondary_customer'):
                secondary_credit_bureau = CreditBureau(
                    customer_id=secondary_customer.id,
                    bureau_score=int(request.form.get('secondary_bureau_score', 0)),
                    bureau_description=request.form.get('secondary_bureau_description', ''),
                    total_loans=int(request.form.get('secondary_total_loans', 0)),
                    active_loans=int(request.form.get('secondary_active_loans', 0)),
                    default_accounts=int(request.form.get('secondary_default_accounts', 0)),
                    principal_outstanding=float(request.form.get('secondary_outstanding_amount', 0)),
                    total_sanctioned=float(request.form.get('secondary_total_sanctioned', 0)),
                    total_disbursed=float(request.form.get('secondary_total_disbursed', 0)),
                    is_secondary=True
                )
                db.session.add(secondary_credit_bureau)
            
            # Loan History
            loan_history = LoanHistory(
                customer_id=primary_customer.id,
                first_emi_default=bool(request.form.get('first_emi_default')),
                new_loans_last_6m=int(request.form.get('new_loans_6m', 0)),
                defaults_last_6m=int(request.form.get('defaults_6m', 0)),
                avg_loan_tenure=float(request.form.get('avg_loan_tenure', 0)),
                time_since_first_loan=int(request.form.get('time_since_first_loan', 0)),
                loan_enquiries=int(request.form.get('loan_enquiries', 0))
            )
            db.session.add(loan_history)
            
            db.session.commit()
            flash('Loan application submitted successfully!', 'success')
            return redirect(url_for('index'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error submitting application: {str(e)}', 'error')
    
    return render_template('loan_application.html')

@app.route('/loan-list')
def loan_list():
    loans = Loan.query.all()
    return render_template('loan_list.html', loans=loans)

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)