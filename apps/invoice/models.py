from django.db import models
from django.db.models import Sum, F
from django.conf import settings
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _
from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete


from apps.service.models import Service
from apps.PRO.models import PRO

import os
from decimal import Decimal


from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from qms_api.util import invoice_pdf_file_path, generate_invoice_pdf


class Invoice(models.Model):
    GROUP_CHOICES = [
        ("PRO", "PRO"),
        ("Normal", "Normal"),
    ]
    phone_num_regex = RegexValidator(
        regex="^[0-9]{9,20}$",
        message=_("Entered phone number isn't in a right format!"),
    )
    mobile_num_regex = RegexValidator(
        regex="^[0-9]{9,20}$",
        message=_("Entered mobile number isn't in a right format!"),
    )
    id = models.CharField(max_length=20, primary_key=True, editable=False)
    token_no = models.CharField(max_length=50)  # ticket number
    receipt_no = models.CharField(max_length=50, null=True, blank=True)
    group = models.CharField(max_length=10, choices=GROUP_CHOICES, default="Normal")
    pro = models.ForeignKey(
        PRO, blank=True, null=True, related_name="pros", on_delete=models.SET_NULL
    )
    # customer info
    contact_name = models.CharField(max_length=255)
    contact_no = models.CharField(
        validators=[mobile_num_regex],
        max_length=20,
    )
    company_name = models.CharField(max_length=100, null=True, blank=True)
    company_number = models.CharField(
        null=True, blank=True, validators=[phone_num_regex], max_length=20
    )
    company_tax_number = models.CharField(null=True, blank=True, max_length=100)
    # fees totals
    total_gov_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    total_service_fee = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.0
    )
    total_typing_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    vat = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    total_additional_fee = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.0
    )
    total_fins = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    grand_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    is_cancelled = models.BooleanField(default=False)
    is_paid = models.BooleanField(default=False)
    pro_commission = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    employee_commission = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.0
    )
    system_commission = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    # invoice pdf
    invoice_pdf = models.FileField(
        upload_to=invoice_pdf_file_path, blank=True, null=True
    )

    # creation info
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="invoice_created_by",
        blank=True,
        null=True,
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="invoice_updated_by",
        blank=True,
        null=True,
    )

    def save(self, *args, **kwargs):
        if not self.id:
            # Fetch the last invoice
            last_invoice = Invoice.objects.order_by("-created_at").first()
            if last_invoice and last_invoice.id.startswith("INV"):
                last_number = int(last_invoice.id[3:])  # Extract the numeric part
                new_number = last_number + 1
            else:
                new_number = 1
            self.id = f"INV{new_number:09d}"  # Format as INV followed by 9-digit number

        # Calculate totals based on line items
        self.total_gov_fee = sum(
            Decimal(item.gov_total) for item in self.line_items.all()
        )
        self.total_service_fee = sum(
            Decimal(item.quantity) * Decimal(item.service.service_fee)
            for item in self.line_items.all()
        )
        self.total_typing_fee = sum(
            Decimal(item.quantity) * Decimal(item.service.typing_fee)
            for item in self.line_items.all()
        )
        self.total_additional_fee = sum(
            Decimal(item.quantity) * Decimal(item.service.add_fee)
            for item in self.line_items.all()
        )
        self.vat = sum(
            Decimal(item.quantity) * Decimal(item.service.vat)
            for item in self.line_items.all()
        )
        self.total_fins = sum(Decimal(item.fins) for item in self.line_items.all())

        self.grand_total = (
            self.total_gov_fee
            + self.total_service_fee
            + self.total_typing_fee
            + self.total_additional_fee
            + self.vat
            + self.total_fins
        )

        # Reset commissions if the invoice is cancelled
        if self.is_cancelled:
            self.pro_commission = Decimal(0)
            self.employee_commission = Decimal(0)
            self.system_commission = Decimal(0)
        else:
            # Calculate commissions only if the invoice is not cancelled
            if self.group == "PRO" and self.pro:
                self.pro_commission = (
                    Decimal(self.pro.commission_percentage)
                    / Decimal(100)
                    * self.total_typing_fee
                )
                self.employee_commission = Decimal(0.25) * self.total_typing_fee
                self.system_commission = self.total_typing_fee - (
                    self.pro_commission + self.employee_commission
                )
            elif self.group == "Normal" and not self.pro:
                self.pro_commission = Decimal(0)
                self.employee_commission = Decimal(0.5) * self.total_typing_fee
                self.system_commission = self.total_typing_fee - (
                    self.pro_commission + self.employee_commission
                )

        super().save(*args, **kwargs)


class InvoiceLineItem(models.Model):
    invoice = models.ForeignKey(
        Invoice, related_name="line_items", on_delete=models.CASCADE
    )
    service = models.ForeignKey(
        Service, blank=True, related_name="services", on_delete=models.CASCADE
    )
    quantity = models.PositiveIntegerField(default=1)
    gov_total = models.DecimalField(max_digits=10, decimal_places=2)
    fins = models.DecimalField(max_digits=10, decimal_places=2)
    ref_no1 = models.CharField(max_length=255, blank=True, null=True)
    ref_no2 = models.CharField(max_length=255, blank=True, null=True)
    ref_no3 = models.CharField(max_length=255, blank=True, null=True)

    def save(self, *args, **kwargs):
        self.gov_total = Decimal(self.service.gov_fee) * self.quantity
        super().save(*args, **kwargs)
        # Trigger invoice save to update totals
        if self.invoice:
            self.invoice.save()


@receiver(post_save, sender=InvoiceLineItem)
def send_invoice_notification(sender, instance, created, **kwargs):
    if created:
        invoice = instance.invoice
        # Serialize line items
        line_items = [
            {
                "service_name": item.service.name,
                "quantity": item.quantity,
                "gov_total": str(item.gov_total),
                "fins": str(item.fins),
            }
            for item in invoice.line_items.all()
        ]

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "invoice_notifications",  # Group name
            {
                "type": "invoice_created",
                "message": {
                    "id": invoice.id,
                    "token_no": invoice.token_no,
                    "contact_name": invoice.contact_name,
                    "contact_no": invoice.contact_no,
                    "is_paid": invoice.is_paid,
                    "is_cancelled": invoice.is_cancelled,
                    "created_at": invoice.created_at.isoformat(),
                    "line_items": line_items,  # Include line items
                },
            },
        )

@receiver(post_delete, sender=Invoice)
def delete_invoice_pdf(sender, instance, **kwargs):
    """Delete the associated PDF file when an invoice is deleted."""
    if instance.invoice_pdf:
        pdf_path = os.path.join(settings.MEDIA_ROOT, instance.invoice_pdf.name)
        if os.path.exists(pdf_path):
            os.remove(pdf_path)