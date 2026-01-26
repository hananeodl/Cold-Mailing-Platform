# app/services.py
from typing import List, Dict, Any, Optional
from sqlalchemy import or_, and_, func
from .models import AccountManager, Customer, Search, Listing, Mailing, Appointment, db
from datetime import datetime, timezone
import json


class AccountManagerService:
    """Service for Account Manager CRUD operations"""

    @staticmethod
    def create_account_manager(data: Dict[str, Any]) -> AccountManager:
        """Create a new account manager"""
        # Validate required fields
        required_fields = ['first_name', 'last_name', 'email']
        for field in required_fields:
            if field not in data or not data[field]:
                raise ValueError(f"Missing required field: {field}")

        # Check if email already exists
        existing = AccountManager.query.filter_by(email=data['email']).first()
        if existing:
            raise ValueError(f"Account manager with email {data['email']} already exists")

        # Create new account manager
        account_manager = AccountManager(
            first_name=data['first_name'],
            last_name=data['last_name'],
            email=data['email'],
            phone=data.get('phone'),
            role=data.get('role', 'ACCOUNT_MANAGER'),
            is_active=data.get('is_active', True)
        )

        db.session.add(account_manager)
        db.session.commit()

        return account_manager

    @staticmethod
    def get_all_account_managers(active_only: bool = True) -> List[AccountManager]:
        """Get all account managers"""
        query = AccountManager.query

        if active_only:
            query = query.filter_by(is_active=True)

        return query.order_by(
            AccountManager.role,
            AccountManager.last_name,
            AccountManager.first_name
        ).all()

    @staticmethod
    def get_account_manager_by_id(account_manager_id: int) -> Optional[AccountManager]:
        """Get account manager by ID"""
        return AccountManager.query.get(account_manager_id)

    @staticmethod
    def get_account_manager_by_email(email: str) -> Optional[AccountManager]:
        """Get account manager by email"""
        return AccountManager.query.filter_by(email=email).first()

    @staticmethod
    def update_account_manager(account_manager_id: int, data: Dict[str, Any]) -> AccountManager:
        """Update account manager"""
        account_manager = AccountManagerService.get_account_manager_by_id(account_manager_id)
        if not account_manager:
            raise ValueError(f"Account manager with ID {account_manager_id} not found")

        # Update fields
        if 'first_name' in data:
            account_manager.first_name = data['first_name']
        if 'last_name' in data:
            account_manager.last_name = data['last_name']
        if 'phone' in data:
            account_manager.phone = data['phone']
        if 'role' in data:
            account_manager.role = data['role']
        if 'is_active' in data:
            account_manager.is_active = data['is_active']

        db.session.commit()
        return account_manager

    @staticmethod
    def delete_account_manager(account_manager_id: int, soft_delete: bool = True) -> bool:
        """Delete or deactivate account manager"""
        account_manager = AccountManagerService.get_account_manager_by_id(account_manager_id)
        if not account_manager:
            return False

        if soft_delete:
            # Soft delete (deactivate)
            account_manager.is_active = False
            db.session.commit()
            return True
        else:
            # Hard delete
            db.session.delete(account_manager)
            db.session.commit()
            return True


