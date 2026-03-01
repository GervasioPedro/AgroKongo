web: gunicorn run:app --workers 2 --threads 4 --timeout 120 --bind 0.0.0.0:$PORT
worker: celery -A celery_worker.celery worker --loglevel=info --concurrency=2
beat: celery -A celery_worker.celery beat --loglevel=info
