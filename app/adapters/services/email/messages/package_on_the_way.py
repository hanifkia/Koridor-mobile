from app.adapters.services.email.base import BaseEmail


class PackageOnTheWayEmail(BaseEmail):
    subject = "Your Package is on the Way"
    template_file = "package_on_the_way.html"

    def __init__(self, to: str, name: str, id: str, time: str):
        self.to = to
        self.name = name
        self.id = id
        self.time = time
