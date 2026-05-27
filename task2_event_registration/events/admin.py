from django.contrib import admin

from .models import Category, Event, EventTag, Registration


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "created_at")
    search_fields = ("name", "description")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(EventTag)
class EventTagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "organizer",
        "status",
        "start_datetime",
        "end_datetime",
        "max_capacity",
        "ticket_price",
    )
    list_filter = ("status", "is_virtual", "category", "start_datetime")
    search_fields = ("title", "description", "venue_name", "city", "country")
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("tags",)


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ("ticket_code", "user", "event", "status", "registered_at", "check_in_time")
    list_filter = ("status", "registered_at")
    search_fields = ("ticket_code", "user__username", "event__title")
