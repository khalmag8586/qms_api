from django.utils.translation import gettext_lazy as _
from django.shortcuts import get_object_or_404

from django_filters.rest_framework import DjangoFilterBackend

from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import (
    generics,
    status,
)
from rest_framework_simplejwt.authentication import JWTAuthentication

from qms_api.pagination import StandardResultsSetPagination

from apps.counter.models import Counter
from apps.counter.serializers import (
    CounterSerializer,
    CounterActiveSerializer,
    CounterDeleteSerializer,
    CounterDialogSerializer,
)


class CounterCreateView(generics.CreateAPIView):
    serializer_class = CounterSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, updated_by=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        return Response(
            {"detail": _("Counter created successfully")},
            status=status.HTTP_201_CREATED,
        )


class CounterListView(generics.ListAPIView):
    queryset = Counter.objects.filter(is_deleted=False)
    serializer_class = CounterSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ["number"]
    ordering_fields = ["number", "-number"]


class DeletedCounterListView(generics.ListAPIView):
    queryset = Counter.objects.filter(is_deleted=True)
    serializer_class = CounterSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ["number"]
    ordering_fields = ["number", "-number"]


class CounterRetrieveView(generics.RetrieveAPIView):
    serializer_class = CounterSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    lookup_field = "id"

    def get_object(self):
        counter_id = self.request.query_params.get("counter_id")
        counter = get_object_or_404(Counter, id=counter_id)
        return counter


class ActiveCounterListView(generics.ListAPIView):
    queryset = Counter.objects.filter(is_deleted=False, is_active=True)
    serializer_class = CounterSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ["number"]
    ordering_fields = ["number", "-number"]


class CounterChangeActiveView(generics.UpdateAPIView):
    serializer_class = CounterActiveSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def update(self, request, *args, **kwargs):
        counter_ids = request.data.get("counter_id", [])
        partial = kwargs.pop("partial", False)
        is_active = request.data.get("is_active")
        if is_active is None:
            return Response(
                {"detail": _("'is_active' field is required")},
                status=status.HTTP_400_BAD_REQUEST,
            )
        for counter_id in counter_ids:
            instance = get_object_or_404(Counter, id=counter_id)
            serializer = self.get_serializer(
                instance, data=request.data, partial=partial
            )
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
        return Response(
            {"detail": _("Counter status changed successfully")},
            status=status.HTTP_200_OK,
        )


class CounterUpdateView(generics.RetrieveUpdateAPIView):
    serializer_class = CounterSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    lookup_field = "id"

    def get_object(self):
        counter_id = self.request.query_params.get("counter_id")
        counter = get_object_or_404(Counter, id=counter_id)
        return counter

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(
            {"detail": _("Counter Updated successfully")}, status=status.HTTP_200_OK
        )


class CounterDeleteTemporaryView(generics.UpdateAPIView):
    serializer_class = CounterDeleteSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def update(self, request, *args, **kwargs):
        counter_ids = request.data.get("counter_id", [])
        partial = kwargs.pop("partial", False)
        is_deleted = request.data.get("is_deleted")

        if is_deleted == False:
            return Response(
                {"detail": _("These counters are not deleted")},
                status=status.HTTP_400_BAD_REQUEST,
            )
        for counter_id in counter_ids:
            instance = get_object_or_404(Counter, id=counter_id)
            if instance.is_deleted:
                return Response(
                    {
                        "detail": _(
                            "Counter with ID {} is already temp deleted".format(
                                counter_id
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
            {"detail": _("Counter temp deleted successfully")},
            status=status.HTTP_200_OK,
        )


class CounterRestoreView(generics.UpdateAPIView):
    serializer_class = CounterDeleteSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def update(self, request, *args, **kwargs):
        counter_ids = request.data.get("counter_id", [])
        partial = kwargs.pop("partial", False)
        is_deleted = request.data.get("is_deleted")

        if is_deleted == True:
            return Response(
                {"detail": _("These counters are already deleted")},
                status=status.HTTP_400_BAD_REQUEST,
            )
        for counter_id in counter_ids:
            instance = get_object_or_404(Counter, id=counter_id)
            if instance.is_deleted == False:
                return Response(
                    {
                        "detail": _(
                            "Counter with ID {} is already restored".format(counter_id)
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            instance.is_active = True
            instance.save()
            serializer = self.get_serializer(
                instance, data=request.data, partial=partial
            )
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)

        return Response(
            {"detail": _("Counter temp deleted successfully")},
            status=status.HTTP_200_OK,
        )


class CounterDeleteView(generics.DestroyAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        counter_ids = request.data.get("counter_id", [])
        for counter_id in counter_ids:
            instance = get_object_or_404(Counter, id=counter_id)
            instance.delete()

        return Response(
            {"detail": _("Counter permanently deleted successfully")},
            status=status.HTTP_204_NO_CONTENT,
        )

class CounterDialogView(generics.ListAPIView):
    authentication_classes=[JWTAuthentication]
    permission_classes=[IsAuthenticated]
    queryset=Counter.objects.filter(is_deleted=False)
    serializer_class=CounterDialogSerializer
