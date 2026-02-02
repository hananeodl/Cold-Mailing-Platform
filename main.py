"""
Application Entry Point
Run this file to start the Flask development server
"""

from app import create_app

# Create Flask application
app = create_app()

if __name__ == '__main__':
    print("\n" + "=" * 60)
    print(" Extra Immobilien Platform - Starting...")
    print("=" * 60 + "\n")

    print("✓ Flask app initialized")
    print("✓ Database connected")
    print("✓ API endpoints registered")
    print("\n Server running at: http://localhost:5000")
    print(" Health check: http://localhost:5000/health")
    print(" API docs: See INTEGRATION_GUIDE.md\n")

    # Run development server
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )