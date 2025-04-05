import requests
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from datetime import datetime
import os

# Configuration from environment variables
SETLISTFM_API_KEY = os.environ.get('SETLISTFM_API_KEY')
SPOTIFY_CLIENT_ID = os.environ.get('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.environ.get('SPOTIFY_CLIENT_SECRET')
SPOTIFY_REDIRECT_URI = os.environ.get('SPOTIFY_REDIRECT_URI', 'http://localhost:8050/callback')

def get_latest_setlist(artist_name):
    headers = {
        "x-api-key": SETLISTFM_API_KEY,
        "Accept": "application/json"
    }
    params = {
        "artistName": artist_name,
        "p": 1  # Start with first page
    }

    try:
        response = requests.get(
            "https://api.setlist.fm/rest/1.0/search/setlists",
            headers=headers,
            params=params
        )
        response.raise_for_status()

        setlists = response.json().get("setlist", [])
        
        for setlist in setlists:
            # Check if there are songs in the setlist
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

def create_spotify_playlist(artist_name, songs, date):
    # Authenticate with Spotify
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIFY_REDIRECT_URI,
        scope="playlist-modify-private"
    ))

    # Get user ID
    user_id = sp.current_user()["id"]
    
    # Create playlist
    playlist_name = f"{artist_name} Setlist - {date}"
    playlist = sp.user_playlist_create(
        user=user_id,
        name=playlist_name,
        public=False
    )

    # Search for tracks and collect URIs
    track_uris = []
    for song in songs:
        result = sp.search(q=f"track:{song} artist:{artist_name}", type="track", limit=1)
        if result["tracks"]["items"]:
            track_uris.append(result["tracks"]["items"][0]["uri"])
        else:
            print(f"Could not find track: {song}")

    # Add tracks to playlist
    if track_uris:
        sp.playlist_add_items(playlist["id"], track_uris)
        print(f"Created playlist: {playlist_name} with {len(track_uris)} songs!")
        return playlist["external_urls"]["spotify"]
    return None

if __name__ == "__main__":
    artist = input("Enter artist name: ")
    songs, date = get_latest_setlist(artist)
    
    if not songs:
        print("No recent setlist found or error occurred.")
        exit()

    print(f"Found {len(songs)} songs from {date}")
    playlist_url = create_spotify_playlist(artist, songs, date)
    
    if playlist_url:
        print(f"Playlist created successfully: {playlist_url}")
    else:
        print("Failed to create playlist")