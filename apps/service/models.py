from django.db import models
from django.conf import settings

from decimal import Decimal
import uuid
from apps.department.models import Department


class Service(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    name = models.CharField(max_length=255, blank=True, null=True)
    name_ar = models.CharField(max_length=255, blank=True, null=True)
    service_symbol = models.CharField(max_length=2, unique=True)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="user_created_service",
        blank=True,
        null=True,
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="user_updated_service",
        blank=True,
        null=True,
    )
    #  Fields of fees
    gov_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    service_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    typing_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    add_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    vat = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    final_cost = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    department = models.ForeignKey(
        Department, related_name="department", on_delete=models.CASCADE
    )

    def save(self, *args, **kwargs):
        # Calculate final cost as cost + VAT
        if self.typing_fee is not None:
            vat_rate = Decimal("0.05")  # Use Decimal for the VAT rate
        self.vat = self.typing_fee * vat_rate
        self.final_cost = (
                self.gov_fee
                + self.service_fee
                + self.typing_fee
                + self.add_fee
                + self.vat
            )
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name or self.service_symbol
