from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()


class EmailBackend(ModelBackend):
    def authenticate(
        self,
        request,
        username=None,
        password=None,
        **kwargs,
    ):
        email = kwargs.get("email")
        username_value = username or kwargs.get("username")

        if not email and not username_value:
            return None

        user = None

        if email:
            user = User.objects.filter(email__iexact=email).first()

        if user is None and username_value:
            if "@" in str(username_value):
                user = User.objects.filter(email__iexact=username_value).first()
            else:
                user = User.objects.filter(username=username_value).first()

        if user is None:
            return None

        if user.check_password(password):
            return user

        return None
