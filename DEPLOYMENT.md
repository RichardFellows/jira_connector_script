# JIRA Analytics - Deployment Guide

This guide covers multiple deployment options for the JIRA Analytics dashboard, from local development to production deployments.

## 📦 Installation Methods

### 1. Direct Installation (Recommended for Development)

```bash
# Clone or download the project
git clone <repository-url>
cd jira_connector_script

# Install dependencies
pip install -r requirements.txt

# Run the analytics dashboard
python jira_analytics_cli.py
```

### 2. Package Installation

```bash
# Install as a Python package
pip install -e .

# Run using CLI commands
jira-extract --help
jira-analytics --help
```

### 3. Docker Deployment (Recommended for Production)

#### Quick Start
```bash
# Build and run with Docker Compose
docker-compose up -d

# Access dashboard at http://localhost:2718
```

#### Manual Docker Build
```bash
# Build the image
docker build -t jira-analytics .

# Run the container
docker run -d \
  --name jira-analytics \
  -p 2718:2718 \
  -v $(pwd)/data:/app/data \
  jira-analytics
```

## 🚀 Deployment Options

### Local Development
```bash
# Start development server
python jira_analytics_cli.py --port 2718 --host localhost

# Access at http://localhost:2718
```

### Team Server Deployment
```bash
# Deploy on team server (accessible to team members)
python jira_analytics_cli.py --host 0.0.0.0 --port 2718

# Access at http://your-server-ip:2718
```

### Production Docker Deployment

#### Option A: Docker Compose (Recommended)
```bash
# Create data directory
mkdir -p data config

# Copy configuration template
cp config.json.example config/config.json

# Set environment variables (optional)
export JIRA_URL="https://your-jira-server.com"
export JIRA_TOKEN="your-personal-access-token"

# Start services
docker-compose up -d

# View logs
docker-compose logs -f jira-analytics
```

#### Option B: Docker with External Database Volume
```bash
# Create named volume for persistence
docker volume create jira_analytics_data

# Run with persistent storage
docker run -d \
  --name jira-analytics-prod \
  --restart unless-stopped \
  -p 2718:2718 \
  -v jira_analytics_data:/app/data \
  -e JIRA_DB_PATH=/app/data/jira_data.duckdb \
  jira-analytics
```

## 🔧 Configuration

### Environment Variables
```bash
# Database configuration
JIRA_DB_PATH=/path/to/jira_data.duckdb

# Optional: Pre-configure JIRA connection
JIRA_URL=https://your-jira-server.com
JIRA_TOKEN=your_personal_access_token
JIRA_USERNAME=your_username
JIRA_PASSWORD=your_password
```

### Configuration Files
```bash
# Copy and customize configuration
cp config.json.example config.json

# Edit custom field mappings and field selections
vim config.json
```

## 🌐 Production Considerations

### 1. Reverse Proxy Setup (Nginx)
```nginx
server {
    listen 80;
    server_name analytics.yourdomain.com;
    
    location / {
        proxy_pass http://localhost:2718;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 2. SSL/TLS Configuration
```bash
# Generate SSL certificates (Let's Encrypt)
certbot --nginx -d analytics.yourdomain.com

# Or use existing certificates
# Update nginx configuration with SSL settings
```

### 3. Process Management (Systemd)
```ini
# /etc/systemd/system/jira-analytics.service
[Unit]
Description=JIRA Analytics Dashboard
After=network.target

[Service]
Type=simple
User=jira-analytics
WorkingDirectory=/opt/jira-analytics
ExecStart=/usr/local/bin/python jira_analytics_cli.py --host 0.0.0.0 --port 2718
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable jira-analytics
sudo systemctl start jira-analytics
sudo systemctl status jira-analytics
```

## 🔐 Security Considerations

### 1. Authentication
- Use Personal Access Tokens instead of passwords
- Store credentials in environment variables or secure vaults
- Rotate tokens regularly

### 2. Network Security
- Use HTTPS in production
- Restrict access to internal networks if possible
- Consider VPN or firewall rules

### 3. Data Security
- Encrypt database files at rest
- Regular backups of DuckDB files
- Secure file permissions (600/700)

### 4. Container Security
```bash
# Run container with read-only filesystem
docker run --read-only --tmpfs /tmp --tmpfs /var/run jira-analytics

# Use non-root user (already configured in Dockerfile)
# Scan images for vulnerabilities
docker scan jira-analytics
```

## 📊 Monitoring and Maintenance

### Health Checks
```bash
# Check service health
curl -f http://localhost:2718/health || echo "Service down"

# Docker health check
docker ps --format "table {{.Names}}\t{{.Status}}"
```

### Log Management
```bash
# View application logs
docker-compose logs -f jira-analytics

# Rotate logs
docker-compose logs --tail=1000 jira-analytics > logs/$(date +%Y%m%d).log
```

### Backup Strategy
```bash
# Backup DuckDB database
cp data/jira_data.duckdb backups/jira_data_$(date +%Y%m%d).duckdb

# Automated backup script
#!/bin/bash
BACKUP_DIR="/backups/jira-analytics"
mkdir -p $BACKUP_DIR
cp /app/data/jira_data.duckdb $BACKUP_DIR/jira_data_$(date +%Y%m%d_%H%M%S).duckdb
find $BACKUP_DIR -name "*.duckdb" -mtime +30 -delete
```

## 🔄 Updates and Upgrades

### Update Application
```bash
# Docker deployment
docker-compose pull
docker-compose up -d

# Direct installation
git pull
pip install -r requirements.txt --upgrade
```

### Database Migration
```bash
# Backup before updates
cp data/jira_data.duckdb data/jira_data_backup.duckdb

# Run update script if provided
python migrate_database.py
```

## 🐛 Troubleshooting

### Common Issues

#### Port Already in Use
```bash
# Find process using port 2718
lsof -i :2718
sudo netstat -tulpn | grep 2718

# Kill process or use different port
python jira_analytics_cli.py --port 2719
```

#### Permission Errors
```bash
# Fix file permissions
sudo chown -R $(whoami):$(whoami) data/
chmod 755 data/
chmod 644 data/jira_data.duckdb
```

#### Memory Issues
```bash
# Monitor memory usage
docker stats jira-analytics

# Increase container memory limit
docker run --memory=2g jira-analytics
```

#### Database Corruption
```bash
# Verify database integrity
python -c "import duckdb; conn = duckdb.connect('data/jira_data.duckdb'); print('Database OK')"

# Restore from backup
cp backups/jira_data_latest.duckdb data/jira_data.duckdb
```

## 📚 Additional Resources

- [Marimo Documentation](https://docs.marimo.io)
- [DuckDB Documentation](https://duckdb.org/docs/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [JIRA REST API Documentation](https://developer.atlassian.com/server/jira/platform/rest-apis/)

## 📞 Support

For issues and questions:
1. Check the troubleshooting section above
2. Review application logs
3. Open an issue in the project repository
4. Contact the development team