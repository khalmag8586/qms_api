from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework_simplejwt.authentication import JWTAuthentication

from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.utils.timezone import now
from django.db.models import Q, Max

from apps.service.models import Service
from apps.ticket.models import Ticket
from apps.ticket.filters import TicketFilter
from apps.ticket.serializers import (
    TicketSerializer,
    CallNextCustomerSerializer,
    TicketRedirectSerializer,
    TicketDialogSerializer,
    TicketStatusDialogSerializer,
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
    ordering_fields = [
        "number",
        "created_at",
        "customer_name",
        "mobile_number",
        "email",
    ]
    pagination_class = StandardResultsSetPagination
    filterset_class = TicketFilter


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
    serializer_class = CallNextCustomerSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        # counter_id = request.data.get("counter_id")
        try:
            counter = Counter.objects.get(employee=self.request.user)
        except Counter.DoesNotExist:
            return Response(
                {"detail": _("No counter is associated with the logged-in user.")},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Use the counter's ID
        counter_id = counter.id
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
        try:
            counter = Counter.objects.prefetch_related("departments").get(id=counter_id)
            services = Service.objects.filter(department__in=counter.departments.all())
            today = now().date()
            next_customer = (
                Ticket.objects.filter(
                    service__in=services,
                    called_at__isnull=True,
                    created_at__date=today,
                )
                .order_by("created_at")
                .first()
            )
            return next_customer
        except Counter.DoesNotExist:
            raise ValidationError({"detail": _("Counter does not exist.")})

    def get_current_customer(self, counter_id):
        current_customer = Ticket.objects.filter(
            Q(counter__employee=self.request.user) & Q(status="in_progress")
        ).first()
        return current_customer

    def update_ticket(self, ticket, counter_id):
        try:
            counter = Counter.objects.get(id=counter_id, employee=self.request.user)
            ticket.called_at = timezone.now()
            ticket.status = "in_progress"
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


class TicketDialogView(generics.ListAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, HasPermissionOrInGroupWithPermission]
    permission_codename = "ticket.view_ticket"
    queryset = Ticket.objects.all()
    serializer_class = TicketDialogSerializer


class TicketInProgressTodayDialogView(generics.ListAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = TicketDialogSerializer
    def get_queryset(self):
        today = now().date()  # Get the current date
        return Ticket.objects.filter(status="in_progress", created_at__date=today)
class TicketStatusDialogView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    # permission_classes = [IsAuthenticated, HasPermissionOrInGroupWithPermission]
    # permission_codename = "ticket.view_ticket"

    def get(self, request, *args, **kwargs):
        # Define the gender choices here
        gender_choices = [
            {"value": "waiting", "display": _("Waiting")},
            {"value": "in_progress", "display": _("In Progress")},
            {"value": "completed", "display": _("Completed")},
        ]

        serializer = TicketStatusDialogSerializer(gender_choices, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
