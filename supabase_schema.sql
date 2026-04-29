-- =====================================================
-- LedgerPro-PH Database Schema for Philippine Accounting
-- =====================================================

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =====================================================
-- USER AND COMPANY MANAGEMENT
-- =====================================================

-- Companies table for multi-tenancy
CREATE TABLE companies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_name VARCHAR(255) NOT NULL,
    business_name VARCHAR(255) NOT NULL,
    tin_number VARCHAR(20) UNIQUE NOT NULL,
    vat_registered BOOLEAN DEFAULT true,
    vat_type VARCHAR(20) DEFAULT 'STANDARD' CHECK (vat_type IN ('STANDARD', 'NON-VAT', 'ZERO-RATED')),
    business_address TEXT,
    contact_number VARCHAR(50),
    email_address VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Users table with company association
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'user' CHECK (role IN ('admin', 'accountant', 'user')),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE
);

-- =====================================================
-- CHART OF ACCOUNTS
-- =====================================================

-- Chart of Accounts
CREATE TABLE chart_of_accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    account_code VARCHAR(20) NOT NULL,
    account_name VARCHAR(255) NOT NULL,
    account_type VARCHAR(50) NOT NULL CHECK (account_type IN ('ASSET', 'LIABILITY', 'EQUITY', 'REVENUE', 'EXPENSE')),
    account_subtype VARCHAR(100),
    normal_balance VARCHAR(10) NOT NULL CHECK (normal_balance IN ('DEBIT', 'CREDIT')),
    is_active BOOLEAN DEFAULT true,
    parent_account_id UUID REFERENCES chart_of_accounts(id),
    tax_code VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(company_id, account_code)
);

-- =====================================================
-- JOURNALS
-- =====================================================

-- Sales Journal (Accounts Receivable)
CREATE TABLE sales_journal (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    transaction_date DATE NOT NULL,
    invoice_number VARCHAR(50) UNIQUE NOT NULL,
    customer_name VARCHAR(255) NOT NULL,
    customer_tin VARCHAR(20),
    account_receivable_id UUID REFERENCES chart_of_accounts(id),
    sales_account_id UUID REFERENCES chart_of_accounts(id),
    vat_account_id UUID REFERENCES chart_of_accounts(id),
    gross_amount DECIMAL(15,2) NOT NULL,
    vat_amount DECIMAL(15,2) DEFAULT 0,
    net_amount DECIMAL(15,2) NOT NULL,
    platform_name VARCHAR(50) CHECK (platform_name IN ('SHOPEE', 'LAZADA', 'TIKTOK', 'OTHER')),
    platform_fee DECIMAL(15,2) DEFAULT 0,
    seller_discount DECIMAL(15,2) DEFAULT 0,
    ewt_rate DECIMAL(5,4) DEFAULT 0,
    ewt_amount DECIMAL(15,2) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'POSTED', 'CANCELLED')),
    posted_date TIMESTAMP WITH TIME ZONE,
    posted_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Cash Receipts Journal
CREATE TABLE cash_receipts_journal (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    transaction_date DATE NOT NULL,
    or_number VARCHAR(50) UNIQUE NOT NULL,
    customer_name VARCHAR(255) NOT NULL,
    cash_account_id UUID REFERENCES chart_of_accounts(id),
    sales_account_id UUID REFERENCES chart_of_accounts(id),
    vat_account_id UUID REFERENCES chart_of_accounts(id),
    ar_account_id UUID REFERENCES chart_of_accounts(id),
    gross_amount DECIMAL(15,2) NOT NULL,
    vat_amount DECIMAL(15,2) DEFAULT 0,
    net_amount DECIMAL(15,2) NOT NULL,
    platform_name VARCHAR(50) CHECK (platform_name IN ('SHOPEE', 'LAZADA', 'TIKTOK', 'OTHER')),
    platform_fee DECIMAL(15,2) DEFAULT 0,
    seller_discount DECIMAL(15,2) DEFAULT 0,
    ewt_rate DECIMAL(5,4) DEFAULT 0,
    ewt_amount DECIMAL(15,2) DEFAULT 0,
    payment_method VARCHAR(50) NOT NULL,
    bank_name VARCHAR(100),
    check_number VARCHAR(50),
    status VARCHAR(20) DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'POSTED', 'CANCELLED')),
    posted_date TIMESTAMP WITH TIME ZONE,
    posted_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Purchase Journal (Accounts Payable)
