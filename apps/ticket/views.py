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
        # Here you can customize the ticket number generation logic based on your requirements
        # For example, you can generate the ticket number with a prefix and the current date
        ticket_number = self.generate_ticket_number(
            serializer.validated_data["service"]
        )
        return serializer.save(number=ticket_number)

    def generate_ticket_number(self, service):
        # Get the service symbol
        service_symbol = (
            service.service_symbol
        )  # Assuming 'symbol' is a field in the Service model

        # Get the current date
        current_date = timezone.now().strftime("%Y%m%d")  # Format: YYYYMMDD

        # Logic to generate a unique identifier (you can use anything here, like a counter)
        # For simplicity, let's use a sequential number starting from 1
        # You might want to enhance this logic based on your requirements
        sequential_number = self.get_next_sequential_number(service)

        # Construct the ticket number using the service symbol, current date, and sequential number
        ticket_number = f"{service_symbol}-{sequential_number}"

        return ticket_number

    def get_next_sequential_number(self, service):
        # Get the current date in YYYYMMDD format
        current_date = timezone.now().strftime("%Y%m%d")

        # Query to get the latest ticket number for the service on the current date
        latest_ticket_number = Ticket.objects.filter(
            service=service,
            created_at__date=timezone.now().date(),
            number__startswith=service.service_symbol + "-",
        ).aggregate(Max("number"))["number__max"]

        # If there are no tickets for the service on the current date, start from 1
        if not latest_ticket_number:
            return 1

        # Extract the sequential number from the latest ticket number
        # Format: SYMBOL-YYYYMMDD-SEQUENTIAL_NUMBER
        # Split the ticket number by '-' and get the last part which is the sequential number
        parts = latest_ticket_number.split("-")
        if len(parts) == 2:  # Ensure the split result contains three parts
            _, sequential_number = parts
            next_sequential_number = int(sequential_number) + 1
        else:
            # Handle the case where the latest ticket number format is incorrect
            next_sequential_number = 1

        return next_sequential_number


class TicketListView(generics.ListAPIView):
    queryset = Ticket.objects.all()
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
        # # Get the logged-in user
        # user = request.user

        # # Get the counter ID associated with the logged-in user
        # try:
        #     counter_id = user.counter.id
        # except Counter.DoesNotExist:
        #     return Response(
        #         {"detail": _("Counter does not exist for the logged-in user")},
        #         status=status.HTTP_404_NOT_FOUND,
        #     )

        # Get the counter ID from the request data
        counter_id = request.data.get("counter_id")

        # Logic to find the next customer based on the counter's queue and current status
        next_customer = self.get_next_customer(counter_id)

        if next_customer:
            # Check if there is a customer currently being served
            current_customer = self.get_current_customer(counter_id)

            if current_customer:
                # Complete the current customer before moving to the next one
                self.complete_ticket(current_customer)

            # Update the next customer
            self.update_ticket(next_customer)

            return Response(
                {"detail": _("Next customer called successfully")},
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {"detail": _("No more customers in the queue")},
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

    def update_ticket(self, ticket):
        try:
            # Update the ticket fields after it's called
            ticket.called_at = timezone.now()
            ticket.status = "in_progress"  # Assuming 'in_progress' is the status when the ticket is being served
            ticket.served_by = self.request.user
            ticket.counter = Counter.objects.get(employee=self.request.user)
            ticket.save()
        except Counter.DoesNotExist:
            raise ValidationError(
                {"detail": _("Counter does not exist for the logged-in user.")}
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


class TicketInCounter(generics.ListAPIView):
    queryset = Ticket.objects.filter(status="in_progress")
    serializer_class = TicketSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, HasPermissionOrInGroupWithPermission]
    permission_codename = "ticket.view_ticket"

    pagination_class = StandardResultsSetPagination
