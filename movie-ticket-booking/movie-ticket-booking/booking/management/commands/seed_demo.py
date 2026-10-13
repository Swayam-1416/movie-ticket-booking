from datetime import datetime, time, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from booking.models import Movie, Screen, Seat, Show, Theatre


MOVIES = [
    {
        "title": "The Last Monsoon",
        "slug": "the-last-monsoon",
        "genre": "Drama · Romance",
        "language": "Hindi",
        "duration_minutes": 132,
        "certificate": "U/A",
        "accent": "#9b7cff",
        "synopsis": "In a rain-washed coastal town, a travelling photographer returns home and discovers that some goodbyes were never really finished. A lyrical story about memory, family and finding your way back.",
    },
    {
        "title": "Neon Run",
        "slug": "neon-run",
        "genre": "Action · Thriller",
        "language": "Hindi",
        "duration_minutes": 146,
        "certificate": "U/A",
        "accent": "#ef7a65",
        "synopsis": "One night. One impossible delivery. A Mumbai bike courier is pulled into a city-wide chase where every turn reveals a new player and nobody is who they claim to be.",
    },
    {
        "title": "Small Wonders",
        "slug": "small-wonders",
        "genre": "Comedy · Family",
        "language": "English",
        "duration_minutes": 118,
        "certificate": "U",
        "accent": "#69c7a3",
        "synopsis": "A curious eight-year-old, a sleepy neighbourhood and one very stubborn stray dog make for a summer full of small surprises and big-hearted laughs.",
    },
]


class Command(BaseCommand):
    help = "Create one sample theatre, a screen, sample movies, seats and future showtimes. Safe to run more than once."

    def handle(self, *args, **options):
        theatre, _ = Theatre.objects.get_or_create(
            slug="aurora-downtown",
            defaults={"name": "Aurora Cinemas", "address": "18 Riverside Road", "city": "Mumbai", "is_active": True},
        )
        screen, _ = Screen.objects.get_or_create(theatre=theatre, name="Screen 1", defaults={"is_active": True})
        if not screen.seats.exists():
            Seat.objects.bulk_create(
                [
                    Seat(
                        screen=screen,
                        row_label=chr(65 + row),
                        seat_number=number,
                        seat_type=Seat.SeatType.PREMIUM if row >= 6 else Seat.SeatType.STANDARD,
                    )
                    for row in range(8)
                    for number in range(1, 11)
                ]
            )

        movies = [Movie.objects.update_or_create(slug=data["slug"], defaults=data)[0] for data in MOVIES]
        local_now = timezone.localtime(timezone.now())
        for movie in movies:
            for day_offset in range(1, 8):
                show_date = local_now.date() + timedelta(days=day_offset)
                for show_time in (time(16, 30), time(20, 0)):
                    starts_at = timezone.make_aware(datetime.combine(show_date, show_time), timezone.get_current_timezone())
                    Show.objects.get_or_create(
                        movie=movie,
                        screen=screen,
                        starts_at=starts_at,
                        defaults={"standard_price": 220, "premium_price": 320, "is_active": True},
                    )
        self.stdout.write(self.style.SUCCESS(f"Demo data ready: 1 theatre, {len(movies)} movies and future showtimes."))
