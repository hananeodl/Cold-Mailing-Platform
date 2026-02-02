#!/usr/bin/env python3
"""
Quick Start Script for Extra Immobilien Platform
Helps you get started quickly with proper setup checks
"""

import os
import sys
import subprocess
from pathlib import Path


def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60 + "\n")


def check_python_version():
    """Check if Python version is compatible"""
    print("✓ Checking Python version...")
    if sys.version_info < (3, 8):
        print(" Python 3.8 or higher is required")
        print(f"   Current version: {sys.version}")
        return False
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True


def check_redis():
    """Check if Redis is running"""
    print("\n✓ Checking Redis...")
    try:
        result = subprocess.run(
            ['redis-cli', 'ping'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.stdout.strip() == 'PONG':
            print("✓ Redis is running")
            return True
        else:
            print("Redis is not responding")
            return False
    except FileNotFoundError:
        print(" Redis is not installed")
        print("   Install Redis:")
        print("   - Ubuntu/Debian: sudo apt-get install redis-server")
        print("   - macOS: brew install redis")
        print("   - Windows: Use WSL or download from https://redis.io/download")
        return False
    except Exception as e:
        print(f"Error checking Redis: {e}")
        return False


def check_mysql():
    """Check if MySQL is accessible"""
    print("\n Checking MySQL...")
    try:
        import pymysql
        # Try to connect (will fail if credentials wrong, but at least MySQL is installed)
        print(" PyMySQL is installed")
        return True
    except ImportError:
        print(" PyMySQL is not installed")
        print("   Run: pip install -r requirements.txt")
        return False


def check_env_file():
    """Check if .env file exists"""
    print("\n Checking .env file...")
    env_path = Path('.env')
    if not env_path.exists():
        print("  .env file not found")
        print("   Creating template .env file...")

        env_template = """# Flask Settings
FLASK_ENV=development
SECRET_KEY=dev-secret-key-change-in-production
DEBUG=True

# Database Settings
DATABASE_URI=mysql+pymysql://root:password@localhost/extra_immobilien

# Celery Settings
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Automation Settings
CSV_IMPORT_DIR=/home/rania/Downloads
SELENIUM_HEADLESS=False

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
"""

        with open('.env', 'w') as f:
            f.write(env_template)

        print(" Template .env file created")
        print("  Please update .env with your actual settings!")
        return False
    else:
        print(" .env file exists")
        return True


def install_dependencies():
    """Install Python dependencies"""
    print("\n Installing dependencies...")
    try:
        subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'],
            check=True
        )
        print(" Dependencies installed")
        return True
    except subprocess.CalledProcessError as e:
        print(f" Failed to install dependencies: {e}")
        return False


def create_logs_directory():
    """Create logs directory if it doesn't exist"""
    print("\n Creating logs directory...")
    logs_dir = Path('logs')
    logs_dir.mkdir(exist_ok=True)
    print(" Logs directory ready")


def print_next_steps():
    """Print next steps for user"""
    print_header(" Setup Complete!")

    print("Next steps:")
    print("\n1. Update your .env file with correct settings:")
    print("   - Database credentials")
    print("   - CSV import directory path")
    print("   - Secret key for production")

    print("\n2. Initialize the database:")
    print("   python scripts/init_database.py")

    print("\n3. Start the services (in separate terminals):")
    print("\n   Terminal 1 - Flask API:")
    print("   python run.py")

    print("\n   Terminal 2 - Celery Worker:")
    print("   celery -A celery_worker.celery worker --loglevel=info --pool=solo")

    print("\n   Terminal 3 - Celery Beat (optional for scheduled tasks):")
    print("   celery -A celery_worker.celery beat --loglevel=info")

    print("\n4. Test the API:")
    print("   curl http://localhost:5000/health")

    print("\n5. Read the full guide:")
    print("   cat INTEGRATION_GUIDE.md")

    print("\n" + "=" * 60 + "\n")


def main():
    """Main setup function"""
    print_header(" Extra Immobilien Platform - Quick Setup")

    # Run checks
    checks = [
        ("Python Version", check_python_version()),
        ("Redis Server", check_redis()),
        ("MySQL/PyMySQL", check_mysql()),
        (".env File", check_env_file()),
    ]

    # Create logs directory
    create_logs_directory()

    # Install dependencies
    print_header(" Installing Dependencies")
    install_dependencies()

    # Summary
    print_header(" Setup Summary")
    all_passed = True
    for name, passed in checks:
        status = "✓" if passed else "❌"
        print(f"{status} {name}")
        if not passed:
            all_passed = False

    if all_passed:
        print("\n All checks passed!")
    else:
        print("\n  Some checks failed. Please fix the issues above.")
        print("   See INTEGRATION_GUIDE.md for detailed instructions.")

    # Print next steps
    print_next_steps()


if __name__ == '__main__':
    main()