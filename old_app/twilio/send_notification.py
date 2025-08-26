# !pip install twilio python-dotenv

from twilio.rest import Client

from config import Config

config = Config()

TWILIO_SID = config.TWILIO_SID
TWILIO_TOKEN = config.TWILIO_TOKEN
TWILIO_FROM = config.TWILIO_FROM


client = Client(TWILIO_SID, TWILIO_TOKEN)

def send_sms( body: str):
    """Send SMS from notebook"""
    message = client.messages.create(
        to="+61405784048",
        from_=TWILIO_FROM,
        body=body
    )
    return message.sid

# Example: send an alert
# send_sms("📈 XAUUSD Alert: Price broke above 2450")

