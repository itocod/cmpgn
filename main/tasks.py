from background_task import background
from .cron import send_pledge_reminders

@background(schedule=0)
def run_pledge_reminders_task():
    send_pledge_reminders()
