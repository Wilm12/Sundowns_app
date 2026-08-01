from ..models import Supporter


class UpdateSupporterProfileService:
    """Application service for maintaining supporter profile information."""

    @staticmethod
    def update(supporter, **fields):
        for field, value in fields.items():
            setattr(supporter, field, value)
        supporter.save(update_fields=list(fields.keys()))
        return supporter
