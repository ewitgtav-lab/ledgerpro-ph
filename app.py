from __future__ import annotations

import os
from datetime import datetime, date
from typing import Any
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.pdfgen import canvas
from io import BytesIO
import csv
import pandas as pd

from models import db, User, Receipt, ReceiptItem

# Base directory for the application (works on PythonAnywhere)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
DATABASE_PATH = os.path.join(BASE_DIR, 'data.db')

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'logos'), exist_ok=True)

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DATABASE_PATH}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

    # Initialize extensions
    db.init_app(app)
    
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    login_manager.login_message = 'Please log in to access this page.'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Trial and monetization middleware
    @app.before_request
    def check_trial_limits():
        # Skip check for static files and auth routes
        if request.endpoint in ['login', 'register', 'static', 'subscribe', 'health']:
            return None
        
        # Skip check if user is not authenticated
        if not current_user.is_authenticated:
            return None
        
        # Skip check for paid users
        if current_user.is_paid:
            return None
        
        # Check if trial has expired or limit reached
        if current_user.is_trial_expired() or current_user.has_reached_limit():
            if request.endpoint != 'subscribe':
                flash('Your trial has expired or you\'ve reached the free limit. Please upgrade to continue.', 'warning')
                return redirect(url_for('subscribe'))
        
        return None

    # Create database tables
    with app.app_context():
        db.create_all()

    # Authentication routes
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            shop_name = request.form.get('shop_name')
            address = request.form.get('address')
            tin_number = request.form.get('tin_number')
            
            # Check if user already exists
            if User.query.filter_by(username=username).first():
                flash('Username already exists. Please choose another one.', 'error')
                return render_template('register.html')
            
            # Create new user
            user = User(
                username=username,
                shop_name=shop_name,
                address=address,
                tin_number=tin_number
            )
            user.set_password(password)
            
            db.session.add(user)
            db.session.commit()
            
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        
        return render_template('register.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            
            user = User.query.filter_by(username=username).first()
            
            if user and user.check_password(password):
                login_user(user)
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('dashboard'))
            else:
                flash('Invalid username or password.', 'error')
        
        return render_template('login.html')

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('You have been logged out.', 'info')
        return redirect(url_for('login'))

    @app.route('/subscribe')
    def subscribe():
        return render_template('subscribe.html')

    # Main dashboard
    @app.route('/')
    @login_required
    def dashboard():
        receipts = Receipt.query.filter_by(user_id=current_user.id).order_by(Receipt.created_at.desc()).limit(10).all()
        receipt_count = current_user.get_receipt_count()
        
        return render_template('dashboard.html', 
                             receipts=receipts, 
                             receipt_count=receipt_count,
                             is_paid=current_user.is_paid,
                             trial_expired=current_user.is_trial_expired())

    # Receipt management
    @app.route('/receipt/new', methods=['GET', 'POST'])
    @login_required
    def new_receipt():
        if request.method == 'POST':
            # Check if user can create more receipts
            if not current_user.is_paid and current_user.has_reached_limit():
                flash('You have reached your free limit of 5 receipts. Please upgrade to create more.', 'error')
                return redirect(url_for('subscribe'))
            
            # Create receipt
            receipt = Receipt(
                user_id=current_user.id,
                customer_name=request.form.get('customer_name'),
                customer_address=request.form.get('customer_address'),
                customer_tin=request.form.get('customer_tin'),
                receipt_date=datetime.strptime(request.form.get('receipt_date'), '%Y-%m-%d').date(),
                receipt_number=request.form.get('receipt_number'),
                subtotal=float(request.form.get('subtotal', 0)),
                tax_rate=float(request.form.get('tax_rate', 0.12)),
                discount_amount=float(request.form.get('discount_amount', 0)),
                payment_method=request.form.get('payment_method'),
                notes=request.form.get('notes')
            )
            
            receipt.calculate_totals()
            db.session.add(receipt)
            db.session.flush()  # Get the receipt ID
            
            # Add receipt items
            item_names = request.form.getlist('item_name')
            item_quantities = request.form.getlist('item_quantity')
            item_prices = request.form.getlist('item_price')
            
            for i, name in enumerate(item_names):
                if name.strip():
                    item = ReceiptItem(
                        receipt_id=receipt.id,
                        item_name=name,
                        quantity=float(item_quantities[i] or 1),
                        unit_price=float(item_prices[i] or 0)
                    )
                    item.calculate_total()
                    db.session.add(item)
            
            db.session.commit()
            flash('Receipt created successfully!', 'success')
            return redirect(url_for('dashboard'))
        
        return render_template('new_receipt.html')

    @app.route('/receipt/<int:receipt_id>/pdf')
    @login_required
    def download_receipt_pdf(receipt_id):
        receipt = Receipt.query.get_or_404(receipt_id)
        
        # Ensure user can only access their own receipts
        if receipt.user_id != current_user.id:
            flash('Access denied.', 'error')
            return redirect(url_for('dashboard'))
        
        # Generate PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        styles = getSampleStyleSheet()
        
        # Get user info for branding
        user = current_user
        
        # Add shop header
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1  # Center
        )
        
        story.append(Paragraph(user.shop_name, title_style))
        story.append(Paragraph(user.address, styles['Normal']))
        story.append(Paragraph(f"TIN: {user.tin_number}", styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Add logo if available and user is paid
        if user.is_paid and user.logo_url and os.path.exists(user.logo_url):
            # Note: In a real implementation, you'd add image handling here
            pass
        
        # Receipt details
        receipt_data = [
            ['Receipt Number:', receipt.receipt_number],
            ['Date:', receipt.receipt_date.strftime('%B %d, %Y')],
            ['Customer:', receipt.customer_name],
        ]
        
        if receipt.customer_address:
            receipt_data.append(['Address:', receipt.customer_address])
        if receipt.customer_tin:
            receipt_data.append(['Customer TIN:', receipt.customer_tin])
        
        receipt_table = Table(receipt_data, colWidths=[2*inch, 4*inch])
        receipt_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))
        
        story.append(receipt_table)
        story.append(Spacer(1, 20))
        
        # Items table
        items_data = [['Item', 'Qty', 'Price', 'Total']]
        for item in receipt.items:
            items_data.append([
                item.item_name,
                str(item.quantity),
                f"₱{item.unit_price:.2f}",
                f"₱{item.total_price:.2f}"
            ])
        
        items_table = Table(items_data, colWidths=[3*inch, 1*inch, 1*inch, 1*inch])
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(items_table)
        story.append(Spacer(1, 20))
        
        # Totals
        totals_data = [
            ['Subtotal:', f"₱{receipt.subtotal:.2f}"],
            ['VAT (12%):', f"₱{receipt.tax_amount:.2f}"],
            ['Discount:', f"₱{receipt.discount_amount:.2f}"],
            ['Total:', f"₱{receipt.total_amount:.2f}"]
        ]
        
        totals_table = Table(totals_data, colWidths=[4*inch, 1*inch])
        totals_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        story.append(totals_table)
        story.append(Spacer(1, 20))
        
        # Amount in words
        story.append(Paragraph(f"Amount in Words: {receipt.amount_in_words}", styles['Normal']))
        
        if receipt.notes:
            story.append(Spacer(1, 20))
            story.append(Paragraph(f"Notes: {receipt.notes}", styles['Normal']))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        
        # Return PDF
        return buffer.getvalue(), 200, {
            'Content-Type': 'application/pdf',
            'Content-Disposition': f'attachment; filename=receipt_{receipt.receipt_number}.pdf',
            'Content-Length': len(buffer.getvalue())
        }

    # Bulk import (Pro feature)
    @app.route('/import', methods=['GET', 'POST'])
    @login_required
    def bulk_import():
        if not current_user.is_paid:
            flash('Bulk import is a Pro feature. Please upgrade to access this feature.', 'warning')
            return redirect(url_for('subscribe'))
        
        if request.method == 'POST':
            if 'file' not in request.files:
                flash('No file selected.', 'error')
                return redirect(request.url)
            
            file = request.files['file']
            if file.filename == '':
                flash('No file selected.', 'error')
                return redirect(request.url)
            
            if file and file.filename.endswith(('.csv', '.xlsx')):
                try:
                    if file.filename.endswith('.csv'):
                        # Process CSV
                        stream = file.read().decode('utf-8').splitlines()
                        csv_reader = csv.DictReader(stream)
                        
                        for row in csv_reader:
                            receipt = Receipt(
                                user_id=current_user.id,
                                customer_name=row.get('customer_name', ''),
                                receipt_date=datetime.strptime(row.get('receipt_date', date.today().strftime('%Y-%m-%d')), '%Y-%m-%d').date(),
                                receipt_number=row.get('receipt_number', ''),
                                subtotal=float(row.get('subtotal', 0)),
                                tax_rate=float(row.get('tax_rate', 0.12)),
                                discount_amount=float(row.get('discount_amount', 0)),
                                payment_method=row.get('payment_method', 'Cash')
                            )
                            receipt.calculate_totals()
                            db.session.add(receipt)
                    
                    else:
                        # Process Excel
                        df = pd.read_excel(file)
                        for _, row in df.iterrows():
                            receipt = Receipt(
                                user_id=current_user.id,
                                customer_name=row.get('customer_name', ''),
                                receipt_date=pd.to_datetime(row.get('receipt_date', date.today())).date(),
                                receipt_number=str(row.get('receipt_number', '')),
                                subtotal=float(row.get('subtotal', 0)),
                                tax_rate=float(row.get('tax_rate', 0.12)),
                                discount_amount=float(row.get('discount_amount', 0)),
                                payment_method=row.get('payment_method', 'Cash')
                            )
                            receipt.calculate_totals()
                            db.session.add(receipt)
                    
                    db.session.commit()
                    flash(f'Successfully imported receipts from {file.filename}', 'success')
                    return redirect(url_for('dashboard'))
                
                except Exception as e:
                    flash(f'Error importing file: {str(e)}', 'error')
                    return redirect(request.url)
        
        return render_template('import.html')

    # Logo upload (Pro feature)
    @app.route('/upload-logo', methods=['POST'])
    @login_required
    def upload_logo():
        if not current_user.is_paid:
            return jsonify({'error': 'Logo upload is a Pro feature'}), 403
        
        if 'logo' not in request.files:
            return jsonify({'error': 'No file selected'}), 400
        
        file = request.files['logo']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if file and file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
            filename = secure_filename(f"logo_{current_user.id}_{file.filename}")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'logos', filename)
            file.save(filepath)
            
            # Update user's logo URL
            current_user.logo_url = filepath
            db.session.commit()
            
            return jsonify({'success': True, 'logo_url': filepath})
        
        return jsonify({'error': 'Invalid file type'}), 400

    @app.route('/health')
    def health():
        return jsonify({'ok': True})

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)

