#!/bin/bash

# Script to generate self-signed SSL certificates for development

set -e

DOMAIN=${1:-localhost}
SSL_DIR="./ssl/certs"

echo "🔐 Generating self-signed SSL certificate for: $DOMAIN"
echo "=============================================="

# Create SSL directory if it doesn't exist
mkdir -p "$SSL_DIR"

# Generate private key
echo "1. Generating private key..."
openssl genrsa -out "$SSL_DIR/key.pem" 2048

# Generate certificate signing request
echo "2. Generating certificate signing request..."
openssl req -new -key "$SSL_DIR/key.pem" -out "$SSL_DIR/csr.pem" \
    -subj "/C=US/ST=California/L=San Francisco/O=HR Bot Dev/CN=$DOMAIN"

# Generate self-signed certificate (valid for 365 days)
echo "3. Generating self-signed certificate..."
openssl x509 -req -days 365 -in "$SSL_DIR/csr.pem" \
    -signkey "$SSL_DIR/key.pem" -out "$SSL_DIR/cert.pem"

# Create a combined certificate file (for some applications)
cat "$SSL_DIR/cert.pem" "$SSL_DIR/key.pem" > "$SSL_DIR/combined.pem"

# Set appropriate permissions
chmod 600 "$SSL_DIR/key.pem"
chmod 644 "$SSL_DIR/cert.pem"
chmod 600 "$SSL_DIR/combined.pem"

# Clean up CSR
rm "$SSL_DIR/csr.pem"

echo ""
echo "✅ SSL certificates generated successfully!"
echo ""
echo "Files created:"
echo "  - Private key: $SSL_DIR/key.pem"
echo "  - Certificate: $SSL_DIR/cert.pem"
echo "  - Combined:    $SSL_DIR/combined.pem"
echo ""
echo "To use with docker-compose:"
echo "  docker-compose -f docker-compose.ssl.yml up -d"
echo ""
echo "To trust the certificate on macOS:"
echo "  sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain $SSL_DIR/cert.pem"
echo ""
echo "⚠️  Note: This is a self-signed certificate for development only!"
echo "    Browsers will show a security warning that you'll need to accept."