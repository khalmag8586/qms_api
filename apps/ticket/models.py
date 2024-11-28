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

channel_layer = get_channel_layer()
class Ticket(models.Model):
    TICKET_STATUS_CHOICES = [
        ("waiting", _("Waiting")),
        ("in_progress", _("In Progress")),
        ("completed", _("Completed")),
    ]
    mobile_num_regex = RegexValidator(
        regex="^[0-9]{9,11}$",
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
        max_length=11,
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
            self.number = f"{self.service.symbol}-{today_date.strftime('%Y%m%d')}-{ticket_count_today}"
        super().save(*args, **kwargs)

    # def complete_ticket(self):
    #     """Mark this ticket as completed."""
    #     self.status = "completed"
    #     self.save()
    # def notify_ticket_update(self):
    #     """Send a WebSocket notification about this ticket's update."""
    #     channel_layer = get_channel_layer()
    #     data = {
    #         "type": "ticket.update",
    #         "ticket_id": str(self.id),
    #         "status": self.status,
    #         "customers_ahead": self.customers_ahead,
    #     }
    #     async_to_sync(channel_layer.group_send)(
    #         f"ticket_{self.id}",  # Group name, e.g., unique to this ticket or service
    #         {"type": "ticket_update", "data": data},
    #     )
@receiver(post_save, sender=Ticket)
def ticket_status_updated(sender, instance, **kwargs):
    """
    Notify the system about ticket updates.
    """
    # Handle notifications when a ticket is ahead
    if instance.status == "waiting":
        # Fetch all tickets waiting for the counter
        tickets = Ticket.objects.filter(counter_id=instance.counter_id, status="waiting").order_by("created_at")
        count = tickets.count()

        # Notify if one ticket is ahead
        if count == 1:
            ticket_ahead = tickets.first()
            async_to_sync(channel_layer.group_send)(
                "global_notifications",  # Notify all clients in global_notifications group
                {
                    "type": "ticket_ahead_notification",
                    "data": {
                        "ticket_number": ticket_ahead.number,
                        "service_name": ticket_ahead.service_name,
                        "customer_name": ticket_ahead.customer_name,
                    },
                },
            )

    # Notify tickets in progress
    if instance.status == "in_progress":
        async_to_sync(channel_layer.group_send)(
            "tickets_in_progress",  # Notify all clients in tickets_in_progress group
            {
                "type": "send_ticket_update",
                "message": {
                    "ticket_number": instance.number,
                    "counter_number": instance.counter.number if instance.counter else None,
                },
            },
        )
