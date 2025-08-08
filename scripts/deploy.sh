#!/bin/bash

# Production deployment script for RAP Web Application
# Usage: ./deploy.sh [--setup|--update|--backup]

set -e

# Configuration
DOMAIN_NAME="rap8.nl"
ACTION=${1:-"--setup"}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
DOCKER_DIR="$PROJECT_DIR/docker"
ENV_FILE="$DOCKER_DIR/.env.prod"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_error "This script should not be run as root. Please run as a regular user with sudo privileges."
        exit 1
    fi
}

# Check system requirements
check_requirements() {
    log_info "Checking system requirements..."
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        echo "Installation guide: https://docs.docker.com/engine/install/"
        exit 1
    fi
    
    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        echo "Installation guide: https://docs.docker.com/compose/install/"
        exit 1
    fi
    
    # Check if user is in docker group
    if ! groups $USER | grep &> /dev/null '\bdocker\b'; then
        log_warning "User is not in docker group. Adding user to docker group..."
        sudo usermod -aG docker $USER
        log_warning "Please log out and log back in for group changes to take effect."
        log_warning "Then run this script again."
        exit 1
    fi
    
    log_success "System requirements check passed"
}

# Setup firewall
setup_firewall() {
    log_info "Setting up firewall..."
    
    # Install UFW if not present
    if ! command -v ufw &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y ufw
    fi
    
    # Configure firewall
    sudo ufw --force reset
    sudo ufw default deny incoming
    sudo ufw default allow outgoing
    sudo ufw allow ssh
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    sudo ufw --force enable
    
    log_success "Firewall configured"
}

