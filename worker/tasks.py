from celery import Celery
import os

celery = Celery(
    "tasks",
    broker="redis://redis:6379/0"
)

@celery.task
def run_scraper():

    os.system("python scraper/scraper.py")
