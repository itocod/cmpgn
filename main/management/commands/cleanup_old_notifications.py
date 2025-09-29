from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from main.models import Notification  # Adjust import based on your app structure

class Command(BaseCommand):
    help = 'Deletes notifications older than 30 days'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Delete notifications older than this number of days (default: 30)',
        )

    def handle(self, *args, **options):
        days = options['days']
        cutoff_date = timezone.now() - timedelta(days=days)
        
        # Delete old notifications (hard delete)
        deleted_count, _ = Notification.objects.filter(
            timestamp__lt=cutoff_date
        ).delete()
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully deleted {deleted_count} notifications older than {days} days')
        )