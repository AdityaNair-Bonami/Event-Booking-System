"""
Celery tasks for email simulations
"""

from celery import Celery

# using Redis as the mailman who delivers the messages
celery_app = Celery("tasks", broker="redis://localhost:6379/0")


@celery_app.task
def send_booking_confirmation(email: str, event_title: str):
    print(f"CELERY TASK: Sending confirmation email to {email} for event '{event_title}'")


@celery_app.task
def notify_event_update(emails: list, event_title: str):
    for email in emails:
        print(f"CELERY TASK: Notifying {email} that the event '{event_title}' has been updated.")


