from django.utils.translation import gettext_lazy as _
from django.shortcuts import get_object_or_404

from django_filters.rest_framework import DjangoFilterBackend

from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import (
    generics,
    status,
)
from rest_framework_simplejwt.authentication import JWTAuthentication

from qms_api.pagination import StandardResultsSetPagination
from qms_api.custom_permissions import HasPermissionOrInGroupWithPermission

from apps.PRO.filters import PROFilter
from apps.PRO.models import PRO
from apps.PRO.serializers import (
    PROSerializer,
    PROActiveSerializer,
    PRODeletedSerializer,
    PRODialogSerializer,
)


class PROCreateView(generics.CreateAPIView):
    serializer_class = PROSerializer
    permission_classes = [IsAuthenticated, HasPermissionOrInGroupWithPermission]
    authentication_classes = [JWTAuthentication]
    permission_codename = "PRO.add_pro"

    def perform_create(self, serializer):
        name = serializer.validated_data.get("name", "")
        lowered_name = name.lower()
        serializer.save(
            name=lowered_name,
            created_by=self.request.user,
            updated_by=self.request.user,
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        return Response(
            {"detail": _("PRO created successfully")},
            status=status.HTTP_201_CREATED,
        )


class PROListView(generics.ListAPIView):
    queryset = PRO.objects.filter(is_deleted=False).order_by("-created_at")
    serializer_class = PROSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, HasPermissionOrInGroupWithPermission]
    permission_codename = "PRO.view_pro"
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = PROFilter
    ordering_fields = ["id", "-id", "name", "-name"]


class DeletedPROListView(generics.ListAPIView):
    queryset = PRO.objects.filter(is_deleted=True).order_by("-created_at")
    serializer_class = PROSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, HasPermissionOrInGroupWithPermission]
    permission_codename = "PRO.view_pro"
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = PROFilter
    ordering_fields = ["id", "-id", "name", "-name"]


class PRORetrieveView(generics.RetrieveAPIView):
    serializer_class = PROSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, HasPermissionOrInGroupWithPermission]
    permission_codename = "PRO.view_pro"
    lookup_field = "id"

    def get_object(self):
        pro_id = self.request.query_params.get("pro_id")
        pro = get_object_or_404(PRO, id=pro_id)
        return pro


class ActivePROListView(generics.ListAPIView):
    queryset = PRO.objects.filter(is_deleted=False, is_active=True).order_by(
        "-created_at"
    )
    serializer_class = PROSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, HasPermissionOrInGroupWithPermission]
    permission_codename = "PRO.view_pro"
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = PROFilter
    ordering_fields = ["id", "-id", "name", "-name"]


class PROChangeActiveView(generics.UpdateAPIView):
    serializer_class = PROActiveSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, HasPermissionOrInGroupWithPermission]
    permission_codename = "PRO.change_pro"

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def update(self, request, *args, **kwargs):
        pro_ids = request.data.get("pro_id", [])
        partial = kwargs.pop("partial", False)
        is_active = request.data.get("is_active")
        if is_active is None:
            return Response(
                {"detail": _("'is_active' field is required")},
                status=status.HTTP_400_BAD_REQUEST,
            )
        for pro_id in pro_ids:
            instance = get_object_or_404(PRO, id=pro_id)
            serializer = self.get_serializer(
                instance, data=request.data, partial=partial
            )
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
        return Response(
            {"detail": _("PRO status changed successfully")},
            status=status.HTTP_200_OK,
        )


class PROUpdateView(generics.UpdateAPIView):
    serializer_class = PROSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, HasPermissionOrInGroupWithPermission]
    permission_codename = "PRO.change_pro"
    lookup_field = "id"

    def get_object(self):
        pro_id = self.request.query_params.get("pro_id")
        pro = get_object_or_404(PRO, id=pro_id)
        return pro

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(
            {"detail": _("PRO Updated successfully")}, status=status.HTTP_200_OK
        )


class PRODeleteTemporaryView(generics.UpdateAPIView):
    serializer_class = PRODeletedSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, HasPermissionOrInGroupWithPermission]
    permission_codename = "PRO.change_pro"

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def update(self, request, *args, **kwargs):
        pro_ids = request.data.get("pro_id", [])
        partial = kwargs.pop("partial", False)
        is_deleted = request.data.get("is_deleted")

        if is_deleted == False:
            return Response(
                {"detail": _("These pro are not deleted")},
                status=status.HTTP_400_BAD_REQUEST,
            )
        for pro_id in pro_ids:
            instance = get_object_or_404(PRO, id=pro_id)
            if instance.is_deleted:
                return Response(
                    {
                        "detail": _(
                            "PRO with ID {} is already temp deleted".format(pro_id)
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
            {"detail": _("PRO temp deleted successfully")},
            status=status.HTTP_200_OK,
        )


class PRORestoreView(generics.RetrieveUpdateAPIView):

    serializer_class = PRODeletedSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, HasPermissionOrInGroupWithPermission]
    permission_codename = "PRO.change_pro"

    def update(self, request, *args, **kwargs):
        pro_ids = request.data.get("pro_id", [])
        partial = kwargs.pop("partial", False)
        is_deleted = request.data.get("is_deleted")

        if is_deleted == True:
            return Response(
                {"detail": _("PRO are already deleted")},
                status=status.HTTP_400_BAD_REQUEST,
            )
        for pro_id in pro_ids:
            instance = get_object_or_404(PRO, id=pro_id)
            if instance.is_deleted == False:
                return Response(
                    {"detail": _("PRO with ID {} is not deleted".format(pro_id))},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            instance.is_active = True

            serializer = self.get_serializer(
                instance, data=request.data, partial=partial
            )
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)

        return Response(
            {"detail": _("PRO restored successfully")}, status=status.HTTP_200_OK
        )


class PRODeleteView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, HasPermissionOrInGroupWithPermission]
    permission_codename = "PRO.delete_pro"

    def delete(self, request, *args, **kwargs):
        # Retrieve pro_ids from request body
        pro_ids = request.data.get("pro_id", [])

        if not pro_ids:
            return Response(
                {"detail": _("No PRO IDs provided.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        for pro_id in pro_ids:
            instance = get_object_or_404(PRO, id=pro_id)
            instance.delete()

        return Response(
            {"detail": _("PRO permanently deleted successfully.")},
            status=status.HTTP_204_NO_CONTENT,
        )

class PRODialogView(generics.ListAPIView):
    queryset = PRO.objects.filter(is_deleted=False, is_active=True)
    serializer_class = PRODialogSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
