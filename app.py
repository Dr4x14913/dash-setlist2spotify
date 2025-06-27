import os
import flask
from flask import session, redirect
import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from setlist2youtubemusic import get_latest_setlist, create_youtube_playlist
import pandas as pd
import requests

class FlaskSessionCacheHandler:
    def __init__(self, session_key='credentials'):
        self.session_key = session_key

    def get_cached_credentials(self):
        return session.get(self.session_key)

    def save_credentials_to_cache(self, credentials):
        session[self.session_key] = credentials

# Configuration
GOOGLE_REDIRECT_URI = os.environ.get('GOOGLE_REDIRECT_URI', 'http://localhost:8050/callback')
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
GOOGLE_SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']
if "https" not in GOOGLE_REDIRECT_URI:
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# Initialize Flask server
server = flask.Flask(__name__)
server.secret_key = os.environ.get('FLASK_SECRET_KEY', 'default-secret-key')

# Initialize Dash app with Bootstrap
app = dash.Dash(__name__, server=server, url_base_pathname='/', external_stylesheets=[dbc.themes.BOOTSTRAP])

# Dash app layout
app.layout = dbc.Container(
    [
        dcc.Location(id='url', refresh=True),
        dbc.Row([
            dbc.Col(
                html.Div([
                    dbc.Button("Clear Session", id="clear-session-btn", color="dark", class_name="mx-1"),
                    html.Div(id="user-info", style={'display': 'flex', 'align-items': 'center'}),
                ], style={'display': 'flex', 'align-items': 'center'}),
                width=12,
                className="text-left mt-3"
            )
        ]),
        dbc.Row(
            dbc.Col(
                html.H1("Create YouTube Playlist from Concert Setlist", style={'color': '#FF0000'}),
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
                dcc.Loading(id='setlist-table-container'),
                width=12
            )
        ),
    ],
    fluid=True,
    style={'backgroundColor': '#282828', 'color': '#FFFFFF', 'padding': '20px'}
)

# YouTube OAuth routes
@server.route('/auth')
def auth():
    session.clear()
    flow = Flow.from_client_config(
        client_config={
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://accounts.google.com/o/oauth2/token",
                "redirect_uris": [GOOGLE_REDIRECT_URI]
            }
        },
        scopes=GOOGLE_SCOPES,
        redirect_uri=GOOGLE_REDIRECT_URI
    )
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )
    session['state'] = state
    return redirect(authorization_url)

@server.route('/')
def index():
    return app.index()

@server.route('/callback')
def callback():
    state = session['state']
    flow = Flow.from_client_config(
        client_config={
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://accounts.google.com/o/oauth2/token",
                "redirect_uris": [GOOGLE_REDIRECT_URI]
            }
        },
        scopes=GOOGLE_SCOPES,
        state=state,
        redirect_uri=GOOGLE_REDIRECT_URI
    )
    flow.fetch_token(authorization_response=flask.request.url)
    credentials = flow.credentials
    session['credentials'] = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }
    return redirect('/')

@server.route('/logout')
def logout():
    # Revoke Google OAuth token
    credentials = session.get('credentials')
    if credentials:
        try:
            # Build revocation request
            revocation_url = "https://oauth2.googleapis.com/revoke"
            headers = {"Content-type": "application/x-www-form-urlencoded"}
            data = {"token": credentials['token']}
            
            # Send revocation request
            response = requests.post(
                revocation_url, 
                headers=headers, 
                data=data
            )
            response.raise_for_status()
        except Exception as e:
            print(f"Token revocation failed: {e}")
    
    # Clear session server-side
    session.clear()
    
    # Create redirect response
    response = redirect('/')
    
    # Delete session cookie client-side
    response.set_cookie('session', '', expires=0)
    return response

