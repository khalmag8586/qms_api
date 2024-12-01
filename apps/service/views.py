from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from django.shortcuts import get_object_or_404

# from django.core.exceptions import ValidationError
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied
from rest_framework.exceptions import ValidationError

from rest_framework.decorators import action
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework import (
    generics,
    status,
)
from rest_framework_simplejwt.authentication import JWTAuthentication

from qms_api.pagination import StandardResultsSetPagination

from apps.service.models import Service
from apps.service.serializers import (
    ServiceSerializer,
    ServiceDeleteSerializer,
    ServiceActiveSerializer,
    ServiceDialogSerializer,
)

from qms_api.custom_permissions import HasPermissionOrInGroupWithPermission


class ServiceCreateView(generics.CreateAPIView):
    serializer_class = ServiceSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, HasPermissionOrInGroupWithPermission]
    permission_codename = "service.add_service"

    def perform_create(self, serializer):
        # Validate the uniqueness of the service_symbol
        service_symbol = serializer.validated_data.get("service_symbol", "").upper()

        if Service.objects.filter(service_symbol=service_symbol).exists():
            raise ValidationError({"detail": _("This service symbol already exists.")})

        # Process and save the service
        name = serializer.validated_data.get("name", "")
        capitalized_name = name.lower()
        serializer.save(
            name=capitalized_name,
            service_symbol=service_symbol,
            created_by=self.request.user,
            updated_by=self.request.user,
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        return Response(
            {"detail": _("Service created successfully")},
            status=status.HTTP_201_CREATED,
        )


class ServiceListView(generics.ListAPIView):
    queryset = Service.objects.filter(is_deleted=False)
    serializer_class = ServiceSerializer
    authentication_classes = [JWTAuthentication]
    permission_codename = "service.view_service"
    permission_classes = [IsAuthenticated, HasPermissionOrInGroupWithPermission]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ["name", "name_ar", "service_symbol"]
    ordering_fields = ["name", "-name", "name_ar", "-name_ar"]


class DeletedServiceListView(generics.ListAPIView):
    queryset = Service.objects.filter(is_deleted=True)
    serializer_class = ServiceSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, HasPermissionOrInGroupWithPermission]
    permission_codename = "service.view_service"
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ["name", "name_ar", "service_symbol"]
    ordering_fields = ["name", "-name", "name_ar", "-name_ar"]


class ServiceRetrieveView(generics.RetrieveAPIView):
    serializer_class = ServiceSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, HasPermissionOrInGroupWithPermission]
    permission_codename = "service.change_service"
    lookup_field = "id"

    def get_object(self):
        service_id = self.request.query_params.get("service_id")
        service = get_object_or_404(Service, id=service_id)
        return service


class ActiveServiceListView(generics.ListAPIView):
    queryset = Service.objects.filter(is_deleted=False, is_active=True)
    serializer_class = ServiceSerializer
    # authentication_classes = [JWTAuthentication]
    # permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ["name", "name_ar", "service_symbol"]
    ordering_fields = ["name", "-name", "name_ar", "-name_ar"]


class ServiceChangeActiveView(generics.UpdateAPIView):
    serializer_class = ServiceActiveSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, HasPermissionOrInGroupWithPermission]
    permission_codename = "service.change_service"

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def update(self, request, *args, **kwargs):
        service_ids = request.data.get("service_id", [])
        partial = kwargs.pop("partial", False)
        is_active = request.data.get("is_active")
        if is_active is None:
            return Response(
                {"detail": _("'is_active' field is required")},
                status=status.HTTP_400_BAD_REQUEST,
            )
        for service_id in service_ids:
            instance = get_object_or_404(Service, id=service_id)
            serializer = self.get_serializer(
                instance, data=request.data, partial=partial
            )
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
        return Response(
            {"detail": _("Service status changed successfully")},
            status=status.HTTP_200_OK,
        )


class ServiceUpdateView(generics.RetrieveUpdateAPIView):
    serializer_class = ServiceSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, HasPermissionOrInGroupWithPermission]
    permission_codename = "service.change_service"

    lookup_field = "id"

    def get_object(self):
        service_id = self.request.query_params.get("service_id")
        service = get_object_or_404(Service, id=service_id)
        return service

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(
            {"detail": _("Service Updated successfully")}, status=status.HTTP_200_OK
        )


class ServiceDeleteTemporaryView(generics.UpdateAPIView):
    serializer_class = ServiceDeleteSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, HasPermissionOrInGroupWithPermission]
    permission_codename = "service.change_service"

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def update(self, request, *args, **kwargs):
        service_ids = request.data.get("service_id", [])
        partial = kwargs.pop("partial", False)
        is_deleted = request.data.get("is_deleted")

        if is_deleted == False:
            return Response(
                {"detail": _("These services are not deleted")},
                status=status.HTTP_400_BAD_REQUEST,
            )
        for service_id in service_ids:
            instance = get_object_or_404(Service, id=service_id)
            if instance.is_deleted:
                return Response(
                    {
                        "detail": _(
                            "Service with ID {} is already temp deleted".format(
                                service_id
                            )
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            instance.is_active = False
            instance.save()
            serializer = self.get_serializer(
                instance, data=request.data, partial=partial
            )
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)

        return Response(
            {"detail": _("Services temp deleted successfully")},
            status=status.HTTP_200_OK,
        )


class ServiceRestoreView(generics.RetrieveUpdateAPIView):

    serializer_class = ServiceDeleteSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, HasPermissionOrInGroupWithPermission]
    permission_codename = "service.change_service"

    def update(self, request, *args, **kwargs):
        service_ids = request.data.get("service_id", [])
        partial = kwargs.pop("partial", False)
        is_deleted = request.data.get("is_deleted")

        if is_deleted == True:
            return Response(
                {"detail": _("services are already deleted")},
                status=status.HTTP_400_BAD_REQUEST,
            )
        for service_id in service_ids:
            instance = get_object_or_404(Service, id=service_id)
            if instance.is_deleted == False:
                return Response(
                    {
                        "detail": _(
                            "service with ID {} is not deleted".format(service_id)
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            instance.is_active = True

            serializer = self.get_serializer(
                instance, data=request.data, partial=partial
            )
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)

        return Response(
            {"detail": _("Services restored successfully")}, status=status.HTTP_200_OK
        )


class ServiceDeleteView(generics.DestroyAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, HasPermissionOrInGroupWithPermission]
    permission_codename = "service.delete_service"

    def delete(self, request, *args, **kwargs):
        service_ids = request.data.get("service_id", [])
        for service_id in service_ids:
            instance = get_object_or_404(Service, id=service_id)
            instance.delete()

        return Response(
            {"detail": _("Service permanently deleted successfully")},
            status=status.HTTP_204_NO_CONTENT,
        )


# Service Dialogs
class ServiceDialogView(generics.ListAPIView):
    serializer_class = ServiceDialogSerializer
    queryset = Service.objects.filter(is_deleted=False, is_active=True)
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, HasPermissionOrInGroupWithPermission]
    permission_codename = "service.view_service"


class AvailableSymbolsView(APIView):
    def get(self, request, format=None):
        # Get all existing symbols
        existing_symbols = Service.objects.values_list("service_symbol", flat=True)

        # Generate available letters by excluding existing symbols
        available_letters = [
            {"title": chr(i), "value": chr(i)}
            for i in range(65, 91)
            if chr(i) not in existing_symbols
        ]

        return Response(available_letters, status=status.HTTP_200_OK)
