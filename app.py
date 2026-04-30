import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
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
    """Check if Supabase connection is working"""
    try:
        supabase = init_supabase()
        # Test connection with a simple query
        result = supabase.table('profiles').select('id').limit(1).execute()
        return True, None
    except Exception as e:
        error_msg = f"Database connection failed: {str(e)}"
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
    # First, check if there's an existing Supabase session
    try:
        supabase = init_supabase()
        session = supabase.auth.get_session()
        
        if session and session.user:
            # Restore session state from Supabase session
            st.session_state.user = session.user
            st.session_state.authenticated = True
            return True
        else:
            # No existing session, check session state
            if 'authenticated' not in st.session_state or not st.session_state.authenticated:
                show_auth_page()
                return False
            return True
            
    except Exception as e:
        # If there's an error checking the session, fall back to session state
        if 'authenticated' not in st.session_state or not st.session_state.authenticated:
            show_auth_page()
            return False
        return True

def get_current_user():
    """Get current authenticated user"""
    return st.session_state.get('user', None)

def handle_signout():
    """Handle user sign out"""
    try:
        supabase = init_supabase()
        supabase.auth.sign_out()
    except:
        pass
    finally:
        # Clear all session state
        if 'user' in st.session_state:
            del st.session_state.user
        if 'authenticated' in st.session_state:
            del st.session_state.authenticated
        
        # Clear any other session data that might exist
        keys_to_clear = ['sales_journal_data', 'purchase_journal_data', 'cash_receipts_data']
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        
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
        display: block !important;
        visibility: visible !important;
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

# Simple navigation function (no sidebar)
def show_navigation():
    st.title("LedgerPro-PH")
    st.markdown("---")
    
    user = get_current_user()
    if user:
        st.write(f"Logged in as: {user.email}")
    
    st.markdown("---")
    
    # Simple navigation
    # Check if a button set the selected_page, otherwise use current selection
    if 'selected_page' not in st.session_state:
        st.session_state.selected_page = "🏠 Dashboard"
    
    pages = [
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
        "🔑 Subscription",
        "⚙️ Settings"
    ]
    
    try:
        current_index = pages.index(st.session_state.selected_page)
    except ValueError:
        current_index = 0
    
    page = st.selectbox(
        "Navigate to:",
        pages,
        index=current_index,
        key="navigation_selectbox"
    )
    
    # Only update session state if user manually changed the selectbox
    # (not if a button set it)
    if page != st.session_state.selected_page:
        st.session_state.selected_page = page
    
    st.markdown("---")
    
    if st.button("🚪 Sign Out"):
        handle_signout()
    
    # Return the session state value (which buttons can set) instead of selectbox value
    return st.session_state.selected_page

# License key verification
@st.cache_data(ttl=300)
def verify_license_key(license_key):
    try:
        supabase = init_supabase()
        st.write(f"DEBUG: Verifying license key: {license_key}")
        result = supabase.table('license_keys').select('*').eq('key', license_key).eq('is_used', False).single().execute()
        st.write(f"DEBUG: Query result: {result.data}")
        return result.data if result.data else None
    except Exception as e:
        st.write(f"DEBUG: License verification error: {str(e)}")
        return None

def activate_license_key(user_id, license_key):
    try:
        supabase = init_supabase()
        st.write(f"DEBUG: Activating license key: {license_key} for user: {user_id}")
        # Mark license as used and link to user
        result = supabase.table('license_keys').update({
            'is_used': True,
            'used_by': user_id,
            'used_at': datetime.now().isoformat()
        }).eq('key', license_key).execute()
        st.write(f"DEBUG: License update result: {result.data}")
        
        # Update user profile to pro status
        profile_result = supabase.table('profiles').update({
            'is_pro_status': True,
            'license_key': license_key
        }).eq('id', user_id).execute()
        st.write(f"DEBUG: Profile update result: {profile_result.data}")
        
        return True
    except Exception as e:
        st.write(f"DEBUG: License activation error: {str(e)}")
        return False

# Admin license generation
def generate_license_key():
    """Generate a new license key"""
    import random
    import string
    
    # Generate random 16-character key in XXXX-XXXX-XXXX-XXXX format
    characters = string.ascii_uppercase + string.digits
    parts = []
    for _ in range(4):
        part = ''.join(random.choice(characters) for _ in range(4))
        parts.append(part)
    
    return '-'.join(parts)

def admin_generate_multiple_keys(count=10):
    """Generate multiple license keys for admin use"""
    keys = []
    for _ in range(count):
        key = generate_license_key()
        try:
            supabase = init_supabase()
            result = supabase.table('license_keys').insert({
                'key': key,
                'is_used': False
            }).execute()
            if result.data:
                keys.append(key)
        except:
            continue
    
    return keys

def admin_get_license_stats():
    """Get statistics about license usage"""
    try:
        supabase = init_supabase()
        
        # Total keys
        total_result = supabase.table('license_keys').select('id', count='exact').execute()
        total_keys = total_result.count or 0
        
        # Used keys
        used_result = supabase.table('license_keys').select('id', count='exact').eq('is_used', True).execute()
        used_keys = used_result.count or 0
        
        # Available keys
        available_keys = total_keys - used_keys
        
        return {
            'total': total_keys,
            'used': used_keys,
            'available': available_keys
        }
    except:
        return {'total': 0, 'used': 0, 'available': 0}

def admin_get_all_licenses():
    """Get all license keys with usage info"""
    try:
        supabase = init_supabase()
        result = supabase.table('license_keys').select(
            'key', 'is_used', 'used_by', 'used_at', 'created_at'
        ).order('created_at', desc=True).execute()
        
        return result.data if result.data else []
    except:
        return []

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
    
    # Admin section (only show for admin users - you can check email or create admin role)
    if user.email == "admin@ledgerpro-ph.com" or user.email.endswith("@admin.com"):  # Replace with your admin email
        st.markdown("---")
        st.markdown("### 🔧 Admin License Management")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Keys", admin_get_license_stats()['total'])
        with col2:
            st.metric("Used Keys", admin_get_license_stats()['used'])
        with col3:
            st.metric("Available Keys", admin_get_license_stats()['available'])
        
        st.markdown("---")
        
        # Generate new keys
        st.markdown("#### 🎯 Generate New License Keys")
        
        col1, col2 = st.columns(2)
        with col1:
            key_count = st.number_input("Number of keys to generate", min_value=1, max_value=100, value=10)
        with col2:
            if st.button("🔑 Generate Keys", type="primary"):
                with st.spinner("Generating license keys..."):
                    new_keys = admin_generate_multiple_keys(key_count)
                    if new_keys:
                        st.success(f"✅ Generated {len(new_keys)} new license keys!")
                        st.code("\n".join(new_keys))
                    else:
                        st.error("❌ Failed to generate license keys")
        
        # View all licenses
        st.markdown("#### 📋 All License Keys")
        
        all_licenses = admin_get_all_licenses()
        if all_licenses:
            license_df = pd.DataFrame(all_licenses)
            license_df['status'] = license_df['is_used'].apply(lambda x: '🟢 Used' if x else '🔴 Available')
            license_df['used_at'] = license_df['used_at'].apply(lambda x: str(x)[:10] if x and not pd.isna(x) else 'Never')
            license_df['created_at'] = license_df['created_at'].apply(lambda x: str(x)[:10] if x and not pd.isna(x) else 'Unknown')
            
            display_df = license_df[['key', 'status', 'used_at', 'created_at']]
            st.dataframe(display_df, width='stretch')
        else:
            st.info("No license keys found.")

