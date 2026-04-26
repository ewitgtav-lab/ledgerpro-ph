import os
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, flash, request, send_file, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
import pandas as pd
import io

load_dotenv()

db = SQLAlchemy()
login_manager = LoginManager()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(512), nullable=False)
    shop_name = db.Column(db.String(100), nullable=False)
    is_pro = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    receipts = db.relationship('Receipt', backref='user', lazy=True, cascade='all, delete-orphan')
    transactions = db.relationship('Transaction', backref='user', lazy=True, cascade='all, delete-orphan')

class Receipt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    customer_name = db.Column(db.String(100), nullable=False)
    items = db.Column(db.Text, nullable=False)  # JSON string of items
    total_amount = db.Column(db.Float, nullable=False)
    receipt_number = db.Column(db.String(20), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    transactions = db.relationship('Transaction', backref='receipt', lazy=True)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receipt_id = db.Column(db.Integer, db.ForeignKey('receipt.id'), nullable=True)
    description = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    type = db.Column(db.String(10), nullable=False)  # 'sale' or 'expense'
    category = db.Column(db.String(50), nullable=True)
    date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    database_url = os.environ.get('DATABASE_URL', 'sqlite:///app.db')
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = 'uploads'
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    @app.context_processor
    def inject_now():
        return {'now': datetime.utcnow}
    
    # Create tables
    with app.app_context():
        db.create_all()
    
    # Routes
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        return redirect(url_for('login'))
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')
            user = User.query.filter_by(email=email).first()
            
            if user and check_password_hash(user.password_hash, password):
                login_user(user)
                return redirect(url_for('dashboard'))
            flash('Invalid email or password')
        
        return render_template('auth/login.html')
    
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')
            shop_name = request.form.get('shop_name')
            
            if User.query.filter_by(email=email).first():
                flash('Email already registered')
                return render_template('auth/register.html')
            
            user = User(
                email=email,
                password_hash=generate_password_hash(password),
                shop_name=shop_name
            )
            db.session.add(user)
            db.session.commit()
            login_user(user)
            return redirect(url_for('dashboard'))
        
        return render_template('auth/register.html')
    
    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('login'))
    
    @app.route('/dashboard')
    @login_required
    def dashboard():
        receipt_count = Receipt.query.filter_by(user_id=current_user.id).count()
        usage_percentage = min((receipt_count / 15) * 100, 100) if not current_user.is_pro else 0
        
        # Calculate analytics
        sales = Transaction.query.filter_by(user_id=current_user.id, type='sale').all()
        expenses = Transaction.query.filter_by(user_id=current_user.id, type='expense').all()
        
        total_sales = sum(t.amount for t in sales)
        total_expenses = sum(t.amount for t in expenses)
        net_profit = total_sales - total_expenses
        
        return render_template('dashboard.html', 
                             receipt_count=receipt_count,
                             usage_percentage=usage_percentage,
                             total_sales=total_sales,
                             total_expenses=total_expenses,
                             net_profit=net_profit)
    
    @app.route('/receipts')
    @login_required
    def receipts_list():
        receipts = Receipt.query.filter_by(user_id=current_user.id).order_by(Receipt.created_at.desc()).all()
        return render_template('receipts/list.html', receipts=receipts)
    
    @app.route('/receipts/new', methods=['GET', 'POST'])
    @login_required
    def new_receipt():
        # Check usage limit for free users
        if not current_user.is_pro:
            receipt_count = Receipt.query.filter_by(user_id=current_user.id).count()
            if receipt_count >= 15:
                flash('You have reached your free plan limit. Upgrade to Pro to create unlimited receipts.')
                return redirect(url_for('subscribe'))
        
        if request.method == 'POST':
            customer_name = request.form.get('customer_name')
            items = request.form.get('items')  # JSON string from frontend
            total_amount = float(request.form.get('total_amount'))
            
            # Generate receipt number
            receipt_count = Receipt.query.filter_by(user_id=current_user.id).count()
            receipt_number = f"RCP-{current_user.id:04d}-{receipt_count + 1:04d}"
            
            receipt = Receipt(
                user_id=current_user.id,
                customer_name=customer_name,
                items=items,
                total_amount=total_amount,
                receipt_number=receipt_number
            )
            db.session.add(receipt)
            db.session.commit()
            
            # Create corresponding transaction
            transaction = Transaction(
                user_id=current_user.id,
                receipt_id=receipt.id,
                description=f"Receipt {receipt_number} - {customer_name}",
                amount=total_amount,
                type='sale',
                category='receipt_sales'
            )
            db.session.add(transaction)
            db.session.commit()
            
            flash('Receipt created successfully!')
            return redirect(url_for('receipts_list'))
        
        return render_template('receipts/new.html')
    
    @app.route('/receipts/<int:id>')
    @login_required
    def view_receipt(id):
        receipt = Receipt.query.filter_by(id=id, user_id=current_user.id).first_or_404()
        return render_template('receipts/view.html', receipt=receipt)
    
    @app.route('/receipts/<int:id>/pdf')
    @login_required
    def receipt_pdf(id):
        receipt = Receipt.query.filter_by(id=id, user_id=current_user.id).first_or_404()
        
        # Create PDF
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        
        # Header
        p.setFont("Helvetica-Bold", 20)
        p.drawString(50, height - 50, current_user.shop_name)
        
        p.setFont("Helvetica", 12)
        p.drawString(50, height - 80, f"Receipt #: {receipt.receipt_number}")
        p.drawString(50, height - 100, f"Date: {receipt.created_at.strftime('%Y-%m-%d %H:%M')}")
        p.drawString(50, height - 120, f"Customer: {receipt.customer_name}")
        
        # Line
        p.line(50, height - 140, width - 50, height - 140)
        
        # Items
        y_position = height - 160
        p.setFont("Helvetica-Bold", 14)
        p.drawString(50, y_position, "Items:")
        y_position -= 25
        
        p.setFont("Helvetica", 11)
        import json
        try:
            items = json.loads(receipt.items)
            for item in items:
                p.drawString(70, y_position, f"{item.get('name', 'N/A')} - ${item.get('price', 0):.2f} x {item.get('quantity', 1)}")
                y_position -= 20
                if y_position < 100:
                    break
        except:
            p.drawString(70, y_position, receipt.items)
        
        # Total
        y_position = height - 350
        p.line(50, y_position, width - 50, y_position)
        y_position -= 20
        p.setFont("Helvetica-Bold", 16)
        p.drawString(width - 200, y_position, f"Total: ${receipt.total_amount:.2f}")
        
        p.save()
        buffer.seek(0)
        
        return send_file(buffer, as_attachment=True, download_name=f'receipt_{receipt.receipt_number}.pdf', mimetype='application/pdf')
    
    @app.route('/receipts/<int:id>/delete', methods=['POST'])
    @login_required
    def delete_receipt(id):
        receipt = Receipt.query.filter_by(id=id, user_id=current_user.id).first_or_404()
        db.session.delete(receipt)
        db.session.commit()
        flash('Receipt deleted successfully!')
        return redirect(url_for('receipts_list'))
    
    @app.route('/subscribe')
    @login_required
    def subscribe():
        return render_template('subscribe.html')
    
    @app.route('/ledger')
    @login_required
    def ledger():
        return redirect(url_for('sales_journal'))
    
    @app.route('/ledger/sales')
    @login_required
    def sales_journal():
        sales = Transaction.query.filter_by(user_id=current_user.id, type='sale').order_by(Transaction.date.desc()).all()
        return render_template('ledger/sales.html', transactions=sales, title='Sales Journal')
    
    @app.route('/ledger/expenses')
    @login_required
    def expenses_journal():
        expenses = Transaction.query.filter_by(user_id=current_user.id, type='expense').order_by(Transaction.date.desc()).all()
        return render_template('ledger/expenses.html', transactions=expenses, title='Expense Journal')
    
    @app.route('/transactions/new', methods=['GET', 'POST'])
    @login_required
    def new_transaction():
        if request.method == 'POST':
            description = request.form.get('description')
            amount = float(request.form.get('amount'))
            transaction_type = request.form.get('type')
            category = request.form.get('category')
            date_str = request.form.get('date')
            
            # Parse date
            if date_str:
                date = datetime.strptime(date_str, '%Y-%m-%d')
            else:
                date = datetime.utcnow()
            
            transaction = Transaction(
                user_id=current_user.id,
                description=description,
                amount=amount,
                type=transaction_type,
                category=category,
                date=date
            )
            db.session.add(transaction)
            db.session.commit()
            
            flash('Transaction added successfully!')
            return redirect(url_for('sales_journal') if transaction_type == 'sale' else 'expenses_journal')
        
        return render_template('transactions/new.html')
    
    @app.route('/transactions/<int:id>/delete', methods=['POST'])
    @login_required
    def delete_transaction(id):
        transaction = Transaction.query.filter_by(id=id, user_id=current_user.id).first_or_404()
        db.session.delete(transaction)
        db.session.commit()
        flash('Transaction deleted successfully!')
        return redirect(url_for('sales_journal') if transaction.type == 'sale' else 'expenses_journal')
    
    @app.route('/import', methods=['GET', 'POST'])
    @login_required
    def import_data():
        if request.method == 'POST':
            if 'file' not in request.files:
                flash('No file selected')
                return redirect(request.url)
            
            file = request.files['file']
            if file.filename == '':
                flash('No file selected')
                return redirect(request.url)
            
            if file and (file.filename.endswith('.csv') or file.filename.endswith(('.xlsx', '.xls'))):
                try:
                    if file.filename.endswith('.csv'):
                        df = pd.read_csv(file)
                    else:
                        df = pd.read_excel(file)
                    
                    # Expected columns: description, amount, type, category, date
                    required_columns = ['description', 'amount', 'type']
                    if not all(col in df.columns for col in required_columns):
                        flash('File must contain columns: description, amount, type')
                        return redirect(request.url)
                    
                    imported_count = 0
                    for _, row in df.iterrows():
                        transaction = Transaction(
                            user_id=current_user.id,
                            description=str(row['description']),
                            amount=float(row['amount']),
                            type=str(row['type']).lower(),
                            category=str(row.get('category', 'imported')),
                            date=pd.to_datetime(row.get('date', datetime.utcnow()))
                        )
                        db.session.add(transaction)
                        imported_count += 1
                    
                    db.session.commit()
                    flash(f'Successfully imported {imported_count} transactions!')
                    return redirect(url_for('ledger'))
                    
                except Exception as e:
                    flash(f'Error importing file: {str(e)}')
                    return redirect(request.url)
            else:
                flash('Please upload a CSV or Excel file')
                return redirect(request.url)
        
        return render_template('import.html')
    
    @app.route('/export')
    @login_required
    def export_data():
        transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.date.desc()).all()
        
        # Create DataFrame
        data = []
        for t in transactions:
            data.append({
                'Date': t.date.strftime('%Y-%m-%d'),
                'Description': t.description,
                'Amount': t.amount,
                'Type': t.type,
                'Category': t.category or '',
                'Receipt Number': t.receipt.receipt_number if t.receipt else ''
            })
        
        df = pd.DataFrame(data)
        
        # Create Excel file
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Transactions')
        
        output.seek(0)
        return send_file(output, as_attachment=True, download_name='transactions.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    
    return app

app = create_app()
