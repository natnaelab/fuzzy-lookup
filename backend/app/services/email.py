import logging
import smtplib
import ssl
from email.message import EmailMessage

from ..config import settings

logger = logging.getLogger(__name__)


class EmailService:
    def is_configured(self) -> bool:
        return all(
            [
                settings.SMTP_HOST,
                settings.SMTP_PORT,
                settings.SMTP_USER,
                settings.SMTP_PASS,
                settings.SMTP_FROM,
            ]
        )

    def send_password_reset_email(
        self,
        to_email: str,
        reset_link: str,
        expiry_minutes: int,
    ) -> None:
        if not self.is_configured():
            if settings.is_development_env():
                logger.warning(
                    "SMTP is not configured. Password reset link for %s: %s",
                    to_email,
                    reset_link,
                )
                return
            raise RuntimeError("SMTP is not configured")

        message = EmailMessage()
        message["Subject"] = "Reset your password"
        message["From"] = settings.SMTP_FROM
        message["To"] = to_email
        message.set_content(
            (
                "We received a request to reset your password.\n\n"
                f"Reset link: {reset_link}\n\n"
                f"This link expires in {expiry_minutes} minutes.\n"
                "If you did not request this change, you can ignore this email."
            )
        )

        try:
            with smtplib.SMTP(
                settings.SMTP_HOST,
                settings.SMTP_PORT,
                timeout=20,
            ) as server:
                if settings.SMTP_USE_TLS:
                    server.starttls(context=ssl.create_default_context())
                server.login(settings.SMTP_USER, settings.SMTP_PASS)
                server.send_message(message)
        except Exception:
            logger.exception("Failed to send password reset email to %s", to_email)
            raise
