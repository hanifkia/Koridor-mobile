from abc import ABC
import asyncio
import logging
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
from app.adapters.services.email.transport.smtp import send_email
from app.adapters.services.email.transport.imap import append_to_sent_folder
from app.config.settings import settings

# Configure logging
logger = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).parent / "templates"
env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html", "xml"]),
)


class BaseEmail(ABC):
    subject: str
    template_file: str
    to: str

    def render(self) -> str:
        template = env.get_template(self.template_file)
        return template.render(**self.__dict__)

    async def send(self):
        try:
            if not settings.SENDING_EMAIL_ENABLED:
                logger.warning(
                    "Email sending is disabled (SENDING_EMAIL_ENABLED=False)"
                )
                return

            logger.info(
                f"Preparing to send email to {self.to} with subject: {self.subject}"
            )

            html = self.render()
            logger.debug(f"Email template rendered successfully")

            raw_message = await send_email(
                to_email=self.to,
                subject=self.subject,
                html=html,
            )
            logger.info(f"Email sent successfully to {self.to}")

            await append_to_sent_folder(raw_message)
            logger.info(f"Email archived in sent folder for {self.to}")

        except Exception as e:
            logger.error(f"Failed to send email to {self.to}: {str(e)}", exc_info=True)
            raise

    async def send_background(self):
        try:
            task = asyncio.create_task(self.send())
            logger.info(f"Background email task created for {self.to}")
        except Exception as e:
            logger.error(
                f"Failed to create background email task: {str(e)}", exc_info=True
            )
