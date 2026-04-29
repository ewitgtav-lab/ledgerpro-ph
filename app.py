import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, date
import plotly.express as px
import plotly.graph_objects as go
from supabase import create_client, Client
import os
from typing import Optional, Dict, Any
import hashlib
import hmac

# Initialize Supabase client
@st.cache_resource
def init_supabase():
    SUPABASE_URL = st.secrets.get("SUPABASE_URL", "your_supabase_url")
    SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "your_supabase_key")
    return create_client(SUPABASE_URL, SUPABASE_KEY)

# Custom CSS for professional styling
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

def load_css():
    st.markdown("""
    <style>
    :root {
        --primary-color: #1e3a8a;
        --secondary-color: #3b82f6;
        --accent-color: #60a5fa;
        --success-color: #10b981;
        --warning-color: #f59e0b;
        --error-color: #ef4444;
        --background-color: #f8fafc;
        --card-background: #ffffff;
        --text-primary: #1e293b;
        --text-secondary: #64748b;
        --border-color: #e2e8f0;
    }

    .stApp {
        background-color: var(--background-color);
    }

    .main-header {
        background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }

    .metric-card {
        background: var(--card-background);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 1.5rem;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        transition: transform 0.2s ease-in-out;
    }

    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }

    .sidebar-nav {
        background: var(--card-background);
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
    }

    .sidebar-nav .stSelectbox > div > div {
        background-color: var(--card-background);
    }

    .data-table {
        background: var(--card-background);
        border-radius: 8px;
        overflow: hidden;
    }

    .data-table .stDataFrame {
        border: 1px solid var(--border-color);
    }

    .form-section {
        background: var(--card-background);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }

    .success-message {
        background-color: #10b98120;
        border: 1px solid var(--success-color);
        color: var(--success-color);
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }

    .error-message {
        background-color: #ef444420;
        border: 1px solid var(--error-color);
        color: var(--error-color);
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }

    .warning-message {
        background-color: #f59e0b20;
        border: 1px solid var(--warning-color);
        color: var(--warning-color);
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }

    .btn-primary {
        background-color: var(--primary-color);
        color: white;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        font-weight: 600;
        transition: background-color 0.2s ease-in-out;
    }

    .btn-primary:hover {
        background-color: var(--secondary-color);
    }

    .btn-secondary {
        background-color: var(--text-secondary);
        color: white;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        font-weight: 600;
    }

    .tax-badge {
        background-color: var(--accent-color);
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.875rem;
        font-weight: 600;
    }

    .status-pending {
        background-color: #f59e0b20;
        color: var(--warning-color);
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.875rem;
        font-weight: 600;
    }

    .status-posted {
        background-color: #10b98120;
        color: var(--success-color);
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.875rem;
        font-weight: 600;
    }

    .status-cancelled {
        background-color: #ef444420;
        color: var(--error-color);
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.875rem;
        font-weight: 600;
    }

    /* Hide streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }

    ::-webkit-scrollbar-track {
        background: var(--background-color);
    }

    ::-webkit-scrollbar-thumb {
        background: var(--text-secondary);
        border-radius: 4px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: var(--text-primary);
    }
    </style>
    """, unsafe_allow_html=True)

# Authentication functions
def check_password():
    """Returns True if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if hmac.compare_digest(st.session_state["password"], st.secrets["password"]):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store password.
        else:
            st.session_state["password_correct"] = False

    if st.session_state.get("password_correct", False):
        return True

    st.text_input(
        "Password", type="password", on_change=password_entered, key="password"
    )
    if "password_correct" in st.session_state:
        st.error("😕 Password incorrect")
    return False

def show_login_page():
    st.markdown("""
    <div class="main-header">
        <h1>LedgerPro-PH</h1>
        <p>Philippine Accounting & Tax Compliance System</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style="max-width: 400px; margin: 0 auto;">
        <h3>Login</h3>
        <p>Please enter your password to access the system.</p>
    </div>
    """, unsafe_allow_html=True)

# Navigation
def show_sidebar():
    with st.sidebar:
        st.markdown("""
        <div class="sidebar-nav">
            <h3>📊 LedgerPro-PH</h3>
            <p style="color: var(--text-secondary); font-size: 0.875rem;">Philippine Accounting System</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Navigation menu
        page = st.selectbox(
            "Navigate to:",
            [
                "🏠 Dashboard",
                "💰 Cash Receipts Journal",
                "📈 Sales Journal", 
                "🛒 Purchase Journal",
                "💳 Cash Disbursement Journal",
                "📝 General Journal",
                "📋 General Ledger",
                "📊 Chart of Accounts",
                "📦 Inventory Management",
                "👥 Payroll Management",
                "🏛️ Tax Compliance",
                "🏦 Bank Reconciliation",
                "🏢 Fixed Assets",
                "📄 Financial Statements",
                "⚙️ Settings"
            ]
        )
        
        st.markdown("---")
        
        # Quick stats
        if 'company_info' in st.session_state:
            st.markdown("**Quick Stats**")
            st.metric("Active Users", "3")
            st.metric("This Month's Sales", "₱125,430")
            st.metric("Tax Due", "₱8,750")
        
        return page

