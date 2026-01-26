from flask import Blueprint, request, jsonify
from .services import AccountManagerService, CustomerService, SearchService
from .models import db

# Create blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api/v1')


# Helper function for error responses
def error_response(message, status_code=400):
    return jsonify({'error': message}), status_code


# Helper function for success responses
def success_response(data, message=None, status_code=200):
    response = {'success': True, 'data': data}
    if message:
        response['message'] = message
    return jsonify(response), status_code


# ==================== #
# ACCOUNT MANAGER ENDPOINTS
# ==================== #

@api_bp.route('/account-managers', methods=['GET'])
def get_account_managers():
    """Get all account managers"""
    try:
        active_only = request.args.get('active_only', 'true').lower() == 'true'
        account_managers = AccountManagerService.get_all_account_managers(active_only)
        return success_response([am.to_dict() for am in account_managers])
    except Exception as e:
        return error_response(str(e), 500)


@api_bp.route('/account-managers', methods=['POST'])
def create_account_manager():
    """Create a new account manager"""
    try:
        data = request.get_json()
        if not data:
            return error_response('No data provided')

        account_manager = AccountManagerService.create_account_manager(data)
        return success_response(account_manager.to_dict(), 'Account manager created successfully', 201)
    except ValueError as e:
        return error_response(str(e), 400)
    except Exception as e:
        return error_response(str(e), 500)


@api_bp.route('/account-managers/<int:account_manager_id>', methods=['GET'])
def get_account_manager(account_manager_id):
    """Get account manager by ID"""
    try:
        account_manager = AccountManagerService.get_account_manager_by_id(account_manager_id)
        if not account_manager:
            return error_response('Account manager not found', 404)

        return success_response(account_manager.to_dict())
    except Exception as e:
        return error_response(str(e), 500)


@api_bp.route('/account-managers/<int:account_manager_id>', methods=['PUT'])
def update_account_manager(account_manager_id):
    """Update account manager"""
    try:
        data = request.get_json()
        if not data:
            return error_response('No data provided')

        account_manager = AccountManagerService.update_account_manager(account_manager_id, data)
        return success_response(account_manager.to_dict(), 'Account manager updated successfully')
    except ValueError as e:
        return error_response(str(e), 400)
    except Exception as e:
        return error_response(str(e), 500)


@api_bp.route('/account-managers/<int:account_manager_id>', methods=['DELETE'])
def delete_account_manager(account_manager_id):
    """Delete account manager"""
    try:
        soft_delete = request.args.get('soft_delete', 'true').lower() == 'true'

        success = AccountManagerService.delete_account_manager(account_manager_id, soft_delete)
        if not success:
            return error_response('Account manager not found', 404)

        message = 'Account manager deactivated successfully' if soft_delete else 'Account manager deleted successfully'
        return success_response(None, message)
    except Exception as e:
        return error_response(str(e), 500)


# ==================== #
# CUSTOMER ENDPOINTS
# ==================== #

@api_bp.route('/customers', methods=['GET'])
def get_customers():
    """Get all customers with optional filters"""
    try:
        filters = {}

        # Parse filters from query parameters
        if 'status' in request.args:
            filters['status'] = request.args['status']
        if 'subscription_tier' in request.args:
            filters['subscription_tier'] = request.args['subscription_tier']
        if 'account_manager_id' in request.args:
            filters['account_manager_id'] = int(request.args['account_manager_id'])
        if 'search' in request.args:
            filters['search_text'] = request.args['search']

        customers = CustomerService.get_all_customers(filters)
        return success_response([customer.to_dict() for customer in customers])
    except Exception as e:
        return error_response(str(e), 500)


@api_bp.route('/customers', methods=['POST'])
def create_customer():
    """Create a new customer"""
    try:
        data = request.get_json()
        if not data:
            return error_response('No data provided')

        customer = CustomerService.create_customer(data)
        return success_response(customer.to_dict(), 'Customer created successfully', 201)
    except ValueError as e:
        return error_response(str(e), 400)
    except Exception as e:
        return error_response(str(e), 500)


