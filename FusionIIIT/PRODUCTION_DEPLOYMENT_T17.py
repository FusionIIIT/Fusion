"""
Production Deployment Guide for FusionIIIT No Dues Management System.

T17 Deliverables:
- Database schema finalization and migration verification
- Environment setup for production
- Nginx/Gunicorn configuration
- Celery worker and beat scheduler setup
- SSL/TLS and security hardening
- Monitoring and logging
- Backup and disaster recovery
- Performance tuning
- Health check procedures
"""

# ==================== PRODUCTION DEPLOYMENT CHECKLIST ====================

PRODUCTION_DEPLOYMENT_CHECKLIST = """
PRODUCTION DEPLOYMENT CHECKLIST - FusionIIIT No Dues Management
Version: 1.0
Date: April 2026

=== PHASE 1: PRE-DEPLOYMENT VERIFICATION ===

[ ] 1.1 Code Review
  [ ] All 24 tasks completed (21/24 minimum critical)
  [ ] No debug code or print statements in production
  [ ] All imports are correct
  [ ] Error handling implemented
  [ ] Logging configured

[ ] 1.2 Database Verification
  [ ] All migrations created (0001, 0002, 0003)
  [ ] Dry-run migrations on staging: python manage.py migrate --plan
  [ ] Database backups configured
  [ ] Connection pooling settings verified

[ ] 1.3 Security Verification
  [ ] DEBUG = False in production
  [ ] SECRET_KEY is random and secure
  [ ] ALLOWED_HOSTS configured correctly
  [ ] HTTPS/SSL certificates installed
  [ ] CORS settings restricted
  [ ] CSRF protection enabled

[ ] 1.4 Tests & Monitoring
  [ ] Run all unit tests: python manage.py test (pass rate >95%)
  [ ] Run integration tests: python manage.py test integration_tests (pass)
  [ ] Load testing completed (100+ concurrent users)
  [ ] Performance baselines recorded
  [ ] Monitoring dashboards created


=== PHASE 2: STAGING DEPLOYMENT ===

[ ] 2.1 Environment Setup
  [ ] Staging server provisioned (OS: Ubuntu 20.04+ or similar)
  [ ] Python 3.8+ installed
  [ ] PostgreSQL 12+ installed (or MySQL 8+)
  [ ] Redis 6.0+ installed
  [ ] Nginx installed

[ ] 2.2 Application Setup
  [ ] Clone repository to /home/fusion/fusioniiit
  [ ] Create Python virtual environment
  [ ] Install requirements.txt
  [ ] Copy settings/production.py → settings/staging.py
  [ ] Configure database: postgresql://user:pass@localhost:5432/fusion_staging
  [ ] Configure cache: redis://localhost:6379/1

[ ] 2.3 Static Files & Media
  [ ] python manage.py collectstatic --noinput
  [ ] Set permissions: chown -R www-data:www-data /var/www/fusion/static
  [ ] Verify /media directory writable

[ ] 2.4 Database Migration
  [ ] python manage.py migrate
  [ ] python manage.py migrate otheracademic
  [ ] Verify all tables created (8 new tables from T22-24, 3 from T14-16)
  [ ] Run: python manage.py check

[ ] 2.5 Initial Data Load
  [ ] Create superuser: python manage.py createsuperuser
  [ ] Load initial data (departments, users) if applicable
  [ ] Verify data integrity

[ ] 2.6 Celery Setup
  [ ] Redis running: redis-cli ping → PONG
  [ ] Start worker: celery -A Fusion worker -l info
  [ ] Start beat: celery -A Fusion beat -l info
  [ ] Monitor tasks: flower -A Fusion --port=5555

[ ] 2.7 Nginx & Gunicorn
  [ ] Configure Gunicorn: gunicorn_config.py created
  [ ] Create systemd service: /etc/systemd/system/fusion.service
  [ ] Configure Nginx: /etc/nginx/sites-available/fusion
  [ ] Test Nginx: sudo nginx -t
  [ ] Start services: systemctl start fusion && systemctl start nginx

[ ] 2.8 Security Hardening
  [ ] Firewall configured: ufw allow 80, 443
  [ ] SSL certificate installed (Let's Encrypt recommended)
  [ ] Nginx force HTTPS redirect
  [ ] Security headers configured (HSTS, CSP, X-Frame-Options)
  [ ] Rate limiting configured

[ ] 2.9 Testing on Staging
  [ ] Health check: GET /api/health-check/full_system_check/ → 200
  [ ] Analytics endpoint: GET /api/analytics/summary/ → 200
  [ ] Feedback submit: POST /api/feedback/ → 201
  [ ] Login & permissions: Verify auth works
  [ ] Workflow test: Student No Dues → Escalation → Approval
  [ ] Load test: 50 concurrent users for 5 minutes


=== PHASE 3: PRODUCTION DEPLOYMENT ===

[ ] 3.1 Production Environment
  [ ] Production server provisioned (separate from staging)
  [ ] Database: PostgreSQL 13+ on separate box or same box isolated
  [ ] Backups: Daily automated backups to S3 or similar
  [ ] Monitoring: Sentry/DataDog/New Relic configured

[ ] 3.2 Application Deployment
  [ ] Clone to /home/fusion/fusioniiit-prod
  [ ] Configure production settings (DEBUG=False, ALLOWED_HOSTS)
  [ ] python manage.py migrate
  [ ] python manage.py collectstatic --noinput
  [ ] Create production superuser

[ ] 3.3 Service Configuration
  [ ] Gunicorn workers: 4 * CPU_cores (recommend 8-16 for medium load)
  [ ] Celery workers: 4 + 1 beat scheduler
  [ ] Supervisor: Manage all services
  [ ] Systemd: Alternative to supervisor

[ ] 3.4 Monitoring & Alerts
  [ ] Application monitoring: New Relic / DataDog agent installed
  [ ] Database monitoring: Configured query logging
  [ ] Log aggregation: CloudWatch / ELK stack / Splunk
  [ ] Alerting: Slack/PagerDuty for critical issues
  [ ] Uptime monitoring: Pingdom / UptimeRobot

[ ] 3.5 Scheduled Tasks Verification
  [ ] 6 AM: System health check runs
  [ ] 10 AM: daily analytics aggregation
  [ ] 11 AM Monday: Weekly analytics
  [ ] 2 PM    : Feedback reminder check
  [ ] 3 AM Sunday: Analytics cleanup


=== PHASE 4: POST-DEPLOYMENT ===

[ ] 4.1 Smoke Testing
  [ ] Access GUI: https://example.com/
  [ ] Login: User authentication works
  [ ] Dashboard: All modules accessible
  [ ] API: curl -H "Authorization: Bearer token" https://example.com/api/analytics/summary/
  [ ] Database: Users can create, read, update records
  [ ] Notifications: Escalations and reminders sent

[ ] 4.2 Backup Verification
  [ ] Database backup runs daily at 2 AM
  [ ] Media files backed up
  [ ] Backups stored redundantly (local + remote)
  [ ] Restore test: Verify backup can be restored

[ ] 4.3 Documentation
  [ ] Deployment runbook finalized
  [ ] Emergency procedures documented
  [ ] Team trained on procedures
  [ ] Incident response plan in place

[ ] 4.4 Monitoring Dashboard
  [ ] Request latency: p50, p95, p99
  [ ] Error rates by endpoint
  [ ] Database query performance
  [ ] Celery task success/failure rates
  [ ] Memory and CPU usage

[ ] 4.5 Daily Checks (First Week)
  [ ] Day 1-3: Monitor every 30 minutes during business hours
  [ ] Day 4-7: Reduce to every 1 hour
  [ ] Check error logs, audit trails, and system health


=== PERFORMANCE BASELINES ===

API Endpoint Performance Targets:
- /api/analytics/summary/ : p95 < 200ms
- /api/feedback/ CREATE: p95 < 100ms
- /api/escalations/ LIST : p95 < 300ms (paginated)
- /api/health-check/full_system_check/ : < 2000ms (runs checks)

Database Targets:
- Query response: p95 < 50ms
- Connection pool: 20-30 active connections
- Slow query log: < 1% of queries > 1000ms

Celery Task Targets:
- generate_daily_analytics: < 30 seconds
- send_unanswered_feedback_reminder: < 5 seconds
- run_system_health_check: < 10 seconds


=== ROLLBACK PROCEDURE ===

If critical issues found:

1. Immediate Actions
   [ ] Stop all requests: systemctl stop nginx
   [ ] Stop Celery: systemctl stop celery celery-beat
   [ ] Stop application: systemctl stop fusion

2. Database Rollback
   [ ] Restore from backup: pg_restore -d fusion_prod backup.sql
   [ ] Verify data: SELECT COUNT(*) FROM auth_user;

3. Code Rollback
   [ ] git checkout previous_tag
   [ ] Redeploy from previous version

4. Restart Services
   [ ] systemctl start fusion
   [ ] systemctl start celery
   [ ] systemctl start celery-beat
   [ ] systemctl start nginx

5. Verification
   [ ] Health check: GET /api/health-check/full_system_check/
   [ ] Users notified of rollback


=== DISK SPACE MANAGEMENT ===

Monitor disk usage (keep >20% free):
- /var/log/ : Rotate logs weekly (keep 4 weeks)
- /var/lib/postgresql/ : Monitor database size
- /home/fusion/media/ : Archive old files monthly
- /tmp/ : Clean regularly

Cleanup commands:
  find /var/log -name "*.log" -mtime +30 -delete
  python manage.py clearsessions  (run daily via cron)
"""


