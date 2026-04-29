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

# Initialize Supabase client with proper error handling
@st.cache_resource
def init_supabase():
    try:
        SUPABASE_URL = st.secrets.get("SUPABASE_URL")
        SUPABASE_KEY = st.secrets.get("SUPABASE_KEY")
        
        # Debug: Show what we're trying to load
        st.sidebar.write("🔍 Debug Info:")
        st.sidebar.write(f"URL found: {bool(SUPABASE_URL)}")
        st.sidebar.write(f"Key found: {bool(SUPABASE_KEY)}")
        
        if not SUPABASE_URL:
            st.error("❌ Missing SUPABASE_URL in secrets")
            st.stop()
            
        if not SUPABASE_KEY:
            st.error("❌ Missing SUPABASE_KEY in secrets")
            st.stop()
            
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        st.error(f"❌ Supabase Connection Error: {str(e)}")
        st.stop()

# Check system health
def check_system_health():
    try:
        supabase = init_supabase()
        # Test connection with a simple query
        result = supabase.table('profiles').select('id').limit(1).execute()
        st.sidebar.write("✅ Database connection successful")
        return True, None
    except Exception as e:
        error_msg = f"Database connection failed: {str(e)}"
        st.sidebar.write(f"❌ {error_msg}")
        return False, error_msg

