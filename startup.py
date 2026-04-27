"""
Startup script for Render deployment
Handles database initialization and provides startup validation
"""

import os
import sys
from models import DatabaseManager

def validate_environment():
    """Validate environment for deployment"""
    print("🔍 Validating deployment environment...")
    
    # Check if we can write to current directory
    try:
        test_file = "startup_test.txt"
        with open(test_file, 'w') as f:
            f.write("test")
        os.remove(test_file)
        print("✅ Directory write permissions: OK")
    except Exception as e:
        print(f"❌ Directory write permissions: FAILED - {e}")
        return False
    
    # Test database creation
    try:
        db = DatabaseManager()
        print("✅ Database initialization: OK")
        return True
    except Exception as e:
        print(f"❌ Database initialization: FAILED - {e}")
        return False

def main():
    """Main startup function"""
    print("🚀 Starting Pang-Kape Bookkeeping System...")
    
    if validate_environment():
        print("✅ Environment validation passed")
        print("🌐 Application is ready to start")
        return 0
    else:
        print("❌ Environment validation failed")
        print("🔧 Please check deployment configuration")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
