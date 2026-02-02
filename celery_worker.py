"""
Celery Worker Entry Point
Run this script to start Celery workers for background tasks

Usage:
    # Start worker (simple)
    python celery_worker.py

    # Start worker (command line - recommended)
    celery -A celery_worker.celery worker --loglevel=info --concurrency=2 --pool=solo

    # Start Beat scheduler for periodic tasks
    celery -A celery_worker.celery beat --loglevel=info

    # Start both worker and beat (development only)
    celery -A celery_worker.celery worker --beat --loglevel=info --pool=solo

    # Monitor tasks
    celery -A celery_worker.celery inspect active
    celery -A celery_worker.celery inspect stats
    celery -A celery_worker.celery inspect registered

Platform-specific:
    Linux/Mac: Use --pool=prefork for better performance
    Windows: Use --pool=solo (required)
"""

import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app, get_celery

# Create Flask app and get Celery instance
print("\n" + "=" * 60)
print("🚀 Starting Celery Worker")
print("=" * 60 + "\n")

app = create_app()
celery = get_celery()

print("✓ Flask app initialized")
print("✓ Celery configured")
print("\nRegistered tasks:")
for task_name in sorted(celery.tasks.keys()):
    if not task_name.startswith('celery.'):
        print(f"  - {task_name}")

print("\n" + "=" * 60)
print("Worker starting... (Press Ctrl+C to stop)")
print("=" * 60 + "\n")

if __name__ == '__main__':
    # Determine pool type based on platform
    pool_type = 'solo' if sys.platform == 'win32' else 'prefork'

    # Run worker
    celery.worker_main([
        'worker',
        '--loglevel=info',
        '--concurrency=2',
        f'--pool={pool_type}'
    ])