# paypal_utils.py - Updated with unique function names
import requests
import json
import base64
from django.conf import settings
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

def get_paypal_access_token():
    """Get PayPal API access token"""
    auth_url = f"{settings.PAYPAL_API_BASE}/v1/oauth2/token"
    auth_data = {"grant_type": "client_credentials"}
    auth_headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {base64.b64encode(f'{settings.PAYPAL_CLIENT_ID}:{settings.PAYPAL_CLIENT_SECRET}'.encode()).decode()}"
    }
    
    try:
        response = requests.post(auth_url, data=auth_data, headers=auth_headers)
        response.raise_for_status()
        return response.json()["access_token"]
    except requests.exceptions.RequestException as e:
        logger.error(f"Error getting PayPal access token: {e}")
        if hasattr(e, 'response') and e.response:
            logger.error(f"PayPal auth response: {e.response.text}")
        return None

def create_donation_paypal_order(amount, campaign_id, return_url, cancel_url):
    """Create a PayPal order for donation (unique name)"""
    access_token = get_paypal_access_token()
    if not access_token:
        logger.error("Failed to get PayPal access token for donation order creation")
        return None
    
    # Ensure amount is properly formatted
    try:
        amount_value = str(float(amount))
    except (ValueError, TypeError):
        logger.error(f"Invalid amount format for donation: {amount}")
        return None
    
    order_url = f"{settings.PAYPAL_API_BASE}/v2/checkout/orders"
    order_data = {
        "intent": "CAPTURE",
        "purchase_units": [
            {
                "amount": {
                    "currency_code": "USD",
                    "value": amount_value
                },
                "custom_id": f"donation_campaign_{campaign_id}",
                "description": f"Donation to campaign #{campaign_id}"
            }
        ],
        "application_context": {
            "return_url": return_url,
            "cancel_url": cancel_url,
            "brand_name": "RallyNex Platform",
            "user_action": "PAY_NOW"
        }
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
        "Prefer": "return=representation"
    }
    
    try:
        response = requests.post(order_url, json=order_data, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error creating donation PayPal order: {e}")
        if hasattr(e, 'response') and e.response:
            logger.error(f"PayPal donation order response: {e.response.text}")
        return None

def capture_donation_paypal_order(order_id):
    """Capture a PayPal payment for donation (unique name)"""
    access_token = get_paypal_access_token()
    if not access_token:
        logger.error("Failed to get PayPal access token for donation order capture")
        return None
    
    capture_url = f"{settings.PAYPAL_API_BASE}/v2/checkout/orders/{order_id}/capture"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
        "Prefer": "return=representation"
    }
    
    try:
        response = requests.post(capture_url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error capturing donation PayPal order {order_id}: {e}")
        if hasattr(e, 'response') and e.response:
            logger.error(f"PayPal donation capture response: {e.response.text}")
        return None

def send_donation_payout(recipient_email, amount, note, sender_item_id):
    """Send payout to recipient using PayPal Payouts for donations (unique name)"""
    access_token = get_paypal_access_token()
    if not access_token:
        logger.error("Failed to get PayPal access token for donation payout")
        return None
    
    payout_url = f"{settings.PAYPAL_API_BASE}/v1/payments/payouts"
    payout_data = {
        "sender_batch_header": {
            "sender_batch_id": f"donation_batch_{int(timezone.now().timestamp())}",
            "email_subject": "You received a donation payment!",
            "email_message": f"You have received a payment of ${amount} from RallyNex platform."
        },
        "items": [
            {
                "recipient_type": "EMAIL",
                "amount": {
                    "value": str(amount),
                    "currency": "USD"
                },
                "note": note,
                "receiver": recipient_email,
                "sender_item_id": sender_item_id
            }
        ]
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    
    try:
        response = requests.post(payout_url, json=payout_data, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error sending donation PayPal payout to {recipient_email}: {e}")
        if hasattr(e, 'response') and e.response:
            logger.error(f"PayPal donation payout response: {e.response.text}")
        return None

def process_donation_split(donation_amount):
    """Calculate the split between campaign owner and platform"""
    platform_share = round(float(donation_amount) * 0.10, 2)  # 10% to platform
    campaign_owner_share = round(float(donation_amount) * 0.90, 2)  # 90% to campaign owner
    
    return platform_share, campaign_owner_share