CREATE TABLE purchase_journal (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    transaction_date DATE NOT NULL,
    invoice_number VARCHAR(50) UNIQUE NOT NULL,
    supplier_name VARCHAR(255) NOT NULL,
    supplier_tin VARCHAR(20),
    account_payable_id UUID REFERENCES chart_of_accounts(id),
    expense_account_id UUID REFERENCES chart_of_accounts(id),
    vat_input_account_id UUID REFERENCES chart_of_accounts(id),
    gross_amount DECIMAL(15,2) NOT NULL,
    vat_amount DECIMAL(15,2) DEFAULT 0,
    net_amount DECIMAL(15,2) NOT NULL,
    ewt_rate DECIMAL(5,4) DEFAULT 0,
    ewt_amount DECIMAL(15,2) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'POSTED', 'CANCELLED')),
    posted_date TIMESTAMP WITH TIME ZONE,
    posted_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Cash Disbursement Journal
CREATE TABLE cash_disbursement_journal (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    transaction_date DATE NOT NULL,
    check_number VARCHAR(50),
    voucher_number VARCHAR(50) UNIQUE NOT NULL,
    payee_name VARCHAR(255) NOT NULL,
    cash_account_id UUID REFERENCES chart_of_accounts(id),
    expense_account_id UUID REFERENCES chart_of_accounts(id),
    vat_input_account_id UUID REFERENCES chart_of_accounts(id),
    ap_account_id UUID REFERENCES chart_of_accounts(id),
    gross_amount DECIMAL(15,2) NOT NULL,
    vat_amount DECIMAL(15,2) DEFAULT 0,
    net_amount DECIMAL(15,2) NOT NULL,
    ewt_rate DECIMAL(5,4) DEFAULT 0,
    ewt_amount DECIMAL(15,2) DEFAULT 0,
    payment_method VARCHAR(50) NOT NULL,
    bank_name VARCHAR(100),
    status VARCHAR(20) DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'POSTED', 'CANCELLED')),
    posted_date TIMESTAMP WITH TIME ZONE,
    posted_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- General Journal
CREATE TABLE general_journal (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    transaction_date DATE NOT NULL,
    journal_number VARCHAR(50) UNIQUE NOT NULL,
    description TEXT NOT NULL,
    total_debit DECIMAL(15,2) NOT NULL,
    total_credit DECIMAL(15,2) NOT NULL,
    status VARCHAR(20) DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'POSTED', 'CANCELLED')),
    posted_date TIMESTAMP WITH TIME ZONE,
    posted_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CHECK (total_debit = total_credit)
);

-- General Journal Lines
CREATE TABLE general_journal_lines (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    journal_id UUID REFERENCES general_journal(id) ON DELETE CASCADE,
    account_id UUID REFERENCES chart_of_accounts(id),
    description TEXT,
    debit_amount DECIMAL(15,2) DEFAULT 0,
    credit_amount DECIMAL(15,2) DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CHECK (debit_amount > 0 OR credit_amount > 0),
    CHECK (debit_amount = 0 OR credit_amount = 0)
);

-- =====================================================
-- GENERAL LEDGER
-- =====================================================

-- General Ledger
CREATE TABLE general_ledger (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    account_id UUID REFERENCES chart_of_accounts(id),
    transaction_date DATE NOT NULL,
    reference_number VARCHAR(50),
    reference_type VARCHAR(50) CHECK (reference_type IN ('SALES', 'CASH_RECEIPT', 'PURCHASE', 'CASH_DISBURSEMENT', 'GENERAL_JOURNAL')),
    reference_id UUID,
    description TEXT,
    debit_amount DECIMAL(15,2) DEFAULT 0,
    credit_amount DECIMAL(15,2) DEFAULT 0,
    balance DECIMAL(15,2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    posted_by UUID REFERENCES users(id)
);

-- =====================================================
-- INVENTORY MANAGEMENT
-- =====================================================

-- Products/Items
CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    item_code VARCHAR(50) NOT NULL,
    item_name VARCHAR(255) NOT NULL,
    description TEXT,
    unit_of_measure VARCHAR(50) NOT NULL,
    cost_price DECIMAL(15,2) NOT NULL,
    selling_price DECIMAL(15,2) NOT NULL,
    inventory_account_id UUID REFERENCES chart_of_accounts(id),
    cogs_account_id UUID REFERENCES chart_of_accounts(id),
    sales_account_id UUID REFERENCES chart_of_accounts(id),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(company_id, item_code)
);