@api_bp.route('/customers/<int:customer_id>', methods=['GET'])
def get_customer(customer_id):
    """Get customer by ID"""
    try:
        customer = CustomerService.get_customer_by_id(customer_id)
        if not customer:
            return error_response('Customer not found', 404)

        return success_response(customer.to_dict())
    except Exception as e:
        return error_response(str(e), 500)


@api_bp.route('/customers/<int:customer_id>', methods=['PUT'])
def update_customer(customer_id):
    """Update customer"""
    try:
        data = request.get_json()
        if not data:
            return error_response('No data provided')

        customer = CustomerService.update_customer(customer_id, data)
        return success_response(customer.to_dict(), 'Customer updated successfully')
    except ValueError as e:
        return error_response(str(e), 400)
    except Exception as e:
        return error_response(str(e), 500)


@api_bp.route('/customers/<int:customer_id>', methods=['DELETE'])
def delete_customer(customer_id):
    """Delete customer"""
    try:
        success = CustomerService.delete_customer(customer_id)
        if not success:
            return error_response('Customer not found', 404)

        return success_response(None, 'Customer deleted successfully')
    except Exception as e:
        return error_response(str(e), 500)


@api_bp.route('/customers/<int:customer_id>/assign-managers', methods=['POST'])
def assign_account_managers(customer_id):
    """Assign account managers to a customer"""
    try:
        data = request.get_json()
        if not data or 'account_manager_ids' not in data:
            return error_response('No account manager IDs provided')

        customer = CustomerService.assign_account_managers(customer_id, data['account_manager_ids'])
        return success_response(customer.to_dict(), 'Account managers assigned successfully')
    except ValueError as e:
        return error_response(str(e), 400)
    except Exception as e:
        return error_response(str(e), 500)


# ==================== #
# SEARCH ENDPOINTS
# ==================== #

@api_bp.route('/searches', methods=['GET'])
def get_searches():
    """Get all searches with optional filters"""
    try:
        filters = {}

        if 'customer_id' in request.args:
            filters['customer_id'] = int(request.args['customer_id'])
        if 'account_manager_id' in request.args:
            filters['account_manager_id'] = int(request.args['account_manager_id'])
        if 'active' in request.args:
            filters['is_active'] = request.args['active'].lower() == 'true'

        searches = SearchService.get_all_searches(filters)
        return success_response([search.to_dict() for search in searches])
    except Exception as e:
        return error_response(str(e), 500)


@api_bp.route('/searches', methods=['POST'])
def create_search():
    """Create a new search"""
    try:
        data = request.get_json()
        if not data:
            return error_response('No data provided')

        search = SearchService.create_search(data)
        return success_response(search.to_dict(), 'Search created successfully', 201)
    except ValueError as e:
        return error_response(str(e), 400)
    except Exception as e:
        return error_response(str(e), 500)


@api_bp.route('/searches/<int:search_id>', methods=['GET'])
def get_search(search_id):
    """Get search by ID"""
    try:
        search = SearchService.get_search_by_id(search_id)
        if not search:
            return error_response('Search not found', 404)

        return success_response(search.to_dict())
    except Exception as e:
        return error_response(str(e), 500)


@api_bp.route('/searches/<int:search_id>', methods=['PUT'])
def update_search(search_id):
    """Update search"""
    try:
        data = request.get_json()
        if not data:
            return error_response('No data provided')

        search = SearchService.update_search(search_id, data)
        return success_response(search.to_dict(), 'Search updated successfully')
    except ValueError as e:
        return error_response(str(e), 400)
    except Exception as e:
        return error_response(str(e), 500)


@api_bp.route('/searches/<int:search_id>', methods=['DELETE'])
def delete_search(search_id):
    """Delete search"""
    try:
        success = SearchService.delete_search(search_id)
        if not success:
            return error_response('Search not found', 404)

        return success_response(None, 'Search deleted successfully')
    except Exception as e:
        return error_response(str(e), 500)


