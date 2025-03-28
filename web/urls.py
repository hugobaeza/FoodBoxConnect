from django.urls import path
from . import views

urlpatterns = [
    #Home
    path('', views.home, name='home'),
    path('api/test/', views.test_api, name='test_api'),
    
    # Autenticación
    path('api/login/', views.login, name='login'),
    path('api/logout/', views.logout, name='logout'),
    
    # Pedidos
    path('api/orders/<str:order_key>/', views.get_order, name='get_order'),
    path('api/orders/create/', views.create_order, name='create_order'),
    
    # ESP32 - Endpoints específicos
    path('api/box-status/', views.box_status, name='box_status'),
    path('api/update-temperature/', views.update_temperature, name='update_temperature'),
    path('api/update-verification/', views.update_verification, name='update_verification'),
    path('api/register-box/', views.register_box, name='register_box'),
]
