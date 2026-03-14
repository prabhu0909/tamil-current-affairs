from celery.schedules import crontab

beat_schedule = {

"scrape-news-every-hour": {
"task": "tasks.run_scraper",
"schedule": crontab(minute=0)
}

}
