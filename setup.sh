#!/bin/bash
# Quick setup script for Flask app

echo "🚀 Setting up Sign Language Detector (Flask Version)..."

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements_render.txt

# Create directories if needed
mkdir -p templates

# Check for model file
if [ ! -f "model.p" ]; then
    echo "⚠️  model.p not found! Please ensure it's in the project root."
else
    echo "✓ model.p found"
fi

# Run the app
echo "✓ Setup complete!"
echo ""
echo "To start the app, run:"
echo "  python app_flask.py"
echo ""
echo "Then visit: http://localhost:5000"
