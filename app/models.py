# app/models.py - CORRIGÉ
from datetime import datetime, timezone
from .database import db
from sqlalchemy import JSON, Enum, Text, ForeignKey, UniqueConstraint, Index, text
from sqlalchemy.orm import relationship
import json

# ==================== #
# ASSOCIATION TABLES
# ==================== #

# Many-to-many relationship: Account Managers ↔ Customers
account_manager_customers = db.Table('account_manager_customers',
                                     db.Column('account_manager_id', db.Integer,
                                               db.ForeignKey('account_managers.id', ondelete='CASCADE'),
                                               primary_key=True),
                                     db.Column('customer_id', db.Integer,
                                               db.ForeignKey('customers.id', ondelete='CASCADE'),
                                               primary_key=True),
                                     db.Column('assigned_date', db.DateTime, default=datetime.now(timezone.utc)),
                                     db.Column('is_primary', db.Boolean, default=False)
                                     )


# ==================== #
# ACCOUNT MANAGERS / USERS
# ==================== #

class AccountManager(db.Model):
    """Account Manager / User model"""
    __tablename__ = 'account_managers'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Personal Information - RÉDUIT POUR ÉVITER L'ERREUR D'INDEX
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(190), unique=True, nullable=False, index=True)  # CHANGÉ: 190 au lieu de 255
    phone = db.Column(db.String(20))

    # Authentication (for future)
    password_hash = db.Column(db.String(255))
    auth_token = db.Column(db.String(255))
    token_expiry = db.Column(db.DateTime)

    # Role Management
    role = db.Column(
        db.Enum('ADMIN', 'ACCOUNT_MANAGER', name='user_roles'),
        default='ACCOUNT_MANAGER',
        nullable=False
    )
    permissions = db.Column(JSON, default=lambda: json.dumps({}))

    # Status
    is_active = db.Column(db.Boolean, default=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=datetime.now(timezone.utc),
                           onupdate=datetime.now(timezone.utc))
    last_login_at = db.Column(db.DateTime)

    # Relationships
    customers = relationship('Customer',
                             secondary=account_manager_customers,
                             back_populates='account_managers')
    searches = relationship('Search', back_populates='account_manager',
                            cascade='all, delete-orphan')

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': f"{self.first_name} {self.last_name}",
            'email': self.email,
            'phone': self.phone,
            'role': self.role,
            'role_display': 'Administrator' if self.role == 'ADMIN' else 'Account Manager',
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None,
            'customer_count': len(self.customers),
            'search_count': len(self.searches)
        }

    def __repr__(self):
        return f'<AccountManager {self.first_name} {self.last_name}>'


# ==================== #
# CUSTOMERS
# ==================== #

class Customer(db.Model):
    """Customer model for real estate clients"""
    __tablename__ = 'customers'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Basic Information - RÉDUIT POUR ÉVITER L'ERREUR D'INDEX
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    company_name = db.Column(db.String(255))
    email = db.Column(db.String(190), unique=True, nullable=False)  # CHANGÉ: 190 au lieu de 255
    phone = db.Column(db.String(20))

    # Address Information
    street = db.Column(db.String(255))
    house_number = db.Column(db.String(20))
    postal_code = db.Column(db.String(10))
    city = db.Column(db.String(100))
    country_code = db.Column(db.String(2), default='DE')
    search_region = db.Column(Text)

    # ImmoMetrica Credentials
    immometrica_email = db.Column(db.String(190))  # CHANGÉ: 190 au lieu de 255
    immometrica_password = db.Column(db.String(255))

    # Settings (JSON for flexibility)
    property_types = db.Column(JSON, default=lambda: json.dumps([]))
    platforms = db.Column(JSON, default=lambda: json.dumps([]))
    search_filters = db.Column(JSON, default=lambda: json.dumps({}))
    notification_settings = db.Column(JSON, default=lambda: json.dumps({}))

    # Status
    status = db.Column(
        db.Enum('ACTIVE', 'INACTIVE', 'PENDING', 'SUSPENDED', name='customer_status'),
        default='ACTIVE'
    )
    subscription_tier = db.Column(
        db.Enum('BASIC', 'PRO', 'ENTERPRISE', name='subscription_tiers'),
        default='BASIC'
    )

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=datetime.now(timezone.utc),
                           onupdate=datetime.now(timezone.utc))
    last_contact_date = db.Column(db.Date)

    # Relationships
    account_managers = relationship('AccountManager',
                                    secondary=account_manager_customers,
                                    back_populates='customers')
    searches = relationship('Search', back_populates='customer',
                            cascade='all, delete-orphan')
    listings = relationship('Listing', back_populates='customer',
                            cascade='all, delete-orphan')
    mailings = relationship('Mailing', back_populates='customer',
                            cascade='all, delete-orphan')
    appointments = relationship('Appointment', back_populates='customer',
                                cascade='all, delete-orphan')

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': f"{self.first_name} {self.last_name}",
            'company_name': self.company_name,
            'email': self.email,
            'phone': self.phone,
            'address': {
                'street': self.street,
                'house_number': self.house_number,
                'postal_code': self.postal_code,
                'city': self.city,
                'country_code': self.country_code
            } if self.street else None,
            'search_region': self.search_region,
            'immometrica_email': self.immometrica_email,
            'property_types': json.loads(self.property_types) if isinstance(self.property_types,
                                                                            str) else self.property_types,
            'platforms': json.loads(self.platforms) if isinstance(self.platforms, str) else self.platforms,
            'search_filters': json.loads(self.search_filters) if isinstance(self.search_filters,
                                                                            str) else self.search_filters,
            'status': self.status,
            'subscription_tier': self.subscription_tier,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_contact_date': self.last_contact_date.isoformat() if self.last_contact_date else None,
            'account_managers': [am.to_dict() for am in self.account_managers],
            'search_count': len(self.searches),
            'listing_count': len(self.listings)
        }

    def __repr__(self):
        return f'<Customer {self.first_name} {self.last_name}>'


