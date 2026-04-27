"""
BIR Forms Generator for Philippine Tax Compliance
Generates ready-to-print PDFs for Annex A, D, and other BIR forms
"""

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib.colors import black, white, HexColor
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
import os
from datetime import datetime, date
from typing import Dict, List, Any, Optional
import json

class BIRFormsGenerator:
    """Generates BIR-compliant tax forms"""
    
    def __init__(self, output_dir: str = "static/bir_forms"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # BIR standard colors
        self.bir_blue = HexColor('#003366')
        self.bir_red = HexColor('#CC0000')
        
        # Page setup
        self.page_size = A4
        self.margin = 0.75 * inch
        
        # Styles
        self.styles = getSampleStyleSheet()
        self._setup_styles()
    
    def _setup_styles(self):
        """Setup custom styles for BIR forms"""
        
        # Form title
        self.styles.add(ParagraphStyle(
            name='BIRFormTitle',
            parent=self.styles['Heading1'],
            fontSize=16,
            spaceAfter=12,
            alignment=TA_CENTER,
            textColor=self.bir_blue,
            fontName='Helvetica-Bold'
        ))
        
        # Form subtitle
        self.styles.add(ParagraphStyle(
            name='BIRFormSubtitle',
            parent=self.styles['Heading2'],
            fontSize=12,
            spaceAfter=8,
            alignment=TA_CENTER,
            textColor=black,
            fontName='Helvetica-Bold'
        ))
        
        # Normal text
        self.styles.add(ParagraphStyle(
            name='BIRFormNormal',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=6,
            alignment=TA_JUSTIFY,
            leading=14
        ))
        
        # Small text
        self.styles.add(ParagraphStyle(
            name='BIRFormSmall',
            parent=self.styles['Normal'],
            fontSize=9,
            spaceAfter=3,
            alignment=TA_LEFT,
            leading=12
        ))
        
        # Bold text
        self.styles.add(ParagraphStyle(
            name='BIRFormBold',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=6,
            alignment=TA_LEFT,
            fontName='Helvetica-Bold',
            leading=14
        ))
    
    def generate_annex_a(self, taxpayer_info: Dict[str, Any], tax_year: int) -> str:
        """Generate BIR Annex A - Sworn Declaration of No Inventory"""
        
        filename = f"BIR_Annex_A_{taxpayer_info.get('tin', 'NO_TIN')}_{tax_year}.pdf"
        filepath = os.path.join(self.output_dir, filename)
        
        # Create PDF document
        doc = SimpleDocTemplate(filepath, pagesize=self.page_size,
                              leftMargin=self.margin, rightMargin=self.margin,
                              topMargin=self.margin, bottomMargin=self.margin)
        
        # Build content
        story = []
        
        # BIR Header
        story.extend(self._build_bir_header())
        
        # Form title and number
        story.extend(self._build_annex_a_header(tax_year))
        
        # Taxpayer information
        story.extend(self._build_taxpayer_info(taxpayer_info))
        
        # Declaration content
        story.extend(self._build_annex_a_declaration())
        
        # Signature section
        story.extend(self._build_signature_section("Sworn Declaration"))
        
        # Footer
        story.extend(self._build_form_footer())
        
        # Build PDF
        doc.build(story)
        
        return filepath
    
    def generate_annex_d(self, inventory_data: List[Dict[str, Any]], 
                        taxpayer_info: Dict[str, Any], tax_year: int) -> str:
        """Generate BIR Annex D - Detailed Inventory List"""
        
        filename = f"BIR_Annex_D_{taxpayer_info.get('tin', 'NO_TIN')}_{tax_year}.pdf"
        filepath = os.path.join(self.output_dir, filename)
        
        # Create PDF document
        doc = SimpleDocTemplate(filepath, pagesize=self.page_size,
                              leftMargin=self.margin, rightMargin=self.margin,
                              topMargin=self.margin, bottomMargin=self.margin)
        
        # Build content
        story = []
        
        # BIR Header
        story.extend(self._build_bir_header())
        
        # Form title
        story.extend(self._build_annex_d_header(tax_year))
        
        # Taxpayer information
        story.extend(self._build_taxpayer_info(taxpayer_info))
        
        # Inventory table
        story.extend(self._build_inventory_table(inventory_data))
        
        # Summary section
        story.extend(self._build_inventory_summary(inventory_data))
        
        # Signature section
        story.extend(self._build_signature_section("Inventory Certification"))
        
        # Footer
        story.extend(self._build_form_footer())
        
        # Build PDF
        doc.build(story)
        
        return filepath
    
    def generate_form_2307(self, withholding_data: Dict[str, Any]) -> str:
        """Generate BIR Form 2307 - Certificate of Creditable Tax Withheld at Source"""
        
        filename = f"BIR_2307_{withholding_data.get('period', 'Q1')}_{withholding_data.get('year', 2026)}.pdf"
        filepath = os.path.join(self.output_dir, filename)
        
        doc = SimpleDocTemplate(filepath, pagesize=self.page_size,
                              leftMargin=self.margin, rightMargin=self.margin,
                              topMargin=self.margin, bottomMargin=self.margin)
        
        story = []
        
        # BIR Header
        story.extend(self._build_bir_header())
        
        # Form 2307 specific header
        story.extend(self._build_form_2307_header(withholding_data))
        
        # Payor and Payee information
        story.extend(self._build_2307_parties_info(withholding_data))
        
        # Tax details table
        story.extend(self._build_2307_tax_details(withholding_data))
        
        # Signature section
        story.extend(self._build_signature_section("Certificate"))
        
        # Footer
        story.extend(self._build_form_footer())
        
        doc.build(story)
        
        return filepath
    
    def _build_bir_header(self) -> List:
        """Build BIR standard header"""
        
        elements = []
        
        # BIR Logo placeholder and title
        header_data = [
            [Paragraph("REPUBLIC OF THE PHILIPPINES", self.styles['BIRFormTitle'])],
            [Paragraph("BUREAU OF INTERNAL REVENUE", self.styles['BIRFormSubtitle'])],
            [Paragraph("_______", self.styles['BIRFormNormal'])],  # Line for District/Regional Office
        ]
        
        header_table = Table(header_data, colWidths=[7*inch])
        header_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        
        elements.append(header_table)
        elements.append(Spacer(1, 0.2*inch))
        
        return elements
    
    def _build_annex_a_header(self, tax_year: int) -> List:
        """Build Annex A specific header"""
        
        elements = []
        
        header_data = [
            [Paragraph("ANNEX A", self.styles['BIRFormTitle'])],
            [Paragraph(f"SWORN DECLARATION OF NO INVENTORY", self.styles['BIRFormSubtitle'])],
            [Paragraph(f"For the Year {tax_year}", self.styles['BIRFormNormal'])],
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
        elements.append(Spacer(1, 0.2*inch))
        
        return elements
    
    def _build_annex_d_header(self, tax_year: int) -> List:
        """Build Annex D specific header"""
        
        elements = []
        
        header_data = [
            [Paragraph("ANNEX D", self.styles['BIRFormTitle'])],
            [Paragraph("DETAILED INVENTORY LIST", self.styles['BIRFormSubtitle'])],
            [Paragraph(f"As of December 31, {tax_year}", self.styles['BIRFormNormal'])],
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
        elements.append(Spacer(1, 0.2*inch))
        
        return elements
    
    def _build_form_2307_header(self, withholding_data: Dict[str, Any]) -> List:
        """Build Form 2307 specific header"""
        
        elements = []
        
        header_data = [
            [Paragraph("CERTIFICATE OF CREDITABLE TAX WITHHELD AT SOURCE", self.styles['BIRFormTitle'])],
            [Paragraph("BIR Form No. 2307", self.styles['BIRFormSubtitle'])],
            [Paragraph(f"{withholding_data.get('period', 'Q1')} {withholding_data.get('year', 2026)}", self.styles['BIRFormNormal'])],
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
        elements.append(Spacer(1, 0.2*inch))
        
        return elements
    
    def _build_taxpayer_info(self, taxpayer_info: Dict[str, Any]) -> List:
        """Build taxpayer information section"""
        
        elements = []
        
        info_data = [
            ["Taxpayer's Name:", taxpayer_info.get('business_name', ''), "TIN:", taxpayer_info.get('tin', '')],
            ["Trade Name:", taxpayer_info.get('trade_name', ''), "RDO Code:", taxpayer_info.get('rdo_code', '')],
            ["Address:", taxpayer_info.get('address', ''), "Telephone:", taxpayer_info.get('telephone', '')],
            ["", "", "Email:", taxpayer_info.get('email', '')],
        ]
        
        info_table = Table(info_data, colWidths=[2*inch, 3*inch, 1.5*inch, 0.5*inch])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, 3), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, 3), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        
        elements.append(info_table)
        elements.append(Spacer(1, 0.2*inch))
        
        return elements
    
    def _build_annex_a_declaration(self) -> List:
        """Build Annex A declaration content"""
        
        elements = []
        
        declaration_text = """
        I, ______________________________________, declare under penalty of perjury under the laws of the Republic of the Philippines that:
        
        1. I am engaged in the business of ________________________________________________;
        2. I am not required to maintain inventory under existing revenue regulations;
        3. I do not have any inventory of goods, merchandise, or articles subject to tax as of December 31, 2026;
        4. All my sales are for services only or for goods that are not required to be inventoried;
        5. I understand that any false statement in this declaration may subject me to criminal prosecution under the Tax Code.
        
        This declaration is being executed to support my income tax return for the year 2026.
        """
        
        declaration = Paragraph(declaration_text, self.styles['BIRFormNormal'])
        elements.append(declaration)
        elements.append(Spacer(1, 0.3*inch))
        
        return elements
    
    def _build_inventory_table(self, inventory_data: List[Dict[str, Any]]) -> List:
        """Build inventory table for Annex D"""
        
        elements = []
        
        # Table headers
        headers = ["Item No.", "Description", "Quantity", "Unit Cost", "Total Cost"]
        
        # Build table data
        table_data = [headers]
        
        for idx, item in enumerate(inventory_data, 1):
            row = [
                str(idx),
                item.get('description', ''),
                str(item.get('quantity', 0)),
                f"₱{item.get('unit_cost', 0):,.2f}",
                f"₱{item.get('total_cost', 0):,.2f}"
            ]
            table_data.append(row)
        
        # Create table
        inventory_table = Table(table_data, colWidths=[0.8*inch, 3*inch, 1*inch, 1.1*inch, 1.1*inch])
        inventory_table.setStyle(TableStyle([
            # Header styling
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#E6E6E6')),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            
            # Data styling
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # Item No.
            ('ALIGN', (1, 1), (1, -1), 'LEFT'),    # Description
            ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),  # Numbers
            ('TOPPADDING', (0, 1), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            
            # Grid lines
            ('GRID', (0, 0), (-1, -1), 1, black),
        ]))
        
        elements.append(inventory_table)
        elements.append(Spacer(1, 0.2*inch))
        
        return elements
    
    def _build_inventory_summary(self, inventory_data: List[Dict[str, Any]]) -> List:
        """Build inventory summary section"""
        
        elements = []
        
        # Calculate totals
        total_items = len(inventory_data)
        total_quantity = sum(item.get('quantity', 0) for item in inventory_data)
        total_cost = sum(item.get('total_cost', 0) for item in inventory_data)
        
        summary_data = [
            ["Total Number of Items:", str(total_items)],
            ["Total Quantity:", str(total_quantity)],
            ["Total Inventory Cost:", f"₱{total_cost:,.2f}"],
        ]
        
        summary_table = Table(summary_data, colWidths=[3*inch, 4*inch])
        summary_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LINEABOVE', (0, 0), (-1, 0), 2, self.bir_blue),
        ]))
        
        elements.append(summary_table)
        elements.append(Spacer(1, 0.2*inch))
        
        return elements
    
    def _build_2307_parties_info(self, withholding_data: Dict[str, Any]) -> List:
        """Build payor and payee information for Form 2307"""
        
        elements = []
        
        parties_data = [
            ["PAYOR", "PAYEE"],
            ["Name:", withholding_data.get('payor_name', ''), "Name:", withholding_data.get('payee_name', '')],
            ["Address:", withholding_data.get('payor_address', ''), "Address:", withholding_data.get('payee_address', '')],
            ["TIN:", withholding_data.get('payor_tin', ''), "TIN:", withholding_data.get('payee_tin', '')],
        ]
        
        parties_table = Table(parties_data, colWidths=[3.5*inch, 3.5*inch])
        parties_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 1), (0, 3), 'Helvetica-Bold'),
            ('FONTNAME', (2, 1), (2, 3), 'Helvetica-Bold'),
            ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('GRID', (0, 0), (-1, -1), 1, black),
        ]))
        
        elements.append(parties_table)
        elements.append(Spacer(1, 0.2*inch))
        
        return elements
    
    def _build_2307_tax_details(self, withholding_data: Dict[str, Any]) -> List:
        """Build tax details section for Form 2307"""
        
        elements = []
        
        tax_data = [
            ["Tax Type", "Base Amount", "Tax Rate", "Tax Withheld"],
            ["Expanded Withholding Tax", 
             f"₱{withholding_data.get('base_amount', 0):,.2f}", 
             f"{withholding_data.get('tax_rate', 0)}%", 
             f"₱{withholding_data.get('tax_withheld', 0):,.2f}"],
        ]
        
        tax_table = Table(tax_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
        tax_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#E6E6E6')),
            ('ALIGN', (0, 1), (0, 1), 'LEFT'),
            ('ALIGN', (1, 1), (-1, 1), 'RIGHT'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, black),
        ]))
        
        elements.append(tax_table)
        elements.append(Spacer(1, 0.2*inch))
        
        return elements
    
    def _build_signature_section(self, section_type: str) -> List:
        """Build signature section"""
        
        elements = []
        
        if section_type == "Sworn Declaration":
            signature_text = """
            SUBSCRIBED AND SWORN to before me this _____ day of ________________, 2026, 
            at _______________________, Philippines, affiant exhibiting his/her competent ID.
            """
        elif section_type == "Inventory Certification":
            signature_text = """
            CERTIFIED UNDER PENALTY OF PERJURY that the foregoing is a true and correct 
            inventory list as of December 31, 2026.
            """
        else:  # Certificate
            signature_text = """
            CERTIFIED UNDER PENALTY OF PERJURY that the foregoing information is true and correct.
            """
        
        certification = Paragraph(signature_text, self.styles['BIRFormNormal'])
        elements.append(certification)
        elements.append(Spacer(1, 0.3*inch))
        
        # Signature lines
        signature_data = [
            ["_________________________", "_________________________"],
            ["Taxpayer/Authorized Representative", "Notary Public"],
            ["", ""],
            ["_________________________", ""],
            ["Signature over Printed Name", ""],
        ]
        
        signature_table = Table(signature_data, colWidths=[3.5*inch, 3.5*inch])
        signature_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 20),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        
        elements.append(signature_table)
        elements.append(Spacer(1, 0.2*inch))
        
        return elements
    
    def _build_form_footer(self) -> List:
        """Build form footer with BIR information"""
        
        elements = []
        
        footer_text = """
        BIR Form No. ___________ 
        Series: ___________
        Page ___ of ___
        
        This form is prescribed by the Bureau of Internal Revenue under 
        Revenue Regulations No. __________ and shall be filed in accordance 
        with the provisions of the National Internal Revenue Code of 1997, 
        as amended, and applicable revenue issuances.
        """
        
        footer = Paragraph(footer_text, self.styles['BIRFormSmall'])
        elements.append(footer)
        
        return elements
