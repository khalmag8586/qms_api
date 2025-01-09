from django.urls import path

from apps.invoice.views import (
    InvoiceCreateView,
    InvoiceListView,
    InvoiceRetrieve,
    InvoiceCanceledListView,
    InvoiceUpdateview,
    InvoiceCancelView,
    InvoiceDownloadPDFView,
    InvoiceDeleteview,
    InvoiceDialogView,
)

app_name = "invoice"

urlpatterns = [
    path("invoice_create/", InvoiceCreateView.as_view(), name="create invoice"),
    path("invoice_list/", InvoiceListView.as_view(), name="invoice list"),
    path("invoice_retrieve/", InvoiceRetrieve.as_view(), name="invoice retrieve"),
    path(
        "invoice_canceled_list/",
        InvoiceCanceledListView.as_view(),
        name="invoice canceled list",
    ),
    path("invoice_update/", InvoiceUpdateview.as_view(), name="invoice update"),
    path("invoice_cancel/", InvoiceCancelView.as_view(), name="invoice cancel"),
    path(
        "invoice_download/", InvoiceDownloadPDFView.as_view(), name="invoice download"
    ),
    path("invoice_delete/", InvoiceDeleteview.as_view(), name="invoice delete"),
    path("invoice_dialog/", InvoiceDialogView.as_view(), name="invoice dialog"),
]
