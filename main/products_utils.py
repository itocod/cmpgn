# main/products_utils.py
import requests
import json
import logging
import uuid
from django.conf import settings
from django.utils import timezone
from .models import Transaction
import time

logger = logging.getLogger(__name__)

def get_paypal_access_token():
    """Get PayPal API access token"""
    auth_url = f"{settings.PAYPAL_API_BASE}/v1/oauth2/token"
    auth_data = {"grant_type": "client_credentials"}
    try:
        response = requests.post(
            auth_url,
            data=auth_data,
            auth=(settings.PAYPAL_CLIENT_ID, settings.PAYPAL_CLIENT_SECRET),
            timeout=30
        )
        response.raise_for_status()
        return response.json().get("access_token")
    except requests.exceptions.RequestException as e:
        logger.error(f"PayPal Auth Error: {str(e)}")
        return None

def create_paypal_order(product, buyer, quantity=1, request=None):
    """
    Create a PayPal order for a product purchase
    """
    access_token = get_paypal_access_token()
    if not access_token:
        return None, "Failed to authenticate with PayPal"

    amount = float(product.price) * quantity
    order_url = f"{settings.PAYPAL_API_BASE}/v2/checkout/orders"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
        "Prefer": "return=representation"
    }

    # Build absolute URLs for PayPal
    if request:
        base_url = f"{request.scheme}://{request.get_host()}"
        return_url = f"{base_url}/paypal/callback/"
        cancel_url = f"{base_url}/payment/failure/"
    else:
        return_url = "/paypal/callback/"
        cancel_url = "/payment/failure/"

    order_payload = {
        "intent": "CAPTURE",
        "purchase_units": [
            {
                "reference_id": f"product_{product.id}",
                "description": product.name[:127],
                "custom_id": f"user_{buyer.id}",
                "amount": {
                    "currency_code": "USD",
                    "value": f"{amount:.2f}",
                }
            }
        ],
        "application_context": {
            "brand_name": settings.PAYPAL_BRAND_NAME,
            "landing_page": "BILLING",
            "user_action": "PAY_NOW",
            "return_url": return_url,
            "cancel_url": cancel_url,
        },
    }

    try:
        response = requests.post(order_url, headers=headers, data=json.dumps(order_payload))
        response.raise_for_status()
        order_data = response.json()

        # Save transaction in DB
        tx_ref = order_data["id"]
        transaction = Transaction.objects.create(
            product=product,
            buyer=buyer,
            amount=amount,
            quantity=quantity,
            tx_ref=tx_ref,
            status="pending",
            paypal_order_id=tx_ref
        )

        return order_data, None
    except Exception as e:
        logger.error(f"PayPal Order Error: {str(e)}")
        return None, str(e)

def capture_paypal_order(order_id):
    """
    Capture an approved PayPal order
    """
    access_token = get_paypal_access_token()
    if not access_token:
        return None, "Failed to authenticate with PayPal"

    capture_url = f"{settings.PAYPAL_API_BASE}/v2/checkout/orders/{order_id}/capture"
    headers = {
        "Content-Type": "application/json", 
        "Authorization": f"Bearer {access_token}",
        "Prefer": "return=representation"
    }

    try:
        response = requests.post(capture_url, headers=headers)
        response.raise_for_status()
        return response.json(), None
    except Exception as e:
        logger.error(f"PayPal Capture Error: {str(e)}")
        return None, str(e)

# products_utils.py - Update the send_product_payout function
def send_product_payout(transaction):
    """
    Send payout for a product sale: 88% to campaign owner, 12% platform fee
    """
    if not getattr(settings, 'PAYPAL_ENABLE_PAYOUTS', False):
        return False, "Payouts are disabled"

    access_token = get_paypal_access_token()
    if not access_token:
        return False, "Failed to authenticate with PayPal"

    try:
        # Get the campaign owner (seller) from the product's campaign
        # Since campaign.user is a Profile, we access it directly
        seller_profile = transaction.product.campaign.user
            
        if not seller_profile.paypal_email:
            return False, f"Seller {seller_profile.user.username} has no PayPal email set in their profile"

        # Calculate amounts: 88% to seller, 12% platform fee
        total_amount = float(transaction.amount)
        platform_fee_percent = 12  # You keep 12%
        seller_percent = 88        # Seller gets 88%
        
        platform_cut = round(total_amount * (platform_fee_percent / 100), 2)
        seller_amount = round(total_amount * (seller_percent / 100), 2)

        # Verify the math adds up (should equal total_amount within rounding)
        if abs((platform_cut + seller_amount) - total_amount) > 0.02:
            return False, "Payout calculation error"

        payout_url = f"{settings.PAYPAL_API_BASE}/v1/payments/payouts"
        headers = {
            "Content-Type": "application/json", 
            "Authorization": f"Bearer {access_token}"
        }

        payout_payload = {
            "sender_batch_header": {
                "sender_batch_id": f"payout_{uuid.uuid4().hex}",
                "email_subject": "💰 You received a payout from Rallynex!",
                "email_message": f"Great news! You've received ${seller_amount} for your product '{transaction.product.name}'. Thank you for using Rallynex!"
            },
            "items": [
                {
                    "recipient_type": "EMAIL",
                    "amount": {
                        "value": f"{seller_amount:.2f}", 
                        "currency": "USD"
                    },
                    "receiver": seller_profile.paypal_email,
                    "note": f"Payout for: {transaction.product.name} (88% of ${total_amount:.2f})",
                    "sender_item_id": f"item_{transaction.id}_{int(time.time())}",
                }
            ],
        }

        response = requests.post(payout_url, headers=headers, data=json.dumps(payout_payload))
        response.raise_for_status()
        
        payout_data = response.json()
        transaction.payout_status = 'paid'
        transaction.payout_reference = payout_data.get('batch_header', {}).get('payout_batch_id')
        transaction.platform_fee = platform_cut  # Store the 12% fee
        transaction.payout_amount = seller_amount  # Store the 88% payout
        transaction.save()
        
        logger.info(f"Payout successful: ${seller_amount} sent to {seller_profile.paypal_email} for transaction {transaction.id}")
        return True, None
        
    except Exception as e:
        logger.error(f"PayPal Payout Error: {str(e)}")
        transaction.payout_status = 'failed'
        transaction.save()
        return False, str(e)