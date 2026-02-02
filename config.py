"""
Configuration Settings for Flask Application
Includes database, API, and Celery configurations
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration"""

    # Flask Settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('DEBUG', 'False') == 'True'

    # Database configuration for PyMySQL
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_PORT = os.environ.get('DB_PORT', '3306')
    DB_NAME = os.environ.get('DB_NAME', 'extra_immobilien')
    DB_USER = os.environ.get('DB_USER', 'root')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', '')

    # PyMySQL connection string
    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'

    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 280,
        'pool_pre_ping': True,
    }
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = DEBUG

    # API Settings
    API_VERSION = 'v1'
    API_PREFIX = '/api/v1'

    # Pagination
    DEFAULT_PAGE_SIZE = 50
    MAX_PAGE_SIZE = 100

    # Celery Settings
    CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
    CELERY_TASK_SERIALIZER = 'json'
    CELERY_RESULT_SERIALIZER = 'json'
    CELERY_ACCEPT_CONTENT = ['json']
    CELERY_TIMEZONE = 'Europe/Berlin'
    CELERY_ENABLE_UTC = True
    CELERY_TASK_TRACK_STARTED = True
    CELERY_TASK_TIME_LIMIT = 3600  # 1 hour
    CELERY_TASK_SOFT_TIME_LIMIT = 3300  # 55 minutes

    # Automation Settings
    CSV_IMPORT_DIR = os.getenv('CSV_IMPORT_DIR', 'C:/Users/Downloads')  # Windows-friendly default
    DEFAULT_CAMPAIGN_LIMIT = 100  # Max listings per campaign run
    SELENIUM_HEADLESS = os.getenv('SELENIUM_HEADLESS', 'False') == 'True'

    # Email/Message Settings (for templates)
    DEFAULT_MESSAGE_TEMPLATE = """Guten Tag,

Wir sind ein Immobilien Makler und Investor aus der Region und sind sehr an Ihrer Immobilie interessiert. Wir würden gerne mehr über diese erfahren. Sie passt zu mehreren unserer hinterlegten Suchprofile - welche wir bei Kunden aufgenommen haben, bei denen ein vorheriger Ankauf nicht geklappt hat. Daher würde ich mich sehr freuen, wenn Sie mir Ihre Telefonnummer und E-Mail zur Verfügung stellen könnten, damit wir uns kurz zu Ihrem Objekt austauschen können.

Mit freundlichen Grüßen

{company_name}
{address}
T: {phone}
{email}"""

    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/app.log')

    # CORS Settings
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False

    def __init__(self):
        """Validate production settings"""
        super().__init__()

        # Validate SECRET_KEY
        if not os.getenv('SECRET_KEY'):
            raise ValueError("SECRET_KEY must be set in production environment")

        # Validate DATABASE_URI
        if not os.getenv('DATABASE_URI'):
            raise ValueError("DATABASE_URI must be set in production environment")

    # Override with environment variables (required in production)
    SECRET_KEY = os.getenv('SECRET_KEY', None)
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URI', None)

    # Selenium should run headless in production
    SELENIUM_HEADLESS = True


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True

    # Use test database
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:password@localhost/extra_immobilien_test'

    # Use in-memory broker for testing
    CELERY_BROKER_URL = 'memory://'
    CELERY_RESULT_BACKEND = 'cache+memory://'


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config():
    """Get configuration based on environment"""
    env = os.getenv('FLASK_ENV', 'development')
    return config.get(env, config['default'])