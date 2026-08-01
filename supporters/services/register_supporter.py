from ..models import Supporter


class RegisterSupporterService:
    """Application service for registering a new supporter aggregate."""

    @staticmethod
    def register(first_name, last_name, email, phone_number="", student_number="", university=""):
        return Supporter.objects.create(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone_number=phone_number,
            student_number=student_number,
            university=university,
        )
