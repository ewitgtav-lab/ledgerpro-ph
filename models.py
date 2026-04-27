import sqlite3
import datetime
from typing import Optional, List, Dict, Any
import os

class DatabaseManager:
    """Manages SQLite database operations for the Pang-Kape Bookkeeping System"""
    
    def __init__(self, db_path: str = "bir_database.db"):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection with foreign key constraints enabled"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """Initialize all database tables with proper relationships"""
        try:
            with self.get_connection() as conn:
                # Chart of Accounts
                conn.execute("""
                CREATE TABLE IF NOT EXISTS chart_of_accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_code VARCHAR(10) UNIQUE NOT NULL,
                    account_name VARCHAR(200) NOT NULL,
                    account_type VARCHAR(50) NOT NULL CHECK (account_type IN ('Asset', 'Liability', 'Equity', 'Revenue', 'Expense')),
                    normal_balance VARCHAR(10) NOT NULL CHECK (normal_balance IN ('Debit', 'Credit')),
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Cash Receipt Journal (CRJ)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cash_receipt_journal (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    transaction_date DATE NOT NULL,
                    reference_number VARCHAR(50),
                    customer_name VARCHAR(200),
                    customer_tin VARCHAR(20),
                    account_code VARCHAR(10) NOT NULL,
                    description TEXT,
                    gross_sales DECIMAL(15,2) DEFAULT 0,
                    vat_output DECIMAL(15,2) DEFAULT 0,
                    net_sales DECIMAL(15,2) DEFAULT 0,
                    platform_name VARCHAR(50),
                    commission_fee DECIMAL(15,2) DEFAULT 0,
                    shipping_subsidy DECIMAL(15,2) DEFAULT 0,
                    total_cash_received DECIMAL(15,2) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (account_code) REFERENCES chart_of_accounts(account_code)
                )
            """)
            
            # Cash Disbursement Journal (CDJ)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cash_disbursement_journal (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    transaction_date DATE NOT NULL,
                    reference_number VARCHAR(50),
                    payee_name VARCHAR(200),
                    payee_tin VARCHAR(20),
                    account_code VARCHAR(10) NOT NULL,
                    expense_category VARCHAR(100),
                    description TEXT,
                    amount DECIMAL(15,2) NOT NULL,
                    vat_input DECIMAL(15,2) DEFAULT 0,
                    ewt DECIMAL(15,2) DEFAULT 0,
                    net_amount DECIMAL(15,2) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (account_code) REFERENCES chart_of_accounts(account_code)
                )
            """)
            
            # General Ledger
            conn.execute("""
                CREATE TABLE IF NOT EXISTS general_ledger (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    transaction_date DATE NOT NULL,
                    reference_number VARCHAR(50),
                    account_code VARCHAR(10) NOT NULL,
                    description TEXT,
                    debit_amount DECIMAL(15,2) DEFAULT 0,
                    credit_amount DECIMAL(15,2) DEFAULT 0,
                    balance DECIMAL(15,2) NOT NULL,
                    source_journal VARCHAR(20) NOT NULL CHECK (source_journal IN ('CRJ', 'CDJ', 'Manual')),
                    source_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (account_code) REFERENCES chart_of_accounts(account_code)
                )
            """)
            
            # Receipt Serial Numbers
            conn.execute("""
                CREATE TABLE IF NOT EXISTS receipt_serials (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    receipt_type VARCHAR(20) NOT NULL CHECK (receipt_type IN ('Sales Invoice', 'Service Invoice', 'Official Receipt')),
                    serial_prefix VARCHAR(10) NOT NULL,
                    current_number INTEGER NOT NULL DEFAULT 1,
                    year INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(receipt_type, serial_prefix, year)
                )
            """)
            
            # Generated Receipts
            conn.execute("""
                CREATE TABLE IF NOT EXISTS generated_receipts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    receipt_type VARCHAR(20) NOT NULL,
                    serial_number VARCHAR(50) UNIQUE NOT NULL,
                    customer_name VARCHAR(200),
                    customer_tin VARCHAR(20),
                    customer_address TEXT,
                    transaction_date DATE NOT NULL,
                    items TEXT, -- JSON string of items
                    total_amount DECIMAL(15,2) NOT NULL,
                    vat_amount DECIMAL(15,2) DEFAULT 0,
                    pdf_path VARCHAR(500),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tax Settings
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tax_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tax_year INTEGER UNIQUE NOT NULL,
                    tax_regime VARCHAR(20) NOT NULL CHECK (tax_regime IN ('8% Flat Rate', 'Graduated Rates', 'Mixed')),
                    business_name VARCHAR(200),
                    owner_name VARCHAR(200),
                    tin VARCHAR(20),
                    address TEXT,
                    registered_date DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tax Computations
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tax_computations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tax_year INTEGER NOT NULL,
                    tax_period VARCHAR(20) NOT NULL CHECK (tax_period IN ('Quarter 1', 'Quarter 2', 'Quarter 3', 'Quarter 4', 'Annual')),
                    gross_sales DECIMAL(15,2) DEFAULT 0,
                    gross_receipts DECIMAL(15,2) DEFAULT 0,
                    non_operating_income DECIMAL(15,2) DEFAULT 0,
                    total_income DECIMAL(15,2) DEFAULT 0,
                    cost_of_goods_sold DECIMAL(15,2) DEFAULT 0,
                    business_expenses DECIMAL(15,2) DEFAULT 0,
                    net_taxable_income DECIMAL(15,2) DEFAULT 0,
                    tax_regime VARCHAR(20) NOT NULL,
                    tax_due DECIMAL(15,2) DEFAULT 0,
                    quarterly_tax_paid DECIMAL(15,2) DEFAULT 0,
                    remaining_tax_due DECIMAL(15,2) DEFAULT 0,
                    computation_details TEXT, -- JSON string of detailed computation
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (tax_regime) REFERENCES tax_settings(tax_regime)
                )
            """)
            
            self._insert_default_accounts(conn)
            conn.commit()
        except Exception as e:
            print(f"Database initialization error: {e}")
            # Continue without database - will be created on first use
    
    def _insert_default_accounts(self, conn: sqlite3.Connection):
        """Insert default chart of accounts"""
        default_accounts = [
            # Assets
            ('101001', 'Cash on Hand', 'Asset', 'Debit'),
            ('101002', 'Cash in Bank', 'Asset', 'Debit'),
            ('101003', 'Accounts Receivable', 'Asset', 'Debit'),
            
            # Liabilities
            ('201001', 'Accounts Payable', 'Liability', 'Credit'),
            ('201002', 'VAT Payable', 'Liability', 'Credit'),
            ('201003', 'Withholding Tax Payable', 'Liability', 'Credit'),
            ('201004', 'Income Tax Payable', 'Liability', 'Credit'),
            
            # Equity
            ('301001', 'Owner\'s Capital', 'Equity', 'Credit'),
            ('301002', 'Owner\'s Drawings', 'Equity', 'Debit'),
            
            # Revenue
            ('401001', 'Sales Revenue', 'Revenue', 'Credit'),
            ('401002', 'Service Revenue', 'Revenue', 'Credit'),
            ('401003', 'Other Income', 'Revenue', 'Credit'),
            
            # Expenses
            ('501001', 'Cost of Goods Sold', 'Expense', 'Debit'),
            ('501002', 'Platform Fees', 'Expense', 'Debit'),
            ('501003', 'Shipping Expenses', 'Expense', 'Debit'),
            ('501004', 'Marketing Expenses', 'Expense', 'Debit'),
            ('501005', 'Office Supplies', 'Expense', 'Debit'),
            ('501006', 'Internet Expenses', 'Expense', 'Debit'),
            ('501007', 'Utilities', 'Expense', 'Debit'),
            ('501008', 'Repairs and Maintenance', 'Expense', 'Debit'),
            ('501009', 'Depreciation Expense', 'Expense', 'Debit'),
            ('501010', 'Miscellaneous Expenses', 'Expense', 'Debit'),
        ]
        
        for account in default_accounts:
            conn.execute("""
                INSERT OR IGNORE INTO chart_of_accounts 
                (account_code, account_name, account_type, normal_balance)
                VALUES (?, ?, ?, ?)
            """, account)
    
    # Cash Receipt Journal Methods
    def add_crj_entry(self, entry_data: Dict[str, Any]) -> int:
        """Add entry to Cash Receipt Journal and auto-post to General Ledger"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO cash_receipt_journal 
                (transaction_date, reference_number, customer_name, customer_tin, 
                 account_code, description, gross_sales, vat_output, net_sales,
                 platform_name, commission_fee, shipping_subsidy, total_cash_received)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entry_data['transaction_date'],
                entry_data.get('reference_number'),
                entry_data.get('customer_name'),
                entry_data.get('customer_tin'),
                entry_data['account_code'],
                entry_data.get('description'),
                entry_data.get('gross_sales', 0),
                entry_data.get('vat_output', 0),
                entry_data.get('net_sales', 0),
                entry_data.get('platform_name'),
                entry_data.get('commission_fee', 0),
                entry_data.get('shipping_subsidy', 0),
                entry_data['total_cash_received']
            ))
            
            crj_id = cursor.lastrowid
            
            # Auto-post to General Ledger
            self._post_crj_to_ledger(conn, crj_id, entry_data)
            
            conn.commit()
            return crj_id
    
    def _post_crj_to_ledger(self, conn: sqlite3.Connection, crj_id: int, entry_data: Dict[str, Any]):
        """Post CRJ entry to General Ledger with double-entry bookkeeping"""
        # Debit Cash
        conn.execute("""
            INSERT INTO general_ledger 
            (transaction_date, reference_number, account_code, description, 
             debit_amount, credit_amount, balance, source_journal, source_id)
            VALUES (?, ?, ?, ?, ?, ?, 
                   (SELECT COALESCE(MAX(balance), 0) + ? FROM general_ledger 
                    WHERE account_code = ? ORDER BY id DESC LIMIT 1) + ?,
                   ?, ?)
        """, (
            entry_data['transaction_date'],
            entry_data.get('reference_number'),
            '101001',  # Cash on Hand
            entry_data.get('description'),
            entry_data['total_cash_received'],
            0,
            entry_data['total_cash_received'],
            '101001',
            entry_data['total_cash_received'],
            'CRJ',
            crj_id
        ))
        
        # Credit Sales Revenue
        net_sales = entry_data.get('net_sales', entry_data['total_cash_received'])
        conn.execute("""
            INSERT INTO general_ledger 
            (transaction_date, reference_number, account_code, description, 
             debit_amount, credit_amount, balance, source_journal, source_id)
            VALUES (?, ?, ?, ?, ?, ?, 
                   (SELECT COALESCE(MAX(balance), 0) + ? FROM general_ledger 
                    WHERE account_code = ? ORDER BY id DESC LIMIT 1) + ?,
                   ?, ?)
        """, (
            entry_data['transaction_date'],
            entry_data.get('reference_number'),
            entry_data['account_code'],
            entry_data.get('description'),
            0,
            net_sales,
            -net_sales,  # Credit reduces balance for revenue accounts
            entry_data['account_code'],
            -net_sales,
            'CRJ',
            crj_id
        ))
    
    # Cash Disbursement Journal Methods
    def add_cdj_entry(self, entry_data: Dict[str, Any]) -> int:
        """Add entry to Cash Disbursement Journal and auto-post to General Ledger"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO cash_disbursement_journal 
                (transaction_date, reference_number, payee_name, payee_tin,
                 account_code, expense_category, description, amount,
                 vat_input, ewt, net_amount)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entry_data['transaction_date'],
                entry_data.get('reference_number'),
                entry_data.get('payee_name'),
                entry_data.get('payee_tin'),
                entry_data['account_code'],
                entry_data.get('expense_category'),
                entry_data.get('description'),
                entry_data['amount'],
                entry_data.get('vat_input', 0),
                entry_data.get('ewt', 0),
                entry_data['net_amount']
            ))
            
            cdj_id = cursor.lastrowid
            
            # Auto-post to General Ledger
            self._post_cdj_to_ledger(conn, cdj_id, entry_data)
            
            conn.commit()
            return cdj_id
    
    def _post_cdj_to_ledger(self, conn: sqlite3.Connection, cdj_id: int, entry_data: Dict[str, Any]):
        """Post CDJ entry to General Ledger with double-entry bookkeeping"""
        # Credit Cash
        conn.execute("""
            INSERT INTO general_ledger 
            (transaction_date, reference_number, account_code, description, 
             debit_amount, credit_amount, balance, source_journal, source_id)
            VALUES (?, ?, ?, ?, ?, ?, 
                   (SELECT COALESCE(MAX(balance), 0) + ? FROM general_ledger 
                    WHERE account_code = ? ORDER BY id DESC LIMIT 1) + ?,
                   ?, ?)
        """, (
            entry_data['transaction_date'],
            entry_data.get('reference_number'),
            '101001',  # Cash on Hand
            entry_data.get('description'),
            0,
            entry_data['net_amount'],
            -entry_data['net_amount'],  # Credit reduces cash balance
            '101001',
            -entry_data['net_amount'],
            'CDJ',
            cdj_id
        ))
        
        # Debit Expense Account
        conn.execute("""
            INSERT INTO general_ledger 
            (transaction_date, reference_number, account_code, description, 
             debit_amount, credit_amount, balance, source_journal, source_id)
            VALUES (?, ?, ?, ?, ?, ?, 
                   (SELECT COALESCE(MAX(balance), 0) + ? FROM general_ledger 
                    WHERE account_code = ? ORDER BY id DESC LIMIT 1) + ?,
                   ?, ?)
        """, (
            entry_data['transaction_date'],
            entry_data.get('reference_number'),
            entry_data['account_code'],
            entry_data.get('description'),
            entry_data['amount'],
            0,
            entry_data['amount'],
            entry_data['account_code'],
            entry_data['amount'],
            'CDJ',
            cdj_id
        ))
    
    def get_trial_balance(self, as_of_date: str = None) -> List[Dict[str, Any]]:
        """Generate trial balance as of specific date"""
        with self.get_connection() as conn:
            date_filter = ""
            params = []
            if as_of_date:
                date_filter = "WHERE gl.transaction_date <= ?"
                params = [as_of_date]
            
            query = f"""
                SELECT 
                    coa.account_code,
                    coa.account_name,
                    coa.account_type,
                    coa.normal_balance,
                    SUM(gl.debit_amount) as total_debits,
                    SUM(gl.credit_amount) as total_credits,
                    CASE 
                        WHEN coa.normal_balance = 'Debit' THEN 
                            SUM(gl.debit_amount) - SUM(gl.credit_amount)
                        ELSE 
                            SUM(gl.credit_amount) - SUM(gl.debit_amount)
                    END as balance
                FROM chart_of_accounts coa
                LEFT JOIN general_ledger gl ON coa.account_code = gl.account_code
                {date_filter}
                GROUP BY coa.account_code, coa.account_name, coa.account_type, coa.normal_balance
                ORDER BY coa.account_type, coa.account_code
            """
            
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_accounts_by_type(self, account_type: str) -> List[Dict[str, Any]]:
        """Get accounts filtered by type"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT account_code, account_name, account_type, normal_balance
                FROM chart_of_accounts 
                WHERE account_type = ? AND is_active = 1
                ORDER BY account_code
            """, (account_type,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_next_receipt_serial(self, receipt_type: str, prefix: str = "SI") -> str:
        """Get next serial number for receipts"""
        current_year = datetime.datetime.now().year
        
        with self.get_connection() as conn:
            # Insert or update serial tracking
            conn.execute("""
                INSERT OR REPLACE INTO receipt_serials 
                (receipt_type, serial_prefix, current_number, year)
                VALUES (?, ?, 
                        COALESCE((SELECT current_number FROM receipt_serials 
                                 WHERE receipt_type = ? AND serial_prefix = ? AND year = ?), 0) + 1,
                        ?)
            """, (receipt_type, prefix, receipt_type, prefix, current_year, current_year))
            
            # Get the new serial number
            cursor = conn.execute("""
                SELECT current_number FROM receipt_serials 
                WHERE receipt_type = ? AND serial_prefix = ? AND year = ?
            """, (receipt_type, prefix, current_year))
            
            serial_number = cursor.fetchone()['current_number']
            return f"{prefix}-{current_year:04d}-{serial_number:06d}"
