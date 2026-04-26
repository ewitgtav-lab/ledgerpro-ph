# Deployment Guide - LedgerPro

## Quick Start for Production

### 1. Set up Supabase Database
1. Create a new Supabase project at https://supabase.com
2. Go to Settings > Database > Connection string
3. Copy the connection string (it will look like `postgresql://[user]:[password]@[host]:[port]/[database]`)

### 2. Deploy to Render
1. Push your code to GitHub
2. Go to https://render.com and create a new Web Service
3. Connect your GitHub repository
4. Configure the service:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT`
   - **Runtime**: Python 3

### 3. Environment Variables
Set these in your Render service environment:
```
DATABASE_URL=your_supabase_connection_string
SECRET_KEY=generate_a_secure_random_string
```

### 4. Automatic Table Creation
The Flask app will automatically create all database tables on first run using:
```python
with app.app_context():
    db.create_all()
```

## Local Development Setup

### Prerequisites
- Python 3.11 or 3.12 (recommended)
- Git

### Installation
```bash
# Clone the repository
git clone <your-repo-url>
cd SaaS-Killer

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your settings

# Run the application
python app.py
```

### Environment Variables for Local Development
Create a `.env` file:
```
DATABASE_URL=sqlite:///app.db
SECRET_KEY=your-secret-key-here
```

## Application Features

### User Management
- User registration with email, password, and shop name
- Secure login/logout with session management
- Password hashing with Werkzeug

### Receipt Management
- Create professional receipts with multiple items
- Auto-generate receipt numbers (format: RCP-XXXX-YYYY)
- Download receipts as PDF files
- View and delete receipts

### Freemium Model
- **Free users**: Limited to 15 receipts total
- **Pro users**: Unlimited receipts
- Usage tracking with progress bar
- Automatic redirect to upgrade page when limit reached

### Financial Ledger
- Separate sales and expense journals
- Manual transaction entry
- Automatic transaction creation from receipts
- Real-time analytics on dashboard

### Data Management
- Import transactions from CSV/Excel files
- Export all data to Excel format
- Required columns: description, amount, type
- Optional columns: category, date

### PDF Generation
- Professional receipt PDFs using ReportLab
- Shop name and receipt number
- Customer information
- Itemized list with quantities and prices
- Total amount calculation

## Security Features
- Password hashing with bcrypt
- User data isolation (users only see their own data)
- Input validation and sanitization
- CSRF protection on forms
- Secure session management

## Responsive Design
- Mobile-first approach with Tailwind CSS
- Responsive navigation with mobile menu
- Touch-friendly interface
- Works on all device sizes

## Database Schema

### Users Table
- id (Primary Key)
- email (Unique)
- password_hash
- shop_name
- is_pro (Boolean)
- created_at

### Receipts Table
- id (Primary Key)
- user_id (Foreign Key)
- customer_name
- items (JSON)
- total_amount
- receipt_number (Unique)
- created_at

### Transactions Table
- id (Primary Key)
- user_id (Foreign Key)
- receipt_id (Foreign Key, nullable)
- description
- amount
- type ('sale' or 'expense')
- category
- date
- created_at

## Troubleshooting

### Common Issues

**Database Connection Error**
- Verify DATABASE_URL is correct
- Check if database is accessible
- Ensure postgresql:// format (not postgres://)

**Import Errors**
- Install all requirements: `pip install -r requirements.txt`
- Use Python 3.11 or 3.12 for best compatibility

**PDF Generation Issues**
- Verify ReportLab is installed
- Check file permissions for uploads directory

**Template Not Found**
- Ensure templates directory structure is correct
- Check for missing template files

### Performance Tips
- Use PostgreSQL for production (not SQLite)
- Add database indexes for large datasets
- Implement pagination for large data sets
- Optimize PDF generation for bulk operations

## Monitoring and Maintenance

### Health Checks
- Application health endpoint: `/`
- Database connectivity check
- Error monitoring through Render logs

### Backup Strategy
- Regular database backups through Supabase
- File system backups for uploaded files
- Version control with Git

### Scaling Considerations
- Horizontal scaling with multiple instances
- Database connection pooling
- CDN for static assets
- Caching for frequently accessed data

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review Render deployment logs
3. Verify environment variables
4. Test with local development setup

## License

MIT License - feel free to use this project for commercial purposes.
