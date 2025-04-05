# dash-setlist2spotify
convert latest artist setlist to spotify playlist

# Get API Keys:

- **Setlist.fm**: Create an account at [setlist.fm](https://www.setlist.fm/) and get an API key from their developer portal.
- **Spotify**: Create a Spotify Developer account and register an app at [Spotify Developer Dashboard](https://developer.spotify.com/dashboard).

# Set up redirect URI:

- In your Spotify Developer App settings, add `http://localhost:8080/callback` as a redirect URI.

# First-run authentication:

- When you first run the script, it will open a browser window for Spotify authentication.

# How to use:

1. Fill in your API keys in the docker-compose file.
4. Run `docker compose up`
3. Authenticate with Spotify when the browser window opens.

# Note:

- The app creates private playlists by default.
- Some songs might not be found if:
  - They're not available on Spotify.
  - The naming doesn't match exactly.
  - The artist name differs between sources.
- The date in the playlist name comes from setlist.fm data (might not always be available).

You can modify the playlist parameters (name, public/private status) by adjusting the `user_playlist_create` parameters in the `create_spotify_playlist` function.