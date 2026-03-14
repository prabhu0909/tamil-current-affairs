import requests
from bs4 import BeautifulSoup
from ai.summarizer import summarize
import psycopg2

conn = psycopg2.connect(
    host="db",
    database="newsdb",
    user="postgres",
    password="password"
)

cur = conn.cursor()

url="https://www.thehindu.com/news/national/tamil-nadu/"

res=requests.get(url)

soup=BeautifulSoup(res.text,"html.parser")

articles=soup.select("h3 a")

for a in articles:

    title=a.text.strip()
    link=a['href']

    summary=summarize(title)

    cur.execute("""
    INSERT INTO news(title,summary,category,source,link)
    VALUES(%s,%s,%s,%s,%s)
    """,(title,summary,"தமிழ்நாடு","The Hindu",link))

conn.commit()