# ==================== ENVIRONMENT CONFIGURATION ====================

PRODUCTION_SETTINGS = """
# settings/production.py

from .common import *
import os

# Security
DEBUG = False
ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com', 'api.yourdomain.com']
SECRET_KEY = os.environ.get('SECRET_KEY')  # Set via environment variable

# HTTPS
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_SECURITY_POLICY = {
    'default-src': ("'self'",),
    'script-src': ("'self'", "'unsafe-inline'"),
    'style-src': ("'self'", "'unsafe-inline'"),
}

# Database (PostgreSQL)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'fusion_prod'),
        'USER': os.environ.get('DB_USER',  'fusion'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
        'CONN_MAX_AGE': 600,
        'OPTIONS': {
            'connect_timeout': 10,
        }
    }
}

# Cache (Redis)
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Celery
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/fusion/django.log',
            'maxBytes': 1024 * 1024 * 10,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'celery': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/fusion/celery.log',
            'maxBytes': 1024 * 1024 * 10,
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['file'],
        'level': 'INFO',
    },
    'loggers': {
        'celery': {
            'handlers': ['celery'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Email (for notifications)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@fusioniiit.com')

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = '/var/www/fusion/static/'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = '/var/www/fusion/media/'
"""


# ==================== GUNICORN CONFIGURATION ====================