# ==================== #
# SEARCHES
# ==================== #

class Search(db.Model):
    """Search configuration model"""
    __tablename__ = 'searches'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    customer_id = db.Column(db.Integer,
                            db.ForeignKey('customers.id', ondelete='CASCADE'),
                            nullable=False)
    account_manager_id = db.Column(db.Integer,
                                   db.ForeignKey('account_managers.id'),
                                   nullable=False)

    # Search Information
    name = db.Column(db.String(255), nullable=False)
    location_postcode = db.Column(db.String(10))
    radius_km = db.Column(db.Integer, default=50)

    # Filters
    price_min = db.Column(db.Numeric(12, 2))
    price_max = db.Column(db.Numeric(12, 2))
    min_units = db.Column(db.Integer, default=1)
    property_types = db.Column(JSON, default=lambda: json.dumps([]))
    platforms = db.Column(JSON, default=lambda: json.dumps([]))
    custom_filters = db.Column(JSON, default=lambda: json.dumps({}))

    # Status & Scheduling
    is_active = db.Column(db.Boolean, default=True)
    frequency_hours = db.Column(db.Integer, default=24)
    last_run_at = db.Column(db.DateTime)
    next_run_at = db.Column(db.DateTime)

    # Results Tracking
    total_listings_found = db.Column(db.Integer, default=0)
    last_listings_count = db.Column(db.Integer, default=0)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=datetime.now(timezone.utc),
                           onupdate=datetime.now(timezone.utc))

    # Relationships
    customer = relationship('Customer', back_populates='searches')
    account_manager = relationship('AccountManager', back_populates='searches')

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'customer_id': self.customer_id,
            'customer_name': f"{self.customer.first_name} {self.customer.last_name}" if self.customer else None,
            'account_manager_id': self.account_manager_id,
            'location_postcode': self.location_postcode,
            'radius_km': self.radius_km,
            'price_range': {
                'min': float(self.price_min) if self.price_min else None,
                'max': float(self.price_max) if self.price_max else None
            },
            'min_units': self.min_units,
            'property_types': json.loads(self.property_types) if isinstance(self.property_types,
                                                                            str) else self.property_types,
            'platforms': json.loads(self.platforms) if isinstance(self.platforms, str) else self.platforms,
            'custom_filters': json.loads(self.custom_filters) if isinstance(self.custom_filters,
                                                                            str) else self.custom_filters,
            'is_active': self.is_active,
            'frequency_hours': self.frequency_hours,
            'last_run_at': self.last_run_at.isoformat() if self.last_run_at else None,
            'next_run_at': self.next_run_at.isoformat() if self.next_run_at else None,
            'total_listings_found': self.total_listings_found,
            'last_listings_count': self.last_listings_count,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<Search {self.name} for Customer {self.customer_id}>'



# ==================== #
# LISTINGS
# ==================== #

