# Setlist2Spotify - Convert Concert Setlists to Spotify Playlists
Convert latest artist setlist to spotify playlist

# Get API Keys:

- **Setlist.fm**: Create an account at [setlist.fm](https://www.setlist.fm/) and get an API key from their developer portal.
- **Spotify**: Create a Spotify Developer account and register an app at [Spotify Developer Dashboard](https://developer.spotify.com/dashboard).

## Set up redirect URI:
- In your Spotify Developer App settings, add `<your-url>/callback` as a redirect URI. You can also add http://localhost:8050/callback for developpment purposes.

# Installation

### Prerequisites
- Docker
- Python

### Steps to Set Up
1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/setlist2spotify.git
   cd setlist2spotify
   ```

2. **Create a `.env` File**
   Create a file named `stack.env` in the project root directory and add your environment variables:
   ```
   SETLISTFM_API_KEY=your_setlistfm_api_key
   SPOTIFY_CLIENT_ID=your_spotify_client_id
   SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
   SPOTIFY_REDIRECT_URI=http://localhost:8050/callback # Or your url
   FLASK_SECRET_KEY=your_flask_secret_key
   ```

3. **Build and Run the Docker Containers**
   ```bash
   docker-compose up --build -d
   ```
  
## Usage

1. **Access the Application**
   Open your web browser and navigate to `http://localhost:8050`.

2. **Login with Spotify**
   Click on the "Go to Auth Page" button and log in with your Spotify account.

3. **Create a Playlist**
   Enter an artist name in the input field, click "Create Playlist," and Setlist2Spotify will create a new playlist with the latest setlist songs.

# Note:
- The app creates private playlists by default.
- Some songs might not be found if:
  - They're not available on Spotify.
  - The naming doesn't match exactly.
  - The artist name differs between sources.
- The date in the playlist name comes from setlist.fm data (might not always be available).
