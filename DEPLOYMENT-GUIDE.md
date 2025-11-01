# 🚀 Object Quest Deployment Guide

## 📋 Overview

This guide covers deploying the Object Quest educational web application with SQLite leaderboard to various environments.

## 🏗️ Architecture

- **Frontend**: HTML/CSS/JavaScript with Three.js for 3D models
- **Backend**: Flask Python application
- **Database**: SQLite for leaderboard persistence
- **Computer Vision**: YOLOv10 for object detection
- **3D Models**: GLB files served from static directory

## 🖥️ Local Development Setup

### Prerequisites

```bash
# Python 3.8+ required
python --version

# Git for version control
git --version

# Node.js (optional, for frontend development)
node --version
```

### 1. Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd ARVROBJECTDETECTION

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Test database setup
python test_leaderboard.py
```

### 2. Run Application

```bash
# Start development server
python app.py

# Access application
# https://127.0.0.1:5000 (HTTPS required for camera access)
```

## 🌐 Production Deployment Options

### Option 1: VPS/Dedicated Server

#### Server Requirements
- **OS**: Ubuntu 20.04+ or CentOS 8+
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 10GB minimum for models and data
- **CPU**: 2 cores minimum, 4 cores recommended

#### Setup Steps

1. **Server Preparation**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install python3 python3-pip python3-venv nginx -y

# Install PyTorch with CUDA support (if GPU available)
pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# Create application user
sudo useradd -m -s /bin/bash objectquest
sudo mkdir -p /opt/objectquest
sudo chown objectquest:objectquest /opt/objectquest
```

2. **Application Deployment**
```bash
# Switch to application user
sudo su - objectquest

# Copy application files
cp -r /path/to/source/code /opt/objectquest/

# Create virtual environment
cd /opt/objectquest
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

3. **Nginx Configuration**
```bash
# Create nginx site config
sudo nano /etc/nginx/sites-available/objectquest
```

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        return 301 https://$server_name$request_uri;
    }
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /path/to/your/certificate.crt;
    ssl_certificate_key /path/to/your/private.key;
    
    location / {
        proxy_pass https://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /static/ {
        alias /opt/objectquest/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

4. **Systemd Service**
```bash
# Create service file
sudo nano /etc/systemd/system/objectquest.service
```

```ini
[Unit]
Description=Object Quest Flask Application
After=network.target

[Service]
Type=simple
User=objectquest
Group=objectquest
WorkingDirectory=/opt/objectquest
Environment=PATH=/opt/objectquest/venv/bin
ExecStart=/opt/objectquest/venv/bin/python app.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

5. **Start Services**
```bash
# Enable and start services
sudo systemctl enable nginx
sudo systemctl enable objectquest
sudo systemctl start objectquest
sudo systemctl start nginx

# Check status
sudo systemctl status objectquest
sudo systemctl status nginx
```

### Option 2: Cloud Platform Deployment

#### Heroku Deployment

1. **Prepare for Heroku**
```bash
# Create Procfile
echo "web: python app.py" > Procfile

# Create runtime.txt
echo "python-3.11.0" > runtime.txt

# Add to requirements.txt
echo "psycopg2-binary==2.9.7" >> requirements.txt
echo "gunicorn==21.2.0" >> requirements.txt
```

2. **Create Heroku App**
```bash
# Install Heroku CLI and login
heroku login

# Create app
heroku create your-objectquest-app

# Set environment variables
heroku config:set FLASK_ENV=production
heroku config:set DATABASE_PATH=/tmp/leaderboard.db
heroku config:set LEADERBOARD_CLEAR_TOKEN=your-secure-token

# Deploy
git push heroku main
```

#### Railway Deployment

1. **Connect Repository**
   - Visit railway.app
   - Connect your GitHub repository
   - Railway will auto-detect Python requirements

2. **Configure Environment**
   - Set `FLASK_ENV=production`
   - Set `DATABASE_PATH=/tmp/leaderboard.db`
   - Set custom port if needed

### Option 3: Docker Deployment

1. **Create Dockerfile**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directory
RUN mkdir -p data

# Expose port
EXPOSE 5000

