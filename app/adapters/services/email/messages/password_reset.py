from app.adapters.services.email.base import BaseEmail


class PasswordResetEmail(BaseEmail):
    subject = "Password Reset Verification Code"
    template_file = "password_reset.html"

    def __init__(self, to: str, name: str, code: str):
        self.to = to
        self.name = name
        self.code = code
