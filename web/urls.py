from django.urls import path
from . import views

urlpatterns = [
    # Autenticación
    path('api/login/', views.login, name='login'),
    path('api/logout/', views.logout, name='logout'),

    # Pedidos
    path('api/orders/<str:order_key>/', views.get_order, name='get_order'),
]
