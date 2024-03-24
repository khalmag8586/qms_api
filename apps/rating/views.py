from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from rest_framework_simplejwt.authentication import JWTAuthentication

from apps.rating.models import Rating
from apps.rating.serializers import RatingSerializer
from apps.service.models import Service


# Rating Views
class RatingCreateView(generics.CreateAPIView):
    queryset = Rating.objects.all()
    serializer_class = RatingSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        # Get the product from the URL
        service_id = self.request.query_params.get("service_id")
        service = Service.objects.get(id=service_id)

        # Set the product field in the review serializer
        serializer.save(service=service)
