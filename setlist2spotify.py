import requests
import spotipy
import requests
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

def create_deezer_playlist(artist_name, songs, date, access_token):
    try:
        # Get user ID
        user_response = requests.get(
            "https://api.deezer.com/user/me",
            params={'access_token': access_token}
        )
        if user_response.status_code != 200:
            print("Failed to fetch Deezer user info.")
            return None
        user_id = user_response.json().get('id')
        if not user_id:
            return None

        # Create playlist
        playlist_name = f"{artist_name} Setlist - {date}"
        create_response = requests.post(
            f"https://api.deezer.com/user/{user_id}/playlists",
            params={'access_token': access_token, 'title': playlist_name}
        )
        if create_response.status_code not in [200, 201]:
            print("Failed to create Deezer playlist.")
            return None
        playlist_id = create_response.json().get('id')
        if not playlist_id:
            return None

        # Search and collect track IDs
        track_ids = []
        for song in songs:
            query = f'track:"{song}" artist:"{artist_name}"'
            search_response = requests.get(
                "https://api.deezer.com/search/track",
                params={'q': query, 'access_token': access_token}
            )
            if search_response.status_code == 200 and search_response.json().get('data'):
                track_ids.append(str(search_response.json()['data'][0]['id']))

        # Add tracks to playlist
        if track_ids:
            add_response = requests.post(
                f"https://api.deezer.com/playlist/{playlist_id}/tracks",
                params={'access_token': access_token, 'songs': ','.join(track_ids)}
            )
            if add_response.status_code == 200:
                return f"https://deezer.com/playlist/{playlist_id}"
        return None
    except Exception as e:
        print(f"Deezer error: {e}")
        return None
