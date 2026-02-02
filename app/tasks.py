"""
Celery Tasks - Background jobs for automation campaigns
"""

from celery import shared_task
from datetime import datetime, timedelta
from sqlalchemy import and_
import os

from app.database import db
from app.models import Customer, Search, Listing, Mailing
from app.automation_service import AutomationService


@shared_task(bind=True, name='app.tasks.run_automation_campaign')
def run_automation_campaign(self, customer_id: int, search_id: int, csv_path: str, limit: int = None):
    """
    Main task to run an automation campaign

    Args:
        customer_id: Customer ID
        search_id: Search configuration ID
        csv_path: Path to CSV file with listings
        limit: Optional limit for number of listings to process

    Returns:
        dict: Campaign statistics
        :param self:
    """
    automation = None

    try:
        print(f" Starting campaign for customer {customer_id}, search {search_id}")

        # Update task state
        self.update_state(
            state='PROCESSING',
            meta={'status': 'Initializing automation...', 'progress': 0}
        )

        # Initialize automation service
        automation = AutomationService(customer_id=customer_id, search_id=search_id)
        automation.setup_driver()

        # Read CSV and save listings to database
        self.update_state(
            state='PROCESSING',
            meta={'status': 'Reading CSV file...', 'progress': 10}
        )

        column_urls = automation.read_csv_and_save_listings(csv_path)

        # Get ImmoScout URLs
        immoscout_urls = column_urls.get('Link ImmoScout', [])

        if not immoscout_urls:
            return {
                'status': 'error',
                'message': 'No ImmoScout URLs found in CSV'
            }

        # Process campaign
        self.update_state(
            state='PROCESSING',
            meta={
                'status': f'Processing {len(immoscout_urls)} listings...',
                'progress': 20
            }
        )

        automation.process_immoscout_campaign(immoscout_urls, limit=limit)

        # Get final stats
        stats = automation.get_stats()

        # Update search last run time
        search = db.session.query(Search).get(search_id)
        if search:
            search.last_run_at = datetime.utcnow()
            search.next_run_at = datetime.utcnow() + timedelta(hours=search.frequency_hours or 24)
            db.session.commit()

        return {
            'status': 'completed',
            'stats': stats,
            'timestamp': datetime.utcnow().isoformat()
        }

    except Exception as e:
        print(f" Campaign failed: {e}")

        return {
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }

    finally:
        if automation:
            automation.cleanup()


@shared_task(name='app.tasks.import_daily_csv')
def import_daily_csv():
    """
    Import daily CSV files from ImmoMetrica
    Scheduled to run every day at 6 AM
    """
    try:
        print(" Starting daily CSV import...")

        # Get CSV directory from config
        csv_dir = os.getenv('CSV_IMPORT_DIR', '/home/rania/Downloads')

        # Find today's CSV file (assuming format: offers_YYYY-MM-DD.csv)
        today = datetime.utcnow().strftime('%Y-%m-%d')
        csv_filename = f"offers_{today}.csv"
        csv_path = os.path.join(csv_dir, csv_filename)

        if not os.path.exists(csv_path):
            # Try default filename
            csv_path = os.path.join(csv_dir, 'offers.csv')

        if not os.path.exists(csv_path):
            print(f" CSV file not found: {csv_path}")
            return {'status': 'error', 'message': 'CSV file not found'}

        # Get all active customers
        active_customers = db.session.query(Customer).filter_by(
            status='active'
        ).all()

        imported_count = 0

        for customer in active_customers:
            # Get active searches for this customer
            active_searches = db.session.query(Search).filter(
                and_(
                    Search.customer_id == customer.id,
                    Search.is_active == True
                )
            ).all()

            for search in active_searches:
                # Trigger campaign for this search
                run_automation_campaign.delay(
                    customer_id=customer.id,
                    search_id=search.id,
                    csv_path=csv_path,
                    limit=100  # Process 100 listings per customer per day
                )
                imported_count += 1

        print(f" Triggered {imported_count} campaigns")

        return {
            'status': 'success',
            'campaigns_triggered': imported_count,
            'timestamp': datetime.utcnow().isoformat()
        }

    except Exception as e:
        print(f" Daily import failed: {e}")
        return {
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }


