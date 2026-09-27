from django.contrib import admin
from django.urls import include, path

from config.api import api_urlpatterns

urlpatterns = [
    path("django/admin/", admin.site.urls),
    path("api/v1/", include((api_urlpatterns, "api"))),
]