# Run application
CMD ["python", "app.py"]
```

2. **Create Docker Compose**
```yaml
version: '3.8'

services:
  objectquest:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - DATABASE_PATH=/tmp/leaderboard.db
    volumes:
      - ./data:/tmp
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/"]
      interval: 30s
      timeout: 10s
      retries: 3
```

3. **Deploy with Docker**
```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f objectquest
```

## 🔒 SSL/HTTPS Setup

### Self-Signed Certificate (Development)

```bash
# Certificate is auto-generated on first run
# For production, use proper SSL certificates
```

### Let's Encrypt (Production)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

## 📊 Database Management

### SQLite Operations

```bash
# View database
sqlite3 data/leaderboard.db "SELECT * FROM leaderboard ORDER BY score DESC;"

# Backup database
cp data/leaderboard.db backup_$(date +%Y%m%d).db

# Restore database
cp backup_20231101.db data/leaderboard.db

# Clear leaderboard (use API with admin token)
curl -X DELETE "https://your-domain.com/api/leaderboard/clear" \
  -H "Authorization: Bearer your-admin-token"
```

### Migration to PostgreSQL (Optional)

If you need to scale beyond SQLite:

1. **Install PostgreSQL**
```bash
sudo apt install postgresql postgresql-contrib
```

2. **Update Dependencies**
```bash
pip install psycopg2-binary SQLAlchemy
```

3. **Modify Database Configuration**
```python
# In config.py
DATABASE_URL = os.environ.get('DATABASE_URL') or \
    'postgresql://user:password@localhost/objectquest'
```

## 🐛 Troubleshooting

### Common Issues

1. **Camera Permission Errors**
   - Ensure HTTPS is enabled
   - Check browser security settings
   - Test on localhost first

2. **Database Connection Issues**
   - Check file permissions on data directory
   - Verify SQLite installation
   - Monitor disk space

3. **3D Model Loading Errors**
   - Check static/models directory exists
   - Verify GLB file formats
   - Check browser console for errors

4. **Performance Issues**
   - Monitor CPU usage for YOLO processing
   - Check memory usage
   - Consider GPU acceleration

### Monitoring and Logging

```bash
# Application logs
tail -f /var/log/objectquest/app.log

# Nginx logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log

# System resources
htop
df -h
```

## 🔧 Maintenance

### Regular Updates

```bash
# Update dependencies
pip install --upgrade -r requirements.txt

# Update system packages
sudo apt update && sudo apt upgrade

# Restart services
sudo systemctl restart objectquest
sudo systemctl restart nginx
```

### Backup Strategy

```bash
#!/bin/bash
# backup_script.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/backups/objectquest"

mkdir -p $BACKUP_DIR

# Backup database
cp data/leaderboard.db $BACKUP_DIR/leaderboard_$DATE.db

# Backup application
tar -czf $BACKUP_DIR/app_$DATE.tar.gz --exclude=venv --exclude=__pycache__ .

# Keep only last 7 days of backups
find $BACKUP_DIR -name "*.db" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
```

### Security Checklist

- [ ] HTTPS enabled with valid certificates
- [ ] Firewall configured (ports 80, 443, 22)
- [ ] Regular security updates
- [ ] Database backups automated
- [ ] Admin tokens secured
- [ ] No debug mode in production
- [ ] Static files served efficiently
- [ ] Rate limiting configured (optional)

## 📈 Performance Optimization

### Application Level

- Enable GZIP compression
- Use CDN for static assets
- Optimize 3D model file sizes
- Implement caching headers

### Infrastructure Level

- Use reverse proxy (Nginx)
- Enable HTTP/2
- Configure keep-alive
- Monitor and scale resources

## 🆘 Support

For deployment issues:

1. Check application logs
2. Verify all dependencies installed
3. Test database connectivity
4. Validate SSL certificate
5. Check firewall settings

The application is designed to be self-contained and should work out of the box on any properly configured Linux server with Python 3.8+.

---

**Deployment Status**: ✅ **READY FOR PRODUCTION**
**Database**: ✅ **SQLITE CONFIGURED**
**Security**: ✅ **HTTPS READY**
**Documentation**: ✅ **COMPREHENSIVE**