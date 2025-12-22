import requests
from django.shortcuts import render, redirect
from django.conf import settings
from urllib.parse import urlencode
from django.http import JsonResponse

SPOTIFY_PLAYER_API = "https://api.spotify.com/v1/me/player"

# Step 3.1: Redirect user to Spotify login
def spotify_login(request):
    scope = "user-read-currently-playing user-read-playback-state"
    params = urlencode({
        "client_id": settings.SPOTIFY_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": settings.SPOTIFY_REDIRECT_URI,
        "scope": scope,
        "prompt": "login"
    })
    url = f"https://accounts.spotify.com/authorize?{params}"
    return redirect(url)

# Step 3.2: Callback to get access token
def spotify_callback(request):
    code = request.GET.get("code")
    if not code:
        return redirect("spotify_login")

    response = requests.post(
        "https://accounts.spotify.com/api/token",
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": settings.SPOTIFY_REDIRECT_URI,
            "client_id": settings.SPOTIFY_CLIENT_ID,
            "client_secret": settings.SPOTIFY_CLIENT_SECRET,
        },
    )
    response.raise_for_status()
    data = response.json()
    request.session["spotify_token"] = data["access_token"]
    request.session["spotify_refresh_token"] = data.get("refresh_token")  # store refresh token
    return redirect("currently_playing")


# Step 3.3: Show currently playing track
def currently_playing(request):
    token = request.session.get("spotify_token")
    if not token:
        return redirect("spotify_login")

    # Fetch currently playing track
    track_data = None
    try:
        response = requests.get(
            f"{SPOTIFY_PLAYER_API}/currently-playing",
            headers={"Authorization": f"Bearer {token}"}
        )

        if response.status_code != 204 and response.content:
            data = response.json()
            if data.get("item"):
                progress_ms = data["progress_ms"]
                duration_ms = data["item"]["duration_ms"]
                track_data = {
                    "name": data["item"]["name"],
                    "artist": ", ".join([a["name"] for a in data["item"]["artists"]]),
                    "album_image": data["item"]["album"]["images"][0]["url"],
                    "is_playing": data["is_playing"],
                    "progress_ms": progress_ms,
                    "duration_ms": duration_ms,
                    "progress_percent": (progress_ms / duration_ms) * 100,  # <- precompute
                }

    except ValueError:
        track_data = None

    # Fetch user info
    user_data = None
    try:
        response = requests.get(
            "https://api.spotify.com/v1/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        if response.status_code == 200:
            data = response.json()
            user_data = {
                "name": data.get("display_name", "Unknown"),
                "image": data["images"][0]["url"] if data.get("images") else None
            }
    except ValueError:
        user_data = None

    return render(request, "currently_playing.html", {
        "track": track_data,
        "user": user_data
    })


def currently_playing_json(request):
    token = request.session.get("spotify_token")
    if not token:
        return JsonResponse({"error": "not authenticated"}, status=401)

    response = requests.get(
        f"{SPOTIFY_PLAYER_API}/currently-playing",
        headers={"Authorization": f"Bearer {token}"}
    )

    if response.status_code == 204 or not response.content:
        return JsonResponse({"track": None})
    
    try:
        data = response.json()
    except ValueError:
        return JsonResponse({"track": None})

    if not data.get("item"):
        return JsonResponse({"track": None})
    
    track_info = {
        "name": data["item"]["name"],
        "artist": ", ".join([a["name"] for a in data["item"]["artists"]]),
        "album_image": data["item"]["album"]["images"][0]["url"],
        "is_playing": data["is_playing"],
        "progress_ms": data["progress_ms"],
        "duration_ms": data["item"]["duration_ms"],
    }

    return JsonResponse({"track": track_info})


def spotify_logout(request):
    request.session.flush()
    return redirect("logged_out")

def logged_out(request):
    return render(request, "logged_out.html")


