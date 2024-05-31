from dash import html

layout = html.Div([
    html.H1("Welcome to the History Dashboard", style={'textAlign': 'center'}),
    html.Div([
        html.A(
            html.Div([
                html.Img(src='/assets/youtube_logo.png', style={'height': '100px'}),
                html.P("YouTube History")
            ], style={'textAlign': 'center'}),
            href="/youtube-history",
            style={'marginRight': '20px', 'textDecoration': 'none', 'color': 'black'}
        ),
        html.A(
            html.Div([
                html.Img(src='/assets/google_maps_logo.png', style={'height': '100px'}),
                html.P("Location History")
            ], style={'textAlign': 'center'}),
            href="/location-history",
            style={'textDecoration': 'none', 'color': 'black'}
        )
    ], style={'display': 'flex', 'justifyContent': 'center'})
], style={'textAlign': 'center', 'fontFamily': 'Arial, sans-serif'})

