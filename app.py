import os
import flask
from flask import session, redirect
import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
from spotipy.oauth2 import SpotifyOAuth
from spotipy.cache_handler import CacheHandler
from spotipy import Spotify
from setlist2spotify import get_latest_setlist, create_spotify_playlist


class FlaskSessionCacheHandler(CacheHandler):
    def __init__(self, session_key='token_info'):
        self.session_key = session_key

    def get_cached_token(self):
        return session.get(self.session_key)

    def save_token_to_cache(self, token_info):
        session[self.session_key] = token_info

# Configuration
SPOTIFY_REDIRECT_URI = os.environ.get('SPOTIFY_REDIRECT_URI', 'http://localhost:8050/callback')
SPOTIFY_CLIENT_ID = os.environ.get('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.environ.get('SPOTIFY_CLIENT_SECRET')


# Initialize Flask server
server = flask.Flask(__name__)
server.secret_key = os.environ.get('FLASK_SECRET_KEY', 'default-secret-key')

# Initialize Dash app with Bootstrap
app = dash.Dash(__name__, server=server, url_base_pathname='/', external_stylesheets=[dbc.themes.BOOTSTRAP])

# App layout with dbc components
app.layout = dbc.Container(
    [
        dcc.Location(id='url', refresh=True),
        dbc.Row(
            dbc.Col(
                html.H1("Create Spotify Playlist from Concert Setlist", style={'color': '#1DB954'}),
                width=12,
                className="text-center mb-4"
            )
        ),
        dbc.Row(
            dbc.Col(
                dbc.Input(id='artist-input', type='text', placeholder='Enter artist name', className="mb-3"),
                width=6
            ),
            justify="center"
        ),
        dbc.Row(
            dbc.Col(
                dbc.Button('Create Playlist', id='submit-button', n_clicks=0, color="success", className="mb-3"),
                width="auto"
            ),
            justify="center"
        ),
        dbc.Row(
            dbc.Col(
                dbc.Button("Show session", id="showsession"),
                width="auto"
            ),
            justify="center"
        ),
        dbc.Row(
            dbc.Col(
                html.Div(id='output-message'),
                width=12
            )
        )
    ],
    fluid=True,
    style={'backgroundColor': '#191414', 'color': '#FFFFFF', 'padding': '20px'}
)

# Spotify OAuth routes
@server.route('/auth')
def auth():
    session.clear()
    sp_oauth = SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIFY_REDIRECT_URI,
        scope='playlist-modify-private user-read-private',
        cache_handler=FlaskSessionCacheHandler(),
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
        scope='playlist-modify-private user-read-private',
        cache_handler=FlaskSessionCacheHandler(),
    )
    code = flask.request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    session['access_token'] = token_info['access_token']
    return redirect('/')

# Dash callback
@app.callback(
        Output('output-message', 'children', allow_duplicate=True),
        Input("showsession", "n_clicks"),
        prevent_initial_call=True,
)
def showsession(_):
    if _ is None:
        return dash.no_update
    sp = Spotify(auth=session['access_token'])
    me = sp.me()
    print(me, flush=True)  # Debug info
    return dbc.Alert(f"{me['display_name']}", color="info")

@app.callback(
    Output('output-message', 'children'),
    Input('submit-button', 'n_clicks'),
    State('artist-input', 'value'),
    prevent_initial_call=True
)
def create_playlist(n_clicks, artist_name):
    if not artist_name:
        return dbc.Alert("Please enter an artist name.", color="warning")

    access_token = session.get('access_token')
    if not access_token:
        return dbc.Alert(
            [
                "Authentication required. ",
                html.A(dbc.Button("Go to Auth Page", color="primary"), href="/auth", className="ml-2")
            ],
            color="danger"
        )

    songs, date = get_latest_setlist(artist_name)
    if not songs:
        return dbc.Alert("No recent setlist found for this artist.", color="warning")

    playlist_url = create_spotify_playlist(artist_name, songs, date, access_token)
    if playlist_url:
        return dbc.Alert(html.A('Playlist created! Open in Spotify', href=playlist_url, target='_blank'), color="success")
    return dbc.Alert("Failed to create playlist", color="danger")

if __name__ == '__main__':
    app.run(port=8050, debug=True, threaded=True)