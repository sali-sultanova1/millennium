from django.contrib import admin
from catalog.models import Destination, Tour, TourImage

class TourImageInline(admin.TabularInline):
    model = TourImage
    extra = 1
    fields = ("image", "alt_text", "sort_order")

@admin.register(Destination)
class DestinationAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "sort_order")
    list_filter = ("is_active",)
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}

@admin.register(Tour)
class TourAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "destination",
        "departure_date",
        "price",
        "currency",
        "price_basis",
        "is_active",
        )

    list_filter = ("is_active", "destination", "currency")
    search_fields = ("title", "hotel_name", "resort")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("created_at", "updated_at")
    list_select_related = ("destination",)
    inlines = (TourImageInline,)