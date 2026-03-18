#!/bin/bash
# MCP Tamil Nadu News System Setup Script

echo "🛠️  Setting up MCP Tamil Nadu News Gathering System"
echo "=================================================="

# Set environment
export LOCAL_DEV=true
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Check system requirements
echo "1. Checking system requirements..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is required but not installed. Aborting."
    exit 1
fi

if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is required but not installed. Aborting."
    exit 1
fi

if ! command -v psql &> /dev/null; then
    echo "❌ PostgreSQL client is required but not installed. Aborting."
    exit 1
fi

# Create virtual environment if not exists
if [ ! -d "venv" ]; then
    echo "2. Creating Python virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
source venv/bin/activate
echo "3. Activated Python virtual environment"

# Upgrade pip
pip install --upgrade pip > /dev/null 2>&1
echo "4. Pip upgraded to latest version"

# Install Python dependencies
echo "5. Installing Python dependencies..."
pip install -r backend/requirements.txt

# Install additional MCP-specific dependencies
pip install pyyaml schedule transformers[torch] sentencepiece
echo "✅ All dependencies installed"

# Set up database
echo "6. Setting up PostgreSQL database..."
if ! pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
    echo "❌ PostgreSQL server is not running on localhost:5432"
    echo "Please start PostgreSQL service:"
    echo "   Ubuntu/Debian: sudo service postgresql start"
    echo "   macOS: brew services start postgresql"
    echo "   CentOS/RHEL: sudo systemctl start postgresql"
    echo ""
    echo "Or use Docker: docker run -d --name postgres -p 5432:5432 -e POSTGRES_PASSWORD=password postgres:15"
    exit 1
fi

# Create database and tables
echo "7. Creating database tables..."
python3 -c "
from scraper.mcp_news_gatherer import MCPNewsGatherer
import psycopg2

# Connect and create tables
conn = psycopg2.connect(
    host='localhost',
    database='newsdb',
    user='postgres',
    password='password'
)
cur = conn.cursor()

# Create enhanced tables for MCP system
cur.execute('''
CREATE TABLE IF NOT EXISTS news (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    summary TEXT,
    full_content TEXT,
    category TEXT,
    source TEXT,
    link TEXT UNIQUE,
    published_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fetched_via TEXT DEFAULT 'MCP',
    sentiment_score FLOAT,
    language_confidence FLOAT,
    summary_model TEXT DEFAULT 'MCP-AI',
    keywords TEXT[],
    region TEXT DEFAULT 'Tamil Nadu',
    is_verified BOOLEAN DEFAULT false,
    quality_score INTEGER DEFAULT 0,
    image_urls TEXT[]
);
''')

# Create MCP stats table
cur.execute('''
CREATE TABLE IF NOT EXISTS mcp_stats (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL DEFAULT CURRENT_DATE,
    sources_success INTEGER DEFAULT 0,
    articles_found INTEGER DEFAULT 0,
    articles_processed INTEGER DEFAULT 0,
    errors_count INTEGER DEFAULT 0,
    mcp_tools_used TEXT[],
    processing_time_seconds INTEGER DEFAULT 0,
    UNIQUE(date)
);
''')

# Create search index for faster queries
cur.execute('CREATE INDEX IF NOT EXISTS idx_news_published_date ON news(published_date);')
cur.execute('CREATE INDEX IF NOT EXISTS idx_news_category ON news(category);')
cur.execute('CREATE INDEX IF NOT EXISTS idx_news_source ON news(source);')

conn.commit()
conn.close()
echo "✅ Database and tables created"
"

# Test the system
echo "8. Running system tests..."
./test_mcp_run.sh

echo ""
echo "🎉 MCP Tamil Nadu News System Setup Complete!"
echo ""
echo "🚀 To start gathering news: ./run_mcp_daily.sh"
echo "🔄 To start worker: source venv/bin/activate && celery -A scraper.mcp_worker worker --loglevel=info"
echo "🌐 API available at: http://localhost:8000/news"
echo ""