@shared_task(name='app.tasks.check_pending_campaigns')
def check_pending_campaigns():
    """
    Check for pending campaigns that need to run
    Scheduled every 30 minutes
    """
    try:
        print(" Checking for pending campaigns...")

        now = datetime.utcnow()

        # Find searches that are due to run
        pending_searches = db.session.query(Search).filter(
            and_(
                Search.is_active == True,
                Search.next_run_at <= now
            )
        ).all()

        triggered_count = 0

        for search in pending_searches:
            # Get latest CSV
            csv_path = os.getenv('CSV_IMPORT_DIR', '/home/rania/Downloads') + '/offers.csv'

            if not os.path.exists(csv_path):
                continue

            # Trigger campaign
            run_automation_campaign.delay(
                customer_id=search.customer_id,
                search_id=search.id,
                csv_path=csv_path,
                limit=100
            )

            triggered_count += 1

        print(f" Triggered {triggered_count} pending campaigns")

        return {
            'status': 'success',
            'campaigns_triggered': triggered_count,
            'timestamp': datetime.utcnow().isoformat()
        }

    except Exception as e:
        print(f" Check pending campaigns failed: {e}")
        return {
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }


@shared_task(name='app.tasks.send_followup_emails')
def send_followup_emails():
    """
    Send follow-up emails to listings that haven't responded
    Runs daily at 10 AM
    """
    try:
        print(" Sending follow-up emails...")

        # Find listings contacted 3 days ago without response
        three_days_ago = datetime.utcnow() - timedelta(days=3)

        listings_needing_followup = db.session.query(Listing).filter(
            and_(
                Listing.status == 'contacted',
                Listing.contacted_at <= three_days_ago,
                Listing.response_at.is_(None)
            )
        ).all()

        followup_count = 0

        for listing in listings_needing_followup:
            # Check if follow-up already sent
            existing_followup = db.session.query(Mailing).filter(
                and_(
                    Mailing.listing_id == listing.id,
                    Mailing.type == 'followup'
                )
            ).first()

            if existing_followup:
                continue

            # Create follow-up mailing record
            # In real implementation, you'd trigger actual email/message here
            mailing = Mailing(
                listing_id=listing.id,
                customer_id=listing.customer_id,
                type='followup',
                subject='Nochmals: Interesse an Ihrer Immobilie',
                content='Follow-up message content...',
                status='scheduled',  # Would be 'sent' after actual send
                sent_at=None
            )

            db.session.add(mailing)
            followup_count += 1

        db.session.commit()

        print(f" Scheduled {followup_count} follow-up emails")

        return {
            'status': 'success',
            'followups_scheduled': followup_count,
            'timestamp': datetime.utcnow().isoformat()
        }

    except Exception as e:
        db.session.rollback()
        print(f" Send follow-up emails failed: {e}")
        return {
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }


@shared_task(name='app.tasks.cleanup_old_listings')
def cleanup_old_listings(days: int = 30):
    """
    Clean up old listings from database

    Args:
        days: Delete listings older than this many days
    """
    try:
        print(f" Cleaning up listings older than {days} days...")

        cutoff_date = datetime.utcnow() - timedelta(days=days)

        deleted_count = db.session.query(Listing).filter(
            and_(
                Listing.created_at < cutoff_date,
                Listing.status.in_(['failed', 'rejected'])
            )
        ).delete()

        db.session.commit()

        print(f" Deleted {deleted_count} old listings")

        return {
            'status': 'success',
            'deleted_count': deleted_count,
            'timestamp': datetime.utcnow().isoformat()
        }

    except Exception as e:
        db.session.rollback()
        print(f" Cleanup failed: {e}")
        return {
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }