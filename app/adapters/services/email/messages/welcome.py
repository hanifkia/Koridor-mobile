from app.adapters.services.email.base import BaseEmail


class WelcomeEmail(BaseEmail):
    subject = "Welcome to Ecolosplus!"
    template_file = "welcome.html"

    def __init__(self, to: str, name: str):
        self.to = to
        self.name = name
