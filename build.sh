#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

# Create upload directory
mkdir -p static/uploads

# Initialize database
python3 -c "from app import app, db; app.app_context().push(); db.create_all(); print('Database initialized')"

# Run seed script if it exists
if [ -f seed.py ]; then
    python3 seed.py || echo "Seed script failed or not needed"
fi
