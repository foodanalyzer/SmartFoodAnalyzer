from celery import Celery

celery_app = Celery(
    "nutrition_worker",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
    include=["app.worker.tasks"]   # ✅ tells Celery where tasks live
)
celery_app.conf.task_serializer = "json"
celery_app.conf.result_serializer = "json"