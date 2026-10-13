# Cinepass · Movie Ticket Booking System

A Django movie ticket booking starter with a responsive dark/light interface, movie search suggestions, theatre and showtime listings, seat selection with five-minute holds, a simulated INR checkout, printable QR tickets, customer accounts, and Django admin.

The data model supports multiple theatres. The demo seed command creates exactly one theatre, Aurora Cinemas, and one screen to get started.

## Requirements

- Python 3.12+
- MySQL 8.x for the intended database, or SQLite for a quick local preview
- The packages in `requirements.txt`

## Run locally on Windows

Open PowerShell in this project folder:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

For a quick preview, leave `DB_ENGINE=sqlite3` in `.env`. To use MySQL, create a database and edit `.env`:

```sql
CREATE DATABASE movie_tickets CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Set `DB_ENGINE=mysql`, then set `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, and `DB_PORT` in `.env` to match your MySQL server.

Create the tables and load the one-theatre demo catalogue:

```powershell
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_demo
python manage.py runserver
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000). The admin panel is at [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/).

## Admin workflow

1. Sign in at `/admin/` with the superuser created above.
2. Add movies in **Movies**. Upload a poster using **Poster image** (JPEG, PNG, or another supported image format). The uploaded image appears on the home page and movie detail page. You can instead provide a poster image URL; if neither is set, the site creates a poster-style graphic from the movie title and accent colour.
3. Add theatres in **Theatres** and add a screen under each theatre. The demo creates one theatre and one screen for you.
4. From **Screens**, select a screen and run **Generate default 8-row × 10-seat layout**. The seed command has already generated this layout for the demo screen.
5. Add showtimes under **Shows**, choosing a movie, screen, date/time, and standard and premium seat prices.

Add another theatre by creating it in the admin, adding its screens and seat layouts, then adding shows for those screens. The public theatre list groups showtimes by theatre automatically.

## Booking flow

Customers can create an account, select a movie, choose a theatre and showtime, and select up to 10 seats. Selecting seats writes a five-minute hold to the database. The server checks seat holds again when confirming checkout. The ticket page shows the booking code, show details, seats, QR code, and print action.

**The checkout is a demo only.** It does not integrate with Razorpay, Stripe, UPI, cards, or wallets and does not collect payment credentials or charge money. Connect a payment provider and confirm payment server-side before using this for real transactions.

## Configuration notes

- `DEBUG=True` and the development secret in `.env.example` are for local use. Set a private `SECRET_KEY`, `DEBUG=False`, and production `ALLOWED_HOSTS` before deployment.
- Uploaded posters are saved under `media/movie_posters/`. Django serves these files automatically while `DEBUG=True`; configure persistent media storage or web-server media serving for production.
- Seat holds expire after five minutes; expired holds are ignored and can be reclaimed by a later customer.
- Site theme choice is stored in the customer's browser using local storage.
