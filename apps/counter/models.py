from django.db import models
from django.conf import settings

import uuid

from apps.service.models import Service
from user.models import User


class Counter(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    number = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="counters_created_by",
        blank=True,
        null=True,
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="counters_updated_by",
        blank=True,
        null=True,
    )
    service = models.ForeignKey(
        Service, on_delete=models.SET_NULL, null=True, blank=True
    )
    employee = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