# Authentication functions
def show_auth_page():
    st.markdown("""
    <div class="main-header">
        <h1>LedgerPro-PH</h1>
        <p>Philippine Bookkeeping & Tax Compliance System</p>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["🔐 Sign In", "📝 Sign Up"])
    
    with tab1:
        with st.form("login_form"):
            email = st.text_input("Email", placeholder="your@email.com")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submitted = st.form_submit_button("Sign In", type="primary")
            
            if submitted:
                if email and password:
                    try:
                        supabase = init_supabase()
                        auth_response = supabase.auth.sign_in_with_password({
                            "email": email,
                            "password": password
                        })
                        
                        if auth_response.user:
                            st.session_state.user = auth_response.user
                            st.session_state.authenticated = True
                            st.success("✅ Welcome back!")
                            st.rerun()
                        else:
                            st.error("❌ Invalid credentials")
                    except Exception as e:
                        st.error("❌ Sign in failed. Please try again.")
                else:
                    st.error("Please fill in all fields")
    
    with tab2:
        with st.form("signup_form"):
            new_email = st.text_input("Email", placeholder="your@email.com")
            new_password = st.text_input("Password", type="password", placeholder="Create a password")
            business_name = st.text_input("Business Name", placeholder="Your Business Name")
            tax_type = st.selectbox("Tax Type", ["NON-VAT (1%)", "NON-VAT (3%)", "VAT (8% Flat)", "VAT (12%)"])
            submitted = st.form_submit_button("Create Account", type="primary")
            
            if submitted:
                if new_email and new_password and business_name:
                    try:
                        supabase = init_supabase()
                        # Create user account
                        auth_response = supabase.auth.sign_up({
                            "email": new_email,
                            "password": new_password,
                            "options": {
                                "data": {
                                    "business_name": business_name,
                                    "tax_type": tax_type
                                }
                            }
                        })
                        
                        if auth_response.user:
                            # Create profile record
                            profile_data = {
                                "id": auth_response.user.id,
                                "email": new_email,
                                "business_name": business_name,
                                "tax_type": tax_type,
                                "is_pro_status": False,
                                "created_at": datetime.now().isoformat()
                            }
                            
                            supabase.table('profiles').insert(profile_data).execute()
                            
                            st.success("✅ Account created! Please check your email to verify.")
                            st.info("After verification, you can sign in to continue.")
                        else:
                            st.error("❌ Account creation failed")
                    except Exception as e:
                        error_msg = str(e).lower()
                        if "already registered" in error_msg or "user_already_exists" in error_msg:
                            st.error("❌ This email is already registered. Try signing in instead.")
                        elif "weak_password" in error_msg:
                            st.error("❌ Password is too weak. Use at least 6 characters.")
                        elif "invalid_email" in error_msg:
                            st.error("❌ Invalid email format.")
                        elif "database" in error_msg or "connection" in error_msg:
                            st.error("❌ Database connection error. Please try again.")
                        else:
                            st.error(f"❌ Signup failed: {str(e)}")
                            st.info("💡 Try checking if the email is already registered or use a different email.")
                else:
                    st.error("Please fill in all fields")

def check_authentication():
    """Check if user is authenticated"""
    if 'authenticated' not in st.session_state or not st.session_state.authenticated:
        show_auth_page()
        return False
    return True

def get_current_user():
    """Get current authenticated user"""
    return st.session_state.get('user', None)

def handle_signout():
    """Handle user sign out"""
    if 'user' in st.session_state:
        try:
            supabase = init_supabase()
            supabase.auth.sign_out()
        except:
            pass
        finally:
            del st.session_state.user
            del st.session_state.authenticated
            st.rerun()

# Custom CSS for professional styling
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

def load_css():
    st.markdown("""
    <style>
    :root {
        --primary-color: #3b82f6;
        --secondary-color: #60a5fa;
        --accent-color: #93c5fd;
        --success-color: #10b981;
        --warning-color: #f59e0b;
        --error-color: #ef4444;
        --background-color: #0f172a;
        --card-background: #1e293b;
        --text-primary: #f1f5f9;
        --text-secondary: #94a3b8;
        --border-color: #334155;
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

    /* Dark mode for Streamlit components */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div > select,
    .stDateInput > div > div > input,
    .stTextArea > div > div > textarea {
        background-color: var(--card-background) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border-color) !important;
    }

    .stButton > button {
        background-color: var(--primary-color) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: background-color 0.2s ease-in-out !important;
    }

    .stButton > button:hover {
        background-color: var(--secondary-color) !important;
    }

    .stDataFrame {
        background-color: var(--card-background) !important;
        color: var(--text-primary) !important;
    }

    .stDataTable {
        background-color: var(--card-background) !important;
    }

    .stTable {
        background-color: var(--card-background) !important;
        color: var(--text-primary) !important;
    }

    .stMetric {
        background-color: var(--card-background) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 8px !important;
        padding: 1rem !important;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1) !important;
    }

    .stTabs [data-baseweb="tab-list"] {
        background-color: var(--card-background) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 8px !important;
    }

    .stTabs [data-baseweb="tab"] {
        color: var(--text-secondary) !important;
        background-color: transparent !important;
        border-radius: 6px !important;
    }

    .stTabs [aria-selected="true"] {
        color: var(--text-primary) !important;
        background-color: var(--primary-color) !important;
    }

    .stExpander {
        background-color: var(--card-background) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 8px !important;
    }

    .stAlert {
        background-color: var(--card-background) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 8px !important;
    }

    .stSidebar {
        background-color: var(--card-background) !important;
        border-right: 1px solid var(--border-color) !important;
    }

    .stSelectbox > div > div {
        background-color: var(--card-background) !important;
        color: var(--text-primary) !important;
    }

    .stMultiSelect > div > div {
        background-color: var(--card-background) !important;
        color: var(--text-primary) !important;
    }

    .stCheckbox > div > label {
        color: var(--text-primary) !important;
    }

    .stRadio > div > label {
        color: var(--text-primary) !important;
    }

    .stSlider > div > div > div {
        background-color: var(--primary-color) !important;
    }

    .stProgress > div > div > div > div {
        background-color: var(--primary-color) !important;
    }

    /* Plotly dark mode */
    .js-plotly-plot .plotly .modebar {
        background-color: var(--card-background) !important;
        border: 1px solid var(--border-color) !important;
    }

    .js-plotly-plot .plotly .modebar-btn {
        background-color: var(--card-background) !important;
        color: var(--text-primary) !important;
    }

    /* Form sections */
    .form-section {
        background: var(--card-background);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }

    /* Success, error, warning messages */
    .success-message {
        background-color: rgba(16, 185, 129, 0.1);
        border: 1px solid var(--success-color);
        color: var(--success-color);
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }

    .error-message {
        background-color: rgba(239, 68, 68, 0.1);
        border: 1px solid var(--error-color);
        color: var(--error-color);
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }

    .warning-message {
        background-color: rgba(245, 158, 11, 0.1);
        border: 1px solid var(--warning-color);
        color: var(--warning-color);
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
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
# Get user profile with caching
@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_user_profile(user_id):
    try:
        supabase = init_supabase()
        result = supabase.table('profiles').select('*').eq('id', user_id).single().execute()
        return result.data if result.data else None
    except:
        return None

# Get user transaction count for limit checking
@st.cache_data(ttl=60)  # Cache for 1 minute
def get_user_transaction_count(user_id):
    try:
        supabase = init_supabase()
        result = supabase.table('transactions').select('id', count='exact').eq('user_id', user_id).execute()
        return result.count or 0
    except:
        return 0

# Navigation with user profile
def show_sidebar_with_user():
    with st.sidebar:
        # User profile section
        user = get_current_user()
        profile = get_user_profile(user.id) if user else None
        
        if profile:
            st.markdown(f"""
            <div class="sidebar-nav">
                <h3>� {profile.get('business_name', 'Business')}</h3>
                <p style="color: var(--text-secondary); font-size: 0.875rem;">{profile.get('email', '')}</p>
                <p style="color: {'#10b981' if profile.get('is_pro_status') else '#f59e0b'}; font-size: 0.75rem;">
                    {'🌟 PRO User' if profile.get('is_pro_status') else '🆓 Free Plan'}
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            # Transaction counter
            transaction_count = get_user_transaction_count(user.id)
            remaining = 20 - transaction_count if not profile.get('is_pro_status') else '∞'
            
            st.markdown(f"""
            <div style="background: var(--card-background); padding: 0.75rem; border-radius: 8px; margin: 1rem 0;">
                <p style="color: var(--text-secondary); font-size: 0.75rem; margin: 0;">Transactions</p>
                <p style="color: var(--text-primary); font-size: 1rem; font-weight: bold; margin: 0;">
                    {transaction_count} / {'∞' if profile.get('is_pro_status') else '20'}
                </p>
                {'<p style="color: #ef4444; font-size: 0.75rem; margin: 0;">⚠️ Limit reached</p>' if not profile.get('is_pro_status') and transaction_count >= 20 else ''}
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
                "🏛️ Tax Compliance",
                "📄 Financial Statements",
                "� Subscription",
                "⚙️ Settings"
            ]
        )
        
        st.markdown("---")
        
        # Sign out button
        if st.button("🚪 Sign Out", use_container_width=True):
            handle_signout()
        
        return page

