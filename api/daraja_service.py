# In api/daraja_service.py

import requests
import os
from requests.auth import HTTPBasicAuth
import base64
from datetime import datetime

def get_daraja_access_token():
    """
    Requests an access token from the Safaricom Daraja API.
    """
    consumer_key = os.getenv('DARAJA_CONSUMER_KEY')
    consumer_secret = os.getenv('DARAJA_CONSUMER_SECRET')
    api_url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"

    try:
        response = requests.get(api_url, auth=HTTPBasicAuth(consumer_key, consumer_secret))
        response.raise_for_status()
        json_response = response.json()
        access_token = json_response.get('access_token')

        if not access_token:
            print("❌ DARAJA AUTH: Could not get access token.")
            return None

        print("✅ DARAJA AUTH: Successfully obtained access token.")
        return access_token

    except requests.exceptions.RequestException as e:
        print(f"❌ DARAJA AUTH: Request failed. Error: {e}")
        return None


# MODIFIED: The function now accepts the 'case' object to update it
def initiate_stk_push(case, phone_number, amount, account_reference, transaction_desc):
    """
    Initiates an M-Pesa STK Push and saves the CheckoutRequestID to the case.
    """
    access_token = get_daraja_access_token()
    if not access_token:
        return {"error": "Could not authenticate with Daraja."}

    api_url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
    headers = {"Authorization": f"Bearer {access_token}"}

    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    shortcode = os.getenv('DARAJA_BUSINESS_SHORTCODE')
    passkey = os.getenv('DARAJA_PASSKEY')
    password_string = f"{shortcode}{passkey}{timestamp}"
    password = base64.b64encode(password_string.encode('utf-8')).decode('utf-8')

    if phone_number.startswith('0'):
        phone_number = '254' + phone_number[1:]

    payload = {
        "BusinessShortCode": shortcode,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": str(amount),
        "PartyA": phone_number,
        "PartyB": shortcode,
        "PhoneNumber": phone_number,
        "CallBackURL": os.getenv('DARAJA_CALLBACK_URL'),
        "AccountReference": account_reference,
        "TransactionDesc": transaction_desc,
    }

    try:
        response = requests.post(api_url, json=payload, headers=headers)
        response.raise_for_status()
        response_json = response.json()

        # ✅ SAVE THE ID: Get the CheckoutRequestID from the response
        checkout_id = response_json.get('CheckoutRequestID')
        if checkout_id:
            case.checkout_request_id = checkout_id
            case.save()

        print("✅ STK PUSH: Request successful. Response:", response_json)
        return response_json
    except requests.exceptions.RequestException as e:
        print(f"❌ STK PUSH: Request failed. Error: {e}")
        return {"error": str(e)}