from django.conf import settings
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path('account/', include('accounts.urls', namespace='account')),
    path("", include("pages.urls", namespace='course')),
    path("students/", include("students.urls", namespace='student')),
    path('activity/', include('actstream.urls')),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
        path("__debug__/", include(debug_toolbar.urls)),
    ] + urlpatterns