GUNICORN_CONFIG = """
/etc/systemd/system/fusion.service

[Unit]
Description=FusionIIIT Gunicorn Service
After=network.target postgresql.service redis.service

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/home/fusion/fusioniiit
Environment="PATH=/home/fusion/fusioniiit/venv/bin"
Environment="DJANGO_SETTINGS_MODULE=Fusion.settings.production"
ExecStart=/home/fusion/fusioniiit/venv/bin/gunicorn \\
    --workers 8 \\
    --worker-class sync \\
    --worker-connections 1000 \\
    --max-requests 1000 \\
    --max-requests-jitter 50 \\
    --timeout 30 \\
    --bind unix:/run/fusion.sock \\
    --error-logfile /var/log/fusion/gunicorn_error.log \\
    --access-logfile /var/log/fusion/gunicorn_access.log \\
    Fusion.wsgi:application

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""


# ==================== NGINX CONFIGURATION ====================

NGINX_CONFIG = """
/etc/nginx/sites-available/fusion

upstream fusioniiit {
    server unix:/run/fusion.sock fail_timeout=0;
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS Server
server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    client_max_body_size 20M;
    
    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers on;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    
    # Logging
    access_log /var/log/nginx/fusion_access.log;
    error_log /var/log/nginx/fusion_error.log;
    
    # Compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript;
    gzip_min_length 1000;

    # Static files
    location /static/ {
        alias /var/www/fusion/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Media files
    location /media/ {
        alias /var/www/fusion/media/;
        expires 7d;
    }

    # API rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
    location /api/ {
        limit_req zone=api_limit burst=20 nodelay;
        proxy_pass http://fusioniiit;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Application
    location / {
        proxy_pass http://fusioniiit;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }
}
"""


# ==================== DEPLOYMENT COMMANDS ====================

DEPLOYMENT_COMMANDS = """
# Automated deployment script

#!/bin/bash
set -e

APP_DIR="/home/fusion/fusioniiit"
VENV="$APP_DIR/venv"
USER="www-data"

echo "=== Starting FusionIIIT Production Deployment ==="

# 1. Pull latest code
cd $APP_DIR
git pull origin main

# 2. Activate virtual environment
source $VENV/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Collect static files
python manage.py collectstatic --noinput

# 5. Run migrations
python manage.py migrate otheracademic

# 6. Run tests
python manage.py test --parallel

# 7. Restart services
systemctl restart fusion
systemctl restart celery celery-beat
systemctl restart nginx

# 8. Verify
sleep 2
curl -s https://yourdomain.com/api/health-check/full_system_check/ | python -m json.tool

echo "=== Deployment Complete ==="
"""


# ==================== MONITORING & ALERTS ====================

MONITORING_SETUP = """
# Monitoring with Sentry (Error Tracking)

SENTRY_DSN = os.environ.get('SENTRY_DSN')

if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.celery import CeleryIntegration
    
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            DjangoIntegration(),
            CeleryIntegration(),
        ],
        traces_sample_rate=0.1,
        send_default_pii=False,
    )

# Database Query Monitoring

DATABASES = {
    'default': {
        ...,
        'CONN_HEALTH_CHECKS': True,
        'OPTIONS': {
            'keepalives': 1,
            'keepalives_idle': 30,
            'keepalives_interval': 10,
            'keepalives_count': 5,
        }
    }
}
"""


print(__doc__)
print(PRODUCTION_DEPLOYMENT_CHECKLIST)
print(PRODUCTION_SETTINGS)
print(GUNICORN_CONFIG)
print(NGINX_CONFIG)
print(DEPLOYMENT_COMMANDS)
print(MONITORING_SETUP)
