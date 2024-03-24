from django.db import models

import uuid
from apps.service.models import Service
from apps.ticket.models import Ticket
from django.core.validators import MaxValueValidator, MinValueValidator


class Rating(models.Model):
    id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        primary_key=True,
    )
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE)
    stars = models.PositiveBigIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    review = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:

        unique_together = (("ticket", "service"),)
        index_together = (("ticket", "service"),)
