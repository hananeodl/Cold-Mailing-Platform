"""
Flask Application Factory with Celery Integration
"""

from flask import Flask
from flask_cors import CORS

from config import get_config
from app.database import db, init_db
from app.celery_config import make_celery

# Global celery instance
celery = None


def create_app(config_name='development'):
    """
    Application factory pattern
    Creates and configures Flask app with Celery
    """
    app = Flask(__name__)

    # Load configuration
    config_class = get_config()

    # Load all config attributes into app.config
    for key in dir(config_class):
        if key.isupper():
            app.config[key] = getattr(config_class, key)

    # Initialize extensions
    db.init_app(app)
    CORS(app, origins=app.config.get('CORS_ORIGINS', ['*']))

    # Initialize Celery
    global celery
    celery = make_celery(app)

    # Register blueprints
    from app.api import api_bp
    from app.automation_api import automation_bp

    app.register_blueprint(api_bp)
    app.register_blueprint(automation_bp)

    # Create database tables
    with app.app_context():
        init_db()

    # Health check endpoint
    @app.route('/health')
    def health_check():
        return {
            'status': 'healthy',
            'version': app.config['API_VERSION']
        }

    return app


def get_celery():
    """Get celery instance"""
    return celery