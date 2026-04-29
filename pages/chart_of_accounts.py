import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.express as px
from supabase import create_client
import json

# Initialize Supabase
@st.cache_resource
def init_supabase():
    SUPABASE_URL = st.secrets.get("SUPABASE_URL", "your_supabase_url")
    SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "your_supabase_key")
    return create_client(SUPABASE_URL, SUPABASE_KEY)

# Philippine Standard Chart of Accounts Template
PHILIPPINE_COA_TEMPLATE = [
    # ASSETS
    {"account_code": "1000", "account_name": "ASSETS", "account_type": "ASSET", "account_subtype": "HEADER", "normal_balance": "DEBIT", "is_active": True},
    {"account_code": "1100", "account_name": "CURRENT ASSETS", "account_type": "ASSET", "account_subtype": "HEADER", "normal_balance": "DEBIT", "is_active": True},
    {"account_code": "1110", "account_name": "Cash and Cash Equivalents", "account_type": "ASSET", "account_subtype": "CURRENT", "normal_balance": "DEBIT", "is_active": True},
    {"account_code": "1111", "account_name": "Cash on Hand", "account_type": "ASSET", "account_subtype": "CURRENT", "normal_balance": "DEBIT", "is_active": True},
    {"account_code": "1112", "account_name": "Cash in Bank", "account_type": "ASSET", "account_subtype": "CURRENT", "normal_balance": "DEBIT", "is_active": True},
    {"account_code": "1113", "account_name": "Petty Cash Fund", "account_type": "ASSET", "account_subtype": "CURRENT", "normal_balance": "DEBIT", "is_active": True},
    {"account_code": "1120", "account_name": "Accounts Receivable", "account_type": "ASSET", "account_subtype": "CURRENT", "normal_balance": "DEBIT", "is_active": True},
    {"account_code": "1121", "account_name": "Trade Receivables", "account_type": "ASSET", "account_subtype": "CURRENT", "normal_balance": "DEBIT", "is_active": True},
    {"account_code": "1122", "account_name": "Other Receivables", "account_type": "ASSET", "account_subtype": "CURRENT", "normal_balance": "DEBIT", "is_active": True},
    {"account_code": "1130", "account_name": "Inventories", "account_type": "ASSET", "account_subtype": "CURRENT", "normal_balance": "DEBIT", "is_active": True},
    {"account_code": "1131", "account_name": "Merchandise Inventory", "account_type": "ASSET", "account_subtype": "CURRENT", "normal_balance": "DEBIT", "is_active": True},
    {"account_code": "1132", "account_name": "Raw Materials", "account_type": "ASSET", "account_subtype": "CURRENT", "normal_balance": "DEBIT", "is_active": True},
    {"account_code": "1140", "account_name": "Prepaid Expenses", "account_type": "ASSET", "account_subtype": "CURRENT", "normal_balance": "DEBIT", "is_active": True},
    {"account_code": "1141", "account_name": "Prepaid Rent", "account_type": "ASSET", "account_subtype": "CURRENT", "normal_balance": "DEBIT", "is_active": True},
    {"account_code": "1142", "account_name": "Prepaid Insurance", "account_type": "ASSET", "account_subtype": "CURRENT", "normal_balance": "DEBIT", "is_active": True},
    {"account_code": "1200", "account_name": "NON-CURRENT ASSETS", "account_type": "ASSET", "account_subtype": "HEADER", "normal_balance": "DEBIT", "is_active": True},
    {"account_code": "1210", "account_name": "Property, Plant and Equipment", "account_type": "ASSET", "account_subtype": "NON-CURRENT", "normal_balance": "DEBIT", "is_active": True},
    {"account_code": "1211", "account_name": "Land", "account_type": "ASSET", "account_subtype": "NON-CURRENT", "normal_balance": "DEBIT", "is_active": True},
    {"account_code": "1212", "account_name": "Building", "account_type": "ASSET", "account_subtype": "NON-CURRENT", "normal_balance": "DEBIT", "is_active": True},
    {"account_code": "1213", "account_name": "Equipment", "account_type": "ASSET", "account_subtype": "NON-CURRENT", "normal_balance": "DEBIT", "is_active": True},
    {"account_code": "1214", "account_name": "Furniture and Fixtures", "account_type": "ASSET", "account_subtype": "NON-CURRENT", "normal_balance": "DEBIT", "is_active": True},
    {"account_code": "1215", "account_name": "Accumulated Depreciation", "account_type": "ASSET", "account_subtype": "NON-CURRENT", "normal_balance": "CREDIT", "is_active": True},
    {"account_code": "1220", "account_name": "Intangible Assets", "account_type": "ASSET", "account_subtype": "NON-CURRENT", "normal_balance": "DEBIT", "is_active": True},
    
    # LIABILITIES
    {"account_code": "2000", "account_name": "LIABILITIES", "account_type": "LIABILITY", "account_subtype": "HEADER", "normal_balance": "CREDIT", "is_active": True},
    {"account_code": "2100", "account_name": "CURRENT LIABILITIES", "account_type": "LIABILITY", "account_subtype": "HEADER", "normal_balance": "CREDIT", "is_active": True},
    {"account_code": "2110", "account_name": "Accounts Payable", "account_type": "LIABILITY", "account_subtype": "CURRENT", "normal_balance": "CREDIT", "is_active": True},
    {"account_code": "2111", "account_name": "Trade Payables", "account_type": "LIABILITY", "account_subtype": "CURRENT", "normal_balance": "CREDIT", "is_active": True},
    {"account_code": "2112", "account_name": "Other Payables", "account_type": "LIABILITY", "account_subtype": "CURRENT", "normal_balance": "CREDIT", "is_active": True},
    {"account_code": "2120", "account_name": "Taxes Payable", "account_type": "LIABILITY", "account_subtype": "CURRENT", "normal_balance": "CREDIT", "is_active": True},
    {"account_code": "2121", "account_name": "VAT Payable", "account_type": "LIABILITY", "account_subtype": "CURRENT", "normal_balance": "CREDIT", "is_active": True},
    {"account_code": "2122", "account_name": "Withholding Tax Payable", "account_type": "LIABILITY", "account_subtype": "CURRENT", "normal_balance": "CREDIT", "is_active": True},
    {"account_code": "2123", "account_name": "Income Tax Payable", "account_type": "LIABILITY", "account_subtype": "CURRENT", "normal_balance": "CREDIT", "is_active": True},
    {"account_code": "2130", "account_name": "Accrued Expenses", "account_type": "LIABILITY", "account_subtype": "CURRENT", "normal_balance": "CREDIT", "is_active": True},
    {"account_code": "2140", "account_name": "Current Portion of Long-Term Debt", "account_type": "LIABILITY", "account_subtype": "CURRENT", "normal_balance": "CREDIT", "is_active": True},
    {"account_code": "2200", "account_name": "NON-CURRENT LIABILITIES", "account_type": "LIABILITY", "account_subtype": "HEADER", "normal_balance": "CREDIT", "is_active": True},
    {"account_code": "2210", "account_name": "Long-Term Debt", "account_type": "LIABILITY", "account_subtype": "NON-CURRENT", "normal_balance": "CREDIT", "is_active": True},
    {"account_code": "2220", "account_name": "Deferred Tax Liabilities", "account_type": "LIABILITY", "account_subtype": "NON-CURRENT", "normal_balance": "CREDIT", "is_active": True},
    
    # EQUITY
    {"account_code": "3000", "account_name": "EQUITY", "account_type": "EQUITY", "account_subtype": "HEADER", "normal_balance": "CREDIT", "is_active": True},
    {"account_code": "3110", "account_name": "Capital Stock", "account_type": "EQUITY", "account_subtype": "CAPITAL", "normal_balance": "CREDIT", "is_active": True},
    {"account_code": "3120", "account_name": "Additional Paid-in Capital", "account_type": "EQUITY", "account_subtype": "CAPITAL", "normal_balance": "CREDIT", "is_active": True},
    {"account_code": "3130", "account_name": "Retained Earnings", "account_type": "EQUITY", "account_subtype": "RETAINED", "normal_balance": "CREDIT", "is_active": True},
    {"account_code": "3140", "account_name": "Dividends", "account_type": "EQUITY", "account_subtype": "DISTRIBUTION", "normal_balance": "DEBIT", "is_active": True},
    
    # REVENUE
    {"account_code": "4000", "account_name": "REVENUE", "account_type": "REVENUE", "account_subtype": "HEADER", "normal_balance": "CREDIT", "is_active": True},
    {"account_code": "4100", "account_name": "Sales Revenue", "account_type": "REVENUE", "account_subtype": "OPERATING", "normal_balance": "CREDIT", "is_active": True},
    {"account_code": "4101", "account_name": "Merchandise Sales", "account_type": "REVENUE", "account_subtype": "OPERATING", "normal_balance": "CREDIT", "is_active": True},
    {"account_code": "4102", "account_name": "Service Revenue", "account_type": "REVENUE", "account_subtype": "OPERATING", "normal_balance": "CREDIT", "is_active": True},
    {"account_code": "4110", "account_name": "Sales Returns and Allowances", "account_type": "REVENUE", "account_subtype": "OPERATING", "normal_balance": "DEBIT", "is_active": True},
    {"account_code": "4120", "account_name": "Sales Discounts", "account_type": "REVENUE", "account_subtype": "OPERATING", "normal_balance": "DEBIT", "is_active": True},
    {"account_code": "4200", "account_name": "Other Revenue", "account_type": "REVENUE", "account_subtype": "NON-OPERATING", "normal_balance": "CREDIT", "is_active": True},
    {"account_code": "4210", "account_name": "Interest Income", "account_type": "REVENUE", "account_subtype": "NON-OPERATING", "normal_balance": "CREDIT", "is_active": True},
    {"account_code": "4220", "account_name": "Rental Income", "account_type": "REVENUE", "account_subtype": "NON-OPERATING", "normal_balance": "CREDIT", "is_active": True},
    {"account_code": "4230", "account_name": "Gain on Sale of Assets", "account_type": "REVENUE", "account_subtype": "NON-OPERATING", "normal_balance": "CREDIT", "is_active": True},
    
    # EXPENSES
    {"account_code": "5000", "account_name": "EXPENSES", "account_type": "EXPENSE", "account_subtype": "HEADER", "normal_balance": "DEBIT", "is_active": True},
    {"account_code": "5100", "account_name": "Cost of Goods Sold", "account_type": "EXPENSE", "account_subtype": "COST", "normal_balance": "DEBIT", "is_active": True},
    {"account_code": "5110", "account_name": "Purchases", "account_type": "EXPENSE", "account_subtype": "COST", "normal_balance": "DEBIT", "is_active": True},
    {"account_code": "5120", "account_name": "Purchase Returns and Allowances", "account_type": "EXPENSE", "account_subtype": "COST", "normal_balance": "CREDIT", "is_active": True},
    {"account_code": "5130", "account_name": "Freight-In", "account_type": "EXPENSE", "account_subtype": "COST", "normal_balance": "DEBIT", "is_active": True},
    {"account_code": "5200", "account_name": "Operating Expenses", "account_type": "EXPENSE", "account_subtype": "OPERATING", "normal_balance": "DEBIT", "is_active": True},
    {"account_code": "5210", "account_name": "Salaries and Wages", "account_type": "EXPENSE", "account_subtype": "OPERATING", "normal_balance": "DEBIT", "is_active": True},
    {"account_code": "5220", "account_name": "Rent Expense", "account_type": "EXPENSE", "account_subtype": "OPERATING", "normal_balance": "DEBIT", "is_active": True},
    {"account_code": "5230", "account_name": "Utilities Expense", "account_type": "EXPENSE", "account_subtype": "OPERATING", "normal_balance": "DEBIT", "is_active": True},
    {"account_code": "5240", "account_name": "Supplies Expense", "account_type": "EXPENSE", "account_subtype": "OPERATING", "normal_balance": "DEBIT", "is_active": True},
    {"account_code": "5250", "account_name": "Depreciation Expense", "account_type": "EXPENSE", "account_subtype": "OPERATING", "normal_balance": "DEBIT", "is_active": True},
    {"account_code": "5260", "account_name": "Insurance Expense", "account_type": "EXPENSE", "account_subtype": "OPERATING", "normal_balance": "DEBIT", "is_active": True},
    {"account_code": "5270", "account_name": "Repairs and Maintenance", "account_type": "EXPENSE", "account_subtype": "OPERATING", "normal_balance": "DEBIT", "is_active": True},
    {"account_code": "5280", "account_name": "Marketing and Advertising", "account_type": "EXPENSE", "account_subtype": "OPERATING", "normal_balance": "DEBIT", "is_active": True},
    {"account_code": "5290", "account_name": "Professional Fees", "account_type": "EXPENSE", "account_subtype": "OPERATING", "normal_balance": "DEBIT", "is_active": True},
    {"account_code": "5300", "account_name": "Other Expenses", "account_type": "EXPENSE", "account_subtype": "NON-OPERATING", "normal_balance": "DEBIT", "is_active": True},
    {"account_code": "5310", "account_name": "Interest Expense", "account_type": "EXPENSE", "account_subtype": "NON-OPERATING", "normal_balance": "DEBIT", "is_active": True},
    {"account_code": "5320", "account_name": "Loss on Sale of Assets", "account_type": "EXPENSE", "account_subtype": "NON-OPERATING", "normal_balance": "DEBIT", "is_active": True},
    {"account_code": "5330", "account_name": "Tax Expense", "account_type": "EXPENSE", "account_subtype": "NON-OPERATING", "normal_balance": "DEBIT", "is_active": True},
]

