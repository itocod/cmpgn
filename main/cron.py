from django.core.mail import send_mail
from django.conf import settings
from .models import Pledge
from django.utils import timezone
from datetime import timedelta

def send_pledge_reminders():
    # Optional: only remind pledges older than 24 hours
    time_threshold = timezone.now() - timedelta(hours=24)
    pending_pledges = Pledge.objects.filter(is_fulfilled=False, timestamp__lte=time_threshold)

    for pledge in pending_pledges:
        if pledge.contact:
            send_mail(
                subject=f"Reminder: Complete your pledge for {pledge.campaign.title}",
                message=(
                    f"Hi {pledge.user.username},\n\n"
                    f"This is a reminder for your pledge of {pledge.amount} {getattr(pledge, 'currency', 'USD')} "
                    f"to '{pledge.campaign.title}' on RallyNex.\n\n"
                    f"Please complete your pledge here: "
                    f"{settings.SITE_URL}/campaigns/{pledge.campaign.id}/pay/\n\n"
                    f"From RallyNex"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[pledge.contact],
                fail_silently=False,  # Set to True in production if you don't want errors to stop cron
            )
            print(f"Sent reminder to {pledge.contact} for pledge {pledge.id}")
