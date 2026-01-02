"""
Email service for sending magic links.
"""

import logging
from typing import Optional
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails."""

    def __init__(self):
        """Initialize email service."""
        self.smtp_host = settings.smtp_host
        self.smtp_port = settings.smtp_port
        self.smtp_user = settings.smtp_user
        self.smtp_password = settings.smtp_password
        self.from_email = settings.smtp_from_email or settings.smtp_user

    async def send_magic_link(
        self, email: str, magic_link: str, frontend_url: str = "http://localhost:3000"
    ) -> bool:
        """
        Send magic link email.

        Args:
            email: Recipient email address
            magic_link: Magic link token
            frontend_url: Frontend URL for constructing the full link

        Returns:
            True if sent successfully, False otherwise
        """
        if not all([self.smtp_host, self.smtp_user, self.smtp_password]):
            logger.warning("SMTP not configured, skipping email send")
            return False

        try:
            # Construct full magic link URL
            verify_url = f"{frontend_url}/verify?token={magic_link}"

            # Create email message
            message = MIMEMultipart("alternative")
            message["Subject"] = "Your TikTok Momentum Tracker Login Link"
            message["From"] = self.from_email
            message["To"] = email

            # Create HTML email body
            html_body = f"""
            <html>
              <body>
                <h2>Login to TikTok Keyword Momentum Tracker</h2>
                <p>Click the link below to sign in:</p>
                <p><a href="{verify_url}" style="background-color: #3B82F6; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">Sign In</a></p>
                <p>Or copy and paste this link into your browser:</p>
                <p>{verify_url}</p>
                <p>This link will expire in 15 minutes.</p>
                <p>If you didn't request this link, you can safely ignore this email.</p>
              </body>
            </html>
            """

            # Create plain text email body
            text_body = f"""
            Login to TikTok Keyword Momentum Tracker

            Click the link below to sign in:
            {verify_url}

            This link will expire in 15 minutes.

            If you didn't request this link, you can safely ignore this email.
            """

            # Attach parts
            text_part = MIMEText(text_body, "plain")
            html_part = MIMEText(html_body, "html")
            message.attach(text_part)
            message.attach(html_part)

            # Send email
            await aiosmtplib.send(
                message,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.smtp_user,
                password=self.smtp_password,
                start_tls=True,
            )

            logger.info(f"Magic link email sent to {email}")
            return True

        except Exception as e:
            logger.error(f"Error sending magic link email to {email}: {e}")
            return False

