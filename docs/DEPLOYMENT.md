# Production Deployment Guide for RAP Web Application

This guide will help you deploy the RAP Web Application to a production VPS server.

## Prerequisites

### Server Requirements
- Ubuntu 20.04+ or Debian 11+ server
- Minimum 2GB RAM, 2 CPU cores
- 20GB+ disk space
- Root or sudo access
- Domain name pointing to your server's IP address

### Local Requirements
- Git installed on your local machine
- SSH access to your server

## Quick Start

### 1. Server Setup

First, connect to your server via SSH:

```bash
ssh your-user@your-server-ip
```

Update your system:

```bash
sudo apt update && sudo apt upgrade -y
```

### 2. Clone Repository

Clone the repository to `/opt/rap`:

```bash
sudo mkdir -p /opt
cd /opt
sudo git clone https://github.com/your-username/rap.git
sudo chown -R $USER:$USER /opt/rap
cd /opt/rap
```

### 3. Run Deployment Script

Make the deployment script executable and run it:

```bash
chmod +x scripts/deploy.sh
./scripts/deploy.sh your-domain.com --setup
```

This will:
- Install Docker and Docker Compose
- Set up firewall rules
- Generate SSL certificates with Let's Encrypt
- Generate production secrets
- Deploy the application with all services

### 4. DNS Configuration

Point your domain's DNS A record to your server's IP address:

```
Type: A
Name: @ (or your subdomain)
Value: your-server-ip
TTL: 3600
```

## Manual Setup (Alternative)

If you prefer to set up manually:

### 1. Install Docker

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Log out and log back in for group changes to take effect
```

### 2. Generate Production Secrets

```bash
cd /opt/rap
chmod +x scripts/generate_secrets.sh
./scripts/generate_secrets.sh your-domain.com
```

### 3. Setup SSL Certificates

Install Certbot and generate certificates:

```bash
sudo apt install certbot
sudo certbot certonly --standalone -d your-domain.com

# Copy certificates to nginx directory
mkdir -p docker/nginx/ssl
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem docker/nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem docker/nginx/ssl/key.pem
sudo chown $USER:$USER docker/nginx/ssl/*.pem
```

### 4. Deploy Application

```bash
# Build and start services
docker-compose -f docker/docker-compose.prod.yml up --build -d

# Wait for database to start
sleep 20

# Run migrations
docker-compose -f docker/docker-compose.prod.yml exec web python manage.py migrate

# Collect static files
docker-compose -f docker/docker-compose.prod.yml exec web python manage.py collectstatic --noinput

# Create superuser
docker-compose -f docker/docker-compose.prod.yml exec web python manage.py createsuperuser
```

## Environment Configuration

The production environment file (`.env.prod`) contains:

```bash
# Django Configuration
DJANGO_SECRET_KEY=<generated-secret-key>
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=your-domain.com,localhost,127.0.0.1
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True

# Database Configuration
POSTGRES_DB=<generated-db-name>
POSTGRES_USER=<generated-user>
POSTGRES_PASSWORD=<generated-password>
DATABASE_URL=postgres://<user>:<password>@db:5432/<db-name>

# Redis Configuration
REDIS_URL=redis://redis:6379/0

# Admin Configuration
ADMIN_URL=<generated-admin-url>/
```

## Service Management

### Start Services
```bash
docker-compose -f docker/docker-compose.prod.yml up -d
```

### Stop Services
```bash
docker-compose -f docker/docker-compose.prod.yml down
```

### View Logs
```bash
# All services
docker-compose -f docker/docker-compose.prod.yml logs -f

# Specific service
docker-compose -f docker/docker-compose.prod.yml logs -f web
docker-compose -f docker/docker-compose.prod.yml logs -f db
docker-compose -f docker/docker-compose.prod.yml logs -f nginx
```

### Check Status
```bash
docker-compose -f docker/docker-compose.prod.yml ps
```

## Maintenance

### Updates

To update the application:

```bash
cd /opt/rap
./scripts/deploy.sh your-domain.com --update
```

This will:
- Create a backup
- Pull latest code from Git
- Update Docker images
- Run database migrations
- Collect static files
- Restart services

### Backups

Create a backup:

```bash
./scripts/deploy.sh your-domain.com --backup
```

Backups are stored in `/opt/rap_backups/`

### SSL Certificate Renewal

SSL certificates are automatically renewed via cron job. To manually renew:

```bash
sudo certbot renew
docker-compose -f docker/docker-compose.prod.yml restart nginx
```

## Security Features

### Firewall (UFW)
- SSH (port 22)
- HTTP (port 80) - redirects to HTTPS
- HTTPS (port 443)
- All other ports blocked

### Nginx Security Headers
- HSTS (HTTP Strict Transport Security)
- XSS Protection
- Content Type Options
- Frame Options
- Content Security Policy
- Rate limiting on login and API endpoints

### Django Security
- DEBUG disabled
- Secure cookies
- CSRF protection
- Session security
- Enhanced password validation
- Security middleware

## Monitoring

### Check Application Health

Visit: `https://your-domain.com/health/`

### Monitor Resources

```bash
# System resources
htop

# Docker resources
docker stats

# Disk usage
df -h
```

## Troubleshooting

### Common Issues

1. **Port 80/443 already in use**
   ```bash
   sudo netstat -tulpn | grep :80
   sudo systemctl stop apache2  # or nginx
   ```

2. **SSL certificate issues**
   ```bash
   sudo certbot certificates
   sudo certbot renew --dry-run
   ```

3. **Database connection issues**
   ```bash
   docker-compose -f docker/docker-compose.prod.yml logs db
   ```

4. **Application not starting**
   ```bash
   docker-compose -f docker/docker-compose.prod.yml logs web
   ```

### Getting Help

- Check logs for specific error messages
- Ensure DNS is properly configured
- Verify firewall rules
- Check SSL certificate validity

## File Structure

```
/opt/rap/
├── docker/
│   ├── docker-compose.prod.yml    # Production Docker Compose
│   ├── .env.prod                  # Production environment variables
│   └── nginx/
│       ├── nginx.prod.conf        # Production Nginx config
│       └── ssl/                   # SSL certificates
├── scripts/
│   ├── deploy.sh                  # Deployment script
│   └── generate_secrets.sh        # Secret generation script
└── web/                           # Django application
```

## Security Checklist

- [ ] SSL certificates installed and working
- [ ] Firewall configured (UFW)
- [ ] Strong database passwords generated
- [ ] Admin URL randomized
- [ ] DEBUG mode disabled
- [ ] Secure cookies enabled
- [ ] HSTS headers configured
- [ ] Regular backups scheduled
- [ ] Log monitoring set up

## Performance Optimization

### Database
- Regular VACUUM and ANALYZE
- Monitor slow queries
- Consider connection pooling for high traffic

### Static Files
- Served by Nginx with caching headers
- Compressed with gzip

### Application
- Gunicorn with multiple workers
- Redis for caching and sessions
- Celery for background tasks

## Support

For issues or questions:
1. Check the logs first
2. Review this documentation
3. Check the GitHub repository issues
4. Contact the development team

---

**Remember**: Keep your `.env.prod` file secure and never commit it to version control!
