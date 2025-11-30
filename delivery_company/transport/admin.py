from django.contrib import admin
from .models import *


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'get_user_email')
    search_fields = ('user__username', 'user__email', 'phone')

    def get_user_email(self, obj):
        return obj.user.email

    get_user_email.short_description = 'Email'


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'phone', 'status', 'fleet')
    list_filter = ('status', 'fleet')
    search_fields = ('last_name', 'first_name', 'phone')


@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    list_display = ('id', 'client', 'get_client_phone', 'status', 'delivery_type', 'driver', 'created_at')
    list_filter = ('status', 'delivery_type', 'created_at')
    search_fields = ('client__user__username', 'client__phone', 'driver__last_name')

    def get_client_phone(self, obj):
        return obj.client.phone

    get_client_phone.short_description = 'Телефон клиента'


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ('delivery', 'departure_city', 'arrival_city', 'distance')
    search_fields = ('departure_city', 'arrival_city')


@admin.register(Cargo)
class CargoAdmin(admin.ModelAdmin):
    list_display = ('name', 'weight')
    search_fields = ('name',)


@admin.register(Fleet)
class FleetAdmin(admin.ModelAdmin):
    list_display = ('license_plate', 'model', 'status', 'capacity')
    list_filter = ('status',)


@admin.register(VehicleMaintenance)
class VehicleMaintenanceAdmin(admin.ModelAdmin):
    list_display = ('fleet', 'service_date', 'status')
    list_filter = ('status', 'service_date')


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('client', 'delivery', 'submitted_at')
    search_fields = ('client__user__username', 'content')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('delivery', 'amount', 'status', 'payment_date')
    list_filter = ('status', 'method')


@admin.register(DriverDowntime)
class DriverDowntimeAdmin(admin.ModelAdmin):
    list_display = ('driver', 'start_datetime', 'end_datetime', 'total_duration')