from django.contrib import admin, messages

from .models import Booking, BookingSeat, Movie, Screen, Seat, SeatHold, Show, Theatre

admin.site.site_header = "Cinepass control room"
admin.site.site_title = "Cinepass admin"
admin.site.index_title = "Manage your cinema"


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ("title", "genre", "language", "duration_minutes", "is_active")
    list_filter = ("is_active", "language", "genre")
    search_fields = ("title", "synopsis")
    prepopulated_fields = {"slug": ("title",)}


class ScreenInline(admin.TabularInline):
    model = Screen
    extra = 1


@admin.register(Theatre)
class TheatreAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "address", "is_active")
    list_filter = ("city", "is_active")
    search_fields = ("name", "city", "address")
    prepopulated_fields = {"slug": ("name",)}
    inlines = (ScreenInline,)


class SeatInline(admin.TabularInline):
    model = Seat
    extra = 0
    fields = ("row_label", "seat_number", "seat_type")


@admin.action(description="Generate default 8-row × 10-seat layout for selected screens")
def generate_default_seats(modeladmin, request, queryset):
    created = 0
    for screen in queryset:
        if screen.seats.exists():
            continue
        seats = [
            Seat(
                screen=screen,
                row_label=chr(65 + row),
                seat_number=number,
                seat_type=Seat.SeatType.PREMIUM if row >= 6 else Seat.SeatType.STANDARD,
            )
            for row in range(8)
            for number in range(1, 11)
        ]
        Seat.objects.bulk_create(seats)
        created += len(seats)
    if created:
        modeladmin.message_user(request, f"Created {created} seats.", messages.SUCCESS)
    else:
        modeladmin.message_user(request, "No seats created; each selected screen already has seats.", messages.WARNING)


@admin.register(Screen)
class ScreenAdmin(admin.ModelAdmin):
    list_display = ("name", "theatre", "is_active", "seat_count")
    list_filter = ("theatre", "is_active")
    search_fields = ("name", "theatre__name")
    inlines = (SeatInline,)
    actions = (generate_default_seats,)

    @admin.display(description="Seats")
    def seat_count(self, obj):
        return obj.seats.count()


@admin.register(Show)
class ShowAdmin(admin.ModelAdmin):
    list_display = ("movie", "screen", "starts_at", "standard_price", "premium_price", "is_active")
    list_filter = ("is_active", "screen__theatre", "starts_at")
    search_fields = ("movie__title", "screen__name", "screen__theatre__name")
    date_hierarchy = "starts_at"


class BookingSeatInline(admin.TabularInline):
    model = BookingSeat
    extra = 0
    can_delete = False
    readonly_fields = ("show", "seat", "price")


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("booking_code", "user", "show", "total_amount", "status", "booked_at")
    list_filter = ("status", "booked_at", "show__screen__theatre")
    search_fields = ("booking_code", "user__username", "user__email", "show__movie__title")
    readonly_fields = ("booking_code", "user", "show", "total_amount", "payment_reference", "booked_at")
    inlines = (BookingSeatInline,)


@admin.register(SeatHold)
class SeatHoldAdmin(admin.ModelAdmin):
    list_display = ("show", "seat", "user", "expires_at")
    list_filter = ("show__screen__theatre", "expires_at")
    search_fields = ("user__username", "show__movie__title", "seat__row_label")
