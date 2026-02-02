"""
Automation API Endpoints
New endpoints to control and monitor automation campaigns
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
from celery.result import AsyncResult
import os

from app.database import db
from app.models import Customer, Search, Listing, Mailing
from app.tasks import run_automation_campaign, cleanup_old_listings
from app.celery_config import make_celery

automation_bp = Blueprint('automation', __name__, url_prefix='/api/v1/automation')


@automation_bp.route('/run-campaign', methods=['POST'])
def run_campaign():
    """
    POST /api/v1/automation/run-campaign

    Start a new automation campaign

    Request body:
    {
        "customer_id": 1,
        "search_id": 1,
        "csv_path": "/path/to/offers.csv",
        "limit": 100  // optional
    }

    Returns:
    {
        "status": "success",
        "task_id": "abc-123-def-456",
        "message": "Campaign started"
    }
    """
    try:
        data = request.get_json()

        # Validate required fields
        customer_id = data.get('customer_id')
        search_id = data.get('search_id')
        csv_path = data.get('csv_path')
        limit = data.get('limit')

        if not customer_id or not search_id:
            return jsonify({
                'status': 'error',
                'message': 'customer_id and search_id are required'
            }), 400

        # Use default CSV path if not provided
        if not csv_path:
            csv_path = os.getenv('CSV_IMPORT_DIR', '/home/rania/Downloads') + '/offers.csv'

        # Check if customer exists
        customer = db.session.query(Customer).get(customer_id)
        if not customer:
            return jsonify({
                'status': 'error',
                'message': 'Customer not found'
            }), 404

        # Check if search exists
        search = db.session.query(Search).get(search_id)
        if not search or search.customer_id != customer_id:
            return jsonify({
                'status': 'error',
                'message': 'Search not found or does not belong to customer'
            }), 404

        # Check if CSV file exists
        if not os.path.exists(csv_path):
            return jsonify({
                'status': 'error',
                'message': f'CSV file not found: {csv_path}'
            }), 404

        # Trigger Celery task
        task = run_automation_campaign.delay(
            customer_id=customer_id,
            search_id=search_id,
            csv_path=csv_path,
            limit=limit
        )

        return jsonify({
            'status': 'success',
            'task_id': task.id,
            'message': 'Campaign started successfully',
            'timestamp': datetime.utcnow().isoformat()
        }), 202

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@automation_bp.route('/campaign-status/<task_id>', methods=['GET'])
def get_campaign_status(task_id):
    """
    GET /api/v1/automation/campaign-status/<task_id>

    Get status of a running campaign

    Returns:
    {
        "status": "PROCESSING",
        "progress": 45,
        "message": "Processing listing 45/100",
        "result": null
    }
    """
    try:
        task = AsyncResult(task_id)

        if task.state == 'PENDING':
            response = {
                'status': 'pending',
                'message': 'Campaign is queued',
                'progress': 0
            }
        elif task.state == 'PROCESSING':
            response = {
                'status': 'processing',
                'message': task.info.get('status', ''),
                'progress': task.info.get('progress', 0)
            }
        elif task.state == 'SUCCESS':
            response = {
                'status': 'completed',
                'result': task.result,
                'progress': 100
            }
        elif task.state == 'FAILURE':
            response = {
                'status': 'failed',
                'message': str(task.info),
                'progress': 0
            }
        else:
            response = {
                'status': task.state.lower(),
                'message': str(task.info) if task.info else '',
                'progress': 0
            }

        return jsonify(response), 200

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@automation_bp.route('/listings', methods=['GET'])
def get_listings():
    """
    GET /api/v1/automation/listings

    Get listings for a customer/search

    Query params:
    - customer_id: Filter by customer
    - search_id: Filter by search
    - status: Filter by status (pending, contacted, responded, failed)
    - limit: Number of results (default 50)
    - offset: Pagination offset (default 0)

    Returns:
    {
        "status": "success",
        "listings": [...],
        "total": 150,
        "limit": 50,
        "offset": 0
    }
    """
    try:
        customer_id = request.args.get('customer_id', type=int)
        search_id = request.args.get('search_id', type=int)
        status = request.args.get('status')
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)

        # Build query
        query = db.session.query(Listing)

        if customer_id:
            query = query.filter(Listing.customer_id == customer_id)

        if search_id:
            query = query.filter(Listing.search_id == search_id)

        if status:
            query = query.filter(Listing.status == status)

        # Get total count
        total = query.count()

        # Apply pagination
        listings = query.order_by(Listing.created_at.desc()).limit(limit).offset(offset).all()

        # Format response
        listings_data = []
        for listing in listings:
            listings_data.append({
                'id': listing.id,
                'external_id': listing.external_id,
                'platform': listing.platform,
                'title': listing.title,
                'status': listing.status,
                'contacted_at': listing.contacted_at.isoformat() if listing.contacted_at else None,
                'response_at': listing.response_at.isoformat() if listing.response_at else None,
                'created_at': listing.created_at.isoformat()
            })

        return jsonify({
            'status': 'success',
            'listings': listings_data,
            'total': total,
            'limit': limit,
            'offset': offset
        }), 200

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@automation_bp.route('/mailings', methods=['GET'])
def get_mailings():
    """
    GET /api/v1/automation/mailings

    Get mailing history

    Query params:
    - customer_id: Filter by customer
    - listing_id: Filter by listing
    - type: Filter by type (initial, followup)
    - status: Filter by status (sent, failed, scheduled)
    - limit: Number of results (default 50)
    - offset: Pagination offset (default 0)

    Returns:
    {
        "status": "success",
        "mailings": [...],
        "total": 200
    }
    """
    try:
        customer_id = request.args.get('customer_id', type=int)
        listing_id = request.args.get('listing_id', type=int)
        mailing_type = request.args.get('type')
        status = request.args.get('status')
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)

        # Build query
        query = db.session.query(Mailing)

        if customer_id:
            query = query.filter(Mailing.customer_id == customer_id)

        if listing_id:
            query = query.filter(Mailing.listing_id == listing_id)

        if mailing_type:
            query = query.filter(Mailing.type == mailing_type)

        if status:
            query = query.filter(Mailing.status == status)

        # Get total count
        total = query.count()

        # Apply pagination
        mailings = query.order_by(Mailing.created_at.desc()).limit(limit).offset(offset).all()

        # Format response
        mailings_data = []
        for mailing in mailings:
            mailings_data.append({
                'id': mailing.id,
                'listing_id': mailing.listing_id,
                'type': mailing.type,
                'subject': mailing.subject,
                'status': mailing.status,
                'sent_at': mailing.sent_at.isoformat() if mailing.sent_at else None,
                'response_at': mailing.response_at.isoformat() if mailing.response_at else None,
                'created_at': mailing.created_at.isoformat()
            })

        return jsonify({
            'status': 'success',
            'mailings': mailings_data,
            'total': total,
            'limit': limit,
            'offset': offset
        }), 200

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@automation_bp.route('/stats', methods=['GET'])
def get_automation_stats():
    """
    GET /api/v1/automation/stats

    Get automation statistics for a customer

    Query params:
    - customer_id: Customer ID (required)
    - days: Number of days to look back (default 7)

    Returns:
    {
        "status": "success",
        "stats": {
            "total_listings": 500,
            "contacted": 450,
            "responded": 45,
            "appointments": 12,
            "response_rate": 10.0,
            "conversion_rate": 2.7
        }
    }
    """
    try:
        customer_id = request.args.get('customer_id', type=int)
        days = request.args.get('days', 7, type=int)

        if not customer_id:
            return jsonify({
                'status': 'error',
                'message': 'customer_id is required'
            }), 400

        # Calculate date range
        from datetime import timedelta
        start_date = datetime.utcnow() - timedelta(days=days)

        # Get listings stats
        total_listings = db.session.query(Listing).filter(
            Listing.customer_id == customer_id,
            Listing.created_at >= start_date
        ).count()

        contacted = db.session.query(Listing).filter(
            Listing.customer_id == customer_id,
            Listing.status.in_(['contacted', 'responded']),
            Listing.contacted_at >= start_date
        ).count()

        responded = db.session.query(Listing).filter(
            Listing.customer_id == customer_id,
            Listing.status == 'responded',
            Listing.response_at >= start_date
        ).count()

        # Get appointments
        from app.models import Appointment
        appointments = db.session.query(Appointment).filter(
            Appointment.customer_id == customer_id,
            Appointment.created_at >= start_date
        ).count()

        # Calculate rates
        response_rate = (responded / contacted * 100) if contacted > 0 else 0
        conversion_rate = (appointments / contacted * 100) if contacted > 0 else 0

        return jsonify({
            'status': 'success',
            'stats': {
                'total_listings': total_listings,
                'contacted': contacted,
                'responded': responded,
                'appointments': appointments,
                'response_rate': round(response_rate, 2),
                'conversion_rate': round(conversion_rate, 2),
                'period_days': days
            }
        }), 200

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@automation_bp.route('/cleanup', methods=['POST'])
def cleanup_listings():
    """
    POST /api/v1/automation/cleanup

    Trigger cleanup of old listings

    Request body:
    {
        "days": 30  // Delete listings older than this
    }

    Returns:
    {
        "status": "success",
        "task_id": "xyz-789"
    }
    """
    try:
        data = request.get_json()
        days = data.get('days', 30)

        # Trigger cleanup task
        task = cleanup_old_listings.delay(days=days)

        return jsonify({
            'status': 'success',
            'task_id': task.id,
            'message': f'Cleanup task started for listings older than {days} days'
        }), 202

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500