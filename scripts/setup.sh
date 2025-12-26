set -e

echo "========================================"
echo "  Air Quality Monitor - Setup"
echo "========================================"
echo ""

# Check Python
echo "📦 Checking Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.9+"
    exit 1
fi
echo "✅ Python: $(python3 --version)"

# Check Node
echo "📦 Checking Node.js..."
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Please install Node.js 18+"
    exit 1
fi
echo "✅ Node: $(node --version)"

# Setup Backend
echo ""
echo "🐍 Setting up Backend..."
cd backend

if [ ! -d "venv" ]; then
    echo "   Creating virtual environment..."
    python3 -m venv venv
fi

echo "   Activating virtual environment..."
source venv/bin/activate

echo "   Installing dependencies..."
pip install -q -r requirements.txt

cd ..

# Setup Frontend
echo ""
echo "⚛️  Setting up Frontend..."
cd frontend

echo "   Installing dependencies..."
npm install --silent

cd ..

echo ""
echo "========================================"
echo "  ✅ Setup Complete!"
echo "========================================"
echo ""
echo "To start the application:"
echo ""
echo "  Terminal 1 (Backend):"
echo "    cd backend"
echo "    source venv/bin/activate"
echo "    python app.py --demo"
echo ""
echo "  Terminal 2 (Frontend):"
echo "    cd frontend"
echo "    npm run dev"
echo ""
echo "Then open: http://localhost:5173"
echo ""
