# Vultr Deployment Guide

## Quick Setup Instructions

### 1. Create Vultr Instance
```bash
# Recommended specs for production:
# - Regular Performance: $12/month (2GB RAM)
# - OS: Ubuntu 22.04 LTS  
# - Location: Choose closest to you
# - SSH Key: Upload your public key
```

### 2. Initial Server Setup
```bash
# SSH into your instance
ssh root@your-vultr-ip

# Update system
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
apt install docker-compose -y

# Create deployment user
useradd -m -s /bin/bash -G docker ren
mkdir -p /home/ren/.ssh
cp /root/.ssh/authorized_keys /home/ren/.ssh/
chown -R ren:ren /home/ren/.ssh
chmod 700 /home/ren/.ssh
chmod 600 /home/ren/.ssh/authorized_keys
```

### 3. Deploy Application
```bash
# Switch to deployment user
su - ren

# Clone repository
git clone https://github.com/renatlas/renatlas-identity.git
cd renatlas-identity/deployment

# Set environment variables
export GITHUB_TOKEN="your_github_token_here"

# Deploy
./deploy.sh
```

### 4. Setup Cloudflare Tunnel (Optional)
```bash
# Create tunnel in Cloudflare dashboard
# Get tunnel token
# Add to .env file:
echo "CF_TUNNEL_TOKEN=your_tunnel_token" >> .env

# Deploy with tunnel
docker-compose --profile cloudflare up -d
```

## Firewall Configuration

```bash
# Basic firewall (if not using Cloudflare Tunnel)
ufw allow ssh
ufw allow 5000/tcp  # Dashboard port
ufw enable
```

## Monitoring Commands

```bash
# Check service status
docker-compose ps

# View logs
docker-compose logs -f

# Restart services
docker-compose restart

# Update deployment
git pull
docker-compose build
docker-compose up -d
```

## Backup Strategy

```bash
# Create backup script
cat > /home/ren/backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M)
cd /home/ren/renatlas-identity/deployment
tar -czf /home/ren/backups/ren-backup-$DATE.tar.gz data/ logs/
find /home/ren/backups/ -name "ren-backup-*.tar.gz" -mtime +7 -delete
EOF

chmod +x /home/ren/backup.sh
mkdir -p /home/ren/backups

# Add to crontab (daily backup)
echo "0 2 * * * /home/ren/backup.sh" | crontab -
```

## Maintenance

### Weekly Tasks:
- Check dashboard for system health
- Review learning cycle performance  
- Update system packages
- Check disk usage

### Monthly Tasks:
- Review and optimize costs
- Update application dependencies
- Analyze learning patterns and adjust configuration

## Troubleshooting

### Common Issues:

**Services won't start:**
```bash
# Check logs
docker-compose logs

# Check disk space
df -h

# Check memory
free -h
```

**GitHub API errors:**
```bash
# Verify token
echo $GITHUB_TOKEN

# Test GitHub CLI
docker-compose exec autonomous-learner gh auth status
```

**Dashboard not accessible:**
```bash
# Check port binding
docker-compose ps
netstat -tlnp | grep 5000
```

## Cost Monitoring

Monitor your Vultr dashboard for:
- CPU usage (should be <50% average)
- Memory usage (should be <80%)  
- Network transfer
- Storage usage

Scale up if consistently hitting limits.