-- Full SQL Editor Prompt to Reset Database Schema and RLS Policies
-- Run this in your Supabase SQL Editor to fix all database issues

-- 1. Drop existing tables and constraints
DROP TABLE IF EXISTS transactions CASCADE;
DROP TABLE IF EXISTS profiles CASCADE;
DROP TABLE IF EXISTS license_keys CASCADE;

-- 2. Create profiles table
CREATE TABLE profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id),
    email TEXT UNIQUE NOT NULL,
    business_name TEXT NOT NULL,
    tax_type TEXT NOT NULL DEFAULT 'VAT (12%)',
    is_pro_status BOOLEAN DEFAULT FALSE,
    license_key TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Create transactions table with all necessary columns
CREATE TABLE transactions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
    transaction_date TIMESTAMP WITH TIME ZONE NOT NULL,
    type TEXT NOT NULL,
    description TEXT,
    customer_name TEXT,
    supplier_name TEXT,
    expense_category TEXT,
    gross_amount DECIMAL(15,2) NOT NULL DEFAULT 0,
    net_amount DECIMAL(15,2) NOT NULL DEFAULT 0,
    vat_amount DECIMAL(15,2) NOT NULL DEFAULT 0,
    ewt_amount DECIMAL(15,2) NOT NULL DEFAULT 0,
    final_amount DECIMAL(15,2) NOT NULL DEFAULT 0,
    payment_method TEXT,
    bank_name TEXT,
    check_number TEXT,
    tax_type TEXT NOT NULL DEFAULT 'VAT (12%)',
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraint that accepts both capitalized and lowercase transaction types
    CONSTRAINT transactions_type_check CHECK (
        type IN ('Sales', 'sales', 'Purchase', 'purchase', 'Expense', 'expense', 'Cash Receipt', 'cash_receipt', 'Cash Disbursement', 'cash_disbursement', 'General Journal', 'general_journal')
    ),
    
    -- Status constraint that accepts both cases
    CONSTRAINT transactions_status_check CHECK (
        status IN ('active', 'inactive', 'cancelled', 'Active', 'Inactive', 'Cancelled')
    )
);

-- 4. Create license_keys table
CREATE TABLE license_keys (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    key TEXT UNIQUE NOT NULL,
    is_used BOOLEAN DEFAULT FALSE,
    used_by UUID REFERENCES profiles(id),
    used_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. Enable RLS on all tables
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE license_keys ENABLE ROW LEVEL SECURITY;

-- 6. Create RLS policies for profiles
CREATE POLICY users_can_view_own_profile ON profiles
    FOR SELECT USING (auth.uid() = id);
    
CREATE POLICY users_can_update_own_profile ON profiles
    FOR UPDATE USING (auth.uid() = id);

-- 7. Create RLS policies for transactions
CREATE POLICY users_can_view_own_transactions ON transactions
    FOR SELECT USING (auth.uid() = user_id);
    
CREATE POLICY users_can_insert_own_transactions ON transactions
    FOR INSERT WITH CHECK (auth.uid() = user_id);
    
CREATE POLICY users_can_update_own_transactions ON transactions
    FOR UPDATE USING (auth.uid() = user_id);
    
CREATE POLICY users_can_delete_own_transactions ON transactions
    FOR DELETE USING (auth.uid() = user_id);

-- 8. Create RLS policies for license_keys
CREATE POLICY users_can_view_license_keys ON license_keys
    FOR SELECT USING (true);
    
CREATE POLICY users_can_insert_license_keys ON license_keys
    FOR INSERT WITH CHECK (true);
    
CREATE POLICY users_can_update_license_keys ON license_keys
    FOR UPDATE USING (true);
    
CREATE POLICY users_can_delete_license_keys ON license_keys
    FOR DELETE USING (true);

-- 9. Create indexes for better performance
CREATE INDEX idx_transactions_user_id ON transactions(user_id);
CREATE INDEX idx_transactions_type ON transactions(type);
CREATE INDEX idx_transactions_date ON transactions(transaction_date);
CREATE INDEX idx_transactions_status ON transactions(status);

-- 10. Create updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_profiles_updated_at BEFORE UPDATE ON profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_transactions_updated_at BEFORE UPDATE ON transactions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
