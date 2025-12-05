import logging
import os

import mailtrap as mt

logger = logging.getLogger(__name__)


def send_alert_email(to_email: str, to_name: str, subject: str, body: str) -> tuple[bool, str]:
    token = os.environ.get("MAILTRAP_TOKEN")
    if not token:
        logger.warning("MAILTRAP_TOKEN not set, email not sent")
        return False, "MAILTRAP_TOKEN not configured"
    try:
        mail = mt.Mail(
            sender=mt.Address(email="hello@demomailtrap.co", name="SafeGuard Alerts"),
            to=[mt.Address(email=to_email, name=to_name)],
            subject=subject,
            text=body,
            category="SafeGuard Alert",
        )
        client = mt.MailtrapClient(token=token)
        response = client.send(mail)
        logger.info("Email sent to %s: %s", to_email, response)
        return True, "sent"
    except Exception as e:
        logger.error("Email send failed: %s", e)
        return False, str(e)

