import ssl
import logging
from aioimaplib import IMAP4_SSL
from app.config.settings import settings

logger = logging.getLogger(__name__)


async def append_to_sent_folder(raw_message: bytes):
    try:
        logger.info(
            f"Connecting to IMAP server {settings.IMAP_HOST}:{settings.IMAP_PORT}"
        )

        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        client = IMAP4_SSL(
            host=settings.IMAP_HOST, port=settings.IMAP_PORT, ssl_context=ssl_context
        )
        await client.wait_hello_from_server()

        logger.info(f"Logging in to IMAP as {settings.IMAP_USER}")
        await client.login(settings.IMAP_USER, settings.IMAP_PASSWORD)

        logger.info(f"Selecting mailbox: {settings.IMAP_SENT_FOLDER}")
        await client.select(mailbox=settings.IMAP_SENT_FOLDER)

        logger.info(f"Appending message to {settings.IMAP_SENT_FOLDER}")
        await client.append(
            mailbox=settings.IMAP_SENT_FOLDER,
            flags="\\Seen",
            date=None,
            message_bytes=raw_message,
        )

        await client.logout()
        logger.info(f"Message successfully archived in {settings.IMAP_SENT_FOLDER}")

    except Exception as e:
        logger.error(f"IMAP error: {str(e)}", exc_info=True)
        raise
