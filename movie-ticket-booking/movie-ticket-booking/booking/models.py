import secrets
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


class Movie(models.Model):
    title = models.CharField(max_length=140)
    slug = models.SlugField(max_length=160, unique=True)
    synopsis = models.TextField()
    genre = models.CharField(max_length=80)
    language = models.CharField(max_length=60, default="Hindi")
    duration_minutes = models.PositiveSmallIntegerField(default=140)
    certificate = models.CharField(max_length=8, default="U/A")
    release_date = models.DateField(null=True, blank=True)
    poster_url = models.URLField(blank=True)
    accent = models.CharField(max_length=7, default="#b68cff", help_text="Poster accent colour, for example #b68cff")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title


class Theatre(models.Model):
    name = models.CharField(max_length=140)
    slug = models.SlugField(max_length=160, unique=True)
    address = models.CharField(max_length=240)
    city = models.CharField(max_length=100, default="Mumbai")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "theatres"

    def __str__(self):
        return f"{self.name} · {self.city}"


class Screen(models.Model):
    theatre = models.ForeignKey(Theatre, related_name="screens", on_delete=models.CASCADE)
    name = models.CharField(max_length=80)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["theatre__name", "name"]
        constraints = [models.UniqueConstraint(fields=["theatre", "name"], name="unique_screen_name_per_theatre")]

    def __str__(self):
        return f"{self.theatre.name} · {self.name}"


class Seat(models.Model):
    class SeatType(models.TextChoices):
        STANDARD = "standard", "Standard"
        PREMIUM = "premium", "Premium"

    screen = models.ForeignKey(Screen, related_name="seats", on_delete=models.CASCADE)
    row_label = models.CharField(max_length=3)
    seat_number = models.PositiveSmallIntegerField()
    seat_type = models.CharField(max_length=12, choices=SeatType.choices, default=SeatType.STANDARD)

    class Meta:
        ordering = ["row_label", "seat_number"]
        constraints = [models.UniqueConstraint(fields=["screen", "row_label", "seat_number"], name="unique_seat_per_screen")]

    @property
    def label(self):
        return f"{self.row_label}{self.seat_number}"

    def __str__(self):
        return f"{self.screen.name} · {self.label}"


class Show(models.Model):
    movie = models.ForeignKey(Movie, related_name="shows", on_delete=models.CASCADE)
    screen = models.ForeignKey(Screen, related_name="shows", on_delete=models.CASCADE)
    starts_at = models.DateTimeField()
    standard_price = models.DecimalField(max_digits=8, decimal_places=2, default=220)
    premium_price = models.DecimalField(max_digits=8, decimal_places=2, default=320)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["starts_at"]
        indexes = [
            models.Index(fields=["movie", "starts_at"], name="idx_show_movie_start"),
            models.Index(fields=["screen", "starts_at"], name="idx_show_screen_start"),
        ]

    @property
    def theatre(self):
        return self.screen.theatre

    def price_for(self, seat):
        return self.premium_price if seat.seat_type == Seat.SeatType.PREMIUM else self.standard_price

    def __str__(self):
        return f"{self.movie.title} · {self.screen} · {timezone.localtime(self.starts_at):%d %b, %I:%M %p}"


class SeatHold(models.Model):
    show = models.ForeignKey(Show, related_name="seat_holds", on_delete=models.CASCADE)
    seat = models.ForeignKey(Seat, related_name="holds", on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="seat_holds", on_delete=models.CASCADE)
    expires_at = models.DateTimeField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["show", "seat"], name="unique_hold_per_show_seat")]

    @classmethod
    def expiry_time(cls):
        return timezone.now() + timedelta(minutes=5)


class Booking(models.Model):
    class Status(models.TextChoices):
        CONFIRMED = "confirmed", "Confirmed"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="movie_bookings", on_delete=models.PROTECT)
    show = models.ForeignKey(Show, related_name="bookings", on_delete=models.PROTECT)
    booking_code = models.CharField(max_length=12, unique=True, editable=False)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.CONFIRMED)
    total_amount = models.DecimalField(max_digits=9, decimal_places=2)
    payment_reference = models.CharField(max_length=32, blank=True)
    booked_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.booking_code:
            self.booking_code = secrets.token_hex(5).upper()
        super().save(*args, **kwargs)

    @property
    def seats_display(self):
        return ", ".join(f"{item.seat.row_label}{item.seat.seat_number}" for item in self.booking_seats.select_related("seat"))

    def __str__(self):
        return f"{self.booking_code} · {self.show.movie.title}"


class BookingSeat(models.Model):
    booking = models.ForeignKey(Booking, related_name="booking_seats", on_delete=models.CASCADE)
    show = models.ForeignKey(Show, related_name="booked_seats", on_delete=models.CASCADE)
    seat = models.ForeignKey(Seat, related_name="booked_for_shows", on_delete=models.PROTECT)
    price = models.DecimalField(max_digits=8, decimal_places=2)

    class Meta:
        ordering = ["seat__row_label", "seat__seat_number"]
        constraints = [models.UniqueConstraint(fields=["show", "seat"], name="unique_booked_seat_per_show")]
