from django.urls import path

from . import views

urlpatterns = [
    path("", views.index_view, name="index"),
    
    path("desks", views.desks_view, name="desks"),
    path("desks/schedule", views.desks_schedule_view, name="desks_schedule"),
    path("desks/bookings", views.desks_bookings_view, name="desks_bookings"),
    path("api/desks", views.api_desks, name="api_desks"),
    path("api/desks/schedule", views.api_desks_schedule, name="api_desks_schedule"),
    path("api/desks/booked", views.api_desks_booked, name="api_desks_booked"),
    
    path("rooms", views.rooms_view, name="rooms"),
    path("rooms/bookings", views.rooms_bookings_view, name="rooms_bookings"),
    path("api/rooms", views.api_rooms, name="api_rooms"),
    path("api/rooms/booked", views.api_rooms_booked, name="api_rooms_booked"),
    
    path("profile", views.profile_view, name="profile"),
    
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register_view, name="register")
]
