from django.contrib import admin
from .models import Registration, Ticket

@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ('user', 'event', 'status', 'discount_percent', 'created_at')
    list_filter = ('status',)
    search_fields = ('user__username', 'event__title')


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('code', 'registration', 'issued_at', 'checked_in_at')
    readonly_fields = ('code',)