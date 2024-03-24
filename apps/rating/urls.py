from django.urls import path
from apps.rating.views import (
    RatingCreateView,
)

app_name = "rating"
urlpatterns = [
    path("rating_create/", RatingCreateView.as_view(), name="rating-create"),
]
