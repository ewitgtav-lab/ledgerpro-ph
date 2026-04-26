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
import io
import json

load_dotenv()

db = SQLAlchemy()
login_manager = LoginManager()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
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
    
    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
