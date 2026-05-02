-- Migration: Add business settings columns to profiles table
-- This migration adds the missing columns for business settings

-- Add business_name column if it doesn't exist
ALTER TABLE profiles 
ADD COLUMN IF NOT EXISTS business_name TEXT DEFAULT '';

-- Add tin column if it doesn't exist
ALTER TABLE profiles 
ADD COLUMN IF NOT EXISTS tin TEXT DEFAULT '000-000-000-000';

-- Add business_address column if it doesn't exist
ALTER TABLE profiles 
ADD COLUMN IF NOT EXISTS business_address TEXT DEFAULT '';

-- Add tax_type column if it doesn't exist
ALTER TABLE profiles 
ADD COLUMN IF NOT EXISTS tax_type TEXT DEFAULT 'VAT (12%)';

-- Add logo_url column if it doesn't exist
ALTER TABLE profiles 
ADD COLUMN IF NOT EXISTS logo_url TEXT DEFAULT '';
