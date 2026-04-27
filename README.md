# Pang-Kape: Budget-friendly Bookkeeping and Tax Automation Suite

A desktop-optimized web application for Filipino e-commerce sellers and freelancers to automate their BIR-required books and tax filings.

## Features
- Smart Journal (CRJ/CDJ) with CSV import for Shopee/Lazada/TikTok
- General Ledger & Trial Balance with real-time sync
- Auto-Receipt Generator with BIR-style PDFs
- 2026 Tax Engine (8% Flat Rate & Graduated Rates)
- BIR Annex A & D Auto-Fill
- Dashboard with Visual Analytics

## Tech Stack
- **Framework**: Streamlit (Modern, dark-themed UI)
- **Data Processing**: Pandas
- **Database**: SQLite (local persistence)
- **PDF Engine**: ReportLab/FPDF2

## Installation
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Project Structure
```
├── app.py                 # Main Streamlit application
├── models.py              # SQLite database schema
├── tax_engine.py          # Tax calculation logic
├── pages/                 # Streamlit multi-page components
├── utils/                 # Utility functions
├── static/                # Static assets (CSS, images)
├── templates/             # PDF templates
└── data/                  # Database files
```