@api_bp.route('/searches/<int:search_id>/update-results', methods=['POST'])
def update_search_results(search_id):
    """Update search results after running automation"""
    try:
        data = request.get_json()
        if not data or 'listings_found' not in data:
            return error_response('No listings count provided')

        search = SearchService.update_search_results(search_id, data['listings_found'])
        return success_response(search.to_dict(), 'Search results updated successfully')
    except ValueError as e:
        return error_response(str(e), 400)
    except Exception as e:
        return error_response(str(e), 500)


# ==================== #
# DASHBOARD & STATS ENDPOINTS
# ==================== #

@api_bp.route('/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    """Get dashboard statistics"""
    try:
        from sqlalchemy import func

        # Get counts
        total_account_managers = AccountManager.query.filter_by(is_active=True).count()
        total_customers = Customer.query.filter_by(status='ACTIVE').count()
        total_searches = Search.query.filter_by(is_active=True).count()

        # Get recent activity
        from datetime import datetime, timedelta, timezone
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)

        recent_customers = Customer.query.filter(
            Customer.created_at >= thirty_days_ago
        ).count()

        # Get platform distribution from customers
        platforms_data = {}
        customers_with_platforms = Customer.query.filter(Customer.platforms.isnot(None)).all()

        for customer in customers_with_platforms:
            for platform in customer.platforms or []:
                platforms_data[platform] = platforms_data.get(platform, 0) + 1

        stats = {
            'totals': {
                'account_managers': total_account_managers,
                'customers': total_customers,
                'searches': total_searches,
                'recent_customers': recent_customers
            },
            'platforms': platforms_data
        }

        return success_response(stats)
    except Exception as e:
        return error_response(str(e), 500)


# ==================== #
# HEALTH CHECK
# ==================== #

@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        db.session.execute('SELECT 1')
        return success_response({'status': 'healthy', 'database': 'connected'})
    except Exception as e:
        return error_response({'status': 'unhealthy', 'error': str(e)}, 500)


# ==================== #
# REACT NATIVE ENDPOINTS
# ==================== #

@api_bp.route('/mobile/dashboard/stats', methods=['GET'])
def get_mobile_dashboard_stats():
    """Get mobile dashboard statistics"""
    try:
        from sqlalchemy import func
        from datetime import datetime, timedelta, timezone

        # Mock data for MVP - replace with real queries later
        stats = {
            'mailings_sent': 2847,
            'active_listings': 156,
            'positive_contacts': 34,
            'response_rate': 1.2,
            'trends': {
                'mailings': '+12%',
                'contacts': '+8%'
            }
        }

        return success_response(stats)
    except Exception as e:
        return error_response(str(e), 500)


@api_bp.route('/mobile/platforms/status', methods=['GET'])
def get_mobile_platforms_status():
    """Get platform status for mobile"""
    try:
        platforms = [
            {
                'id': 1,
                'name': 'Kleinanzeigen',
                'display_name': 'Kleinanzeigen',
                'last_scanned': 'vor 12 Min.',
                'active_listings': 67,
                'is_live': True,
                'icon': 'kleinanzeigen'
            },
            {
                'id': 2,
                'name': 'ImmoScout24',
                'display_name': 'ImmoScout24',
                'last_scanned': 'vor 8 Min.',
                'active_listings': 52,
                'is_live': True,
                'icon': 'immoscout24'
            },
            {
                'id': 3,
                'name': 'Immowelt',
                'display_name': 'Immowelt',
                'last_scanned': 'vor 15 Min.',
                'active_listings': 37,
                'is_live': True,
                'icon': 'immowelt'
            }
        ]

        return success_response(platforms)
    except Exception as e:
        return error_response(str(e), 500)


