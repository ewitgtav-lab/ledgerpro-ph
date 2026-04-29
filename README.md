# LedgerPro-PH: Philippine Accounting & Tax Compliance System

A comprehensive automated bookkeeping web application specifically designed for Philippine tax compliance and BIR regulations.

## 🚀 Features

### Core Accounting Modules
- **Chart of Accounts**: Customizable COA with Philippine accounting standards
- **Sales Journal**: Track accounts receivable with platform fee integration
- **Cash Receipts Journal**: Record cash sales and customer payments
- **Purchase Journal**: Manage accounts payable and supplier invoices
- **Cash Disbursement Journal**: Track expense payments
- **General Journal**: Manual journal entries with automated posting
- **General Ledger**: Real-time ledger updates and trial balance

### Specialized Philippine Features
- **VAT/Non-VAT Toggle**: Switch between VAT (12%) and Non-VAT (3%, 8%, OSD) taxation
- **Platform Integration**: Automatic calculations for Shopee, Lazada, TikTok fees
- **BIR Compliance**: Ready-to-print Forms 2307 and 1601C
- **Government Contributions**: Automated SSS, PhilHealth, Pag-IBIG calculations
- **Withholding Tax**: Configurable EWT rates per transaction type

### Business Operations
- **Inventory Management**: Real-time tracking with PO/SO/DR generation
- **Payroll System**: Automated tax computations and payslip generation
- **Fixed Assets**: Depreciation schedules and asset tracking
- **Bank Reconciliation**: Match bank statements with internal records

### Reporting & Analytics
- **Financial Statements**: Balance Sheet, Income Statement, Statement of Changes in Equity
- **Tax Reports**: Quarterly and annual BIR-compliant reports
- **Dashboard**: Visual summaries of financial performance
- **PDF Generation**: Export receipts, vouchers, and BIR forms

## 🛠️ Technology Stack

- **Frontend**: Streamlit with professional CSS styling
- **Backend/Database**: Supabase (PostgreSQL) with Row Level Security
- **Authentication**: Secure session management
- **PDF Generation**: ReportLab for document generation
- **Data Visualization**: Plotly for interactive charts

## 📋 Prerequisites

- Python 3.8+
- Supabase account
- Git

## 🚀 Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd SaaS-Killer
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up Supabase**
   - Create a new Supabase project
   - Run the `supabase_schema.sql` file in the SQL editor
   - Update the `.streamlit/secrets.toml` file with your Supabase credentials

4. **Configure environment**
   ```bash
   # Edit .streamlit/secrets.toml
   SUPABASE_URL = "your_supabase_url"
   SUPABASE_KEY = "your_supabase_anon_key"
   ```

5. **Run the application**
   ```bash
   streamlit run app.py
   ```

6. **Login**
   - Default password: `admin123`
   - Change the password in `.streamlit/secrets.toml` for production

## 📊 Database Schema

The application uses a comprehensive database schema with the following key tables:

- **companies**: Multi-tenancy support
- **users**: User management with role-based access
- **chart_of_accounts**: Philippine-standard COA
- ***_journal**: All journal types (sales, cash receipts, purchase, etc.)
- **general_ledger**: Central ledger with automated posting
- **products**: Inventory management
- **employees**: Payroll and HR data
- **tax_payments**: BIR compliance tracking

## 🔧 Configuration

### Tax Settings
Configure Philippine tax rates in `.streamlit/secrets.toml`:

```toml
VAT_RATE = 0.12
EWT_RATES = {
    "Professional Fees": 0.10,
    "Rent": 0.05,
    "Supplies": 0.01
}
```

### Government Contributions
2024 contribution rates are pre-configured:
- SSS: 4.5% employee, 9.5% employer
- PhilHealth: 5% total (shared)
- Pag-IBIG: 2% employee, 2% employer

## 🎯 Usage

### 1. Company Setup
- Register your company with TIN number
- Configure VAT registration status
- Set up your Chart of Accounts

### 2. Daily Operations
- Record sales in Sales Journal
- Process cash receipts with automatic tax calculations
- Manage purchases and expenses
- Track inventory movements

### 3. Payroll Processing
- Add employee information
- Process payroll periods
- Generate payslips with tax computations

### 4. Tax Compliance
- Generate BIR Forms 2307 and 1601C
- Track tax payments
- Produce quarterly and annual reports

## 📱 Modules Overview

### Dashboard
- Real-time financial metrics
- Revenue and expense trends
- Quick access to all modules
- Tax liability summaries

### Cash Receipts Journal
- Automated VAT and EWT calculations
- Platform fee integration (Shopee, Lazada, TikTok)
- Multiple payment methods
- Export to Excel and PDF

### Sales Journal
- Accounts receivable management
- Invoice tracking
- Customer information
- Tax withholding calculations

### Purchase Journal
- Supplier management
- Expense tracking
- Input VAT claims
- EWT processing

### Payroll Management
- Automated government contributions
- Withholding tax calculations
- Payslip generation
- 13th-month pay processing

## 🔒 Security Features

- **Row Level Security**: Users can only access their company's data
- **Secure Authentication**: Password-protected access
- **Data Validation**: Ensures accounting equations balance
- **Audit Trail**: Track all changes and postings

## 📈 Reports Available

### Financial Statements
- Balance Sheet (Statement of Financial Position)
- Income Statement (Statement of Comprehensive Income)
- Statement of Changes in Equity
- Trial Balance
- General Ledger

### Tax Reports
- VAT Returns (Form 2550Q/M)
- Expanded Withholding Tax (Form 2307)
- Creditable Withholding Tax (Form 1601C)
- Annual Income Tax (Form 1701Q)

### Operational Reports
- Sales Reports
- Expense Analysis
- Inventory Valuation
- Payroll Summaries

## 🤝 Support

For support and inquiries:
- Documentation: Available in-app
- Issues: Create GitHub issues
- Updates: Follow the project repository

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🗺️ Roadmap

### Phase 1 (Current)
- [x] Database schema design
- [x] Basic Streamlit application
- [x] Cash Receipts Journal
- [ ] User authentication with Supabase Auth
- [ ] Chart of Accounts management

### Phase 2 (Q2 2024)
- [ ] Complete journal modules
- [ ] General Ledger automation
- [ ] Basic financial statements
- [ ] Inventory management

### Phase 3 (Q3 2024)
- [ ] Payroll system
- [ ] BIR form generators
- [ ] Bank reconciliation
- [ ] Fixed assets management

### Phase 4 (Q4 2024)
- [ ] Advanced reporting
- [ ] Mobile responsiveness
- [ ] API integrations
- [ ] Multi-currency support

---

**LedgerPro-PH** - Simplifying Philippine Accounting and Tax Compliance
