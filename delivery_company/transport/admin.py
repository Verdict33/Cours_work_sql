from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import *


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone')
    search_fields = ('user__username', 'phone')


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ('user', 'last_name', 'first_name', 'phone', 'status', 'fleet')
    list_filter = ('status',)
    search_fields = ('user__username', 'last_name', 'first_name', 'phone')


@admin.register(Fleet)
class FleetAdmin(admin.ModelAdmin):
    list_display = ('license_plate', 'model', 'status', 'capacity')
    list_filter = ('status',)
    search_fields = ('license_plate', 'model')


@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    list_display = ('id', 'client', 'driver', 'status', 'delivery_type', 'created_at')
    list_filter = ('status', 'delivery_type')
    search_fields = ('client__user__username', 'driver__user__username')


# Регистрация остальных моделей
admin.site.register(Cargo)
admin.site.register(Route)
admin.site.register(VehicleMaintenance)
admin.site.register(Feedback)
admin.site.register(Payment)