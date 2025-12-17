from django.urls import path
from .views import spotify_login, spotify_callback, currently_playing, currently_playing_json

urlpatterns = [
    path("spotify/login/", spotify_login, name="spotify_login"),
    path("spotify/callback/", spotify_callback, name="spotify_callback"),
    path("", currently_playing, name="currently_playing"),
    path("currently_playing/json/", currently_playing_json, name="currently_playing_json"),
]
