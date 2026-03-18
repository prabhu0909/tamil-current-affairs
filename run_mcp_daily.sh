#!/bin/bash
# MCP Daily Tamil Nadu News Gathering Script

echo "📰 Running MCP Daily Tamil Nadu News Gathering"
echo "============================================="

# Set environment
export LOCAL_DEV=true
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Start Redis if not running (assumes local installation)
if ! pgrep -x "redis-server" > /dev/null; then
    echo "🔄 Starting Redis server..."
    redis-server --daemonize yes --port 6379
    sleep 2
fi

# Start PostgreSQL if not running (Ubuntu/Debian)
if ! pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
    sudo service postgresql start > /dev/null 2>&1
fi

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
fi

echo "1. Testing MCP news gatherer..."
python3 -c "
from scraper.mcp_news_gatherer import MCPNewsGatherer
import time

print(f'🚀 Starting MCP gathering at {time.strftime(\"%Y-%m-%d %H:%M:%S\")}')

db_config = {
    'host': 'localhost',
    'database': 'newsdb',
    'user': 'postgres',
    'password': 'password'
}

try:
    gatherer = MCPNewsGatherer(db_config)
    gatherer.run_full_gathering()
    print('✅ MCP gathering completed successfully')
except Exception as e:
    print('❌ Error during gathering:', e)
"

echo ""
echo "2. Checking gathered news statistics..."
python3 -c "
import psycopg2
import datetime

# Get today's stats
today = datetime.date.today()

conn = psycopg2.connect(
    host='localhost',
    database='newsdb',
    user='postgres',
    password='password'
)
cur = conn.cursor()

# Count today's articles
cur.execute('SELECT COUNT(*) FROM news WHERE DATE(published_date) = %s', (today,))
today_count = cur.fetchone()[0]

# Count total articles
cur.execute('SELECT COUNT(*) FROM news')
total_count = cur.fetchone()[0]

# Get recent sources
cur.execute('SELECT source, COUNT(*) FROM news WHERE DATE(published_date) = %s GROUP BY source ORDER BY count DESC', (today,))
sources_today = cur.fetchall()

print(f'📊 Today\\''s gathering stats:')
print(f'   📰 New articles: {today_count}')
print(f'   📚 Total articles: {total_count}')
print(f'   🏛️  Sources gathered from:')
for source, count in sources_today[:5]:  # Top 5 sources
    print(f'      {source}: {count} articles')

# Check MCP stats
cur.execute('SELECT * FROM mcp_stats WHERE date = %s', (today,))
stats = cur.fetchone()
if stats:
    print(f'   🤖 MCP performance:')
    print(f'      Sources successful: {stats[2]}')
    print(f'      Articles found: {stats[3]}')
    print(f'      Processing time: {stats[7]}s')
else:
    print('   ❓ No MCP stats recorded (first run?)')

conn.close()
"

echo ""
echo "3. Starting background worker for continuous monitoring..."
# Start Celery worker in background
celery -A scraper.mcp_worker worker --loglevel=info --concurrency=2 &

echo "✅ Daily news gathering completed!"
echo ""
echo "🌐 Access news at: http://localhost:8000/news"
echo "🔄 Worker running in background for continuous updates"
echo ""

# Optional: Schedule next run (if not using cron)
if [ "$SCHEDULE_NEXT" = "true" ]; then
    echo "⏰ Scheduling next run in 24 hours..."
    sleep 86400 && ./run_mcp_daily.sh &
fi