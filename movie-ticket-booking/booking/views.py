import base64
import io
import json
import secrets
from decimal import Decimal

import qrcode
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import SignUpForm
from .models import Booking, BookingSeat, Movie, Seat, SeatHold, Show


def home(request):
    movies = Movie.objects.filter(is_active=True)
    return render(request, "booking/home.html", {"movies": movies})


def movie_detail(request, slug):
    movie = get_object_or_404(Movie, slug=slug, is_active=True)
    shows = (
        Show.objects.filter(movie=movie, is_active=True, starts_at__gte=timezone.now(), screen__is_active=True, screen__theatre__is_active=True)
        .select_related("screen", "screen__theatre")[:12]
    )
    return render(request, "booking/movie_detail.html", {"movie": movie, "shows": shows})


def theatre_list(request, slug):
    movie = get_object_or_404(Movie, slug=slug, is_active=True)
    shows = list(
        Show.objects.filter(movie=movie, is_active=True, starts_at__gte=timezone.now(), screen__is_active=True, screen__theatre__is_active=True)
        .select_related("screen", "screen__theatre")
        .order_by("screen__theatre__name", "starts_at")
    )
    venue_map = {}
    for show in shows:
        venue_map.setdefault(show.screen.theatre_id, {"theatre": show.screen.theatre, "shows": []})["shows"].append(show)
    return render(request, "booking/theatres.html", {"movie": movie, "venues": list(venue_map.values())})


@login_required
def seat_selection(request, show_id):
    show = get_object_or_404(
        Show.objects.select_related("movie", "screen", "screen__theatre"),
        pk=show_id,
        is_active=True,
        starts_at__gte=timezone.now(),
    )
    now = timezone.now()
    seat_list = list(show.screen.seats.all())
    booked_ids = set(BookingSeat.objects.filter(show=show).values_list("seat_id", flat=True))
    active_holds = SeatHold.objects.filter(show=show, expires_at__gt=now).select_related("user")
    holds_by_seat = {hold.seat_id: hold for hold in active_holds}
    rows = {}
    for seat in seat_list:
        hold = holds_by_seat.get(seat.id)
        if seat.id in booked_ids:
            state = "booked"
        elif hold and hold.user_id != request.user.id:
            state = "held"
        elif hold:
            state = "mine"
        else:
            state = "available"
        rows.setdefault(seat.row_label, []).append(
            {"seat": seat, "state": state, "price": show.price_for(seat), "expires_at": hold.expires_at if hold else None}
        )
    return render(
        request,
        "booking/seats.html",
        {"show": show, "rows": rows.items(), "hold_seconds": 300},
    )


@login_required
@require_POST
def hold_seats(request, show_id):
    show = get_object_or_404(Show, pk=show_id, is_active=True, starts_at__gte=timezone.now())
    try:
        payload = json.loads(request.body or "{}")
        seat_ids = list(dict.fromkeys(int(value) for value in payload.get("seat_ids", [])))
    except (ValueError, TypeError, json.JSONDecodeError):
        return JsonResponse({"error": "Invalid seat selection."}, status=400)
    if len(seat_ids) > 10:
        return JsonResponse({"error": "You can book up to 10 seats in one order."}, status=400)

    try:
        with transaction.atomic():
            seats = list(Seat.objects.select_for_update().filter(pk__in=seat_ids, screen_id=show.screen_id).order_by("pk"))
            if len(seats) != len(seat_ids):
                raise ValueError("One or more selected seats are not available for this show.")
            already_booked = set(BookingSeat.objects.filter(show=show, seat_id__in=seat_ids).values_list("seat_id", flat=True))
            if already_booked:
                raise ValueError("A selected seat was just booked. Please choose another seat.")

            now = timezone.now()
            for hold in SeatHold.objects.select_for_update().filter(show=show, seat_id__in=seat_ids):
                if hold.expires_at > now and hold.user_id != request.user.id:
                    raise ValueError("A selected seat is being held by another customer.")

            # The user's previous selection is replaced as one atomic operation.
            SeatHold.objects.filter(show=show, user=request.user).exclude(seat_id__in=seat_ids).delete()
            expiry = SeatHold.expiry_time()
            for seat in seats:
                SeatHold.objects.update_or_create(
                    show=show,
                    seat=seat,
                    defaults={"user": request.user, "expires_at": expiry},
                )
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=409)
    except IntegrityError:
        return JsonResponse({"error": "A seat was selected at the same time by another customer. Refresh and try again."}, status=409)

    return JsonResponse({"ok": True, "seat_ids": seat_ids, "expires_in": 300})


