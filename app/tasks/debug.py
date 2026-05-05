from app.celery_app import celery

@celery.task
def debug_task():
    print('Debug task executed')
    return "ok"

