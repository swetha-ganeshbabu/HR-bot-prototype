#!/bin/bash
set -e

echo "Starting HR Bot backend..."

# Wait for database to be ready
echo "Initializing database..."
python -c "from app.database import engine, Base; from app.models import *; Base.metadata.create_all(bind=engine)"

# Create demo user if not exists
python -c "from app.database import SessionLocal; from app.auth import create_demo_user; db = SessionLocal(); create_demo_user(db); db.close()"

# Check if HR documents need to be ingested
if [ -z "$(ls -A data/hr_docs/*.md 2>/dev/null)" ]; then
    echo "No HR documents found in data/hr_docs/"
else
    echo "Ingesting HR documents..."
    python scripts/ingest_hr_documents.py || echo "Document ingestion completed (some documents may already exist)"
fi

# Start the application
echo "Starting Uvicorn server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000