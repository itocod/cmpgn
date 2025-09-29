
import requests
import secrets
import string
from django.conf import settings

def generate_donation_reference():
    """Generate unique transaction reference"""
    chars = string.ascii_uppercase + string.digits
    return "DN_" + "".join(secrets.choice(chars) for _ in range(12))

def get_paypal_access_token():
    """Get PayPal access token"""
    url = "https://api-m.sandbox.paypal.com/v1/oauth2/token" if settings.PAYPAL_MODE == "sandbox" else "https://api-m.paypal.com/v1/oauth2/token"
    auth = (settings.PAYPAL_CLIENT_ID, settings.PAYPAL_CLIENT_SECRET)
    headers = {"Accept": "application/json", "Accept-Language": "en_US"}
    data = {"grant_type": "client_credentials"}
    response = requests.post(url, headers=headers, data=data, auth=auth)
    return response.json().get("access_token")

def create_paypal_order_with_split(amount, owner_email, return_url, cancel_url):
    """Create PayPal order with 95%-5% split"""
    access_token = get_paypal_access_token()
    url = "https://api-m.sandbox.paypal.com/v2/checkout/orders" if settings.PAYPAL_MODE == "sandbox" else "https://api-m.paypal.com/v2/checkout/orders"

    platform_fee = round(float(amount) * 0.05, 2)
    owner_amount = round(float(amount) * 0.95, 2)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }

    payload = {
        "intent": "CAPTURE",
        "purchase_units": [
            {
                "amount": {"currency_code": "USD", "value": str(owner_amount)},
                "payee": {"email_address": owner_email},
                "description": "Donation to campaign (95% to owner)"
            },
            {
                "amount": {"currency_code": "USD", "value": str(platform_fee)},
                "payee": {"email_address": settings.PAYPAL_PLATFORM_EMAIL},
                "description": "Platform fee (5%)"
            }
        ],
        "application_context": {
            "return_url": return_url,
            "cancel_url": cancel_url
        }
    }

    response = requests.post(url, headers=headers, json=payload)
    data = response.json()
    if response.status_code in [200, 201]:
        for link in data.get("links", []):
            if link["rel"] == "approve":
                return data["id"], link["href"]
    print("PayPal error:", data)
    return None, None

def capture_paypal_order(order_id):
    """Capture PayPal order"""
    access_token = get_paypal_access_token()
    url = f"https://api-m.sandbox.paypal.com/v2/checkout/orders/{order_id}/capture" if settings.PAYPAL_MODE == "sandbox" else f"https://api-m.paypal.com/v2/checkout/orders/{order_id}/capture"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    response = requests.post(url, headers=headers)
    data = response.json()
    if response.status_code in [200, 201] and data.get("status") == "COMPLETED":
        return data
    print("PayPal capture error:", data)
    return None
