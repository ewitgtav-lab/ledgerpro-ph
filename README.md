# LedgerPro - Shop Receipt & Financial Management System

A production-ready Flask application for managing shop receipts and financial journals with a Freemium usage model, designed for deployment on Render + Supabase.

## Features

### Core Features
- **User System**: Registration and login with shop name field
- **Receipt Management**: Create, view, and delete professional receipts
- **PDF Generation**: Generate professional PDF receipts using ReportLab
- **Usage Limits**: Free users limited to 15 receipts, Pro users have unlimited receipts
- **Financial Ledger**: Separate sales and expense journals
- **Analytics**: Dashboard with total sales, expenses, and net profit
- **Data Import/Export**: Bulk import from CSV/Excel, export to Excel

### Freemium Model
- **Free Plan**: 15 receipts per month, basic features
- **Pro Plan**: Unlimited receipts, advanced features ($19/month)

## Tech Stack

- **Backend**: Flask with Application Factory pattern
- **Database**: PostgreSQL (via Supabase) with SQLAlchemy
- **Authentication**: Flask-Login
- **Frontend**: Tailwind CSS for responsive design
- **PDF Generation**: ReportLab
- **Data Processing**: Pandas with OpenPyXL
- **Deployment**: Gunicorn on Render

## Project Structure

```
SaaS-Killer/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── Procfile              # Render deployment configuration
├── .env.example          # Environment variables template
├── templates/
│   ├── base.html         # Base template with navigation
│   ├── auth/             # Authentication templates
│   ├── receipts/         # Receipt management templates
│   ├── ledger/           # Financial ledger templates
│   └── transactions/     # Transaction templates
├── static/               # Static assets (CSS, JS)
└── uploads/              # File upload directory
```

## Setup Instructions

### Local Development

1. **Clone and install dependencies**:
```bash
git clone <repository-url>
cd SaaS-Killer
pip install -r requirements.txt
```

2. **Set up environment variables**:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. **Run the application**:
```bash
python app.py
```

### Production Deployment (Render + Supabase)

1. **Set up Supabase**:
   - Create a new Supabase project
   - Get your database connection string
   - Set up the database (tables will be created automatically)

2. **Deploy to Render**:
   - Connect your GitHub repository to Render
   - Set environment variables:
     - `DATABASE_URL`: Your Supabase connection string
     - `SECRET_KEY`: Generate a secure secret key
   - Render will automatically detect the Procfile and deploy

3. **Environment Variables Required**:
   - `DATABASE_URL`: PostgreSQL connection string
   - `SECRET_KEY`: Flask secret key

## Database Models

### User
- Email (unique)
- Password hash
- Shop name
- Pro status (boolean)
- Created timestamp

### Receipt
- User relationship
- Customer name
- Items (JSON)
- Total amount
- Receipt number (auto-generated)
- Created timestamp

### Transaction
- User relationship
- Receipt relationship (optional)
- Description
- Amount
- Type (sale/expense)
- Category
- Date
- Created timestamp

## API Endpoints

### Authentication
- `GET/POST /login` - User login
- `GET/POST /register` - User registration
- `GET /logout` - User logout

### Dashboard
- `GET /` - Redirect to dashboard
- `GET /dashboard` - Main dashboard with analytics

### Receipts
- `GET /receipts` - List all receipts
- `GET/POST /receipts/new` - Create new receipt
- `GET /receipts/<id>` - View receipt details
- `GET /receipts/<id>/pdf` - Download PDF receipt
- `POST /receipts/<id>/delete` - Delete receipt

### Financial Ledger
- `GET /ledger` - Redirect to sales journal
- `GET /ledger/sales` - Sales journal
- `GET /ledger/expenses` - Expense journal
- `GET/POST /transactions/new` - Add transaction
- `POST /transactions/<id>/delete` - Delete transaction

### Data Management
- `GET/POST /import` - Import transactions from CSV/Excel
- `GET /export` - Export all transactions to Excel

### Subscription
- `GET /subscribe` - Upgrade to Pro plan

## Usage Limit Implementation

Free users are limited to 15 receipts total. The system:
- Tracks receipt count per user
- Shows usage progress bar on dashboard
- Prevents new receipt creation when limit is reached
- Redirects to subscription page when limit is hit

## PDF Generation

Receipts are generated as professional PDFs using ReportLab with:
- Shop name and receipt number
- Customer information
- Itemized list with quantities and prices
- Total amount
- Clean, minimalist design

## Data Import/Export

### Import Format
Required columns:
- `description`: Transaction description
- `amount`: Numeric amount
- `type`: "sale" or "expense"

Optional columns:
- `category`: Transaction category
- `date`: Date in YYYY-MM-DD format

### Export Format
Exports to Excel with all transaction data including:
- Date, description, amount, type, category
- Receipt numbers (if applicable)

## Security Features

- Password hashing with Werkzeug
- User authentication with Flask-Login
- CSRF protection on forms
- Input validation and sanitization
- User data isolation (each user only sees their own data)

## Responsive Design

- Mobile-first approach with Tailwind CSS
- Responsive navigation with mobile menu
- Touch-friendly interface
- Progressive enhancement

## Performance Considerations

- Database indexing on frequently queried fields
- Efficient pagination for large datasets
- Optimized PDF generation
- Minimal external dependencies

## License

This project is licensed under the MIT License.

## Support

For support or questions, please open an issue in the repository or contact the development team.
