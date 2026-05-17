"""User views for profile retrieval and updates."""

from rest_framework import generics, permissions

from .serializers import UserProfileSerializer


class UserProfileView(generics.RetrieveUpdateAPIView):
    """API endpoint for retrieving and updating the authenticated user's profile."""

    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user