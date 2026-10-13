from datetime import date, datetime, time, timedelta
from decimal import Decimal

from django.contrib import admin, messages
from django.db.models import Count, Sum
from django.http import HttpResponseBadRequest
from django.template.response import TemplateResponse
from django.urls import path
from django.utils import timezone
from django.utils.html import format_html

from .models import Booking, BookingSeat, Movie, Screen, Seat, SeatHold, Show, Theatre

admin.site.site_header = "Cinepass control room"
admin.site.site_title = "Cinepass admin"
admin.site.index_title = "Manage your cinema"


def sales_report_view(request):
    """A compact, date-filterable report for confirmed ticket sales."""
    today = timezone.localdate()
    default_start = today - timedelta(days=29)
    try:
        start_date = date.fromisoformat(request.GET.get("from", default_start.isoformat()))
        end_date = date.fromisoformat(request.GET.get("to", today.isoformat()))
    except (TypeError, ValueError):
        return HttpResponseBadRequest("Enter dates in YYYY-MM-DD format.")
    if start_date > end_date:
        start_date, end_date = end_date, start_date

    current_tz = timezone.get_current_timezone()
    start_at = timezone.make_aware(datetime.combine(start_date, time.min), current_tz)
    end_before = timezone.make_aware(datetime.combine(end_date + timedelta(days=1), time.min), current_tz)
    bookings = Booking.objects.filter(
        status=Booking.Status.CONFIRMED,
        booked_at__gte=start_at,
        booked_at__lt=end_before,
    )

    totals = bookings.aggregate(revenue=Sum("total_amount"))
    revenue = totals["revenue"] or Decimal("0.00")
    booking_count = bookings.count()
    ticket_count = BookingSeat.objects.filter(booking__in=bookings).count()
    average_order = revenue / booking_count if booking_count else Decimal("0.00")

    # Group in Python so MySQL does not need its optional time-zone tables for
    # CONVERT_TZ(), which otherwise makes this chart fail on fresh installs.
    daily_sales = {}
    for booked_at, amount in bookings.values_list("booked_at", "total_amount").iterator(chunk_size=2000):
        day = timezone.localtime(booked_at, current_tz).date()
        row = daily_sales.setdefault(day, {"revenue": Decimal("0.00"), "booking_count": 0})
        row["revenue"] += amount
        row["booking_count"] += 1

    daily_tickets = {}
    for booked_at in BookingSeat.objects.filter(booking__in=bookings).values_list("booking__booked_at", flat=True).iterator(chunk_size=2000):
        day = timezone.localtime(booked_at, current_tz).date()
        daily_tickets[day] = daily_tickets.get(day, 0) + 1
    chart_days = []
    cursor = start_date
    while cursor <= end_date:
        row = daily_sales.get(cursor, {})
        chart_days.append({
            "label": cursor.strftime("%d %b"),
            "revenue": row.get("revenue") or Decimal("0.00"),
            "booking_count": row.get("booking_count", 0),
            "ticket_count": daily_tickets.get(cursor, 0),
        })
        cursor += timedelta(days=1)
    peak = max((day["revenue"] for day in chart_days), default=Decimal("0.00"))
    for day in chart_days:
        day["bar_height"] = max(4, int(day["revenue"] / peak * 100)) if peak else 4

    top_movies = list(
        bookings.values("show__movie_id", "show__movie__title")
        .annotate(revenue=Sum("total_amount"), booking_count=Count("id"))
        .order_by("-revenue")[:8]
    )
    ticket_totals = {}
    show_ticket_totals = {}
    theatre_ticket_totals = {}
    for row in (
        BookingSeat.objects.filter(booking__in=bookings)
        .values("show_id", "show__movie_id", "show__screen__theatre_id")
        .annotate(ticket_count=Count("id"))
    ):
        ticket_totals[row["show__movie_id"]] = ticket_totals.get(row["show__movie_id"], 0) + row["ticket_count"]
        show_ticket_totals[row["show_id"]] = row["ticket_count"]
        theatre_id = row["show__screen__theatre_id"]
        theatre_ticket_totals[theatre_id] = theatre_ticket_totals.get(theatre_id, 0) + row["ticket_count"]
    for movie in top_movies:
        movie["ticket_count"] = ticket_totals.get(movie["show__movie_id"], 0)

    theatre_sales = list(
        bookings.values("show__screen__theatre_id", "show__screen__theatre__name")
        .annotate(revenue=Sum("total_amount"), booking_count=Count("id"))
        .order_by("show__screen__theatre__name")
    )
    for theatre_sale in theatre_sales:
        theatre_sale["ticket_count"] = theatre_ticket_totals.get(theatre_sale["show__screen__theatre_id"], 0)

    show_sales = list(
        bookings.values(
            "show_id",
            "show__movie__title",
            "show__screen__theatre__name",
            "show__screen__name",
            "show__starts_at",
        )
        .annotate(revenue=Sum("total_amount"), booking_count=Count("id"))
        .order_by("show__screen__theatre__name", "show__starts_at", "show__movie__title")
    )
    for show_sale in show_sales:
        show_sale["ticket_count"] = show_ticket_totals.get(show_sale["show_id"], 0)

    recent_bookings = list(
        bookings.select_related("user", "show__movie", "show__screen__theatre")
        .prefetch_related("booking_seats__seat")
        .order_by("-booked_at")[:10]
    )
    for booking in recent_bookings:
        booking.report_seats = ", ".join(
            f"{item.seat.row_label}{item.seat.seat_number}"
            for item in booking.booking_seats.all()
        )

    context = {
        **admin.site.each_context(request),
        "title": "Sales report",
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "revenue": revenue,
        "booking_count": booking_count,
        "ticket_count": ticket_count,
        "average_order": average_order,
        "chart_days": chart_days,
        "has_chart_sales": booking_count > 0,
        "top_movies": top_movies,
        "theatre_sales": theatre_sales,
        "show_sales": show_sales,
        "recent_bookings": recent_bookings,
    }
    return TemplateResponse(request, "admin/sales_report.html", context)


# Add a staff-protected page to Django's existing admin site so all registered
# model administration keeps working as it does today.
_default_admin_get_urls = admin.site.get_urls


def _admin_urls_with_sales_report():
    custom_urls = [
        path("sales-report/", admin.site.admin_view(sales_report_view), name="sales_report"),
    ]
    return custom_urls + _default_admin_get_urls()


admin.site.get_urls = _admin_urls_with_sales_report


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ("title", "poster_preview", "genre", "language", "duration_minutes", "is_active")
    list_filter = ("is_active", "language", "genre")
    search_fields = ("title", "synopsis", "director", "cast")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("poster_preview",)
    fields = (
        "title", "slug", "synopsis", "genre", "language", "duration_minutes",
        "certificate", "release_date", "director", "cast", "rating", "poster_image", "poster_url", "accent",
        "is_active", "poster_preview",
    )

    @admin.display(description="Poster preview")
    def poster_preview(self, obj):
        if obj and obj.poster_image:
            return format_html('<img src="{}" alt="{}" style="max-height: 130px; max-width: 220px; border-radius: 6px;">', obj.poster_image.url, obj.title)
        return "No uploaded poster"


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
