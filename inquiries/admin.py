from django.contrib import admin

from .models import Inquiry, InquiryTour


class InquiryTourInline(admin.StackedInline):
    model = InquiryTour
    extra = 0
    can_delete = False
    fields = (
        "tour",
        "title_snapshot",
        "destination_snapshot",
        "resort_snapshot",
        "hotel_name_snapshot",
        "hotel_stars_snapshot",
        "departure_city_snapshot",
        "departure_date_snapshot",
        "nights_snapshot",
        "meal_snapshot",
        "meal_details_snapshot",
        "price_snapshot",
        "currency_snapshot",
        "price_basis_snapshot",
        "price_details_snapshot",
        "price_from_snapshot",
        "position",
    )

    readonly_fields = fields

    def has_add_permission(self, request, obj=None):
        return False

@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    inlines = [InquiryTourInline]
    list_display = ("id", "name", "phone", "source", "status", "created_at")
    list_filter = ("status", "source", "created_at")
    search_fields = ("name", "phone", "selected_tours__title_snapshot")
    readonly_fields = ("source", "created_at")

    def has_add_permission(self, request, obj=None):
        return False