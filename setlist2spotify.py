import requests
import spotipy
from datetime import datetime
import os

# Configuration from environment variables
SETLISTFM_API_KEY = os.environ.get('SETLISTFM_API_KEY')
SPOTIFY_CLIENT_ID = os.environ.get('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.environ.get('SPOTIFY_CLIENT_SECRET')


def get_latest_setlist(artist_name):
    headers = {
        "x-api-key": SETLISTFM_API_KEY,
        "Accept": "application/json"
    }
    params = {"artistName": artist_name, "p": 1}

    try:
        response = requests.get(
            "https://api.setlist.fm/rest/1.0/search/setlists",
            headers=headers,
            params=params
        )
        response.raise_for_status()

        setlists = response.json().get("setlist", [])
        
        for setlist in setlists:
            if setlist.get("sets") and setlist["sets"].get("set"):
                songs = []
                for set_group in setlist["sets"]["set"]:
                    for song in set_group.get("song", []):
                        if song.get("name"):
                            songs.append(song["name"])
                if songs:
                    return songs, setlist.get("eventDate", "")
        return None, None

    except requests.exceptions.RequestException as e:
        print(f"Error fetching setlist: {e}")
        return None, None

def create_spotify_playlist(artist_name, songs, date, access_token):
    sp = spotipy.Spotify(auth=access_token)
    
    try:
        user_id = sp.current_user()["id"]
        playlist_name = f"{artist_name} Setlist - {date}"
        playlist = sp.user_playlist_create(
            user=user_id,
            name=playlist_name,
            public=False
        )

        track_uris = []
        for song in songs:
            result = sp.search(q=f"track:{song} artist:{artist_name}", type="track", limit=1)
            if result["tracks"]["items"]:
                track_uris.append(result["tracks"]["items"][0]["uri"])
            else:
                print(f"Could not find track: {song}")

        if track_uris:
            sp.playlist_add_items(playlist["id"], track_uris)
            return playlist["external_urls"]["spotify"]
        return None

    except Exception as e:
        print(f"Spotify error: {e}")
        return None