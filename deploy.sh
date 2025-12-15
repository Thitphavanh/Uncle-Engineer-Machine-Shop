#!/bin/bash
echo "Deploying to Production Server..."
ssh uncle-machine@129.212.238.63 << 'EOF'
    set -e
    cd ~/Uncle-Machine/Uncle-Engineer-Machine-Shop
    
    echo "Pulling latest code..."
    git pull origin main
    
    echo "Rebuilding web container..."
    docker compose -f docker-compose.yml up -d --build web-prod
    
    echo "Running migrations..."
    docker compose -f docker-compose.yml exec web-prod python manage.py migrate
    
    echo "Collecting static files..."
    docker compose -f docker-compose.yml exec web-prod python manage.py collectstatic --noinput
    
    echo "Restarting service..."
    docker compose -f docker-compose.yml restart web-prod
    
    echo "Deployment Complete!"
EOF
