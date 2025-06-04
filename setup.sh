#!/bin/bash

# HR Bot Local Setup Script
# This script sets up the HR Bot for local development

set -e

echo "Setting up HR Bot Prototype..."

# Check Python version
if ! python3 --version | grep -E "3\.(9|10|11)" &> /dev/null; then
    echo "Error: Python 3.9+ is required"
    exit 1
fi

# Check Node.js
if ! node --version &> /dev/null; then
    echo "Error: Node.js is required"
    exit 1
fi

# Backend setup
echo "Setting up backend..."
cd backend

# Create virtual environment
echo "Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create directories
mkdir -p data/hr_docs

# Copy env file if not exists
if [ ! -f .env ]; then
    cp .env.example .env
    echo ""
    echo "⚠️  Please edit backend/.env and add your API keys!"
    echo ""
fi

# Create sample documents
echo "Creating sample HR documents..."
python scripts/ingest_docs.py

deactivate
cd ..

# Frontend setup
echo "Setting up frontend..."
cd frontend

echo "Installing Node dependencies..."
npm install

cd ..

echo ""
echo "✅ Setup complete!"
echo ""
echo "To run the application:"
echo ""
echo "1. Backend (in one terminal):"
echo "   cd backend"
echo "   source venv/bin/activate"
echo "   uvicorn app.main:app --reload"
echo ""
echo "2. Frontend (in another terminal):"
echo "   cd frontend"
echo "   npm start"
echo ""
echo "3. Open http://localhost:3000 in your browser"
echo ""
echo "Demo credentials: admin / password"
echo ""
echo "⚠️  Don't forget to add your API keys to backend/.env!"