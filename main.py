from app import create_app

app = create_app()

if __name__ == '__main__':
    print("Starting EXTRA Immobilien Backend API...")
    print("API available at: http://localhost:5000")
    print("API documentation:")
    print("  - GET  /api/v1/account-managers")
    print("  - POST /api/v1/account-managers")
    print("  - GET  /api/v1/customers")
    print("  - POST /api/v1/customers")
    print("  - GET  /api/v1/dashboard/stats")
    app.run(debug=True, host='0.0.0.0', port=5000)