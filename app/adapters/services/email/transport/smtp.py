import logging
from aiosmtplib import SMTP
from email.message import EmailMessage
from app.config.settings import settings

logger = logging.getLogger(__name__)


async def send_email(to_email: str, subject: str, html: str):
    try:
        message = EmailMessage()
        message["From"] = settings.FROM_EMAIL
        message["To"] = to_email
        message["Subject"] = subject
        message.set_content("This email requires an HTML capable client")
        message.add_alternative(html, subtype="html")

        logger.info(
            f"Connecting to SMTP server {settings.SMTP_HOST}:{settings.SMTP_PORT}"
        )

        async with SMTP(
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            use_tls=True,
            validate_certs=False,
        ) as smtp:
            logger.info(f"Logging in to SMTP as {settings.SMTP_USER}")
            await smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)

            logger.info(f"Sending email to {to_email}")
            await smtp.send_message(message)

        logger.info(f"Email successfully sent to {to_email}")
        return message.as_bytes()

    except Exception as e:
        logger.error(f"SMTP error sending to {to_email}: {str(e)}", exc_info=True)
        raise
