"""
Tax Engine for Pang-Kape Bookkeeping System
Calculates Philippine taxes for 2026 including 8% Flat Rate and Graduated Rates
"""

import json
from datetime import datetime, date
from typing import Dict, Any, Optional, List
from models import DatabaseManager

class TaxCalculator:
    """Philippine Tax Calculator for 2026"""
    
    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.db = db_manager or DatabaseManager()
        
        # 2026 Graduated Tax Rates (for individuals)
        self.graduated_rates_2026 = [
            {'min': 0, 'max': 250000, 'rate': 0, 'base_tax': 0},
            {'min': 250001, 'max': 400000, 'rate': 0.20, 'base_tax': 0},
            {'min': 400001, 'max': 800000, 'rate': 0.25, 'base_tax': 30000},
            {'min': 800001, 'max': 2000000, 'rate': 0.30, 'base_tax': 130000},
            {'min': 2000001, 'max': 8000000, 'rate': 0.32, 'base_tax': 490000},
            {'min': 8000001, 'max': float('inf'), 'rate': 0.35, 'base_tax': 2410000}
        ]
        
        # 8% Flat Rate Settings
        self.flat_rate_settings = {
            'rate': 0.08,
            'deduction': 250000,  # Standard deduction for non-mixed income
            'applicable_income_types': ['business_income', 'professional_income']
        }
    
    def calculate_tax(self, tax_year: int, period: str = "Annual", 
                     regime: str = "8% Flat Rate") -> Dict[str, Any]:
        """
        Calculate tax based on regime and period
        
        Args:
            tax_year: Tax year (e.g., 2026)
            period: "Quarter 1", "Quarter 2", "Quarter 3", "Quarter 4", or "Annual"
            regime: "8% Flat Rate", "Graduated Rates", or "Mixed"
        
        Returns:
            Dictionary with tax computation details
        """
        
        # Get financial data from database
        financial_data = self._get_financial_data(tax_year, period)
        
        if regime == "8% Flat Rate":
            return self._calculate_flat_rate_tax(financial_data, tax_year, period)
        elif regime == "Graduated Rates":
            return self._calculate_graduated_tax(financial_data, tax_year, period)
        elif regime == "Mixed":
            return self._calculate_mixed_tax(financial_data, tax_year, period)
        else:
            raise ValueError(f"Unknown tax regime: {regime}")
    
    def _get_financial_data(self, tax_year: int, period: str) -> Dict[str, float]:
        """Extract financial data from database for tax computation"""
        
        # Determine date range based on period
        if period == "Quarter 1":
            start_date = f"{tax_year}-01-01"
            end_date = f"{tax_year}-03-31"
        elif period == "Quarter 2":
            start_date = f"{tax_year}-04-01"
            end_date = f"{tax_year}-06-30"
        elif period == "Quarter 3":
            start_date = f"{tax_year}-07-01"
            end_date = f"{tax_year}-09-30"
        elif period == "Quarter 4":
            start_date = f"{tax_year}-10-01"
            end_date = f"{tax_year}-12-31"
        elif period == "Annual":
            start_date = f"{tax_year}-01-01"
            end_date = f"{tax_year}-12-31"
        else:
            raise ValueError(f"Invalid period: {period}")
        
        with self.db.get_connection() as conn:
            # Get gross sales from CRJ
            cursor = conn.execute("""
                SELECT 
                    SUM(gross_sales) as total_gross_sales,
                    SUM(net_sales) as total_net_sales,
                    SUM(vat_output) as total_vat_output,
                    SUM(commission_fee) as total_commission,
                    SUM(shipping_subsidy) as total_shipping
                FROM cash_receipt_journal 
                WHERE transaction_date BETWEEN ? AND ?
            """, (start_date, end_date))
            
            sales_data = cursor.fetchone()
            
            # Get total expenses from CDJ
            cursor = conn.execute("""
                SELECT 
                    SUM(amount) as total_expenses,
                    SUM(vat_input) as total_vat_input,
                    SUM(ewt) as total_ewt
                FROM cash_disbursement_journal 
                WHERE transaction_date BETWEEN ? AND ?
            """, (start_date, end_date))
            
            expense_data = cursor.fetchone()
            
            # Get other income (non-operating)
            cursor = conn.execute("""
                SELECT SUM(credit_amount) as other_income
                FROM general_ledger 
                WHERE transaction_date BETWEEN ? AND ?
                AND account_code LIKE '403%'  # Other income accounts
            """, (start_date, end_date))
            
            other_income_data = cursor.fetchone()
        
        return {
            'gross_sales': sales_data['total_gross_sales'] or 0,
            'net_sales': sales_data['total_net_sales'] or 0,
            'vat_output': sales_data['total_vat_output'] or 0,
            'commission_fees': sales_data['total_commission'] or 0,
            'shipping_subsidies': sales_data['total_shipping'] or 0,
            'total_expenses': expense_data['total_expenses'] or 0,
            'vat_input': expense_data['total_vat_input'] or 0,
            'ewt': expense_data['total_ewt'] or 0,
            'other_income': other_income_data['other_income'] or 0
        }
    
    def _calculate_flat_rate_tax(self, financial_data: Dict[str, float], 
                                tax_year: int, period: str) -> Dict[str, Any]:
        """Calculate tax using 8% flat rate regime"""
        
        # Calculate total income
        gross_income = (financial_data['gross_sales'] + 
                       financial_data['other_income'])
        
        # Apply standard deduction for non-mixed income
        taxable_income = max(0, gross_income - self.flat_rate_settings['deduction'])
        
        # Calculate 8% tax
        tax_due = taxable_income * self.flat_rate_settings['rate']
        
        # For quarterly periods, adjust proportionally
        if period != "Annual":
            quarter_multiplier = 0.25  # Each quarter is 1/4 of annual
            tax_due *= quarter_multiplier
        
        # Get quarterly tax paid (if any)
        quarterly_paid = self._get_quarterly_tax_paid(tax_year, period)
        
        remaining_tax = max(0, tax_due - quarterly_paid)
        
        computation = {
            'regime': '8% Flat Rate',
            'tax_year': tax_year,
            'period': period,
            'gross_sales': financial_data['gross_sales'],
            'other_income': financial_data['other_income'],
            'total_income': gross_income,
            'standard_deduction': self.flat_rate_settings['deduction'],
            'net_taxable_income': taxable_income,
            'tax_rate': self.flat_rate_settings['rate'],
            'tax_due': tax_due,
            'quarterly_tax_paid': quarterly_paid,
            'remaining_tax_due': remaining_tax,
            'computation_details': {
                'gross_income': gross_income,
                'less_deduction': self.flat_rate_settings['deduction'],
                'taxable_income': taxable_income,
                'tax_rate_percent': 8,
                'computed_tax': tax_due
            }
        }
        
        # Save computation to database
        self._save_tax_computation(computation)
        
        return computation
    
    def _calculate_graduated_tax(self, financial_data: Dict[str, float], 
                                tax_year: int, period: str) -> Dict[str, Any]:
        """Calculate tax using graduated rates"""
        
        # Calculate net taxable income
        gross_income = (financial_data['gross_sales'] + 
                       financial_data['other_income'])
        
        # Allowable deductions (OSOC - Optional Standard Deduction or Itemized)
        # For simplicity, using 40% OSD or itemized, whichever is higher
        osd = gross_income * 0.40
        itemized_deductions = financial_data['total_expenses']
        
        allowable_deductions = max(osd, itemized_deductions)
        
        net_taxable_income = max(0, gross_income - allowable_deductions)
        
        # Calculate tax using graduated rates
        tax_due = self._compute_graduated_tax(net_taxable_income)
        
        # For quarterly periods, adjust proportionally
        if period != "Annual":
            quarter_multiplier = 0.25
            tax_due *= quarter_multiplier
        
        # Get quarterly tax paid
        quarterly_paid = self._get_quarterly_tax_paid(tax_year, period)
        
        remaining_tax = max(0, tax_due - quarterly_paid)
        
        computation = {
            'regime': 'Graduated Rates',
            'tax_year': tax_year,
            'period': period,
            'gross_sales': financial_data['gross_sales'],
            'other_income': financial_data['other_income'],
            'total_income': gross_income,
            'osd_amount': osd,
            'itemized_deductions': itemized_deductions,
            'allowable_deductions': allowable_deductions,
            'net_taxable_income': net_taxable_income,
            'tax_due': tax_due,
            'quarterly_tax_paid': quarterly_paid,
            'remaining_tax_due': remaining_tax,
            'computation_details': {
                'gross_income': gross_income,
                'osd_percentage': 40,
                'osd_amount': osd,
                'itemized_deductions': itemized_deductions,
                'total_deductions': allowable_deductions,
                'taxable_income': net_taxable_income,
                'tax_brackets_applied': self._get_tax_bracket_details(net_taxable_income),
                'computed_tax': tax_due
            }
        }
        
        # Save computation to database
        self._save_tax_computation(computation)
        
        return computation
    
    def _calculate_mixed_tax(self, financial_data: Dict[str, float], 
                           tax_year: int, period: str) -> Dict[str, Any]:
        """Calculate tax using mixed regime (combination of flat and graduated)"""
        
        # Separate business income from other income
        business_income = financial_data['gross_sales']
        other_income = financial_data['other_income']
        
        # Apply 8% rate to business income
        business_taxable = max(0, business_income - self.flat_rate_settings['deduction'])
        business_tax = business_taxable * self.flat_rate_settings['rate']
        
        # Apply graduated rates to other income
        other_taxable = other_income
        other_tax = self._compute_graduated_tax(other_taxable)
        
        total_tax = business_tax + other_tax
        
        # For quarterly periods, adjust proportionally
        if period != "Annual":
            quarter_multiplier = 0.25
            total_tax *= quarter_multiplier
        
        # Get quarterly tax paid
        quarterly_paid = self._get_quarterly_tax_paid(tax_year, period)
        
        remaining_tax = max(0, total_tax - quarterly_paid)
        
        computation = {
            'regime': 'Mixed',
            'tax_year': tax_year,
            'period': period,
            'business_income': business_income,
            'other_income': other_income,
            'total_income': business_income + other_income,
            'business_taxable_income': business_taxable,
            'business_tax': business_tax,
            'other_taxable_income': other_taxable,
            'other_tax': other_tax,
            'total_tax_due': total_tax,
            'quarterly_tax_paid': quarterly_paid,
            'remaining_tax_due': remaining_tax,
            'computation_details': {
                'business_income_8_percent': {
                    'income': business_income,
                    'deduction': self.flat_rate_settings['deduction'],
                    'taxable': business_taxable,
                    'tax': business_tax
                },
                'other_income_graduated': {
                    'income': other_income,
                    'taxable': other_taxable,
                    'tax': other_tax,
                    'brackets': self._get_tax_bracket_details(other_taxable)
                },
                'total_tax': total_tax
            }
        }
        
        # Save computation to database
        self._save_tax_computation(computation)
        
        return computation
    
    def _compute_graduated_tax(self, taxable_income: float) -> float:
        """Compute tax using graduated rates"""
        
        if taxable_income <= 0:
            return 0
        
        tax = 0
        for bracket in self.graduated_rates_2026:
            if taxable_income <= bracket['min']:
                break
            
            if taxable_income > bracket['max']:
                # Income exceeds this bracket
                bracket_income = bracket['max'] - bracket['min'] + 1
                tax += bracket_income * bracket['rate']
            else:
                # Income falls within this bracket
                bracket_income = taxable_income - bracket['min'] + 1
                tax += bracket_income * bracket['rate']
                break
        
        return tax
    
    def _get_tax_bracket_details(self, taxable_income: float) -> List[Dict[str, Any]]:
        """Get details of tax brackets applied"""
        
        brackets_applied = []
        
        for bracket in self.graduated_rates_2026:
            if taxable_income <= bracket['min']:
                break
            
            if taxable_income > bracket['max']:
                bracket_income = bracket['max'] - bracket['min'] + 1
            else:
                bracket_income = taxable_income - bracket['min'] + 1
            
            bracket_tax = bracket_income * bracket['rate']
            
            brackets_applied.append({
                'range': f"₱{bracket['min']:,} - ₱{bracket['max']:,}" if bracket['max'] != float('inf') else f"₱{bracket['min']:,} and above",
                'rate': f"{bracket['rate']*100}%",
                'income_in_bracket': bracket_income,
                'tax_from_bracket': bracket_tax,
                'cumulative_tax': bracket['base_tax'] + bracket_tax
            })
        
        return brackets_applied
    
    def _get_quarterly_tax_paid(self, tax_year: int, current_period: str) -> float:
        """Get total tax paid in previous quarters"""
        
        quarters = ["Quarter 1", "Quarter 2", "Quarter 3", "Quarter 4"]
        current_index = quarters.index(current_period)
        
        if current_index == 0:  # First quarter, no previous payments
            return 0
        
        previous_quarters = quarters[:current_index]
        total_paid = 0
        
        with self.db.get_connection() as conn:
            for quarter in previous_quarters:
                cursor = conn.execute("""
                    SELECT tax_due FROM tax_computations 
                    WHERE tax_year = ? AND tax_period = ?
                """, (tax_year, quarter))
                
                result = cursor.fetchone()
                if result:
                    total_paid += result['tax_due']
        
        return total_paid
    
    def _save_tax_computation(self, computation: Dict[str, Any]):
        """Save tax computation to database"""
        
        with self.db.get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO tax_computations 
                (tax_year, tax_period, gross_sales, gross_receipts, non_operating_income,
                 total_income, cost_of_goods_sold, business_expenses, net_taxable_income,
                 tax_regime, tax_due, quarterly_tax_paid, remaining_tax_due, computation_details)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                computation['tax_year'],
                computation['period'],
                computation.get('gross_sales', 0),
                computation.get('gross_sales', 0),  # Using gross_sales as gross_receipts
                computation.get('other_income', 0),
                computation.get('total_income', 0),
                0,  # COGS not implemented yet
                computation.get('total_expenses', 0),
                computation.get('net_taxable_income', 0),
                computation['regime'],
                computation.get('tax_due', 0),
                computation.get('quarterly_tax_paid', 0),
                computation.get('remaining_tax_due', 0),
                json.dumps(computation.get('computation_details', {}))
            ))
    
    def calculate_estimated_tax(self, tax_year: int) -> float:
        """Quick estimate of annual tax due (for dashboard)"""
        
        try:
            # Get current year's financial data
            financial_data = self._get_financial_data(tax_year, "Annual")
            
            # Calculate using 8% flat rate (most common for small businesses)
            gross_income = financial_data['gross_sales'] + financial_data['other_income']
            taxable_income = max(0, gross_income - self.flat_rate_settings['deduction'])
            estimated_tax = taxable_income * self.flat_rate_settings['rate']
            
            return estimated_tax
            
        except Exception:
            # Return 0 if no data available
            return 0
    
    def get_tax_summary(self, tax_year: int) -> Dict[str, Any]:
        """Get comprehensive tax summary for the year"""
        
        summary = {
            'tax_year': tax_year,
            'quarterly_computations': [],
            'annual_projection': {},
            'recommendations': []
        }
        
        # Get quarterly computations
        quarters = ["Quarter 1", "Quarter 2", "Quarter 3", "Quarter 4"]
        
        with self.db.get_connection() as conn:
            for quarter in quarters:
                cursor = conn.execute("""
                    SELECT * FROM tax_computations 
                    WHERE tax_year = ? AND tax_period = ?
                """, (tax_year, quarter))
                
                result = cursor.fetchone()
                if result:
                    summary['quarterly_computations'].append(dict(result))
        
        # Get annual computation if available
        cursor = conn.execute("""
            SELECT * FROM tax_computations 
            WHERE tax_year = ? AND tax_period = 'Annual'
        """, (tax_year,))
        
        result = cursor.fetchone()
        if result:
            summary['annual_computation'] = dict(result)
        
        # Generate recommendations
        summary['recommendations'] = self._generate_tax_recommendations(summary)
        
        return summary
    
    def _generate_tax_recommendations(self, tax_summary: Dict[str, Any]) -> List[str]:
        """Generate tax planning recommendations"""
        
        recommendations = []
        
        # Check if quarterly payments are on track
        total_quarterly_paid = sum(
            comp.get('tax_due', 0) for comp in tax_summary['quarterly_computations']
        )
        
        if 'annual_computation' in tax_summary:
            annual_tax = tax_summary['annual_computation'].get('tax_due', 0)
            remaining_quarters = 4 - len(tax_summary['quarterly_computations'])
            
            if remaining_quarters > 0:
                suggested_quarterly_payment = (annual_tax - total_quarterly_paid) / remaining_quarters
                recommendations.append(
                    f"Consider paying ₱{suggested_quarterly_payment:,.2f} per remaining quarter "
                    f"to avoid underpayment penalties"
                )
        
        # Check expense optimization
        if tax_summary['quarterly_computations']:
            latest_computation = tax_summary['quarterly_computations'][-1]
            total_income = latest_computation.get('total_income', 0)
            total_expenses = latest_computation.get('business_expenses', 0)
            
            expense_ratio = (total_expenses / total_income * 100) if total_income > 0 else 0
            
            if expense_ratio < 20:
                recommendations.append(
                    "Your expense ratio is low. Consider documenting all legitimate business expenses "
                    "to optimize your tax position"
                )
            elif expense_ratio > 60:
                recommendations.append(
                    "Your expense ratio is high. Ensure all expenses are properly documented "
                    "and directly related to business operations"
                )
        
        # VAT considerations
        recommendations.append(
            "Monitor your VAT position. Consider registering for VAT if annual sales exceed ₱3M"
        )
        
        return recommendations
