from django.utils.translation import gettext_lazy as _
from django.shortcuts import get_object_or_404


from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend


from rest_framework_simplejwt.authentication import JWTAuthentication

from apps.department.models import Department
from apps.department.serializers import (
    DepartmentSerializer,
    DepartmentActiveSerializer,
    DepartmentDeleteSerializer,
    DepartmentDialogSerializer,
)
from apps.department.filters import DepartmentFilter

from qms_api.pagination import StandardResultsSetPagination
from qms_api.custom_permissions import HasPermissionOrInGroupWithPermission


class DepartmentCreateView(generics.CreateAPIView):
    serializer_class = DepartmentSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, HasPermissionOrInGroupWithPermission]
    permission_codename = "department.add_department"

    def perform_create(self, serializer):
        name = serializer.validated_data.get("name", "")
        capitalized_name = name.capitalize()
        serializer.save(
            name=capitalized_name,
            created_by=self.request.user,
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        return Response(
            {"detail": _("Department created successfully")},
            status=status.HTTP_201_CREATED,
        )


class DepartmentListView(generics.ListAPIView):
    queryset = Department.objects.filter(is_deleted=False)
    serializer_class = DepartmentSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, HasPermissionOrInGroupWithPermission]
    permission_codename = "department.view_department"
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = DepartmentFilter
    filter_fields = ["name", "name_ar"]
    ordering_fields = ["name", "-name", "name_ar", "-name_ar"]


class DeletedDepartmentListView(generics.ListAPIView):
    queryset = Department.objects.filter(is_deleted=True)
    serializer_class = DepartmentSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, HasPermissionOrInGroupWithPermission]
    permission_codename = "department.view_department"
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = DepartmentFilter
    filter_fields = ["name", "name_ar"]
    ordering_fields = ["name", "-name", "name_ar", "-name_ar"]


class DepartmentRetrieveView(generics.RetrieveAPIView):
    serializer_class = DepartmentSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, HasPermissionOrInGroupWithPermission]
    permission_codename = "department.view_department"
    lookup_field = "id"

    def get_object(self):
        department_id = self.request.query_params.get("department_id")
        department = get_object_or_404(Department, id=department_id)
        return department


class DepartmentChangeActiveView(generics.UpdateAPIView):
    serializer_class = DepartmentActiveSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, HasPermissionOrInGroupWithPermission]
    permission_codename = "department.change_department"

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def update(self, request, *args, **kwargs):
        department_ids = request.data.get("department_id", [])
        partial = kwargs.pop("partial", False)
        is_active = request.data.get("is_active")
        if is_active is None:
            return Response(
                {"detail": _("'is_active' field is required")},
                status=status.HTTP_400_BAD_REQUEST,
            )
        for department_id in department_ids:
            instance = get_object_or_404(Department, id=department_id)
            serializer = self.get_serializer(
                instance, data=request.data, partial=partial
            )
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
        return Response(
            {"detail": _("Department status changed successfully")},
            status=status.HTTP_200_OK,
        )


class DepartmentUpdateView(generics.UpdateAPIView):
    serializer_class = DepartmentSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, HasPermissionOrInGroupWithPermission]
    permission_codename = "department.change_department"
    lookup_field = "id"

    def get_object(self):
        department_id = self.request.query_params.get("department_id")
        department = get_object_or_404(Department, id=department_id)
        return department

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(
            {"detail": _("Department Updated successfully")}, status=status.HTTP_200_OK
        )


class DepartmentDeleteTemporaryView(generics.UpdateAPIView):
    serializer_class = DepartmentDeleteSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, HasPermissionOrInGroupWithPermission]
    permission_codename = "department.change_department"

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def update(self, request, *args, **kwargs):
        department_ids = request.data.get("department_id", [])
        partial = kwargs.pop("partial", False)
        is_deleted = request.data.get("is_deleted")

        if is_deleted == False:
            return Response(
                {"detail": _("These departments are not deleted")},
                status=status.HTTP_400_BAD_REQUEST,
            )
        for department_id in department_ids:
            instance = get_object_or_404(Department, id=department_id)
            if instance.is_deleted:
                return Response(
                    {
                        "detail": _(
                            "Department with ID {} is already temp deleted".format(
                                department_id
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
            {"detail": _("Department temp deleted successfully")},
            status=status.HTTP_200_OK,
        )


class DepartmentRestoreView(generics.RetrieveUpdateAPIView):

    serializer_class = DepartmentDeleteSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, HasPermissionOrInGroupWithPermission]
    permission_codename = "department.change_department"

    def update(self, request, *args, **kwargs):
        department_ids = request.data.get("department_id", [])
        partial = kwargs.pop("partial", False)
        is_deleted = request.data.get("is_deleted")

        if is_deleted == True:
            return Response(
                {"detail": _("departments are already deleted")},
                status=status.HTTP_400_BAD_REQUEST,
            )
        for department_id in department_ids:
            instance = get_object_or_404(Department, id=department_id)
            if instance.is_deleted == False:
                return Response(
                    {
                        "detail": _(
                            "department with ID {} is not deleted".format(department_id)
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
            {"detail": _("Department restored successfully")}, status=status.HTTP_200_OK
        )


class DepartmentDeleteView(generics.DestroyAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, HasPermissionOrInGroupWithPermission]
    permission_codename = "department.delete_department"

    def delete(self, request, *args, **kwargs):
        department_ids = request.data.get("department_id", [])
        for department_id in department_ids:
            instance = get_object_or_404(Department, id=department_id)
            instance.delete()

        return Response(
            {"detail": _("Department permanently deleted successfully")},
            status=status.HTTP_204_NO_CONTENT,
        )
class DepartmentDialogView(generics.ListAPIView):
    queryset=Department.objects.filter(is_deleted=False)
    serializer_class=DepartmentDialogSerializer
    authentication_classes=[JWTAuthentication]
    permission_classes=[IsAuthenticated, HasPermissionOrInGroupWithPermission]
    permission_codename = "department.view_department"