# License key verification
@st.cache_data(ttl=300)
def verify_license_key(license_key):
    try:
        supabase = init_supabase()
        result = supabase.table('license_keys').select('*').eq('key', license_key).eq('is_used', False).single().execute()
        return result.data if result.data else None
    except:
        return None

def activate_license_key(user_id, license_key):
    try:
        supabase = init_supabase()
        # Mark license as used
        supabase.table('license_keys').update({'is_used': True, 'used_by': user_id, 'used_at': datetime.now().isoformat()}).eq('key', license_key).execute()
        
        # Update user profile to pro status
        supabase.table('profiles').update({'is_pro_status': True, 'license_key': license_key}).eq('id', user_id).execute()
        
        return True
    except:
        return False

# Subscription page
def show_subscription_page():
    st.markdown("""
    <div class="main-header">
        <h1>🔑 Subscription</h1>
        <p>Manage your LedgerPro-PH subscription</p>
    </div>
    """, unsafe_allow_html=True)
    
    user = get_current_user()
    profile = get_user_profile(user.id) if user else None
    
    if not profile:
        st.error("Unable to load user profile")
        return
    
    # Current status
    st.markdown("### 📊 Current Status")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
        <div style="background: var(--card-background); padding: 1.5rem; border-radius: 10px; text-align: center;">
            <h3 style="color: {'#10b981' if profile.get('is_pro_status') else '#f59e0b'}; margin: 0;">
                {'🌟 PRO PLAN' if profile.get('is_pro_status') else '🆓 FREE PLAN'}
            </h3>
            <p style="color: var(--text-secondary); margin: 0.5rem 0;">
                {'Unlimited transactions' if profile.get('is_pro_status') else '20 transactions limit'}
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        transaction_count = get_user_transaction_count(user.id)
        st.markdown(f"""
        <div style="background: var(--card-background); padding: 1.5rem; border-radius: 10px; text-align: center;">
            <h3 style="color: var(--text-primary); margin: 0;">{transaction_count}</h3>
            <p style="color: var(--text-secondary); margin: 0.5rem 0;">Transactions Used</p>
            <p style="color: {'#10b981' if profile.get('is_pro_status') else '#f59e0b'}; font-size: 0.875rem;">
                {'∞ Available' if profile.get('is_pro_status') else f'{20 - transaction_count} Remaining'}
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # License key activation
    if not profile.get('is_pro_status'):
        st.markdown("---")
        st.markdown("### 🚀 Upgrade to Pro")
        
        st.markdown("""
        <div style="background: linear-gradient(135deg, var(--primary-color), var(--secondary-color)); 
                    padding: 1.5rem; border-radius: 10px; color: white; margin-bottom: 1rem;">
            <h3 style="margin: 0;">🌟 Pro Features</h3>
            <ul style="margin: 1rem 0;">
                <li>✅ Unlimited transactions</li>
                <li>✅ Advanced tax reports</li>
                <li>✅ Export to Excel/PDF</li>
                <li>✅ Priority support</li>
                <li>✅ Multi-user access</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("activate_license"):
            license_key = st.text_input("Enter License Key", placeholder="XXXX-XXXX-XXXX-XXXX", help="Purchase a license key from our Ko-fi store")
            submitted = st.form_submit_button("🔓 Activate License", type="primary")
            
            if submitted and license_key:
                with st.spinner("Verifying license key..."):
                    license_info = verify_license_key(license_key)
                    
                    if license_info:
                        success = activate_license_key(user.id, license_key)
                        if success:
                            st.success("🎉 License activated successfully! Welcome to Pro!")
                            st.balloons()
                            # Clear cache to refresh profile
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error("❌ Failed to activate license. Please try again.")
                    else:
                        st.error("❌ Invalid or already used license key")
    
    else:
        st.markdown("---")
        st.markdown("### 🌟 Pro Benefits Active")
        st.success("You're enjoying all Pro features!")
        
        if profile.get('license_key'):
            st.info(f"License Key: {profile.get('license_key')}")

# Settings page
def show_settings_page():
    st.markdown("""
    <div class="main-header">
        <h1>⚙️ Settings</h1>
        <p>Manage your account settings</p>
    </div>
    """, unsafe_allow_html=True)
    
    user = get_current_user()
    profile = get_user_profile(user.id) if user else None
    
    if not profile:
        st.error("Unable to load user profile")
        return
    
    # Profile settings
    st.markdown("### 👤 Profile Settings")
    
    with st.form("profile_settings"):
        business_name = st.text_input("Business Name", value=profile.get('business_name', ''))
        tax_type = st.selectbox("Tax Type", 
                               ["NON-VAT (1%)", "NON-VAT (3%)", "VAT (8% Flat)", "VAT (12%)"],
                               index=["NON-VAT (1%)", "NON-VAT (3%)", "VAT (8% Flat)", "VAT (12%)"].index(profile.get('tax_type', 'VAT (12%)')))
        
        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("💾 Save Changes", type="primary")
        with col2:
            if st.form_submit_button("🚪 Sign Out"):
                handle_signout()
        
        if submitted:
            try:
                supabase = init_supabase()
                supabase.table('profiles').update({
                    'business_name': business_name,
                    'tax_type': tax_type
                }).eq('id', user.id).execute()
                
                st.success("✅ Profile updated successfully!")
                st.cache_data.clear()  # Clear cache to refresh profile
                st.rerun()
            except Exception as e:
                st.error("❌ Failed to update profile")
    
    st.markdown("---")
    st.markdown("### 📊 Usage Statistics")
    
    transaction_count = get_user_transaction_count(user.id)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Transactions", transaction_count)
    with col2:
        st.metric("Account Type", "Pro" if profile.get('is_pro_status') else "Free")
    with col3:
        st.metric("Member Since", datetime.fromisoformat(profile.get('created_at', datetime.now().isoformat())).strftime('%b %Y'))

# Philippine Tax Engine
def calculate_tax_amounts(gross_amount, tax_type, platform_name=None, platform_fee=0):
    """Calculate tax amounts based on Philippine tax rules"""
    
    # Platform fee rates (typical rates)
    platform_rates = {
        'SHOPEE': 0.0585,  # 5.85% (5.4% + 0.45% payment fee)
        'LAZADA': 0.0645,   # 6.45% (6% + 0.45% payment fee)
        'TIKTOK': 0.05,     # 5% (estimated)
        'None': 0
    }
    
    # Calculate platform fee if not provided
    if platform_fee == 0 and platform_name in platform_rates:
        platform_fee = gross_amount * platform_rates[platform_name]
    
    # Net amount after platform fee
    net_amount = gross_amount - platform_fee
    
    # Tax calculations based on tax type
    if tax_type == "NON-VAT (1%)":
        vat_rate = 0
        ewt_rate = 0.01
    elif tax_type == "NON-VAT (3%)":
        vat_rate = 0
        ewt_rate = 0.03
    elif tax_type == "VAT (8% Flat)":
        vat_rate = 0.08
        ewt_rate = 0
    else:  # VAT (12%)
        vat_rate = 0.12
        ewt_rate = 0
    
    vat_amount = net_amount * vat_rate
    ewt_amount = net_amount * ewt_rate
    final_amount = net_amount + vat_amount - ewt_amount
    
    return {
        'platform_fee': platform_fee,
        'net_amount': net_amount,
        'vat_amount': vat_amount,
        'ewt_amount': ewt_amount,
        'final_amount': final_amount,
        'vat_rate': vat_rate,
        'ewt_rate': ewt_rate
    }

# Check user transaction limit
def check_transaction_limit(user_id):
    """Check if user has reached transaction limit"""
    profile = get_user_profile(user_id)
    if not profile or profile.get('is_pro_status'):
        return True, None  # Pro users have no limit
    
    transaction_count = get_user_transaction_count(user_id)
    if transaction_count >= 20:
        return False, "Transaction limit reached. Upgrade to Pro for unlimited transactions."
    
    return True, None

# Dashboard
def show_dashboard():
    st.markdown("""
    <div class="main-header">
        <h1>Dashboard</h1>
        <p>Overview of your financial performance</p>
    </div>
    """, unsafe_allow_html=True)
    
    user = get_current_user()
    profile = get_user_profile(user.id) if user else None
    
    if not profile:
        st.error("Unable to load user profile")
        return
    
    # Load user transactions with date filtering
    try:
        supabase = init_supabase()
        # Get current month data
        current_month = datetime.now().strftime('%Y-%m')
        # Use date range filter instead of LIKE on timestamp
        from dateutil.relativedelta import relativedelta
        start_date = datetime.now().replace(day=1)
        end_date = start_date + relativedelta(months=1)
        
        result = supabase.table('transactions').select('*').eq('user_id', user.id).gte('transaction_date', start_date.strftime('%Y-%m-%d')).lt('transaction_date', end_date.strftime('%Y-%m-%d')).execute()
        
        if result.data and len(result.data) > 0:
            # Create DataFrame with explicit error handling
            try:
                transactions = pd.DataFrame(result.data)
            except Exception as df_error:
                st.error(f"DataFrame creation error: {str(df_error)}")
                st.write("Debug - Raw data sample:", result.data[:2])
                raise df_error
            
            # Ensure proper data types
            if not transactions.empty:
                # Convert numeric columns
                numeric_cols = ['gross_amount', 'platform_fee', 'net_amount', 'vat_amount', 'ewt_amount', 'final_amount']
                for col in numeric_cols:
                    if col in transactions.columns:
                        transactions[col] = pd.to_numeric(transactions[col], errors='coerce').fillna(0)
                
                # Convert dates
                transactions['transaction_date'] = pd.to_datetime(transactions['transaction_date'], errors='coerce')
                
                # Key metrics with explicit error handling
                try:
                    revenue_mask = transactions['type'].isin(['cash_receipt', 'sales'])
                    expense_mask = transactions['type'].isin(['purchase', 'expense'])
                    
                    total_revenue = transactions[revenue_mask]['final_amount'].sum()
                    total_expenses = transactions[expense_mask]['final_amount'].sum()
                    net_income = total_revenue - total_expenses
                    total_tax = transactions['vat_amount'].sum() + transactions['ewt_amount'].sum()
                except Exception as metric_error:
                    st.error(f"Metrics calculation error: {str(metric_error)}")
                    st.write("Debug - Transactions types:", transactions['type'].unique() if 'type' in transactions.columns else "No type column")
                    raise metric_error
            else:
                total_revenue = total_expenses = net_income = total_tax = 0
        else:
            st.write("Debug - No transaction data found")
            total_revenue = total_expenses = net_income = total_tax = 0
            transactions = pd.DataFrame()
        
        # Display metrics (show even if no data)
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Revenue", f"₱{total_revenue:,.2f}")
        with col2:
            st.metric("Total Expenses", f"₱{total_expenses:,.2f}")
        with col3:
            st.metric("Net Income", f"₱{net_income:,.2f}")
        with col4:
            st.metric("Tax Total", f"₱{total_tax:,.2f}")
        
        # Revenue trend chart
        if not transactions.empty and len(transactions) > 0:
            revenue_transactions = transactions[transactions['type'].isin(['cash_receipt', 'sales'])]
            if len(revenue_transactions) > 0:
                daily_revenue = revenue_transactions.groupby(revenue_transactions['transaction_date'].dt.date)['final_amount'].sum().reset_index()
                
                if len(daily_revenue) > 0:
                    fig = px.line(daily_revenue, x='transaction_date', y='final_amount',
                                 title='Daily Revenue Trend',
                                 labels={'final_amount': 'Revenue (₱)', 'transaction_date': 'Date'},
                                 color_discrete_sequence=['#3b82f6'])
                    # fig = apply_dark_theme(fig)  # Commented out - function doesn't exist
                    st.plotly_chart(fig, use_container_width=True)
        
        # Recent transactions
        st.markdown("### 📋 Recent Transactions")
        if not transactions.empty and len(transactions) > 0:
            recent_transactions = transactions.sort_values('transaction_date', ascending=False).head(10)
            
            if len(recent_transactions) > 0:
                display_data = recent_transactions[['transaction_date', 'type', 'description', 'final_amount']].copy()
                display_data['transaction_date'] = display_data['transaction_date'].dt.strftime('%Y-%m-%d')
                display_data.columns = ['Date', 'Type', 'Description', 'Amount']
                st.dataframe(display_data, width="stretch", hide_index=True)
            else:
                st.info("No transactions this month. Start by adding your first transaction!")
        else:
            st.info("No transactions yet. Start by adding your first transaction!")
            
    except Exception as e:
        st.error(f"Error loading dashboard data: {str(e)}")
        st.info("Please try refreshing the page")
        
        # Additional debug info
        import traceback
        st.error("Full error details:")
        st.code(traceback.format_exc())
        
        # Try to get basic user info
        try:
            user = get_current_user()
            st.write("Current user:", user.id if user else "No user")
        except:
            st.write("Could not get user info")
    
    # Quick actions
    st.markdown("---")
    st.markdown("### 🚀 Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("➕ Add Transaction", type="primary", use_container_width=True):
            st.session_state.selected_page = "💰 Cash Receipts Journal"
            st.rerun()
    
    with col2:
        if st.button("📊 View Reports", use_container_width=True):
            st.session_state.selected_page = "🏛️ Tax Compliance"
            st.rerun()
    
    with col3:
        if st.button("🔑 Upgrade to Pro", use_container_width=True, disabled=profile.get('is_pro_status')):
            st.session_state.selected_page = "🔑 Subscription"
            st.rerun()
    
    # Cash Receipts Journal
def show_cash_receipts_journal():
    st.markdown("""
    <div class="main-header">
        <h1>Cash Receipts Journal</h1>
        <p>Record cash sales and customer payments</p>
    </div>
    """, unsafe_allow_html=True)
    
    user = get_current_user()
    profile = get_user_profile(user.id) if user else None
    
    if not profile:
        st.error("Unable to load user profile")
        return
    
    # Check transaction limit
    can_add, limit_message = check_transaction_limit(user.id)
    
    # Transaction form
    with st.expander("➕ Add Cash Receipt", expanded=can_add):
        if not can_add:
            st.warning(limit_message)
            st.markdown("---")
            st.markdown("### 🚀 Upgrade to Pro")
            st.info("Upgrade to Pro for unlimited transactions and advanced features!")
            if st.button("🔑 Upgrade Now", type="primary"):
                st.session_state.selected_page = "🔑 Subscription"
                st.rerun()
        else:
            with st.form("cash_receipt_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    customer_name = st.text_input("Customer Name*", placeholder="Enter customer name")
                    gross_amount = st.number_input("Gross Amount*", min_value=0.0, step=0.01, format="%.2f", placeholder="0.00")
                    platform_name = st.selectbox("Platform", ["None", "SHOPEE", "LAZADA", "TIKTOK"])
                    platform_fee = st.number_input("Platform Fee", min_value=0.0, step=0.01, format="%.2f", value=0.0, help="Leave 0 to auto-calculate")
                    seller_discount = st.number_input("Seller Discount", min_value=0.0, step=0.01, format="%.2f", value=0.0)
                
                with col2:
                    payment_method = st.selectbox("Payment Method*", ["Cash", "Bank Transfer", "Check", "Digital Wallet"])
                    bank_name = st.text_input("Bank Name", placeholder="Enter bank name")
                    check_number = st.text_input("Check Number", placeholder="Enter check number")
                    description = st.text_input("Description", placeholder="Payment description")
                
                # Auto-calculate tax amounts (initialize with default values)
                tax_calculations = calculate_tax_amounts(
                    gross_amount, 
                    profile.get('tax_type', 'VAT (12%)'),
                    platform_name,
                    platform_fee
                )
                
                # Display calculated amounts if gross_amount > 0
                if gross_amount > 0:
                    st.markdown("### 💰 Amount Breakdown")
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Net Amount", f"₱{tax_calculations['net_amount']:,.2f}")
                    with col2:
                        st.metric("VAT Amount", f"₱{tax_calculations['vat_amount']:,.2f}")
                    with col3:
                        st.metric("EWT Amount", f"₱{tax_calculations['ewt_amount']:,.2f}")
                    with col4:
                        st.metric("Final Amount", f"₱{tax_calculations['final_amount']:,.2f}")
                
                # Submit button
                col1, col2, col3 = st.columns(3)
                with col2:
                    if st.form_submit_button("💾 Save Cash Receipt", type="primary", use_container_width=False):
                        try:
                            # Initialize Supabase client
                            supabase = init_supabase()
                            
                            # Prepare data for insertion
                            cash_receipt_data = {
                                'user_id': user.id,
                                'transaction_date': datetime.now().isoformat(),
                                'type': 'cash_receipt',
                                'description': description or f"Payment from {customer_name}",
                                'customer_name': customer_name,
                                'gross_amount': gross_amount,
                                'platform_name': platform_name if platform_name != 'None' else None,
                                'platform_fee': tax_calculations['platform_fee'],
                                'seller_discount': seller_discount,
                                'net_amount': tax_calculations['net_amount'],
                                'vat_amount': tax_calculations['vat_amount'],
                                'ewt_amount': tax_calculations['ewt_amount'],
                                'final_amount': tax_calculations['final_amount'],
                                'payment_method': payment_method,
                                'bank_name': bank_name if bank_name else None,
                                'check_number': check_number if check_number else None,
                                'tax_type': profile.get('tax_type', 'VAT (12%)'),
                                'vat_rate': tax_calculations['vat_rate'],
                                'ewt_rate': tax_calculations['ewt_rate'],
                                'status': 'POSTED',
                                'created_at': datetime.now().isoformat()
                            }
                            
                            # Insert into Supabase
                            result = supabase.table('transactions').insert(cash_receipt_data).execute()
                            
                            if result.data:
                                st.success("✅ Cash receipt saved successfully!")
                                st.balloons()
                                # Clear cache to refresh transaction count
                                st.cache_data.clear()
                                st.rerun()
                            else:
                                st.error("❌ Failed to save cash receipt")
                                
                        except Exception as e:
                            st.error(f"❌ Error saving cash receipt: {str(e)}")
                            st.info("Please try again or contact support if the issue persists.")
    
    # Existing records table
    st.markdown("### 📋 Cash Receipts Records")
    
    # Date filter
    col1, col2 = st.columns(2)
    with col1:
        month_filter = st.selectbox("Filter by Month", 
                                   ["All", "January", "February", "March", "April", "May", "June",
                                    "July", "August", "September", "October", "November", "December"])
    with col2:
        year_filter = st.selectbox("Filter by Year", 
                                  ["All"] + list(range(2020, datetime.now().year + 1)))
    
    # Load data from Supabase with filters
    try:
        supabase = init_supabase()
        query = supabase.table('transactions').select('*').eq('user_id', user.id).eq('type', 'cash_receipt')
        
        # Apply date filters using proper date range comparisons
        if month_filter != "All":
            month_num = datetime.strptime(month_filter, "%B").month
            current_year = datetime.now().year
            start_date = datetime(current_year, month_num, 1)
            if month_num == 12:
                end_date = datetime(current_year + 1, 1, 1)
            else:
                end_date = datetime(current_year, month_num + 1, 1)
            query = query.gte('transaction_date', start_date.strftime('%Y-%m-%d')).lt('transaction_date', end_date.strftime('%Y-%m-%d'))
        
        if year_filter != "All":
            start_date = datetime(year_filter, 1, 1)
            end_date = datetime(year_filter + 1, 1, 1)
            query = query.gte('transaction_date', start_date.strftime('%Y-%m-%d')).lt('transaction_date', end_date.strftime('%Y-%m-%d'))
        
        result = query.order('created_at', desc=True).execute()
        
        if result.data:
            # Convert to DataFrame for display
            cash_receipts_data = pd.DataFrame(result.data)
            
            # Format for display
            display_data = []
            for _, record in cash_receipts_data.iterrows():
                display_data.append({
                    'Date': pd.to_datetime(record['transaction_date']).strftime('%Y-%m-%d'),
                    'Customer': record['customer_name'],
                    'Description': record['description'],
                    'Gross Amount': record['gross_amount'],
                    'VAT': record['vat_amount'],
                    'EWT': record['ewt_amount'],
                    'Final Amount': record['final_amount'],
                    'Platform': record['platform_name'] or 'None',
                    'Status': record['status']
                })
            
            display_df = pd.DataFrame(display_data)
            st.dataframe(display_df, width="stretch", hide_index=True)
            
            # Summary stats
            st.markdown("### 📊 Summary")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                total_amount = display_df['Final Amount'].sum()
                st.metric("Total Amount", f"₱{total_amount:,.2f}")
            with col2:
                avg_amount = display_df['Final Amount'].mean()
                st.metric("Average Amount", f"₱{avg_amount:,.2f}")
            with col3:
                st.metric("Total Records", len(display_df))
            
        else:
            st.info("📝 No cash receipts found. Start by adding your first transaction!")
            
    except Exception as e:
        st.error(f"❌ Error loading data: {str(e)}")
        st.info("Please try refreshing the page")

# Create database schema function
def create_database_schema():
    """Create the required database tables if they don't exist"""
    try:
        supabase = init_supabase()
        
        # Profiles table
        profiles_sql = """
        CREATE TABLE IF NOT EXISTS profiles (
            id UUID PRIMARY KEY REFERENCES auth.users(id),
            email TEXT UNIQUE NOT NULL,
            business_name TEXT NOT NULL,
            tax_type TEXT NOT NULL DEFAULT 'VAT (12%)',
            is_pro_status BOOLEAN DEFAULT FALSE,
            license_key TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """
        
        # Transactions table
        transactions_sql = """
        CREATE TABLE IF NOT EXISTS transactions (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            user_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
            transaction_date TIMESTAMP WITH TIME ZONE NOT NULL,
            type TEXT NOT NULL CHECK (type IN ('cash_receipt', 'sales', 'purchase', 'expense')),
            description TEXT,
            customer_name TEXT,
            supplier_name TEXT,
            gross_amount DECIMAL(15,2) NOT NULL,
            platform_name TEXT,
            platform_fee DECIMAL(15,2) DEFAULT 0,
            seller_discount DECIMAL(15,2) DEFAULT 0,
            net_amount DECIMAL(15,2) NOT NULL,
            vat_amount DECIMAL(15,2) DEFAULT 0,
            ewt_amount DECIMAL(15,2) DEFAULT 0,
            final_amount DECIMAL(15,2) NOT NULL,
            payment_method TEXT,
            bank_name TEXT,
            check_number TEXT,
            tax_type TEXT NOT NULL,
            vat_rate DECIMAL(5,4) DEFAULT 0,
            ewt_rate DECIMAL(5,4) DEFAULT 0,
            status TEXT DEFAULT 'POSTED' CHECK (status IN ('POSTED', 'PENDING', 'CANCELLED')),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """
        
        # License keys table
        license_keys_sql = """
        CREATE TABLE IF NOT EXISTS license_keys (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            key TEXT UNIQUE NOT NULL,
            is_used BOOLEAN DEFAULT FALSE,
            used_by UUID REFERENCES profiles(id),
            used_at TIMESTAMP WITH TIME ZONE,
            expires_at TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """
        
        # Enable RLS
        rls_sql = """
        ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
        ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;
        ALTER TABLE license_keys ENABLE ROW LEVEL SECURITY;
        
        -- Profiles RLS policies
        DROP POLICY IF EXISTS users_can_view_own_profile ON profiles;
        CREATE POLICY users_can_view_own_profile ON profiles
            FOR SELECT USING (auth.uid() = id);
            
        DROP POLICY IF EXISTS users_can_update_own_profile ON profiles;
        CREATE POLICY users_can_update_own_profile ON profiles
            FOR UPDATE USING (auth.uid() = id);
            
        -- Transactions RLS policies
        DROP POLICY IF EXISTS users_can_view_own_transactions ON transactions;
        CREATE POLICY users_can_view_own_transactions ON transactions
            FOR SELECT USING (auth.uid() = user_id);
            
        DROP POLICY IF EXISTS users_can_insert_own_transactions ON transactions;
        CREATE POLICY users_can_insert_own_transactions ON transactions
            FOR INSERT WITH CHECK (auth.uid() = user_id);
            
        DROP POLICY IF EXISTS users_can_update_own_transactions ON transactions;
        CREATE POLICY users_can_update_own_transactions ON transactions
            FOR UPDATE USING (auth.uid() = user_id);
            
        DROP POLICY IF EXISTS users_can_delete_own_transactions ON transactions;
        CREATE POLICY users_can_delete_own_transactions ON transactions
            FOR DELETE USING (auth.uid() = user_id);
        """
        
        # Execute schema creation (this would need to be run manually in Supabase SQL editor)
        return True
        
    except Exception as e:
        return False

# Main app
def main():
    # Load CSS
    load_css()
    
    # Check system health first
    is_healthy, error = check_system_health()
    if not is_healthy:
        st.error("❌ Connection Error")
        st.error(f"Details: {error}")
        st.info("Please check your Supabase configuration and try again.")
        return
    
    # Check authentication
    if not check_authentication():
        return
    
    # Get current user
    user = get_current_user()
    if not user:
        show_auth_page()
        return
    
    # Show sidebar and get selected page
    page = show_sidebar_with_user()
    
    # Route to appropriate page
    if page == "🏠 Dashboard":
        show_dashboard()
    elif page == "💰 Cash Receipts Journal":
        show_cash_receipts_journal()
    elif page == "📈 Sales Journal":
        from pages.sales_journal import show_sales_journal
        show_sales_journal()
    elif page == "🛒 Purchase Journal":
        from pages.purchase_journal import show_purchase_journal
        show_purchase_journal()
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
        from pages.chart_of_accounts import show_chart_of_accounts
        show_chart_of_accounts()
    elif page == "🏛️ Tax Compliance":
        st.markdown("### 🏛️ Tax Compliance")
        st.info("Tax Compliance module coming soon...")
    elif page == "📄 Financial Statements":
        st.markdown("### � Financial Statements")
        st.info("Financial Statements module coming soon...")
    elif page == "🔑 Subscription":
        show_subscription_page()
    elif page == "⚙️ Settings":
        show_settings_page()

if __name__ == "__main__":
    main()
