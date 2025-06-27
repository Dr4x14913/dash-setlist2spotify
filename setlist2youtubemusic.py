import os
import requests
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime

# Configuration from environment variables
SETLISTFM_API_KEY = os.environ.get('SETLISTFM_API_KEY', 'WdCJj-S8gzRfK6cLwLWfMyVuuQhjiwuqJg7l')

def get_latest_setlist(artist_name):
    """Fetch the latest setlist for an artist from setlist.fm"""
    headers = {
        "x-api-key": SETLISTFM_API_KEY,
        "Accept": "application/json"
    }
    params = {"artistName": artist_name, "p": 1}
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
                real_name = None
                style = None
                place = None
                if setlist.get("artist"):
                    real_name = setlist['artist'].get("name")
                    style = setlist['artist'].get("disambiguation")
                if setlist.get("venue"):
                    place = setlist['venue'].get("name")
                return songs, setlist.get("eventDate", ""), real_name, style, place
    return None, None

def create_youtube_playlist(artist_name, songs, date, credentials):
    """Create a YouTube playlist from a setlist of songs"""
    # Build YouTube service with credentials
    youtube = build('youtube', 'v3', credentials=credentials)
    
    # Create playlist
    date_str = datetime.strptime(date, '%d-%m-%Y').strftime('%Y-%m-%d')
    playlist_name = f"{artist_name} Setlist - {date_str}"
    playlist_description = f"Concert setlist performed by {artist_name} on {date_str}"
    
    playlist = youtube.playlists().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": playlist_name,
                "description": playlist_description,
            },
            "status": {
                "privacyStatus": "private"
            }
        }
    ).execute()
    
    playlist_id = playlist["id"]
    
    # Search for each song and add to playlist
    for song in songs:
        # Search for song on YouTube
        search_response = youtube.search().list(
            q=f"{artist_name} {song} official",
            part="id",
            maxResults=1,
            type="video"
        ).execute()
        
        if search_response.get("items"):
            video_id = search_response["items"][0]["id"]["videoId"]
            
            # Add video to playlist
            youtube.playlistItems().insert(
                part="snippet",
                body={
                    "snippet": {
                        "playlistId": playlist_id,
                        "resourceId": {
                            "kind": "youtube#video",
                            "videoId": video_id
                        }
                    }
                }
            ).execute()
    
    # Return playlist URL
    return f"https://www.youtube.com/playlist?list={playlist_id}"