-- Purchase Orders
CREATE TABLE purchase_orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    po_number VARCHAR(50) UNIQUE NOT NULL,
    supplier_name VARCHAR(255) NOT NULL,
    order_date DATE NOT NULL,
    expected_delivery_date DATE,
    status VARCHAR(20) DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'PARTIAL', 'RECEIVED', 'CANCELLED')),
    total_amount DECIMAL(15,2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Purchase Order Lines
CREATE TABLE purchase_order_lines (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    po_id UUID REFERENCES purchase_orders(id) ON DELETE CASCADE,
    product_id UUID REFERENCES products(id),
    quantity DECIMAL(15,2) NOT NULL,
    unit_price DECIMAL(15,2) NOT NULL,
    total_amount DECIMAL(15,2) NOT NULL,
    received_quantity DECIMAL(15,2) DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Sales Orders
CREATE TABLE sales_orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    so_number VARCHAR(50) UNIQUE NOT NULL,
    customer_name VARCHAR(255) NOT NULL,
    order_date DATE NOT NULL,
    delivery_date DATE,
    status VARCHAR(20) DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'PARTIAL', 'DELIVERED', 'CANCELLED')),
    total_amount DECIMAL(15,2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Sales Order Lines
CREATE TABLE sales_order_lines (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    so_id UUID REFERENCES sales_orders(id) ON DELETE CASCADE,
    product_id UUID REFERENCES products(id),
    quantity DECIMAL(15,2) NOT NULL,
    unit_price DECIMAL(15,2) NOT NULL,
    total_amount DECIMAL(15,2) NOT NULL,
    delivered_quantity DECIMAL(15,2) DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Delivery Receipts
CREATE TABLE delivery_receipts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    dr_number VARCHAR(50) UNIQUE NOT NULL,
    reference_type VARCHAR(20) CHECK (reference_type IN ('PO', 'SO')),
    reference_id UUID,
    customer_name VARCHAR(255),
    supplier_name VARCHAR(255),
    delivery_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'POSTED', 'CANCELLED')),
    total_amount DECIMAL(15,2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Delivery Receipt Lines
CREATE TABLE delivery_receipt_lines (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    dr_id UUID REFERENCES delivery_receipts(id) ON DELETE CASCADE,
    product_id UUID REFERENCES products(id),
    quantity DECIMAL(15,2) NOT NULL,
    unit_price DECIMAL(15,2) NOT NULL,
    total_amount DECIMAL(15,2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- PAYROLL MANAGEMENT
-- =====================================================

-- Employees
CREATE TABLE employees (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    employee_code VARCHAR(50) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    position VARCHAR(100),
    department VARCHAR(100),
    sss_number VARCHAR(20),
    philhealth_number VARCHAR(20),
    pagibig_number VARCHAR(20),
    tin_number VARCHAR(20),
    bank_name VARCHAR(100),
    bank_account_number VARCHAR(50),
    basic_salary DECIMAL(15,2) NOT NULL,
    allowance DECIMAL(15,2) DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    hire_date DATE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(company_id, employee_code)
);

-- Payroll Periods
CREATE TABLE payroll_periods (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    pay_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'PROCESSING', 'POSTED')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(company_id, period_start, period_end)
);

-- Payroll Details
CREATE TABLE payroll_details (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    payroll_period_id UUID REFERENCES payroll_periods(id) ON DELETE CASCADE,
    employee_id UUID REFERENCES employees(id),
    basic_salary DECIMAL(15,2) NOT NULL,
    overtime_pay DECIMAL(15,2) DEFAULT 0,
    holiday_pay DECIMAL(15,2) DEFAULT 0,
    allowance DECIMAL(15,2) DEFAULT 0,
    gross_salary DECIMAL(15,2) NOT NULL,
    sss_contribution DECIMAL(15,2) DEFAULT 0,
    philhealth_contribution DECIMAL(15,2) DEFAULT 0,
    pagibig_contribution DECIMAL(15,2) DEFAULT 0,
    withholding_tax DECIMAL(15,2) DEFAULT 0,
    other_deductions DECIMAL(15,2) DEFAULT 0,
    total_deductions DECIMAL(15,2) NOT NULL,
    net_salary DECIMAL(15,2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- TAX COMPLIANCE
-- =====================================================

-- BIR Forms Configuration
CREATE TABLE bir_forms_config (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    form_type VARCHAR(50) NOT NULL,
    form_number VARCHAR(50) NOT NULL,
    description TEXT,
    frequency VARCHAR(20) CHECK (frequency IN ('MONTHLY', 'QUARTERLY', 'ANNUALLY')),
    due_day INTEGER,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tax Payments
CREATE TABLE tax_payments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    tax_type VARCHAR(50) NOT NULL,
    form_number VARCHAR(50),
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    tax_amount DECIMAL(15,2) NOT NULL,
    payment_date DATE,
    payment_method VARCHAR(50),
    bank_name VARCHAR(100),
    check_number VARCHAR(50),
    confirmation_number VARCHAR(100),
    status VARCHAR(20) DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'PAID', 'CANCELLED')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- BANK RECONCILIATION
-- =====================================================

-- Bank Accounts
CREATE TABLE bank_accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    bank_name VARCHAR(100) NOT NULL,
    account_number VARCHAR(50) NOT NULL,
    account_type VARCHAR(50) NOT NULL,
    account_name VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(company_id, bank_name, account_number)
);

-- Bank Statements
CREATE TABLE bank_statements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    bank_account_id UUID REFERENCES bank_accounts(id) ON DELETE CASCADE,
    statement_date DATE NOT NULL,
    beginning_balance DECIMAL(15,2) NOT NULL,
    ending_balance DECIMAL(15,2) NOT NULL,
    file_path VARCHAR(500),
    uploaded_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Bank Statement Lines
CREATE TABLE bank_statement_lines (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    statement_id UUID REFERENCES bank_statements(id) ON DELETE CASCADE,
    transaction_date DATE NOT NULL,
    description TEXT,
    reference_number VARCHAR(100),
    debit_amount DECIMAL(15,2) DEFAULT 0,
    credit_amount DECIMAL(15,2) DEFAULT 0,
    balance DECIMAL(15,2) NOT NULL,
    is_reconciled BOOLEAN DEFAULT false,
    matched_transaction_id UUID,
    matched_transaction_type VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- FIXED ASSETS
-- =====================================================

-- Fixed Assets
CREATE TABLE fixed_assets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    asset_code VARCHAR(50) NOT NULL,
    asset_name VARCHAR(255) NOT NULL,
    description TEXT,
    asset_category VARCHAR(100),
    acquisition_date DATE NOT NULL,
    acquisition_cost DECIMAL(15,2) NOT NULL,
    useful_life_years INTEGER NOT NULL,
    depreciation_method VARCHAR(50) DEFAULT 'STRAIGHT_LINE',
    salvage_value DECIMAL(15,2) DEFAULT 0,
    accumulated_depreciation DECIMAL(15,2) DEFAULT 0,
    net_book_value DECIMAL(15,2) NOT NULL,
    asset_account_id UUID REFERENCES chart_of_accounts(id),
    depreciation_account_id UUID REFERENCES chart_of_accounts(id),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(company_id, asset_code)
);

-- Depreciation Schedule
CREATE TABLE depreciation_schedule (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    asset_id UUID REFERENCES fixed_assets(id) ON DELETE CASCADE,
    fiscal_year INTEGER NOT NULL,
    depreciation_amount DECIMAL(15,2) NOT NULL,
    accumulated_depreciation DECIMAL(15,2) NOT NULL,
    net_book_value DECIMAL(15,2) NOT NULL,
    posted_date TIMESTAMP WITH TIME ZONE,
    posted_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- INDEXES FOR PERFORMANCE
-- =====================================================

-- Company-based indexes
CREATE INDEX idx_users_company_id ON users(company_id);
CREATE INDEX idx_chart_of_accounts_company_id ON chart_of_accounts(company_id);
CREATE INDEX idx_sales_journal_company_id ON sales_journal(company_id);
CREATE INDEX idx_cash_receipts_journal_company_id ON cash_receipts_journal(company_id);
CREATE INDEX idx_purchase_journal_company_id ON purchase_journal(company_id);
CREATE INDEX idx_cash_disbursement_journal_company_id ON cash_disbursement_journal(company_id);
CREATE INDEX idx_general_journal_company_id ON general_journal(company_id);
CREATE INDEX idx_general_ledger_company_id ON general_ledger(company_id);
CREATE INDEX idx_products_company_id ON products(company_id);
CREATE INDEX idx_employees_company_id ON employees(company_id);

-- Date-based indexes
CREATE INDEX idx_sales_journal_date ON sales_journal(transaction_date);
CREATE INDEX idx_cash_receipts_journal_date ON cash_receipts_journal(transaction_date);
CREATE INDEX idx_purchase_journal_date ON purchase_journal(transaction_date);
CREATE INDEX idx_cash_disbursement_journal_date ON cash_disbursement_journal(transaction_date);
CREATE INDEX idx_general_journal_date ON general_journal(transaction_date);
CREATE INDEX idx_general_ledger_date ON general_ledger(transaction_date);

-- Status-based indexes
CREATE INDEX idx_sales_journal_status ON sales_journal(status);
CREATE INDEX idx_cash_receipts_journal_status ON cash_receipts_journal(status);
CREATE INDEX idx_purchase_journal_status ON purchase_journal(status);
CREATE INDEX idx_cash_disbursement_journal_status ON cash_disbursement_journal(status);
CREATE INDEX idx_general_journal_status ON general_journal(status);

-- =====================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- =====================================================

-- Enable RLS on all tables
ALTER TABLE companies ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE chart_of_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE sales_journal ENABLE ROW LEVEL SECURITY;
ALTER TABLE cash_receipts_journal ENABLE ROW LEVEL SECURITY;
ALTER TABLE purchase_journal ENABLE ROW LEVEL SECURITY;
ALTER TABLE cash_disbursement_journal ENABLE ROW LEVEL SECURITY;
ALTER TABLE general_journal ENABLE ROW LEVEL SECURITY;
ALTER TABLE general_journal_lines ENABLE ROW LEVEL SECURITY;
ALTER TABLE general_ledger ENABLE ROW LEVEL SECURITY;
ALTER TABLE products ENABLE ROW LEVEL SECURITY;
ALTER TABLE purchase_orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE purchase_order_lines ENABLE ROW LEVEL SECURITY;
ALTER TABLE sales_orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE sales_order_lines ENABLE ROW LEVEL SECURITY;
ALTER TABLE delivery_receipts ENABLE ROW LEVEL SECURITY;
ALTER TABLE delivery_receipt_lines ENABLE ROW LEVEL SECURITY;
ALTER TABLE employees ENABLE ROW LEVEL SECURITY;
ALTER TABLE payroll_periods ENABLE ROW LEVEL SECURITY;
ALTER TABLE payroll_details ENABLE ROW LEVEL SECURITY;
ALTER TABLE bir_forms_config ENABLE ROW LEVEL SECURITY;
ALTER TABLE tax_payments ENABLE ROW LEVEL SECURITY;
ALTER TABLE bank_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE bank_statements ENABLE ROW LEVEL SECURITY;
ALTER TABLE bank_statement_lines ENABLE ROW LEVEL SECURITY;
ALTER TABLE fixed_assets ENABLE ROW LEVEL SECURITY;
ALTER TABLE depreciation_schedule ENABLE ROW LEVEL SECURITY;

-- RLS Policies
-- Users can only access their own company's data
CREATE POLICY "Users can view own company data" ON companies
    FOR ALL USING (id IN (
        SELECT company_id FROM users WHERE id = auth.uid()
    ));

CREATE POLICY "Users can view own profile" ON users
    FOR ALL USING (id = auth.uid());

-- Company-specific policies
CREATE POLICY "Company access for chart_of_accounts" ON chart_of_accounts
    FOR ALL USING (company_id IN (
        SELECT company_id FROM users WHERE id = auth.uid()
    ));

CREATE POLICY "Company access for sales_journal" ON sales_journal
    FOR ALL USING (company_id IN (
        SELECT company_id FROM users WHERE id = auth.uid()
    ));

CREATE POLICY "Company access for cash_receipts_journal" ON cash_receipts_journal
    FOR ALL USING (company_id IN (
        SELECT company_id FROM users WHERE id = auth.uid()
    ));

CREATE POLICY "Company access for purchase_journal" ON purchase_journal
    FOR ALL USING (company_id IN (
        SELECT company_id FROM users WHERE id = auth.uid()
    ));

CREATE POLICY "Company access for cash_disbursement_journal" ON cash_disbursement_journal
    FOR ALL USING (company_id IN (
        SELECT company_id FROM users WHERE id = auth.uid()
    ));

CREATE POLICY "Company access for general_journal" ON general_journal
    FOR ALL USING (company_id IN (
        SELECT company_id FROM users WHERE id = auth.uid()
    ));

CREATE POLICY "Company access for general_ledger" ON general_ledger
    FOR ALL USING (company_id IN (
        SELECT company_id FROM users WHERE id = auth.uid()
    ));

-- Similar policies for other tables...
CREATE POLICY "Company access for products" ON products
    FOR ALL USING (company_id IN (
        SELECT company_id FROM users WHERE id = auth.uid()
    ));

CREATE POLICY "Company access for employees" ON employees
    FOR ALL USING (company_id IN (
        SELECT company_id FROM users WHERE id = auth.uid()
    ));

-- =====================================================
-- TRIGGERS AND FUNCTIONS
-- =====================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at triggers
CREATE TRIGGER update_companies_updated_at BEFORE UPDATE ON companies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_chart_of_accounts_updated_at BEFORE UPDATE ON chart_of_accounts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to post journal entries to ledger
CREATE OR REPLACE FUNCTION post_to_ledger()
RETURNS TRIGGER AS $$
BEGIN
    -- This function will be called when journals are posted
    -- Implementation will be added in the application layer
    RETURN NEW;
END;
$$ language 'plpgsql';

-- =====================================================
-- VIEWS FOR REPORTING
-- =====================================================

-- Trial Balance View
CREATE VIEW trial_balance AS
SELECT 
    coa.account_code,
    coa.account_name,
    coa.account_type,
    coa.normal_balance,
    COALESCE(SUM(gl.debit_amount), 0) as total_debits,
    COALESCE(SUM(gl.credit_amount), 0) as total_credits,
    CASE 
        WHEN coa.normal_balance = 'DEBIT' THEN 
            COALESCE(SUM(gl.debit_amount), 0) - COALESCE(SUM(gl.credit_amount), 0)
        ELSE 
            COALESCE(SUM(gl.credit_amount), 0) - COALESCE(SUM(gl.debit_amount), 0)
    END as balance
FROM chart_of_accounts coa
LEFT JOIN general_ledger gl ON coa.id = gl.account_id
WHERE coa.is_active = true
GROUP BY coa.id, coa.account_code, coa.account_name, coa.account_type, coa.normal_balance
ORDER BY coa.account_code;

-- Financial Summary View
CREATE VIEW financial_summary AS
SELECT 
    gl.company_id,
    EXTRACT(YEAR FROM gl.transaction_date) as fiscal_year,
    EXTRACT(QUARTER FROM gl.transaction_date) as quarter,
    EXTRACT(MONTH FROM gl.transaction_date) as month,
    SUM(CASE WHEN coa.account_type = 'REVENUE' THEN gl.credit_amount - gl.debit_amount ELSE 0 END) as total_revenue,
    SUM(CASE WHEN coa.account_type = 'EXPENSE' THEN gl.debit_amount - gl.credit_amount ELSE 0 END) as total_expenses,
    SUM(CASE WHEN coa.account_type = 'ASSET' THEN gl.debit_amount - gl.credit_amount ELSE 0 END) as total_assets,
    SUM(CASE WHEN coa.account_type = 'LIABILITY' THEN gl.credit_amount - gl.debit_amount ELSE 0 END) as total_liabilities,
    SUM(CASE WHEN coa.account_type = 'EQUITY' THEN gl.credit_amount - gl.debit_amount ELSE 0 END) as total_equity
FROM general_ledger gl
JOIN chart_of_accounts coa ON gl.account_id = coa.id
GROUP BY gl.company_id, EXTRACT(YEAR FROM gl.transaction_date), 
         EXTRACT(QUARTER FROM gl.transaction_date), 
         EXTRACT(MONTH FROM gl.transaction_date)
ORDER BY gl.company_id, fiscal_year, quarter, month;
