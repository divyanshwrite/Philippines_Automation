#!/bin/bash

echo "🚀 FDA Philippines Automation - Setup Script"
echo "=============================================="

# Check Python version
echo "🐍 Checking Python version..."
python3 --version

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv .venv

# Activate virtual environment
echo "⚡ Activating virtual environment..."
source .venv/bin/activate

# Install requirements
echo "📋 Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "✅ Setup complete!"
echo ""
echo "🎯 Next steps:"
echo "1. Configure your database settings in config.py"
echo "2. Ensure PostgreSQL is running and accessible"
echo "3. Run: source .venv/bin/activate"
echo "4. Run: python3 main_updated.py"
echo ""
echo "🧪 To test the system:"
echo "   python3 test_db_integration.py"
echo "   python3 test_10_docs.py"
echo ""
echo "📊 To check system status:"
echo "   python3 system_status.py"
echo ""
echo "🎉 Happy automating!"