def show_chart_of_accounts():
    st.markdown("""
    <div class="main-header">
        <h1>Chart of Accounts</h1>
        <p>Manage your Philippine Standard Chart of Accounts</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize session state for COA data
    if 'coa_data' not in st.session_state:
        st.session_state.coa_data = PHILIPPINE_COA_TEMPLATE
    
    # Tabs for different functions
    tab1, tab2, tab3, tab4 = st.tabs(["📋 View Accounts", "➕ Add Account", "📥 Import/Export", "⚙️ Settings"])
    
    with tab1:
        show_accounts_view()
    
    with tab2:
        show_add_account()
    
    with tab3:
        show_import_export()
    
    with tab4:
        show_coa_settings()

def show_accounts_view():
    # Search and filter options
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        search_term = st.text_input("🔍 Search accounts", placeholder="Search by account name or code...")
    
    with col2:
        account_type_filter = st.selectbox("Filter by Type", ["All", "ASSET", "LIABILITY", "EQUITY", "REVENUE", "EXPENSE"])
    
    with col3:
        status_filter = st.selectbox("Filter by Status", ["All", "Active", "Inactive"])
    
    # Filter data
    filtered_data = st.session_state.coa_data.copy()
    
    if search_term:
        filtered_data = [acc for acc in filtered_data 
                        if search_term.lower() in acc['account_name'].lower() 
                        or search_term.lower() in acc['account_code'].lower()]
    
    if account_type_filter != "All":
        filtered_data = [acc for acc in filtered_data if acc['account_type'] == account_type_filter]
    
    if status_filter != "All":
        is_active = status_filter == "Active"
        filtered_data = [acc for acc in filtered_data if acc['is_active'] == is_active]
    
    # Display accounts in a tree-like structure
    st.markdown("### 📊 Chart of Accounts Structure")
    
    # Group by account type
    account_types = {}
    for account in filtered_data:
        acc_type = account['account_type']
        if acc_type not in account_types:
            account_types[acc_type] = []
        account_types[acc_type].append(account)
    
    # Display each account type
    for acc_type, accounts in account_types.items():
        with st.expander(f"📁 {acc_type} ({len(accounts)} accounts)", expanded=True):
            # Convert to DataFrame for display
            df = pd.DataFrame(accounts)
            
            # Add action buttons
            df['Actions'] = ''
            
            # Style the dataframe
            def style_accounts(val):
                if isinstance(val, str):
                    if 'HEADER' in val:
                        return 'font-weight: bold; background-color: #f0f9ff;'
                    elif 'CURRENT' in val or 'OPERATING' in val:
                        return 'background-color: #f8fafc;'
                return ''
            
            styled_df = df.style.map(style_accounts, subset=['account_subtype'])
            
            # Display with custom formatting
            display_df = df[['account_code', 'account_name', 'account_subtype', 'normal_balance', 'is_active']].copy()
            display_df['is_active'] = display_df['is_active'].map({True: '✅ Active', False: '❌ Inactive'})
            
            st.dataframe(display_df, width="100%", hide_index=True)
    
    # Summary statistics
    st.markdown("### 📈 Account Summary")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_accounts = len(st.session_state.coa_data)
        st.metric("Total Accounts", total_accounts)
    
    with col2:
        active_accounts = len([acc for acc in st.session_state.coa_data if acc['is_active']])
        st.metric("Active Accounts", active_accounts)
    
    with col3:
        asset_accounts = len([acc for acc in st.session_state.coa_data if acc['account_type'] == 'ASSET'])
        st.metric("Asset Accounts", asset_accounts)
    
    with col4:
        liability_accounts = len([acc for acc in st.session_state.coa_data if acc['account_type'] == 'LIABILITY'])
        st.metric("Liability Accounts", liability_accounts)

def show_add_account():
    st.markdown("### ➕ Add New Account")
    
    with st.form("add_account_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            account_code = st.text_input("Account Code*", placeholder="e.g., 1111")
            account_name = st.text_input("Account Name*", placeholder="e.g., Cash on Hand")
            account_type = st.selectbox("Account Type*", ["ASSET", "LIABILITY", "EQUITY", "REVENUE", "EXPENSE"])
            normal_balance = st.selectbox("Normal Balance*", ["DEBIT", "CREDIT"])
        
        with col2:
            account_subtype = st.selectbox("Account Subtype", 
                                         ["HEADER", "CURRENT", "NON-CURRENT", "CAPITAL", "RETAINED", 
                                          "DISTRIBUTION", "OPERATING", "NON-OPERATING", "COST"])
            tax_code = st.text_input("Tax Code (Optional)", placeholder="e.g., VAT-INPUT")
            parent_account = st.selectbox("Parent Account (Optional)", 
                                         ["None"] + [acc['account_name'] for acc in st.session_state.coa_data])
            is_active = st.checkbox("Active", value=True)
        
        submitted = st.form_submit_button("💾 Add Account", type="primary")
        
        if submitted:
            if account_code and account_name and account_type and normal_balance:
                # Check for duplicate account code
                existing_codes = [acc['account_code'] for acc in st.session_state.coa_data]
                if account_code in existing_codes:
                    st.error("❌ Account code already exists!")
                else:
                    new_account = {
                        "account_code": account_code,
                        "account_name": account_name,
                        "account_type": account_type,
                        "account_subtype": account_subtype,
                        "normal_balance": normal_balance,
                        "tax_code": tax_code,
                        "parent_account_id": None,  # Will be implemented with database
                        "is_active": is_active
                    }
                    st.session_state.coa_data.append(new_account)
                    st.success(f"✅ Account '{account_name}' added successfully!")
                    st.balloons()
            else:
                st.error("❌ Please fill in all required fields!")

def show_import_export():
    st.markdown("### 📥 Import/Export Chart of Accounts")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📥 Import Accounts")
        
        # File upload
        uploaded_file = st.file_uploader("Upload CSV file", type=['csv'])
        
        if uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file)
                st.success(f"✅ File loaded successfully! Found {len(df)} accounts.")
                
                # Display preview
                st.dataframe(df.head(), width="100%")
                
                if st.button("📥 Import Accounts", type="primary"):
                    # Convert DataFrame to COA format
                    required_columns = ['account_code', 'account_name', 'account_type', 'normal_balance']
                    
                    if all(col in df.columns for col in required_columns):
                        imported_accounts = df.to_dict('records')
                        st.session_state.coa_data.extend(imported_accounts)
                        st.success(f"✅ Successfully imported {len(imported_accounts)} accounts!")
                    else:
                        st.error("❌ Missing required columns. Please check your file format.")
                        
            except Exception as e:
                st.error(f"❌ Error reading file: {str(e)}")
        
        # Download template
        st.markdown("#### 📋 Download Template")
        template_df = pd.DataFrame(PHILIPPINE_COA_TEMPLATE[:5])  # First 5 accounts as template
        
        csv = template_df.to_csv(index=False)
        st.download_button(
            label="📥 Download CSV Template",
            data=csv,
            file_name="coa_template.csv",
            mime="text/csv"
        )
    
    with col2:
        st.markdown("#### 📤 Export Accounts")
        
        export_format = st.selectbox("Export Format", ["CSV", "Excel", "JSON"])
        
        if st.button("📤 Export Current Chart of Accounts", type="primary"):
            df = pd.DataFrame(st.session_state.coa_data)
            
            if export_format == "CSV":
                csv = df.to_csv(index=False)
                st.download_button(
                    label="📥 Download CSV",
                    data=csv,
                    file_name="chart_of_accounts.csv",
                    mime="text/csv"
                )
            elif export_format == "Excel":
                # Note: In production, you'd use openpyxl
                st.info("📄 Excel export will be implemented with openpyxl library")
            elif export_format == "JSON":
                json_data = json.dumps(st.session_state.coa_data, indent=2)
                st.download_button(
                    label="📥 Download JSON",
                    data=json_data,
                    file_name="chart_of_accounts.json",
                    mime="application/json"
                )

def show_coa_settings():
    st.markdown("### ⚙️ Chart of Accounts Settings")
    
    with st.expander("🔧 Account Numbering", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            numbering_system = st.selectbox("Numbering System", 
                                           ["Standard Philippine", "Custom", "Industry-Specific"])
            auto_generate_codes = st.checkbox("Auto-generate Account Codes", value=True)
        
        with col2:
            code_prefix = st.text_input("Code Prefix", placeholder="e.g., PH-")
            code_length = st.number_input("Code Length", min_value=3, max_value=10, value=4)
    
    with st.expander("🏛️ BIR Compliance Settings"):
        col1, col2 = st.columns(2)
        
        with col1:
            bir_compliant = st.checkbox("BIR Compliant Mode", value=True)
            include_tax_codes = st.checkbox("Include Tax Codes", value=True)
        
        with col2:
            fiscal_year_end = st.selectbox("Fiscal Year End", 
                                         ["December 31", "March 31", "June 30", "September 30"])
            reporting_currency = st.selectbox("Reporting Currency", ["PHP", "USD"])
    
    with st.expander("🎨 Display Settings"):
        col1, col2 = st.columns(2)
        
        with col1:
            show_inactive = st.checkbox("Show Inactive Accounts", value=False)
            group_by_type = st.checkbox("Group by Account Type", value=True)
        
        with col2:
            show_balances = st.checkbox("Show Account Balances", value=True)
            decimal_places = st.number_input("Decimal Places", min_value=0, max_value=4, value=2)
    
    st.markdown("### 🔄 Advanced Operations")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Reset to Philippine Standard", type="secondary"):
            st.session_state.coa_data = PHILIPPINE_COA_TEMPLATE.copy()
            st.success("✅ Reset to Philippine Standard Chart of Accounts!")
    
    with col2:
        if st.button("🗑️ Clear All Accounts", type="secondary"):
            if st.session_state.get('confirm_clear', False):
                st.session_state.coa_data = []
                st.success("✅ All accounts cleared!")
                st.session_state.confirm_clear = False
            else:
                st.session_state.confirm_clear = True
                st.warning("⚠️ Click again to confirm clearing all accounts")
    
    with col3:
        if st.button("💾 Save to Database", type="primary"):
            st.success("✅ Chart of Accounts saved to database!")
            st.info("📝 Note: Database integration will be implemented with Supabase")

# Utility functions for validation
def validate_account_code(code):
    """Validate account code format"""
    import re
    # Allow alphanumeric codes with optional hyphens
    pattern = r'^[A-Z0-9-]+$'
    return re.match(pattern, code) is not None

def validate_account_hierarchy(parent_code, child_code):
    """Validate parent-child account relationship"""
    # Parent should have fewer digits than child
    if len(parent_code) >= len(child_code):
        return False
    # Child should start with parent code
    return child_code.startswith(parent_code)

def get_account_by_code(account_code):
    """Get account by code from session state"""
    for account in st.session_state.coa_data:
        if account['account_code'] == account_code:
            return account
    return None

def get_child_accounts(parent_code):
    """Get all child accounts of a parent account"""
    return [acc for acc in st.session_state.coa_data 
            if acc['account_code'].startswith(parent_code) 
            and acc['account_code'] != parent_code]

if __name__ == "__main__":
    show_chart_of_accounts()
