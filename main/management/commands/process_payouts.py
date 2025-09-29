# your_app/management/commands/process_payouts.py
from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.auth.models import User
from main.models import Transaction, Profile
from main.products_utils import send_product_payout
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Manually process payouts for successful transactions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--transaction-id',
            type=int,
            help='Process payout for a specific transaction ID',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Process all pending payouts',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be processed without actually sending payouts',
        )
        parser.add_argument(
            '--seller',
            type=str,
            help='Process payouts for a specific seller (username)',
        )

    def handle(self, *args, **options):
        transaction_id = options.get('transaction_id')
        process_all = options.get('all')
        dry_run = options.get('dry_run')
        seller_username = options.get('seller')
        
        if not settings.PAYPAL_ENABLE_PAYOUTS:
            self.stdout.write(
                self.style.WARNING('PAYPAL_ENABLE_PAYOUTS is set to False in settings. Payouts are disabled.')
            )
            return
        
        # Get transactions that need payout processing
        transactions = Transaction.objects.filter(
            status='successful',
            payout_status='pending'
        ).select_related('product__campaign__user__user')
        
        if transaction_id:
            transactions = transactions.filter(id=transaction_id)
            if not transactions.exists():
                self.stdout.write(
                    self.style.ERROR(f'No pending payout found for transaction ID {transaction_id}')
                )
                return
        
        if seller_username:
            try:
                # Since campaign.user is a Profile, we need to find the Profile for this username
                user = User.objects.get(username=seller_username)
                profile = Profile.objects.get(user=user)
                transactions = transactions.filter(product__campaign__user=profile)
            except (User.DoesNotExist, Profile.DoesNotExist):
                self.stdout.write(
                    self.style.ERROR(f'Seller with username {seller_username} not found')
                )
                return
        
        if not transactions.exists():
            self.stdout.write(
                self.style.WARNING('No pending payouts found.')
            )
            return
        
        self.stdout.write(
            self.style.SUCCESS(f'Found {transactions.count()} transaction(s) needing payout processing')
        )
        
        # Check for sellers without PayPal emails
        sellers_without_paypal = set()
        for transaction in transactions:
            seller_profile = transaction.product.campaign.user  # This is a Profile object
            
            if not seller_profile.paypal_email:
                sellers_without_paypal.add(seller_profile.user.username)
        
        if sellers_without_paypal:
            self.stdout.write(
                self.style.ERROR(
                    f'The following sellers need PayPal emails configured: {", ".join(sellers_without_paypal)}\n'
                    f'Please add PayPal emails to their profiles before processing payouts.'
                )
            )
            return
        
        # Process the transactions
        success_count = 0
        failure_count = 0
        
        for transaction in transactions:
            seller_profile = transaction.product.campaign.user  # This is a Profile object
            self.stdout.write(
                f"Processing transaction #{transaction.id}: "
                f"{transaction.product.name} - ${transaction.amount} "
                f"(Buyer: {transaction.buyer.username}, Seller: {seller_profile.user.username})"
            )
            
            if dry_run:
                seller_amount = float(transaction.amount) * 0.88
                self.stdout.write(
                    self.style.WARNING(
                        f'DRY RUN: Would process payout of ${seller_amount:.2f} '
                        f'to {seller_profile.paypal_email}'
                    )
                )
                continue
            
            # Process the payout
            success, error = send_product_payout(transaction)
            
            if success:
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully processed payout for transaction #{transaction.id}')
                )
                success_count += 1
            else:
                self.stdout.write(
                    self.style.ERROR(f'Failed to process payout for transaction #{transaction.id}: {error}')
                )
                failure_count += 1
        
        # Summary
        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'DRY RUN: Would have processed {transactions.count()} payouts')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Payout processing completed. Success: {success_count}, Failures: {failure_count}'
                )
            )




# process payouts command python manage.py process_payouts --all
# check seller with pending transaction python manage.py check_sellers --with-transactions