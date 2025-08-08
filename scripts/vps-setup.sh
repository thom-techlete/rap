#!/bin/bash

# Quick VPS deployment script for RAP Web Application
# Run this script on a fresh Ubuntu/Debian server

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}"
echo "🚀 RAP Web Application - Quick VPS Setup"
echo "========================================"
echo -e "${NC}"

# Get domain name
read -p "Enter your domain name (e.g., rap.yourdomain.com): " DOMAIN_NAME

if [[ -z "$DOMAIN_NAME" ]]; then
    echo -e "${RED}Domain name is required!${NC}"
    exit 1
fi

echo -e "${BLUE}Setting up RAP Web Application for domain: $DOMAIN_NAME${NC}"

# Update system
echo -e "${BLUE}📦 Updating system packages...${NC}"
sudo apt-get update && sudo apt-get upgrade -y

# Install essential packages
echo -e "${BLUE}📦 Installing essential packages...${NC}"
sudo apt-get install -y curl wget git htop unzip ufw

# Install Docker
echo -e "${BLUE}🐳 Installing Docker...${NC}"
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
fi

# Install Docker Compose
echo -e "${BLUE}🐳 Installing Docker Compose...${NC}"
if ! command -v docker-compose &> /dev/null; then
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

# Setup project directory
echo -e "${BLUE}📁 Setting up project directory...${NC}"
sudo mkdir -p /opt
cd /opt

# Clone repository (you'll need to replace this with your actual repository URL)
echo -e "${BLUE}📥 Cloning repository...${NC}"
if [[ ! -d "/opt/rap" ]]; then
    echo "Please enter your repository URL (e.g., https://github.com/your-username/rap.git):"
    read -p "Repository URL: " REPO_URL
    
    if [[ -z "$REPO_URL" ]]; then
        echo -e "${RED}Repository URL is required!${NC}"
        exit 1
    fi
    
    sudo git clone "$REPO_URL" rap
    sudo chown -R $USER:$USER /opt/rap
fi

cd /opt/rap

# Make scripts executable
chmod +x scripts/*.sh

# Check if user is in docker group
if ! groups $USER | grep &> /dev/null '\bdocker\b'; then
    echo -e "${BLUE}👤 Adding user to docker group...${NC}"
    echo "You need to log out and log back in after this script completes."
    echo "Then run: /opt/rap/scripts/deploy.sh $DOMAIN_NAME --setup"
    exit 0
fi

# Run deployment
echo -e "${BLUE}🚀 Starting deployment...${NC}"
./scripts/deploy.sh "$DOMAIN_NAME" --setup

echo -e "${GREEN}"
echo "✅ Setup completed!"
echo ""
echo "🌐 Your application should be available at: https://$DOMAIN_NAME"
echo "🔧 Admin panel: Check the generated admin URL in the deployment output"
echo ""
echo "📝 Next steps:"
echo "1. Point your domain DNS A record to this server's IP address"
echo "2. Wait for DNS propagation (5-30 minutes)"
echo "3. Visit your domain to access the application"
echo ""
echo "🔍 Useful commands:"
echo "  Status: /opt/rap/scripts/deploy.sh $DOMAIN_NAME --status"
echo "  Update: /opt/rap/scripts/deploy.sh $DOMAIN_NAME --update"
echo "  Backup: /opt/rap/scripts/deploy.sh $DOMAIN_NAME --backup"
echo "  Logs: docker-compose -f /opt/rap/docker/docker-compose.prod.yml logs -f"
echo -e "${NC}"