# Dashboard
def show_dashboard():
    st.markdown("""
    <div class="main-header">
        <h1>Dashboard</h1>
        <p>Overview of your financial performance</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h4>Gross Sales</h4>
            <h2 style="color: var(--success-color);">₱125,430</h2>
            <p style="color: var(--text-secondary); font-size: 0.875rem;">↑ 12% from last month</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <h4>Total Expenses</h4>
            <h2 style="color: var(--warning-color);">₱45,230</h2>
            <p style="color: var(--text-secondary); font-size: 0.875rem;">↑ 5% from last month</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card">
            <h4>Net Income</h4>
            <h2 style="color: var(--primary-color);">₱80,200</h2>
            <p style="color: var(--text-secondary); font-size: 0.875rem;">↑ 18% from last month</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="metric-card">
            <h4>Tax Liabilities</h4>
            <h2 style="color: var(--error-color);">₱8,750</h2>
            <p style="color: var(--text-secondary); font-size: 0.875rem;">Due this quarter</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Revenue Trend")
        # Sample data
        revenue_data = pd.DataFrame({
            'Month': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
            'Revenue': [95000, 105000, 115000, 108000, 118000, 125430]
        })
        fig = px.line(revenue_data, x='Month', y='Revenue', 
                     title='Monthly Revenue Trend',
                     color_discrete_sequence=['#1e3a8a'])
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### Expense Breakdown")
        expense_data = pd.DataFrame({
            'Category': ['Cost of Goods', 'Salaries', 'Rent', 'Utilities', 'Others'],
            'Amount': [15000, 18000, 5000, 3230, 4000]
        })
        fig = px.pie(expense_data, values='Amount', names='Category',
                    title='Monthly Expense Breakdown',
                    color_discrete_sequence=px.colors.sequential.Blues)
        st.plotly_chart(fig, use_container_width=True)
    
    # Recent transactions
    st.markdown("### Recent Transactions")
    recent_data = pd.DataFrame({
        'Date': ['2024-01-15', '2024-01-14', '2024-01-13', '2024-01-12', '2024-01-11'],
        'Type': ['Cash Receipt', 'Sales', 'Purchase', 'Cash Disbursement', 'Sales'],
        'Description': ['Payment from Customer A', 'Sales Invoice #001', 'Office Supplies', 'Rent Payment', 'Sales Invoice #002'],
        'Amount': [15000, 25000, 3500, 5000, 18000],
        'Status': ['Posted', 'Posted', 'Posted', 'Posted', 'Pending']
    })
    
    st.dataframe(recent_data, use_container_width=True, hide_index=True)

# Cash Receipts Journal
def show_cash_receipts_journal():
    st.markdown("""
    <div class="main-header">
        <h1>Cash Receipts Journal</h1>
        <p>Record cash sales and customer payments</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Form section
    with st.expander("📝 Add New Cash Receipt", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            transaction_date = st.date_input("Transaction Date*", value=date.today())
            or_number = st.text_input("O.R. Number*", placeholder="CR-2024-001")
            customer_name = st.text_input("Customer Name*", placeholder="Enter customer name")
            customer_tin = st.text_input("Customer TIN", placeholder="000-000-000-000")
        
        with col2:
            gross_amount = st.number_input("Gross Amount*", min_value=0.0, step=0.01, format="%.2f")
            platform_name = st.selectbox("Platform", ["None", "SHOPEE", "LAZADA", "TIKTOK", "OTHER"])
            platform_fee = st.number_input("Platform Fee", min_value=0.0, step=0.01, format="%.2f", value=0.0)
            seller_discount = st.number_input("Seller Discount", min_value=0.0, step=0.01, format="%.2f", value=0.0)
        
        with col3:
            payment_method = st.selectbox("Payment Method*", ["Cash", "Bank Transfer", "Check", "Digital Wallet"])
            bank_name = st.text_input("Bank Name", placeholder="Enter bank name")
            check_number = st.text_input("Check Number", placeholder="Enter check number")
            
            # Tax calculations
            vat_registered = st.checkbox("VAT Registered", value=True)
            if vat_registered:
                vat_rate = 0.12
                ewt_rate_options = [0.0, 0.01, 0.02, 0.05]
                ewt_rate = st.selectbox("EWT Rate", options=ewt_rate_options, 
                                     format_func=lambda x: f"{x*100:.0f}%" if x > 0 else "None")
            else:
                vat_rate = 0.0
                ewt_rate = 0.0
        
        # Calculate amounts
        net_amount = gross_amount - platform_fee - seller_discount
        vat_amount = net_amount * vat_rate
        ewt_amount = net_amount * ewt_rate
        final_amount = net_amount + vat_amount - ewt_amount
        
        # Display calculated amounts
        st.markdown("### 💰 Amount Breakdown")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Net Amount", f"₱{net_amount:,.2f}")
        with col2:
            st.metric("VAT Amount", f"₱{vat_amount:,.2f}")
        with col3:
            st.metric("EWT Amount", f"₱{ewt_amount:,.2f}")
        with col4:
            st.metric("Final Amount", f"₱{final_amount:,.2f}")
        
        # Submit button
        col1, col2, col3 = st.columns(3)
        with col2:
            if st.button("💾 Save Cash Receipt", type="primary", use_container_width=True):
                st.success("✅ Cash receipt saved successfully!")
                st.balloons()
    
    # Existing records table
    st.markdown("### 📋 Cash Receipts Records")
    
    # Sample data
    cash_receipts_data = pd.DataFrame({
        'Date': ['2024-01-15', '2024-01-14', '2024-01-13', '2024-01-12'],
        'O.R. #': ['CR-2024-001', 'CR-2024-002', 'CR-2024-003', 'CR-2024-004'],
        'Customer': ['Juan Dela Cruz', 'Maria Santos', 'Pedro Reyes', 'Anna Cruz'],
        'Gross Amount': [15000.00, 25000.00, 8500.00, 12000.00],
        'VAT': [1800.00, 3000.00, 1020.00, 1440.00],
        'Net Amount': [13200.00, 22000.00, 7480.00, 10560.00],
        'Platform': ['SHOPEE', 'None', 'LAZADA', 'TIKTOK'],
        'Status': ['Posted', 'Posted', 'Posted', 'Pending']
    })
    
    # Style the dataframe
    st.dataframe(cash_receipts_data, use_container_width=True, hide_index=True)
    
    # Action buttons
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.button("📥 Export to Excel", use_container_width=True)
    with col2:
        st.button("📄 Print Report", use_container_width=True)
    with col3:
        st.button("🔄 Refresh", use_container_width=True)
    with col4:
        st.button("🗑️ Clear Filters", use_container_width=True)

# Main app
def main():
    # Load CSS
    load_css()
    
    # Check authentication
    if not check_password():
        show_login_page()
        return
    
    # Initialize session state
    if 'company_info' not in st.session_state:
        st.session_state.company_info = {
            'name': 'Sample Company',
            'tin': '000-000-000-000',
            'vat_registered': True
        }
    
    # Show sidebar and get selected page
    page = show_sidebar()
    
    # Route to appropriate page
    if page == "🏠 Dashboard":
        show_dashboard()
    elif page == "💰 Cash Receipts Journal":
        show_cash_receipts_journal()
    elif page == "📈 Sales Journal":
        st.markdown("### 📈 Sales Journal")
        st.info("Sales Journal module coming soon...")
    elif page == "🛒 Purchase Journal":
        st.markdown("### 🛒 Purchase Journal")
        st.info("Purchase Journal module coming soon...")
    elif page == "💳 Cash Disbursement Journal":
        st.markdown("### 💳 Cash Disbursement Journal")
        st.info("Cash Disbursement Journal module coming soon...")
    elif page == "📝 General Journal":
        st.markdown("### 📝 General Journal")
        st.info("General Journal module coming soon...")
    elif page == "📋 General Ledger":
        st.markdown("### 📋 General Ledger")
        st.info("General Ledger module coming soon...")
    elif page == "📊 Chart of Accounts":
        st.markdown("### 📊 Chart of Accounts")
        st.info("Chart of Accounts module coming soon...")
    elif page == "📦 Inventory Management":
        st.markdown("### 📦 Inventory Management")
        st.info("Inventory Management module coming soon...")
    elif page == "👥 Payroll Management":
        st.markdown("### 👥 Payroll Management")
        st.info("Payroll Management module coming soon...")
    elif page == "🏛️ Tax Compliance":
        st.markdown("### 🏛️ Tax Compliance")
        st.info("Tax Compliance module coming soon...")
    elif page == "🏦 Bank Reconciliation":
        st.markdown("### 🏦 Bank Reconciliation")
        st.info("Bank Reconciliation module coming soon...")
    elif page == "🏢 Fixed Assets":
        st.markdown("### 🏢 Fixed Assets")
        st.info("Fixed Assets module coming soon...")
    elif page == "📄 Financial Statements":
        st.markdown("### 📄 Financial Statements")
        st.info("Financial Statements module coming soon...")
    elif page == "⚙️ Settings":
        st.markdown("### ⚙️ Settings")
        st.info("Settings module coming soon...")

if __name__ == "__main__":
    main()