class CustomerService:
    """Service for Customer CRUD operations"""

    @staticmethod
    def create_customer(data: Dict[str, Any]) -> Customer:
        """Create a new customer"""
        # Validate required fields
        required_fields = ['first_name', 'last_name', 'email']
        for field in required_fields:
            if field not in data or not data[field]:
                raise ValueError(f"Missing required field: {field}")

        # Check if email already exists
        existing = Customer.query.filter_by(email=data['email']).first()
        if existing:
            raise ValueError(f"Customer with email {data['email']} already exists")

        # Create new customer
        customer = Customer(
            first_name=data['first_name'],
            last_name=data['last_name'],
            company_name=data.get('company_name'),
            email=data['email'],
            phone=data.get('phone'),
            street=data.get('street'),
            house_number=data.get('house_number'),
            postal_code=data.get('postal_code'),
            city=data.get('city'),
            country_code=data.get('country_code', 'DE'),
            search_region=data.get('search_region'),
            immometrica_email=data.get('immometrica_email'),
            immometrica_password=data.get('immometrica_password'),
            property_types=json.dumps(data.get('property_types', [])),
            platforms=json.dumps(data.get('platforms', [])),
            search_filters=json.dumps(data.get('search_filters', {})),
            status=data.get('status', 'ACTIVE'),
            subscription_tier=data.get('subscription_tier', 'BASIC')
        )

        db.session.add(customer)
        db.session.commit()

        # Link to account managers if provided
        if 'account_manager_ids' in data and data['account_manager_ids']:
            CustomerService.assign_account_managers(customer.id, data['account_manager_ids'])

        return customer

    @staticmethod
    def get_all_customers(filters: Optional[Dict[str, Any]] = None) -> List[Customer]:
        """Get all customers with optional filters"""
        query = Customer.query

        if filters:
            # Apply filters
            if 'status' in filters:
                query = query.filter_by(status=filters['status'])
            if 'subscription_tier' in filters:
                query = query.filter_by(subscription_tier=filters['subscription_tier'])
            if 'account_manager_id' in filters:
                query = query.filter(Customer.account_managers.any(id=filters['account_manager_id']))
            if 'search_text' in filters:
                search_text = f"%{filters['search_text']}%"
                query = query.filter(or_(
                    Customer.first_name.ilike(search_text),
                    Customer.last_name.ilike(search_text),
                    Customer.company_name.ilike(search_text),
                    Customer.email.ilike(search_text),
                    Customer.city.ilike(search_text)
                ))

        return query.order_by(Customer.last_name, Customer.first_name).all()

    @staticmethod
    def get_customer_by_id(customer_id: int) -> Optional[Customer]:
        """Get customer by ID"""
        return Customer.query.get(customer_id)

    @staticmethod
    def update_customer(customer_id: int, data: Dict[str, Any]) -> Customer:
        """Update customer"""
        customer = CustomerService.get_customer_by_id(customer_id)
        if not customer:
            raise ValueError(f"Customer with ID {customer_id} not found")

        # Update basic fields
        update_fields = [
            'first_name', 'last_name', 'company_name', 'email', 'phone',
            'street', 'house_number', 'postal_code', 'city', 'country_code',
            'search_region', 'immometrica_email', 'immometrica_password',
            'property_types', 'platforms', 'search_filters', 'status',
            'subscription_tier', 'last_contact_date'
        ]

        for field in update_fields:
            if field in data:
                if field in ['property_types', 'platforms', 'search_filters']:
                    setattr(customer, field, json.dumps(data[field]))
                else:
                    setattr(customer, field, data[field])

        # Update account managers if provided
        if 'account_manager_ids' in data:
            CustomerService.assign_account_managers(customer_id, data['account_manager_ids'])

        db.session.commit()
        return customer

    @staticmethod
    def delete_customer(customer_id: int) -> bool:
        """Delete customer"""
        customer = CustomerService.get_customer_by_id(customer_id)
        if not customer:
            return False

        db.session.delete(customer)
        db.session.commit()
        return True

    @staticmethod
    def assign_account_managers(customer_id: int, account_manager_ids: List[int]) -> Customer:
        """Assign account managers to a customer"""
        customer = CustomerService.get_customer_by_id(customer_id)
        if not customer:
            raise ValueError(f"Customer with ID {customer_id} not found")

        # Clear existing assignments
        customer.account_managers.clear()

        # Add new assignments
        for am_id in account_manager_ids:
            account_manager = AccountManagerService.get_account_manager_by_id(am_id)
            if account_manager:
                customer.account_managers.append(account_manager)

        db.session.commit()
        return customer


