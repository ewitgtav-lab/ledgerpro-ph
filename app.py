import streamlit as st
import pandas as pd
from datetime import datetime, date
import plotly.express as px
import plotly.graph_objects as go
from models import DatabaseManager
from tax_engine import TaxCalculator

# Configure Streamlit page
st.set_page_config(
    page_title="Pang-Kape: Bookkeeping & Tax Suite",
    page_icon="☕",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark theme
st.markdown("""
<style>
    .stApp {
        background-color: #1a1a1a;
    }
    .stSidebar {
        background-color: #2d2d2d;
    }
    .main-header {
        font-size: 2.5rem;
        color: #ff6b6b;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #2d2d2d;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #ff6b6b;
    }
    .dataframe {
        background-color: #2d2d2d !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize database
@st.cache_resource
def init_db():
    return DatabaseManager()

db = init_db()
tax_calc = TaxCalculator()

def main():
    # Sidebar navigation
    st.sidebar.markdown("# ☕ Pang-Kape Suite")
    st.sidebar.markdown("---")
    
    page = st.sidebar.selectbox(
        "Navigate to:",
        [
            "📊 Dashboard",
            "💰 Cash Receipt Journal",
            "💸 Cash Disbursement Journal", 
            "📖 General Ledger",
            "⚖️ Trial Balance",
            "🧾 Receipt Generator",
            "📋 Tax Reports",
            "⚙️ Settings"
        ]
    )
    
    # Display current date and tax year
    st.sidebar.markdown(f"**Tax Year:** 2026")
    st.sidebar.markdown(f"**Today:** {date.today().strftime('%B %d, %Y')}")
    
    if page == "📊 Dashboard":
        show_dashboard()
    elif page == "💰 Cash Receipt Journal":
        show_cash_receipt_journal()
    elif page == "💸 Cash Disbursement Journal":
        show_cash_disbursement_journal()
    elif page == "📖 General Ledger":
        show_general_ledger()
    elif page == "⚖️ Trial Balance":
        show_trial_balance()
    elif page == "🧾 Receipt Generator":
        show_receipt_generator()
    elif page == "📋 Tax Reports":
        show_tax_reports()
    elif page == "⚙️ Settings":
        show_settings()

def show_dashboard():
    st.markdown('<h1 class="main-header">📊 Dashboard</h1>', unsafe_allow_html=True)
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Get total sales for current month
        current_month = date.today().replace(day=1)
        total_sales = get_monthly_sales(current_month)
        st.metric("Monthly Sales", f"₱{total_sales:,.2f}", delta="+12.5%")
    
    with col2:
        # Get total expenses for current month
        total_expenses = get_monthly_expenses(current_month)
        st.metric("Monthly Expenses", f"₱{total_expenses:,.2f}", delta="-5.2%")
    
    with col3:
        # Calculate estimated tax
        estimated_tax = tax_calc.calculate_estimated_tax(2026)
        st.metric("Estimated Tax Due", f"₱{estimated_tax:,.2f}")
    
    with col4:
        # Net income
        net_income = total_sales - total_expenses
        st.metric("Net Income", f"₱{net_income:,.2f}", delta="+8.3%")
    
    st.markdown("---")
    
    # Charts section
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📈 Monthly Sales vs Expenses")
        monthly_data = get_monthly_comparison()
        if monthly_data:
            fig = px.line(
                monthly_data, 
                x='month', 
                y=['sales', 'expenses'],
                title="Sales vs Expenses Trend",
                labels={'value': 'Amount (₱)', 'month': 'Month'},
                color_discrete_map={'sales': '#ff6b6b', 'expenses': '#4ecdc4'}
            )
            fig.update_layout(template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### 🛍️ Platform Sales Breakdown")
        platform_data = get_platform_breakdown()
        if platform_data:
            fig = px.pie(
                platform_data,
                values='amount',
                names='platform',
                title="Sales by Platform",
                color_discrete_sequence=['#ff6b6b', '#4ecdc4', '#45b7d1', '#f9ca24']
            )
            fig.update_layout(template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)
    
    # Recent transactions
    st.markdown("### 📝 Recent Transactions")
    recent_transactions = get_recent_transactions()
    if recent_transactions:
        df = pd.DataFrame(recent_transactions)
        st.dataframe(df, use_container_width=True)

def show_cash_receipt_journal():
    st.markdown('<h1 class="main-header">💰 Cash Receipt Journal</h1>', unsafe_allow_html=True)
    
    # Tabs for manual entry and CSV import
    tab1, tab2 = st.tabs(["📝 Manual Entry", "📁 CSV Import"])
    
    with tab1:
        st.markdown("### Add New Cash Receipt")
        
        col1, col2 = st.columns(2)
        
        with col1:
            transaction_date = st.date_input("Transaction Date", value=date.today())
            reference_number = st.text_input("Reference Number (Optional)")
            customer_name = st.text_input("Customer Name")
            customer_tin = st.text_input("Customer TIN (Optional)")
        
        with col2:
            # Get revenue accounts
            revenue_accounts = db.get_accounts_by_type('Revenue')
            account_options = {f"{acc['account_code']} - {acc['account_name']}": acc['account_code'] 
                              for acc in revenue_accounts}
            selected_account = st.selectbox("Revenue Account", list(account_options.keys()))
            account_code = account_options[selected_account]
            
            platform_name = st.selectbox("Platform", ["None", "Shopee", "Lazada", "TikTok", "Facebook", "Instagram"])
            description = st.text_area("Description")
        
        # Financial details
        st.markdown("### 💵 Financial Details")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            gross_sales = st.number_input("Gross Sales", min_value=0.0, value=0.0, step=0.01)
            vat_output = st.number_input("VAT Output (12%)", min_value=0.0, value=0.0, step=0.01)
        
        with col2:
            commission_fee = st.number_input("Commission Fee", min_value=0.0, value=0.0, step=0.01)
            shipping_subsidy = st.number_input("Shipping Subsidy", min_value=0.0, value=0.0, step=0.01)
        
        with col3:
            net_sales = gross_sales - vat_output
            total_cash_received = net_sales - commission_fee + shipping_subsidy
            st.markdown("**Net Sales:**")
            st.info(f"₱{net_sales:,.2f}")
            st.markdown("**Total Cash Received:**")
            st.success(f"₱{total_cash_received:,.2f}")
        
        # Submit button
        if st.button("💾 Add Entry", type="primary"):
            entry_data = {
                'transaction_date': transaction_date,
                'reference_number': reference_number,
                'customer_name': customer_name,
                'customer_tin': customer_tin,
                'account_code': account_code,
                'description': description,
                'gross_sales': gross_sales,
                'vat_output': vat_output,
                'net_sales': net_sales,
                'platform_name': platform_name if platform_name != "None" else None,
                'commission_fee': commission_fee,
                'shipping_subsidy': shipping_subsidy,
                'total_cash_received': total_cash_received
            }
            
            try:
                crj_id = db.add_crj_entry(entry_data)
                st.success(f"✅ Entry added successfully! ID: {crj_id}")
                st.balloons()
            except Exception as e:
                st.error(f"❌ Error adding entry: {str(e)}")
    
    with tab2:
        st.markdown("### 📁 Import from CSV")
        st.markdown("Upload CSV files from Shopee, Lazada, or TikTok")
        
        uploaded_file = st.file_uploader("Choose CSV file", type=['csv'])
        
        if uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file)
                st.success(f"✅ File loaded successfully! Found {len(df)} records")
                
                # Show preview
                st.markdown("### 📋 Data Preview")
                st.dataframe(df.head())
                
                # Column mapping
                st.markdown("### 🔄 Map Columns")
                
                # Auto-detect common column names
                common_mappings = {
                    'Date': ['date', 'transaction_date', 'order_date', 'created_at'],
                    'Customer': ['customer_name', 'buyer_name', 'customer', 'buyer'],
                    'Amount': ['amount', 'total', 'gross_sales', 'order_amount'],
                    'Commission': ['commission', 'commission_fee', 'platform_fee'],
                    'Shipping': ['shipping', 'shipping_fee', 'shipping_subsidy']
                }
                
                mapped_columns = {}
                for field, possible_names in common_mappings.items():
                    available_columns = [col for col in df.columns if any(name in col.lower() for name in possible_names)]
                    if available_columns:
                        mapped_columns[field] = st.selectbox(f"{field} Column", available_columns, index=0)
                    else:
                        mapped_columns[field] = st.selectbox(f"{field} Column", df.columns)
                
                # Process import
                if st.button("🚀 Import Data", type="primary"):
                    success_count = 0
                    error_count = 0
                    
                    for index, row in df.iterrows():
                        try:
                            entry_data = {
                                'transaction_date': pd.to_datetime(row[mapped_columns['Date']]).date(),
                                'reference_number': f"CSV-{index+1}",
                                'customer_name': row.get(mapped_columns['Customer'], f"Customer {index+1}"),
                                'account_code': '401001',  # Default Sales Revenue
                                'description': f"CSV Import - {platform_name}",
                                'gross_sales': float(row[mapped_columns['Amount']]),
                                'commission_fee': float(row.get(mapped_columns['Commission'], 0)),
                                'shipping_subsidy': float(row.get(mapped_columns['Shipping'], 0)),
                                'total_cash_received': float(row[mapped_columns['Amount']])
                            }
                            
                            db.add_crj_entry(entry_data)
                            success_count += 1
                        except Exception as e:
                            error_count += 1
                            continue
                    
                    st.success(f"✅ Import completed! {success_count} records added, {error_count} errors")
                    
            except Exception as e:
                st.error(f"❌ Error reading file: {str(e)}")
    
    # Display existing entries
    st.markdown("### 📋 Recent Cash Receipts")
    crj_entries = get_crj_entries()
    if crj_entries:
        df = pd.DataFrame(crj_entries)
        st.dataframe(df, use_container_width=True)

def show_cash_disbursement_journal():
    st.markdown('<h1 class="main-header">💸 Cash Disbursement Journal</h1>', unsafe_allow_html=True)
    
    st.markdown("### Add New Cash Disbursement")
    
    col1, col2 = st.columns(2)
    
    with col1:
        transaction_date = st.date_input("Transaction Date", value=date.today(), key="cdj_date")
        reference_number = st.text_input("Reference Number (Optional)", key="cdj_ref")
        payee_name = st.text_input("Payee Name")
        payee_tin = st.text_input("Payee TIN (Optional)")
    
    with col2:
        # Get expense accounts
        expense_accounts = db.get_accounts_by_type('Expense')
        account_options = {f"{acc['account_code']} - {acc['account_name']}": acc['account_code'] 
                          for acc in expense_accounts}
        selected_account = st.selectbox("Expense Account", list(account_options.keys()), key="cdj_account")
        account_code = account_options[selected_account]
        
        # Auto-categorization
        expense_categories = [
            "Platform Fees", "Shipping Expenses", "Marketing Expenses", 
            "Office Supplies", "Internet Expenses", "Utilities", 
            "Repairs and Maintenance", "Miscellaneous Expenses"
        ]
        expense_category = st.selectbox("Expense Category", expense_categories)
        
        description = st.text_area("Description", key="cdj_desc")
    
    # Financial details
    st.markdown("### 💵 Financial Details")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        amount = st.number_input("Amount", min_value=0.0, value=0.0, step=0.01, key="cdj_amount")
    
    with col2:
        vat_input = st.number_input("VAT Input (12%)", min_value=0.0, value=0.0, step=0.01, key="cdj_vat")
        ewt = st.number_input("EWT (if applicable)", min_value=0.0, value=0.0, step=0.01, key="cdj_ewt")
    
    with col3:
        net_amount = amount - vat_input - ewt
        st.markdown("**Net Amount:**")
        st.success(f"₱{net_amount:,.2f}")
    
    # Submit button
    if st.button("💾 Add Disbursement", type="primary"):
        entry_data = {
            'transaction_date': transaction_date,
            'reference_number': reference_number,
            'payee_name': payee_name,
            'payee_tin': payee_tin,
            'account_code': account_code,
            'expense_category': expense_category,
            'description': description,
            'amount': amount,
            'vat_input': vat_input,
            'ewt': ewt,
            'net_amount': net_amount
        }
        
        try:
            cdj_id = db.add_cdj_entry(entry_data)
            st.success(f"✅ Disbursement added successfully! ID: {cdj_id}")
            st.balloons()
        except Exception as e:
            st.error(f"❌ Error adding disbursement: {str(e)}")
    
    # Display existing entries
    st.markdown("### 📋 Recent Cash Disbursements")
    cdj_entries = get_cdj_entries()
    if cdj_entries:
        df = pd.DataFrame(cdj_entries)
        st.dataframe(df, use_container_width=True)

def show_general_ledger():
    st.markdown('<h1 class="main-header">📖 General Ledger</h1>', unsafe_allow_html=True)
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        account_types = ['All', 'Asset', 'Liability', 'Equity', 'Revenue', 'Expense']
        selected_type = st.selectbox("Account Type", account_types)
    
    with col2:
        start_date = st.date_input("Start Date", value=date(date.today().year, 1, 1))
    
    with col3:
        end_date = st.date_input("End Date", value=date.today())
    
    # Get ledger data
    ledger_entries = get_ledger_entries(selected_type, start_date, end_date)
    
    if ledger_entries:
        df = pd.DataFrame(ledger_entries)
        
        # Summary by account
        st.markdown("### 📊 Account Summary")
        account_summary = df.groupby(['account_code', 'account_name']).agg({
            'debit_amount': 'sum',
            'credit_amount': 'sum',
            'balance': 'last'
        }).reset_index()
        
        st.dataframe(account_summary, use_container_width=True)
        
        # Detailed transactions
        st.markdown("### 📋 Detailed Transactions")
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No ledger entries found for the selected criteria.")

def show_trial_balance():
    st.markdown('<h1 class="main-header">⚖️ Trial Balance</h1>', unsafe_allow_html=True)
    
    as_of_date = st.date_input("As of Date", value=date.today())
    
    # Get trial balance
    trial_balance = db.get_trial_balance(as_of_date.strftime('%Y-%m-%d'))
    
    if trial_balance:
        df = pd.DataFrame(trial_balance)
        
        # Calculate totals
        total_debits = df[df['normal_balance'] == 'Debit']['balance'].sum()
        total_credits = df[df['normal_balance'] == 'Credit']['balance'].sum()
        
        # Display trial balance
        st.markdown("### 📋 Trial Balance")
        st.dataframe(df, use_container_width=True)
        
        # Totals
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Debits", f"₱{total_debits:,.2f}")
        with col2:
            st.metric("Total Credits", f"₱{total_credits:,.2f}")
        
        # Check if balanced
        if abs(total_debits - total_credits) < 0.01:
            st.success("✅ Trial Balance is BALANCED")
        else:
            st.error(f"❌ Trial Balance is NOT BALANCED. Difference: ₱{abs(total_debits - total_credits):,.2f}")
    else:
        st.info("No trial balance data available.")

def show_receipt_generator():
    st.markdown('<h1 class="main-header">🧾 Receipt Generator</h1>', unsafe_allow_html=True)
    
    # Receipt type selection
    receipt_type = st.selectbox("Receipt Type", ["Sales Invoice", "Service Invoice", "Official Receipt"])
    
    # Customer information
    st.markdown("### 👤 Customer Information")
    col1, col2 = st.columns(2)
    
    with col1:
        customer_name = st.text_input("Customer Name *")
        customer_tin = st.text_input("Customer TIN *")
        customer_address = st.text_area("Customer Address")
    
    with col2:
        transaction_date = st.date_input("Transaction Date", value=date.today())
        payment_method = st.selectbox("Payment Method", ["Cash", "Bank Transfer", "GCash", "PayMaya", "Credit Card"])
    
    # Items
    st.markdown("### 📦 Items")
    items = []
    
    # Item input
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        item_description = st.text_input("Item Description")
    with col2:
        item_quantity = st.number_input("Quantity", min_value=1, value=1)
    with col3:
        unit_price = st.number_input("Unit Price", min_value=0.0, value=0.0, step=0.01)
    with col4:
        vat_rate = st.selectbox("VAT Rate", [0, 12]) / 100
    
    # Add item button
    if st.button("➕ Add Item"):
        if item_description and unit_price > 0:
            items.append({
                'description': item_description,
                'quantity': item_quantity,
                'unit_price': unit_price,
                'vat_rate': vat_rate,
                'total': item_quantity * unit_price,
                'vat_amount': item_quantity * unit_price * vat_rate
            })
            st.success(f"✅ {item_description} added")
    
    # Display items
    if items:
        st.markdown("### 📋 Current Items")
        items_df = pd.DataFrame(items)
        st.dataframe(items_df, use_container_width=True)
        
        total_amount = sum(item['total'] for item in items)
        total_vat = sum(item['vat_amount'] for item in items)
        grand_total = total_amount + total_vat
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Subtotal", f"₱{total_amount:,.2f}")
        with col2:
            st.metric("VAT", f"₱{total_vat:,.2f}")
        with col3:
            st.metric("Grand Total", f"₱{grand_total:,.2f}")
    
    # Generate receipt
    if st.button("🧾 Generate Receipt", type="primary") and items and customer_name:
        try:
            # Get next serial number
            serial_number = db.get_next_receipt_serial(receipt_type)
            
            # Generate PDF (placeholder for now)
            st.success(f"✅ Receipt generated! Serial: {serial_number}")
            st.info(f"Customer: {customer_name}")
            st.info(f"Total Amount: ₱{grand_total:,.2f}")
            
        except Exception as e:
            st.error(f"❌ Error generating receipt: {str(e)}")

def show_tax_reports():
    st.markdown('<h1 class="main-header">📋 Tax Reports</h1>', unsafe_allow_html=True)
    
    # Tax period selection
    col1, col2 = st.columns(2)
    
    with col1:
        tax_year = st.selectbox("Tax Year", [2026, 2025, 2024])
        tax_period = st.selectbox("Tax Period", ["Quarter 1", "Quarter 2", "Quarter 3", "Quarter 4", "Annual"])
    
    with col2:
        tax_regime = st.selectbox("Tax Regime", ["8% Flat Rate", "Graduated Rates", "Mixed"])
    
    # Calculate tax
    if st.button("🧮 Calculate Tax", type="primary"):
        tax_computation = tax_calc.calculate_tax(
            tax_year=tax_year,
            period=tax_period,
            regime=tax_regime
        )
        
        if tax_computation:
            st.markdown("### 📊 Tax Computation Results")
            
            # Display computation details
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Gross Sales", f"₱{tax_computation.get('gross_sales', 0):,.2f}")
                st.metric("Business Expenses", f"₱{tax_computation.get('business_expenses', 0):,.2f}")
                st.metric("Net Taxable Income", f"₱{tax_computation.get('net_taxable_income', 0):,.2f}")
            
            with col2:
                st.metric("Tax Due", f"₱{tax_computation.get('tax_due', 0):,.2f}")
                st.metric("Quarterly Tax Paid", f"₱{tax_computation.get('quarterly_tax_paid', 0):,.2f}")
                st.metric("Remaining Tax Due", f"₱{tax_computation.get('remaining_tax_due', 0):,.2f}")
            
            # Generate BIR forms
            st.markdown("### 📄 BIR Forms Generation")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📋 Generate Annex A (No Inventory)"):
                    st.info("Annex A PDF generation will be implemented")
            
            with col2:
                if st.button("📋 Generate Annex D (Inventory List)"):
                    st.info("Annex D PDF generation will be implemented")

def show_settings():
    st.markdown('<h1 class="main-header">⚙️ Settings</h1>', unsafe_allow_html=True)
    
    st.markdown("### 🏢 Business Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        business_name = st.text_input("Business Name")
        owner_name = st.text_input("Owner Name")
        tin = st.text_input("TIN")
    
    with col2:
        business_address = st.text_area("Business Address")
        registered_date = st.date_input("Registered Date")
    
    st.markdown("### 🧮 Tax Settings")
    
    default_regime = st.selectbox(
        "Default Tax Regime",
        ["8% Flat Rate", "Graduated Rates", "Mixed"],
        help="Select your preferred tax regime for calculations"
    )
    
    st.markdown("### 📊 Data Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📥 Export Data", type="secondary"):
            st.info("Data export functionality will be implemented")
    
    with col2:
        if st.button("🗑️ Clear All Data", type="secondary"):
            st.warning("This will delete all data. This action cannot be undone!")
            confirm = st.checkbox("I understand and want to proceed")
            if confirm and st.button("Yes, Delete Everything", type="primary"):
                st.info("Data deletion will be implemented")

# Helper functions for data retrieval
def get_monthly_sales(month_date):
    """Get total sales for a specific month"""
    # Placeholder implementation
    return 150000.00

def get_monthly_expenses(month_date):
    """Get total expenses for a specific month"""
    # Placeholder implementation
    return 45000.00

def get_monthly_comparison():
    """Get monthly sales vs expenses data for charts"""
    # Placeholder implementation
    return [
        {'month': 'Jan', 'sales': 120000, 'expenses': 35000},
        {'month': 'Feb', 'sales': 135000, 'expenses': 40000},
        {'month': 'Mar', 'sales': 150000, 'expenses': 45000},
        {'month': 'Apr', 'sales': 142000, 'expenses': 42000}
    ]

def get_platform_breakdown():
    """Get sales breakdown by platform"""
    # Placeholder implementation
    return [
        {'platform': 'Shopee', 'amount': 85000},
        {'platform': 'Lazada', 'amount': 45000},
        {'platform': 'TikTok', 'amount': 20000}
    ]

def get_recent_transactions():
    """Get recent transactions for dashboard"""
    # Placeholder implementation
    return [
        {'date': '2026-04-27', 'type': 'Sales', 'description': 'Shopee Order #1234', 'amount': 2500.00},
        {'date': '2026-04-27', 'type': 'Expense', 'description': 'Internet Bill', 'amount': -1500.00},
        {'date': '2026-04-26', 'type': 'Sales', 'description': 'Lazada Order #5678', 'amount': 3200.00}
    ]

def get_crj_entries():
    """Get cash receipt journal entries"""
    # Placeholder implementation
    return [
        {'date': '2026-04-27', 'customer': 'Juan Dela Cruz', 'amount': 2500.00, 'platform': 'Shopee'},
        {'date': '2026-04-26', 'customer': 'Maria Santos', 'amount': 3200.00, 'platform': 'Lazada'}
    ]

def get_cdj_entries():
    """Get cash disbursement journal entries"""
    # Placeholder implementation
    return [
        {'date': '2026-04-27', 'payee': 'PLDT', 'amount': 1500.00, 'category': 'Internet Expenses'},
        {'date': '2026-04-26', 'payee': 'Meralco', 'amount': 2200.00, 'category': 'Utilities'}
    ]

def get_ledger_entries(account_type, start_date, end_date):
    """Get general ledger entries"""
    # Placeholder implementation
    return [
        {'date': '2026-04-27', 'account_code': '401001', 'account_name': 'Sales Revenue', 'debit': 0, 'credit': 2500.00, 'balance': 2500.00},
        {'date': '2026-04-27', 'account_code': '101001', 'account_name': 'Cash on Hand', 'debit': 2500.00, 'credit': 0, 'balance': 2500.00}
    ]

if __name__ == "__main__":
    main()
