import os
import flask
from flask import session, redirect
import dash
from dash import dcc, html, Input, Output, State
from spotipy.oauth2 import SpotifyOAuth
from setlist2spotify import get_latest_setlist, create_spotify_playlist

# Configuration
SPOTIFY_REDIRECT_URI = os.environ.get('SPOTIFY_REDIRECT_URI', 'http://localhost:8050/callback')
SPOTIFY_CLIENT_ID = os.environ.get('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.environ.get('SPOTIFY_CLIENT_SECRET')

# Initialize Flask server
server = flask.Flask(__name__)
server.secret_key = os.environ.get('FLASK_SECRET_KEY', 'default-secret-key')

# Initialize Dash app
app = dash.Dash(__name__, server=server, url_base_pathname='/')

# App layout
app.layout = html.Div([
    dcc.Location(id='url', refresh=True),
    html.H1("Create Spotify Playlist from Concert Setlist"),
    dcc.Input(id='artist-input', type='text', placeholder='Enter artist name'),
    html.Button('Create Playlist', id='submit-button', n_clicks=0),
    html.Div(id='output-message')
])

# Spotify OAuth routes
@server.route('/auth')
def auth():
    sp_oauth = SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIFY_REDIRECT_URI,
        scope='playlist-modify-private'
    )
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@server.route('/')
def index():
    return app.index()

@server.route('/callback')
def callback():
    sp_oauth = SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIFY_REDIRECT_URI,
        scope='playlist-modify-private'
    )
    session.clear()
    code = flask.request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    session['access_token'] = token_info['access_token']
    return redirect('/')

# Dash callback
@app.callback(
    Output('output-message', 'children'),
    Input('submit-button', 'n_clicks'),
    State('artist-input', 'value'),
    prevent_initial_call=True
)
def create_playlist(n_clicks, artist_name):
    if not artist_name:
        return "Please enter an artist name."
    
    access_token = session.get('access_token')
    if not access_token:
        return "Authentication required. Please go to auth page"
    
    songs, date = get_latest_setlist(artist_name)
    if not songs:
        return "No recent setlist found for this artist."
    
    playlist_url = create_spotify_playlist(artist_name, songs, date, access_token)
    if playlist_url:
        return html.A('Playlist created! Open in Spotify', href=playlist_url, target='_blank')
    return "Failed to create playlist"

if __name__ == '__main__':
    app.run(port=8050, debug=True)