class SearchService:
    """Service for Search CRUD operations"""

    @staticmethod
    def create_search(data: Dict[str, Any]) -> Search:
        """Create a new search"""
        required_fields = ['name', 'customer_id', 'account_manager_id']
        for field in required_fields:
            if field not in data or not data[field]:
                raise ValueError(f"Missing required field: {field}")

        # Create new search
        search = Search(
            name=data['name'],
            customer_id=data['customer_id'],
            account_manager_id=data['account_manager_id'],
            location_postcode=data.get('location_postcode'),
            radius_km=data.get('radius_km', 50),
            price_min=data.get('price_min'),
            price_max=data.get('price_max'),
            min_units=data.get('min_units', 1),
            property_types=json.dumps(data.get('property_types', [])),
            platforms=json.dumps(data.get('platforms', [])),
            custom_filters=json.dumps(data.get('custom_filters', {})),
            is_active=data.get('is_active', True),
            frequency_hours=data.get('frequency_hours', 24),
            next_run_at=data.get('next_run_at')
        )

        db.session.add(search)
        db.session.commit()
        return search

    @staticmethod
    def get_all_searches(filters: Optional[Dict[str, Any]] = None) -> List[Search]:
        """Get all searches with optional filters"""
        query = Search.query

        if filters:
            if 'customer_id' in filters:
                query = query.filter_by(customer_id=filters['customer_id'])
            if 'account_manager_id' in filters:
                query = query.filter_by(account_manager_id=filters['account_manager_id'])
            if 'is_active' in filters:
                query = query.filter_by(is_active=filters['is_active'])

        return query.order_by(Search.created_at.desc()).all()

    @staticmethod
    def get_search_by_id(search_id: int) -> Optional[Search]:
        """Get search by ID"""
        return Search.query.get(search_id)

    @staticmethod
    def update_search(search_id: int, data: Dict[str, Any]) -> Search:
        """Update search"""
        search = SearchService.get_search_by_id(search_id)
        if not search:
            raise ValueError(f"Search with ID {search_id} not found")

        # Update fields
        update_fields = [
            'name', 'location_postcode', 'radius_km', 'price_min', 'price_max',
            'min_units', 'property_types', 'platforms', 'custom_filters',
            'is_active', 'frequency_hours', 'next_run_at'
        ]

        for field in update_fields:
            if field in data:
                if field in ['property_types', 'platforms', 'custom_filters']:
                    setattr(search, field, json.dumps(data[field]))
                else:
                    setattr(search, field, data[field])

        db.session.commit()
        return search

    @staticmethod
    def delete_search(search_id: int) -> bool:
        """Delete search"""
        search = SearchService.get_search_by_id(search_id)
        if not search:
            return False

        db.session.delete(search)
        db.session.commit()
        return True

    @staticmethod
    def update_search_results(search_id: int, listings_found: int) -> Search:
        """Update search results after running"""
        search = SearchService.get_search_by_id(search_id)
        if not search:
            raise ValueError(f"Search with ID {search_id} not found")

        search.last_run_at = datetime.now(timezone.utc)
        search.last_listings_count = listings_found
        search.total_listings_found += listings_found

        # Calculate next run (simple scheduling)
        if search.frequency_hours:
            from datetime import timedelta
            search.next_run_at = search.last_run_at + timedelta(hours=search.frequency_hours)

        db.session.commit()
        return search


