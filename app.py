# app.py
import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
from setlist2spotify import *

# Initialize the app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

# App layout
app.layout = dbc.Container([
    dbc.Row(
        dbc.Col(
            html.H1("Setlist to Spotify Playlist Creator", className="text-center my-4"),
            width=12
        )
    ),
    dbc.Row(
        dbc.Col([
            dbc.InputGroup([
                dbc.Input(
                    id='artist-input',
                    placeholder="Enter artist name...",
                    type="text",
                    className="mb-3"
                ),
                dbc.Button(
                    "Create Playlist",
                    id='submit-button',
                    color="success",
                    className="mb-3"
                ),
            ], className="mb-4"),
            
            dbc.Alert(
                id='output-message',
                color="info",
                dismissable=True,
                className="mb-3",
                is_open=False
            ),
            
            dbc.Card(
                dbc.CardBody(
                    id='playlist-link',
                    className="text-center"
                ),
                className="mb-3"
            ),
            
            dcc.Store(id='song-store')
        ], width=12, md=8, className="mx-auto")
    )
], fluid=True)

@app.callback(
    [Output('output-message', 'children'),
     Output('output-message', 'color'),
     Output('output-message', 'is_open'),
     Output('song-store', 'data'),
     Output('playlist-link', 'children')],
    [Input('submit-button', 'n_clicks')],
    [State('artist-input', 'value')]
)
def create_playlist(n_clicks, artist_name):
    if n_clicks is None or not artist_name:
        return dash.no_update
    
    try:
        songs, date = get_latest_setlist(artist_name)
        if not songs:
            return (
                "No recent setlist found for this artist.",
                "warning",
                True,
                None,
                None
            )
            
        playlist_url = create_spotify_playlist(artist_name, songs, date)
        if not playlist_url:
            return (
                "Failed to create Spotify playlist.",
                "danger",
                True,
                None,
                None
            )
            
        return [
            f"Successfully created playlist with {len(songs)} songs from {date}!",
            "success",
            True,
            {'songs': songs, 'date': date},
            dbc.Button(
                "Open Playlist on Spotify",
                href=playlist_url,
                target="_blank",
                color="success",
                className="mt-2"
            )
        ]
        
    except Exception as e:
        return (
            f"Error: {str(e)}",
            "danger",
            True,
            None,
            None
        )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8050, debug=os.environ.get('DEBUG', False))