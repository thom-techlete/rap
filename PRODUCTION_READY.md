# RAP Web Application - Production Ready Setup ✅

Your RAP Web Application is now fully configured for production deployment! Here's everything that's been set up for you:

## 🚀 Production Configuration Complete

### ✅ What's Ready

1. **Docker Production Environment**
   - `docker/docker-compose.prod.yml` - Full production stack
   - PostgreSQL database with health checks
   - Redis for caching and sessions
   - Nginx reverse proxy with SSL termination
   - Celery workers for background tasks
   - Security-hardened configuration

2. **Security Features**
   - SSL/TLS encryption (HTTPS only)
   - Security headers (HSTS, CSP, XSS protection)
   - Rate limiting on login and API endpoints
   - Secure cookies and sessions
   - Firewall configuration (UFW)
   - Secret generation with strong passwords

3. **Automated Deployment Scripts**
   - `scripts/deploy.sh` - Complete deployment automation
   - `scripts/generate_secrets.sh` - Secure secret generation
   - `scripts/vps-setup.sh` - One-command VPS setup

4. **Monitoring & Health Checks**
   - `/health/` endpoint for application monitoring
   - Docker health checks for all services
   - Comprehensive logging configuration

## 🌐 VPS Deployment Instructions

### Quick Setup (Recommended)

1. **Get a VPS server** (Ubuntu 20.04+ recommended)
   - Minimum: 2GB RAM, 2 CPU cores, 20GB storage
   - Set up SSH access

2. **Point your domain to the server IP**
   ```
   DNS A Record: your-domain.com → your-server-ip
   ```

3. **Run the one-line setup**
   ```bash
   # On your VPS server:
   curl -fsSL https://raw.githubusercontent.com/your-username/rap/main/scripts/vps-setup.sh | bash
   ```

### Manual Setup

If you prefer step-by-step control:

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/rap.git /opt/rap
   cd /opt/rap
   ```

2. **Generate production secrets**
   ```bash
   ./scripts/generate_secrets.sh your-domain.com
   ```

3. **Deploy the application**
   ```bash
   ./scripts/deploy.sh your-domain.com --setup
   ```

## 🔧 Management Commands

### Application Management
```bash
# Check status
./scripts/deploy.sh your-domain.com --status

# Update application
./scripts/deploy.sh your-domain.com --update

# Create backup
./scripts/deploy.sh your-domain.com --backup

# View logs
docker-compose -f docker/docker-compose.prod.yml logs -f
```

### Service Management
```bash
# Start services
docker-compose -f docker/docker-compose.prod.yml up -d

# Stop services
docker-compose -f docker/docker-compose.prod.yml down

# Restart specific service
docker-compose -f docker/docker-compose.prod.yml restart web
```

## 🛡️ Security Features

### Automatic Security
- **SSL/TLS**: Auto-configured with Let's Encrypt
- **Firewall**: UFW rules for ports 22, 80, 443 only
- **Rate Limiting**: Protection against brute force attacks
- **Security Headers**: HSTS, CSP, XSS protection
- **Secure Secrets**: Randomly generated passwords and keys

### Manual Security Steps
- Change default SSH port (recommended)
- Set up SSH key authentication
- Configure fail2ban for additional protection
- Regular security updates

## 📊 Monitoring

### Health Check Endpoint
```bash
curl https://your-domain.com/health/
```

### Application URLs
- **Main site**: `https://your-domain.com`
- **Admin panel**: `https://your-domain.com/[generated-admin-url]/`
- **Health check**: `https://your-domain.com/health/`

### Log Monitoring
```bash
# Application logs
docker-compose -f docker/docker-compose.prod.yml logs web

# Database logs
docker-compose -f docker/docker-compose.prod.yml logs db

# Nginx logs
docker-compose -f docker/docker-compose.prod.yml logs nginx
```

## 🔄 Backup & Recovery

### Automatic Backups
The deployment script creates backups before updates:
- Database dumps
- Full application backup
- Stored in `/opt/rap_backups/`

### Manual Backup
```bash
./scripts/deploy.sh your-domain.com --backup
```

## 🚨 Troubleshooting

### Common Issues

1. **Domain not accessible**
   - Check DNS propagation: `nslookup your-domain.com`
   - Verify firewall: `sudo ufw status`
   - Check SSL certificates: `sudo certbot certificates`

2. **Services not starting**
   ```bash
   docker-compose -f docker/docker-compose.prod.yml ps
   docker-compose -f docker/docker-compose.prod.yml logs
   ```

3. **Database connection issues**
   ```bash
   docker-compose -f docker/docker-compose.prod.yml logs db
   ```

### Get Support
- Check logs first for specific error messages
- Verify all environment variables in `.env.prod`
- Ensure domain DNS is properly configured

## 📁 File Structure

```
/opt/rap/                           # Production installation
├── docker/
│   ├── docker-compose.prod.yml     # Production Docker setup
│   ├── .env.prod                   # Production secrets (secured)
│   └── nginx/
│       ├── nginx.prod.conf         # Production Nginx config
│       └── ssl/                    # SSL certificates
├── scripts/
│   ├── deploy.sh                   # Main deployment script
│   ├── generate_secrets.sh         # Secret generation
│   └── vps-setup.sh               # VPS initial setup
├── web/                           # Django application
└── docs/
    └── DEPLOYMENT.md              # Detailed deployment guide
```

## 🎯 Next Steps

1. **Deploy to VPS**: Use the deployment scripts
2. **Configure DNS**: Point your domain to the server
3. **Access Application**: Visit your domain after deployment
4. **Create Admin User**: Follow the deployment script prompts
5. **Customize**: Update branding, add content, configure features

## 🔐 Security Reminders

- ✅ **Never commit `.env.prod` to version control**
- ✅ **Keep your server updated**: `sudo apt update && sudo apt upgrade`
- ✅ **Monitor logs regularly** for suspicious activity
- ✅ **Backup regularly** before making changes
- ✅ **Use strong passwords** for admin accounts

---

Your RAP Web Application is production-ready! 🎉

For detailed deployment instructions, see `docs/DEPLOYMENT.md`.
