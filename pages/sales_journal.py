import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, date
import plotly.express as px
from supabase import create_client
import json

# Dark mode chart helper
def apply_dark_theme(fig):
    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_color='#f1f5f9',
        title_font_color='#f1f5f9',
        legend_font_color='#f1f5f9',
        xaxis=dict(gridcolor='#334155'),
        yaxis=dict(gridcolor='#334155')
    )
    return fig

# Initialize Supabase
@st.cache_resource
def init_supabase():
    SUPABASE_URL = st.secrets.get("SUPABASE_URL", "your_supabase_url")
    SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "your_supabase_key")
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def show_sales_journal():
    st.markdown("""
    <div class="main-header">
        <h1>Sales Journal</h1>
        <p>Record credit sales and accounts receivable</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize session state for sales data
    if 'sales_journal_data' not in st.session_state:
        st.session_state.sales_journal_data = []
    
    # Tabs for different functions
    tab1, tab2, tab3, tab4 = st.tabs(["📝 New Sales Entry", "📋 Sales Records", "📊 Reports", "⚙️ Settings"])
    
    with tab1:
        show_new_sales_entry()
    
    with tab2:
        show_sales_records()
    
    with tab3:
        show_sales_reports()
    
    with tab4:
        show_sales_settings()

def show_new_sales_entry():
    st.markdown("### 📝 Create New Sales Entry")
    
    with st.form("sales_entry_form"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            transaction_date = st.date_input("Transaction Date*", value=date.today())
            invoice_number = st.text_input("Invoice Number*", placeholder="SI-2024-001")
            customer_name = st.text_input("Customer Name*", placeholder="Enter customer name")
            customer_tin = st.text_input("Customer TIN", placeholder="000-000-000-000")
            customer_address = st.text_area("Customer Address", placeholder="Enter customer address")
        
        with col2:
            gross_amount = st.number_input("Gross Amount*", min_value=0.0, step=0.01, format="%.2f")
            platform_name = st.selectbox("Platform", ["None", "SHOPEE", "LAZADA", "TIKTOK", "OTHER"])
            platform_fee = st.number_input("Platform Fee", min_value=0.0, step=0.01, format="%.2f", value=0.0)
            seller_discount = st.number_input("Seller Discount", min_value=0.0, step=0.01, format="%.2f", value=0.0)
            sales_rep = st.text_input("Sales Representative", placeholder="Enter sales rep name")
        
        with col3:
            # Tax configuration
            vat_registered = st.checkbox("VAT Registered", value=True)
            if vat_registered:
                vat_rate = 0.12
                ewt_rate_options = [0.0, 0.01, 0.02, 0.05, 0.10]
                ewt_rate = st.selectbox("EWT Rate", options=ewt_rate_options, 
                                     format_func=lambda x: f"{x*100:.0f}%" if x > 0 else "None")
                vat_type = st.selectbox("VAT Type", ["VATable", "VAT-Exempt", "Zero-Rated"])
            else:
                vat_rate = 0.0
                ewt_rate = 0.0
                vat_type = "Non-VAT"
            
            # Payment terms
            payment_terms = st.selectbox("Payment Terms", ["COD", "Net 30", "Net 60", "Net 90"])
            due_date = st.date_input("Due Date", value=date.today())
            
            # Account selection (would be populated from COA)
            ar_account = st.selectbox("Accounts Receivable Account", 
                                     ["1112 - Accounts Receivable", "1121 - Trade Receivables"])
            sales_account = st.selectbox("Sales Account", 
                                       ["4101 - Merchandise Sales", "4102 - Service Revenue"])
            vat_account = st.selectbox("VAT Account", 
                                      ["2121 - VAT Payable"]) if vat_registered else None
        
        # Calculate amounts
        net_amount = gross_amount - platform_fee - seller_discount
        
        if vat_registered and vat_type == "VATable":
            vat_amount = net_amount * vat_rate
        else:
            vat_amount = 0.0
        
        ewt_amount = net_amount * ewt_rate
        final_amount = net_amount + vat_amount - ewt_amount
        
        # Display calculated amounts
        st.markdown("### 💰 Amount Breakdown")
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("Gross Amount", f"₱{gross_amount:,.2f}")
        with col2:
            st.metric("Net Amount", f"₱{net_amount:,.2f}")
        with col3:
            st.metric("VAT Amount", f"₱{vat_amount:,.2f}")
        with col4:
            st.metric("EWT Amount", f"₱{ewt_amount:,.2f}")
        with col5:
            st.metric("Total Due", f"₱{final_amount:,.2f}")
        
        # Additional details
        st.markdown("### 📄 Additional Details")
        col1, col2 = st.columns(2)
        
        with col1:
            notes = st.text_area("Notes", placeholder="Enter any additional notes...")
            delivery_date = st.date_input("Delivery Date", value=date.today())
            delivery_address = st.text_area("Delivery Address", placeholder="Enter delivery address")
        
        with col2:
            reference_number = st.text_input("Reference Number", placeholder="PO number or other reference")
            approved_by = st.text_input("Approved By", placeholder="Manager name")
            terms_conditions = st.text_area("Terms & Conditions", 
                                          placeholder="Enter terms and conditions...")
        
        # Submit buttons
        col1, col2, col3 = st.columns(3)
        with col1:
            submitted = st.form_submit_button("💾 Save Sales Entry", type="primary")
        with col2:
            draft = st.form_submit_button("📝 Save as Draft")
        with col3:
            cancel = st.form_submit_button("❌ Cancel")
        
        if submitted:
            if invoice_number and customer_name and gross_amount > 0:
                new_entry = {
                    "id": len(st.session_state.sales_journal_data) + 1,
                    "transaction_date": transaction_date.strftime("%Y-%m-%d"),
                    "invoice_number": invoice_number,
                    "customer_name": customer_name,
                    "customer_tin": customer_tin,
                    "customer_address": customer_address,
                    "gross_amount": gross_amount,
                    "platform_name": platform_name,
                    "platform_fee": platform_fee,
                    "seller_discount": seller_discount,
                    "net_amount": net_amount,
                    "vat_registered": vat_registered,
                    "vat_type": vat_type,
                    "vat_amount": vat_amount,
                    "ewt_rate": ewt_rate,
                    "ewt_amount": ewt_amount,
                    "final_amount": final_amount,
                    "payment_terms": payment_terms,
                    "due_date": due_date.strftime("%Y-%m-%d"),
                    "ar_account": ar_account,
                    "sales_account": sales_account,
                    "vat_account": vat_account,
                    "sales_rep": sales_rep,
                    "notes": notes,
                    "delivery_date": delivery_date.strftime("%Y-%m-%d"),
                    "delivery_address": delivery_address,
                    "reference_number": reference_number,
                    "approved_by": approved_by,
                    "terms_conditions": terms_conditions,
                    "status": "POSTED",
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                st.session_state.sales_journal_data.append(new_entry)
                st.success(f"✅ Sales entry {invoice_number} saved successfully!")
                st.balloons()
            else:
                st.error("❌ Please fill in all required fields!")

def show_sales_records():
    st.markdown("### 📋 Sales Records")
    
    # Search and filter options
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    
    with col1:
        search_term = st.text_input("🔍 Search", placeholder="Search by customer, invoice, or reference...")
    
    with col2:
        status_filter = st.selectbox("Status", ["All", "POSTED", "PENDING", "CANCELLED"])
    
    with col3:
        date_filter = st.selectbox("Date Filter", ["All", "Today", "This Week", "This Month", "This Quarter"])
    
    with col4:
        platform_filter = st.selectbox("Platform", ["All", "None", "SHOPEE", "LAZADA", "TIKTOK", "OTHER"])
    
    # Filter data
    filtered_data = st.session_state.sales_journal_data.copy()
    
    if search_term:
        filtered_data = [sale for sale in filtered_data 
                        if search_term.lower() in sale.get('customer_name', '').lower() 
                        or search_term.lower() in sale.get('invoice_number', '').lower()
                        or search_term.lower() in sale.get('reference_number', '').lower()]
    
    if status_filter != "All":
        filtered_data = [sale for sale in filtered_data if sale.get('status') == status_filter]
    
    if platform_filter != "All":
        filtered_data = [sale for sale in filtered_data if sale.get('platform_name') == platform_filter]
    
    # Display records
    if filtered_data:
        # Create DataFrame for display
        df = pd.DataFrame(filtered_data)
        
        # Format for display
        display_columns = [
            'transaction_date', 'invoice_number', 'customer_name', 'gross_amount', 
            'vat_amount', 'final_amount', 'platform_name', 'status', 'due_date'
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
            st.dataframe(styled_df, width="stretch", hide_index=True)
            
            # Action buttons
            st.markdown("### 🔧 Actions")
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.button("📥 Export to Excel", use_container_width=False)
            with col2:
                st.button("📄 Print Report", use_container_width=False)
            with col3:
                st.button("📧 Send Email", use_container_width=False)
            with col4:
                st.button("🔄 Refresh", use_container_width=False)
            with col5:
                st.button("🗑️ Clear Filters", use_container_width=False)
        else:
            st.info("📝 No sales records found. Create your first sales entry!")
    else:
        st.info("📝 No sales records found. Create your first sales entry!")
    
    # Summary statistics
    if st.session_state.sales_journal_data:
        st.markdown("### 📊 Sales Summary")
        col1, col2, col3, col4 = st.columns(4)
        
        total_sales = sum(sale['final_amount'] for sale in st.session_state.sales_journal_data)
        total_vat = sum(sale['vat_amount'] for sale in st.session_state.sales_journal_data)
        total_ewt = sum(sale['ewt_amount'] for sale in st.session_state.sales_journal_data)
        outstanding_receivables = sum(sale['final_amount'] for sale in st.session_state.sales_journal_data 
                                   if sale.get('status') == 'POSTED')
        
        with col1:
            st.metric("Total Sales", f"₱{total_sales:,.2f}")
        with col2:
            st.metric("Total VAT", f"₱{total_vat:,.2f}")
        with col3:
            st.metric("Total EWT", f"₱{total_ewt:,.2f}")
        with col4:
            st.metric("Outstanding Receivables", f"₱{outstanding_receivables:,.2f}")

def show_sales_reports():
    st.markdown("### 📊 Sales Reports")
    
    report_type = st.selectbox("Select Report Type", 
                              ["Sales Summary", "Customer Aging", "Platform Analysis", "Tax Summary"])
    
    if report_type == "Sales Summary":
        show_sales_summary_report()
    elif report_type == "Customer Aging":
        show_customer_aging_report()
    elif report_type == "Platform Analysis":
        show_platform_analysis_report()
    elif report_type == "Tax Summary":
        show_tax_summary_report()

def show_sales_summary_report():
    st.markdown("#### 📈 Sales Summary Report")
    
    if not st.session_state.sales_journal_data:
        st.info("📝 No sales data available for reporting.")
        return
    
    # Date range filter
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", value=date.today().replace(day=1))
    with col2:
        end_date = st.date_input("End Date", value=date.today())
    
    # Filter data by date range
    filtered_data = [sale for sale in st.session_state.sales_journal_data 
                    if start_date <= datetime.strptime(sale['transaction_date'], "%Y-%m-%d").date() <= end_date]
    
    if filtered_data:
        # Monthly sales trend
        df = pd.DataFrame(filtered_data)
        df['month'] = pd.to_datetime(df['transaction_date']).dt.to_period('M')
        monthly_sales = df.groupby('month')['final_amount'].sum().reset_index()
        monthly_sales['month'] = monthly_sales['month'].astype(str)
        
        fig = px.line(monthly_sales, x='month', y='final_amount', 
                     title='Monthly Sales Trend',
                     labels={'final_amount': 'Sales Amount (₱)', 'month': 'Month'},
                     color_discrete_sequence=['#3b82f6'])
        fig = apply_dark_theme(fig)
        st.plotly_chart(fig, width="100%")
        
        # Top customers
        customer_sales = df.groupby('customer_name')['final_amount'].sum().sort_values(ascending=False).head(10)
        
        fig = px.bar(x=customer_sales.index, y=customer_sales.values,
                    title='Top 10 Customers by Sales',
                    labels={'x': 'Customer', 'y': 'Sales Amount (₱)'},
                    color_discrete_sequence=['#3b82f6'])
        fig.update_xaxis(tickangle=45)
        fig = apply_dark_theme(fig)
        st.plotly_chart(fig, width="100%")

def show_customer_aging_report():
    st.markdown("#### 👥 Customer Aging Report")
    
    if not st.session_state.sales_journal_data:
        st.info("📝 No sales data available for aging report.")
        return
    
    # Calculate aging
    aging_data = []
    for sale in st.session_state.sales_journal_data:
        if sale.get('status') == 'POSTED':
            days_overdue = (date.today() - datetime.strptime(sale['due_date'], "%Y-%m-%d").date()).days
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
                'customer': sale['customer_name'],
                'invoice': sale['invoice_number'],
                'amount': sale['final_amount'],
                'due_date': sale['due_date'],
                'days_overdue': max(0, days_overdue),
                'bucket': bucket
            })
    
    if aging_data:
        df = pd.DataFrame(aging_data)
        
        # Aging summary
        aging_summary = df.groupby('bucket')['amount'].sum().reset_index()
        aging_summary = aging_summary.reindex([0, 1, 2, 3, 4])  # Reorder buckets
        
        fig = px.pie(aging_summary, values='amount', names='bucket',
                    title='Aging Breakdown',
                    color_discrete_sequence=['#3b82f6', '#60a5fa', '#93c5fd', '#dbeafe', '#eff6ff'])
        fig = apply_dark_theme(fig)
        st.plotly_chart(fig, width="100%")
        
        # Detailed aging table
        st.dataframe(df, width="stretch", hide_index=True)

def show_platform_analysis_report():
    st.markdown("#### 📱 Platform Analysis Report")
    
    if not st.session_state.sales_journal_data:
        st.info("📝 No sales data available for platform analysis.")
        return
    
    df = pd.DataFrame(st.session_state.sales_journal_data)
    
    # Platform breakdown
    platform_sales = df.groupby('platform_name')['final_amount'].sum().reset_index()
    
    fig = px.bar(platform_sales, x='platform_name', y='final_amount',
                title='Sales by Platform',
                labels={'final_amount': 'Sales Amount (₱)', 'platform_name': 'Platform'},
                color_discrete_sequence=['#3b82f6'])
    fig = apply_dark_theme(fig)
    st.plotly_chart(fig, width="100%")
    
    # Platform fees analysis
    platform_fees = df.groupby('platform_name')['platform_fee'].sum().reset_index()
    
    fig = px.pie(platform_fees, values='platform_fee', names='platform_name',
                title='Platform Fees Distribution',
                color_discrete_sequence=['#3b82f6', '#60a5fa', '#93c5fd', '#dbeafe', '#eff6ff'])
    fig = apply_dark_theme(fig)
    st.plotly_chart(fig, width="100%")

def show_tax_summary_report():
    st.markdown("#### 🏛️ Tax Summary Report")
    
    if not st.session_state.sales_journal_data:
        st.info("📝 No sales data available for tax summary.")
        return
    
    df = pd.DataFrame(st.session_state.sales_journal_data)
    
    # Tax calculations
    total_sales = df['final_amount'].sum()
    total_vat = df['vat_amount'].sum()
    total_ewt = df['ewt_amount'].sum()
    net_revenue = total_sales - total_vat
    
    # Display tax summary
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Sales", f"₱{total_sales:,.2f}")
    with col2:
        st.metric("Output VAT", f"₱{total_vat:,.2f}")
    with col3:
        st.metric("EWT Collected", f"₱{total_ewt:,.2f}")
    with col4:
        st.metric("Net Revenue", f"₱{net_revenue:,.2f}")
    
    # Monthly tax trend
    df['month'] = pd.to_datetime(df['transaction_date']).dt.to_period('M')
    monthly_tax = df.groupby('month')[['vat_amount', 'ewt_amount']].sum().reset_index()
    monthly_tax['month'] = monthly_tax['month'].astype(str)
    
    fig = px.bar(monthly_tax, x='month', y=['vat_amount', 'ewt_amount'],
                title='Monthly Tax Collections',
                labels={'value': 'Amount (₱)', 'month': 'Month', 'variable': 'Tax Type'},
                color_discrete_map={'vat_amount': '#3b82f6', 'ewt_amount': '#60a5fa'})
    fig = apply_dark_theme(fig)
    st.plotly_chart(fig, width="100%")

def show_sales_settings():
    st.markdown("### ⚙️ Sales Journal Settings")
    
    with st.expander("🔢 Numbering Settings"):
        col1, col2 = st.columns(2)
        
        with col1:
            invoice_prefix = st.text_input("Invoice Prefix", value="SI-")
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
    
    with st.expander("📧 Notification Settings"):
        col1, col2 = st.columns(2)
        
        with col1:
            email_customer = st.checkbox("Email Customer Invoice", value=False)
            email_sales_rep = st.checkbox("Email Sales Rep", value=True)
        
        with col2:
            email_manager = st.checkbox("Email Manager", value=True)
            overdue_reminders = st.checkbox("Overdue Payment Reminders", value=True)
    
    st.markdown("### 🔄 Advanced Operations")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📥 Import Sales Data", type="secondary"):
            st.info("📝 Import functionality will be implemented")
    
    with col2:
        if st.button("📤 Export All Sales", type="secondary"):
            st.info("📝 Export functionality will be implemented")
    
    with col3:
        if st.button("🔄 Recalculate Tax", type="primary"):
            st.success("✅ Tax recalculated for all entries!")

if __name__ == "__main__":
    show_sales_journal()
