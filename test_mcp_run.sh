#!/bin/bash
# Test script for MCP-powered Tamil Nadu news gathering

echo "🧪 Testing MCP News Gathering System"
echo "=================================="

# Set environment
export LOCAL_DEV=true
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

echo "1. Testing module imports..."
python3 -c "
try:
    from scraper.mcp_news_gatherer import MCPNewsGatherer
    from scraper.news_sources import sources, mcp_config
    from scraper.ai_summary_pro import generate_summary
    print('✅ All MCP modules imported successfully')
except ImportError as e:
    print('❌ Import error:', e)
"

echo ""
echo "2. Testing MCP configuration..."
python3 -c "
from scraper.news_sources import sources, mcp_config
print(f'📊 Configured sources: {len(sources)}')
print(f'🤖 MCP tools configured: {len(mcp_config[\"tools\"])}')
for tool in mcp_config['tools']:
    print(f'   - {tool[\"name\"]}: {\"enabled\" if tool.get(\"enabled\", True) else \"disabled\"}')
"

echo ""
echo "3. Testing AI summary..."
python3 -c "
from scraper.ai_summary_pro import generate_summary
test_content = 'தமிழ்நாடு அரசு மாணவர்களுக்கு புதிய கல்வி உதவி திட்டம் அறிவித்துள்ளது'
summary = generate_summary(test_content, 'தமிழ்நாடு')
print(f'📝 Test summary: {summary}')
"

echo ""
echo "4. Testing MCP news gatherer initialization..."
python3 -c "
from scraper.mcp_news_gatherer import MCPNewsGatherer
import os

db_config = {
    'host': 'localhost',
    'database': 'newsdb',
    'user': 'postgres',
    'password': 'password'
}

try:
    gatherer = MCPNewsGatherer(db_config)
    print('✅ MCP News Gatherer initialized successfully')
    print('🚀 Ready to gather from', len(gatherer._gather_from_source.__wrapped__ or []), 'source types')
except Exception as e:
    print('❌ Initialization error:', e)
"

echo ""
echo "5. Database connection test..."
python3 -c "
import psycopg2
try:
    conn = psycopg2.connect(
        host='localhost',
        database='newsdb',
        user='postgres',
        password='password'
    )
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM news')
    count = cur.fetchone()[0]
    print(f'✅ Database connected. Current news count: {count}')
    conn.close()
except Exception as e:
    print('❌ Database connection error:', e)
"

echo ""
echo "🎉 MCP News System Test Complete!"
echo "Run ./run_mcp_daily.sh to start gathering Tamil Nadu news"