#!/bin/bash

# Visa Platform Setup Script
# This script sets up the development environment for the visa platform

echo "🚀 Setting up Visa Platform Development Environment"
echo "=================================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+ first."
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18+ first."
    exit 1
fi

# Check if pip is installed
if ! command -v pip &> /dev/null; then
    echo "❌ pip is not installed. Please install pip first."
    exit 1
fi

echo "✅ Prerequisites check passed"

# Set up backend
echo ""
echo "📦 Setting up Backend (FastAPI + PostgreSQL)"
echo "============================================="

cd backend || exit 1

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Set up environment file
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cp ../.env.example .env
    echo "⚠️  Please update the .env file with your actual configuration values"
fi

# Initialize database (placeholder)
echo "Database setup will be done when you run migrations"
echo "Run: cd backend && alembic upgrade head"

cd ..

# Set up frontend
echo ""
echo "🎨 Setting up Frontend (Next.js + React)"
echo "========================================"

cd frontend || exit 1

# Install Node.js dependencies
echo "Installing Node.js dependencies..."
npm install

# Set up environment file
if [ ! -f ".env.local" ]; then
    echo "Creating .env.local file..."
    cat > .env.local << EOL
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
EOL
    echo "⚠️  Please update the .env.local file with your actual configuration values"
fi

cd ..

# Set up Docker environment
echo ""
echo "🐳 Setting up Docker Environment"
echo "================================="

if command -v docker &> /dev/null; then
    echo "Docker is installed. You can run:"
    echo "  docker-compose up -d"
    echo ""
    echo "To start all services in detached mode"
else
    echo "⚠️  Docker is not installed. Install Docker for full environment setup"
fi

echo ""
echo "🎉 Setup Complete!"
echo "=================="
echo ""
echo "To start the development environment:"
echo ""
echo "1. Start the backend (in a new terminal):"
echo "   cd backend"
echo "   source venv/bin/activate"
echo "   uvicorn src.main:app --reload"
echo ""
echo "2. Start the frontend (in a new terminal):"
echo "   cd frontend"
echo "   npm run dev"
echo ""
echo "3. Or start everything with Docker:"
echo "   docker-compose up"
echo ""
echo "4. Visit http://localhost:3000 to see the application"
echo ""
echo "📝 Next Steps:"
echo "  - Update .env files with your configuration"
echo "  - Run database migrations: cd backend && alembic upgrade head"
echo "  - Seed sample data: python backend/src/scripts/seed_data.py"
echo ""
echo "📚 Documentation:"
echo "  - README.md for project overview"
echo "  - TECH_STACK_ANALYSIS.md for technical details"
echo ""
echo "Happy coding! 🚀"