# Generate SSL certificates using Let's Encrypt
setup_ssl() {
    log_info "Setting up SSL certificates for $DOMAIN_NAME..."
    
    # Install certbot if not present
    if ! command -v certbot &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y certbot
    fi
    
    # Create SSL directory
    SSL_DIR="$DOCKER_DIR/nginx/ssl"
    mkdir -p "$SSL_DIR"
    
    # Stop any running nginx to free port 80
    docker-compose -f "$DOCKER_DIR/docker-compose.prod.yml" stop nginx 2>/dev/null || true
    
    # Generate certificate
    log_info "Generating SSL certificate..."
    sudo certbot certonly \
        --standalone \
        --non-interactive \
        --agree-tos \
        --email "admin@$DOMAIN_NAME" \
        -d "$DOMAIN_NAME"
    
    # Copy certificates
    sudo cp "/etc/letsencrypt/live/$DOMAIN_NAME/fullchain.pem" "$SSL_DIR/cert.pem"
    sudo cp "/etc/letsencrypt/live/$DOMAIN_NAME/privkey.pem" "$SSL_DIR/key.pem"
    sudo chown $USER:$USER "$SSL_DIR"/*.pem
    sudo chmod 644 "$SSL_DIR"/*.pem
    
    # Setup automatic renewal
    cat > /tmp/certbot-renewal << 'EOF'
#!/bin/bash
certbot renew --quiet --deploy-hook "docker-compose -f /opt/rap/docker/docker-compose.prod.yml restart nginx"
EOF
    
    sudo cp /tmp/certbot-renewal /etc/cron.weekly/
    sudo chmod +x /etc/cron.weekly/certbot-renewal
    
    log_success "SSL certificates configured"
}

# Create backup
create_backup() {
    log_info "Creating backup..."
    
    BACKUP_DIR="/opt/rap_backups"
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    BACKUP_FILE="$BACKUP_DIR/rap_backup_$TIMESTAMP.tar.gz"
    
    sudo mkdir -p "$BACKUP_DIR"
    
    # Stop services
    cd "$PROJECT_DIR"
    docker-compose -f "$DOCKER_DIR/docker-compose.prod.yml" stop
    
    # Create database backup
    docker-compose -f "$DOCKER_DIR/docker-compose.prod.yml" up -d db
    sleep 10
    docker-compose -f "$DOCKER_DIR/docker-compose.prod.yml" exec -T db pg_dump -U rap_user rap_db > "$BACKUP_DIR/db_backup_$TIMESTAMP.sql"
    
    # Create full backup
    sudo tar -czf "$BACKUP_FILE" \
        --exclude='*.pyc' \
        --exclude='__pycache__' \
        --exclude='.git' \
        --exclude='venv' \
        --exclude='node_modules' \
        "$PROJECT_DIR"
    
    log_success "Backup created: $BACKUP_FILE"
}

# Deploy application
deploy_application() {
    log_info "Deploying RAP Web Application..."
    
    cd "$PROJECT_DIR"
    
    # Generate production secrets if not exists
    if [[ ! -f "$ENV_FILE" ]]; then
        log_info "Generating production secrets..."
        "$SCRIPT_DIR/generate_secrets.sh" "$DOMAIN_NAME"
    fi
    
    # Pull latest images
    log_info "Pulling latest Docker images..."
    docker-compose -f "$DOCKER_DIR/docker-compose.prod.yml" pull
    
    # Build and start services
    log_info "Building and starting services..."
    docker-compose -f "$DOCKER_DIR/docker-compose.prod.yml" up --build -d
    
    # Wait for database to be ready
    log_info "Waiting for database to be ready..."
    sleep 20
    
    # Run migrations
    log_info "Running database migrations..."
    docker-compose -f "$DOCKER_DIR/docker-compose.prod.yml" exec web python manage.py migrate
    
    # Collect static files
    log_info "Collecting static files..."
    docker-compose -f "$DOCKER_DIR/docker-compose.prod.yml" exec web python manage.py collectstatic --noinput
    
    # Create superuser if needed
    log_info "Creating superuser..."
    echo "Please create a superuser account:"
    docker-compose -f "$DOCKER_DIR/docker-compose.prod.yml" exec web python manage.py createsuperuser || true
    
    log_success "Application deployed successfully!"
}

# Update application
update_application() {
    log_info "Updating RAP Web Application..."
    
    cd "$PROJECT_DIR"
    
    # Create backup before update
    create_backup
    
    # Pull latest code
    git pull origin main
    
    # Update containers
    docker-compose -f "$DOCKER_DIR/docker-compose.prod.yml" pull
    docker-compose -f "$DOCKER_DIR/docker-compose.prod.yml" up --build -d
    
    # Run migrations
    docker-compose -f "$DOCKER_DIR/docker-compose.prod.yml" exec web python manage.py migrate
    
    # Collect static files
    docker-compose -f "$DOCKER_DIR/docker-compose.prod.yml" exec web python manage.py collectstatic --noinput
    
    log_success "Application updated successfully!"
}

# Install system dependencies
install_dependencies() {
    log_info "Installing system dependencies..."
    
    sudo apt-get update
    sudo apt-get install -y \
        curl \
        wget \
        git \
        htop \
        unzip \
        software-properties-common \
        apt-transport-https \
        ca-certificates \
        gnupg \
        lsb-release
    
    log_success "System dependencies installed"
}

# Show status
show_status() {
    log_info "Application Status:"
    cd "$PROJECT_DIR"
    docker-compose -f "$DOCKER_DIR/docker-compose.prod.yml" ps
    
    echo ""
    log_info "Application URLs:"
    echo "  Main site: https://$DOMAIN_NAME"
    if [[ -f "$ENV_FILE" ]]; then
        ADMIN_URL=$(grep "ADMIN_URL=" "$ENV_FILE" | cut -d'=' -f2)
        echo "  Admin: https://$DOMAIN_NAME/$ADMIN_URL"
    fi
    
    echo ""
    log_info "Logs:"
    echo "  Application: docker-compose -f $DOCKER_DIR/docker-compose.prod.yml logs web"
    echo "  Database: docker-compose -f $DOCKER_DIR/docker-compose.prod.yml logs db"
    echo "  Nginx: docker-compose -f $DOCKER_DIR/docker-compose.prod.yml logs nginx"
}

# Main execution
main() {
    echo "🚀 RAP Web Application Deployment Script"
    echo "=========================================="
    echo "Domain: $DOMAIN_NAME"
    echo "Action: $ACTION"
    echo ""
    
    check_root
    
    case $ACTION in
        --setup)
            check_requirements
            install_dependencies
            setup_firewall
            setup_ssl
            deploy_application
            show_status
            ;;
        --update)
            update_application
            show_status
            ;;
        --backup)
            create_backup
            ;;
        --status)
            show_status
            ;;
        *)
            echo "Usage: $0 [domain_name] [--setup|--update|--backup|--status]"
            echo ""
            echo "Actions:"
            echo "  --setup   : Initial setup (install dependencies, SSL, deploy)"
            echo "  --update  : Update application (backup, pull, deploy)"
            echo "  --backup  : Create backup only"
            echo "  --status  : Show application status"
            exit 1
            ;;
    esac
    
    echo ""
    log_success "🎉 Operation completed successfully!"
    echo ""
    echo "📝 Next steps:"
    echo "  - Point your domain DNS A record to this server's IP"
    echo "  - Visit https://$DOMAIN_NAME to access the application"
    echo "  - Monitor logs with: docker-compose -f $DOCKER_DIR/docker-compose.prod.yml logs -f"
    echo "  - For updates, run: $0 $DOMAIN_NAME --update"
}

# Run main function
main "$@"
