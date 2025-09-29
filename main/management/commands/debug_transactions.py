# your_app/management/commands/debug_transactions.py
from django.core.management.base import BaseCommand
from main.models import Transaction

class Command(BaseCommand):
    help = 'Debug transaction relationships'

    def handle(self, *args, **options):
        transactions = Transaction.objects.filter(
            status='successful',
            payout_status='pending'
        )[:5]  # Just check first 5
        
        for transaction in transactions:
            self.stdout.write(f"Transaction ID: {transaction.id}")
            self.stdout.write(f"Product: {transaction.product.name}")
            self.stdout.write(f"Campaign: {transaction.product.campaign.title}")
            self.stdout.write(f"Campaign User: {transaction.product.campaign.user} (type: {type(transaction.product.campaign.user)})")
            
            # Check if user has profile
            user = transaction.product.campaign.user
            if hasattr(user, 'profile'):
                self.stdout.write(f"Profile exists: Yes")
                self.stdout.write(f"PayPal email: {user.profile.paypal_email}")
            else:
                self.stdout.write(f"Profile exists: No")
            
            self.stdout.write("---")