from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.exceptions import ValidationError
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework_simplejwt.authentication import JWTAuthentication

from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db.models import Q, Max

from apps.ticket.models import Ticket
from apps.ticket.serializers import (
    TicketSerializer,
    CallNextCustomerSerializer,
    TicketRedirectSerializer,
)

from qms_api.pagination import StandardResultsSetPagination
from qms_api.custom_permissions import HasPermissionOrInGroupWithPermission
from apps.counter.models import Counter


class TicketCreateView(generics.CreateAPIView):
    serializer_class = TicketSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ticket = self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            TicketSerializer(ticket).data,
            status=status.HTTP_201_CREATED,
            headers=headers,
        )

    def perform_create(self, serializer):
        ticket_number = self.generate_ticket_number(
            serializer.validated_data["service"]
        )
        return serializer.save(number=ticket_number)

    def generate_ticket_number(self, service):
        service_symbol = service.service_symbol
        sequential_number = self.get_next_sequential_number(service)
        ticket_number = f"{service_symbol}-{sequential_number}"
        return ticket_number

    def get_next_sequential_number(self, service):
        current_date = timezone.now().date()
        latest_ticket_number = (
            Ticket.objects.filter(
                service=service,
                created_at__date=current_date,
                number__startswith=f"{service.service_symbol}-",
            )
            .order_by("-created_at")
            .first()
        )

        if not latest_ticket_number:
            return 1

        try:
            sequential_number = int(latest_ticket_number.number.split("-")[-1])
            return sequential_number + 1
        except (IndexError, ValueError):
            return 1


class TicketListView(generics.ListAPIView):
    queryset = Ticket.objects.all().order_by("-created_at")
    serializer_class = TicketSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, HasPermissionOrInGroupWithPermission]
    permission_codename = "ticket.view_ticket"

    pagination_class = StandardResultsSetPagination


class TicketRetrieveView(generics.RetrieveAPIView):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
    lookup_field = "id"

    def get_object(self):
        ticket_id = self.request.query_params.get("ticket_id")
        ticket = get_object_or_404(Ticket, id=ticket_id)
        return ticket


class CallNextCustomerView(generics.UpdateAPIView):
    queryset = Ticket.objects.all()
    serializer_class = CallNextCustomerSerializer  # Define the serializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, HasPermissionOrInGroupWithPermission]
    permission_codename = "ticket.change_ticket"

    def update(self, request, *args, **kwargs):
        counter_id = request.data.get("counter_id")

        # Validate the counter ID
        if not counter_id:
            return Response(
                {"detail": _("Counter ID is required.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        next_customer = self.get_next_customer(counter_id)

        if next_customer:
            current_customer = self.get_current_customer(counter_id)

            if current_customer:
                self.complete_ticket(current_customer)

            self.update_ticket(next_customer, counter_id)

            return Response(
                {
                    "detail": _("Next customer called successfully."),
                    "ticket_id": next_customer.id,
                    "counter_number": (
                        next_customer.counter.number if next_customer.counter else None
                    ),
                    "ticket_number": next_customer.number,
                },
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {"detail": _("No more customers in the queue.")},
                status=status.HTTP_404_NOT_FOUND,
            )

    def get_next_customer(self, counter_id):
        # Logic to get the next customer based on the counter's queue and current status
        # You might need to implement your own logic here based on your application's requirements
        next_customer = (
            Ticket.objects.filter(called_at__isnull=True).order_by("created_at").first()
        )
        return next_customer

    def get_current_customer(self, counter_id):
        # Logic to get the current customer being served at the counter
        # You might need to implement your own logic here based on your application's requirements
        current_customer = Ticket.objects.filter(
            Q(counter__employee=self.request.user) & Q(status="in_progress")
        ).first()
        return current_customer

    def update_ticket(self, ticket, counter_id):
        try:
            # Ensure the counter exists and is associated with the user
            counter = Counter.objects.get(id=counter_id, employee=self.request.user)

            # Update the ticket fields after it's called
            ticket.called_at = timezone.now()
            ticket.status = "in_progress"  # Assuming 'in_progress' is the status when the ticket is being served
            ticket.served_by = self.request.user
            ticket.counter = counter
            ticket.save()
        except Counter.DoesNotExist:
            raise ValidationError(
                {
                    "detail": _(
                        "Counter does not exist or is not associated with the logged-in user."
                    )
                }
            )

    def complete_ticket(self, ticket):
        """Mark a ticket as completed"""
        ticket.status = "completed"

        ticket.save()


class TicketRedirectToAnotherCounter(generics.UpdateAPIView):
    serializer_class = TicketRedirectSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, HasPermissionOrInGroupWithPermission]
    permission_codename = "ticket.change_ticket"

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        ticket_id = request.data.get("ticket_id")
        new_counter_id = request.data.get("new_counter_id")

        try:
            ticket = Ticket.objects.get(id=ticket_id)
            counter = Counter.objects.get(id=new_counter_id)

        except Ticket.DoesNotExist:
            return Response(
                {"detail": _("Ticket not found")}, status=status.HTTP_404_NOT_FOUND
            )
        except Counter.DoesNotExist:
            return Response(
                {"detail": _("Counter not found")}, status=status.HTTP_404_NOT_FOUND
            )
        # Update the counter for the ticket
        try:
            # ticket.counter = counter
            ticket.redirect_to = counter
            ticket.save()
        except ValueError:
            return Response(
                {"detail": _("Invalid counter ID provided")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {"detail": _("Ticket redirected successfully")}, status=status.HTTP_200_OK
        )
class TicketUpdateView(generics.RetrieveUpdateAPIView):
    serializer_class = TicketSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, HasPermissionOrInGroupWithPermission]
    permission_codename = "ticket.change_ticket"

    lookup_field = "id"

    def get_object(self):
        ticket_id = self.request.query_params.get("ticket_id")
        ticket = get_object_or_404(Ticket, id=ticket_id)
        return ticket

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(
            {"detail": _("Ticket Updated successfully")}, status=status.HTTP_200_OK
        )


class TicketInCounter(generics.ListAPIView):
    queryset = Ticket.objects.filter(status="in_progress")
    serializer_class = TicketSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, HasPermissionOrInGroupWithPermission]
    permission_codename = "ticket.view_ticket"

    pagination_class = StandardResultsSetPagination




class TicketDeleteView(generics.DestroyAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, HasPermissionOrInGroupWithPermission]
    permission_codename = "ticket.delete_ticket"

    def delete(self, request, *args, **kwargs):
        ticket_ids = request.data.get("ticket_id", [])
        for ticket_id in ticket_ids:
            instance = get_object_or_404(Ticket, id=ticket_id)
            instance.delete()

        return Response(
            {"detail": _("Ticket permanently deleted successfully")},
            status=status.HTTP_204_NO_CONTENT,
        )