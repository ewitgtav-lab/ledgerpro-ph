import os
import uuid
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, flash, request, send_file, jsonify, session
from functools import wraps
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
import pandas as pd
import io
import json

# Try to import num2words, use fallback if not available
try:
    from num2words import num2words
    NUM2WORDS_AVAILABLE = True
except ImportError:
    NUM2WORDS_AVAILABLE = False
    def num2words(amount, lang='en'):
        # Fallback function that converts number to words
        def number_to_words(num):
            if num == 0:
                return "zero"
            
            ones = ["", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]
            teens = ["ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"]
            tens = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]
            
            def convert_less_than_thousand(n):
                if n == 0:
                    return ""
                elif n < 10:
                    return ones[n]
                elif n < 20:
                    return teens[n - 10]
                elif n < 100:
                    return tens[n // 10] + (" " + ones[n % 10] if n % 10 != 0 else "")
                else:
                    return ones[n // 100] + " hundred" + (" " + convert_less_than_thousand(n % 100) if n % 100 != 0 else "")
            
            if num < 1000:
                return convert_less_than_thousand(num)
            elif num < 1000000:
                return convert_less_than_thousand(num // 1000) + " thousand" + (" " + convert_less_than_thousand(num % 1000) if num % 1000 != 0 else "")
            elif num < 1000000000:
                return convert_less_than_thousand(num // 1000000) + " million" + (" " + convert_less_than_thousand(num % 1000000) if num % 1000000 != 0 else "")
            else:
                return str(num)
        
        return number_to_words(amount)

load_dotenv()

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()

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

class SubscriptionRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    screenshot_filename = db.Column(db.String(255), nullable=False)  # Renamed from screenshot_path
    status = db.Column(db.String(20), default='Pending')  # Pending, Approved, Rejected
    amount_paid = db.Column(db.Float, nullable=False, default=19.00)  # Amount paid by user
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    user = db.relationship('User', backref='subscription_requests')

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
    csrf.init_app(app)
    login_manager.login_view = 'login'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    @app.context_processor
    def inject_now():
        return {'now': datetime.utcnow}
    
    @app.template_filter('from_json')
    def from_json(value):
        import json
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return []
    
    @app.template_filter('currency')
    def currency_format(value):
        """Format currency with ₱ symbol and proper formatting"""
        return f"₱{value:,.2f}"
    
    def allowed_file(filename):
        ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    
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
        
        # Check for pending subscription request
        pending_request = SubscriptionRequest.query.filter_by(user_id=current_user.id, status='Pending').first()
        
        # Calculate real-time analytics (fresh calculation each time dashboard loads)
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
                             net_profit=net_profit,
                             pending_request=pending_request)
    
    @app.route('/receipts')
    @login_required
    def receipts_list():
        receipts = Receipt.query.filter_by(user_id=current_user.id).order_by(Receipt.created_at.desc()).all()
        return render_template('receipts/list.html', receipts=receipts)
    
    @app.route('/receipts/new', methods=['GET', 'POST'])
    @login_required
    def new_receipt():
        # Check if user has reached receipt limit (count database entries)
        if not current_user.is_pro:
            receipt_count = Receipt.query.filter_by(user_id=current_user.id).count()
            if receipt_count >= 15:
                flash('You have reached your free plan limit. Upgrade to Pro to create unlimited receipts.')
                return redirect(url_for('subscribe'))
        
        if request.method == 'POST':
            customer_name = request.form.get('customer_name')
            items = request.form.get('items')  # JSON string from frontend
            raw_total = request.form.get('total_amount')
            total_amount = float(raw_total) if raw_total and raw_total.strip() else 0.0
            
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
        
        # Handle items data - ensure it's always valid
        try:
            items = json.loads(receipt.items) if receipt.items else []
            # If no items, create a default "General Sales" item
            if not items:
                default_item = {
                    'name': 'General Sales',
                    'price': receipt.total_amount,
                    'quantity': 1
                }
                items = [default_item]
                # Update the receipt with the default item
                receipt.items = json.dumps(items)
                db.session.commit()
        except (json.JSONDecodeError, TypeError):
            # Create default item if JSON is invalid
            default_item = {
                'name': 'General Sales',
                'price': receipt.total_amount,
                'quantity': 1
            }
            items = [default_item]
            receipt.items = json.dumps(items)
            db.session.commit()
        
        # Calculate amount in words for professional receipt
        total_amount = receipt.total_amount
        pesos = int(total_amount)
        centavos = int(round((total_amount - pesos) * 100))
        
        # Debug logging
        import sys
        print(f"DEBUG: total_amount={total_amount}, pesos={pesos}, centavos={centavos}", file=sys.stderr)
        
        if centavos > 0:
            amount_in_words = f"{num2words(pesos, lang='en').title()} Pesos and {num2words(centavos, lang='en').title()} Centavos"
        else:
            amount_in_words = f"{num2words(pesos, lang='en').title()} Pesos"
        
        print(f"DEBUG: amount_in_words='{amount_in_words}'", file=sys.stderr)
        
        return render_template('receipts/view.html', receipt=receipt, amount_in_words=amount_in_words)
    
    @app.route('/receipts/<int:id>/pdf')
    @login_required
    def receipt_pdf(id):
        receipt = Receipt.query.filter_by(id=id, user_id=current_user.id).first_or_404()
        
        try:
            # Create Professional Philippine Business Receipt
            buffer = io.BytesIO()
            p = canvas.Canvas(buffer, pagesize=letter)
            width, height = letter
            
            # Set margins for thermal receipt width simulation
            left_margin = 50
            right_margin = width - 50
            center_x = width / 2
            
            # Header Section - Shop Name and Official Receipt
            p.setFillColor(colors.black)
            p.setFont("Helvetica-Bold", 20)
            
            # Get the raw shop_name value
            raw_shop_name = getattr(current_user, 'shop_name', None)
            
            # Debug logging (you can remove this in production)
            import sys
            print(f"DEBUG: raw_shop_name type: {type(raw_shop_name)}, value: {raw_shop_name}", file=sys.stderr)
            
            # Handle different data types
            if raw_shop_name is None:
                shop_name = 'LedgerPro PH'
            elif isinstance(raw_shop_name, (int, float)):
                # Convert numbers to string
                if raw_shop_name != 0:  # Only use non-zero numbers
                    shop_name = str(int(raw_shop_name)) if raw_shop_name == int(raw_shop_name) else str(raw_shop_name)
                else:
                    shop_name = 'LedgerPro PH'
            else:
                # Handle strings and other types
                shop_name = str(raw_shop_name).strip()
            
            # Clean up the string
            shop_name = shop_name.replace('nan', '').replace('None', '').strip()
            if not shop_name:
                shop_name = 'LedgerPro PH'
                
            # Final safety check - ensure it's a string
            if not isinstance(shop_name, str):
                shop_name = str(shop_name)
            
            # Final safety check before passing to ReportLab
            if not isinstance(shop_name, str) or not shop_name:
                shop_name = 'LedgerPro PH'
            
            # ABSOLUTE FINAL SAFETY CHECK - Force string conversion at the last possible moment
            shop_name = str(shop_name) if shop_name is not None else 'LedgerPro PH'
            if not isinstance(shop_name, str):
                shop_name = 'LedgerPro PH'
            
            # Double-check we're not passing a float or any other type
            try:
                float(shop_name)  # This will fail if it's not a number-like string
                # If we get here, it might still be a number-like string, ensure it's actually a string
                shop_name = str(shop_name)
            except:
                # It's not a number, which is good - keep it as is
                pass
            
            p.drawCentredString(str(shop_name).upper(), center_x, height - 60)
            
            p.setFont("Helvetica-Bold", 16)
            p.drawCentredString("OFFICIAL RECEIPT", center_x, height - 85)
            
            # Metadata Section - Date and Receipt Number
            p.setFont("Helvetica", 11)
            p.drawString(left_margin, height - 120, f"Date: {receipt.created_at.strftime('%B %d, %Y')}")
            p.drawString(right_margin - 150, height - 120, f"Receipt No: {receipt.receipt_number}")
            
            # Customer Information
            p.setFont("Helvetica-Bold", 12)
            p.drawString(left_margin, height - 150, "Customer:")
            p.setFont("Helvetica", 11)
            p.drawString(left_margin + 60, height - 150, str(receipt.customer_name))
            
            # Line separator
            p.setStrokeColor(colors.black)
            p.line(left_margin, height - 170, right_margin, height - 170)
            
            # Items Table Header
            y_position = height - 190
            p.setFont("Helvetica-Bold", 10)
            p.drawString(left_margin, y_position, "ITEM/DESCRIPTION")
            p.drawCentredString("QTY", center_x - 50, y_position)
            p.drawString(right_margin - 80, y_position, "AMOUNT")
            
            # Line separator under headers
            p.line(left_margin, y_position - 10, right_margin, y_position - 10)
            
            # Items List
            y_position -= 30
            p.setFont("Helvetica", 10)
            
            try:
                items = json.loads(receipt.items)
                for item in items:
                    item_name = item.get('name', 'N/A')
                    quantity = item.get('quantity', 1)
                    price = item.get('price', 0)
                    total = price * quantity
                    
                    # Handle long item names
                    if len(item_name) > 30:
                        item_name = item_name[:27] + "..."
                    
                    p.drawString(left_margin, y_position, str(item_name))
                    p.drawCentredString(str(quantity), center_x - 50, y_position)
                    p.drawString(right_margin - 80, y_position, f"₱{total:,.2f}")
                    
                    y_position -= 20
                    if y_position < height - 400:
                        break
            except:
                p.drawString(left_margin, y_position, "Error loading items")
            
            # Dotted line separator before totals
            y_position -= 10
            p.setStrokeColor(colors.black)
            p.setDash([2, 2])
            p.line(left_margin, y_position, right_margin, y_position)
            p.setDash()  # Reset to solid line
            
            # Totals Section
            y_position -= 25
            p.setFont("Helvetica-Bold", 12)
            p.drawString(right_margin - 120, y_position, f"TOTAL: ₱{receipt.total_amount:,.2f}")
            
            # Amount in Words (Crucial Part)
            y_position -= 30
            p.setFont("Helvetica-Oblique", 10)
            
            # Calculate amount in words before canvas drawing
            try:
                total_amount = receipt.total_amount
                pesos = int(total_amount)
                centavos = int(round((total_amount - pesos) * 100))
                
                if centavos > 0:
                    amount_in_words = f"{num2words(pesos, lang='en').title()} Pesos and {num2words(centavos, lang='en').title()} Centavos Only"
                else:
                    amount_in_words = f"{num2words(pesos, lang='en').title()} Pesos Only"
            except Exception as e:
                # Fallback if num2words fails
                amount_in_words = f"{receipt.total_amount:,.2f} Pesos Only"
            
            p.drawString(left_margin, y_position, str(amount_in_words))
            
            # Dotted line separator after amount in words
            y_position -= 20
            p.setStrokeColor(colors.black)
            p.setDash([2, 2])
            p.line(left_margin, y_position, right_margin, y_position)
            p.setDash()
            
            # Footer Section
            footer_y = 80
            p.setFillColor(colors.black)
            p.setFont("Helvetica", 10)
            p.drawCentredString(f"Thank you for shopping at {str(shop_name)}!", center_x, footer_y)
            
            # Watermark
            p.setFillColor(colors.lightgrey)
            p.setFont("Helvetica", 8)
            p.drawCentredString("Generated by LedgerPro PH", center_x, footer_y - 20)
            
            # Generation timestamp
            p.setFillColor(colors.grey)
            p.setFont("Helvetica", 8)
            p.drawCentredString(f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", center_x, footer_y - 35)
            p.showPage()
            p.save()
            
            buffer.seek(0)
            
            return send_file(buffer, as_attachment=True, download_name=f'Receipt_{receipt.receipt_number}.pdf', mimetype='application/pdf')
            
        except Exception as e:
            # Log error and return a simple error response
            import sys
            print(f"PDF Generation Error: {e}", file=sys.stderr)
            
            # Create a simple error PDF as fallback
            error_buffer = io.BytesIO()
            error_p = canvas.Canvas(error_buffer, pagesize=letter)
            error_p.setFont("Helvetica", 16)
            error_p.drawCentredString("Error Generating PDF", letter[0]/2, letter[1]/2)
            error_p.setFont("Helvetica", 12)
            error_p.drawCentredString(f"Error: {str(e)}", letter[0]/2, letter[1]/2 - 30)
            error_p.showPage()
            error_p.save()
            error_buffer.seek(0)
            
            return send_file(error_buffer, as_attachment=True, download_name=f'Error_Receipt_{receipt.receipt_number}.pdf', mimetype='application/pdf')
    
    @app.route('/receipts/<int:id>/delete', methods=['POST'])
    @login_required
    def delete_receipt(id):
        receipt = Receipt.query.filter_by(id=id, user_id=current_user.id).first_or_404()
        db.session.delete(receipt)
        db.session.commit()
        flash('Receipt deleted successfully!')
        return redirect(url_for('receipts_list'))
    
    @app.route('/subscribe', methods=['GET', 'POST'])
    @login_required
    def subscribe():
        if current_user.is_pro:
            flash('You are already a Pro user!')
            return redirect(url_for('dashboard'))
        
        # Check if user already has a pending request
        existing_request = SubscriptionRequest.query.filter_by(user_id=current_user.id, status='Pending').first()
        if existing_request:
            flash('You already have a pending subscription request. Please wait for verification.')
            return redirect(url_for('dashboard'))
        
        if request.method == 'POST':
            if 'screenshot' not in request.files:
                flash('Please select a payment screenshot')
                return redirect(request.url)
            
            file = request.files['screenshot']
            if file.filename == '':
                flash('Please select a payment screenshot')
                return redirect(request.url)
            
            if file and allowed_file(file.filename):
                # Generate unique filename
                filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4()}_{filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                
                # Ensure upload directory exists
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                
                # Save file
                file.save(filepath)
                
                # Create subscription request
                subscription = SubscriptionRequest(
                    user_id=current_user.id,
                    screenshot_filename=unique_filename,
                    status='Pending',
                    amount_paid=19.00
                )
                db.session.add(subscription)
                db.session.commit()
                
                flash('Payment submitted! Please wait 12-24 hours for manual verification.')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid file type. Please upload an image file.')
                return redirect(request.url)
        
        return render_template('subscribe.html')
    
    @app.route('/ledger')
    @login_required
    def ledger():
        return redirect(url_for('sales_journal'))
    
    @app.route('/ledger/sales')
    @login_required
    def sales_journal():
        sales = Transaction.query.filter_by(user_id=current_user.id, type='sale').order_by(Transaction.date.desc()).all()
        total_sales = sum(transaction.amount for transaction in sales)
        return render_template('ledger/sales.html', transactions=sales, title='Sales Journal', total_sales=total_sales)
    
    @app.route('/ledger/expenses')
    @login_required
    def expenses_journal():
        expenses = Transaction.query.filter_by(user_id=current_user.id, type='expense').order_by(Transaction.date.desc()).all()
        total_expenses = sum(transaction.amount for transaction in expenses)
        return render_template('ledger/expenses.html', transactions=expenses, title='Expense Journal', total_expenses=total_expenses)
    
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
                    
                    # Get column mappings
                    description_col = request.form.get('description_col', 'description')
                    amount_col = request.form.get('amount_col', 'amount')
                    type_col = request.form.get('type_col', 'type')
                    
                    imported_count = 0
                    for _, row in df.iterrows():
                        transaction = Transaction(
                            user_id=current_user.id,
                            description=str(row[description_col]),
                            amount=float(row[amount_col]),
                            type=str(row[type_col]).lower(),
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
                flash('Invalid file type. Please upload a CSV or Excel file.')
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
    
    # Admin routes
    @app.route('/admin/login', methods=['GET', 'POST'])
    def admin_login():
        if request.method == 'POST':
            admin_password = request.form.get('password')
            expected_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
            
            if admin_password == expected_password:
                session['is_admin'] = True
                flash('Admin login successful!')
                return redirect(url_for('admin_verify'))
            else:
                flash('Invalid admin password')
        
        return render_template('admin/login.html')
    
    def admin_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not session.get('is_admin'):
                return redirect(url_for('admin_login'))
            return f(*args, **kwargs)
        return decorated_function
    
    @app.route('/admin/verify')
    @admin_required
    def admin_verify():
        pending_requests = SubscriptionRequest.query.filter_by(status='Pending').order_by(SubscriptionRequest.created_at.desc()).all()
        return render_template('admin/verify.html', requests=pending_requests)
    
    @app.route('/admin/approve/<int:request_id>', methods=['POST'])
    @admin_required
    def approve_request(request_id):
        subscription = SubscriptionRequest.query.get_or_404(request_id)
        subscription.status = 'Approved'
        
        # Upgrade user to Pro
        user = subscription.user
        user.is_pro = True
        
        # Optionally delete screenshot to save space
        try:
            screenshot_path = os.path.join(app.config['UPLOAD_FOLDER'], subscription.screenshot_filename)
            if os.path.exists(screenshot_path):
                os.remove(screenshot_path)
        except Exception as e:
            print(f"Error deleting screenshot: {e}")
        
        db.session.commit()
        flash(f'User {user.email} has been upgraded to Pro!')
        return redirect(url_for('admin_verify'))
    
    @app.route('/admin/reject/<int:request_id>', methods=['POST'])
    @admin_required
    def reject_request(request_id):
        subscription = SubscriptionRequest.query.get_or_404(request_id)
        subscription.status = 'Rejected'
        
        db.session.commit()
        flash(f'Subscription request for {subscription.user.email} has been rejected.')
        return redirect(url_for('admin_verify'))
    
    @app.route('/admin/update-db-schema')
    def update_db_schema():
        try:
            db.create_all()
            return "Database tables updated with missing columns successfully!"
        except Exception as e:
            return f"Error: {str(e)}"

    @app.route('/admin/logout')
    def admin_logout():
        session.pop('is_admin', None)
        flash('Admin logged out successfully!')
        return redirect(url_for('dashboard'))
    
    @app.route('/uploads/<filename>')
    def uploaded_file(filename):
        return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    
    @app.after_request
    def after_request(response):
        # Add caching headers for static assets
        if request.endpoint and request.endpoint.startswith('static'):
            response.cache_control.max_age = 31536000  # 1 year
            response.cache_control.public = True
        return response
    
    @app.errorhandler(500)
    def internal_server_error(error):
        return render_template('errors/500.html', error=str(error)), 500
    
    return app

app = create_app()
