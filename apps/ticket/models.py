import uuid

from django.db import models
from django.db.models import Avg, F, ExpressionWrapper, fields
from django.conf import settings
from django.core.validators import RegexValidator
from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete


from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from apps.counter.models import Counter
from apps.service.models import Service

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from channels.layers import get_channel_layer

from collections import defaultdict


channel_layer = get_channel_layer()


class Ticket(models.Model):
    TICKET_STATUS_CHOICES = [
        ("waiting", _("Waiting")),
        ("in_progress", _("In Progress")),
        ("completed", _("Completed")),
    ]
    mobile_num_regex = RegexValidator(
        regex="^[0-9]{9,20}$",
        message=_("Entered mobile number isn't in a right format!"),
    )
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    number = models.CharField(max_length=20)
    created_at = models.DateTimeField(default=timezone.now)
    called_at = models.DateTimeField(blank=True, null=True)
    status = models.CharField(
        max_length=20, choices=TICKET_STATUS_CHOICES, default="waiting"
    )
    served_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True
    )
    counter = models.ForeignKey(
        Counter, on_delete=models.SET_NULL, blank=True, null=True
    )
    hold_reason = models.CharField(max_length=255, blank=True, null=True)
    redirect_to = models.ForeignKey(
        Counter,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="redirecting_tickets",
    )
    # customer info
    customer_name = models.CharField(max_length=255)
    customer_name_ar = models.CharField(max_length=255)
    nationality = models.CharField(max_length=255)
    mobile_number = models.CharField(
        validators=[mobile_num_regex],
        max_length=20,
    )
    email = models.EmailField(max_length=255)

    def __str__(self):
        return f"Ticket {self.number} - {self.service.name}"

    @property
    def customers_ahead(self):
        """
        Calculate the number of customers ahead of the current ticket
        """
        tickets_ahead = Ticket.objects.filter(
            service=self.service,
            created_at__lt=self.created_at,
            called_at__isnull=True,  # Exclude tickets that have been called
        ).count()
        return tickets_ahead

    @property
    def avg_wait_time(self):
        """
        Calculate the average wait time for the current ticket
        """
        # Filter tickets for the same service that have been called
        previous_tickets = Ticket.objects.filter(
            service=self.service,
            called_at__isnull=False,
            created_at__lt=self.created_at,
        )

        # Initialize total wait time and number of previous tickets
        total_wait_time = timezone.timedelta(0)
        num_previous_tickets = 0

        # Iterate through previous tickets to calculate total wait time
        for ticket in previous_tickets:
            # Calculate wait time only for tickets that are not in progress or waiting
            if ticket.status == "completed":
                wait_time = ticket.called_at - ticket.created_at
                total_wait_time += wait_time
                num_previous_tickets += 1

        # Calculate the average wait time
        if num_previous_tickets > 0:
            average_wait_time = total_wait_time / num_previous_tickets
            return (
                average_wait_time.total_seconds()
            )  # Return average wait time in seconds
        else:
            return 0

    def save(self, *args, **kwargs):
        # Generate ticket number with service symbol prefix and current date
        if not self.number:
            today_date = timezone.now().date()
            ticket_count_today = (
                Ticket.objects.filter(created_at__date=today_date).count() + 1
            )
            self.number = f"{self.service.service_symbol}-{today_date.strftime('%Y%m%d')}-{ticket_count_today}"
        super().save(*args, **kwargs)




in_progress_tickets = defaultdict(list)

@receiver(post_save, sender=Ticket)
def ticket_status_updated(sender, instance, **kwargs):
    # Fetch all current in-progress tickets
    all_in_progress_tickets = [
        {
            "ticket_number": t.number.split("-")[0] + "-" + t.number.split("-")[-1],
            "counter": t.counter.number if t.counter else None,
            "status": t.status,
        }
        for t in Ticket.objects.filter(status="in_progress")
    ]

    if instance.status == "in_progress":
        channel_layer = get_channel_layer()

        # Extract the first and last parts of the ticket number
        ticket_number_parts = instance.number.split("-")
        shortened_ticket_number = f"{ticket_number_parts[0]}-{ticket_number_parts[-1]}"

        # Send a message to the specific ticket's group (for TicketConsumer)
        async_to_sync(channel_layer.group_send)(
            f"ticket_{instance.id}",  # Use the ticket UUID as the group name
            {
                "type": "ticket_notification",
                "data": {
                    "ticket_number": shortened_ticket_number,
                    "counter": instance.counter.number if instance.counter else None,
                    "message": f"Your ticket {shortened_ticket_number} is now being served.",
                },
            },
        )

        # Remove duplicate entries based on the ticket number and counter
        unique_in_progress_tickets = {
            (ticket["counter"], ticket["ticket_number"]): ticket
            for ticket in all_in_progress_tickets
        }

        # Add new ticket if not already present
        unique_in_progress_tickets[(instance.counter.number, shortened_ticket_number)] = {
            "ticket_number": shortened_ticket_number,
            "counter": instance.counter.number,
            "status": instance.status,
        }

        # Convert back to a list
        in_progress_tickets["tickets_in_progress"] = list(unique_in_progress_tickets.values())

        # Send the updated tickets to the group
        async_to_sync(channel_layer.group_send)(
            "tickets_in_progress",  # Group for all tickets in "in_progress"
            {
                "type": "send_ticket_update",
                "message": in_progress_tickets["tickets_in_progress"],  # Send full list
            },
        )
