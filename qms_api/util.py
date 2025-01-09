import string, random
from django.db.models.signals import pre_save, post_migrate
from django.dispatch import receiver
from django.utils.text import slugify
from django.apps import apps
from django.db.models import Q
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _
from rest_framework.views import APIView
from django.contrib.auth.models import Group, Permission

from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.lib import colors
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Table,
    TableStyle,
    Image,
    Spacer,
)
from arabic_reshaper import arabic_reshaper
from bidi.algorithm import get_display
from io import BytesIO

from django.conf import settings
import os
from decimal import Decimal
import barcode
from barcode.writer import ImageWriter


def format_arabic_text(text):
    """Reshape and reorder Arabic text for proper rendering."""
    reshaped_text = arabic_reshaper.reshape(text)
    bidi_text = get_display(reshaped_text)
    return bidi_text


def generate_invoice_pdf(invoice):
    # Define the file path
    file_name = f"{invoice.id}.pdf"
    file_path = os.path.join(
        settings.MEDIA_ROOT, "uploads", "invoice", "pdf", file_name
    )

    # Ensure the directory exists
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # Define the path to the Arimo and NotoSansArabic font files
    font_path = os.path.join(settings.BASE_DIR, "fonts", "Arimo-Regular.ttf")
    arabic_font_path = os.path.join(
        settings.BASE_DIR, "fonts", "NotoSansArabic-VariableFont_wdth,wght.ttf"
    )

    # Check if the font files exist
    if not os.path.exists(font_path):
        raise FileNotFoundError(f"Font file not found at: {font_path}")
    if not os.path.exists(arabic_font_path):
        raise FileNotFoundError(f"Arabic font file not found at: {arabic_font_path}")

    # Register the fonts
    pdfmetrics.registerFont(TTFont("Arimo", font_path))
    pdfmetrics.registerFont(TTFont("NotoSansArabic", arabic_font_path))

    # Create the PDF document with adjusted margins
    pdf = SimpleDocTemplate(
        file_path, pagesize=A4, leftMargin=10, rightMargin=10
    )  # Reduced margins
    elements = []

    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        name="TitleStyle",
        parent=styles["Title"],
        fontSize=12,  # Reduced font size
        alignment=1,  # Center alignment
    )
    normal_style = ParagraphStyle(
        name="NormalStyle",
        parent=styles["Normal"],
        fontSize=7,  # Further reduced font size for better fit
        fontName="Arimo",  # Use Arimo for English text
    )
    arabic_style = ParagraphStyle(
        name="ArabicStyle",
        parent=styles["Normal"],
        fontSize=7,  # Further reduced font size for better fit
        fontName="NotoSansArabic",  # Use NotoSansArabic for Arabic text
        alignment=2,  # Right alignment for Arabic text
    )

    # Add logo
    logo_path = os.path.join(
        settings.MEDIA_ROOT, "default_photos", "quickStop-logo.png"
    )
    if os.path.exists(logo_path):
        logo = Image(
            logo_path, width=100, height=50
        )  # Adjust width and height as needed
        logo.hAlign = "LEFT"
        elements.append(logo)
        elements.append(Spacer(1, 12))

    # Add title
    elements.append(Paragraph("TAX INVOICE", title_style))
    elements.append(Spacer(1, 12))

    # Generate barcode
    barcode_class = barcode.get_barcode_class("code128")
    barcode_instance = barcode_class(str(invoice.id), writer=ImageWriter())
    barcode_buffer = BytesIO()
    barcode_instance.write(barcode_buffer)
    barcode_image = Image(barcode_buffer, width=200, height=50)
    elements.append(barcode_image)
    elements.append(Spacer(1, 12))

    # Add invoice details in the top right
    details = [
        ["INV NO:", invoice.id],
        ["Token No:", invoice.token_no],
        ["Company No:", invoice.company_number or ""],
        ["Date:", invoice.created_at.strftime("%d/%m/%Y %H:%M:%S")],
        ["Receipt No:", invoice.receipt_no or ""],
        ["Company Name:", invoice.company_name or ""],
        ["Contact Name:", invoice.contact_name],
        ["Contact No:", invoice.contact_no],
    ]
    details_table = Table(details, colWidths=[80, 180])  # Adjusted column widths
    details_table.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
                ("FONTNAME", (0, 0), (-1, -1), "Arimo"),  # Use Arimo for details
                ("FONTSIZE", (0, 0), (-1, -1), 7),  # Reduced font size
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    elements.append(details_table)
    elements.append(Spacer(1, 12))

    # Add line items
    line_items = [
        [
            "NO",
            "DEPARTMENT",
            "SERVICE NAME",
            "GOV FEE",
            "QTY",
            "GOV. TOTAL",
            "SERVICE",
            "TYPING",
            "ADDFEE",
            "VAT",
            "FINS",  # New column for fins
            "TOTAL",
            "REFNO 1",
            "REFNO 2",
            "REFNO 3",
        ]
    ]

    for index, item in enumerate(invoice.line_items.all(), start=1):
        department_name = (
            item.service.department.name if item.service.department else ""
        )
        service_name = item.service.name if item.service else ""
        gov_fee = f"{float(item.service.gov_fee):.2f}" if item.service else "0.00"
        gov_total = f"{float(item.gov_total):.2f}" if item.gov_total else "0.00"
        quantity = (
            int(item.quantity) if item.quantity else 0
        )  # Ensure quantity is an integer
        service_fee = float(item.service.service_fee) if item.service else 0.00
        typing_fee = float(item.service.typing_fee) if item.service else 0.00
        add_fee = float(item.service.add_fee) if item.service else 0.00
        vat = float(item.service.vat) if item.service else 0.00
        fins = float(item.fins) if item.fins else 0.00  # Get fins value

        # Calculate total with quantity applied to service_fee, typing_fee, add_fee, and vat
        total = f"{float(Decimal(gov_total) + Decimal(service_fee * quantity) + Decimal(typing_fee * quantity) + Decimal(add_fee * quantity) + Decimal(vat * quantity)):.2f}"

        ref_no1 = item.ref_no1 or ""
        ref_no2 = item.ref_no2 or ""
        ref_no3 = item.ref_no3 or ""

        line_items.append(
            [
                str(index),
                department_name,
                service_name,
                gov_fee,
                quantity,
                gov_total,
                f"{service_fee:.2f}",
                f"{typing_fee:.2f}",
                f"{add_fee:.2f}",
                f"{vat:.2f}",
                f"{fins:.2f}",  # Add fins value
                total,
                ref_no1,
                ref_no2,
                ref_no3,
            ]
        )

    # Define column widths for the line items table
    col_widths = [
        15,
        60,
        90,
        35,
        20,
        40,
        35,
        35,
        35,
        35,
        35,
        35,
        35,
        35,
        35,
    ]  # Adjusted widths

    # Create the line items table
    line_items_table = Table(line_items, colWidths=col_widths)
    line_items_table.setStyle(
        TableStyle(
            [
                # Header row styling
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Arimo"),  # Use Arimo for headers
                ("FONTSIZE", (0, 0), (-1, 0), 7),  # Reduced font size
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                # Body row styling
                ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
                # Cell padding
                ("PADDING", (0, 0), (-1, -1), 5),  # Add padding to all cells
                # Align text columns to the left
                ("ALIGN", (1, 1), (2, -1), "LEFT"),  # DEPARTMENT and SERVICE NAME
                # Align numeric columns to the right
                ("ALIGN", (3, 1), (-1, -1), "RIGHT"),  # GOV FEE, QTY, GOV. TOTAL, etc.
                # Font size for body
                ("FONTSIZE", (0, 1), (-1, -1), 7),  # Reduced font size
                # Wrap text for headers and cells
                (
                    "WORDWRAP",
                    (0, 0),
                    (-1, -1),
                    True,
                ),  # Enable text wrapping for all cells
            ]
        )
    )
    elements.append(line_items_table)
    elements.append(Spacer(1, 12))

    # Add totals and footer in a two-column layout
    totals_footer_table = Table(
        [
            [
                Paragraph(
                    format_arabic_text(
                        "المركز غير مسؤول عن أي معاملة بعد ثلاثة أيام من تاريخ الانجاز"
                    ),
                    arabic_style,
                ),
                Paragraph("Total Govt Fee:", normal_style),
                f"{float(invoice.total_gov_fee):.2f}",
            ],
            [
                Paragraph(
                    format_arabic_text(
                        "يرجى مراجعة بيانات المعاملة حيث اننا مسؤولون عنها قبل تسليمها للعمل"
                    ),
                    arabic_style,
                ),
                Paragraph("Total Service Fee:", normal_style),
                f"{float(invoice.total_service_fee):.2f}",
            ],
            [
                Paragraph(
                    "The Center is not responsible for any transaction after 3 Days from completion",
                    normal_style,
                ),
                Paragraph("Total Typing Fee:", normal_style),
                f"{float(invoice.total_typing_fee):.2f}",
            ],
            [
                Paragraph(
                    "Transaction revision is advised as we are responsible for it before delivering to labour authority",
                    normal_style,
                ),
                Paragraph("VAT:", normal_style),
                f"{float(invoice.vat):.2f}",
            ],
            [
                Paragraph("Telephone: +971 4 222 0013", normal_style),
                Paragraph("Total Additional Fee:", normal_style),
                f"{float(invoice.total_additional_fee):.2f}",
            ],
            [
                "",  # Empty cell for Arabic text or description
                Paragraph("Total Fins:", normal_style),  # Total Fins label
                f"{float(invoice.total_fins):.2f}",  # Total Fins value
            ],
            [
                Paragraph("Al Maktoum Hospital Rd - Al Wasl Deira", normal_style),
                Paragraph("Grand Total Fee:", normal_style),
                f"{float(invoice.grand_total):.2f}",
            ],
            [
                Paragraph("Dubai, UAE, P.O. Box: 40974", normal_style),
                "",  # Empty cell for alignment
                "",  # Empty cell for alignment
            ],
        ],
        colWidths=[250, 100, 100],  # Adjust column widths as needed
    )
    totals_footer_table.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),  # Align footer text to the left
                ("ALIGN", (1, 0), (2, -1), "RIGHT"),  # Align totals to the right
                ("FONTNAME", (0, 0), (-1, -1), "Arimo"),  # Use Arimo for all text
                ("FONTSIZE", (0, 0), (-1, -1), 7),  # Reduced font size
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    elements.append(totals_footer_table)

    # Build the PDF
    pdf.build(elements)

    # Return the file path relative to MEDIA_ROOT
    return os.path.join("uploads", "invoice", "pdf", file_name)


