#!/bin/bash

# Script to set up Let's Encrypt SSL certificates for production

set -e

# Check if domain and email are provided
if [ $# -ne 2 ]; then
    echo "Usage: $0 <domain> <email>"
    echo "Example: $0 hrbot.example.com admin@example.com"
    exit 1
fi

DOMAIN=$1
EMAIL=$2

echo "🔐 Setting up Let's Encrypt SSL for: $DOMAIN"
echo "=============================================="

# Create required directories
mkdir -p ./certbot/conf
mkdir -p ./certbot/www

# First, start nginx with HTTP only to handle ACME challenge
echo "1. Starting nginx for domain validation..."
NGINX_HOST=$DOMAIN docker-compose -f docker-compose.ssl.yml up -d nginx

# Wait for nginx to be ready
sleep 5

# Request certificate from Let's Encrypt
echo "2. Requesting certificate from Let's Encrypt..."
docker run --rm \
    -v "$(pwd)/certbot/conf:/etc/letsencrypt" \
    -v "$(pwd)/certbot/www:/var/www/certbot" \
    certbot/certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email $EMAIL \
    --agree-tos \
    --no-eff-email \
    -d $DOMAIN

# Check if certificate was obtained
if [ -f "./certbot/conf/live/$DOMAIN/fullchain.pem" ]; then
    echo "✅ Certificate obtained successfully!"
    
    # Update nginx configuration to use Let's Encrypt paths
    echo "3. Updating nginx configuration..."
    sed -i.bak \
        -e "s|ssl_certificate /etc/nginx/ssl/cert.pem;|ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;|" \
        -e "s|ssl_certificate_key /etc/nginx/ssl/key.pem;|ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;|" \
        ./nginx/nginx-ssl.conf
    
    # Restart nginx with SSL enabled
    echo "4. Restarting nginx with SSL..."
    docker-compose -f docker-compose.ssl.yml restart nginx
    
    # Start certbot container for auto-renewal
    echo "5. Starting certbot auto-renewal..."
    docker-compose -f docker-compose.ssl.yml --profile letsencrypt up -d certbot
    
    echo ""
    echo "✅ Let's Encrypt SSL setup complete!"
    echo ""
    echo "Your site is now available at: https://$DOMAIN"
    echo ""
    echo "Certificate auto-renewal is configured and will run twice daily."
    echo ""
    echo "To manually renew certificates:"
    echo "  docker-compose -f docker-compose.ssl.yml run certbot renew"
else
    echo "❌ Failed to obtain certificate!"
    echo "Please check the error messages above."
    exit 1
fi