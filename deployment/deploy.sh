#!/bin/bash
# Deployment script for Ren Atlas Autonomous Learner

set -e

echo "🚀 Deploying Ren Atlas Autonomous Learner"

# Check environment variables
if [ -z "$GITHUB_TOKEN" ]; then
    echo "❌ GITHUB_TOKEN environment variable is required"
    exit 1
fi

# Create deployment directory structure
mkdir -p data/cycles logs

# Copy environment template if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template"
    cat > .env << EOF
# GitHub Configuration
GITHUB_TOKEN=${GITHUB_TOKEN}
REPO=renatlas/renatlas-identity

# Learning Configuration  
CYCLE_INTERVAL_MINUTES=120

# Cloudflare Tunnel (optional)
# CF_TUNNEL_TOKEN=your_tunnel_token_here
EOF
    echo "✅ Created .env file - please review and update as needed"
fi

# Build and start services
echo "🐳 Building Docker containers..."
docker-compose build

echo "🚀 Starting services..."
docker-compose up -d autonomous-learner dashboard

# Wait for services to be healthy
echo "⏳ Waiting for services to start..."
sleep 10

# Check service health
echo "🔍 Checking service health..."
if docker-compose ps | grep -q "Up (healthy)"; then
    echo "✅ Services are running and healthy!"
    echo ""
    echo "📊 Dashboard: http://localhost:5000"
    echo "🔍 View logs: docker-compose logs -f"
    echo "📈 Monitor: docker-compose ps"
    echo ""
    echo "🛠️  To deploy with Cloudflare Tunnel:"
    echo "   1. Set CF_TUNNEL_TOKEN in .env"
    echo "   2. Run: docker-compose --profile cloudflare up -d"
else
    echo "⚠️  Some services may not be healthy yet. Check logs:"
    docker-compose logs
    exit 1
fi

echo "🎉 Deployment complete!"