# Cinepass — Movie Ticket Booking System

A Django-based movie ticket booking web application featuring a responsive dark/light interface, movie discovery, theatre and showtime listings, interactive seat selection, temporary seat reservations, demo checkout, printable QR tickets, customer accounts, and a Django admin dashboard.

The data model supports multiple theatres. The demo seed command creates one theatre, **Aurora Cinemas**, with one screen and a default seat layout.

## Features

- **Movie discovery:** Rotating movie poster carousel and search suggestions.
- **Theatre listings:** Browse theatres, movies, and available showtimes.
- **Seat selection:** Interactive seating layout with five-minute seat holds.
- **Booking management:** Customer accounts and a personal booking history.
- **Digital tickets:** Booking codes, QR codes, and printable tickets.
- **Admin dashboard:** Manage movies, theatres, screens, seats, and shows.
- **Sales reporting:** Review confirmed sales, ticket counts, bookings, revenue trends, and top movies.
- **Responsive interface:** Dark/light theme and mobile-friendly layouts.
- **Database support:** MySQL for the intended setup, with SQLite available for a quick local preview.

## Tech Stack

- **Backend:** Python, Django
- **Database:** MySQL 8.x or SQLite
- **Frontend:** HTML, CSS, JavaScript
- **Dependencies:** See `requirements.txt`

## Requirements

- Python 3.12 or later
- MySQL 8.x (optional if using SQLite)
- Git
- Packages listed in `requirements.txt`

## Installation and Setup

### 1. Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd movie-ticket-booking
```

Replace `YOUR_GITHUB_REPOSITORY_URL` with your repository's clone URL.

If you already have the project files, open PowerShell in the project root instead.

### 2. Create and activate a virtual environment

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure environment variables

Create your local `.env` file:

```powershell
Copy-Item .env.example .env
```

Keep `.env` private. Never commit your real database password or Django secret key.

### 5. Configure MySQL

Open MySQL Workbench and connect to your local MySQL server. Run the following SQL, replacing the sample password with a strong password of your choice.

```sql
CREATE DATABASE movie_tickets
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'movie_app'@'localhost'
    IDENTIFIED BY 'choose-a-strong-password';

ALTER USER 'movie_app'@'localhost'
    IDENTIFIED BY 'choose-a-strong-password';

GRANT ALL PRIVILEGES ON movie_tickets.*
    TO 'movie_app'@'localhost';
```

Update the corresponding values in `.env`, including `DB_PASSWORD`.

For a quick SQLite preview, configure:

```dotenv
DB_ENGINE=sqlite3
```

Use the database configuration names expected by your project's settings.

### 6. Run migrations and initialize demo data

```powershell
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_demo
```

The seed command creates the initial demo theatre, screen, and seating layout.

### 7. Start the development server

```powershell
python manage.py runserver
```

Open the application:

- Website: http://127.0.0.1:8000/
- Django admin: http://127.0.0.1:8000/admin/
- Sales report: http://127.0.0.1:8000/admin/sales-report/

## Admin Workflow

1. Sign in to Django admin using your superuser account.
2. Add movies and configure their posters, ratings, directors, cast, and release dates.
3. Add theatres and screens as needed.
4. Generate the default eight-row by ten-seat layout when required.
5. Create showtimes by selecting a movie, screen, date, time, and seat prices.
6. Open the sales report to review bookings and revenue.

The demo setup creates one theatre and one screen. Additional theatres can be added through the admin interface.

## Booking Flow

1. Create a customer account or sign in.
2. Select a movie, theatre, and showtime.
3. Choose up to ten seats.
4. Seats are held for five minutes while the customer proceeds to checkout.
5. Complete the simulated checkout.
6. Open **My Bookings** to review bookings and print tickets with QR codes.

The application checks seat availability again when confirming checkout.

## Payment Disclaimer

**This project uses simulated checkout only.**

It does not integrate with Razorpay, Stripe, UPI, credit cards, debit cards, or wallets. It does not charge money or process real payments.

A real deployment would require a payment provider integration, server-side payment verification, and appropriate security measures.

## Configuration and Security

- The sample development secret key and `DEBUG=True` configuration are intended only for local development.
- Use a private `SECRET_KEY`, `DEBUG=False`, and appropriate `ALLOWED_HOSTS` in production.
- Uploaded posters are stored under `media/movie_posters/`.
- Configure persistent media storage and appropriate web-server or storage access for production.
- Seat holds expire after five minutes; expired holds can be reclaimed.
- The selected theme is stored in browser local storage.
- Never publish real credentials, secret keys, or sensitive customer data.

## Future Improvements

- Integrate a real payment gateway.
- Deploy the application with production-grade configuration.
- Add automated tests for seat availability and booking concurrency.
- Improve booking notifications and email confirmations.

## License

No license has been specified yet. Add a license if you intend to permit others to reuse or modify the project.