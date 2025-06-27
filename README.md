# Setlist2YouTubeMusic - Convert Concert Setlists to YouTube Music Playlists
Convert the latest artist setlist into a YouTube Music playlist

# Get API Keys and Credentials:

- **Setlist.fm**: Create an account at [setlist.fm](https://www.setlist.fm/) and get an API key from their developer portal.
- **Google Cloud Platform**: 
  1. Create a project at [Google Cloud Console](https://console.cloud.google.com/)
  2. Enable "YouTube Data API v3"
  3. Create OAuth 2.0 credentials:
     - Application type: "Web application"
     - Add authorized redirect URIs:
       - `https://yourdomain.com/callback` (your production URL)
       - `http://localhost:8050/callback` (for development)

## Set up redirect URI:
- In your Google Cloud credentials, add both your production URL (`https://yourdomain.com/callback`) and local development URL (`http://localhost:8050/callback`) as authorized redirect URIs.

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
   GOOGLE_CLIENT_ID=your_google_client_id
   GOOGLE_CLIENT_SECRET=your_google_client_secret
   GOOGLE_REDIRECT_URI=http://localhost:8050/callback  # Or your production URL
   FLASK_SECRET_KEY=your_flask_secret_key
   ```

3. **Build and Run the Docker Containers**
   ```bash
   docker-compose up --build -d
   ```
  
## Usage

1. **Access the Application**
   Open your web browser and navigate to `http://localhost:8050`.

2. **Connect YouTube Account**
   Click on the "Connect YouTube Account" button and log in with your Google account.

3. **Create a Playlist**
   Enter an artist name in the input field, click "Validate Setlist" to preview songs, then click "Create Playlist" to generate a new YouTube Music playlist with the latest setlist.

# Features
- Creates private YouTube Music playlists
- Preview setlists before creating playlists
- Clear session to switch YouTube accounts
- Responsive design with dark theme

# Notes:
- The app creates private playlists by default
- Playlist creation might take 1-2 minutes depending on setlist size
- Some songs might not be found if:
  - They're not available on YouTube Music
  - The naming doesn't match exactly
  - The artist name differs between sources
- The date in the playlist name comes from setlist.fm data
- Requires a Google account with YouTube access

# Troubleshooting
If you encounter HTTPS errors in production:
1. Ensure your reverse proxy is properly configured with:
   ```nginx
   proxy_set_header X-Forwarded-Proto $scheme;
   ```
2. Verify your environment variables match your deployment environment
3. Check that your redirect URIs in Google Cloud Console exactly match your application URLs