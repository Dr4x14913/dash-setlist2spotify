import os
import flask
from flask import session, redirect
import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
from urllib.parse import urlencode
import requests
from spotipy.oauth2 import SpotifyOAuth
from spotipy.cache_handler import CacheHandler
from spotipy import Spotify
from setlist2spotify import get_latest_setlist, create_spotify_playlist, create_deezer_playlist
import pandas as pd

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

DEEZER_REDIRECT_URI = os.environ.get('DEEZER_REDIRECT_URI', 'http://localhost:8050/deezer_callback')
DEEZER_CLIENT_ID = os.environ.get("DEEZER_CLIENT_ID")
DEEZER_CLIENT_SECRET = os.environ.get("DEEZER_CLIENT_SECRET")

# Initialize Flask server
server = flask.Flask(__name__)
server.secret_key = os.environ.get('FLASK_SECRET_KEY', 'default-secret-key')

# Initialize Dash app with Bootstrap
app = dash.Dash(__name__, server=server, url_base_pathname='/', external_stylesheets=[dbc.themes.BOOTSTRAP])

#-----------------------------------------------------------------------------------------------
#-- Dash app layout
#-----------------------------------------------------------------------------------------------
app.layout = dbc.Container(
    [
        dcc.Location(id='url', refresh=True),
        dbc.Row([
            dbc.Col(
                html.Div([
                    dbc.Button("Clear Session", id="clear-session-btn", color="dark", class_name="mx-1"),
                    html.Div(id="user-info", style={'display': 'flex', 'align-items': 'center'}),
                ], style={'display': 'flex', 'align-items': 'center'}),
                className="text-left",
                width=3
            ),
            dbc.Col(
                dcc.RadioItems(
                    id='service-selector',
                    options=[
                        {'label': ' Spotify', 'value': 'spotify'},
                        {'label': ' Deezer', 'value': 'deezer'}
                    ],
                    value='spotify',
                    inline=True,
                    labelStyle={'margin-right': '20px'}
                ),
                className="text-left",
                width=3
            ),
        ], className="text-left my-3"),
        dbc.Row(
            dbc.Col(
                html.H1(
                    "Create Playlist from Concert Setlist",
                    style={'color': '#1DB954'},
                    id='title'
                ),
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
            dbc.Col([
                dbc.Button('Validate setlist', id='submit-button', disabled=True, className="m-3"),
            ], width="auto"
            ),
            justify="center"
        ),
        dbc.Row(
            dbc.Col(
                html.Div(id='output-message'),
                width=12
            )
        ),
        dbc.Row(
            dbc.Col(
                html.Div(id='setlist-table-container'),
                width=12
            )
        ),
    ],
    fluid=True,
    style={'backgroundColor': '#191414', 'color': '#FFFFFF', 'padding': '20px'}
)

#-----------------------------------------------------------------------------------------------
#-- Routes
#-----------------------------------------------------------------------------------------------
@server.route('/')
def index():
    return app.index()

# Spotify OAuth routes
@server.route('/spot_auth')
def spot_auth():
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

# Deezer Auth Route
@server.route('/deezer_auth')
def deezer_auth():
    session.clear()
    params = {
        'app_id': DEEZER_CLIENT_ID,
        'redirect_uri': DEEZER_REDIRECT_URI,
        'perms': 'manage_library,delete_library'
    }
    auth_url = f"https://connect.deezer.com/oauth/auth.php?{urlencode(params)}"
    return redirect(auth_url)

# Spotify Callback Route
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

# Deezer Callback Route
@server.route('/deezer_callback')
def deezer_callback():
    code = flask.request.args.get('code')
    if not code:
        return "Authorization failed: No code returned.", 400

    # Exchange code for token
    token_url = "https://connect.deezer.com/oauth/access_token.php"
    params = {
        'app_id': DEEZER_CLIENT_ID,
        'secret': DEEZER_CLIENT_SECRET,
        'code': code
    }
    response = requests.get(token_url, params=params)
    if response.status_code != 200:
        return "Failed to obtain access token.", 400

    token_data = response.text  # Comes as query string
    access_token = token_data.split('=')[1].split('&')[0]
    session['deezer_access_token'] = access_token
    return redirect('/')

#-----------------------------------------------------------------------------------------------
#-- Dash callbacks
#-----------------------------------------------------------------------------------------------

@app.callback(
    Output('title', 'style'),
    Input('service-selector', 'value')
)
def update_title_color(service):
    return {'color': '#1DB954'} if service == 'spotify' else {'color': '#00C7F2'}

# Dash callback to show the connected user
@app.callback(
    Output('user-info', 'children'),
    [
        Input('url', 'pathname'),
        Input('service-selector', 'value'),
    ],
    prevent_initial_call=True
)
def update_user_info(pathname, service):
    if service == 'spotify':
        if not session.get('access_token'):
            return html.A(
                dbc.Button("Login to Spotify", color="success", outline=True, className="mx-1"),
                href="/spot_auth"
            )
        else:
            sp = Spotify(auth=session['access_token'])
            me = sp.me()
            return html.Span(f"Spotify: {me['display_name']}", style={'color': '#1DB954', 'margin-left': '10px'})

    elif service == 'deezer':
        if not session.get('deezer_access_token'):
            return html.A(
                dbc.Button("Login to Deezer", color="primary", outline=True, className="mx-1"),
                href="/deezer_auth"
            )
        else:
            user_info = requests.get(
                "https://api.deezer.com/user/me",
                params={'access_token': session['deezer_access_token']}
            ).json()
            return html.Span(f"Deezer: {user_info.get('name', 'User')}", style={'color': '#00C7F2', 'margin-left': '10px'})
    return html.Div()


@app.callback(
    Output('url', 'pathname'),
    Input('clear-session-btn', 'n_clicks'),
    prevent_initial_call=True
)
def clear_session(_):
    if _ is not None:
        session.clear()
    return '/'

# Dash callback to create playlist
@app.callback(
    [
        Output('output-message', 'children', allow_duplicate=True),
        Output('setlist-table-container', 'children'),
        Output('submit-button', 'disabled')
    ],
    Input('artist-input', 'value'),
    State('service-selector', 'value'),
    prevent_initial_call=True
)
def gen_table(artist_name, service):
    if not artist_name:
        return dbc.Alert("Please enter an artist name.", color="warning"), None, True

    if service == 'spotify' and not session.get('access_token'):
        return (
            dbc.Alert(
                ["Authentication required. ", html.A(dbc.Button("Login to Spotify", href="/spot_auth", className="ml-2"))],
                color="danger"
            ),
            None,
            True
        )
    elif service == 'deezer' and not session.get('deezer_access_token'):
        return (
            dbc.Alert(
                ["Authentication required. ", html.A(dbc.Button("Login to Deezer", href="/deezer_auth", className="ml-2"))],
                color="danger"
            ),
            None,
            True
        )

    songs, date = get_latest_setlist(artist_name)
    if not songs:
        return dbc.Alert("No recent setlist found for this artist.", color="warning"), None, True

    table_data = [{'Song': song,} for song in songs]
    table = [html.Label(date), dbc.Table.from_dataframe(pd.DataFrame(table_data), striped=True, bordered=True, hover=True, style={"fontSize": "0.8rem"})]

    return "", table, False

@app.callback(
    Output('output-message', 'children', allow_duplicate=True),
    Input('submit-button', 'n_clicks'),
    State('artist-input', 'value'),
    State('service-selector', 'value'),
    prevent_initial_call=True
)
def create_playlist(n_clicks, artist_name, service):
    if not artist_name:
        return dbc.Alert("Please enter an artist name.", color="warning")

    songs, date = get_latest_setlist(artist_name)
    if not songs:
        return dbc.Alert("No recent setlist found for this artist.", color="warning")

    if service == 'spotify':
        access_token = session.get('access_token')
        if not access_token:
            return dbc.Alert("Spotify authentication required.", color="danger")
        playlist_url = create_spotify_playlist(artist_name, songs, date, access_token)
    elif service == 'deezer':
        access_token = session.get('deezer_access_token')
        if not access_token:
            return dbc.Alert("Deezer authentication required.", color="danger")
        playlist_url = create_deezer_playlist(artist_name, songs, date, access_token)
    else:
        return dbc.Alert("Invalid service.", color="danger")


    if playlist_url:
        return dbc.Alert(html.A('Playlist created! Open in Spotify', href=playlist_url, target='_blank'), color="success")
    return dbc.Alert("Failed to create playlist", color="danger")

#-----------------------------------------------------------------------------------------------
#-- Main
#-----------------------------------------------------------------------------------------------
if __name__ == '__main__':
    app.run(port=8050, debug=True, threaded=True)
