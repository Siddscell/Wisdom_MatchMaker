"""send(to, subject, body) with two backends chosen by EMAIL_BACKEND.

outbox: the email is only recorded in email_outbox (viewable at /dev/outbox).
smtp:   the email is recorded in email_outbox and sent; sent_at is set on success.
"""

import logging
import smtplib
from datetime import UTC, datetime
from email.message import EmailMessage

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import EmailOutbox

log = logging.getLogger(__name__)


def send(db: Session, to: str, subject: str, body: str) -> None:
    row = EmailOutbox(to_email=to, subject=subject, body=body)
    db.add(row)
    settings = get_settings()
    if settings.EMAIL_BACKEND != "smtp":
        return
    message = EmailMessage()
    message["From"], message["To"], message["Subject"] = settings.SMTP_FROM, to, subject
    message.set_content(body)
    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as smtp:
            smtp.starttls()
            if settings.SMTP_USER:
                smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            smtp.send_message(message)
        row.sent_at = datetime.now(UTC)
    except (smtplib.SMTPException, OSError):
        # The outbox row (sent_at = null) keeps the email so it is not lost.
        log.exception("SMTP send to %s failed", to)
