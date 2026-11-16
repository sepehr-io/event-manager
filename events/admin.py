from django.contrib import admin
from .models import Category, DiscountCode, Event

class DiscountCodeInline(admin.TabularInline):
    model = DiscountCode
    extra = 0

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'organizer', 'category', 'start_at', 'capacity', 'status')
    list_filter = ('status', 'category')
    search_fields = ('title', 'location')
    inlines = [DiscountCodeInline]