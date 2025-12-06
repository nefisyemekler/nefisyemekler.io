#!/usr/bin/env bash
# exit on error
set -o errexit

echo "=== Installing dependencies ==="
pip install -r requirements.txt

echo "=== Creating directories ==="
mkdir -p static/uploads

echo "=== Initializing database ==="
python3 -c "
from app import app, db
with app.app_context():
    try:
        db.create_all()
        print('✓ Database tables created')
    except Exception as e:
        print(f'✗ Database initialization error: {e}')
        raise
"

echo "=== Seeding database ==="
if [ -f seed.py ]; then
    python3 seed.py
else
    echo "No seed.py found, skipping"
fi

echo "=== Build complete ==="
