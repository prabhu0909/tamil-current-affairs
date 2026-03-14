import time
import psycopg2
from fastapi import FastAPI

app = FastAPI()

conn = None

# wait until database is ready
while conn is None:
    try:
        conn = psycopg2.connect(
            host="db",
            database="newsdb",
            user="postgres",
            password="password"
        )
        print("Database connected")
    except:
        print("Waiting for database...")
        time.sleep(5)

cur = conn.cursor()

# auto create table if it doesn't exist
cur.execute("""
CREATE TABLE IF NOT EXISTS news (
    id SERIAL PRIMARY KEY,
    title TEXT,
    summary TEXT,
    category TEXT,
    source TEXT,
    link TEXT
);
""")

conn.commit()

# insert demo news if table empty
cur.execute("SELECT COUNT(*) FROM news")
count = cur.fetchone()[0]

if count == 0:
    cur.execute("""
    INSERT INTO news(title,summary,category,source,link)
    VALUES(
    'தமிழ்நாடு அரசு புதிய திட்டம்',
    'தமிழ்நாடு அரசு மாணவர்களுக்கு புதிய கல்வி உதவி திட்டம் அறிவித்துள்ளது',
    'தமிழ்நாடு',
    'Demo Source',
    'https://example.com'
    )
    """)
    conn.commit()
@app.get("/quiz")

def quiz():

    cur = conn.cursor()

    cur.execute("SELECT title FROM news ORDER BY RANDOM() LIMIT 1")

    row = cur.fetchone()

    from quiz import generate_quiz

    return generate_quiz(row[0])

@app.get("/news")
def get_news():

    cur = conn.cursor()

    cur.execute("""
    SELECT title,summary,category,source,link
    FROM news
    ORDER BY id DESC
    """)

    rows = cur.fetchall()

    return [
        {
            "title": r[0],
            "summary": r[1],
            "category": r[2],
            "source": r[3],
            "link": r[4]
        }
        for r in rows
    ]
