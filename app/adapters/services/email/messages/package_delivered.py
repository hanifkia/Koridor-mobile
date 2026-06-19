from app.adapters.services.email.base import BaseEmail


class PackageDeliveredEmail(BaseEmail):
    subject = "Your Package Has Been Delivered"
    template_file = "package_delivered.html"

    def __init__(self, to: str, name: str, id: str):
        self.to = to
        self.name = name
        self.id = id
