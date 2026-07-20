"""Email delivery for account recovery (and future transactional mail).

Local/dev: logs the message (and recovery code) to the console — no SMTP needed.
Production: set SMTP_* env vars to send via a real mail server.
"""

from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Thin mailer. Never raises to the caller for optional SMTP failures in local."""

    def send(self, *, to: str, subject: str, body: str) -> bool:
        """Send an email. Returns True if delivered (or logged in local)."""
        if settings.environment == "local" and not settings.smtp_host:
            logger.info(
                "EMAIL (local, not sent)\nTo: %s\nSubject: %s\n\n%s",
                to,
                subject,
                body,
            )
            return True

        if not settings.smtp_host:
            logger.warning("SMTP not configured; email to %s was not sent", to)
            return False

        msg = EmailMessage()
        msg["From"] = settings.smtp_from or settings.vapid_subject.replace(
            "mailto:", ""
        )
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body)

        try:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
                if settings.smtp_use_tls:
                    server.starttls()
                if settings.smtp_user and settings.smtp_password:
                    server.login(settings.smtp_user, settings.smtp_password)
                server.send_message(msg)
            return True
        except OSError:
            logger.exception("Failed to send email to %s", to)
            return False

    def send_recovery_code(self, *, to: str, username: str, code: str) -> bool:
        """Send (or log) a password recovery code."""
        return self.send(
            to=to,
            subject="Your The Todo Way recovery code",
            body=(
                f"Hi {username},\n\n"
                f"Your recovery code is: {code}\n\n"
                f"It expires in {settings.recovery_code_ttl_minutes} minutes.\n"
                "If you did not request this, you can ignore this email.\n"
            ),
        )
