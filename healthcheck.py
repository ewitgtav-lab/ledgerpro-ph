"""
Health check endpoint for Render deployment
This file can be used as a simple health check for the Streamlit app
"""

import sys
import os
from models import DatabaseManager

def health_check():
    """Simple health check function"""
    try:
        # Test database connection
        db = DatabaseManager()
        with db.get_connection() as conn:
            conn.execute("SELECT 1")
        
        return {
            "status": "healthy",
            "database": "connected",
            "message": "All systems operational"
        }
    except Exception as e:
        return {
            "status": "unhealthy", 
            "database": "disconnected",
            "message": f"Error: {str(e)}"
        }

if __name__ == "__main__":
    # For testing purposes
    result = health_check()
    print(f"Health Status: {result['status']}")
    print(f"Database: {result['database']}")
    print(f"Message: {result['message']}")
    
    # Exit with appropriate code for CI/CD
    sys.exit(0 if result['status'] == 'healthy' else 1)
