-- LedgerPro-PH Production Database Schema
-- Run this in Supabase SQL Editor to set up the production database

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Profiles table for user information
CREATE TABLE IF NOT EXISTS profiles (
    id UUID PRIMARY KEY DEFAULT auth.uid(),
    email TEXT UNIQUE NOT NULL,
    business_name TEXT NOT NULL,
    tax_type TEXT NOT NULL DEFAULT 'VAT (12%)',
    is_pro_status BOOLEAN DEFAULT FALSE,
    license_key TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Transactions table for all financial transactions
CREATE TABLE IF NOT EXISTS transactions (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
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

-- License keys table for monetization
CREATE TABLE IF NOT EXISTS license_keys (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    key TEXT UNIQUE NOT NULL,
    is_used BOOLEAN DEFAULT FALSE,
    used_by UUID REFERENCES profiles(id),
    used_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable Row Level Security
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
    
DROP POLICY IF EXISTS users_can_insert_own_profile ON profiles;
CREATE POLICY users_can_insert_own_profile ON profiles
    FOR INSERT WITH CHECK (auth.uid() = id);

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

-- License keys RLS policies
DROP POLICY IF EXISTS anyone_can_view_unused_license_keys ON license_keys;
CREATE POLICY anyone_can_view_unused_license_keys ON license_keys
    FOR SELECT USING (is_used = FALSE);
    
DROP POLICY IF EXISTS anyone_can_use_license_keys ON license_keys;
CREATE POLICY anyone_can_use_license_keys ON license_keys
    FOR UPDATE USING (is_used = FALSE);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(transaction_date);
CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions(type);
CREATE INDEX IF NOT EXISTS idx_transactions_status ON transactions(status);
CREATE INDEX IF NOT EXISTS idx_profiles_email ON profiles(email);
CREATE INDEX IF NOT EXISTS idx_license_keys_key ON license_keys(key);
CREATE INDEX IF NOT EXISTS idx_license_keys_used ON license_keys(is_used);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_profiles_updated_at BEFORE UPDATE ON profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    
CREATE TRIGGER update_transactions_updated_at BEFORE UPDATE ON transactions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert sample license keys (you can generate these for your Ko-fi store)
INSERT INTO license_keys (key, expires_at) VALUES 
    ('DEMO-PRO-2024-001', '2025-12-31 23:59:59'),
    ('DEMO-PRO-2024-002', '2025-12-31 23:59:59'),
    ('DEMO-PRO-2024-003', '2025-12-31 23:59:59'),
    ('DEMO-PRO-2024-004', '2025-12-31 23:59:59'),
    ('DEMO-PRO-2024-005', '2025-12-31 23:59:59')
ON CONFLICT (key) DO NOTHING;

-- Grant necessary permissions
GRANT ALL ON profiles TO authenticated;
GRANT ALL ON transactions TO authenticated;
GRANT SELECT, UPDATE ON license_keys TO authenticated;
