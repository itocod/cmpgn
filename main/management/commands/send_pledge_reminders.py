from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail
from datetime import timedelta

from main.models import Pledge


class Command(BaseCommand):
    help = "Send email reminders to pledgers who haven't fulfilled their pledge"

    def handle(self, *args, **kwargs):
        # -------------------------
        # For testing: send to all pending pledges
        # -------------------------
        pledges_to_remind = Pledge.objects.filter(is_fulfilled=False)

        # Uncomment below lines for production (24-hour filter)
        # time_threshold = timezone.now() - timedelta(hours=24)
        # pledges_to_remind = Pledge.objects.filter(is_fulfilled=False, timestamp__lte=time_threshold)

        if not pledges_to_remind.exists():
            self.stdout.write("No pledges to remind.")
            return

        for pledge in pledges_to_remind:
            if "@" in pledge.contact:  # Only email
                subject = f"Reminder: Complete your pledge to {pledge.campaign.title}"
                body = (
                    f"Hi {pledge.user.username},\n\n"
                    f"Thank you for pledging ${pledge.amount} to '{pledge.campaign.title}'!\n"
                    f"Please complete your pledge by visiting your campaign page:\n\n"
                    f"https://localhost:8000/pledge-payment/{pledge.id}/\n\n"  # Clickable link
                    "Best regards,\n"
                    "RallyNex Team"
                )
                try:
                    send_mail(
                        subject=subject,
                        message=body,
                        from_email="no-reply@rallynex.com",
                        recipient_list=[pledge.contact],
                        fail_silently=False
                    )
                    self.stdout.write(f"Reminder sent to {pledge.contact}")
                except Exception as e:
                    self.stdout.write(f"Failed to send email to {pledge.contact}: {e}")
