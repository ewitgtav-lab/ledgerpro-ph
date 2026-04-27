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

### Local Development
```bash
pip install -r requirements.txt
streamlit run app.py
```

### Render Deployment
1. Push to GitHub repository
2. Connect to Render.com
3. Use the following configuration:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `streamlit run app.py --server.port=$PORT --server.address=0.0.0.0`
   - **Health Check**: `/healthcheck` or Streamlit's built-in health endpoint
   - **Python Version**: 3.11.0 (recommended for pandas compatibility)

### Database
- Uses SQLite with relative path `bir_database.db`
- Automatically creates database on first run
- No persistent disk required for Render Free Tier
- Handles database errors gracefully

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
