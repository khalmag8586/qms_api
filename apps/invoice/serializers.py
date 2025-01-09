from django.utils.translation import gettext_lazy as _
from django.conf import settings

from rest_framework import serializers

from apps.invoice.models import Invoice, InvoiceLineItem

from qms_api.util import generate_invoice_pdf
import os



class InvoiceLineItemSerializer(serializers.ModelSerializer):
    # service details
    service_name = serializers.CharField(source="service.name", read_only=True)

    service_name_ar = serializers.CharField(source="service.name_ar", read_only=True)
    department_name = serializers.CharField(
        source="service.department.name", read_only=True
    )
    department_name_ar = serializers.CharField(
        source="service.department.name_ar", read_only=True
    )
    gov_fee = serializers.CharField(source="service.gov_fee", read_only=True)
    additional_fee = serializers.SerializerMethodField()
    service_fee = serializers.SerializerMethodField()
    calculated_fins = serializers.SerializerMethodField()
    vat = serializers.SerializerMethodField()
    typing_fee = serializers.SerializerMethodField()

    class Meta:
        model = InvoiceLineItem
        fields = [
            "id",
            "service",
            "service_name",
            "service_name_ar",
            "department_name",
            "department_name_ar",
            "gov_fee",
            "quantity",
            "gov_total",
            "service_fee",
            "typing_fee",
            "additional_fee",
            "vat",
            "fins",
            "calculated_fins",
            "ref_no1",
            "ref_no2",
            "ref_no3",
        ]
        read_only_fields = ["id", "gov_total"]

    def get_calculated_fins(self, obj):
        # Access fields using dot notation
        return str(float(obj.fins) * obj.quantity)

    def get_vat(self, obj):
        # Access fields using dot notation
        return str(float(obj.service.vat) * obj.quantity)

    def get_typing_fee(self, obj):
        return str(float(obj.service.typing_fee) * obj.quantity)

    def get_service_fee(self, obj):
        return str(float(obj.service.service_fee) * obj.quantity)

    def get_additional_fee(self, obj):
        return str(float(obj.service.add_fee) * obj.quantity)


class InvoiceSerializer(serializers.ModelSerializer):
    line_items = InvoiceLineItemSerializer(many=True)  # Nested serializer
    # user details
    created_at = serializers.SerializerMethodField()
    created_by_user_name = serializers.CharField(
        source="created_by.name", read_only=True
    )
    created_by_user_name_ar = serializers.CharField(
        source="created_by.name_ar", read_only=True
    )
    updated_at = serializers.SerializerMethodField()
    updated_by_user_name = serializers.CharField(
        source="updated_by.name", read_only=True
    )
    updated_by_user_name_ar = serializers.CharField(
        source="updated_by.name_ar", read_only=True
    )

    class Meta:
        model = Invoice
        fields = [
            "id",
            "token_no",
            "receipt_no",
            "is_paid",
            "group",
            "pro",
            "contact_name",
            "contact_no",
            "company_name",
            "company_number",
            "company_tax_number",
            "line_items",  # Include the nested line items
            "total_gov_fee",
            "total_service_fee",
            "total_typing_fee",
            "vat",
            "total_additional_fee",
            "total_fins",
            "grand_total",
            "is_cancelled",
            "pro_commission",
            "employee_commission",
            "system_commission",
            "invoice_pdf",
            "created_at",
            "created_by",
            "created_by_user_name",
            "created_by_user_name_ar",
            "updated_at",
            "updated_by",
            "updated_by_user_name",
            "updated_by_user_name_ar",
        ]
        read_only_fields = [
            "id",
            "is_cancelled",
            "is_paid",
            "created_at",
            "created_by",
            "updated_at",
            "updated-by",
        ]

    def get_created_at(self, obj):
        return obj.created_at.strftime("%Y-%m-%d")

    def get_updated_at(self, obj):
        return obj.updated_at.strftime("%Y-%m-%d")

    def validate(self, data):
        """Ensure PRO is provided if group is 'PRO'."""
        if data.get("group") == "PRO" and not data.get("pro"):
            raise serializers.ValidationError(
                {"pro": _("PRO ID must be provided when the group is set to PRO.")}
            )
        return data

    def create(self, validated_data):
        """Handle creation of Invoice with nested line items."""
        line_items_data = validated_data.pop("line_items", [])
        invoice = Invoice.objects.create(**validated_data)

        # Create and associate line items with the invoice
        for item_data in line_items_data:
            InvoiceLineItem.objects.create(invoice=invoice, **item_data)

        # Generate the PDF and save it to the media directory
        pdf_path = generate_invoice_pdf(invoice)
        invoice.invoice_pdf = pdf_path
        invoice.save(update_fields=["invoice_pdf"])

        return invoice

    def update(self, instance, validated_data):
        """Handle update of Invoice and nested line items."""
        line_items_data = validated_data.pop("line_items", [])  # Extract line items data

        # Delete the old PDF file if it exists
        if instance.invoice_pdf:
            old_pdf_path = os.path.join(settings.MEDIA_ROOT, instance.invoice_pdf.name)
            if os.path.exists(old_pdf_path):
                os.remove(old_pdf_path)

        # Update invoice fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Keep track of existing line items to delete those not in the update
        existing_line_items = instance.line_items.all()
        existing_line_items_ids = set(item.id for item in existing_line_items)
        updated_line_items_ids = set()

        # Update or create line items
        for item_data in line_items_data:
            line_item_id = item_data.get("id")
            if line_item_id:
                # Update existing line item
                line_item = InvoiceLineItem.objects.get(id=line_item_id, invoice=instance)
                for attr, value in item_data.items():
                    setattr(line_item, attr, value)
                line_item.save()
                updated_line_items_ids.add(line_item_id)
            else:
                # Create new line item
                InvoiceLineItem.objects.create(invoice=instance, **item_data)

        # Delete line items that were not included in the update
        for item in existing_line_items:
            if item.id not in updated_line_items_ids:
                item.delete()

        # Recalculate totals after updating line items
        instance.save()  # Trigger the save method in the Invoice model

        # Generate a new PDF with the updated data
        pdf_path = generate_invoice_pdf(instance)
        instance.invoice_pdf = pdf_path
        instance.save(update_fields=["invoice_pdf"])

        return instance


class InvoiceDialogSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = ["id"]


class InvoiceIsCancelledSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = ["is_cancelled"]
