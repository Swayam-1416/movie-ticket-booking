# Initial schema for the Cinepass booking app.
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]

    operations = [
        migrations.CreateModel(
            name="Movie",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=140)),
                ("slug", models.SlugField(max_length=160, unique=True)),
                ("synopsis", models.TextField()),
                ("genre", models.CharField(max_length=80)),
                ("language", models.CharField(default="Hindi", max_length=60)),
                ("duration_minutes", models.PositiveSmallIntegerField(default=140)),
                ("certificate", models.CharField(default="U/A", max_length=8)),
                ("release_date", models.DateField(blank=True, null=True)),
                ("poster_url", models.URLField(blank=True)),
                ("accent", models.CharField(default="#b68cff", help_text="Poster accent colour, for example #b68cff", max_length=7)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ["title"]},
        ),
        migrations.CreateModel(
            name="Theatre",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=140)),
                ("slug", models.SlugField(max_length=160, unique=True)),
                ("address", models.CharField(max_length=240)),
                ("city", models.CharField(default="Mumbai", max_length=100)),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={"verbose_name_plural": "theatres", "ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="Screen",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=80)),
                ("is_active", models.BooleanField(default=True)),
                ("theatre", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="screens", to="booking.theatre")),
            ],
            options={"ordering": ["theatre__name", "name"]},
        ),
        migrations.CreateModel(
            name="Seat",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("row_label", models.CharField(max_length=3)),
                ("seat_number", models.PositiveSmallIntegerField()),
                ("seat_type", models.CharField(choices=[("standard", "Standard"), ("premium", "Premium")], default="standard", max_length=12)),
                ("screen", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="seats", to="booking.screen")),
            ],
            options={"ordering": ["row_label", "seat_number"]},
        ),
        migrations.CreateModel(
            name="Show",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("starts_at", models.DateTimeField()),
                ("standard_price", models.DecimalField(decimal_places=2, default=220, max_digits=8)),
                ("premium_price", models.DecimalField(decimal_places=2, default=320, max_digits=8)),
                ("is_active", models.BooleanField(default=True)),
                ("movie", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="shows", to="booking.movie")),
                ("screen", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="shows", to="booking.screen")),
            ],
            options={"ordering": ["starts_at"]},
        ),
        migrations.CreateModel(
            name="Booking",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("booking_code", models.CharField(editable=False, max_length=12, unique=True)),
                ("status", models.CharField(choices=[("confirmed", "Confirmed")], default="confirmed", max_length=12)),
                ("total_amount", models.DecimalField(decimal_places=2, max_digits=9)),
                ("payment_reference", models.CharField(blank=True, max_length=32)),
                ("booked_at", models.DateTimeField(auto_now_add=True)),
                ("show", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="bookings", to="booking.show")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="movie_bookings", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="SeatHold",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("expires_at", models.DateTimeField(db_index=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("seat", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="holds", to="booking.seat")),
                ("show", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="seat_holds", to="booking.show")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="seat_holds", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="BookingSeat",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("price", models.DecimalField(decimal_places=2, max_digits=8)),
                ("booking", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="booking_seats", to="booking.booking")),
                ("seat", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="booked_for_shows", to="booking.seat")),
                ("show", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="booked_seats", to="booking.show")),
            ],
            options={"ordering": ["seat__row_label", "seat__seat_number"]},
        ),
        migrations.AddConstraint(
            model_name="screen",
            constraint=models.UniqueConstraint(fields=("theatre", "name"), name="unique_screen_name_per_theatre"),
        ),
        migrations.AddConstraint(
            model_name="seat",
            constraint=models.UniqueConstraint(fields=("screen", "row_label", "seat_number"), name="unique_seat_per_screen"),
        ),
        migrations.AddConstraint(
            model_name="seathold",
            constraint=models.UniqueConstraint(fields=("show", "seat"), name="unique_hold_per_show_seat"),
        ),
        migrations.AddConstraint(
            model_name="bookingseat",
            constraint=models.UniqueConstraint(fields=("show", "seat"), name="unique_booked_seat_per_show"),
        ),
        migrations.AddIndex(model_name="show", index=models.Index(fields=["movie", "starts_at"], name="idx_show_movie_start")),
        migrations.AddIndex(model_name="show", index=models.Index(fields=["screen", "starts_at"], name="idx_show_screen_start")),
    ]
