import logging
logger = logging.getLogger(__name__)
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from ..core.config import settings

class EmailService:
    @staticmethod
    def send_email(to_email: str, subject: str, html_content: str) -> bool:
        if not settings.SMTP_HOST or not settings.SMTP_USERNAME or not settings.SMTP_PASSWORD:
            logger.info("[EmailService] SMTP settings are not fully configured. Email was not sent.")
            return False
            
        try:
            msg = MIMEMultipart()
            msg['From'] = settings.SMTP_SENDER or settings.SMTP_USERNAME
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(html_content, 'html'))
            
            # Setup server
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
            server.starttls()
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.sendmail(msg['From'], to_email, msg.as_string())
            server.quit()
            
            logger.info(f"[EmailService] Successfully sent email to {to_email}")
            return True
        except Exception as e:
            logger.info(f"[EmailService] Failed to send email to {to_email}: {e}")
            return False

    @staticmethod
    def send_2fa_code(to_email: str, code: str) -> bool:
        subject = "PowerCortex Security Verification Code"
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; padding: 20px; color: #333;">
                <h2 style="color: #1E3A8A;">PowerCortex Multi-Factor Authentication</h2>
                <p>Hello,</p>
                <p>A sign-in or security configuration request was initiated for your PowerCortex account.</p>
                <div style="background-color: #F3F4F6; padding: 15px; border-radius: 8px; font-size: 24px; font-weight: bold; letter-spacing: 2px; text-align: center; margin: 20px 0; color: #1E3A8A; border: 1px solid #E5E7EB;">
                    {code}
                </div>
                <p>Please enter this 6-digit verification code to complete your verification. This code is valid for 30 seconds.</p>
                <p style="font-size: 12px; color: #9CA3AF; margin-top: 40px;">This is an automated security message. Please do not reply to this email.</p>
            </body>
        </html>
        """
        return EmailService.send_email(to_email, subject, html_content)

    @staticmethod
    def send_reset_token(to_email: str, token: str) -> bool:
        subject = "PowerCortex Password Reset Request"
        reset_link = f"{settings.API_BASE_URL}/api/v1/auth/reset-password?token={token}"
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; padding: 20px; color: #333;">
                <h2 style="color: #1E3A8A;">PowerCortex Password Reset</h2>
                <p>Hello,</p>
                <p>We received a request to reset the password for your PowerCortex account.</p>
                <p>To reset your password, please use the following reset token:</p>
                <div style="background-color: #F3F4F6; padding: 15px; border-radius: 8px; font-family: monospace; font-size: 14px; word-break: break-all; margin: 20px 0; border: 1px solid #E5E7EB;">
                    {token}
                </div>
                <p>Alternatively, you can reset your password directly using this link:</p>
                <p><a href="{reset_link}" style="color: #1E3A8A; font-weight: bold;">Reset Password Link</a></p>
                <p>This token and link are valid for 15 minutes.</p>
                <p style="font-size: 12px; color: #9CA3AF; margin-top: 40px;">If you did not request a password reset, please ignore this email.</p>
            </body>
        </html>
        """
        return EmailService.send_email(to_email, subject, html_content)

