# In api/africastalking_service.py

import africastalking
import os

# --- Initialize the SDK ---
# Fetch credentials from your .env file
username = os.getenv('AT_USERNAME')
api_key = os.getenv('AT_API_KEY')

# Initialize the SDK
africastalking.initialize(username, api_key)

# Initialize the SMS service, which we will use to send the OTP
sms = africastalking.SMS

def send_otp_sms(phone_number, otp_code):
    """
    Sends the OTP code to a user's phone number using Africa's Talking.
    """
    # Set the recipient's phone number in the correct international format
    recipients = [phone_number]

    # Set your message
    message = f"Your AfyaLink verification code is {otp_code}. It is valid for 5 minutes."

    # Set your shortCode or senderId.
    # If you do not have one, this will be "AFRICASTKNG" by default.
    sender = "AFRICASTKNG"

    try:
        # Send the message
        response = sms.send(message, recipients, sender)
        print("✅ SMS SENT: ", response)
        return True
    except Exception as e:
        print(f"❌ SMS FAILED: Something went wrong and we could not send the message. Error: {e}")
        return False