from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.functions import Lower
from django.utils.crypto import salted_hmac

from .validators import validate_phone_number


class User(AbstractUser):
    phone = models.CharField("Телефон", max_length=30, blank=True, validators=[validate_phone_number])
    session_version = models.PositiveIntegerField(default=0, editable=False)

    class Meta(AbstractUser.Meta):
        constraints = [
            models.UniqueConstraint(
                Lower("email"),
                condition=~models.Q(email=""),
                name="accounts_user_unique_email",
                violation_error_message="Этот адрес уже используется.",
            ),
        ]

    def _get_session_auth_hash(self, secret=None):
        session_hash = super()._get_session_auth_hash(secret=secret)
        if self.session_version == 0:
            return session_hash
        return salted_hmac(
            "accounts.User.session_version",
            str(self.session_version),
            secret=session_hash,
            algorithm="sha256",
        ).hexdigest()
