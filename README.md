# 🏠 Extra Immobilien - Cold Mailing Automation Platform

Automated cold mailing platform for German real estate agents. Integrates CSV imports from ImmoMetrica with Selenium automation to contact property sellers at scale.

---

## 📋 Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [API Documentation](#api-documentation)
- [Deployment](#deployment)
- [Contributing](#contributing)

---

## ✨ Features

### Core Functionality
- ✅ **Automated CSV Import** - Daily scheduled imports from ImmoMetrica
- ✅ **Multi-Platform Support** - ImmoScout24, Kleinanzeigen, and more
- ✅ **Intelligent Automation** - Selenium-based form filling
- ✅ **Campaign Management** - Run, track, and analyze campaigns
- ✅ **Follow-up System** - Automatic follow-ups after 3 days
- ✅ **Real-time Dashboard** - Track response rates and conversions
- ✅ **Asynchronous Processing** - Celery task queue for scalability

### Technical Features
- ✅ RESTful API with Flask
- ✅ SQLAlchemy ORM for database management
- ✅ Celery + Redis for background tasks
- ✅ Selenium WebDriver for automation
- ✅ Comprehensive error handling & logging
- ✅ Environment-based configuration

---

## 🛠️ Tech Stack

| Category | Technology |
|----------|-----------|
| **Backend** | Flask 2.3.3, Python 3.8+ |
| **Database** | MySQL with SQLAlchemy ORM |
| **Task Queue** | Celery 5.3.4 + Redis 5.0.1 |
| **Automation** | Selenium 4.15.2 + ChromeDriver |
| **Data Processing** | Pandas 2.1.3 |
| **Frontend** | React Native (mobile app) |
| **Deployment** | Gunicorn + Nginx + Supervisor |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- MySQL 5.7+
- Redis 5.0+
- Chrome Browser + ChromeDriver

### 1. Clone & Install

```bash
# Clone repository
git clone https://github.com/your-org/extra-immobilien.git
cd extra-immobilien

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy .env template
cp .env.example .env

# Edit .env with your settings
nano .env
```

Required settings:
```env
DATABASE_URI=mysql+pymysql://root:password@localhost/extra_immobilien
CELERY_BROKER_URL=redis://localhost:6379/0
CSV_IMPORT_DIR=/path/to/csv/files
```

### 3. Initialize Database

```bash
# Create tables and add test data
python scripts/init_database.py

# Verify database
python scripts/check_database.py
```

### 4. Start Services

**Terminal 1 - Flask API:**
```bash
python run.py
```

**Terminal 2 - Celery Worker:**
```bash
celery -A celery_worker.celery worker --loglevel=info --pool=solo
```

**Terminal 3 - Celery Beat (Optional):**
```bash
celery -A celery_worker.celery beat --loglevel=info
```

### 5. Test the System

```bash
# Health check
curl http://localhost:5000/health

# Run test campaign
curl -X POST http://localhost:5000/api/v1/automation/run-campaign \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": 1,
    "search_id": 1,
    "csv_path": "/path/to/offers.csv",
    "limit": 3
  }'
```

---

## 📁 Project Structure

```
PythonProject/
├── app/                      # Main application package
│   ├── __init__.py          # Flask app factory
│   ├── models.py            # Database models
│   ├── database.py          # Database setup
│   ├── services.py          # Business logic
│   ├── api.py               # Original REST API
│   ├── automation_api.py    # ✨ Automation endpoints
│   ├── automation_service.py # ✨ Selenium logic
│   ├── tasks.py             # ✨ Celery tasks
│   └── celery_config.py     # ✨ Celery config
│
├── scripts/                  # Utility scripts
│   ├── init_database.py     # DB initialization
│   └── check_database.py    # DB verification
│
├── logs/                     # Application logs
├── data/                     # CSV imports & backups
├── tests/                    # Unit tests
│
├── config.py                 # Configuration
├── run.py                    # Flask entry point
├── celery_worker.py          # Celery entry point
├── requirements.txt          # Dependencies
├── .env                      # Environment variables
│
├── INTEGRATION_GUIDE.md      # Complete setup guide
├── ARCHITECTURE.md           # System architecture
└── README.md                 # This file
```

---

## 📡 API Documentation

### Base URL
```
http://localhost:5000/api/v1
```

### Endpoints

#### Account Managers
- `GET /account-managers` - List all
- `POST /account-managers` - Create
- `GET /account-managers/<id>` - Get by ID
- `PUT /account-managers/<id>` - Update
- `DELETE /account-managers/<id>` - Delete

#### Customers
- `GET /customers` - List all
- `POST /customers` - Create
- `GET /customers/<id>` - Get by ID
- `PUT /customers/<id>` - Update
- `DELETE /customers/<id>` - Delete

#### Searches
- `GET /searches` - List all
- `POST /searches` - Create
- `GET /searches/<id>` - Get by ID
- `PUT /searches/<id>` - Update
- `DELETE /searches/<id>` - Delete

#### ✨ Automation (NEW)
- `POST /automation/run-campaign` - Start campaign
- `GET /automation/campaign-status/<task_id>` - Check status
- `GET /automation/listings` - List listings
- `GET /automation/mailings` - Mailing history
- `GET /automation/stats` - Statistics
- `POST /automation/cleanup` - Cleanup old data

#### Dashboard
- `GET /dashboard/stats` - Get statistics

---

## 🎯 Usage Examples

### Start a Campaign

```bash
curl -X POST http://localhost:5000/api/v1/automation/run-campaign \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": 1,
    "search_id": 1,
    "csv_path": "/home/rania/Downloads/offers.csv",
    "limit": 100
  }'
```

### Check Campaign Status

```bash
curl http://localhost:5000/api/v1/automation/campaign-status/abc-123-def-456
```

### Get Statistics

```bash
curl "http://localhost:5000/api/v1/automation/stats?customer_id=1&days=7"
```

---

## 🚢 Deployment

### Production Setup

1. **Environment Variables**
   ```bash
   FLASK_ENV=production
   SECRET_KEY=<strong-random-key>
   SELENIUM_HEADLESS=True
   ```

2. **Supervisor Configuration**
   See `INTEGRATION_GUIDE.md` for complete supervisor config

3. **Nginx Reverse Proxy**
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       location / {
           proxy_pass http://127.0.0.1:5000;
           proxy_set_header Host $host;
       }
   }
   ```

4. **Start Services**
   ```bash
   sudo supervisorctl start extra_flask extra_celery_worker extra_celery_beat
   ```

---

## 📊 Monitoring

### View Celery Tasks
```bash
celery -A celery_worker.celery inspect active
celery -A celery_worker.celery inspect stats
```

### View Logs
```bash
tail -f logs/app.log
tail -f logs/celery.log
```

### Database Status
```bash
python scripts/check_database.py
```

---

## 🐛 Troubleshooting

### Redis Connection Error
```bash
# Check Redis status
redis-cli ping

# Start Redis
sudo systemctl start redis
```

### Database Connection Error
```bash
# Check MySQL status
sudo systemctl status mysql

# Test connection
mysql -u root -p
```

### Selenium ChromeDriver Error
```bash
# Update ChromeDriver
pip install --upgrade webdriver-manager
```

See `INTEGRATION_GUIDE.md` for more troubleshooting.

---

## 📚 Documentation

- **[INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md)** - Complete setup & integration guide
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture diagrams
- **[COMPLETE_BACKEND_STRUCTURE.md](COMPLETE_BACKEND_STRUCTURE.md)** - Detailed file structure

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/

# Run specific test
pytest tests/test_automation.py

# With coverage
pytest --cov=app tests/
```

---

## 🤝 Contributing

### Development Setup
```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run in debug mode
export FLASK_ENV=development
python run.py
```

### Code Style
- Follow PEP 8
- Use type hints
- Write docstrings
- Add unit tests

---

## 📄 License

This project is proprietary and confidential.

---

## 👥 Team

- **Backend & Database**: Your Name
- **CSV Processing & Automation**: Rania
- **Frontend**: Mobile Team

---

## 📞 Support

For issues or questions:
- Email: support@extra-immobilien.de
- Slack: #extra-immobilien-dev

---

## 🎯 Roadmap

- [ ] JWT Authentication
- [ ] Rate limiting
- [ ] Webhook integrations
- [ ] Advanced analytics
- [ ] Multi-language support
- [ ] Email template editor
- [ ] Webhook for responses

---

**Last Updated**: 2025-01-29
**Version**: 1.0.0