class Listing(db.Model):
    __tablename__ = 'listings'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    customer_id = db.Column(db.Integer,
                            db.ForeignKey('customers.id', ondelete='CASCADE'),
                            nullable=False)
    search_id = db.Column(db.Integer,
                          db.ForeignKey('searches.id', ondelete='SET NULL'))


    external_id = db.Column(db.String(100), unique=True)

    title = db.Column(db.String(200), nullable=False)
    description = db.Column(Text)
    platform = db.Column(db.String(50))
    platform_display = db.Column(db.String(100))
    url = db.Column(Text)
    location = db.Column(db.String(150))
    address = db.Column(db.String(200))
    postal_code = db.Column(db.String(10))
    city = db.Column(db.String(100))
    property_type = db.Column(db.String(100))
    rooms = db.Column(db.Float)
    living_area = db.Column(db.Float)
    year_built = db.Column(db.Integer)
    price = db.Column(db.Numeric(12, 2))
    price_per_sqm = db.Column(db.Numeric(10, 2))
    contact_name = db.Column(db.String(150))
    contact_phone = db.Column(db.String(50))
    contact_email = db.Column(db.String(100))
    status = db.Column(
        db.Enum('new', 'contacted', 'responded', 'appointment', 'closed', name='listing_status'),
        default='new'
    )
    mailing_history = db.Column(JSON, default=lambda: json.dumps([]))
    scraped_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    contacted_at = db.Column(db.DateTime)
    responded_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=datetime.now(timezone.utc),
                           onupdate=datetime.now(timezone.utc))

    customer = relationship('Customer', back_populates='listings')
    search = relationship('Search')
    mailings = relationship('Mailing', back_populates='listing',
                            cascade='all, delete-orphan')
    appointments = relationship('Appointment', back_populates='listing',
                                cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'platform': self.platform,
            'platform_display': self.platform_display,
            'location': self.location,
            'address': self.address,
            'postal_code': self.postal_code,
            'city': self.city,
            'rooms': self.rooms,
            'living_area': self.living_area,
            'year_built': self.year_built,
            'price': float(self.price) if self.price else None,
            'price_per_sqm': float(self.price_per_sqm) if self.price_per_sqm else None,
            'contact_name': self.contact_name,
            'contact_phone': self.contact_phone,
            'contact_email': self.contact_email,
            'status': self.status,
            'scraped_at': self.scraped_at.isoformat() if self.scraped_at else None,
            'contacted_at': self.contacted_at.isoformat() if self.contacted_at else None,
            'responded_at': self.responded_at.isoformat() if self.responded_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'customer_id': self.customer_id,
            'search_id': self.search_id,
            'external_id': self.external_id,
            'mailing_history': json.loads(self.mailing_history) if isinstance(self.mailing_history,
                                                                              str) else self.mailing_history
        }

    def __repr__(self):
        return f'<Listing {self.title} ({self.platform})>'

# ==================== #
# MAILINGS
# ==================== #

class Mailing(db.Model):
    """Mailing history model"""
    __tablename__ = 'mailings'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    listing_id = db.Column(db.Integer,
                           db.ForeignKey('listings.id', ondelete='CASCADE'),
                           nullable=False)
    customer_id = db.Column(db.Integer,
                            db.ForeignKey('customers.id', ondelete='CASCADE'),
                            nullable=False)

    # Mailing Details
    type = db.Column(db.String(50))  # initial, followup_1, followup_2
    subject = db.Column(db.String(500))
    content = db.Column(Text, nullable=False)

    # Status
    status = db.Column(
        db.Enum('sent', 'delivered', 'opened', 'clicked', 'replied', 'error', name='mailing_status'),
        default='sent'
    )

    # Response
    response_content = db.Column(Text)
    response_at = db.Column(db.DateTime)

    # Timestamps
    sent_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))

    # Relationships
    listing = relationship('Listing', back_populates='mailings')
    customer = relationship('Customer', back_populates='mailings')

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'listing_id': self.listing_id,
            'customer_id': self.customer_id,
            'type': self.type,
            'subject': self.subject,
            'content': self.content,
            'status': self.status,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'response_content': self.response_content,
            'response_at': self.response_at.isoformat() if self.response_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<Mailing {self.type} for Listing {self.listing_id}>'


# ==================== #
# APPOINTMENTS
# ==================== #

class Appointment(db.Model):
    """Appointment model"""
    __tablename__ = 'appointments'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    listing_id = db.Column(db.Integer,
                           db.ForeignKey('listings.id', ondelete='SET NULL'))
    customer_id = db.Column(db.Integer,
                            db.ForeignKey('customers.id', ondelete='CASCADE'),
                            nullable=False)

    # Appointment Details
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(Text)

    # Client Information
    client_name = db.Column(db.String(200))
    client_email = db.Column(db.String(190))  # CHANGÉ: 190 au lieu de 255
    client_phone = db.Column(db.String(50))

    # Appointment Details
    scheduled_at = db.Column(db.DateTime, nullable=False)
    duration_minutes = db.Column(db.Integer, default=60)
    location = db.Column(db.String(500))

    # Status
    status = db.Column(
        db.Enum('scheduled', 'confirmed', 'completed', 'cancelled', name='appointment_status'),
        default='scheduled'
    )

    # Notes
    notes = db.Column(Text)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=datetime.now(timezone.utc),
                           onupdate=datetime.now(timezone.utc))

    # Relationships
    listing = relationship('Listing', back_populates='appointments')
    customer = relationship('Customer', back_populates='appointments')

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'client_name': self.client_name,
            'client_email': self.client_email,
            'client_phone': self.client_phone,
            'scheduled_at': self.scheduled_at.isoformat() if self.scheduled_at else None,
            'duration_minutes': self.duration_minutes,
            'location': self.location,
            'status': self.status,
            'status_display': 'positive' if self.status in ['confirmed', 'completed'] else 'pending',
            'notes': self.notes,
            'listing_id': self.listing_id,
            'customer_id': self.customer_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<Appointment {self.title} with {self.client_name}>'