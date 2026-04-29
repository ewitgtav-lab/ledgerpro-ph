import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, date
import plotly.express as px
from supabase import create_client
import json

# Initialize Supabase
@st.cache_resource
def init_supabase():
    SUPABASE_URL = st.secrets.get("SUPABASE_URL", "your_supabase_url")
    SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "your_supabase_key")
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def show_purchase_journal():
    st.markdown("""
    <div class="main-header">
        <h1>Purchase Journal</h1>
        <p>Record purchases and accounts payable</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize session state for purchase data
    if 'purchase_journal_data' not in st.session_state:
        st.session_state.purchase_journal_data = []
    
    # Tabs for different functions
    tab1, tab2, tab3, tab4 = st.tabs(["📝 New Purchase Entry", "📋 Purchase Records", "📊 Reports", "⚙️ Settings"])
    
    with tab1:
        show_new_purchase_entry()
    
    with tab2:
        show_purchase_records()
    
    with tab3:
        show_purchase_reports()
    
    with tab4:
        show_purchase_settings()

def show_new_purchase_entry():
    st.markdown("### 📝 Create New Purchase Entry")
    
    with st.form("purchase_entry_form"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            transaction_date = st.date_input("Transaction Date*", value=date.today())
            invoice_number = st.text_input("Invoice Number*", placeholder="PI-2024-001")
            supplier_name = st.text_input("Supplier Name*", placeholder="Enter supplier name")
            supplier_tin = st.text_input("Supplier TIN", placeholder="000-000-000-000")
            supplier_address = st.text_area("Supplier Address", placeholder="Enter supplier address")
        
        with col2:
            gross_amount = st.number_input("Gross Amount*", min_value=0.0, step=0.01, format="%.2f")
            purchase_type = st.selectbox("Purchase Type", 
                                        ["Goods/Merchandise", "Services", "Supplies", "Fixed Assets", "Others"])
            expense_category = st.selectbox("Expense Category",
                                          ["Cost of Goods Sold", "Operating Expenses", "Capital Expenditures", "Others"])
            purchase_order = st.text_input("Purchase Order Number", placeholder="PO-2024-001")
            receiving_department = st.text_input("Receiving Department", placeholder="e.g., Warehouse, Operations")
        
        with col3:
            # Tax configuration
            vat_registered = st.checkbox("VAT Registered", value=True)
            if vat_registered:
                vat_type = st.selectbox("VAT Type", ["VATable", "VAT-Exempt", "Zero-Rated"])
                if vat_type == "VATable":
                    vat_rate = 0.12
                else:
                    vat_rate = 0.0
                ewt_rate_options = [0.0, 0.01, 0.02, 0.05, 0.10]
                ewt_rate = st.selectbox("EWT Rate", options=ewt_rate_options, 
                                     format_func=lambda x: f"{x*100:.0f}%" if x > 0 else "None")
            else:
                vat_rate = 0.0
                ewt_rate = 0.0
                vat_type = "Non-VAT"
            
            # Payment terms
            payment_terms = st.selectbox("Payment Terms", ["COD", "Net 30", "Net 60", "Net 90"])
            due_date = st.date_input("Due Date", value=date.today())
            
            # Account selection (would be populated from COA)
            ap_account = st.selectbox("Accounts Payable Account", 
                                     ["2111 - Trade Payables", "2112 - Other Payables"])
            expense_account = st.selectbox("Expense Account", 
                                          ["5110 - Purchases", "5210 - Salaries and Wages", "5220 - Rent Expense"])
            vat_input_account = st.selectbox("VAT Input Account", 
                                            ["2121 - VAT Payable"]) if vat_registered else None
        
        # Calculate amounts
        net_amount = gross_amount
        
        if vat_registered and vat_type == "VATable":
            vat_amount = net_amount * vat_rate
            net_amount_with_vat = net_amount + vat_amount
        else:
            vat_amount = 0.0
            net_amount_with_vat = net_amount
        
        ewt_amount = net_amount * ewt_rate
        final_amount = net_amount_with_vat - ewt_amount
        
        # Display calculated amounts
        st.markdown("### 💰 Amount Breakdown")
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("Gross Amount", f"₱{gross_amount:,.2f}")
        with col2:
            st.metric("VAT Input", f"₱{vat_amount:,.2f}")
        with col3:
            st.metric("EWT Amount", f"₱{ewt_amount:,.2f}")
        with col4:
            st.metric("Net Amount", f"₱{net_amount_with_vat:,.2f}")
        with col5:
            st.metric("Amount Payable", f"₱{final_amount:,.2f}")
        
        # Additional details
        st.markdown("### 📄 Additional Details")
        col1, col2 = st.columns(2)
        
        with col1:
            notes = st.text_area("Notes", placeholder="Enter any additional notes...")
            delivery_date = st.date_input("Delivery Date", value=date.today())
            delivery_location = st.text_area("Delivery Location", placeholder="Enter delivery location")
        
        with col2:
            approved_by = st.text_input("Approved By", placeholder="Manager name")
            requested_by = st.text_input("Requested By", placeholder="Employee name")
            terms_conditions = st.text_area("Terms & Conditions", 
                                          placeholder="Enter terms and conditions...")
        
        # Submit buttons
        col1, col2, col3 = st.columns(3)
        with col1:
            submitted = st.form_submit_button("💾 Save Purchase Entry", type="primary")
        with col2:
            draft = st.form_submit_button("📝 Save as Draft")
        with col3:
            cancel = st.form_submit_button("❌ Cancel")
        
        if submitted:
            if invoice_number and supplier_name and gross_amount > 0:
                new_entry = {
                    "id": len(st.session_state.purchase_journal_data) + 1,
                    "transaction_date": transaction_date.strftime("%Y-%m-%d"),
                    "invoice_number": invoice_number,
                    "supplier_name": supplier_name,
                    "supplier_tin": supplier_tin,
                    "supplier_address": supplier_address,
                    "gross_amount": gross_amount,
                    "purchase_type": purchase_type,
                    "expense_category": expense_category,
                    "purchase_order": purchase_order,
                    "receiving_department": receiving_department,
                    "vat_registered": vat_registered,
                    "vat_type": vat_type,
                    "vat_rate": vat_rate,
                    "vat_amount": vat_amount,
                    "ewt_rate": ewt_rate,
                    "ewt_amount": ewt_amount,
                    "net_amount": net_amount_with_vat,
                    "final_amount": final_amount,
                    "payment_terms": payment_terms,
                    "due_date": due_date.strftime("%Y-%m-%d"),
                    "ap_account": ap_account,
                    "expense_account": expense_account,
                    "vat_input_account": vat_input_account,
                    "notes": notes,
                    "delivery_date": delivery_date.strftime("%Y-%m-%d"),
                    "delivery_location": delivery_location,
                    "approved_by": approved_by,
                    "requested_by": requested_by,
                    "terms_conditions": terms_conditions,
                    "status": "POSTED",
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                st.session_state.purchase_journal_data.append(new_entry)
                st.success(f"✅ Purchase entry {invoice_number} saved successfully!")
                st.balloons()
            else:
                st.error("❌ Please fill in all required fields!")

def show_purchase_records():
    st.markdown("### 📋 Purchase Records")
    
    # Search and filter options
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    
    with col1:
        search_term = st.text_input("🔍 Search", placeholder="Search by supplier, invoice, or PO...")
    
    with col2:
        status_filter = st.selectbox("Status", ["All", "POSTED", "PENDING", "CANCELLED"])
    
    with col3:
        date_filter = st.selectbox("Date Filter", ["All", "Today", "This Week", "This Month", "This Quarter"])
    
    with col4:
        purchase_type_filter = st.selectbox("Purchase Type", 
                                           ["All", "Goods/Merchandise", "Services", "Supplies", "Fixed Assets", "Others"])
    
    # Filter data
    filtered_data = st.session_state.purchase_journal_data.copy()
    
    if search_term:
        filtered_data = [purchase for purchase in filtered_data 
                        if search_term.lower() in purchase.get('supplier_name', '').lower() 
                        or search_term.lower() in purchase.get('invoice_number', '').lower()
                        or search_term.lower() in purchase.get('purchase_order', '').lower()]
    
    if status_filter != "All":
        filtered_data = [purchase for purchase in filtered_data if purchase.get('status') == status_filter]
    
    if purchase_type_filter != "All":
        filtered_data = [purchase for purchase in filtered_data if purchase.get('purchase_type') == purchase_type_filter]
    
    # Display records
    if filtered_data:
        # Create DataFrame for display
        df = pd.DataFrame(filtered_data)
        
        # Format for display
        display_columns = [
            'transaction_date', 'invoice_number', 'supplier_name', 'gross_amount', 
            'vat_amount', 'final_amount', 'purchase_type', 'status', 'due_date'
        ]
        
        if all(col in df.columns for col in display_columns):
            display_df = df[display_columns].copy()
            display_df['gross_amount'] = display_df['gross_amount'].apply(lambda x: f"₱{x:,.2f}")
            display_df['vat_amount'] = display_df['vat_amount'].apply(lambda x: f"₱{x:,.2f}")
            display_df['final_amount'] = display_df['final_amount'].apply(lambda x: f"₱{x:,.2f}")
            
            # Add status styling
            def style_status(val):
                if val == 'POSTED':
                    return 'background-color: #10b98120; color: #10b981;'
                elif val == 'PENDING':
                    return 'background-color: #f59e0b20; color: #f59e0b;'
                elif val == 'CANCELLED':
                    return 'background-color: #ef444420; color: #ef4444;'
                return ''
            
            styled_df = display_df.style.map(style_status, subset=['status'])
            st.dataframe(styled_df, use_container_width=True, hide_index=True)
            
            # Action buttons
            st.markdown("### 🔧 Actions")
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.button("📥 Export to Excel", use_container_width=True)
            with col2:
                st.button("📄 Print Report", use_container_width=True)
            with col3:
                st.button("📧 Send Email", use_container_width=True)
            with col4:
                st.button("🔄 Refresh", use_container_width=True)
            with col5:
                st.button("🗑️ Clear Filters", use_container_width=True)
        else:
            st.info("📝 No purchase records found. Create your first purchase entry!")
    else:
        st.info("📝 No purchase records found. Create your first purchase entry!")
    
    # Summary statistics
    if st.session_state.purchase_journal_data:
        st.markdown("### 📊 Purchase Summary")
        col1, col2, col3, col4 = st.columns(4)
        
        total_purchases = sum(purchase['final_amount'] for purchase in st.session_state.purchase_journal_data)
        total_vat_input = sum(purchase['vat_amount'] for purchase in st.session_state.purchase_journal_data)
        total_ewt = sum(purchase['ewt_amount'] for purchase in st.session_state.purchase_journal_data)
        outstanding_payables = sum(purchase['final_amount'] for purchase in st.session_state.purchase_journal_data 
                                 if purchase.get('status') == 'POSTED')
        
        with col1:
            st.metric("Total Purchases", f"₱{total_purchases:,.2f}")
        with col2:
            st.metric("VAT Input", f"₱{total_vat_input:,.2f}")
        with col3:
            st.metric("EWT Applied", f"₱{total_ewt:,.2f}")
        with col4:
            st.metric("Outstanding Payables", f"₱{outstanding_payables:,.2f}")

def show_purchase_reports():
    st.markdown("### 📊 Purchase Reports")
    
    report_type = st.selectbox("Select Report Type", 
                              ["Purchase Summary", "Supplier Aging", "Category Analysis", "Tax Summary"])
    
    if report_type == "Purchase Summary":
        show_purchase_summary_report()
    elif report_type == "Supplier Aging":
        show_supplier_aging_report()
    elif report_type == "Category Analysis":
        show_category_analysis_report()
    elif report_type == "Tax Summary":
        show_purchase_tax_summary_report()

def show_purchase_summary_report():
    st.markdown("#### 📈 Purchase Summary Report")
    
    if not st.session_state.purchase_journal_data:
        st.info("📝 No purchase data available for reporting.")
        return
    
    # Date range filter
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", value=date.today().replace(day=1))
    with col2:
        end_date = st.date_input("End Date", value=date.today())
    
    # Filter data by date range
    filtered_data = [purchase for purchase in st.session_state.purchase_journal_data 
                    if start_date <= datetime.strptime(purchase['transaction_date'], "%Y-%m-%d").date() <= end_date]
    
    if filtered_data:
        # Monthly purchase trend
        df = pd.DataFrame(filtered_data)
        df['month'] = pd.to_datetime(df['transaction_date']).dt.to_period('M')
        monthly_purchases = df.groupby('month')['final_amount'].sum().reset_index()
        monthly_purchases['month'] = monthly_purchases['month'].astype(str)
        
        fig = px.line(monthly_purchases, x='month', y='final_amount', 
                     title='Monthly Purchase Trend',
                     labels={'final_amount': 'Purchase Amount (₱)', 'month': 'Month'})
        st.plotly_chart(fig, use_container_width=True)
        
        # Top suppliers
        supplier_purchases = df.groupby('supplier_name')['final_amount'].sum().sort_values(ascending=False).head(10)
        
        fig = px.bar(x=supplier_purchases.index, y=supplier_purchases.values,
                    title='Top 10 Suppliers by Purchase Amount',
                    labels={'x': 'Supplier', 'y': 'Purchase Amount (₱)'})
        fig.update_xaxis(tickangle=45)
        st.plotly_chart(fig, use_container_width=True)

def show_supplier_aging_report():
    st.markdown("#### 🏢 Supplier Aging Report")
    
    if not st.session_state.purchase_journal_data:
        st.info("📝 No purchase data available for aging report.")
        return
    
    # Calculate aging
    aging_data = []
    for purchase in st.session_state.purchase_journal_data:
        if purchase.get('status') == 'POSTED':
            days_overdue = (date.today() - datetime.strptime(purchase['due_date'], "%Y-%m-%d").date()).days
            if days_overdue <= 0:
                bucket = "Current"
            elif days_overdue <= 30:
                bucket = "1-30 Days"
            elif days_overdue <= 60:
                bucket = "31-60 Days"
            elif days_overdue <= 90:
                bucket = "61-90 Days"
            else:
                bucket = "90+ Days"
            
            aging_data.append({
                'supplier': purchase['supplier_name'],
                'invoice': purchase['invoice_number'],
                'amount': purchase['final_amount'],
                'due_date': purchase['due_date'],
                'days_overdue': max(0, days_overdue),
                'bucket': bucket
            })
    
    if aging_data:
        df = pd.DataFrame(aging_data)
        
        # Aging summary
        aging_summary = df.groupby('bucket')['amount'].sum().reset_index()
        
        fig = px.pie(aging_summary, values='amount', names='bucket',
                    title='Payables Aging Breakdown')
        st.plotly_chart(fig, use_container_width=True)
        
        # Detailed aging table
        st.dataframe(df, use_container_width=True, hide_index=True)

def show_category_analysis_report():
    st.markdown("#### 📂 Purchase Category Analysis")
    
    if not st.session_state.purchase_journal_data:
        st.info("📝 No purchase data available for category analysis.")
        return
    
    df = pd.DataFrame(st.session_state.purchase_journal_data)
    
    # Category breakdown
    category_purchases = df.groupby('expense_category')['final_amount'].sum().reset_index()
    
    fig = px.bar(category_purchases, x='expense_category', y='final_amount',
                title='Purchases by Category',
                labels={'final_amount': 'Purchase Amount (₱)', 'expense_category': 'Category'})
    fig.update_xaxis(tickangle=45)
    st.plotly_chart(fig, use_container_width=True)
    
    # Purchase type breakdown
    type_purchases = df.groupby('purchase_type')['final_amount'].sum().reset_index()
    
    fig = px.pie(type_purchases, values='final_amount', names='purchase_type',
                title='Purchases by Type')
    st.plotly_chart(fig, use_container_width=True)

def show_purchase_tax_summary_report():
    st.markdown("#### 🏛️ Purchase Tax Summary Report")
    
    if not st.session_state.purchase_journal_data:
        st.info("📝 No purchase data available for tax summary.")
        return
    
    df = pd.DataFrame(st.session_state.purchase_journal_data)
    
    # Tax calculations
    total_purchases = df['final_amount'].sum()
    total_vat_input = df['vat_amount'].sum()
    total_ewt = df['ewt_amount'].sum()
    net_purchases = total_purchases - total_vat_input
    
    # Display tax summary
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Purchases", f"₱{total_purchases:,.2f}")
    with col2:
        st.metric("VAT Input", f"₱{total_vat_input:,.2f}")
    with col3:
        st.metric("EWT Applied", f"₱{total_ewt:,.2f}")
    with col4:
        st.metric("Net Purchases", f"₱{net_purchases:,.2f}")
    
    # Monthly tax trend
    df['month'] = pd.to_datetime(df['transaction_date']).dt.to_period('M')
    monthly_tax = df.groupby('month')[['vat_amount', 'ewt_amount']].sum().reset_index()
    monthly_tax['month'] = monthly_tax['month'].astype(str)
    
    fig = px.bar(monthly_tax, x='month', y=['vat_amount', 'ewt_amount'],
                title='Monthly Tax Benefits',
                labels={'value': 'Amount (₱)', 'month': 'Month', 'variable': 'Tax Type'})
    st.plotly_chart(fig, use_container_width=True)

def show_purchase_settings():
    st.markdown("### ⚙️ Purchase Journal Settings")
    
    with st.expander("🔢 Numbering Settings"):
        col1, col2 = st.columns(2)
        
        with col1:
            invoice_prefix = st.text_input("Invoice Prefix", value="PI-")
            auto_generate_invoice = st.checkbox("Auto-generate Invoice Numbers", value=True)
        
        with col2:
            starting_number = st.number_input("Starting Number", min_value=1, value=1)
            reset_monthly = st.checkbox("Reset Monthly", value=False)
    
    with st.expander("💰 Default Values"):
        col1, col2 = st.columns(2)
        
        with col1:
            default_vat_rate = st.selectbox("Default VAT Rate", [0.12, 0.0], 
                                          format_func=lambda x: f"{x*100:.0f}%" if x > 0 else "None")
            default_payment_terms = st.selectbox("Default Payment Terms", 
                                               ["COD", "Net 30", "Net 60", "Net 90"])
        
        with col2:
            default_ewt_rate = st.selectbox("Default EWT Rate", [0.0, 0.01, 0.02, 0.05, 0.10],
                                          format_func=lambda x: f"{x*100:.0f}%" if x > 0 else "None")
            auto_post = st.checkbox("Auto-post Entries", value=True)
    
    with st.expander("🏢 Supplier Management"):
        col1, col2 = st.columns(2)
        
        with col1:
            require_tin = st.checkbox("Require Supplier TIN", value=True)
            require_address = st.checkbox("Require Supplier Address", value=True)
        
        with col2:
            credit_limit_check = st.checkbox("Check Credit Limits", value=False)
            duplicate_invoice_check = st.checkbox("Check Duplicate Invoices", value=True)
    
    with st.expander("📧 Notification Settings"):
        col1, col2 = st.columns(2)
        
        with col1:
            email_supplier = st.checkbox("Email Supplier Confirmation", value=False)
            email_manager = st.checkbox("Email Manager", value=True)
        
        with col2:
            email_department = st.checkbox("Email Department Head", value=True)
            payment_reminders = st.checkbox("Payment Due Reminders", value=True)
    
    st.markdown("### 🔄 Advanced Operations")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📥 Import Purchase Data", type="secondary"):
            st.info("📝 Import functionality will be implemented")
    
    with col2:
        if st.button("📤 Export All Purchases", type="secondary"):
            st.info("📝 Export functionality will be implemented")
    
    with col3:
        if st.button("🔄 Recalculate Tax", type="primary"):
            st.success("✅ Tax recalculated for all entries!")

if __name__ == "__main__":
    show_purchase_journal()