@api_bp.route('/mobile/listings', methods=['GET'])
def get_mobile_listings():
    """Get listings for mobile app"""
    try:
        # Query parameters for filtering
        platform = request.args.get('platform')
        status = request.args.get('status')
        search = request.args.get('search')

        # Mock data - replace with database query
        listings = [
            {
                'id': 1,
                'title': 'MFH Charlottenburg',
                'platform': 'immowelt',
                'platform_display': 'Immowelt',
                'location': 'Charlottenburg',
                'rooms': 2,
                'living_area': 68,
                'year': 1980,
                'price': 488000.00,
                'price_per_sqm': 7176.47,
                'status': 'new',  # new, contacted, responded
                'contacted_at': None,
                'responded_at': None,
                'created_at': '2024-01-20T10:30:00Z'
            },
            {
                'id': 2,
                'title': 'MFH Charlottenburg',
                'platform': 'immoscout24',
                'platform_display': 'ImmoScout24',
                'location': 'Charlottenburg',
                'rooms': 3,
                'living_area': 69,
                'year': 1900,
                'price': 448500.00,
                'price_per_sqm': 6500.00,
                'status': 'new',
                'contacted_at': None,
                'responded_at': None,
                'created_at': '2024-01-20T09:15:00Z'
            },
            {
                'id': 3,
                'title': 'Wohnung Moabit',
                'platform': 'kleinanzeigen',
                'platform_display': 'Kleinanzeigen',
                'location': 'Moabit',
                'rooms': 2,
                'living_area': 28,
                'year': 1997,
                'price': 255560.00,
                'price_per_sqm': 9127.14,
                'status': 'contacted',
                'contacted_at': '2024-01-19T14:20:00Z',
                'responded_at': None,
                'created_at': '2024-01-19T08:45:00Z'
            }
        ]

        # Apply filters (in real app, these would be database filters)
        filtered_listings = listings

        if platform:
            filtered_listings = [l for l in filtered_listings if l['platform'] == platform]

        if status:
            filtered_listings = [l for l in filtered_listings if l['status'] == status]

        if search:
            search_lower = search.lower()
            filtered_listings = [
                l for l in filtered_listings
                if search_lower in l['title'].lower() or
                   search_lower in l['location'].lower()
            ]

        return success_response(filtered_listings)
    except Exception as e:
        return error_response(str(e), 500)


@api_bp.route('/mobile/listings/<int:listing_id>', methods=['GET'])
def get_mobile_listing(listing_id):
    """Get single listing detail"""
    try:
        # Mock data - replace with database query
        listing = {
            'id': listing_id,
            'title': 'MFH Charlottenburg',
            'platform': 'immowelt',
            'platform_display': 'Immowelt',
            'location': 'Charlottenburg, Berlin',
            'address': 'Musterstraße 123, 10585 Berlin',
            'rooms': 2,
            'living_area': 68,
            'year': 1980,
            'price': 488000.00,
            'price_per_sqm': 7176.47,
            'description': 'Schönes Mehrfamilienhaus in bester Lage...',
            'status': 'new',
            'contact_info': {
                'name': 'Max Mustermann',
                'phone': '+49 123 456789',
                'email': 'max@example.de'
            },
            'mailing_history': [
                {
                    'id': 1,
                    'type': 'initial',
                    'sent_at': '2024-01-20T10:30:00Z',
                    'content': 'Sehr geehrter Herr Mustermann,...',
                    'response': None
                }
            ],
            'created_at': '2024-01-20T10:30:00Z',
            'updated_at': '2024-01-20T10:30:00Z'
        }

        return success_response(listing)
    except Exception as e:
        return error_response(str(e), 500)


@api_bp.route('/mobile/listings/<int:listing_id>/contact', methods=['POST'])
def contact_listing(listing_id):
    """Send contact message for a listing"""
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return error_response('No message provided')

        # In production: Save to database and send actual email
        response = {
            'success': True,
            'message_id': 123,
            'sent_at': datetime.now(timezone.utc).isoformat(),
            'status': 'sent'
        }

        return success_response(response, 'Nachricht erfolgreich gesendet')
    except Exception as e:
        return error_response(str(e), 500)


