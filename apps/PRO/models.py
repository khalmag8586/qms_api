from django.db import models
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _
from django.conf import settings

import uuid


class PRO(models.Model):
    phone_num_regex = RegexValidator(
        regex="^[0-9]{9,20}$",
        message=_("Entered phone number isn't in a right format!"),
    )
    mobile_num_regex = RegexValidator(
        regex="^[0-9]{9,20}$",
        message=_("Entered mobile number isn't in a right format!"),
    )
    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    name = models.CharField(max_length=100)
    name_ar = models.CharField(max_length=100)
    mobile_number = models.CharField(
        validators=[mobile_num_regex],
        unique=True,
        max_length=20,
    )
    company_name = models.CharField(max_length=100, null=True, blank=True)
    company_number = models.CharField(
        null=True, blank=True, validators=[phone_num_regex], max_length=20
    )
    company_tax_number = models.CharField(max_length=100, null=True, blank=True)
    remarks = models.TextField(blank=True, null=True)
    commission_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="user_created_PRO",
        blank=True,
        null=True,
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="user_updated_PRO",
        blank=True,
        null=True,
    )
