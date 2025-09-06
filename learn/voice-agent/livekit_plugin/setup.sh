#!/bin/bash

# LiveKit Fireworks Voice Agent Setup Script

set -e

echo "🚀 Setting up LiveKit Fireworks Voice Agent Plugin..."

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    echo "Please install Python 3.8 or later and try again."
    exit 1
fi

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv .venv

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Copy environment template if .env doesn't exist
if [ ! -f .env ]; then
    echo "📋 Creating .env file from template..."
    cp env_template.txt .env
    echo "✅ Created .env file. Please edit it with your API keys:"
    echo "   - FIREWORKS_API_KEY"
    echo "   - LIVEKIT_API_KEY"
    echo "   - LIVEKIT_API_SECRET"
    echo "   - LIVEKIT_URL"
else
    echo "ℹ️  .env file already exists, skipping template copy."
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your API keys"
echo "2. Activate the virtual environment: source .venv/bin/activate"
echo "3. Run the agent: python fireworks_voice_agent.py start"
echo ""
echo "For testing in console mode: python fireworks_voice_agent.py console"
echo ""
echo "📚 See README.md for detailed usage instructions."