class ListingService:
    """Service for Listing CRUD operations"""

    @staticmethod
    def create_listing(data: Dict[str, Any]) -> Listing:
        """Create a new listing"""
        required_fields = ['title', 'platform', 'customer_id']
        for field in required_fields:
            if field not in data or not data[field]:
                raise ValueError(f"Missing required field: {field}")

        # Create new listing
        listing = Listing(
            title=data['title'],
            customer_id=data['customer_id'],
            search_id=data.get('search_id'),
            external_id=data.get('external_id'),
            platform=data['platform'],
            platform_display=data.get('platform_display', data['platform']),
            location=data.get('location'),
            address=data.get('address'),
            postal_code=data.get('postal_code'),
            city=data.get('city'),
            property_type=data.get('property_type'),
            rooms=data.get('rooms'),
            living_area=data.get('living_area'),
            year_built=data.get('year_built'),
            price=data.get('price'),
            price_per_sqm=data.get('price_per_sqm'),
            contact_name=data.get('contact_name'),
            contact_phone=data.get('contact_phone'),
            contact_email=data.get('contact_email'),
            status=data.get('status', 'new'),
            url=data.get('url'),
            description=data.get('description')
        )

        db.session.add(listing)
        db.session.commit()
        return listing

    @staticmethod
    def get_all_listings(filters: Optional[Dict[str, Any]] = None) -> List[Listing]:
        """Get all listings with optional filters"""
        query = Listing.query

        if filters:
            if 'customer_id' in filters:
                query = query.filter_by(customer_id=filters['customer_id'])
            if 'search_id' in filters:
                query = query.filter_by(search_id=filters['search_id'])
            if 'platform' in filters:
                query = query.filter_by(platform=filters['platform'])
            if 'status' in filters:
                query = query.filter_by(status=filters['status'])
            if 'min_price' in filters:
                query = query.filter(Listing.price >= filters['min_price'])
            if 'max_price' in filters:
                query = query.filter(Listing.price <= filters['max_price'])
            if 'search_text' in filters:
                search_text = f"%{filters['search_text']}%"
                query = query.filter(or_(
                    Listing.title.ilike(search_text),
                    Listing.location.ilike(search_text),
                    Listing.address.ilike(search_text)
                ))

        return query.order_by(Listing.scraped_at.desc()).all()

    @staticmethod
    def get_listing_by_id(listing_id: int) -> Optional[Listing]:
        """Get listing by ID"""
        return Listing.query.get(listing_id)

    @staticmethod
    def update_listing_status(listing_id: int, status: str) -> Listing:
        """Update listing status"""
        listing = ListingService.get_listing_by_id(listing_id)
        if not listing:
            raise ValueError(f"Listing with ID {listing_id} not found")

        valid_statuses = ['new', 'contacted', 'responded', 'appointment', 'closed']
        if status not in valid_statuses:
            raise ValueError(f"Invalid status. Must be one of: {valid_statuses}")

        listing.status = status

        # Update timestamps based on status
        now = datetime.now(timezone.utc)
        if status == 'contacted' and not listing.contacted_at:
            listing.contacted_at = now
        elif status == 'responded' and not listing.responded_at:
            listing.responded_at = now

        db.session.commit()
        return listing

    @staticmethod
    def delete_listing(listing_id: int) -> bool:
        """Delete listing"""
        listing = ListingService.get_listing_by_id(listing_id)
        if not listing:
            return False

        db.session.delete(listing)
        db.session.commit()
        return True


class DashboardService:
    """Service for Dashboard statistics"""

    @staticmethod
    def get_dashboard_stats(customer_id: Optional[int] = None) -> Dict[str, Any]:
        """Get dashboard statistics"""
        stats = {}

        # Get counts
        if customer_id:
            # For specific customer
            stats['listings_count'] = Listing.query.filter_by(
                customer_id=customer_id
            ).count()

            stats['listings_by_status'] = {
                'new': Listing.query.filter_by(
                    customer_id=customer_id, status='new'
                ).count(),
                'contacted': Listing.query.filter_by(
                    customer_id=customer_id, status='contacted'
                ).count(),
                'responded': Listing.query.filter_by(
                    customer_id=customer_id, status='responded'
                ).count(),
                'appointment': Listing.query.filter_by(
                    customer_id=customer_id, status='appointment'
                ).count()
            }

            stats['mailings_count'] = Mailing.query.filter_by(
                customer_id=customer_id
            ).count()

            stats['appointments_count'] = Appointment.query.filter_by(
                customer_id=customer_id
            ).count()

            # Calculate response rate
            total_mailings = stats['mailings_count']
            responded_mailings = Mailing.query.filter_by(
                customer_id=customer_id, status='replied'
            ).count()

            stats['response_rate'] = round(
                (responded_mailings / total_mailings * 100) if total_mailings > 0 else 0,
                2
            )

        else:
            # For all customers (admin view)
            stats['customers_count'] = Customer.query.filter_by(
                status='ACTIVE'
            ).count()

            stats['account_managers_count'] = AccountManager.query.filter_by(
                is_active=True
            ).count()

            stats['searches_count'] = Search.query.filter_by(
                is_active=True
            ).count()

            stats['total_listings'] = Listing.query.count()

        return stats

    @staticmethod
    def get_platform_distribution(customer_id: Optional[int] = None) -> Dict[str, int]:
        """Get listing distribution by platform"""
        from sqlalchemy import func

        query = db.session.query(
            Listing.platform,
            func.count(Listing.id).label('count')
        )

        if customer_id:
            query = query.filter_by(customer_id=customer_id)

        query = query.group_by(Listing.platform)

        results = query.all()
        return {platform: count for platform, count in results}