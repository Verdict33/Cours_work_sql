from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Главная страница и аутентификация
    path('', views.home, name='home'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', views.register_view, name='register'),
    path('dashboard/', views.dashboard, name='dashboard'),

    # Клиентские URL
    path('client/dashboard/', views.client_dashboard, name='client_dashboard'),
    path('client/delivery/create/', views.create_delivery, name='create_delivery'),
    path('client/delivery/delete/<int:delivery_id>/', views.delete_delivery, name='delete_delivery'),
    path('client/profile/', views.client_profile, name='client_profile'),
    path('client/feedback/<int:delivery_id>/', views.leave_feedback, name='leave_feedback'),
    path('client/payment/<int:delivery_id>/', views.make_payment, name='make_payment'),

    # Водительские URL
    path('driver/dashboard/', views.driver_dashboard, name='driver_dashboard'),
    path('driver/deliveries/available/', views.available_deliveries, name='available_deliveries'),
    path('driver/delivery/accept/<int:delivery_id>/', views.accept_delivery, name='accept_delivery'),
    path('driver/delivery/cancel/<int:delivery_id>/', views.cancel_delivery, name='cancel_delivery'),
    path('driver/delivery/complete/<int:delivery_id>/', views.complete_delivery, name='complete_delivery'),
    path('driver/profile/', views.driver_profile, name='driver_profile'),
]