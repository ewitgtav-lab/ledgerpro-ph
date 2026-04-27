"""
PDF Generator for BIR-style receipts and tax forms
Uses ReportLab for professional PDF generation
"""

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib.colors import black, white, HexColor
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Frame, PageTemplate
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
import os
from datetime import datetime, date
from typing import Dict, List, Any, Optional
import json

class BIRReceiptGenerator:
    """Generates BIR-compliant receipts and invoices"""
    
    def __init__(self, output_dir: str = "static/receipts"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # BIR standard colors
        self.bir_blue = HexColor('#003366')
        self.bir_red = HexColor('#CC0000')
        
        # Page setup
        self.page_size = A4
        self.margin = 0.5 * inch
        
        # Styles
        self.styles = getSampleStyleSheet()
        self._setup_styles()
    
    def _setup_styles(self):
        """Setup custom styles for BIR forms"""
        
        # Header style
        self.styles.add(ParagraphStyle(
            name='BIRHeader',
            parent=self.styles['Heading1'],
            fontSize=14,
            spaceAfter=6,
            alignment=TA_CENTER,
            textColor=self.bir_blue
        ))
        
        # Subheader style
        self.styles.add(ParagraphStyle(
            name='BIRSubheader',
            parent=self.styles['Heading2'],
            fontSize=10,
            spaceAfter=3,
            alignment=TA_CENTER,
            textColor=black
        ))
        
        # Normal text
        self.styles.add(ParagraphStyle(
            name='BIRNormal',
            parent=self.styles['Normal'],
            fontSize=9,
            spaceAfter=2,
            alignment=TA_LEFT
        ))
        
        # Small text
        self.styles.add(ParagraphStyle(
            name='BIRSmall',
            parent=self.styles['Normal'],
            fontSize=8,
            spaceAfter=1,
            alignment=TA_LEFT
        ))
        
        # Bold text
        self.styles.add(ParagraphStyle(
            name='BIRBold',
            parent=self.styles['Normal'],
            fontSize=9,
            spaceAfter=2,
            alignment=TA_LEFT,
            fontName='Helvetica-Bold'
        ))
    
    def generate_sales_invoice(self, receipt_data: Dict[str, Any]) -> str:
        """Generate BIR Sales Invoice"""
        
        filename = f"SI_{receipt_data['serial_number'].replace('-', '_')}.pdf"
        filepath = os.path.join(self.output_dir, filename)
        
        # Create PDF document
        doc = SimpleDocTemplate(filepath, pagesize=self.page_size, 
                              leftMargin=self.margin, rightMargin=self.margin,
                              topMargin=self.margin, bottomMargin=self.margin)
        
        # Build content
        story = []
        
        # Header section
        story.extend(self._build_invoice_header(receipt_data, "SALES INVOICE"))
        
        # Customer information
        story.extend(self._build_customer_info(receipt_data))
        
        # Items table
        story.extend(self._build_items_table(receipt_data['items']))
        
        # Summary section
        story.extend(self._build_invoice_summary(receipt_data))
        
        # Footer section
        story.extend(self._build_invoice_footer(receipt_data))
        
        # Build PDF
        doc.build(story)
        
        return filepath
    
    def generate_service_invoice(self, receipt_data: Dict[str, Any]) -> str:
        """Generate BIR Service Invoice"""
        
        filename = f"SERV_{receipt_data['serial_number'].replace('-', '_')}.pdf"
        filepath = os.path.join(self.output_dir, filename)
        
        doc = SimpleDocTemplate(filepath, pagesize=self.page_size,
                              leftMargin=self.margin, rightMargin=self.margin,
                              topMargin=self.margin, bottomMargin=self.margin)
        
        story = []
        
        # Header section
        story.extend(self._build_invoice_header(receipt_data, "SERVICE INVOICE"))
        
        # Customer information
        story.extend(self._build_customer_info(receipt_data))
        
        # Service details
        story.extend(self._build_service_details(receipt_data))
        
        # Summary section
        story.extend(self._build_invoice_summary(receipt_data))
        
        # Footer section
        story.extend(self._build_invoice_footer(receipt_data))
        
        doc.build(story)
        
        return filepath
    
    def generate_official_receipt(self, receipt_data: Dict[str, Any]) -> str:
        """Generate BIR Official Receipt"""
        
        filename = f"OR_{receipt_data['serial_number'].replace('-', '_')}.pdf"
        filepath = os.path.join(self.output_dir, filename)
        
        doc = SimpleDocTemplate(filepath, pagesize=self.page_size,
                              leftMargin=self.margin, rightMargin=self.margin,
                              topMargin=self.margin, bottomMargin=self.margin)
        
        story = []
        
        # Header section
        story.extend(self._build_invoice_header(receipt_data, "OFFICIAL RECEIPT"))
        
        # Payment information
        story.extend(self._build_payment_info(receipt_data))
        
        # Amount details
        story.extend(self._build_amount_details(receipt_data))
        
        # Footer section
        story.extend(self._build_invoice_footer(receipt_data))
        
        doc.build(story)
        
        return filepath
    
    def _build_invoice_header(self, receipt_data: Dict[str, Any], document_type: str) -> List:
        """Build invoice header section"""
        
        elements = []
        
        # Business name and TIN
        business_info = [
            [Paragraph("BIR ACCREDITATION NO. 0000000000000", self.styles['BIRSmall'])],
            [Paragraph("PANG-KAPE ENTERPRISES", self.styles['BIRHeader'])],
            [Paragraph("TIN: 000-000-000-000", self.styles['BIRSubheader'])],
            [Paragraph("123 Business Street, Makati City, Philippines", self.styles['BIRNormal'])],
            [Paragraph("Tel: (02) 1234-5678 | Email: info@pangkape.com", self.styles['BIRSmall'])],
        ]
        
        business_table = Table(business_info, colWidths=[7*inch])
        business_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        
        elements.append(business_table)
        elements.append(Spacer(1, 0.1*inch))
        
        # Document type and serial number
        header_data = [
            [Paragraph(document_type, self.styles['BIRHeader'])],
            [Paragraph(f"SERIAL NO.: {receipt_data['serial_number']}", self.styles['BIRBold'])],
        ]
        
        header_table = Table(header_data, colWidths=[7*inch])
        header_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LINEBELOW', (0, 0), (-1, 0), 2, self.bir_blue),
        ]))
        
        elements.append(header_table)
        elements.append(Spacer(1, 0.1*inch))
        
        # Date and customer info header
        date_info = [
            [Paragraph("DATE:", self.styles['BIRBold']), 
             Paragraph(receipt_data['transaction_date'], self.styles['BIRNormal'])],
            [Paragraph("CUSTOMER:", self.styles['BIRBold']), 
             Paragraph(receipt_data['customer_name'], self.styles['BIRNormal'])],
        ]
        
        date_table = Table(date_info, colWidths=[1.5*inch, 5.5*inch])
        date_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ]))
        
        elements.append(date_table)
        elements.append(Spacer(1, 0.1*inch))
        
        return elements
    
    def _build_customer_info(self, receipt_data: Dict[str, Any]) -> List:
        """Build customer information section"""
        
        elements = []
        
        customer_data = [
            ["Customer Name:", receipt_data.get('customer_name', ''), "TIN:", receipt_data.get('customer_tin', '')],
            ["Business Style:", receipt_data.get('business_style', ''), "Address:", receipt_data.get('customer_address', '')],
        ]
        
        customer_table = Table(customer_data, colWidths=[1.5*inch, 2.5*inch, 0.8*inch, 2.2*inch])
        customer_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, 1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, 1), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        
        elements.append(customer_table)
        elements.append(Spacer(1, 0.1*inch))
        
        return elements
    
    def _build_items_table(self, items: List[Dict[str, Any]]) -> List:
        """Build items table for sales invoice"""
        
        elements = []
        
        # Table headers
        headers = ["Quantity", "Unit", "Description", "Unit Price", "Amount"]
        
        # Build table data
        table_data = [headers]
        
        for item in items:
            row = [
                str(item.get('quantity', 1)),
                item.get('unit', 'pcs'),
                item.get('description', ''),
                f"₱{item.get('unit_price', 0):,.2f}",
                f"₱{item.get('total', 0):,.2f}"
            ]
            table_data.append(row)
        
        # Create table
        items_table = Table(table_data, colWidths=[0.8*inch, 0.8*inch, 3*inch, 1.2*inch, 1.2*inch])
        items_table.setStyle(TableStyle([
            # Header styling
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#E6E6E6')),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            
            # Data styling
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # Quantity
            ('ALIGN', (1, 1), (1, -1), 'CENTER'),  # Unit
            ('ALIGN', (2, 1), (2, -1), 'LEFT'),    # Description
            ('ALIGN', (3, 1), (-1, -1), 'RIGHT'),  # Prices
            ('TOPPADDING', (0, 1), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            
            # Grid lines
            ('GRID', (0, 0), (-1, -1), 1, black),
        ]))
        
        elements.append(items_table)
        elements.append(Spacer(1, 0.1*inch))
        
        return elements
    
    def _build_service_details(self, receipt_data: Dict[str, Any]) -> List:
        """Build service details for service invoice"""
        
        elements = []
        
        # Service description
        service_data = [
            ["Service Description:", receipt_data.get('description', 'Professional Services')],
            ["Period Covered:", receipt_data.get('period', f"{receipt_data.get('transaction_date', date.today())}")],
            ["Terms:", receipt_data.get('terms', 'Due upon receipt')],
        ]
        
        service_table = Table(service_data, colWidths=[1.5*inch, 5.5*inch])
        service_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, 2), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        
        elements.append(service_table)
        elements.append(Spacer(1, 0.2*inch))
        
        return elements
    
    def _build_payment_info(self, receipt_data: Dict[str, Any]) -> List:
        """Build payment information for official receipt"""
        
        elements = []
        
        payment_data = [
            ["Received from:", receipt_data.get('customer_name', '')],
            ["Payment for:", receipt_data.get('description', 'Goods/Services')],
            ["Payment method:", receipt_data.get('payment_method', 'Cash')],
        ]
        
        payment_table = Table(payment_data, colWidths=[1.5*inch, 5.5*inch])
        payment_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, 2), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        
        elements.append(payment_table)
        elements.append(Spacer(1, 0.2*inch))
        
        return elements
    
    def _build_amount_details(self, receipt_data: Dict[str, Any]) -> List:
        """Build amount details section"""
        
        elements = []
        
        # Amount in words
        amount = receipt_data.get('total_amount', 0)
        amount_words = self._number_to_words(amount)
        
        amount_data = [
            ["Amount in Words:", amount_words],
            ["Amount in Figures:", f"₱{amount:,.2f}"],
        ]
        
        amount_table = Table(amount_data, colWidths=[1.5*inch, 5.5*inch])
        amount_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, 1), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        
        elements.append(amount_table)
        elements.append(Spacer(1, 0.2*inch))
        
        return elements
    
    def _build_invoice_summary(self, receipt_data: Dict[str, Any]) -> List:
        """Build invoice summary section"""
        
        elements = []
        
        # Calculate totals
        subtotal = sum(item.get('total', 0) for item in receipt_data.get('items', []))
        vat_amount = receipt_data.get('vat_amount', 0)
        total_amount = receipt_data.get('total_amount', subtotal + vat_amount)
        
        summary_data = [
            ["Subtotal:", f"₱{subtotal:,.2f}"],
            ["VAT (12%):", f"₱{vat_amount:,.2f}"],
            ["TOTAL:", f"₱{total_amount:,.2f}"],
        ]
        
        summary_table = Table(summary_data, colWidths=[5.5*inch, 1.5*inch])
        summary_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, 1), 'RIGHT'),
            ('ALIGN', (0, 2), (0, 2), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 2), (1, 2), 'Helvetica-Bold'),
            ('FONTNAME', (0, 0), (1, 1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('LINEABOVE', (0, 2), (-1, 2), 2, self.bir_blue),
        ]))
        
        elements.append(summary_table)
        elements.append(Spacer(1, 0.2*inch))
        
        return elements
    
    def _build_invoice_footer(self, receipt_data: Dict[str, Any]) -> List:
        """Build invoice footer section"""
        
        elements = []
        
        # Signature lines
        signature_data = [
            ["", "", ""],
            ["_________________________", "_________________________", "_________________________"],
            ["Signature over Printed Name", "Signature over Printed Name", "Signature over Printed Name"],
            ["Authorized Signatory", "Authorized Signatory", "Customer"],
        ]
        
        signature_table = Table(signature_data, colWidths=[2.3*inch, 2.3*inch, 2.3*inch])
        signature_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 20),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        
        elements.append(signature_table)
        elements.append(Spacer(1, 0.2*inch))
        
        # BIR disclaimer
        disclaimer_text = (
            "This receipt/invoice shall be valid for five (5) years from the date of issue. "
            "Please present this receipt for any warranty claims. "
            "Thank you for your business!"
        )
        
        disclaimer = Paragraph(disclaimer_text, self.styles['BIRSmall'])
        elements.append(disclaimer)
        
        return elements
    
    def _number_to_words(self, amount: float) -> str:
        """Convert number to words (Philippine Peso format)"""
        
        # Simple implementation - can be enhanced
        if amount == 0:
            return "Zero Pesos"
        
        pesos = int(amount)
        centavos = int(round((amount - pesos) * 100))
        
        # Convert pesos to words (simplified)
        if pesos == 1:
            pesos_words = "One Peso"
        else:
            pesos_words = f"{self._convert_number_to_words(pesos)} Pesos"
        
        # Add centavos if any
        if centavos > 0:
            if centavos == 1:
                centavos_words = "and One Centavo"
            else:
                centavos_words = f"and {self._convert_number_to_words(centavos)} Centavos"
        else:
            centavos_words = ""
        
        return f"{pesos_words} {centavos_words}".strip()
    
    def _convert_number_to_words(self, num: int) -> str:
        """Convert number to words (basic implementation)"""
        
        if num == 0:
            return "Zero"
        
        ones = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine"]
        teens = ["Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", 
                "Sixteen", "Seventeen", "Eighteen", "Nineteen"]
        tens = ["", "Ten", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]
        
        if num < 10:
            return ones[num]
        elif num < 20:
            return teens[num - 10]
        elif num < 100:
            return tens[num // 10] + (" " + ones[num % 10] if num % 10 else "")
        elif num < 1000:
            return ones[num // 100] + " Hundred" + (" " + self._convert_number_to_words(num % 100) if num % 100 else "")
        elif num < 1000000:
            return self._convert_number_to_words(num // 1000) + " Thousand" + (" " + self._convert_number_to_words(num % 1000) if num % 1000 else "")
        else:
            return self._convert_number_to_words(num // 1000000) + " Million" + (" " + self._convert_number_to_words(num % 1000000) if num % 1000000 else "")

class BIRFormGenerator:
    """Generates BIR tax forms (Annex A, D, etc.)"""
    
    def __init__(self, output_dir: str = "static/tax_forms"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def generate_annex_a(self, tax_data: Dict[str, Any]) -> str:
        """Generate BIR Annex A - Sworn Declaration of No Inventory"""
        
        filename = f"Annex_A_{tax_data.get('tax_year', 2026)}_{datetime.now().strftime('%Y%m%d')}.pdf"
        filepath = os.path.join(self.output_dir, filename)
        
        # Implementation for Annex A generation
        # This would create the specific BIR form format
        
        return filepath
    
    def generate_annex_d(self, inventory_data: List[Dict[str, Any]]) -> str:
        """Generate BIR Annex D - Inventory List"""
        
        filename = f"Annex_D_{datetime.now().strftime('%Y%m%d')}.pdf"
        filepath = os.path.join(self.output_dir, filename)
        
        # Implementation for Annex D generation
        # This would create the inventory list format
        
        return filepath
