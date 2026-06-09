import os
import logging
from twilio.rest import Client

logger = logging.getLogger(__name__)

# Retrieve configuration from environment
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER")
TWILIO_TO_NUMBER = os.getenv("TWILIO_TO_NUMBER") # Fallback default on-duty engineer

class TwilioService:
    @staticmethod
    def _get_client():
        if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
            return None
        if "your_" in TWILIO_ACCOUNT_SID.lower() or "your_" in TWILIO_AUTH_TOKEN.lower():
            return None
        try:
            return Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        except Exception as e:
            logger.error(f"Failed to initialize Twilio client: {e}")
            return None

    @classmethod
    async def send_sms(cls, message: str, to_number: str = None) -> bool:
        """
        Sends an SMS notification using Twilio.
        """
        target_number = to_number or TWILIO_TO_NUMBER
        if not target_number:
            logger.warning("[Twilio Mock] SMS recipient phone number not configured.")
            target_number = "+1234567890"

        client = cls._get_client()
        if not client or not TWILIO_FROM_NUMBER:
            logger.info(f"[Twilio Mock] Sending SMS to {target_number}: {message}")
            return True

        try:
            client.messages.create(
                body=message,
                from_=TWILIO_FROM_NUMBER,
                to=target_number
            )
            logger.info(f"Successfully sent Twilio SMS to {target_number}")
            return True
        except Exception as e:
            logger.error(f"Failed to send Twilio SMS to {target_number}: {e}")
            # Fallback mock print
            logger.info(f"[Twilio Mock-Fallback] Sending SMS to {target_number}: {message}")
            return False

    @classmethod
    async def trigger_voice_call(cls, message: str, to_number: str = None) -> bool:
        """
        Triggers an automated voice call using Twilio.
        """
        target_number = to_number or TWILIO_TO_NUMBER
        if not target_number:
            logger.warning("[Twilio Mock] Voice call recipient phone number not configured.")
            target_number = "+1234567890"

        client = cls._get_client()
        if not client or not TWILIO_FROM_NUMBER:
            logger.info(f"[Twilio Mock] Triggering voice call to {target_number} with message: {message}")
            return True

        try:
            # We can use TwiML to speak the message
            twiml_instruction = f"<Response><Say voice='alice'>{message}</Say></Response>"
            client.calls.create(
                twiml=twiml_instruction,
                from_=TWILIO_FROM_NUMBER,
                to=target_number
            )
            logger.info(f"Successfully initiated Twilio Voice Call to {target_number}")
            return True
        except Exception as e:
            logger.error(f"Failed to trigger Twilio Voice Call to {target_number}: {e}")
            # Fallback mock print
            logger.info(f"[Twilio Mock-Fallback] Triggering voice call to {target_number} with message: {message}")
            return False
