from django.utils.translation import gettext_lazy as _
from django.shortcuts import get_object_or_404
from django.http import FileResponse, Http404
from django.conf import settings

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.throttling import UserRateThrottle
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework_simplejwt.authentication import JWTAuthentication

from apps.invoice.models import Invoice, InvoiceLineItem
from apps.invoice.serializers import (
    InvoiceSerializer,
    InvoiceDialogSerializer,
    InvoiceIsCancelledSerializer,
)
from apps.invoice.filters import InvoiceFilter

from qms_api.pagination import StandardResultsSetPagination
from qms_api.custom_permissions import HasPermissionOrInGroupWithPermission

import os


class InvoiceCreateView(generics.CreateAPIView):
    serializer_class = InvoiceSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, HasPermissionOrInGroupWithPermission]
    permission_codename = "invoice.add_invoice"

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        return Response(
            {"detail": _("Invoice created successfully")},
            status=status.HTTP_201_CREATED,
        )


class InvoiceListView(generics.ListAPIView):
    queryset = Invoice.objects.all().order_by("-created_at")
    serializer_class = InvoiceSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, HasPermissionOrInGroupWithPermission]
    permission_codename = "invoice.view_invoice"
    pagination_class = StandardResultsSetPagination
    filter_backends = [SearchFilter, OrderingFilter, DjangoFilterBackend]
    filterset_class = InvoiceFilter
    ordering_fields = [
        "id",
        "created_at",
        "contact_name",
        "contact_no",
    ]


class InvoiceRetrieve(generics.RetrieveAPIView):
    serializer_class = InvoiceSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, HasPermissionOrInGroupWithPermission]
    permission_codename = "invoice.view_invoice"
    lookup_field = "id"

    def get_object(self):
        invoice_id = self.request.query_params.get("invoice_id")
        invoice = get_object_or_404(Invoice, id=invoice_id)
        return invoice


class InvoiceCanceledListView(generics.ListAPIView):
    queryset = Invoice.objects.filter(is_cancelled=True).order_by("-created_at")
    serializer_class = InvoiceSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, HasPermissionOrInGroupWithPermission]
    permission_codename = "invoice.view_invoice"
    pagination_class = StandardResultsSetPagination
    filter_backends = [SearchFilter, OrderingFilter, DjangoFilterBackend]
    filterset_class = InvoiceFilter
    ordering_fields = [
        "id",
        "created_at",
        "contact_name",
        "contact_no",
    ]


class InvoiceUpdateview(generics.UpdateAPIView):
    serializer_class = InvoiceSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, HasPermissionOrInGroupWithPermission]
    permission_codename = "invoice.change_invoice"
    lookup_field = "id"

    def get_object(self):
        invoice_id = self.request.query_params.get("invoice_id")
        invoice = get_object_or_404(Invoice, id=invoice_id)
        return invoice

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(
            {"detail": _("Invoice Updated successfully")}, status=status.HTTP_200_OK
        )


class InvoiceCancelView(generics.UpdateAPIView):
    serializer_class = InvoiceIsCancelledSerializer
    permission_classes = [
        IsAuthenticated,
        HasPermissionOrInGroupWithPermission,
    ]  # Add authentication if required
    permission_codename = "invoice.change_invoice"

    lookup_field = "id"  # Use 'id' as the lookup field

    def get_object(self):
        # Get the invoice ID from query parameters
        invoice_id = self.request.query_params.get("invoice_id")
        invoice = get_object_or_404(Invoice, id=invoice_id)
        return invoice

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def update(self, request, *args, **kwargs):
        # Get the invoice instance
        instance = self.get_object()

        # Update the invoice fields
        instance.is_cancelled = True
        instance.receipt_no = ""  # Clear receipt_no
        instance.is_paid = False  # Ensure is_paid is False
        # Save the updated instance
        instance.save()

        return Response(
            {
                "detail": _("Invoice cancelled successfully"),
            },
            status=status.HTTP_200_OK,
        )


class InvoiceDeleteview(generics.DestroyAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, HasPermissionOrInGroupWithPermission]
    permission_codename = "invoice.delete_invoice"

    def delete(self, request, *args, **kwargs):
        invoice_ids = request.data.get("invoice_id", [])
        for invoice_id in invoice_ids:
            instance = get_object_or_404(Invoice, id=invoice_id)
            instance.delete()
        return Response(
            {"detail": _("Invoice permanently deleted successfully")},
            # status=status.HTTP_204_NO_CONTENT,
            status=status.HTTP_200_OK,
        )


class InvoiceDownloadPDFView(generics.RetrieveAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, HasPermissionOrInGroupWithPermission]
    permission_codename = "invoice.view_invoice"
    throttle_classes=[UserRateThrottle]
    lookup_field = "id"  # Use 'id' as the lookup field

    def get_object(self):
        invoice_id = self.request.query_params.get("invoice_id")
        invoice = get_object_or_404(Invoice, id=invoice_id)
        return invoice

    def retrieve(self, request, *args, **kwargs):
        # Fetch the invoice object
        invoice = self.get_object()

        # Get the file path from the invoice_pdf field
        file_path = os.path.join(settings.MEDIA_ROOT, str(invoice.invoice_pdf))

        # Check if the file exists
        if not os.path.exists(file_path):
            raise Http404("Invoice PDF not found")

        # Open the file and return it as a downloadable response
        try:
            response = FileResponse(
                open(file_path, "rb"), content_type="application/pdf"
            )
            response["Content-Disposition"] = (
                f'attachment; filename="{os.path.basename(file_path)}"'
            )
            return response
        except Exception as e:
            raise Http404("Error opening the file")


class InvoiceDialogView(generics.ListAPIView):
    queryset = Invoice.objects.filter(is_cancelled=False).order_by("-created_at")
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = InvoiceDialogSerializer
