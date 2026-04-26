from __future__ import annotations

import os
from datetime import datetime, date
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

# Base directory for the application (works on PythonAnywhere)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """User model for multi-user SaaS application."""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    shop_name = db.Column(db.String(120), nullable=False)
    address = db.Column(db.Text, nullable=False)
    tin_number = db.Column(db.String(20), nullable=False)
    logo_url = db.Column(db.String(255), nullable=True)
    is_paid = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationship with receipts
    receipts = db.relationship('Receipt', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Set password hash."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash."""
        return check_password_hash(self.password_hash, password)
    
    def is_trial_expired(self):
        """Check if user's trial has expired (3 days)."""
        if self.is_paid:
            return False
        trial_period = datetime.utcnow() - self.created_at
        return trial_period.days > 3
    
    def get_receipt_count(self):
        """Get total number of receipts for this user."""
        return Receipt.query.filter_by(user_id=self.id).count()
    
    def has_reached_limit(self):
        """Check if user has reached free tier limit (5 receipts)."""
        if self.is_paid:
            return False
        return self.get_receipt_count() >= 5
    
    def __repr__(self):
        return f'<User {self.username}>'


class Receipt(db.Model):
    """Receipt model for Philippine standard receipts."""
    __tablename__ = 'receipts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    customer_name = db.Column(db.String(120), nullable=False)
    customer_address = db.Column(db.Text, nullable=True)
    customer_tin = db.Column(db.String(20), nullable=True)
    receipt_date = db.Column(db.Date, nullable=False, default=date.today)
    receipt_number = db.Column(db.String(50), nullable=False)
    
    # Financial details
    subtotal = db.Column(db.Float, nullable=False, default=0.0)
    tax_rate = db.Column(db.Float, nullable=False, default=0.12)  # 12% VAT
    tax_amount = db.Column(db.Float, nullable=False, default=0.0)
    discount_amount = db.Column(db.Float, nullable=False, default=0.0)
    total_amount = db.Column(db.Float, nullable=False, default=0.0)
    amount_in_words = db.Column(db.Text, nullable=False)
    
    # Payment details
    payment_method = db.Column(db.String(50), nullable=True)  # Cash, Card, GCash, etc.
    payment_status = db.Column(db.String(20), default='Paid', nullable=False)
    
    # Additional notes
    notes = db.Column(db.Text, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationship with receipt items
    items = db.relationship('ReceiptItem', backref='receipt', lazy=True, cascade='all, delete-orphan')
    
    def calculate_totals(self):
        """Calculate tax and total amounts."""
        self.tax_amount = round(self.subtotal * self.tax_rate, 2)
        self.total_amount = round(self.subtotal + self.tax_amount - self.discount_amount, 2)
        self.amount_in_words = self.number_to_words(self.total_amount)
    
    @staticmethod
    def number_to_words(amount):
        """Convert number to words (Philippine Peso format)."""
        # Simple implementation for amounts up to millions
        units = ['', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine']
        teens = ['Ten', 'Eleven', 'Twelve', 'Thirteen', 'Fourteen', 'Fifteen', 'Sixteen', 
                'Seventeen', 'Eighteen', 'Nineteen']
        tens = ['', '', 'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety']
        
        if amount == 0:
            return 'Zero'
        
        words = []
        pesos = int(amount)
        centavos = int(round((amount - pesos) * 100))
        
        if pesos > 0:
            if pesos >= 1000000:
                millions = pesos // 1000000
                words.append(f"{units[millions]} Million")
                pesos %= 1000000
            
            if pesos >= 1000:
                thousands = pesos // 1000
                if thousands >= 100:
                    hundreds = thousands // 100
                    words.append(units[hundreds] + ' Hundred')
                    thousands %= 100
                
                if thousands >= 20:
                    tens_digit = thousands // 10
                    words.append(tens[tens_digit])
                    thousands %= 10
                    if thousands > 0:
                        words.append(units[thousands])
                elif thousands >= 10:
                    words.append(teens[thousands - 10])
                elif thousands > 0:
                    words.append(units[thousands])
                
                words.append('Thousand')
                pesos %= 1000
            
            if pesos >= 100:
                hundreds = pesos // 100
                words.append(units[hundreds] + ' Hundred')
                pesos %= 100
            
            if pesos >= 20:
                tens_digit = pesos // 10
                words.append(tens[tens_digit])
                pesos %= 10
                if pesos > 0:
                    words.append(units[pesos])
            elif pesos >= 10:
                words.append(teens[pesos - 10])
            elif pesos > 0:
                words.append(units[pesos])
            
            words.append('Peso' if pesos == 1 else 'Pesos')
        
        if centavos > 0:
            if centavos >= 20:
                tens_digit = centavos // 10
                words.append(tens[tens_digit])
                centavos %= 10
                if centavos > 0:
                    words.append(units[centavos])
            elif centavos >= 10:
                words.append(teens[centavos - 10])
            elif centavos > 0:
                words.append(units[centavos])
            
            words.append('Centavo' if centavos == 1 else 'Centavos')
        
        return ' '.join(words)
    
    def __repr__(self):
        return f'<Receipt {self.receipt_number}>'


class ReceiptItem(db.Model):
    """Individual items within a receipt."""
    __tablename__ = 'receipt_items'
    
    id = db.Column(db.Integer, primary_key=True)
    receipt_id = db.Column(db.Integer, db.ForeignKey('receipts.id'), nullable=False)
    item_name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    quantity = db.Column(db.Float, nullable=False, default=1.0)
    unit_price = db.Column(db.Float, nullable=False, default=0.0)
    total_price = db.Column(db.Float, nullable=False, default=0.0)
    
    def calculate_total(self):
        """Calculate total price for this item."""
        self.total_price = round(self.quantity * self.unit_price, 2)
    
    def __repr__(self):
        return f'<ReceiptItem {self.item_name}>'
