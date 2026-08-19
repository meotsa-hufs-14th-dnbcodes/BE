from celery import shared_task

from . import services


@shared_task
def generate_retreatment_notifications_task():
    created = services.generate_retreatment_notifications()
    return {"created": created}


@shared_task
def generate_weekly_report_notifications_task():
    created = services.generate_weekly_report_notifications()
    return {"created": created}