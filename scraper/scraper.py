import requests
from bs4 import BeautifulSoup
import psycopg2

from news_sources import sources
from ai_summary import summarize

conn = psycopg2.connect(
    host="db",
    database="newsdb",
    user="postgres",
    password="password"
)

cur = conn.cursor()

for src in sources:

    try:

        page = requests.get(src["url"])
        soup = BeautifulSoup(page.text,"html.parser")

        headlines = soup.find_all("a")[:20]

        for h in headlines:

            title = h.text.strip()

            if len(title) < 20:
                continue

            summary = summarize(title)

            cur.execute("""
            INSERT INTO news(title,summary,category,source,link)
            VALUES(%s,%s,%s,%s,%s)
            """,(title,summary,src["category"],src["name"],h.get("href")))

            conn.commit()

    except:
        pass
