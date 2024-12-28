from django.db import models
from django.conf import settings

import uuid

from apps.department.models import Department
from user.models import User


class Counter(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    number = models.PositiveIntegerField(unique=True)
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
    departments = models.ManyToManyField(  # Change this to ManyToManyField
        Department, blank=True, related_name="counters"
    )
    employee = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

