#!/bin/bash

# PricingEngine Startup Script
echo "=== Starting PricingEngine ==="

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
fi

echo "=== Setup Complete ==="
echo ""
echo "To start the API server:"
echo "  python main.py"
echo ""
echo "To run tests:"
echo "  pytest -v"
echo ""
echo "To test the API:"
echo "  python test_api_client.py"
echo ""
echo "API Documentation will be available at:"
echo "  http://localhost:8000/docs"
