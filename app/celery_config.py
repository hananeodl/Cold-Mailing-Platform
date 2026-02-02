"""
Celery Configuration for Asynchronous Task Processing
Handles background automation tasks, scheduled campaigns, etc.
"""

from celery import Celery
from celery.schedules import crontab
import os


def make_celery(app):
    """Factory function to create Celery instance with Flask app context"""
    celery = Celery(
        app.import_name,
        backend=app.config['CELERY_RESULT_BACKEND'],
        broker=app.config['CELERY_BROKER_URL']
    )

    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery


# Celery Beat Schedule for Periodic Tasks
celery_beat_schedule = {
    # Run daily CSV import at 6 AM
    'daily-csv-import': {
        'task': 'app.tasks.import_daily_csv',
        'schedule': crontab(hour=6, minute=0),
        'args': ()
    },

    # Check for pending campaigns every 30 minutes
    'check-pending-campaigns': {
        'task': 'app.tasks.check_pending_campaigns',
        'schedule': crontab(minute='*/30'),
        'args': ()
    },

    # Send follow-up emails (3 days after initial contact)
    'send-followup-emails': {
        'task': 'app.tasks.send_followup_emails',
        'schedule': crontab(hour=10, minute=0),
        'args': ()
    },
}

# Celery Configuration Settings
CELERY_CONFIG = {
    # Broker settings (Redis recommended for production)
    'CELERY_BROKER_URL': os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    'CELERY_RESULT_BACKEND': os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0'),

    # Task settings
    'CELERY_TASK_SERIALIZER': 'json',
    'CELERY_RESULT_SERIALIZER': 'json',
    'CELERY_ACCEPT_CONTENT': ['json'],
    'CELERY_TIMEZONE': 'Europe/Berlin',
    'CELERY_ENABLE_UTC': True,

    # Task execution settings
    'CELERY_TASK_TRACK_STARTED': True,
    'CELERY_TASK_TIME_LIMIT': 3600,  # 1 hour max per task
    'CELERY_TASK_SOFT_TIME_LIMIT': 3300,  # 55 minutes soft limit

    # Result backend settings
    'CELERY_RESULT_EXPIRES': 86400,  # Results expire after 24 hours

    # Beat schedule
    'CELERYBEAT_SCHEDULE': celery_beat_schedule,

    # Worker settings
    'CELERYD_CONCURRENCY': 2,  # Number of worker processes
    'CELERYD_PREFETCH_MULTIPLIER': 1,  # Tasks per worker
}