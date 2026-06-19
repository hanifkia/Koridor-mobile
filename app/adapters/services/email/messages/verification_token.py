from app.adapters.services.email.base import BaseEmail


class VerificationEmailMessage(BaseEmail):
    subject = "Email Verification"
    template_file = "verification.html"

    def __init__(self, to: str, name: str, token: str):
        self.to = to
        self.name = name
        self.token = token
