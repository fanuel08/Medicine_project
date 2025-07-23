from django.contrib import admin
from django.urls import path, include



urlpatterns = [
    # 1. The URL for the Django Admin Panel
    path('admin/', admin.site.urls),

    # 2. This single line tells Django that all your API urls
    #    (like /api/token/, /api/cases/, etc.)
    #    are handled in the api/urls.py file.
    path('api/', include('api.urls')),
]

