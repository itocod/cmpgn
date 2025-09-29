# your_app/management/commands/check_sellers.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from main.models import Transaction, Profile

class Command(BaseCommand):
    help = 'Check which sellers need PayPal emails configured'

    def add_arguments(self, parser):
        parser.add_argument(
            '--with-transactions',
            action='store_true',
            help='Only show sellers with pending transactions',
        )

    def handle(self, *args, **options):
        with_transactions = options.get('with_transactions')
        
        if with_transactions:
            # Get sellers with pending transactions
            seller_profiles = set()
            pending_transactions = Transaction.objects.filter(
                status='successful', 
                payout_status='pending'
            ).select_related('product__campaign__user__user')
            
            for transaction in pending_transactions:
                seller_profile = transaction.product.campaign.user
                seller_profiles.add(seller_profile)
            
            sellers = list(seller_profiles)
            self.stdout.write(
                self.style.SUCCESS(f'Found {len(sellers)} seller(s) with pending transactions')
            )
        else:
            # Get all sellers (profiles who have created campaigns)
            sellers = Profile.objects.filter(user_campaigns__isnull=False).distinct()
            self.stdout.write(
                self.style.SUCCESS(f'Found {sellers.count()} seller(s) with campaigns')
            )
        
        for seller_profile in sellers:
            # Count pending transactions for this seller
            pending_count = Transaction.objects.filter(
                product__campaign__user=seller_profile,
                status='successful',
                payout_status='pending'
            ).count()
            
            if seller_profile.paypal_email:
                status = self.style.SUCCESS('✅ PayPal configured')
            else:
                status = self.style.ERROR('❌ Missing PayPal email')
            
            self.stdout.write(
                f"{seller_profile.user.username}: {status} | Pending payouts: {pending_count} | PayPal: {seller_profile.paypal_email or 'Not set'}"
            )