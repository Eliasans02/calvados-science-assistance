#!/bin/bash
# Dead Regulations Detector - Quick Launcher
# Decentrathon 5.0 Project

echo "🏛️  Dead Regulations Detector"
echo "=============================="
echo ""

# Activate virtual environment
source venv/bin/activate

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found. Creating from template..."
    cp .env.example .env
    echo "✅ Created .env file"
fi

# Check GitHub token
if command -v gh &> /dev/null; then
    if gh auth status &> /dev/null; then
        export GITHUB_TOKEN=$(gh auth token)
        echo "✅ GitHub Models enabled - FREE AI!"
    fi
fi

# Stop existing Streamlit
pkill -f "streamlit run" 2>/dev/null || true

# Run Streamlit
echo "🚀 Starting Streamlit dashboard..."
echo "📍 Open: http://localhost:8501"
echo "🛑 Press Ctrl+C to stop"
echo ""

# Auto-open browser after 2 seconds
(sleep 2 && open http://localhost:8501 2>/dev/null) &

streamlit run src/ui/app.py --server.port 8501

