#!/bin/bash
# Setup script for Insurance Insights Assistant (Mac/Linux)

set -e

echo "Setting up backend..."

# Create venv if it doesn't exist
if [ ! -d "backend/venv" ]; then
    python3 -m venv backend/venv
fi

# Install Python dependencies
backend/venv/bin/pip install -r backend/requirements.txt

# Copy .env.example to .env if .env doesn't exist
if [ ! -f "backend/.env" ]; then
    cp backend/.env.example backend/.env
    echo "Created backend/.env from .env.example — fill in your OPENAI_API_KEY before running."
fi

echo "Setting up frontend..."
cd frontend
npm install
cd ..

echo ""
echo "Setup complete. To start the app:"
echo "  Backend:  source backend/venv/bin/activate  then  python backend/app.py"
echo "  Frontend: cd frontend  then  npm run dev"
