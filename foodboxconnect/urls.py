from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('web.urls')),  # Asegúrate que 'web' sea el nombre correcto de tu app
]
