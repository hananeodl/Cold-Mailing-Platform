# app/__init__.py - CORRIGÉ
from flask import Flask
from flask_cors import CORS
from config import config
from .database import db
from .api import api_bp


def create_app(config_class=config):
    """Application factory"""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Enable CORS for development
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Initialize database
    db.init_app(app)

    # Register blueprints
    app.register_blueprint(api_bp)

    # Create tables (for development)
    with app.app_context():
        try:
            db.create_all()
            print(" Database tables created successfully!")

            # Create initial data if tables are empty
            create_initial_data()

        except Exception as e:
            print(f" Error creating tables: {e}")
            raise  # Ajoutez cette ligne pour voir l'erreur complète

    # Add headers for mobile app
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response

    return app


def create_initial_data():
    """Create initial data if tables are empty"""
    from .models import AccountManager, Customer, Search, Listing, Mailing, Appointment
    from datetime import datetime, timezone, timedelta
    import json

    # Check if we have any account managers
    if AccountManager.query.count() == 0:
        print(" Creating initial data...")

        # Create admin account
        admin = AccountManager(
            first_name='Daniel',
            last_name='Mathiesen',
            email='daniel@extraimmobilien.de',
            phone='+49 ********',
            role='ADMIN',
            is_active=True
        )
        db.session.add(admin)

        # Create account manager
        am = AccountManager(
            first_name='Rania',
            last_name='rania',
            email='rania@extraimmobilien.de',
            phone='+212 *********',
            role='ACCOUNT_MANAGER',
            is_active=True
        )
        db.session.add(am)

        db.session.commit()
        print(" Initial account managers created")

    # Check if we have any customers
    if Customer.query.count() == 0:
        # Create a customer
        customer = Customer(
            first_name='Customer',
            last_name='customer',
            company_name='Customer Immobilien GmbH',
            email='Customer@customer-immobilien.de',
            phone='+49 *********',
            street='Musterstraße',
            house_number='123',
            postal_code='44789',
            city='Bochum',
            country_code='DE',
            search_region='Ruhrgebiet, NRW',
            immometrica_email='Customer@immometrica-immobilien.de',
            immometrica_password='secure_password_123',
            property_types=json.dumps(['Mehrfamilienhaus', 'Wohn- & Geschäftshaus']),
            platforms=json.dumps(['kleinanzeigen', 'immoscout24', 'immowelt']),
            search_filters=json.dumps({
                'min_price': 250000,
                'max_price': 2500000,
                'min_units': 4,
                'radius_km': 50
            }),
            status='ACTIVE',
            subscription_tier='PRO',
            last_contact_date=datetime.now(timezone.utc).date()
        )
        db.session.add(customer)

        # Link customer to account manager
        am = AccountManager.query.filter_by(role='ACCOUNT_MANAGER').first()
        if am:
            customer.account_managers.append(am)

        db.session.commit()
        print(" Initial customer created")