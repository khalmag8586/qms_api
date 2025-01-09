from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from qms_api.util import CheckFieldValueExistenceView

urlpatterns = [
    path("i18n/", include("django.conf.urls.i18n")),
]
urlpatterns += i18n_patterns(
    path("admin/", admin.site.urls),
    # path('api/project_setup/',include('apps.project_setup.urls')),
    path("auth/", include("djoser.urls")),
    # path("auth/", include("djoser.urls.jwt")),
    # path("auth/", include("djoser.urls.authtoken")),
    path(
        "check_field_value_existence/",
        CheckFieldValueExistenceView.as_view(),
        name="check_field_value_existence",
    ),
    path("api/users/", include("user.urls")),
    path("api/permissions/", include("apps.permissions_api.urls")),

    path('api/department/',include('apps.department.urls')),
    path('api/service/',include('apps.service.urls')),
    path('api/contact_us/',include('apps.contact_us.urls')),
    path('api/about_us/',include('apps.about_us.urls')),
    path('api/counter/',include('apps.counter.urls')),
    path('api/ticket/',include('apps.ticket.urls')),
    path('api/PRO/',include('apps.PRO.urls')),
    path('api/invoice/',include('apps.invoice.urls')),
    path('api/rating/',include('apps.rating.urls')),
)

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )
    urlpatterns += static(
        settings.STATIC_URL,
        document_root=settings.STATIC_ROOT,
    )
