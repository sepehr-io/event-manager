from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Event Manager', {'fields': ('role', 'phone')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Event Manager', {'fields': ('email', 'role', 'phone')}),
    )
    list_display = ('username', 'email', 'role', 'is_active')
    list_filter = UserAdmin.list_filter + ('role',)
    search_fields = ('username', 'email')