@api_bp.route('/mobile/user/profile', methods=['GET'])
def get_user_profile():
    """Get user profile for mobile"""
    try:
        # Mock data - replace with actual user query
        profile = {
            'id': 1,
            'first_name': 'Max',
            'last_name': 'Mustermann',
            'email': 'max@mustermann-immobilien.de',
            'phone': '+49 234 123456',
            'company': 'Mustermann Immobilien GmbH',
            'role': 'customer',
            'avatar_initials': 'MM',
            'settings': {
                'notifications': True,
                'email_alerts': True,
                'push_enabled': True
            }
        }

        return success_response(profile)
    except Exception as e:
        return error_response(str(e), 500)


@api_bp.route('/mobile/user/profile', methods=['PUT'])
def update_user_profile():
    """Update user profile"""
    try:
        data = request.get_json()
        if not data:
            return error_response('No data provided')

        # In production: Update user in database
        updated_profile = {
            'id': 1,
            'first_name': data.get('first_name', 'Max'),
            'last_name': data.get('last_name', 'Mustermann'),
            'email': data.get('email', 'max@mustermann-immobilien.de'),
            'phone': data.get('phone', '+49 234 123456'),
            'company': data.get('company', 'Mustermann Immobilien GmbH'),
            'role': 'customer',
            'avatar_initials': 'MM',
            'settings': data.get('settings', {})
        }

        return success_response(updated_profile, 'Profil erfolgreich aktualisiert')
    except Exception as e:
        return error_response(str(e), 500)


# ==================== #
# MOCK DATA ENDPOINTS (Temporaire)
# ==================== #

@api_bp.route('/mobile/mock/dashboard', methods=['GET'])
def get_mock_dashboard():
    """Mock dashboard data for React Native"""
    return success_response({
        'stats': {
            'mailings_sent': 2847,
            'active_listings': 156,
            'positive_contacts': 34,
            'response_rate': 1.2,
            'trends': {
                'mailings': '+12%',
                'contacts': '+8%'
            }
        },
        'platforms': [
            {
                'id': 1,
                'name': 'Kleinanzeigen',
                'display_name': 'Kleinanzeigen',
                'last_scanned': 'vor 12 Min.',
                'active_listings': 67,
                'is_live': True
            },
            {
                'id': 2,
                'name': 'ImmoScout24',
                'display_name': 'ImmoScout24',
                'last_scanned': 'vor 8 Min.',
                'active_listings': 52,
                'is_live': True
            },
            {
                'id': 3,
                'name': 'Immowelt',
                'display_name': 'Immowelt',
                'last_scanned': 'vor 15 Min.',
                'active_listings': 37,
                'is_live': True
            }
        ],
        'mailing_activity': [
            {'week': 'KW 48', 'count': 140},
            {'week': 'KW 49', 'count': 120},
            {'week': 'KW 50', 'count': 100},
            {'week': 'KW 51', 'count': 110},
            {'week': 'KW 52', 'count': 70},
            {'week': 'KW 01', 'count': 50},
            {'week': 'KW 02', 'count': 60}
        ],
        'appointments': [
            {
                'id': 1,
                'client_name': 'Meyer Immobilien',
                'property_type': 'MFH Dortmund',
                'date': 'Heute 14:30',
                'status': 'positive'
            },
            {
                'id': 2,
                'client_name': 'Schmidt & Koch',
                'property_type': 'Wohn- & Geschäftshaus',
                'date': 'Morgen 10:00',
                'status': 'positive'
            },
            {
                'id': 3,
                'client_name': 'Becker Holdings',
                'property_type': 'Wohnanlage Essen',
                'date': 'Mi, 11:00',
                'status': 'pending'
            }
        ]
    })