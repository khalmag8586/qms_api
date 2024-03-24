from rest_framework import serializers
from apps.rating.models import Rating


# Rating serializer
class RatingSerializer(serializers.ModelSerializer):

    class Meta:
        model = Rating
        fields = ["id", "service", "ticket", "stars", "review", "created_at"]
        fields_read_only = ["id", "created_at"]
