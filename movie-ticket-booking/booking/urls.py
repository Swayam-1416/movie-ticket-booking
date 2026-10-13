from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = "booking"

urlpatterns = [
    path("", views.home, name="home"),
    path("movies/<slug:slug>/", views.movie_detail, name="movie_detail"),
    path("movies/<slug:slug>/theatres/", views.theatre_list, name="theatres"),
    path("shows/<int:show_id>/seats/", views.seat_selection, name="seats"),
    path("shows/<int:show_id>/hold-seats/", views.hold_seats, name="hold_seats"),
    path("shows/<int:show_id>/payment/", views.payment, name="payment"),
    path("shows/<int:show_id>/confirm/", views.confirm_booking, name="confirm_booking"),
    path("tickets/<str:booking_code>/", views.ticket, name="ticket"),
    path("search/suggestions/", views.search_suggestions, name="search_suggestions"),
    path("accounts/login/", auth_views.LoginView.as_view(template_name="booking/login.html"), name="login"),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("accounts/signup/", views.signup, name="signup"),
]
