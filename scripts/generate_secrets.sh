#!/bin/bash

# Script to generate production secrets for RAP Web Application
# Usage: ./generate_secrets.sh [domain_name]

set -e

DOMAIN_NAME=${1:-"your-domain.com"}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCKER_DIR="$(dirname "$SCRIPT_DIR")/docker"
ENV_FILE="$DOCKER_DIR/.env.prod"

echo "🔐 Generating production secrets for RAP Web Application..."
echo "Domain: $DOMAIN_NAME"

# Function to generate random string
generate_random() {
    openssl rand -base64 "$1" | tr -d "=+/" | cut -c1-"$1"
}

# Function to generate Django secret key
generate_django_secret() {
    python3 -c "
import secrets
import string
alphabet = string.ascii_letters + string.digits + '!@#$%^&*(-_=+)'
key = ''.join(secrets.choice(alphabet) for i in range(50))
print(key)
"
}

# Create docker directory if it doesn't exist
mkdir -p "$DOCKER_DIR"

# Generate secrets
echo "📝 Generating secrets..."

DJANGO_SECRET_KEY=$(generate_django_secret)
POSTGRES_PASSWORD=$(generate_random 32)
POSTGRES_USER="rap_user"
POSTGRES_DB="rap_db"
ADMIN_URL="admin-$(generate_random 16)/"

# Create .env.prod file
cat > "$ENV_FILE" << EOF
# Production Environment Variables
# Generated on $(date)

# Django Configuration
DJANGO_SECRET_KEY=$DJANGO_SECRET_KEY
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=$DOMAIN_NAME,localhost,127.0.0.1,0.0.0.0,web
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True

# Proxy Configuration
USE_X_FORWARDED_HOST=True
USE_X_FORWARDED_PORT=True
SECURE_PROXY_SSL_HEADER=HTTP_X_FORWARDED_PROTO,https

# Database Configuration
POSTGRES_DB=$POSTGRES_DB
POSTGRES_USER=$POSTGRES_USER
POSTGRES_PASSWORD=$POSTGRES_PASSWORD
POSTGRES_HOST=db
POSTGRES_PORT=5432
DATABASE_URL=postgres://$POSTGRES_USER:$POSTGRES_PASSWORD@db:5432/$POSTGRES_DB

# Redis Configuration
REDIS_URL=redis://redis:6379/0

# Admin Configuration
ADMIN_URL=$ADMIN_URL

# Docker Compose Configuration
COMPOSE_PROJECT_NAME=rap_prod
EOF

echo "✅ Production environment file created: $ENV_FILE"

# Set secure permissions
chmod 600 "$ENV_FILE"
echo "🔒 Set secure permissions (600) on environment file"

echo ""
echo "🎉 Production secrets generated successfully!"
echo ""
echo "📋 Summary:"
echo "  - Environment file: $ENV_FILE"
echo "  - Database: $POSTGRES_DB"
echo "  - Database User: $POSTGRES_USER"
echo "  - Admin URL: https://$DOMAIN_NAME/$ADMIN_URL"
echo ""
echo "🚨 IMPORTANT NEXT STEPS:"
echo "  1. Update DJANGO_ALLOWED_HOSTS in $ENV_FILE if needed"
echo ""
echo "  2. Start the production environment:"
echo "     cd $(dirname "$SCRIPT_DIR")"
echo "     docker-compose -f docker/docker-compose.prod.yml up -d"
echo ""
echo "ℹ️  SSL/TLS certificates are managed automatically by Caddy via Let's Encrypt."
echo "   No manual certificate setup is required."
echo ""
echo "🔐 Keep the .env.prod file secure and never commit it to version control!"
