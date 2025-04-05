# dash-setlist2spotify
convert latest artist setlist to spotify playlist

# Get API Keys:

- **Setlist.fm**: Create an account at [setlist.fm](https://www.setlist.fm/) and get an API key from their developer portal.
- **Spotify**: Create a Spotify Developer account and register an app at [Spotify Developer Dashboard](https://developer.spotify.com/dashboard).

# Set up redirect URI:

- In your Spotify Developer App settings, add `<your-url>/callback` as a redirect URI.

# How to use:

1. Fill in your API keys in the stack.env file.
2. Run `docker compose up`
3. Authenticate with Spotify when the browser window opens.

# Note:

- The app creates private playlists by default.
- Some songs might not be found if:
  - They're not available on Spotify.
  - The naming doesn't match exactly.
  - The artist name differs between sources.
- The date in the playlist name comes from setlist.fm data (might not always be available).