# CI/CD Pipeline Setup Guide for SV Rap 8

This document explains how to set up and use the CI/CD pipeline for the SV Rap 8 event presence webapp.

## Overview

The CI/CD pipeline consists of three main jobs:

1. **Test**: Runs Django tests, linting, formatting checks, and health checks
2. **Build**: Builds and pushes Docker images to GitHub Container Registry
3. **Deploy**: Deploys the application to production server with automatic rollback on failure

## Pipeline Triggers

The pipeline is triggered on:
- Pull requests to the `main` branch (runs tests only)
- Pushes to the `main` branch (runs tests, build, and deploy)
- Manual workflow dispatch (runs all jobs)

## Required GitHub Secrets

To use this pipeline, you need to configure the following secrets in your GitHub repository:

### Server Access Secrets
```
DEPLOY_HOST        # IP address or hostname of your production server
DEPLOY_USER        # SSH username for deployment
DEPLOY_KEY         # SSH private key for server access (RSA format)
DEPLOY_PORT        # SSH port (optional, defaults to 22)
DEPLOY_PATH        # Path to project on server (optional, defaults to /opt/rap)
```

### Application Secrets
```
DJANGO_SECRET_KEY      # Django secret key for production
DJANGO_ALLOWED_HOSTS   # Comma-separated list of allowed hosts (e.g., yourdomain.com,www.yourdomain.com)
POSTGRES_DB           # PostgreSQL database name
POSTGRES_USER         # PostgreSQL username
POSTGRES_PASSWORD     # PostgreSQL password
PRODUCTION_URL        # Full URL to your production site (e.g., https://yourdomain.com)
```

### Email Configuration (Optional)
```
EMAIL_HOST            # SMTP server hostname
EMAIL_PORT            # SMTP port (defaults to 587)
EMAIL_HOST_USER       # SMTP username
EMAIL_HOST_PASSWORD   # SMTP password
EMAIL_USE_TLS         # Whether to use TLS (defaults to True)
DEFAULT_FROM_EMAIL    # Default sender email address
```

### Notification Secrets (Optional)
```
SLACK_WEBHOOK         # Slack webhook URL for deployment notifications
```

## Setting Up Secrets in GitHub

1. Go to your GitHub repository
2. Click on **Settings** tab
3. Click on **Secrets and variables** → **Actions**
4. Click **New repository secret**
5. Add each secret with its corresponding value

## SSH Key Setup

To generate an SSH key for deployment:

```bash
# Generate a new SSH key pair
ssh-keygen -t rsa -b 4096 -f ~/.ssh/rap_deploy_key

# Copy the public key to your server
ssh-copy-id -i ~/.ssh/rap_deploy_key.pub your-user@your-server

# Copy the private key content to GitHub secret DEPLOY_KEY
cat ~/.ssh/rap_deploy_key
```

## Production Server Setup

Your production server should have:

1. **Docker and Docker Compose installed**
2. **Git repository cloned** at the deployment path (default: `/opt/rap`)
3. **Proper permissions** for the deployment user
4. **SSL certificates** configured in `docker/nginx/ssl/`

### Initial Server Setup Commands

```bash
# Clone repository
sudo git clone https://github.com/your-username/rap.git /opt/rap
sudo chown -R your-user:your-user /opt/rap

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker your-user

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

## Pipeline Jobs Explained

### Test Job

Runs on every PR and push. Includes:
- Code formatting check with Black
- Linting with flake8
- Django system checks
- Database migrations test
- Unit tests
- Health check endpoint test

### Build Job

Runs only on pushes to main branch. Features:
- Builds Docker image
- Pushes to GitHub Container Registry
- Uses layer caching for faster builds
- Tags images with commit SHA and `latest`

### Deploy Job

Runs only on pushes to main branch after successful test and build. Features:
- SSH deployment to production server
- Blue-green deployment strategy
- Database migrations
- Static file collection
- Sample data creation (first deploy only)
- Health check verification
- Automatic rollback on failure
- Slack notifications

## Environment Files

The pipeline automatically creates a `.env.prod` file on the server with all necessary environment variables from GitHub secrets.

## Monitoring and Debugging

### Viewing Logs

Check deployment logs in the GitHub Actions tab of your repository.

### Server Logs

SSH into your server and run:
```bash
cd /opt/rap/docker
docker-compose -f docker-compose.prod.yml logs -f
```

### Health Check

The pipeline verifies deployment by checking the health endpoint:
```
GET https://yourdomain.com/health/
```

This endpoint returns JSON with the status of database and Redis connections.

## Rollback Process

If deployment fails, the pipeline automatically:
1. Detects the failure
2. Checks out the previous commit
3. Restarts services with the previous version
4. Logs the rollback process

## Manual Deployment

You can trigger a manual deployment by:
1. Going to the **Actions** tab in GitHub
2. Selecting **SV Rap 8 CI/CD Pipeline**
3. Clicking **Run workflow**
4. Selecting the branch and clicking **Run workflow**

## Security Best Practices

1. **Secrets Management**: Never commit secrets to the repository
2. **SSH Key Security**: Use dedicated deployment keys with minimal permissions
3. **Server Access**: Limit SSH access and use key-based authentication
4. **Environment Isolation**: Use separate secrets for staging/production
5. **Regular Updates**: Keep server dependencies up to date

## Troubleshooting

### Common Issues

1. **SSH Connection Failed**
   - Check `DEPLOY_HOST`, `DEPLOY_USER`, and `DEPLOY_KEY` secrets
   - Verify SSH key is properly formatted (RSA private key)
   - Ensure server allows SSH connections

2. **Database Connection Failed**
   - Check PostgreSQL credentials in secrets
   - Verify database service is running on server

3. **Health Check Failed**
   - Check application logs on server
   - Verify domain DNS configuration
   - Ensure SSL certificates are valid

4. **Docker Build Failed**
   - Check Dockerfile syntax
   - Verify all dependencies in requirements.txt
   - Check for syntax errors in code

### Getting Help

1. Check the **Actions** logs for detailed error messages
2. SSH into the server and check application logs
3. Verify all secrets are properly configured
4. Review the deployment documentation in `/docs/DEPLOYMENT.md`

## Pipeline Customization

You can customize the pipeline by:

1. **Modifying triggers**: Change `on:` section in the workflow file
2. **Adding tests**: Add more test steps in the test job
3. **Changing deployment strategy**: Modify the deploy job script
4. **Adding notifications**: Configure additional notification services

## Best Practices

1. **Test Locally**: Always test changes locally before pushing
2. **Small Commits**: Make small, focused commits for easier debugging
3. **Branch Protection**: Set up branch protection rules requiring PR reviews
4. **Monitoring**: Set up monitoring and alerting for your production application
5. **Backups**: Regularly backup your database and important data

---

For more detailed deployment information, see `/docs/DEPLOYMENT.md` in the repository.