@login_required
def payment(request, show_id):
    show = get_object_or_404(
        Show.objects.select_related("movie", "screen", "screen__theatre"),
        pk=show_id,
        is_active=True,
        starts_at__gte=timezone.now(),
    )
    holds = list(
        SeatHold.objects.filter(show=show, user=request.user, expires_at__gt=timezone.now())
        .select_related("seat")
        .order_by("seat__row_label", "seat__seat_number")
    )
    if not holds:
        messages.error(request, "Your seat hold expired. Please select your seats again.")
        return redirect("booking:seats", show_id=show.id)
    total = sum((show.price_for(hold.seat) for hold in holds), Decimal("0.00"))
    return render(request, "booking/payment.html", {"show": show, "holds": holds, "total": total})


@login_required
@require_POST
def confirm_booking(request, show_id):
    show = get_object_or_404(
        Show.objects.select_related("movie", "screen", "screen__theatre"),
        pk=show_id,
        is_active=True,
        starts_at__gte=timezone.now(),
    )
    try:
        with transaction.atomic():
            holds = list(
                SeatHold.objects.select_for_update()
                .filter(show=show, user=request.user, expires_at__gt=timezone.now())
                .select_related("seat")
                .order_by("seat__row_label", "seat__seat_number")
            )
            if not holds:
                messages.error(request, "Your seat hold expired. Please select your seats again.")
                return redirect("booking:seats", show_id=show.id)
            seat_ids = [hold.seat_id for hold in holds]
            if BookingSeat.objects.filter(show=show, seat_id__in=seat_ids).exists():
                messages.error(request, "A seat is no longer available. Please choose seats again.")
                return redirect("booking:seats", show_id=show.id)

            prices = {hold.seat_id: show.price_for(hold.seat) for hold in holds}
            total = sum(prices.values(), Decimal("0.00"))
            booking = Booking.objects.create(
                user=request.user,
                show=show,
                total_amount=total,
                payment_reference=f"DEMO-{secrets.token_hex(4).upper()}",
            )
            BookingSeat.objects.bulk_create(
                [BookingSeat(booking=booking, show=show, seat_id=seat_id, price=price) for seat_id, price in prices.items()]
            )
            SeatHold.objects.filter(pk__in=[hold.pk for hold in holds]).delete()
    except IntegrityError:
        messages.error(request, "A seat was just booked by another customer. Please choose seats again.")
        return redirect("booking:seats", show_id=show.id)

    messages.success(request, "TICKETS BOOKED SUCCESSFULLY")
    return redirect("booking:ticket", booking_code=booking.booking_code)


@login_required
def ticket(request, booking_code):
    booking = get_object_or_404(
        Booking.objects.select_related("show__movie", "show__screen", "show__screen__theatre", "user").prefetch_related("booking_seats__seat"),
        booking_code=booking_code.upper(),
    )
    if booking.user_id != request.user.id and not request.user.is_staff:
        return redirect("booking:home")
    qr_content = f"CINEMAPASS|{booking.booking_code}|{booking.show.movie.title}"
    qr = qrcode.make(qr_content)
    buffer = io.BytesIO()
    qr.save(buffer, format="PNG")
    qr_image = base64.b64encode(buffer.getvalue()).decode("ascii")
    return render(request, "booking/ticket.html", {"booking": booking, "qr_image": qr_image})


def search_suggestions(request):
    query = request.GET.get("q", "").strip()
    movies = Movie.objects.filter(is_active=True)
    if query:
        movies = movies.filter(Q(title__icontains=query) | Q(genre__icontains=query) | Q(language__icontains=query))
    results = [{"title": movie.title, "url": reverse("booking:movie_detail", args=[movie.slug]), "genre": movie.genre} for movie in movies[:6]]
    return JsonResponse({"results": results})


def signup(request):
    if request.user.is_authenticated:
        return redirect("booking:home")
    form = SignUpForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        next_url = request.GET.get("next") or request.POST.get("next", "")
        if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
            return redirect(next_url)
        return redirect("booking:home")
    return render(request, "booking/signup.html", {"form": form})
