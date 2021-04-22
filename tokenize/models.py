import uuid

from django.db import models

from user import User


class TemporaryToken(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE
    )
    token = models.UUIDField(
        default=uuid.uuid4
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )
    called = models.BooleanField(
        default=False
    )
    uploaded = models.BooleanField(
        default=False
    )
