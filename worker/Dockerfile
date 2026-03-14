FROM python:3.11

WORKDIR /app

RUN pip install celery redis requests beautifulsoup4 psycopg2-binary openai

COPY . .

CMD ["celery","-A","tasks","worker","--loglevel=info"]