# Dash callback to show the connected user
@app.callback(
    Output('user-info', 'children'),
    Input('url', 'pathname'),
    prevent_initial_call=True
)
def update_user_info(pathname):
    if not session.get('credentials'):
        return html.A(dbc.Button("Connect YouTube Account", color="danger", outline=True), href="/auth")
    
    credentials_dict = session['credentials']
    credentials = Credentials(
        token=credentials_dict['token'],
        refresh_token=credentials_dict.get('refresh_token'),
        token_uri=credentials_dict['token_uri'],
        client_id=credentials_dict['client_id'],
        client_secret=credentials_dict['client_secret'],
        scopes=credentials_dict['scopes']
    )
    youtube = build('youtube', 'v3', credentials=credentials)
    response = youtube.channels().list(part='snippet', mine=True).execute()
    channel_name = response['items'][0]['snippet']['title']
    return html.Span(f"Connected as {channel_name}", style={"color":"#FF0000"})

@app.callback(
    Output('url', 'pathname'),
    Input('clear-session-btn', 'n_clicks'),
    prevent_initial_call=True
)
def clear_session(_):
    if _ is not None:
        return "/logout"
    return dash.no_update

# Dash callback to create playlist
@app.callback(
    [
        Output('output-message', 'children', allow_duplicate=True),
        Output('setlist-table-container', 'children'),
        Output('submit-button', 'disabled')
    ], 
    Input('artist-input', 'value'),
    prevent_initial_call=True
)
def gen_table(artist_name):
    if not artist_name:
        return dbc.Alert("Please enter an artist name.", color="warning"), None, True

    credentials = session.get('credentials')
    if not credentials:
        return dbc.Alert(
            [
                "Authentication required. ",
                html.A(dbc.Button("Connect YouTube Account", color="danger"), href="/auth", className="ml-2")
            ],
            color="danger"
        ), None, True
    try:
        songs, date, real_name, style, place = get_latest_setlist(artist_name)
    except Exception as e:
        error_msg = f"Error: {e}"
        print(error_msg, flush=True)
        return dbc.Alert(error_msg, color="danger")
    if not songs:
        return dbc.Alert("No recent setlist found for this artist.", color="warning"), None, True

    table_data = [{'Song': song,} for song in songs]
    table = [html.Label(f"{date}, {real_name} at {place} ({style})"), dbc.Table.from_dataframe(pd.DataFrame(table_data), striped=True, bordered=True, hover=True, style={"fontSize": "0.8rem"})]

    return "", table, False

@app.callback(
    Output('output-message', 'children', allow_duplicate=True),
    Input('submit-button', 'n_clicks'),
    State('artist-input', 'value'),
    prevent_initial_call=True
)
def create_playlist(n_clicks, artist_name):
    if not artist_name:
        return dbc.Alert("Please enter an artist name.", color="warning")

    credentials_dict = session.get('credentials')
    if not credentials_dict:
        return dbc.Alert(
            [
                "Authentication required. ",
                html.A(dbc.Button("Connect YouTube Account", color="danger"), href="/auth", className="ml-2")
            ],
            color="danger"
        )

    credentials = Credentials(
        token=credentials_dict['token'],
        refresh_token=credentials_dict.get('refresh_token'),
        token_uri=credentials_dict['token_uri'],
        client_id=credentials_dict['client_id'],
        client_secret=credentials_dict['client_secret'],
        scopes=credentials_dict['scopes']
    )

    try:
        songs, date, real_name, style, place = get_latest_setlist(artist_name)
        if not songs:
            return dbc.Alert("No recent setlist found for this artist.", color="warning")
    except Exception as e:
        error_msg = f'Error while getting setlist: {e}'
        print(error_msg, flush=True)
        return dbc.Alert(error_msg, color='danger')

    try:
        playlist_url = create_youtube_playlist(artist_name, songs, date, credentials)
        if playlist_url:
            return dbc.Alert(html.A('Playlist created! Open in YouTube', href=playlist_url, target='_blank'), color="success")
        return dbc.Alert("Failed to create playlist", color="danger")
    except Exception as e:
        error_msg = f"Failed to create playlist: {e}"
        print(error_msg, flush=True)
        return dbc.Alert(error_msg, color='danger')

if __name__ == '__main__':
    app.run(port=8050, debug=True, threaded=True)