############################################################################################
def invoice_pdf_file_path(instance, filename):
    # Get the file extension
    ext = os.path.splitext(filename)[1]

    # Use the instance's ID as the filename
    filename = f"{instance.id}{ext}"

    # Return the file path
    return os.path.join("uploads", "invoice", "pdf", filename)


def random_string_generator(size=10, chars=string.ascii_lowercase + string.digits):
    return "".join(random.choice(chars) for _ in range(size))


def unique_slug_generator(instance, new_slug=None):
    if new_slug is not None:
        slug = new_slug
    else:
        slug = slugify(instance.name)
    Klass = instance.__class__
    max_length = Klass._meta.get_field("slug").max_length
    slug = slug[:max_length]
    qs_exists = Klass.objects.filter(slug=slug).exists()

    if qs_exists:
        new_slug = "{slug}-{randstr}".format(
            slug=slug[: max_length - 5], randstr=random_string_generator(size=4)
        )

        return unique_slug_generator(instance, new_slug=new_slug)
    return slug


class CheckFieldValueExistenceView(APIView):
    def get(self, request):
        field_name = request.GET.get("field")
        field_value = request.GET.get("value")

        if not field_name or not field_value:
            return JsonResponse(
                {
                    "detail": _(
                        "Field name and value are required in the query parameters."
                    )
                },
                status=400,
            )

        app_models = apps.get_models()

        # List to store model names where the field exists
        existing_models = []

        # Iterate through all models and check if the field exists
        for model in app_models:
            if hasattr(model, field_name):
                # Use Q objects to handle fields with the same name
                filter_query = Q(**{field_name: field_value})
                exists = model.objects.filter(filter_query).exists()
                if exists:
                    existing_models.append(model.__name__)

        if existing_models:
            message = _(
                "The value '{}' already exists in the following models: {}"
            ).format(field_value, ", ".join(existing_models))
            return JsonResponse({"is_exist": True, "detail": message}, status=200)
        else:
            message = _("The value '{}' does not exist in any model.").format(
                field_value
            )
            return JsonResponse({"is_exist": False, "detail": message}, status=200)


@receiver(post_migrate)
def create_initial_groups(sender, **kwargs):
    if sender.name == "user":
        # Create or get the 'admins' group
        admin_group, created = Group.objects.get_or_create(name="admins")

        # Assign all permissions to the 'admins' group
        all_permissions = Permission.objects.all()
        admin_group.permissions.set(all_permissions)

        # Create or get the 'normal' group
        normal_group, created = Group.objects.get_or_create(name="normal")

        # Assign view permissions to the 'normal' group
        # Assuming 'view' permissions are represented by the 'view' codename
        view_permissions = Permission.objects.filter(codename__startswith="view")
        normal_group.permissions.set(view_permissions)
