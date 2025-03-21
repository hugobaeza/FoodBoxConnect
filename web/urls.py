from django.urls import path
from . import views

urlpatterns = [
    # Rutas para la interfaz web
    path('orders/', views.order_view, name='orders'),
    path('orders/<str:order_id>/', views.order_view, name='order_detail'),
    
    # Rutas para la API del ESP32
    path('api/box/<str:box_id>/', views.get_box_key, name='get_box_key'),
    path('api/box/<str:box_id>/status/', views.get_box_status, name='get_box_status'),
    path('api/temperature/', views.register_temperature, name='register_temperature'),
]