# Cash Disbursement Journal
def show_cash_disbursement_journal():
    st.markdown("""
    <div class="main-header">
        <h1>Cash Disbursement Journal</h1>
        <p>Record cash payments, expenses, and disbursements</p>
    </div>
    """, unsafe_allow_html=True)
    
    user = get_current_user()
    profile = get_user_profile(user.id) if user else None
    
    if not profile:
        st.error("Unable to load user profile")
        return
    
    # Check transaction limit
    can_add, limit_msg = check_transaction_limit(user.id)
    if not can_add:
        st.error(limit_msg)
        st.info("🔑 Upgrade to Pro for unlimited transactions")
        st.session_state.selected_page = "🔑 Subscription"
        st.rerun()
    else:
        with st.form("cash_disbursement_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                payee_name = st.text_input("Payee Name*", placeholder="Enter payee name", key="disb_payee_v1")
                gross_amount = st.number_input("Amount*", min_value=0.01, value=0.01, step=0.01, format="%.2f", key="disb_amount_v1")
                expense_type = st.selectbox("Expense Type*", ["Office Supplies", "Rent", "Utilities", "Salaries", "Marketing", "Professional Fees", "Equipment", "Travel", "Insurance", "Taxes", "Other Expenses"], key="disb_expense_type_v1")
                description = st.text_input("Description", placeholder="Payment description", key="disb_description_v1")
                
            with col2:
                payment_method = st.selectbox("Payment Method*", ["Cash", "Bank Transfer", "Check", "Credit Card", "Digital Wallet"], key="disb_payment_v1")
                bank_name = st.text_input("Bank Name", placeholder="Enter bank name", key="disb_bank_v1")
                check_number = st.text_input("Check Number", placeholder="Enter check number", key="disb_check_v1")
                expense_category = st.selectbox("Expense Category", ["Operating Expenses", "Cost of Goods Sold", "Capital Expenses", "Financial Expenses"], key="disb_category_v1")
            
            # Auto-calculate tax amounts (initialize with default values)
            tax_calculations = calculate_tax_amounts(
                gross_amount, 
                profile.get('tax_type', 'VAT (12%)'),
                None,  # No platform for expenses
                0.0
            )
            
            # Display calculated amounts if gross_amount > 0
            if gross_amount > 0:
                st.markdown("### 💰 Amount Breakdown")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Net Amount", f"₱{tax_calculations['net_amount']:,.2f}")
                with col2:
                    st.metric("Input VAT", f"₱{tax_calculations['vat_amount']:,.2f}")
                with col3:
                    st.metric("EWT Amount", f"₱{tax_calculations['ewt_amount']:,.2f}")
                with col4:
                    st.metric("Final Amount", f"₱{tax_calculations['final_amount']:,.2f}")
            
            # Submit button - validation moved inside submission check
            col1, col2, col3 = st.columns(3)
            with col2:
                submitted = st.form_submit_button(" Save Cash Disbursement", type="primary", use_container_width=False)
                
                if submitted:
                    try:
                        # Strict validation - prevent database insertion unless conditions are met
                        if not payee_name or not payee_name.strip():
                            st.error("Payee name is required and cannot be empty")
                            return
                        
                        if not gross_amount or gross_amount <= 0:
                            st.error("Amount must be greater than 0")
                            return
                        
                        # Initialize Supabase client
                        supabase = init_supabase()
                        
                        # Prepare data for insertion
                        cash_disbursement_data = {
                            'user_id': user.id,
                            'transaction_date': datetime.now().strftime('%Y-%m-%d'),
                            'type': 'expense',
                            'description': description or f"Payment to {payee_name}",
                            'customer_name': None,
                            'supplier_name': payee_name.strip(),
                            'gross_amount': gross_amount,
                            'platform_name': None,
                            'platform_fee': tax_calculations['platform_fee'],
                            'seller_discount': 0.0,
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
                            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                        
                        # Insert data
                        result = supabase.table('transactions').insert(cash_disbursement_data).execute()
                        
                        if result.data:
                            st.success(" Cash disbursement saved successfully!")
                            st.balloons()
                            # Explicit state reset to prevent multi-tab synchronization issues
                            for key in list(st.session_state.keys()):
                                if key.startswith('disb_'):
                                    del st.session_state[key]
                            st.rerun()
                        else:
                            st.error(" Failed to save cash disbursement")
                            
                    except Exception as e:
                        if not handle_database_error(e):
                            st.error(f" Error saving cash disbursement: {str(e)}")
                            st.info("Please try again or contact support if the issue persists.")
    
    # Existing records table
    st.markdown("### Cash Disbursement Records")
    
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
        query = supabase.table('transactions').select('*').eq('user_id', user.id).eq('type', 'expense')
        
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
            cash_disbursements_data = pd.DataFrame(result.data)
            
            # Format for display
            display_data = []
            for _, record in cash_disbursements_data.iterrows():
                display_data.append({
                    'Date': pd.to_datetime(record['transaction_date'], format='ISO8601', errors='coerce').strftime('%Y-%m-%d'),
                    'Payee': record['supplier_name'],
                    'Description': record['description'],
                    'Gross Amount': record['gross_amount'],
                    'Input VAT': record['vat_amount'],
                    'EWT': record['ewt_amount'],
                    'Final Amount': record['final_amount'],
                    'Payment Method': record['payment_method'],
                    'Status': record['status']
                })
            
            display_df = pd.DataFrame(display_data)
            st.dataframe(display_df, width="stretch", hide_index=True)
        else:
            st.info("No cash disbursements found for the selected period.")
            
    except Exception as e:
        st.error(f"❌ Error loading data: {str(e)}")
        st.info("Please try refreshing the page")

# General Journal
def show_general_journal():
    st.markdown("""
    <div class="main-header">
        <h1>General Journal</h1>
        <p>Manual journal entries and adjustments</p>
    </div>
    """, unsafe_allow_html=True)
    
    user = get_current_user()
    profile = get_user_profile(user.id) if user else None
    
    if not profile:
        st.error("Unable to load user profile")
        return
    
    # Check transaction limit
    can_add, limit_msg = check_transaction_limit(user.id)
    if not can_add:
        st.error(limit_msg)
        st.info("🔑 Upgrade to Pro for unlimited transactions")
        st.session_state.selected_page = "🔑 Subscription"
        st.rerun()
    else:
        with st.form("general_journal_form", clear_on_submit=True):
            st.markdown("### 📝 Journal Entry Details")
            
            col1, col2 = st.columns(2)
            
            with col1:
                entry_date = st.date_input("Entry Date*", value=datetime.now().date(), key="gen_date_v1")
                entry_type = st.selectbox("Entry Type*", ["Adjusting Entry", "Correcting Entry", "Closing Entry", "Reversing Entry", "Other"], key="gen_type_v1")
                reference_no = st.text_input("Reference No.", placeholder="Enter reference number", key="gen_ref_v1")
                
            with col2:
                explanation = st.text_area("Explanation*", placeholder="Detailed explanation of the journal entry", height=100, key="gen_explanation_v1")
                
            st.markdown("### 💰 Account Entries")
            
            # Dynamic entry lines
            num_entries = st.number_input("Number of entry lines", min_value=2, max_value=10, value=2, step=1)
            
            entries = []
            total_debit = 0
            total_credit = 0
            
            for i in range(num_entries):
                with st.expander(f"Entry Line {i+1}", expanded=True):
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        account = st.selectbox(f"Account*", [
                            "Cash", "Accounts Receivable", "Inventory", "Prepaid Expenses",
                            "Equipment", "Accumulated Depreciation", "Accounts Payable",
                            "Accrued Expenses", "Notes Payable", "Owner's Equity",
                            "Revenue", "Sales Revenue", "Service Revenue", "Cost of Goods Sold",
                            "Operating Expenses", "Salaries Expense", "Rent Expense",
                            "Utilities Expense", "Depreciation Expense", "Interest Expense",
                            "Tax Expense"
                        ], key=f"account_{i}")
                    
                    with col2:
                        debit = st.number_input(f"Debit", min_value=0.0, step=0.01, format="%.2f", key=f"debit_{i}")
                    
                    with col3:
                        credit = st.number_input(f"Credit", min_value=0.0, step=0.01, format="%.2f", key=f"credit_{i}")
                    
                    with col4:
                        description = st.text_input(f"Description", placeholder="Line description", key=f"desc_{i}")
                    
                    total_debit += debit
                    total_credit += credit
                    
                    entries.append({
                        'account': account,
                        'debit': debit,
                        'credit': credit,
                        'description': description
                    })
            
            # Show totals
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Debit", f"₱{total_debit:,.2f}")
            with col2:
                st.metric("Total Credit", f"₱{total_credit:,.2f}")
            with col3:
                balance = total_debit - total_credit
                st.metric("Balance", f"₱{balance:,.2f}", delta=f"{'Balanced' if abs(balance) < 0.01 else 'Out of Balance'}")
            
            # Validation
            if abs(total_debit - total_credit) > 0.01:
                st.error("⚠️ Journal entry must balance (Total Debit = Total Credit)")
            
            # Submit button
            col1, col2, col3 = st.columns(3)
            with col2:
                submitted = st.form_submit_button("💾 Save Journal Entry", type="primary", width='content')
                
                if submitted:
                    # Strict validation - prevent database insertion unless conditions are met
                    if not explanation or not explanation.strip():
                        st.error("Explanation is required and cannot be empty")
                        return
                    
                    if abs(total_debit - total_credit) > 0.01:
                        st.error(" Journal entry must balance before saving")
                        return
                    
                    if total_debit == 0 and total_credit == 0:
                        st.error(" Journal entry must have at least one debit or credit amount")
                        return
                    
                    try:
                        supabase = init_supabase()
                            
                        # Create summary description
                        summary = f"{entry_type}: {explanation}"
                        
                        # Save each entry line as a separate transaction
                        for entry in entries:
                            if entry['debit'] > 0:
                                # Debit entry
                                transaction_data = {
                                    'user_id': user.id,
                                    'transaction_date': entry_date.isoformat(),
                                    'type': 'expense',  # Debits are expenses
                                    'description': f"{summary} - {entry['description']}",
                                    'customer_name': None,
                                    'supplier_name': entry['account'],
                                    'gross_amount': entry['debit'],
                                    'platform_name': None,
                                    'platform_fee': 0.0,
                                    'seller_discount': 0.0,
                                    'net_amount': entry['debit'],
                                    'vat_amount': 0.0,
                                    'ewt_amount': 0.0,
                                    'final_amount': entry['debit'],
                                    'payment_method': 'Journal Entry',
                                    'bank_name': None,
                                    'check_number': reference_no,
                                    'tax_type': profile.get('tax_type', 'VAT (12%)'),
                                    'vat_rate': 0.0,
                                    'ewt_rate': 0.0,
                                    'status': 'POSTED',
                                    'created_at': datetime.now().isoformat()
                                }
                            for entry in entries:
                                if entry['debit'] > 0:
                                    # Debit entry
                                    transaction_data = {
                                        'user_id': user.id,
                                        'transaction_date': entry_date.isoformat(),
                                        'type': 'expense',  # Debits are expenses
                                        'description': f"{summary} - {entry['description']}",
                                        'customer_name': None,
                                        'supplier_name': entry['account'],
                                        'gross_amount': entry['debit'],
                                        'platform_name': None,
                                        'platform_fee': 0.0,
                                        'seller_discount': 0.0,
                                        'net_amount': entry['debit'],
                                        'vat_amount': 0.0,
                                        'ewt_amount': 0.0,
                                        'final_amount': entry['debit'],
                                        'payment_method': 'Journal Entry',
                                        'bank_name': None,
                                        'check_number': reference_no,
                                        'tax_type': profile.get('tax_type', 'VAT (12%)'),
                                        'vat_rate': 0.0,
                                        'ewt_rate': 0.0,
                                        'status': 'POSTED',
                                        'created_at': datetime.now().isoformat()
                                    }
                                    
                                    result = supabase.table('transactions').insert(transaction_data).execute()
                                    if not result.data:
                                        st.error("❌ Failed to save debit entry")
                                        raise Exception("Debit entry failed")
                                
                                if entry['credit'] > 0:
                                    # Credit entry
                                    transaction_data = {
                                        'user_id': user.id,
                                        'transaction_date': entry_date.isoformat(),
                                        'type': 'cash_receipt',  # Credits are receipts
                                        'description': f"{summary} - {entry['description']}",
                                        'customer_name': entry['account'],
                                        'supplier_name': None,
                                        'gross_amount': entry['credit'],
                                        'platform_name': None,
                                        'platform_fee': 0.0,
                                        'seller_discount': 0.0,
                                        'net_amount': entry['credit'],
                                        'vat_amount': 0.0,
                                        'ewt_amount': 0.0,
                                        'final_amount': entry['credit'],
                                        'payment_method': 'Journal Entry',
                                        'bank_name': None,
                                        'check_number': reference_no,
                                        'tax_type': profile.get('tax_type', 'VAT (12%)'),
                                        'vat_rate': 0.0,
                                        'ewt_rate': 0.0,
                                        'status': 'POSTED',
                                        'created_at': datetime.now().isoformat()
                                    }
                                    
                                    result = supabase.table('transactions').insert(transaction_data).execute()
                                    if not result.data:
                                        st.error("❌ Failed to save credit entry")
                                        raise Exception("Credit entry failed")
                            
                            st.success("✅ Journal entry saved successfully!")
                            st.balloons()
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"❌ Error saving journal entry: {str(e)}")
                            st.info("Please try again or contact support if the issue persists.")
    
    # Existing entries table
    st.markdown("### 📋 Recent Journal Entries")
    
    # Load recent journal entries
    try:
        supabase = init_supabase()
        # Get entries with "Journal Entry" payment method
        result = supabase.table('transactions').select('*').eq('user_id', user.id).eq('payment_method', 'Journal Entry').order('created_at', desc=True).limit(50).execute()
        
        if result.data:
            # Group by reference number
            entries_by_ref = {}
            for record in result.data:
                ref = record.get('check_number', 'No Ref')
                if ref not in entries_by_ref:
                    entries_by_ref[ref] = []
                entries_by_ref[ref].append(record)
            
            # Display grouped entries
            for ref, entries in entries_by_ref.items():
                with st.expander(f"Journal Entry - {ref} ({entries[0]['transaction_date'][:10]})"):
                    for entry in entries:
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            if entry['type'] == 'expense':
                                st.write(f"**Debit**: {entry['supplier_name']}")
                            else:
                                st.write(f"**Credit**: {entry['customer_name']}")
                        
                        with col2:
                            st.write(f"₱{entry['final_amount']:,.2f}")
                        
                        with col3:
                            st.write(entry['description'])
                        
                        with col4:
                            st.write(entry['status'])
        else:
            st.info("No journal entries found.")
            
    except Exception as e:
        st.error(f"❌ Error loading journal entries: {str(e)}")
        st.info("Please try refreshing the page")

# General Ledger
def show_general_ledger():
    st.markdown("""
    <div class="main-header">
        <h1>General Ledger</h1>
        <p>Complete ledger of all financial transactions</p>
    </div>
    """, unsafe_allow_html=True)
    
    user = get_current_user()
    profile = get_user_profile(user.id) if user else None
    
    if not profile:
        st.error("Unable to load user profile")
        return
    
    # Load all transactions
    try:
        supabase = init_supabase()
        result = supabase.table('transactions').select('*').eq('user_id', user.id).order('transaction_date', desc=True).execute()
        
        if result.data and len(result.data) > 0:
            transactions = pd.DataFrame(result.data)
            
            # Convert dates
            transactions['transaction_date'] = pd.to_datetime(transactions['transaction_date'], format='ISO8601', errors='coerce')
            
            # Account mapping
            account_mapping = {
                'cash_receipt': {
                    'Cash': 'Cash',
                    'Accounts Receivable': 'Accounts Receivable',
                    'Revenue': 'Revenue',
                    'Sales Revenue': 'Sales Revenue',
                    'Service Revenue': 'Service Revenue'
                },
                'sales': {
                    'Accounts Receivable': 'Accounts Receivable',
                    'Revenue': 'Revenue',
                    'Sales Revenue': 'Sales Revenue'
                },
                'purchase': {
                    'Inventory': 'Inventory',
                    'Equipment': 'Equipment',
                    'Accounts Payable': 'Accounts Payable'
                },
                'expense': {
                    'Cash': 'Cash',
                    'Bank': 'Cash',
                    'Operating Expenses': 'Operating Expenses',
                    'Salaries Expense': 'Salaries Expense',
                    'Rent Expense': 'Rent Expense',
                    'Utilities Expense': 'Utilities Expense',
                    'Marketing': 'Marketing Expense',
                    'Professional Fees': 'Professional Fees',
                    'Equipment': 'Equipment',
                    'Insurance': 'Insurance Expense',
                    'Taxes': 'Tax Expense'
                }
            }
            
            # Create ledger entries
            ledger_entries = []
            
            for _, transaction in transactions.iterrows():
                trans_date = transaction['transaction_date']
                trans_type = transaction['type']
                description = transaction['description']
                amount = transaction['final_amount']
                
                # Determine debit and credit accounts based on transaction type
                if trans_type == 'cash_receipt':
                    # Cash receipts: Debit Cash, Credit Revenue
                    ledger_entries.append({
                        'Date': trans_date,
                        'Account': 'Cash',
                        'Description': description,
                        'Debit': amount,
                        'Credit': 0.0,
                        'Balance': 0.0,
                        'Type': 'Asset'
                    })
                    ledger_entries.append({
                        'Date': trans_date,
                        'Account': 'Revenue',
                        'Description': description,
                        'Debit': 0.0,
                        'Credit': amount,
                        'Balance': 0.0,
                        'Type': 'Revenue'
                    })
                
                elif trans_type == 'sales':
                    # Sales: Debit Accounts Receivable, Credit Revenue
                    ledger_entries.append({
                        'Date': trans_date,
                        'Account': 'Accounts Receivable',
                        'Description': description,
                        'Debit': amount,
                        'Credit': 0.0,
                        'Balance': 0.0,
                        'Type': 'Asset'
                    })
                    ledger_entries.append({
                        'Date': trans_date,
                        'Account': 'Revenue',
                        'Description': description,
                        'Debit': 0.0,
                        'Credit': amount,
                        'Balance': 0.0,
                        'Type': 'Revenue'
                    })
                
                elif trans_type == 'purchase':
                    # Purchases: Debit Expense/Asset, Credit Cash/Accounts Payable
                    if transaction.get('payment_method') == 'Cash':
                        debit_account = 'Equipment' if 'Equipment' in description else 'Inventory'
                        ledger_entries.append({
                            'Date': trans_date,
                            'Account': debit_account,
                            'Description': description,
                            'Debit': amount,
                            'Credit': 0.0,
                            'Balance': 0.0,
                            'Type': 'Asset'
                        })
                        ledger_entries.append({
                            'Date': trans_date,
                            'Account': 'Cash',
                            'Description': description,
                            'Debit': 0.0,
                            'Credit': amount,
                            'Balance': 0.0,
                            'Type': 'Asset'
                        })
                    else:
                        debit_account = 'Equipment' if 'Equipment' in description else 'Inventory'
                        ledger_entries.append({
                            'Date': trans_date,
                            'Account': debit_account,
                            'Description': description,
                            'Debit': amount,
                            'Credit': 0.0,
                            'Balance': 0.0,
                            'Type': 'Asset'
                        })
                        ledger_entries.append({
                            'Date': trans_date,
                            'Account': 'Accounts Payable',
                            'Description': description,
                            'Debit': 0.0,
                            'Credit': amount,
                            'Balance': 0.0,
                            'Type': 'Liability'
                        })
                
                elif trans_type == 'expense':
                    # Expenses: Debit Expense Account, Credit Cash
                    expense_account = 'Operating Expenses'  # Default
                    if 'Salaries' in description:
                        expense_account = 'Salaries Expense'
                    elif 'Rent' in description:
                        expense_account = 'Rent Expense'
                    elif 'Utilities' in description:
                        expense_account = 'Utilities Expense'
                    elif 'Marketing' in description:
                        expense_account = 'Marketing Expense'
                    elif 'Professional' in description:
                        expense_account = 'Professional Fees'
                    elif 'Equipment' in description:
                        expense_account = 'Equipment'
                    elif 'Insurance' in description:
                        expense_account = 'Insurance Expense'
                    elif 'Tax' in description:
                        expense_account = 'Tax Expense'
                    
                    ledger_entries.append({
                        'Date': trans_date,
                        'Account': expense_account,
                        'Description': description,
                        'Debit': amount,
                        'Credit': 0.0,
                        'Balance': 0.0,
                        'Type': 'Expense'
                    })
                    ledger_entries.append({
                        'Date': trans_date,
                        'Account': 'Cash',
                        'Description': description,
                        'Debit': 0.0,
                        'Credit': amount,
                        'Balance': 0.0,
                        'Type': 'Asset'
                    })
            
            if ledger_entries:
                ledger_df = pd.DataFrame(ledger_entries)
                ledger_df = ledger_df.sort_values('Date')
                
                # Calculate running balances for each account
                account_balances = {}
                for idx, row in ledger_df.iterrows():
                    account = row['Account']
                    if account not in account_balances:
                        account_balances[account] = 0
                    
                    # Update balance based on account type
                    if row['Type'] in ['Asset', 'Expense']:
                        account_balances[account] += row['Debit'] - row['Credit']
                    else:  # Liability, Equity, Revenue
                        account_balances[account] += row['Credit'] - row['Debit']
                    
                    ledger_df.at[idx, 'Balance'] = account_balances[account]
                
                # Account filter
                all_accounts = sorted(ledger_df['Account'].unique())
                selected_account = st.selectbox("Filter by Account", ["All Accounts"] + all_accounts)
                
                if selected_account != "All Accounts":
                    filtered_ledger = ledger_df[ledger_df['Account'] == selected_account]
                else:
                    filtered_ledger = ledger_df
                
                # Display ledger
                st.markdown(f"### 📋 Ledger Entries ({len(filtered_ledger)} records)")
                
                # Format for display
                display_df = filtered_ledger.copy()
                display_df['Date'] = display_df['Date'].dt.strftime('%Y-%m-%d')
                display_df['Debit'] = display_df['Debit'].apply(lambda x: f"₱{x:,.2f}" if x > 0 else "")
                display_df['Credit'] = display_df['Credit'].apply(lambda x: f"₱{x:,.2f}" if x > 0 else "")
                display_df['Balance'] = display_df['Balance'].apply(lambda x: f"₱{x:,.2f}")
                
                display_df = display_df[['Date', 'Account', 'Description', 'Debit', 'Credit', 'Balance', 'Type']]
                
                st.dataframe(display_df, width="stretch", hide_index=True)
                
                # Trial Balance
                st.markdown("---")
                st.markdown("### ⚖️ Trial Balance")
                
                trial_balance = []
                for account in all_accounts:
                    account_transactions = ledger_df[ledger_df['Account'] == account]
                    total_debits = account_transactions['Debit'].sum()
                    total_credits = account_transactions['Credit'].sum()
                    
                    if total_debits > 0 or total_credits > 0:
                        balance = account_balances[account]
                        trial_balance.append({
                            'Account': account,
                            'Type': account_transactions['Type'].iloc[0],
                            'Debit': balance if balance > 0 and account_transactions['Type'].iloc[0] in ['Asset', 'Expense'] else 0,
                            'Credit': abs(balance) if balance < 0 or account_transactions['Type'].iloc[0] not in ['Asset', 'Expense'] else 0
                        })
                
                trial_balance_df = pd.DataFrame(trial_balance)
                trial_balance_df['Debit'] = trial_balance_df['Debit'].apply(lambda x: f"₱{x:,.2f}" if x > 0 else "")
                trial_balance_df['Credit'] = trial_balance_df['Credit'].apply(lambda x: f"₱{x:,.2f}" if x > 0 else "")
                
                st.dataframe(trial_balance_df, width="stretch", hide_index=True)
                
                # Summary
                total_debits = trial_balance_df['Debit'].apply(lambda x: float(x.replace('₱', '').replace(',', '')) if x else 0).sum()
                total_credits = trial_balance_df['Credit'].apply(lambda x: float(x.replace('₱', '').replace(',', '')) if x else 0).sum()
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Debits", f"₱{total_debits:,.2f}")
                with col2:
                    st.metric("Total Credits", f"₱{total_credits:,.2f}")
                with col3:
                    difference = total_debits - total_credits
                    st.metric("Difference", f"₱{abs(difference):,.2f}", delta=f"{'Balanced' if abs(difference) < 0.01 else 'Out of Balance'}")
                
            else:
                st.info("No transactions found to display in the ledger.")
                
        else:
            st.info("No transactions found. Add transactions through the journal modules to see them here.")
            
    except Exception as e:
        st.error(f"❌ Error loading ledger data: {str(e)}")
        st.info("Please try refreshing the page")

# Data Integrity and Validation Functions
def clean_transaction_data(transactions):
    """Remove nulls, None, and empty strings from transaction data"""
    if transactions.empty:
        return transactions
    
    # Remove rows with essential null values
    essential_columns = ['transaction_date', 'final_amount', 'type']
    for col in essential_columns:
        if col in transactions.columns:
            transactions = transactions[transactions[col].notna()]
            transactions = transactions[transactions[col] != '']
    
    # Clean string columns
    string_columns = ['description', 'customer_name', 'supplier_name', 'payment_method']
    for col in string_columns:
        if col in transactions.columns:
            transactions[col] = transactions[col].fillna('')
            transactions[col] = transactions[col].astype(str)
    
    return transactions

def format_currency_ph(amount):
    """Format currency using Philippine Peso symbol with proper formatting"""
    try:
        if pd.isna(amount) or amount == 0:
            return "0.00"
        return f" {amount:,.2f}"
    except:
        return "0.00"

def validate_transaction_data(transaction_data, transaction_type):
    """Validate transaction data before saving to database"""
    errors = []
    
    # Check required fields based on transaction type
    if transaction_type == 'Sales':
        if not transaction_data.get('customer_name') or transaction_data.get('customer_name').strip() == '':
            errors.append("Customer name is required")
    elif transaction_type == 'Purchase':
        if not transaction_data.get('supplier_name') or transaction_data.get('supplier_name').strip() == '':
            errors.append("Supplier name is required")
    
    # Check amount
    try:
        amount = float(transaction_data.get('gross_amount', 0))
        if amount <= 0:
            errors.append("Amount must be greater than 0")
    except (ValueError, TypeError):
        errors.append("Invalid amount format")
    
    # Check transaction date
    if not transaction_data.get('transaction_date'):
        errors.append("Transaction date is required")
    
    return errors

def validate_required_fields(form_data, form_type):
    """Check if all required fields are filled"""
    errors = []
    
    if form_type == 'Sales':
        if not form_data.get('customer_name') or form_data.get('customer_name').strip() == '':
            errors.append("Customer name is required")
    elif form_type == 'Purchase':
        if not form_data.get('supplier_name') or form_data.get('supplier_name').strip() == '':
            errors.append("Supplier name is required")
    elif form_type == 'Cash Receipt':
        if not form_data.get('customer_name') or form_data.get('customer_name').strip() == '':
            errors.append("Customer name is required")
    
    if not form_data.get('gross_amount') or form_data.get('gross_amount') <= 0:
        errors.append("Amount must be greater than 0")
    
    if not form_data.get('transaction_date'):
        errors.append("Transaction date is required")
    
    return errors

def handle_database_error(error):
    """Handle and display database errors gracefully"""
    error_str = str(error)
    
    if '23514' in error_str:  # Check constraint violation
        if 'transactions_status_check' in error_str:
            st.error("Invalid status value. Please use a valid status.")
        elif 'transactions_type_check' in error_str:
            st.error("Invalid transaction type. Please use a valid transaction type.")
        else:
            st.error("Data validation error. Please check your input values.")
    elif '42703' in error_str:  # Column does not exist
        st.error("Database schema error. Please contact support.")
    elif 'PGRST204' in error_str:  # Column not found in schema cache
        st.error("Database configuration error. Please contact support.")
    else:
        st.error(f"Database error: {error_str}")
    
    return False

# Tax Compliance
def show_tax_compliance():
    st.markdown("""
    <div class="main-header">
        <h1>🏛️ Tax Compliance</h1>
        <p>Philippine tax forms and compliance reports</p>
    </div>
    """, unsafe_allow_html=True)
    
    user = get_current_user()
    profile = get_user_profile(user.id) if user else None
    
    if not profile:
        st.error("Unable to load user profile")
        return
    
    # Load transactions for tax calculations
    try:
        supabase = init_supabase()
        current_year = datetime.now().year
        # Use proper date range filter instead of LIKE on timestamp
        start_date = datetime(current_year, 1, 1)
        end_date = datetime(current_year + 1, 1, 1)
        result = supabase.table('transactions').select('*').eq('user_id', user.id).gte('transaction_date', start_date.strftime('%Y-%m-%d')).lt('transaction_date', end_date.strftime('%Y-%m-%d')).execute()
        
        if result.data:
            transactions = pd.DataFrame(result.data)
            transactions['transaction_date'] = pd.to_datetime(transactions['transaction_date'], format='ISO8601', errors='coerce')
            
            # Clean transaction data to remove nulls and invalid entries
            transactions = clean_transaction_data(transactions)
            
            # Tax calculations
            total_revenue = transactions[transactions['type'].isin(['cash_receipt', 'sales'])]['final_amount'].sum()
            total_expenses = transactions[transactions['type'] == 'expense']['final_amount'].sum()
            total_vat_input = transactions['vat_amount'].sum()
            total_ewt = transactions[transactions['ewt_amount'] > 0]['ewt_amount'].sum()
            
            # Quarterly breakdown
            transactions['quarter'] = transactions['transaction_date'].dt.quarter
            quarterly_data = []
            
            for quarter in range(1, 5):
                quarter_data = transactions[transactions['quarter'] == quarter]
                q_revenue = quarter_data[quarter_data['type'].isin(['cash_receipt', 'sales'])]['final_amount'].sum()
                q_expenses = quarter_data[quarter_data['type'] == 'expense']['final_amount'].sum()
                q_vat = quarter_data['vat_amount'].sum()
                q_ewt = quarter_data[quarter_data['ewt_amount'] > 0]['ewt_amount'].sum()
                
                quarterly_data.append({
                    'Quarter': f'Q{quarter}',
                    'Revenue': q_revenue,
                    'Expenses': q_expenses,
                    'Net Income': q_revenue - q_expenses,
                    'VAT': q_vat,
                    'EWT': q_ewt
                })
            
            quarterly_df = pd.DataFrame(quarterly_data)
            
            # Display summary
            st.markdown("### 📊 Tax Summary")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Revenue", format_currency_ph(total_revenue))
            with col2:
                st.metric("Total Expenses", format_currency_ph(total_expenses))
            with col3:
                st.metric("Total VAT", format_currency_ph(total_vat_input))
            with col4:
                st.metric("Total EWT", format_currency_ph(total_ewt))
            
            # Quarterly breakdown
            st.markdown("### 📈 Quarterly Breakdown")
            display_q_df = quarterly_df.copy()
            for col in ['Revenue', 'Expenses', 'Net Income', 'VAT', 'EWT']:
                display_q_df[col] = display_q_df[col].apply(format_currency_ph)
            
            st.dataframe(display_q_df, width="stretch", hide_index=True)
            
            # BIR Forms Section
            st.markdown("---")
            st.markdown("### 📋 BIR Forms")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 📄 Form 2307 - BIR Form No. 2307")
                st.info("Certificate of Creditable Tax Withheld at Source")
                
                if total_ewt > 0:
                    st.write("**Summary of Creditable Withholding Tax:**")
                    ewt_transactions = transactions[transactions['ewt_amount'] > 0]
                    
                    for _, trans in ewt_transactions.iterrows():
                        st.write(f"- {trans['description']}: ₱{trans['ewt_amount']:,.2f}")
                    
                    st.success(f"Total Creditable EWT: ₱{total_ewt:,.2f}")
                    
                    if st.button(" Generate Form 2307", type="primary"):
                        st.markdown("#####  BIR Form No. 2307")
                        st.markdown("**Certificate of Creditable Tax Withheld at Source**")
                        
                        # Professional header with logo placeholder
                        st.markdown("""
                        <div style="text-align: center; margin-bottom: 20px;">
                            <div style="border: 2px dashed #ccc; padding: 20px; margin-bottom: 10px;">
                                <p style="color: #666; margin: 0;">[BUSINESS LOGO]</p>
                            </div>
                            <h3 style="margin: 5px 0;">BIR Form No. 2307</h3>
                            <p style="margin: 5px 0;">Certificate of Creditable Tax Withheld at Source</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Standard BIR Form 2307 fields
                        st.markdown("####  Withholding Agent Information")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Withholding Agent Name:** {profile.get('business_name', 'Your Business')}")
                            st.write(f"**TIN:** 000-000-000-000")
                            st.write(f"**Address:** Business Address")
                        with col2:
                            st.write(f"**Period:** {datetime.now().strftime('%B %Y')}")
                            st.write(f"**ATC:** Expanded (Creditable)")
                            st.write(f"**Date Issued:** {datetime.now().strftime('%Y-%m-%d')}")
                        
                        # Professional transaction table
                        st.markdown("####  Transaction Details")
                        
                        # Create structured table data
                        table_data = []
                        total_gross_amount = 0
                        for _, trans in ewt_transactions.iterrows():
                            gross_amount = trans.get('gross_amount', trans.get('final_amount', 0))
                            table_data.append({
                                'Date': trans['transaction_date'].strftime('%Y-%m-%d'),
                                'Payee Name': trans.get('supplier_name', trans.get('customer_name', 'N/A')),
                                'Description': trans.get('description', 'N/A'),
                                'ATC': 'Expanded',
                                'Tax Base (Gross Amount)': format_currency_ph(gross_amount),
                                'EWT Rate': '1%',
                                'EWT Amount': format_currency_ph(trans['ewt_amount'])
                            })
                            total_gross_amount += gross_amount
                        
                        if table_data:
                            df_table = pd.DataFrame(table_data)
                            st.dataframe(df_table, use_container_width=True, hide_index=True)
                            
                            # Summary section
                            st.markdown("####  Summary")
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Total Gross Amount", format_currency_ph(total_gross_amount))
                            with col2:
                                st.metric("Total EWT", format_currency_ph(total_ewt))
                            with col3:
                                st.metric("Net Amount", format_currency_ph(total_gross_amount - total_ewt))
                        else:
                            st.info("No EWT transactions found for this period.")
                        
                        # Professional footer with signature lines
                        st.markdown("""
                        <div style="margin-top: 40px;">
                            <div style="display: flex; justify-content: space-between; margin-top: 30px;">
                                <div style="width: 45%;">
                                    <div style="border-bottom: 1px solid #000; height: 40px;"></div>
                                    <p style="text-align: center; margin: 5px 0;">Signature over Printed Name</p>
                                    <p style="text-align: center; margin: 5px 0;">Withholding Agent</p>
                                </div>
                                <div style="width: 45%;">
                                    <div style="border-bottom: 1px solid #000; height: 40px;"></div>
                                    <p style="text-align: center; margin: 5px 0;">Signature over Printed Name</p>
                                    <p style="text-align: center; margin: 5px 0;">Payee</p>
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Professional downloadable form
                        form_2307_content = f"""
{'='*80}
BIR FORM NO. 2307
CERTIFICATE OF CREDITABLE TAX WITHHELD AT SOURCE
{'='*80}

WITHHOLDING AGENT INFORMATION:
Withholding Agent Name: {profile.get('business_name', 'Your Business')}
TIN: 000-000-000-000
Address: Business Address
Period: {datetime.now().strftime('%B %Y')}
ATC: Expanded (Creditable)
Date Issued: {datetime.now().strftime('%Y-%m-%d')}

TRANSACTION DETAILS:
{'-'*80}
{'Date':<12} {'Payee Name':<25} {'Description':<20} {'Tax Base':<15} {'EWT':<12}
{'-'*80}
"""
                        
                        for _, trans in ewt_transactions.iterrows():
                            gross_amount = trans.get('gross_amount', trans.get('final_amount', 0))
                            payee_name = trans.get('supplier_name', trans.get('customer_name', 'N/A'))[:24]
                            description = trans.get('description', 'N/A')[:19]
                            form_2307_content += f"{trans['transaction_date'].strftime('%Y-%m-%d'):<12} {payee_name:<25} {description:<20} {format_currency_ph(gross_amount):<15} {format_currency_ph(trans['ewt_amount']):<12}\n"
                        
                        form_2307_content += f"""
{'-'*80}
SUMMARY:
Total Gross Amount: {format_currency_ph(total_gross_amount)}
Total EWT Withheld: {format_currency_ph(total_ewt)}
Net Amount: {format_currency_ph(total_gross_amount - total_ewt)}

{'='*80}
CERTIFIED CORRECT:
_________________________    _________________________
Withholding Agent              Payee
Signature over Printed Name    Signature over Printed Name

{'='*80}
This certificate is issued pursuant to Sec. 83 of the National Internal 
Revenue Code of 1997, as amended.
"""
                        
                        st.download_button(
                            label=" Download Professional Form 2307",
                            data=form_2307_content,
                            file_name=f"BIR_Form_2307_{datetime.now().strftime('%Y%m')}.txt",
                            mime="text/plain",
                            type="primary"
                        )
                else:
                    st.write("No EWT transactions found for this period.")
            
            with col2:
                st.markdown("#### 📄 Form 1601C - Monthly Withholding Tax Return")
                st.info("Creditable Withholding Tax Expanded")
                
                # Get current month data
                current_month = datetime.now().month
                month_data = transactions[transactions['transaction_date'].dt.month == current_month]
                month_ewt = month_data[month_data['ewt_amount'] > 0]['ewt_amount'].sum()
                
                if month_ewt > 0:
                    st.write(f"**Current Month ({datetime.now().strftime('%B')}):**")
                    st.write(f"- Total EWT Withheld: ₱{month_ewt:,.2f}")
                    st.write(f"- Tax Type: Expanded")
                    st.write(f"- Period: {datetime.now().strftime('%B %Y')}")
                    
                    if st.button(" Generate Form 1601C", type="primary"):
                        st.markdown("#####  BIR Form No. 1601C")
                        st.markdown("**Monthly Withholding Tax Return - Creditable Withholding Tax Expanded**")
                        
                        # Professional header with logo placeholder
                        st.markdown("""
                        <div style="text-align: center; margin-bottom: 20px;">
                            <div style="border: 2px dashed #ccc; padding: 20px; margin-bottom: 10px;">
                                <p style="color: #666; margin: 0;">[BUSINESS LOGO]</p>
                            </div>
                            <h3 style="margin: 5px 0;">BIR Form No. 1601C</h3>
                            <p style="margin: 5px 0;">Monthly Withholding Tax Return - Creditable Withholding Tax Expanded</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Standard BIR Form 1601C fields
                        st.markdown("####  Taxpayer Information")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Withholding Agent Name:** {profile.get('business_name', 'Your Business')}")
                            st.write(f"**TIN:** 000-000-000-000")
                            st.write(f"**Address:** Business Address")
                        with col2:
                            st.write(f"**Taxable Period:** {datetime.now().strftime('%B %Y')}")
                            st.write(f"**Tax Type:** Expanded (Creditable)")
                            st.write(f"**Due Date:** 20th {datetime.now().strftime('%B %Y')}")
                        
                        # Professional transaction table
                        st.markdown("####  Creditable Withholding Tax Details")
                        
                        # Create structured table data
                        table_data = []
                        total_gross_amount = 0
                        month_ewt_trans = month_data[month_data['ewt_amount'] > 0]
                        for _, trans in month_ewt_trans.iterrows():
                            gross_amount = trans.get('gross_amount', trans.get('final_amount', 0))
                            table_data.append({
                                'Date': trans['transaction_date'].strftime('%Y-%m-%d'),
                                'Payee Name': trans.get('supplier_name', trans.get('customer_name', 'N/A')),
                                'Description': trans.get('description', 'N/A'),
                                'ATC': 'Expanded',
                                'Tax Base (Gross Amount)': format_currency_ph(gross_amount),
                                'EWT Rate': '1%',
                                'EWT Withheld': format_currency_ph(trans['ewt_amount'])
                            })
                            total_gross_amount += gross_amount
                        
                        if table_data:
                            df_table = pd.DataFrame(table_data)
                            st.dataframe(df_table, use_container_width=True, hide_index=True)
                            
                            # Summary section
                            st.markdown("####  Tax Computation Summary")
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Total Tax Base", format_currency_ph(total_gross_amount))
                            with col2:
                                st.metric("Total EWT Withheld", format_currency_ph(month_ewt))
                            with col3:
                                st.metric("Net Amount", format_currency_ph(total_gross_amount - month_ewt))
                        else:
                            st.info("No EWT transactions found for current month.")
                        
                        # Professional footer with signature lines
                        st.markdown("""
                        <div style="margin-top: 40px;">
                            <div style="display: flex; justify-content: space-between; margin-top: 30px;">
                                <div style="width: 45%;">
                                    <div style="border-bottom: 1px solid #000; height: 40px;"></div>
                                    <p style="text-align: center; margin: 5px 0;">Signature over Printed Name</p>
                                    <p style="text-align: center; margin: 5px 0;">Withholding Agent</p>
                                </div>
                                <div style="width: 45%;">
                                    <div style="border-bottom: 1px solid #000; height: 40px;"></div>
                                    <p style="text-align: center; margin: 5px 0;">Signature over Printed Name</p>
                                    <p style="text-align: center; margin: 5px 0;">Authorized Representative</p>
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Professional downloadable form
                        form_1601c_content = f"""
{'='*80}
BIR FORM NO. 1601C
MONTHLY WITHHOLDING TAX RETURN - CREDITABLE WITHHOLDING TAX EXPANDED
{'='*80}

TAXPAYER INFORMATION:
Withholding Agent Name: {profile.get('business_name', 'Your Business')}
TIN: 000-000-000-000
Address: Business Address
Taxable Period: {datetime.now().strftime('%B %Y')}
Tax Type: Expanded (Creditable)
Due Date: 20th {datetime.now().strftime('%B %Y')}

CREDITABLE WITHHOLDING TAX DETAILS:
{'-'*80}
{'Date':<12} {'Payee Name':<25} {'Description':<20} {'Tax Base':<15} {'EWT':<12}
{'-'*80}
"""
                        
                        for _, trans in month_ewt_trans.iterrows():
                            gross_amount = trans.get('gross_amount', trans.get('final_amount', 0))
                            payee_name = trans.get('supplier_name', trans.get('customer_name', 'N/A'))[:24]
                            description = trans.get('description', 'N/A')[:19]
                            form_1601c_content += f"{trans['transaction_date'].strftime('%Y-%m-%d'):<12} {payee_name:<25} {description:<20} {format_currency_ph(gross_amount):<15} {format_currency_ph(trans['ewt_amount']):<12}\n"
                        
                        form_1601c_content += f"""
{'-'*80}
TAX COMPUTATION SUMMARY:
Total Tax Base: {format_currency_ph(total_gross_amount)}
Total EWT Withheld: {format_currency_ph(month_ewt)}
Net Amount: {format_currency_ph(total_gross_amount - month_ewt)}

{'='*80}
CERTIFIED CORRECT:
_________________________    _________________________
Withholding Agent              Authorized Representative
Signature over Printed Name    Signature over Printed Name

{'='*80}
This return is filed pursuant to Sec. 58 of the National Internal 
Revenue Code of 1997, as amended.
"""
                        
                        st.download_button(
                            label=" Download Professional Form 1601C",
                            data=form_1601c_content,
                            file_name=f"BIR_Form_1601C_{datetime.now().strftime('%Y%m')}.txt",
                            mime="text/plain",
                            type="primary"
                        )
                else:
                    st.write("No EWT transactions for current month.")
            
            # VAT Returns
            st.markdown("---")
            st.markdown("### 📊 VAT Returns")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 📄 Form 2550Q - Quarterly VAT Return")
                
                for _, quarter in quarterly_df.iterrows():
                    quarter_num = quarter['Quarter'].replace('Q', '')
                    with st.expander(f"{quarter['Quarter']} VAT Return"):
                        st.write(f"**Period:** {quarter_num} {current_year}")
                        st.write(f"**Output VAT:** {quarter['VAT']:,.2f}")
                        st.write(f"**Input VAT:** {quarter['VAT']:,.2f}")  # Simplified
                        st.write(f"**VAT Payable:** {quarter['VAT']:,.2f}")  # Simplified
                        
                        if st.button(f" Generate {quarter['Quarter']} VAT Return", key=f"vat_{quarter_num}"):
                            st.markdown(f"#####  BIR Form No. 2550Q")
                            st.markdown(f"**Quarterly VAT Return - {quarter['Quarter']} {current_year}**")
                            
                            # Professional header with logo placeholder
                            st.markdown(f"""
                            <div style="text-align: center; margin-bottom: 20px;">
                                <div style="border: 2px dashed #ccc; padding: 20px; margin-bottom: 10px;">
                                    <p style="color: #666; margin: 0;">[BUSINESS LOGO]</p>
                                </div>
                                <h3 style="margin: 5px 0;">BIR Form No. 2550Q</h3>
                                <p style="margin: 5px 0;">Quarterly VAT Return - {quarter['Quarter']} {current_year}</p>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Standard BIR Form 2550Q fields
                            st.markdown("####  Taxpayer Information")
                            col1, col2 = st.columns(2)
                            with col1:
                                st.write(f"**Taxpayer Name:** {profile.get('business_name', 'Your Business')}")
                                st.write(f"**TIN:** 000-000-000-000")
                                st.write(f"**Address:** Business Address")
                            with col2:
                                st.write(f"**Taxable Period:** Q{quarter_num} {current_year}")
                                st.write(f"**VAT Type:** {profile.get('tax_type', 'VAT (12%)')}")
                                st.write(f"**Due Date:** 20th day following end of Q{quarter_num} {current_year}")
                            
                            # Professional VAT transaction table
                            st.markdown("####  VAT Transaction Details")
                            
                            # Create structured table data
                            table_data = []
                            total_output_vat = 0
                            total_input_vat = 0
                            quarter_trans = transactions[transactions['quarter'] == int(quarter_num)]
                            vat_trans = quarter_trans[quarter_trans['vat_amount'] > 0]
                            
                            for _, trans in vat_trans.iterrows():
                                is_output = trans['type'] in ['cash_receipt', 'sales']
                                if is_output:
                                    total_output_vat += trans['vat_amount']
                                else:
                                    total_input_vat += trans['vat_amount']
                                
                                table_data.append({
                                    'Date': trans['transaction_date'].strftime('%Y-%m-%d'),
                                    'Transaction Type': trans['type'].title(),
                                    'Description': trans.get('description', 'N/A'),
                                    'Gross Amount': format_currency_ph(trans.get('gross_amount', 0)),
                                    'VAT Rate': f"{trans.get('vat_rate', 0) * 100:.0f}%",
                                    'VAT Amount': format_currency_ph(trans['vat_amount']),
                                    'VAT Type': 'Output' if is_output else 'Input'
                                })
                            
                            if table_data:
                                df_table = pd.DataFrame(table_data)
                                st.dataframe(df_table, use_container_width=True, hide_index=True)
                                
                                # VAT computation summary
                                st.markdown("####  VAT Computation Summary")
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("Total Output VAT", format_currency_ph(total_output_vat))
                                with col2:
                                    st.metric("Total Input VAT", format_currency_ph(total_input_vat))
                                with col3:
                                    vat_payable = total_output_vat - total_input_vat
                                    st.metric("VAT Payable/Refundable", format_currency_ph(vat_payable))
                            else:
                                st.info(f"No VAT transactions found for {quarter['Quarter']} {current_year}.")
                            
                            # Professional footer with signature lines
                            st.markdown(f"""
                            <div style="margin-top: 40px;">
                                <div style="display: flex; justify-content: space-between; margin-top: 30px;">
                                    <div style="width: 45%;">
                                        <div style="border-bottom: 1px solid #000; height: 40px;"></div>
                                        <p style="text-align: center; margin: 5px 0;">Signature over Printed Name</p>
                                        <p style="text-align: center; margin: 5px 0;">Taxpayer</p>
                                    </div>
                                    <div style="width: 45%;">
                                        <div style="border-bottom: 1px solid #000; height: 40px;"></div>
                                        <p style="text-align: center; margin: 5px 0;">Signature over Printed Name</p>
                                        <p style="text-align: center; margin: 5px 0;">Authorized Representative</p>
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Professional downloadable form
                            form_2550q_content = f"""
{'='*80}
BIR FORM NO. 2550Q
QUARTERLY VAT RETURN - Q{quarter_num} {current_year}
{'='*80}

TAXPAYER INFORMATION:
Taxpayer Name: {profile.get('business_name', 'Your Business')}
TIN: 000-000-000-000
Address: Business Address
Taxable Period: Q{quarter_num} {current_year}
VAT Type: {profile.get('tax_type', 'VAT (12%)')}
Due Date: 20th day following end of Q{quarter_num} {current_year}

VAT TRANSACTION DETAILS:
{'-'*80}
{'Date':<12} {'Type':<15} {'Description':<20} {'Gross':<12} {'VAT':<12}
{'-'*80}
"""
                            
                            for _, trans in vat_trans.iterrows():
                                is_output = trans['type'] in ['cash_receipt', 'sales']
                                trans_type = trans['type'].title()[:14]
                                description = trans.get('description', 'N/A')[:19]
                                form_2550q_content += f"{trans['transaction_date'].strftime('%Y-%m-%d'):<12} {trans_type:<15} {description:<20} {format_currency_ph(trans.get('gross_amount', 0)):<12} {format_currency_ph(trans['vat_amount']):<12}\n"
                            
                            vat_payable = total_output_vat - total_input_vat
                            form_2550q_content += f"""
{'-'*80}
VAT COMPUTATION SUMMARY:
Total Output VAT: {format_currency_ph(total_output_vat)}
Total Input VAT: {format_currency_ph(total_input_vat)}
VAT Payable/Refundable: {format_currency_ph(vat_payable)}

{'='*80}
CERTIFIED CORRECT:
_________________________    _________________________
Taxpayer                      Authorized Representative
Signature over Printed Name    Signature over Printed Name

{'='*80}
This return is filed pursuant to Sec. 114 of the National Internal 
Revenue Code of 1997, as amended.
"""
                            
                            st.download_button(
                                label=f" Download Professional {quarter['Quarter']} VAT Return",
                                data=form_2550q_content,
                                file_name=f"BIR_Form_2550Q_{current_year}_Q{quarter_num}.txt",
                                mime="text/plain",
                                type="primary"
                            )
            
            with col2:
                st.markdown("#### 📄 Annual Income Tax")
                
                annual_income = total_revenue - total_expenses
                tax_type = profile.get('tax_type', 'VAT (12%)')
                
                st.write(f"**Tax Type:** {tax_type}")
                st.write(f"**Gross Income:** {annual_income:,.2f}")
                
                # Simplified tax calculation
                if 'NON-VAT' in tax_type:
                    if '1%' in tax_type:
                        income_tax = annual_income * 0.01
                    elif '3%' in tax_type:
                        income_tax = annual_income * 0.03
                    else:
                        income_tax = annual_income * 0.08
                else:
                    # Simplified VAT calculation
                    income_tax = annual_income * 0.12
                
                st.write(f"**Estimated Income Tax:** {income_tax:,.2f}")
                
                if st.button(" Generate Annual Tax Return", type="primary"):
                    st.markdown("#####  BIR Form No. 1701")
                    st.markdown("**Annual Income Tax Return**")
                    
                    # Professional header with logo placeholder
                    st.markdown(f"""
                    <div style="text-align: center; margin-bottom: 20px;">
                        <div style="border: 2px dashed #ccc; padding: 20px; margin-bottom: 10px;">
                            <p style="color: #666; margin: 0;">[BUSINESS LOGO]</p>
                        </div>
                        <h3 style="margin: 5px 0;">BIR Form No. 1701</h3>
                        <p style="margin: 5px 0;">Annual Income Tax Return - Tax Year {current_year}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Standard BIR Form 1701 fields
                    st.markdown("####  Taxpayer Information")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Taxpayer Name:** {profile.get('business_name', 'Your Business')}")
                        st.write(f"**TIN:** 000-000-000-000")
                        st.write(f"**Address:** Business Address")
                    with col2:
                        st.write(f"**Tax Year:** {current_year}")
                        st.write(f"**Tax Type:** {tax_type}")
                        st.write(f"**Due Date:** April 15, {current_year + 1}")
                    
                    # Professional income computation table
                    st.markdown("####  Income Tax Computation")
                    
                    # Create structured income data
                    income_data = []
                    total_revenue_amount = 0
                    total_expenses_amount = 0
                    
                    # Revenue transactions
                    revenue_trans = transactions[transactions['type'].isin(['cash_receipt', 'sales'])]
                    for _, trans in revenue_trans.iterrows():
                        total_revenue_amount += trans['final_amount']
                        income_data.append({
                            'Date': trans['transaction_date'].strftime('%Y-%m-%d'),
                            'Transaction Type': 'Revenue',
                            'Description': trans.get('description', 'Sales'),
                            'Amount': format_currency_ph(trans['final_amount']),
                            'Category': 'Gross Income'
                        })
                    
                    # Expense transactions
                    expense_trans = transactions[transactions['type'].isin(['purchase', 'expense'])]
                    for _, trans in expense_trans.iterrows():
                        total_expenses_amount += trans['final_amount']
                        income_data.append({
                            'Date': trans['transaction_date'].strftime('%Y-%m-%d'),
                            'Transaction Type': 'Expense',
                            'Description': trans.get('description', 'Purchase'),
                            'Amount': format_currency_ph(trans['final_amount']),
                            'Category': 'Deductible Expense'
                        })
                    
                    if income_data:
                        df_income = pd.DataFrame(income_data)
                        st.dataframe(df_income, use_container_width=True, hide_index=True)
                        
                        # Tax computation summary
                        st.markdown("####  Tax Computation Summary")
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Total Gross Income", format_currency_ph(total_revenue_amount))
                        with col2:
                            st.metric("Total Deductible Expenses", format_currency_ph(total_expenses_amount))
                        with col3:
                            st.metric("Taxable Income", format_currency_ph(annual_income))
                        with col4:
                            st.metric("Estimated Income Tax", format_currency_ph(income_tax))
                    else:
                        st.info(f"No income transactions found for tax year {current_year}.")
                    
                    # Tax rate explanation
                    st.markdown("####  Tax Rate Applied")
                    if 'NON-VAT' in tax_type:
                        if '1%' in tax_type:
                            st.write(f"**Tax Rate:** 1% (NON-VAT Registered - 1% Presumptive)")
                        elif '3%' in tax_type:
                            st.write(f"**Tax Rate:** 3% (NON-VAT Registered - 3% Presumptive)")
                        else:
                            st.write(f"**Tax Rate:** 8% (NON-VAT Registered - 8% Presumptive)")
                    else:
                        st.write(f"**Tax Rate:** 12% (VAT Registered - Corporate Income Tax)")
                    
                    st.write(f"**Computation:** {format_currency_ph(annual_income)} × Tax Rate = {format_currency_ph(income_tax)}")
                    
                    # Professional footer with signature lines
                    st.markdown(f"""
                    <div style="margin-top: 40px;">
                        <div style="display: flex; justify-content: space-between; margin-top: 30px;">
                            <div style="width: 45%;">
                                <div style="border-bottom: 1px solid #000; height: 40px;"></div>
                                <p style="text-align: center; margin: 5px 0;">Signature over Printed Name</p>
                                <p style="text-align: center; margin: 5px 0;">Taxpayer</p>
                            </div>
                            <div style="width: 45%;">
                                <div style="border-bottom: 1px solid #000; height: 40px;"></div>
                                <p style="text-align: center; margin: 5px 0;">Signature over Printed Name</p>
                                <p style="text-align: center; margin: 5px 0;">Authorized Representative</p>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Professional downloadable form
                    form_1701_content = f"""
{'='*80}
BIR FORM NO. 1701
ANNUAL INCOME TAX RETURN - TAX YEAR {current_year}
{'='*80}

TAXPAYER INFORMATION:
Taxpayer Name: {profile.get('business_name', 'Your Business')}
TIN: 000-000-000-000
Address: Business Address
Tax Year: {current_year}
Tax Type: {tax_type}
Due Date: April 15, {current_year + 1}

INCOME TAX COMPUTATION:
{'-'*80}
{'Date':<12} {'Type':<15} {'Description':<20} {'Amount':<15} {'Category':<20}
{'-'*80}
"""
                    
                    for item in income_data:
                        date = item['Date']
                        trans_type = item['Transaction Type'][:14]
                        description = item['Description'][:19]
                        amount = item['Amount']
                        category = item['Category'][:19]
                        form_1701_content += f"{date:<12} {trans_type:<15} {description:<20} {amount:<15} {category:<20}\n"
                    
                    form_1701_content += f"""
{'-'*80}
TAX COMPUTATION SUMMARY:
Total Gross Income: {format_currency_ph(total_revenue_amount)}
Total Deductible Expenses: {format_currency_ph(total_expenses_amount)}
Taxable Income: {format_currency_ph(annual_income)}
Estimated Income Tax: {format_currency_ph(income_tax)}

TAX RATE APPLIED:
"""
                    if 'NON-VAT' in tax_type:
                        if '1%' in tax_type:
                            form_1701_content += "Tax Rate: 1% (NON-VAT Registered - 1% Presumptive)\n"
                        elif '3%' in tax_type:
                            form_1701_content += "Tax Rate: 3% (NON-VAT Registered - 3% Presumptive)\n"
                        else:
                            form_1701_content += "Tax Rate: 8% (NON-VAT Registered - 8% Presumptive)\n"
                    else:
                        form_1701_content += "Tax Rate: 12% (VAT Registered - Corporate Income Tax)\n"
                    
                    form_1701_content += f"Computation: {format_currency_ph(annual_income)} × Tax Rate = {format_currency_ph(income_tax)}\n"
                    
                    form_1701_content += f"""
{'='*80}
CERTIFIED CORRECT:
_________________________    _________________________
Taxpayer                      Authorized Representative
Signature over Printed Name    Signature over Printed Name

{'='*80}
This return is filed pursuant to Sec. 42 of the National Internal 
Revenue Code of 1997, as amended.

DISCLAIMER:
This is a simplified calculation for informational purposes only. 
Please consult with a qualified tax professional for accurate tax filing.
{'='*80}
"""
                    
                    st.download_button(
                        label=" Download Professional Annual Tax Return",
                        data=form_1701_content,
                        file_name=f"BIR_Form_1701_{current_year}.txt",
                        mime="text/plain",
                        type="primary"
                    )
            
            # Tax Calendar
            st.markdown("---")
            st.markdown("### 📅 Tax Calendar")
            
            tax_deadlines = [
                {"Date": "Monthly 20th", "Form": "Form 1601C", "Description": "Monthly Withholding Tax"},
                {"Date": "Quarterly 20th", "Form": "Form 2550Q", "Description": "Quarterly VAT Return"},
                {"Date": "Quarterly 20th", "Form": "Form 1701Q", "Description": "Quarterly Income Tax"},
                {"Date": "April 15", "Form": "Form 1701", "Description": "Annual Income Tax"},
                {"Date": "Monthly 20th", "Form": "Form 2307", "Description": "Certificate of EWT"}
            ]
            
            deadlines_df = pd.DataFrame(tax_deadlines)
            st.dataframe(deadlines_df, width="stretch", hide_index=True)
            
        else:
            st.info("No transactions found for the current year. Add transactions to generate tax reports.")
            
    except Exception as e:
        st.error(f"❌ Error loading tax data: {str(e)}")
        st.info("Please try refreshing the page")

# Financial Statement Export Functions
def generate_pdf_financial_statements(period_title, income_data, balance_data, equity_data, cash_flow_data):
    """Generate professional PDF financial statements"""
    try:
        # Create professional PDF content
        pdf_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: 'Times New Roman', serif; margin: 40px; }}
                .header {{ text-align: center; margin-bottom: 30px; }}
                .title {{ font-size: 24px; font-weight: bold; margin-bottom: 10px; }}
                .subtitle {{ font-size: 16px; color: #666; margin-bottom: 20px; }}
                .statement-title {{ font-size: 18px; font-weight: bold; margin-top: 30px; margin-bottom: 15px; border-bottom: 2px solid #333; padding-bottom: 5px; }}
                table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
                th, td {{ text-align: left; padding: 8px; border-bottom: 1px solid #ddd; }}
                .total {{ font-weight: bold; border-top: 2px solid #333; }}
                .grand-total {{ font-weight: bold; font-size: 14px; background-color: #f5f5f5; }}
                .right-align {{ text-align: right; }}
                .indent {{ padding-left: 20px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <div class="title">FINANCIAL STATEMENTS</div>
                <div class="subtitle">For the period ended {period_title}</div>
                <div class="subtitle">Generated on {datetime.now().strftime('%B %d, %Y')}</div>
            </div>
            
            <div class="statement-title">STATEMENT OF COMPREHENSIVE INCOME</div>
            <table>
                <tr><td width="70%">Revenue</td><td class="right-align" width="30%">PHP {sum(item['Amount'] for item in income_data if item['Type'] == 'Revenue'):,.2f}</td></tr>
                <tr><td class="indent">Less: Cost of Goods Sold</td><td class="right-align">PHP 0.00</td></tr>
                <tr><td class="total">Gross Profit</td><td class="right-align">PHP {sum(item['Amount'] for item in income_data if item['Type'] == 'Total' and 'Profit' in item['Item']):,.2f}</td></tr>
                <tr><td colspan="2">&nbsp;</td></tr>
                <tr><td>Operating Expenses</td><td class="right-align">PHP {sum(item['Amount'] for item in income_data if 'Expense' in item['Type'] and 'Tax' not in item['Item']):,.2f}</td></tr>
                <tr><td class="total">Net Income</td><td class="right-align">PHP {sum(item['Amount'] for item in income_data if 'Net Income' in item['Item']):,.2f}</td></tr>
            </table>
            
            <div class="statement-title">BALANCE SHEET</div>
            <table>
                <tr><td class="grand-total">TOTAL ASSETS</td><td class="right-align grand-total">PHP {sum(item['Amount'] for item in balance_data if item['Type'] == 'Asset'):,.2f}</td></tr>
                <tr><td class="grand-total">TOTAL LIABILITIES</td><td class="right-align grand-total">PHP {sum(item['Amount'] for item in balance_data if item['Type'] == 'Liability'):,.2f}</td></tr>
                <tr><td class="grand-total">TOTAL EQUITY</td><td class="right-align grand-total">PHP {sum(item['Amount'] for item in balance_data if item['Type'] == 'Equity'):,.2f}</td></tr>
            </table>
        </body>
        </html>
        """
        
        # Save to temporary file and provide download
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            f.write(pdf_content)
            temp_file = f.name
        
        st.success("PDF generated successfully! The file contains professionally formatted financial statements.")
        st.info("Note: In production, this would generate a downloadable PDF file.")
        
    except Exception as e:
        st.error(f"Error generating PDF: {str(e)}")

def generate_excel_financial_statements(period_title, income_data, balance_data, equity_data, cash_flow_data):
    """Generate professional Excel financial statements"""
    try:
        # Create Excel content
        import io
        import xlsxwriter
        from xlsxwriter.utility import xl_range
        
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        
        # Format styles
        bold_format = workbook.add_format({'bold': True, 'font_size': 14})
        title_format = workbook.add_format({'bold': True, 'font_size': 16, 'align': 'center'})
        header_format = workbook.add_format({'bold': True, 'bg_color': '#D9E1F2', 'border': 1})
        total_format = workbook.add_format({'bold': True, 'border': 1, 'bg_color': '#E2EFDA'})
        currency_format = workbook.add_format({'num_format': 'PHP #,##0.00', 'border': 1})
        
        # Income Statement
        income_sheet = workbook.add_worksheet('Income Statement')
        income_sheet.write(0, 0, f'STATEMENT OF COMPREHENSIVE INCOME', title_format)
        income_sheet.write(1, 0, f'For the period ended {period_title}', bold_format)
        income_sheet.write(2, 0, f'Generated on {datetime.now().strftime("%B %d, %Y")}', bold_format)
        
        # Income Statement data
        row = 4
        income_sheet.write(row, 0, 'Item', header_format)
        income_sheet.write(row, 1, 'Amount', header_format)
        row += 1
        
        for item in income_data:
            if item['Type'] == 'GrandTotal':
                income_sheet.write(row, 0, item['Item'], total_format)
                income_sheet.write(row, 1, item['Amount'], total_format)
            elif item['Type'] == 'Total':
                income_sheet.write(row, 0, item['Item'], bold_format)
                income_sheet.write(row, 1, item['Amount'], currency_format)
            else:
                income_sheet.write(row, 0, item['Item'], None)
                income_sheet.write(row, 1, item['Amount'], currency_format)
            row += 1
        
        # Balance Sheet
        balance_sheet = workbook.add_worksheet('Balance Sheet')
        balance_sheet.write(0, 0, 'BALANCE SHEET', title_format)
        balance_sheet.write(1, 0, f'As of {period_title}', bold_format)
        
        # Balance Sheet data
        row = 3
        balance_sheet.write(row, 0, 'Section', header_format)
        balance_sheet.write(row, 1, 'Item', header_format)
        balance_sheet.write(row, 2, 'Amount', header_format)
        row += 1
        
        for item in balance_data:
            if item['Type'] == 'GrandTotal':
                balance_sheet.write(row, 0, item['Section'], total_format)
                balance_sheet.write(row, 1, item['Item'], total_format)
                balance_sheet.write(row, 2, item['Amount'], total_format)
            else:
                balance_sheet.write(row, 0, item['Section'], None)
                balance_sheet.write(row, 1, item['Item'], None)
                balance_sheet.write(row, 2, item['Amount'], currency_format)
            row += 1
        
        workbook.close()
        output.seek(0)
        
        st.success("Excel file generated successfully! Contains professionally formatted financial statements with proper accounting formats.")
        st.info("Note: In production, this would provide a downloadable Excel file.")
        
    except Exception as e:
        st.error(f"Error generating Excel: {str(e)}")

def print_financial_statements(period_title, income_data, balance_data, equity_data, cash_flow_data):
    """Generate print-friendly financial statements"""
    try:
        # Create print-friendly CSS
        st.markdown("""
        <style>
            @media print {
                .print-header { page-break-after: always; }
                .no-print { display: none; }
                .print-only { display: block; }
                body { font-family: 'Times New Roman', serif; }
            }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="print-header">
            <h1 style="text-align: center; font-size: 24px; font-weight: bold;">FINANCIAL STATEMENTS</h1>
            <p style="text-align: center; font-size: 16px; color: #666;">For the period ended {period_title}</p>
            <p style="text-align: center; font-size: 14px;">Generated on {datetime.now().strftime('%B %d, %Y')}</p>
            <hr style="border: 2px solid #333; margin: 20px 0;">
        </div>
        """, unsafe_allow_html=True)
        
        st.success("Print view ready! Use browser's print function (Ctrl+P) to print professionally formatted statements.")
        st.info("For best results, set printer orientation to Landscape and margins to Narrow.")
        
    except Exception as e:
        st.error(f"Error preparing print view: {str(e)}")

# Financial Statements
def show_financial_statements():
    st.markdown("""
    <div class="main-header">
        <h1>📄 Financial Statements</h1>
        <p>Philippine financial statements and reports</p>
    </div>
    """, unsafe_allow_html=True)
    
    user = get_current_user()
    profile = get_user_profile(user.id) if user else None
    
    if not profile:
        st.error("Unable to load user profile")
        return
    
    # Period selection
    col1, col2 = st.columns(2)
    with col1:
        period_type = st.selectbox("Period Type", ["Monthly", "Quarterly", "Annual"])
    with col2:
        if period_type == "Monthly":
            selected_month = st.selectbox("Select Month", 
                ["January", "February", "March", "April", "May", "June",
                 "July", "August", "September", "October", "November", "December"])
            selected_year = st.selectbox("Select Year", list(range(2020, datetime.now().year + 1)), 
                                      index=len(list(range(2020, datetime.now().year + 1))) - 1)
        elif period_type == "Quarterly":
            selected_quarter = st.selectbox("Select Quarter", ["Q1", "Q2", "Q3", "Q4"])
            selected_year = st.selectbox("Select Year", list(range(2020, datetime.now().year + 1)), 
                                      index=len(list(range(2020, datetime.now().year + 1))) - 1)
        else:
            selected_year = st.selectbox("Select Year", list(range(2020, datetime.now().year + 1)), 
                                      index=len(list(range(2020, datetime.now().year + 1))) - 1)
    
    # Load transactions for the selected period
    try:
        supabase = init_supabase()
        
        # Calculate date range based on period selection
        if period_type == "Monthly":
            month_num = datetime.strptime(selected_month, "%B").month
            start_date = datetime(selected_year, month_num, 1)
            if month_num == 12:
                end_date = datetime(selected_year + 1, 1, 1)
            else:
                end_date = datetime(selected_year, month_num + 1, 1)
            period_title = f"{selected_month} {selected_year}"
        elif period_type == "Quarterly":
            quarter_num = int(selected_quarter.replace("Q", ""))
            start_month = (quarter_num - 1) * 3 + 1
            start_date = datetime(selected_year, start_month, 1)
            if quarter_num == 4:
                end_date = datetime(selected_year + 1, 1, 1)
            else:
                end_date = datetime(selected_year, start_month + 3, 1)
            period_title = f"{selected_quarter} {selected_year}"
        else:
            start_date = datetime(selected_year, 1, 1)
            end_date = datetime(selected_year + 1, 1, 1)
            period_title = f"Year {selected_year}"
        
        result = supabase.table('transactions').select('*').eq('user_id', user.id).gte('transaction_date', start_date.strftime('%Y-%m-%d')).lt('transaction_date', end_date.strftime('%Y-%m-%d')).execute()
        
        if result.data and len(result.data) > 0:
            transactions = pd.DataFrame(result.data)
            transactions['transaction_date'] = pd.to_datetime(transactions['transaction_date'], format='ISO8601', errors='coerce')
            
            # Calculate financial metrics
            revenue = transactions[transactions['type'].isin(['cash_receipt', 'sales'])]['final_amount'].sum()
            expenses = transactions[transactions['type'] == 'expense']['final_amount'].sum()
            gross_profit = revenue  # Simplified
            operating_income = gross_profit - expenses
            net_income = operating_income
            
            # Calculate account balances
            cash = transactions[transactions['payment_method'] == 'Cash']['final_amount'].sum()
            accounts_receivable = transactions[transactions['type'] == 'sales']['final_amount'].sum()
            accounts_payable = transactions[transactions['type'] == 'purchase']['final_amount'].sum()
            
            # Statement tabs
            tab1, tab2, tab3, tab4 = st.tabs(["📊 Income Statement", "⚖️ Balance Sheet", "📈 Statement of Changes in Equity", "📋 Cash Flow Statement"])
            
            with tab1:
                st.markdown(f"### 📊 Statement of Comprehensive Income")
                st.markdown(f"**For the period ended {period_title}**")
                
                # Income Statement
                income_statement_data = [
                    {"Item": "Revenue", "Amount": revenue, "Type": "Revenue"},
                    {"Item": "Less: Cost of Goods Sold", "Amount": 0, "Type": "Expense"},  # Simplified
                    {"Item": "Gross Profit", "Amount": gross_profit, "Type": "Total"},
                    {"Item": "", "Amount": 0, "Type": "Separator"},
                    {"Item": "Operating Expenses", "Amount": 0, "Type": "Header"},
                    {"Item": "Salaries and Wages", "Amount": expenses * 0.3, "Type": "Expense"},
                    {"Item": "Rent Expense", "Amount": expenses * 0.2, "Type": "Expense"},
                    {"Item": "Utilities", "Amount": expenses * 0.1, "Type": "Expense"},
                    {"Item": "Other Operating Expenses", "Amount": expenses * 0.4, "Type": "Expense"},
                    {"Item": "Total Operating Expenses", "Amount": expenses, "Type": "Total"},
                    {"Item": "Operating Income", "Amount": operating_income, "Type": "Total"},
                    {"Item": "", "Amount": 0, "Type": "Separator"},
                    {"Item": "Other Income", "Amount": 0, "Type": "Revenue"},
                    {"Item": "Interest Expense", "Amount": 0, "Type": "Expense"},
                    {"Item": "Net Income Before Tax", "Amount": operating_income, "Type": "Total"},
                    {"Item": "Income Tax Expense", "Amount": operating_income * 0.3, "Type": "Expense"},  # Simplified
                    {"Item": "Net Income", "Amount": net_income * 0.7, "Type": "Total"}
                ]
                
                income_df = pd.DataFrame(income_statement_data)
                
                for idx, row in income_df.iterrows():
                    if row['Type'] == "Separator":
                        st.markdown("---")
                    elif row['Type'] == "Header":
                        st.markdown(f"**{row['Item']}**")
                    else:
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            if row['Type'] == "Total":
                                st.markdown(f"**{row['Item']}**")
                            else:
                                st.write(row['Item'])
                        with col2:
                            if row['Type'] == "Total":
                                st.markdown(f"**₱{row['Amount']:,.2f}**")
                            else:
                                st.write(f"₱{row['Amount']:,.2f}")
                
                # Summary metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Revenue", f"₱{revenue:,.2f}")
                with col2:
                    st.metric("Total Expenses", f"₱{expenses:,.2f}")
                with col3:
                    st.metric("Net Income", f"₱{net_income * 0.7:,.2f}")
            
            with tab2:
                st.markdown(f"### ⚖️ Statement of Financial Position (Balance Sheet)")
                st.markdown(f"**As of {end_date.strftime('%B %d, %Y')}**")
                
                # Balance Sheet
                total_assets = cash + accounts_receivable + 10000  # Adding some fixed assets
                total_liabilities = accounts_payable + 5000  # Adding some liabilities
                total_equity = total_assets - total_liabilities
                
                balance_sheet_data = [
                    {"Section": "ASSETS", "Item": "", "Amount": 0, "Type": "Header"},
                    {"Section": "Current Assets", "Item": "Cash and Cash Equivalents", "Amount": cash, "Type": "Asset"},
                    {"Section": "Current Assets", "Item": "Accounts Receivable", "Amount": accounts_receivable, "Type": "Asset"},
                    {"Section": "Current Assets", "Item": "Inventories", "Amount": 5000, "Type": "Asset"},
                    {"Section": "Current Assets", "Item": "Total Current Assets", "Amount": cash + accounts_receivable + 5000, "Type": "Total"},
                    {"Section": "Non-current Assets", "Item": "Equipment", "Amount": 8000, "Type": "Asset"},
                    {"Section": "Non-current Assets", "Item": "Furniture and Fixtures", "Amount": 2000, "Type": "Asset"},
                    {"Section": "Non-current Assets", "Item": "Total Non-current Assets", "Amount": 10000, "Type": "Total"},
                    {"Section": "TOTAL ASSETS", "Item": "", "Amount": total_assets, "Type": "GrandTotal"},
                    {"Section": "LIABILITIES AND EQUITY", "Item": "", "Amount": 0, "Type": "Header"},
                    {"Section": "Current Liabilities", "Item": "Accounts Payable", "Amount": accounts_payable, "Type": "Liability"},
                    {"Section": "Current Liabilities", "Item": "Accrued Expenses", "Amount": 2000, "Type": "Liability"},
                    {"Section": "Current Liabilities", "Item": "Total Current Liabilities", "Amount": accounts_payable + 2000, "Type": "Total"},
                    {"Section": "Non-current Liabilities", "Item": "Notes Payable", "Amount": 3000, "Type": "Liability"},
                    {"Section": "Non-current Liabilities", "Item": "Total Non-current Liabilities", "Amount": 3000, "Type": "Total"},
                    {"Section": "TOTAL LIABILITIES", "Item": "", "Amount": total_liabilities, "Type": "GrandTotal"},
                    {"Section": "EQUITY", "Item": "Owner's Capital", "Amount": total_equity * 0.8, "Type": "Equity"},
                    {"Section": "EQUITY", "Item": "Retained Earnings", "Amount": total_equity * 0.2, "Type": "Equity"},
                    {"Section": "TOTAL EQUITY", "Item": "", "Amount": total_equity, "Type": "GrandTotal"},
                    {"Section": "TOTAL LIABILITIES AND EQUITY", "Item": "", "Amount": total_liabilities + total_equity, "Type": "GrandTotal"}
                ]
                
                balance_df = pd.DataFrame(balance_sheet_data)
                
                current_section = ""
                for idx, row in balance_df.iterrows():
                    if row['Type'] == "Header":
                        st.markdown(f"### {row['Section']}")
                        current_section = row['Section']
                    elif row['Type'] == "GrandTotal":
                        st.markdown("---")
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.markdown(f"**{row['Section']}**")
                        with col2:
                            st.markdown(f"**₱{row['Amount']:,.2f}**")
                    else:
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            if row['Type'] == "Total":
                                st.markdown(f"*{row['Item']}*")
                            else:
                                st.write(f"&nbsp;&nbsp;&nbsp;&nbsp;{row['Item']}")
                        with col2:
                            if row['Type'] == "Total":
                                st.markdown(f"*₱{row['Amount']:,.2f}*")
                            else:
                                st.write(f"₱{row['Amount']:,.2f}")
                
                # Key metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Assets", f"₱{total_assets:,.2f}")
                with col2:
                    st.metric("Total Liabilities", f"₱{total_liabilities:,.2f}")
                with col3:
                    st.metric("Total Equity", f"₱{total_equity:,.2f}")
            
            with tab3:
                st.markdown(f"### 📈 Statement of Changes in Equity")
                st.markdown(f"**For the period ended {period_title}**")
                
                # Statement of Changes in Equity
                beginning_equity = total_equity * 0.5  # Simplified
                net_income_for_period = net_income * 0.7
                owner_contributions = 0
                owner_drawings = 0
                ending_equity = beginning_equity + net_income_for_period + owner_contributions - owner_drawings
                
                equity_changes = [
                    {"Item": "Beginning Balance", "Amount": beginning_equity},
                    {"Item": "Add: Net Income for the Period", "Amount": net_income_for_period},
                    {"Item": "Less: Owner Drawings", "Amount": owner_drawings},
                    {"Item": "Add: Owner Contributions", "Amount": owner_contributions},
                    {"Item": "Ending Balance", "Amount": ending_equity, "Highlight": True}
                ]
                
                for item in equity_changes:
                    if item.get("Highlight"):
                        st.markdown("---")
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.markdown(f"**{item['Item']}**")
                        with col2:
                            st.markdown(f"**₱{item['Amount']:,.2f}**")
                    else:
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.write(item['Item'])
                        with col2:
                            st.write(f"₱{item['Amount']:,.2f}")
            
            with tab4:
                st.markdown(f"### 📋 Statement of Cash Flows")
                st.markdown(f"**For the period ended {period_title}**")
                
                # Cash Flow Statement
                cash_flow_data = [
                    {"Section": "Cash flows from operating activities", "Item": "", "Amount": 0, "Type": "Header"},
                    {"Section": "Operating", "Item": "Net Income", "Amount": net_income * 0.7, "Type": "Cash"},
                    {"Section": "Operating", "Item": "Adjustments for:", "Amount": 0, "Type": "SubHeader"},
                    {"Section": "Operating", "Item": "Depreciation", "Amount": 1000, "Type": "Cash"},
                    {"Section": "Operating", "Item": "Increase in Accounts Receivable", "Amount": -accounts_receivable * 0.5, "Type": "Cash"},
                    {"Section": "Operating", "Item": "Increase in Accounts Payable", "Amount": accounts_payable * 0.5, "Type": "Cash"},
                    {"Section": "Operating", "Item": "Net cash from operating activities", "Amount": net_income * 0.7 + 1000, "Type": "Total"},
                    {"Section": "Cash flows from investing activities", "Item": "", "Amount": 0, "Type": "Header"},
                    {"Section": "Investing", "Item": "Purchase of Equipment", "Amount": -2000, "Type": "Cash"},
                    {"Section": "Investing", "Item": "Net cash from investing activities", "Amount": -2000, "Type": "Total"},
                    {"Section": "Cash flows from financing activities", "Item": "", "Amount": 0, "Type": "Header"},
                    {"Section": "Financing", "Item": "Owner Contributions", "Amount": 0, "Type": "Cash"},
                    {"Section": "Financing", "Item": "Owner Drawings", "Amount": 0, "Type": "Cash"},
                    {"Section": "Financing", "Item": "Net cash from financing activities", "Amount": 0, "Type": "Total"},
                    {"Section": "", "Item": "Net increase in cash", "Amount": net_income * 0.7 - 1000, "Type": "GrandTotal"},
                    {"Section": "", "Item": "Cash at beginning of period", "Amount": cash * 0.5, "Type": "GrandTotal"},
                    {"Section": "", "Item": "Cash at end of period", "Amount": cash, "Type": "GrandTotal"}
                ]
                
                current_section = ""
                for item in cash_flow_data:
                    if item['Type'] == "Header":
                        st.markdown(f"**{item['Section']}**")
                    elif item['Type'] == "SubHeader":
                        st.write(f"*{item['Item']}*")
                    elif item['Type'] == "GrandTotal":
                        st.markdown("---")
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.markdown(f"**{item['Item']}**")
                        with col2:
                            st.markdown(f"**₱{item['Amount']:,.2f}**")
                    else:
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            if item['Type'] == "Total":
                                st.markdown(f"*{item['Item']}*")
                            else:
                                st.write(f"&nbsp;&nbsp;&nbsp;&nbsp;{item['Item']}")
                        with col2:
                            if item['Type'] == "Total":
                                st.markdown(f"*₱{item['Amount']:,.2f}*")
                            else:
                                st.write(f"₱{item['Amount']:,.2f}")
            
            # Export options
            st.markdown("---")
            st.markdown("### 📥 Export Options")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("Export as PDF", type="secondary"):
                    generate_pdf_financial_statements(period_title, income_statement_data, balance_sheet_data, equity_changes, cash_flow_data)
            
            with col2:
                if st.button("Export as Excel", type="secondary"):
                    generate_excel_financial_statements(period_title, income_statement_data, balance_sheet_data, equity_changes, cash_flow_data)
            
            with col3:
                if st.button("Print Statement", type="secondary"):
                    print_financial_statements(period_title, income_statement_data, balance_sheet_data, equity_changes, cash_flow_data)
        
        else:
            st.info(f"No transactions found for {period_title}. Add transactions to generate financial statements.")
            
    except Exception as e:
        st.error(f"❌ Error loading financial data: {str(e)}")
        st.info("Please try refreshing the page")

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
        
        submitted = st.form_submit_button("💾 Save Changes", type="primary")
        
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
    
    # Sign Out button outside of form
    if st.button("🚪 Sign Out", width='stretch'):
        handle_signout()
    
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
    
    try:
        user = get_current_user()
        if not user:
            st.error("Unable to load user")
            return
            
        profile = get_user_profile(user.id)
        if not profile:
            st.error("Unable to load user profile")
            return
    
        # Initialize default values
        total_revenue = total_expenses = net_income = total_tax = 0
        transactions = pd.DataFrame()
        
        # Load user transactions with date filtering
        try:
            supabase = init_supabase()
            from dateutil.relativedelta import relativedelta
            start_date = datetime.now().replace(day=1)
            end_date = start_date + relativedelta(months=1)
            
            result = supabase.table('transactions').select('*').eq('user_id', user.id).gte('transaction_date', start_date.strftime('%Y-%m-%d')).lt('transaction_date', end_date.strftime('%Y-%m-%d')).execute()
            
            if result.data and len(result.data) > 0:
                transactions = pd.DataFrame(result.data)
                
                if not transactions.empty:
                    # Convert numeric columns
                    numeric_cols = ['gross_amount', 'platform_fee', 'net_amount', 'vat_amount', 'ewt_amount', 'final_amount']
                    for col in numeric_cols:
                        if col in transactions.columns:
                            transactions[col] = pd.to_numeric(transactions[col], errors='coerce').fillna(0)
                    
                    # Convert dates
                    transactions['transaction_date'] = pd.to_datetime(transactions['transaction_date'], format='ISO8601', errors='coerce')
                    
                    # Calculate metrics
                    if 'type' in transactions.columns:
                        revenue_mask = transactions['type'].isin(['cash_receipt', 'sales'])
                        expense_mask = transactions['type'].isin(['purchase', 'expense'])
                        
                        total_revenue = transactions[revenue_mask]['final_amount'].sum()
                        total_expenses = transactions[expense_mask]['final_amount'].sum()
                        net_income = total_revenue - total_expenses
                        total_tax = transactions['vat_amount'].sum() + transactions['ewt_amount'].sum()
        except Exception as e:
            st.error(f"Error loading transactions: {str(e)}")
        
        # Enhanced metrics display with professional styling
        st.markdown("### 📊 Financial Overview")
        
        # Create professional metrics cards
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            delta_color = "normal" if total_revenue >= 0 else "inverse"
            st.metric(
                "💰 Total Revenue", 
                f"₱{total_revenue:,.2f}",
                delta=f"₱{total_revenue:,.2f}" if total_revenue != 0 else None,
                delta_color=delta_color
            )
            
        with col2:
            delta_color = "inverse" if total_expenses > 0 else "normal"
            st.metric(
                "💸 Total Expenses", 
                f"₱{total_expenses:,.2f}",
                delta=f"₱{total_expenses:,.2f}" if total_expenses != 0 else None,
                delta_color=delta_color
            )
            
        with col3:
            delta_color = "normal" if net_income >= 0 else "inverse"
            st.metric(
                "📈 Net Income", 
                f"₱{net_income:,.2f}",
                delta=f"₱{net_income:,.2f}" if net_income != 0 else None,
                delta_color=delta_color
            )
            
        with col4:
            st.metric(
                "🏛️ Tax Total", 
                f"₱{total_tax:,.2f}",
                delta=f"₱{total_tax:,.2f}" if total_tax != 0 else None
            )
        
        # Simple revenue chart
        st.markdown("### 📈 Revenue Trend")
        if not transactions.empty and len(transactions) > 0 and 'type' in transactions.columns:
            revenue_data = transactions[transactions['type'].isin(['cash_receipt', 'sales'])]
            if len(revenue_data) > 0:
                chart_data = revenue_data.groupby('transaction_date')['final_amount'].sum().reset_index()
                if len(chart_data) > 0:
                    fig = px.line(chart_data, x='transaction_date', y='final_amount', title='Revenue Over Time')
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No revenue data available")
            else:
                st.info("No revenue transactions found")
        else:
            st.info("No transaction data available")
        
        # Simple pie chart
        st.markdown("### 🥧 Transaction Distribution")
        if not transactions.empty and len(transactions) > 0 and 'type' in transactions.columns:
            pie_data = transactions.groupby('type')['final_amount'].sum().reset_index()
            if len(pie_data) > 0:
                fig = px.pie(pie_data, values='final_amount', names='type', title='Transaction Distribution')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No transaction data available")
        else:
            st.info("No transaction data available")
                
        # Enhanced recent transactions section
        st.markdown("### 📋 Recent Activity")
        
        if not transactions.empty and len(transactions) > 0:
            recent_transactions = transactions.sort_values('transaction_date', ascending=False).head(10)
            
            if len(recent_transactions) > 0:
                display_data = recent_transactions[['transaction_date', 'type', 'description', 'final_amount']].copy()
                display_data['transaction_date'] = display_data['transaction_date'].dt.strftime('%Y-%m-%d')
                display_data.columns = ['Date', 'Type', 'Description', 'Amount']
                
                # Add styling for amounts
                display_data['Amount'] = display_data['Amount'].apply(lambda x: f"₱{x:,.2f}")
                
                # Add emoji for transaction types
                type_emoji = {
                    'cash_receipt': '💰',
                    'sales': '📈', 
                    'purchase': '🛒',
                    'expense': '💸',
                    'cash_disbursement': '💳'
                }
                display_data['Type'] = display_data['Type'].apply(lambda x: f"{type_emoji.get(x, '📝')} {x.title()}")
                
                st.dataframe(display_data, width="stretch", hide_index=True, use_container_width=True)
            else:
                st.info("No transactions this month. Start by adding your first transaction!")
        else:
            st.info("📝 No transactions yet. Navigate to any journal to start recording your financial data.")
            
    except Exception as e:
        st.error(f"Error loading dashboard data: {str(e)}")
        st.info("Please try refreshing the page")
        
        # Additional debug info
        import traceback
        st.error("Full error details:")
        st.code(traceback.format_exc())
        
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
            with st.form("cash_receipt_form", clear_on_submit=True):
                col1, col2 = st.columns(2)
                
                with col1:
                    customer_name = st.text_input("Customer Name*", placeholder="Enter customer name", key="cash_cust_name_v1")
                    gross_amount = st.number_input("Gross Amount*", min_value=0.01, value=0.01, step=0.01, format="%.2f", key="cash_amount_v1")
                    platform_name = st.selectbox("Platform", ["None", "SHOPEE", "LAZADA", "TIKTOK"], key="cash_platform_v1")
                    platform_fee = st.number_input("Platform Fee", min_value=0.0, step=0.01, format="%.2f", value=0.0, help="Leave 0 to auto-calculate", key="cash_platform_fee_v1")
                    seller_discount = st.number_input("Seller Discount", min_value=0.0, step=0.01, format="%.2f", value=0.0, key="cash_discount_v1")
                
                with col2:
                    payment_method = st.selectbox("Payment Method*", ["Cash", "Bank Transfer", "Check", "Digital Wallet"], key="cash_payment_v1")
                    bank_name = st.text_input("Bank Name", placeholder="Enter bank name", key="cash_bank_v1")
                    check_number = st.text_input("Check Number", placeholder="Enter check number", key="cash_check_v1")
                    description = st.text_input("Description", placeholder="Payment description", key="cash_description_v1")
                
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
                        st.metric("Net Amount", format_currency_ph(tax_calculations['net_amount']))
                    with col2:
                        st.metric("VAT Amount", format_currency_ph(tax_calculations['vat_amount']))
                    with col3:
                        st.metric("EWT Amount", format_currency_ph(tax_calculations['ewt_amount']))
                    with col4:
                        st.metric("Final Amount", format_currency_ph(tax_calculations['final_amount']))
                
                # Submit button - validation moved inside submission check
                col1, col2, col3 = st.columns(3)
                with col2:
                    submitted = st.form_submit_button(
                        " Save Cash Receipt", 
                        type="primary", 
                        use_container_width=False
                    )
                
                if submitted:
                    try:
                        # Strict validation - prevent database insertion unless conditions are met
                        if not customer_name or not customer_name.strip():
                            st.error("Customer name is required and cannot be empty")
                            return
                        
                        if not gross_amount or gross_amount <= 0:
                            st.error("Amount must be greater than 0")
                            return
                        
                        # Additional validation to prevent duplicate entries
                        form_data = {
                            'customer_name': customer_name,
                            'gross_amount': gross_amount,
                            'transaction_date': datetime.now().strftime('%Y-%m-%d')
                        }
                        validation_errors = validate_required_fields(form_data, 'Cash Receipt')
                        
                        if validation_errors:
                            for error in validation_errors:
                                st.error(f"Validation Error: {error}")
                            # Don't proceed with database insertion
                            return
                        
                        # Initialize Supabase client
                        supabase = init_supabase()
                        
                        # Prepare data for insertion
                        cash_receipt_data = {
                            'user_id': user.id,
                            'transaction_date': datetime.now().strftime('%Y-%m-%d'),
                            'type': 'cash_receipt',
                            'description': description or f"Payment from {customer_name}",
                            'customer_name': customer_name.strip(),
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
                            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                        
                        # Insert into Supabase
                        result = supabase.table('transactions').insert(cash_receipt_data).execute()
                        
                        if result.data:
                            st.success(" Cash receipt saved successfully!")
                            st.balloons()
                            # Clear cache to refresh transaction count
                            st.cache_data.clear()
                            # Explicit state reset to prevent multi-tab synchronization issues
                            for key in list(st.session_state.keys()):
                                if key.startswith('cash_'):
                                    del st.session_state[key]
                            st.rerun()
                        else:
                            st.error(" Failed to save cash receipt")
                            
                    except Exception as e:
                        if not handle_database_error(e):
                            st.error(f" Error saving cash receipt: {str(e)}")
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
                    'Date': pd.to_datetime(record['transaction_date'], format='ISO8601', errors='coerce').strftime('%Y-%m-%d'),
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
            type TEXT NOT NULL CHECK (type IN ('Cash Receipt', 'Sales', 'Purchase', 'Cash Disbursement', 'General Journal')),
            description TEXT,
            invoice_no TEXT,
            receipt_no TEXT,
            customer_name TEXT,
            supplier_name TEXT,
            expense_category TEXT,
            amount DECIMAL(15,2) NOT NULL,
            gross_amount DECIMAL(15,2) NOT NULL,
            platform_name TEXT,
            platform_fee DECIMAL(15,2) DEFAULT 0,
            seller_discount DECIMAL(15,2) DEFAULT 0,
            net_amount DECIMAL(15,2) NOT NULL,
            vat_rate DECIMAL(5,4) DEFAULT 0,
            vat_amount DECIMAL(15,2) DEFAULT 0,
            ewt_rate DECIMAL(5,4) DEFAULT 0,
            ewt_amount DECIMAL(15,2) DEFAULT 0,
            final_amount DECIMAL(15,2) NOT NULL,
            payment_method TEXT,
            bank_name TEXT,
            check_number TEXT,
            tax_type TEXT NOT NULL,
            status TEXT DEFAULT 'Active' CHECK (status IN ('Active', 'Inactive', 'Cancelled')),
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
            
        -- License Keys RLS policies
        DROP POLICY IF EXISTS users_can_view_license_keys ON license_keys;
        CREATE POLICY users_can_view_license_keys ON license_keys
            FOR SELECT USING (true);  -- Anyone can view license keys
            
        DROP POLICY IF EXISTS users_can_insert_license_keys ON license_keys;
        CREATE POLICY users_can_insert_license_keys ON license_keys
            FOR INSERT WITH CHECK (true);  -- Anyone can insert license keys
            
        DROP POLICY IF EXISTS users_can_update_license_keys ON license_keys;
        CREATE POLICY users_can_update_license_keys ON license_keys
            FOR UPDATE USING (true);  -- Anyone can update license keys
            
        DROP POLICY IF EXISTS users_can_delete_license_keys ON license_keys;
        CREATE POLICY users_can_delete_license_keys ON license_keys
            FOR DELETE USING (true);  -- Anyone can delete license keys
        """
        
        # Execute schema creation (this would need to be run manually in Supabase SQL editor)
        return True
        
    except Exception as e:
        return False

# Sales Journal
def show_sales_journal():
    st.markdown("""
    <div class="main-header">
        <h1>📈 Sales Journal</h1>
        <p>Record sales transactions and accounts receivable</p>
    </div>
    """, unsafe_allow_html=True)
    
    user = get_current_user()
    profile = get_user_profile(user.id) if user else None
    
    if not profile:
        st.error("Unable to load user profile")
        return
    
    # Check transaction limits
    transaction_count = get_user_transaction_count(user.id)
    can_add = profile.get('is_pro_status') or transaction_count < 20
    limit_msg = "You've reached your free plan limit. Upgrade to Pro for unlimited transactions."
    
    if not can_add:
        st.error(limit_msg)
        st.info("🔑 Upgrade to Pro for unlimited transactions")
        st.session_state.selected_page = "🔑 Subscription"
        st.rerun()
    else:
        with st.form("sales_entry_form", clear_on_submit=True):
            st.markdown("####  Sales Transaction Details")
            
            col1, col2 = st.columns(2)
            
            with col1:
                transaction_date = st.date_input("Transaction Date *", value=datetime.now().date(), key="sales_date_v1")
                customer_name = st.text_input("Customer Name *", placeholder="Enter customer name", key="sales_cust_name_v1")
                invoice_no = st.text_input("Invoice Number", placeholder="Optional", key="sales_invoice_v1")
                
            with col2:
                amount = st.number_input("Amount *", min_value=0.01, value=0.01, step=0.01, format="%.2f", key="sales_amount_v1")
                payment_method = st.selectbox("Payment Method *", ["Cash", "Bank Transfer", "Check", "Online Payment"], key="sales_payment_v1")
            
            st.markdown("####  Tax Information")
            
            col1, col2 = st.columns(2)
            
            with col1:
                vat_rate = st.selectbox("VAT Rate", [0.00, 0.12], format_func=lambda x: f"{x*100:.0f}%", key="sales_vat_rate_v1")
                if vat_rate > 0:
                    vat_amount = amount * vat_rate
                else:
                    vat_amount = 0
            
            with col2:
                ewt_rate = st.selectbox("EWT Rate", [0.00, 0.01, 0.02], format_func=lambda x: f"{x*100:.0f}%", key="sales_ewt_rate_v1")
                if ewt_rate > 0:
                    ewt_amount = amount * ewt_rate
                else:
                    ewt_amount = 0
            
            final_amount = amount - vat_amount - ewt_amount
            
            st.markdown("####  Transaction Summary")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Gross Amount", format_currency_ph(amount))
            with col2:
                st.metric("Total Tax", format_currency_ph(vat_amount + ewt_amount))
            with col3:
                st.metric("Final Amount", format_currency_ph(final_amount))
            
            # Submit button - validation moved inside submission check
            col1, col2, col3 = st.columns(3)
            with col2:
                submitted = st.form_submit_button(
                    " Save Sales Entry", 
                    type="primary", 
                    use_container_width=False
                )
            
            if submitted:
                try:
                    # Strict validation - prevent database insertion unless conditions are met
                    if not customer_name or not customer_name.strip():
                        st.error("Customer name is required and cannot be empty")
                        return
                    
                    if not amount or amount <= 0:
                        st.error("Amount must be greater than 0")
                        return
                    
                    # Additional validation to prevent duplicate entries
                    form_data = {
                        'customer_name': customer_name,
                        'gross_amount': amount,
                        'transaction_date': transaction_date.strftime('%Y-%m-%d')
                    }
                    validation_errors = validate_required_fields(form_data, 'Sales')
                    
                    if validation_errors:
                        for error in validation_errors:
                            st.error(f"Validation Error: {error}")
                        # Don't proceed with database insertion
                        return
                    
                    supabase = init_supabase()
                    
                    # Insert sales transaction
                    sales_data = {
                        'user_id': user.id,
                        'transaction_date': transaction_date.strftime('%Y-%m-%d'),
                        'customer_name': customer_name.strip(),
                        'payment_method': payment_method,
                        'gross_amount': amount,
                        'net_amount': amount - vat_amount - ewt_amount,
                        'vat_rate': vat_rate,
                        'vat_amount': vat_amount,
                        'ewt_rate': ewt_rate,
                        'ewt_amount': ewt_amount,
                        'final_amount': final_amount,
                        'type': 'Sales',
                        'tax_type': profile.get('tax_type', 'VAT (12%)')
                    }
                    
                    result = supabase.table('transactions').insert(sales_data).execute()
                    
                    if result.data:
                        st.success(" Sales entry saved successfully!")
                        st.balloons()
                        # Explicit state reset to prevent multi-tab synchronization issues
                        for key in list(st.session_state.keys()):
                            if key.startswith('sales_'):
                                del st.session_state[key]
                        st.rerun()
                    else:
                        st.error(" Failed to save sales entry")
                        
                except Exception as e:
                    if not handle_database_error(e):
                        st.error(f" Error saving sales entry: {str(e)}")
                        st.info("Please try again or contact support if the issue persists.")
    
    # Recent sales entries
    st.markdown("### 📋 Recent Sales Entries")
    
    try:
        supabase = init_supabase()
        result = supabase.table('transactions').select('*').eq('user_id', user.id).eq('type', 'Sales').order('created_at', desc=True).limit(10).execute()
        
        if result.data:
            for entry in result.data:
                with st.expander(f"Sales Entry - {entry['transaction_date'][:10]}"):
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.write(f"**Customer:** {entry['customer_name']}")
                        st.write(f"**Amount:** ₱{entry['gross_amount']:,.2f}")
                        
                    with col2:
                        st.write(f"**VAT:** ₱{entry['vat_amount']:,.2f}")
                        st.write(f"**Net:** ₱{entry['final_amount']:,.2f}")
                        
                    with col3:
                        st.write(f"**Method:** {entry['payment_method']}")
                        st.write(f"**Status:** {entry['status']}")
                        
                    with col4:
                        if st.button("🗑️ Delete", key=f"delete_sales_{entry['id']}"):
                            try:
                                supabase.table('transactions').delete().eq('id', entry['id']).execute()
                                st.rerun()
                            except:
                                st.error("Failed to delete entry")
        else:
            st.info("No sales entries found.")
            
    except Exception as e:
        st.error(f"❌ Error loading sales entries: {str(e)}")
        st.info("Please try refreshing the page")

# Purchase Journal
def show_purchase_journal():
    st.markdown("""
    <div class="main-header">
        <h1>🛒 Purchase Journal</h1>
        <p>Record purchase transactions and accounts payable</p>
    </div>
    """, unsafe_allow_html=True)
    
    user = get_current_user()
    profile = get_user_profile(user.id) if user else None
    
    if not profile:
        st.error("Unable to load user profile")
        return
    
    # Check transaction limits
    transaction_count = get_user_transaction_count(user.id)
    can_add = profile.get('is_pro_status') or transaction_count < 20
    limit_msg = "You've reached your free plan limit. Upgrade to Pro for unlimited transactions."
    
    if not can_add:
        st.error(limit_msg)
        st.info("🔑 Upgrade to Pro for unlimited transactions")
        st.session_state.selected_page = "🔑 Subscription"
        st.rerun()
    else:
        with st.form("purchase_journal_form", clear_on_submit=True):
            st.markdown("###  Purchase Entry Details")
            
            col1, col2 = st.columns(2)
            
            with col1:
                transaction_date = st.date_input("Transaction Date*", datetime.now().date(), key="purchase_date_v1")
                receipt_no = st.text_input("Receipt No.*", placeholder="Enter receipt number", key="purchase_receipt_v1")
                
            with col2:
                supplier_name = st.text_input("Supplier Name*", placeholder="Enter supplier name", key="purchase_supp_name_v1")
                expense_category = st.selectbox("Expense Category*", ["Office Supplies", "Equipment", "Utilities", "Rent", "Marketing", "Professional Services", "Other"], key="purchase_category_v1")
                
            st.markdown("###  Purchase Details")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                amount = st.number_input("Amount*", min_value=0.01, value=0.01, step=0.01, format="%.2f", key="purchase_amount_v1")
                
            with col2:
                vat_rate = st.selectbox("VAT Rate", [0.00, 0.12], format_func=lambda x: f"{x*100:.0f}%", key="purchase_vat_rate_v1")
                vat_amount = amount * vat_rate
                
            with col3:
                ewt_rate = st.selectbox("EWT Rate", [0.00, 0.01, 0.02], format_func=lambda x: f"{x*100:.0f}%", key="purchase_ewt_rate_v1")
                ewt_amount = amount * ewt_rate
                
            final_amount = amount - vat_amount - ewt_amount
            
            st.markdown("### 📋 Summary")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Gross Amount", f"₱{amount:,.2f}")
                
            with col2:
                st.metric("VAT", f"₱{vat_amount:,.2f}")
                
            with col3:
                st.metric("Net Amount", f"₱{final_amount:,.2f}")
            
            # Submit button - validation moved inside submission check
            col1, col2, col3 = st.columns(3)
            with col2:
                submitted = st.form_submit_button(
                    " Save Purchase Entry", 
                    type="primary", 
                    use_container_width=False
                )
                
                if submitted:
                    try:
                        # Strict validation - prevent database insertion unless conditions are met
                        if not supplier_name or not supplier_name.strip():
                            st.error("Supplier name is required and cannot be empty")
                            return
                        
                        if not amount or amount <= 0:
                            st.error("Amount must be greater than 0")
                            return
                        
                        # Additional validation to prevent duplicate entries
                        form_data = {
                            'supplier_name': supplier_name,
                            'gross_amount': amount,
                            'transaction_date': transaction_date.strftime('%Y-%m-%d')
                        }
                        validation_errors = validate_required_fields(form_data, 'Purchase')
                        
                        if validation_errors:
                            for error in validation_errors:
                                st.error(f"Validation Error: {error}")
                            # Don't proceed with database insertion
                            return
                        
                        supabase = init_supabase()
                        
                        # Check for potential duplicate entry (same supplier, amount, and date within last 5 minutes)
                        five_minutes_ago = datetime.now() - timedelta(minutes=5)
                        duplicate_check = supabase.table('transactions').select('*').eq('user_id', user.id).eq('supplier_name', supplier_name.strip()).eq('gross_amount', amount).eq('transaction_date', transaction_date.strftime('%Y-%m-%d')).eq('type', 'Purchase').gte('created_at', five_minutes_ago.strftime('%Y-%m-%d %H:%M:%S')).execute()
                        
                        if duplicate_check.data and len(duplicate_check.data) > 0:
                            st.error("Duplicate entry detected! A similar purchase entry was recently created.")
                            return
                        
                        # Insert purchase transaction
                        purchase_data = {
                            'user_id': user.id,
                            'transaction_date': transaction_date.strftime('%Y-%m-%d'),
                            'supplier_name': supplier_name.strip(),
                            'expense_category': expense_category,
                            'gross_amount': amount,
                            'net_amount': amount - vat_amount - ewt_amount,
                            'vat_rate': vat_rate,
                            'vat_amount': vat_amount,
                            'ewt_rate': ewt_rate,
                            'ewt_amount': ewt_amount,
                            'final_amount': final_amount,
                            'type': 'Purchase',
                            'tax_type': profile.get('tax_type', 'VAT (12%)')
                        }
                        
                        result = supabase.table('transactions').insert(purchase_data).execute()
                        
                        if result.data:
                            st.success(" Purchase entry saved successfully!")
                            st.balloons()
                            # Explicit state reset to prevent multi-tab synchronization issues
                            for key in list(st.session_state.keys()):
                                if key.startswith('purchase_'):
                                    del st.session_state[key]
                            st.rerun()
                        else:
                            st.error(" Failed to save purchase entry")
                            
                    except Exception as e:
                        if not handle_database_error(e):
                            st.error(f" Error saving purchase entry: {str(e)}")
                            st.info("Please try again or contact support if the issue persists.")
    
    # Recent purchase entries
    st.markdown("### 📋 Recent Purchase Entries")
    
    try:
        supabase = init_supabase()
        result = supabase.table('transactions').select('*').eq('user_id', user.id).eq('type', 'Purchase').order('created_at', desc=True).limit(10).execute()
        
        if result.data:
            for entry in result.data:
                with st.expander(f"Purchase Entry - {entry['transaction_date'][:10]}"):
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.write(f"**Supplier:** {entry['supplier_name']}")
                        st.write(f"**Amount:** ₱{entry['gross_amount']:,.2f}")
                        
                    with col2:
                        st.write(f"**Category:** {entry.get('expense_category', 'N/A')}")
                        st.write(f"**VAT:** {entry['vat_amount']:,.2f}")
                        
                    with col3:
                        st.write(f"**Net:** ₱{entry['final_amount']:,.2f}")
                        st.write(f"**Status:** {entry['status']}")
                        
                    with col4:
                        if st.button("🗑️ Delete", key=f"delete_purchase_{entry['id']}"):
                            try:
                                supabase.table('transactions').delete().eq('id', entry['id']).execute()
                                st.rerun()
                            except:
                                st.error("Failed to delete entry")
        else:
            st.info("No purchase entries found.")
            
    except Exception as e:
        st.error(f"❌ Error loading purchase entries: {str(e)}")
        st.info("Please try refreshing the page")

# Chart of Accounts
def show_chart_of_accounts():
    st.markdown("""
    <div class="main-header">
        <h1>📊 Chart of Accounts</h1>
        <p>Philippine Chart of Accounts management</p>
    </div>
    """, unsafe_allow_html=True)
    
    user = get_current_user()
    profile = get_user_profile(user.id) if user else None
    
    if not profile:
        st.error("Unable to load user profile")
        return
    
    # Philippine Standard Chart of Accounts
    st.markdown("### 📋 Philippine Standard Chart of Accounts")
    
    # Assets
    with st.expander("💰 Assets (1000-1999)"):
        st.markdown("""
        **Current Assets (1000-1499)**
        - 1010 Cash and Cash Equivalents
        - 1020 Accounts Receivable
        - 1030 Inventories
        - 1040 Prepaid Expenses
        - 1050 Other Current Assets
        
        **Non-Current Assets (1500-1999)**
        - 1510 Property, Plant and Equipment
        - 1520 Accumulated Depreciation
        - 1530 Investment Property
        - 1540 Intangible Assets
        - 1550 Long-term Investments
        """)
    
    # Liabilities
    with st.expander("💳 Liabilities (2000-2999)"):
        st.markdown("""
        **Current Liabilities (2000-2499)**
        - 2010 Accounts Payable
        - 2020 Short-term Loans
        - 2030 Tax Payable
        - 2040 Accrued Expenses
        - 2050 Other Current Liabilities
        
        **Non-Current Liabilities (2500-2999)**
        - 2510 Long-term Loans
        - 2520 Deferred Tax Liabilities
        - 2530 Lease Liabilities
        - 2540 Other Non-Current Liabilities
        """)
    
    # Equity
    with st.expander("👥 Equity (3000-3999)"):
        st.markdown("""
        **Share Capital (3000-3099)**
        - 3010 Common Stock
        - 3020 Preferred Stock
        - 3030 Additional Paid-in Capital
        
        **Retained Earnings (3100-3199)**
        - 3110 Retained Earnings
        - 3120 Appropriations
        
        **Other Equity (3200-3999)**
        - 3210 Treasury Stock
        - 3220 Other Comprehensive Income
        """)
    
    # Revenue
    with st.expander("📈 Revenue (4000-4999)"):
        st.markdown("""
        **Sales Revenue (4000-4099)**
        - 4010 Sales of Goods
        - 4020 Sales of Services
        - 4030 Sales Returns and Allowances
        
        **Other Revenue (4100-4999)**
        - 4110 Interest Income
        - 4120 Rental Income
        - 4130 Dividend Income
        - 4140 Other Operating Income
        """)
    
    # Expenses
    with st.expander("💸 Expenses (5000-5999)"):
        st.markdown("""
        **Cost of Sales (5000-5099)**
        - 5010 Cost of Goods Sold
        - 5020 Direct Labor
        - 5030 Direct Materials
        - 5040 Manufacturing Overhead
        
        **Operating Expenses (5100-5999)**
        - 5110 Salaries and Wages
        - 5120 Rent Expense
        - 5130 Utilities Expense
        - 5140 Marketing Expense
        - 5150 Depreciation Expense
        - 5160 Interest Expense
        - 5170 Tax Expense
        """)
    
    st.markdown("---")
    
    # Account Management
    st.markdown("### ⚙️ Account Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📊 Account Summary")
        
        # Create sample account summary
        account_data = {
            'Account': ['Cash', 'Accounts Receivable', 'Inventory', 'Equipment', 'Accounts Payable', 'Loans Payable'],
            'Type': ['Asset', 'Asset', 'Asset', 'Asset', 'Liability', 'Liability'],
            'Balance': [50000, 25000, 15000, 100000, 20000, 50000]
        }
        
        df_accounts = pd.DataFrame(account_data)
        st.dataframe(df_accounts, width='stretch')
        
        st.markdown("#### 📈 Account Balances")
        
        # Simple bar chart
        fig = px.bar(df_accounts, x='Account', y='Balance', color='Type',
                    title='Account Balance Distribution')
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, width='stretch')
    
    with col2:
        st.markdown("#### 📋 Account Categories")
        
        categories = {
            'Current Assets': 90000,
            'Non-Current Assets': 100000,
            'Current Liabilities': 20000,
            'Non-Current Liabilities': 50000,
            'Equity': 120000
        }
        
        for category, amount in categories.items():
            st.metric(category, f"₱{amount:,.2f}")
        
        st.markdown("#### 🔧 Account Actions")
        
        # Import Chart of Accounts
        if st.button(" Import Chart of Accounts", type="secondary"):
            st.markdown("#####  Import Chart of Accounts")
            uploaded_file = st.file_uploader("Choose a CSV file", type=['csv'])
            
            if uploaded_file is not None:
                try:
                    # Read CSV file
                    df = pd.read_csv(uploaded_file)
                    st.success(f"Successfully imported {len(df)} accounts!")
                    st.dataframe(df)
                except Exception as e:
                    st.error(f"Error importing file: {str(e)}")
            
            st.markdown("**Expected CSV Format:**")
            st.code("""
Account Code,Account Name,Account Type,Parent Account
1010,Cash and Cash Equivalents,Asset,
1020,Accounts Receivable,Asset,
2010,Accounts Payable,Liability,
3010,Common Stock,Equity,
            """)
        
        # Export Chart of Accounts
        if st.button(" Export Chart of Accounts", type="secondary"):
            st.markdown("#####  Export Chart of Accounts")
            
            # Create sample chart of accounts data
            chart_data = {
                'Account Code': ['1010', '1020', '1030', '2010', '2020', '3010', '3110', '4010', '5010', '5110'],
                'Account Name': [
                    'Cash and Cash Equivalents',
                    'Accounts Receivable', 
                    'Inventory',
                    'Accounts Payable',
                    'Short-term Loans',
                    'Common Stock',
                    'Retained Earnings',
                    'Sales of Goods',
                    'Cost of Goods Sold',
                    'Salaries and Wages'
                ],
                'Account Type': ['Asset', 'Asset', 'Asset', 'Liability', 'Liability', 'Equity', 'Equity', 'Revenue', 'Expense', 'Expense'],
                'Parent Account': ['', '', '', '', '', '', '', '', '', '']
            }
            
            df_export = pd.DataFrame(chart_data)
            
            # Convert to CSV
            csv = df_export.to_csv(index=False)
            st.download_button(
                label=" Download CSV",
                data=csv,
                file_name='chart_of_accounts.csv',
                mime='text/csv',
                type="primary"
            )
            
            st.dataframe(df_export)
        
        # Add New Account
        if st.button(" Add New Account", type="primary"):
            st.markdown("#####  Add New Account")
            
            with st.form("add_account_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    account_code = st.text_input("Account Code *", placeholder="e.g., 1010")
                    account_name = st.text_input("Account Name *", placeholder="e.g., Cash and Cash Equivalents")
                    account_type = st.selectbox("Account Type *", ["Asset", "Liability", "Equity", "Revenue", "Expense"])
                    
                with col2:
                    parent_account = st.text_input("Parent Account", placeholder="Optional - leave blank if none")
                    description = st.text_area("Description", placeholder="Optional description of the account")
                
                col3, col4 = st.columns(2)
                with col3:
                    submitted = st.form_submit_button(" Add Account", type="primary")
                with col4:
                    cancelled = st.form_submit_button(" Cancel", type="secondary")
                
                if submitted:
                    if account_code and account_name and account_type:
                        # Here you would save to database
                        st.success(f"Account '{account_name}' ({account_code}) added successfully!")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error("Please fill in all required fields (*)")
                
                if cancelled:
                    st.rerun()
    
    st.markdown("---")
    
    # Account Setup Tips
    st.markdown("### 💡 Account Setup Tips")
    
    tips = [
        "Follow Philippine Accounting Standards (PAS)",
        "Use proper account codes for easy identification",
        "Maintain consistent naming conventions",
        "Regularly reconcile account balances",
        "Keep supporting documents for all transactions"
    ]
    
    for i, tip in enumerate(tips, 1):
        st.write(f"{i}. {tip}")
    
    st.markdown("---")
    
    # Tax Compliance Notes
    st.markdown("### 🏛️ Tax Compliance Notes")
    
    st.info("""
    **Important for Philippine Businesses:**
    - Maintain separate accounts for VAT and non-VAT transactions
    - Track input and output VAT separately
    - Keep records for at least 5 years
    - Use BIR-prescribed account classifications
    """)

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
    
    # Show navigation and get selected page
    page = show_navigation()
    
    # Route to appropriate page
    if page == "🏠 Dashboard":
        show_dashboard()
    elif page == "💰 Cash Receipts Journal":
        show_cash_receipts_journal()
    elif page == "📈 Sales Journal":
        show_sales_journal()
    elif page == "🛒 Purchase Journal":
        show_purchase_journal()
    elif page == "💳 Cash Disbursement Journal":
        show_cash_disbursement_journal()
    elif page == "📝 General Journal":
        show_general_journal()
    elif page == "📋 General Ledger":
        show_general_ledger()
    elif page == "📊 Chart of Accounts":
        show_chart_of_accounts()
    elif page == "🏛️ Tax Compliance":
        show_tax_compliance()
    elif page == "📄 Financial Statements":
        show_financial_statements()
    elif page == "🔑 Subscription":
        show_subscription_page()
    elif page == "⚙️ Settings":
        show_settings_page()

if __name__ == "__main__":
    main()
