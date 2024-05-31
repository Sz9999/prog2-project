import dash
from dash import dcc, html
from dash.dependencies import Input, Output
from layout import layout
from youtube_history import youtube_layout, youtube_callbacks
from location_history import open_heatmap, run_geo_heatmap

app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.title = "History Dashboard"

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/youtube-history':
        return youtube_layout
    elif pathname == '/location-history':
        # Check if heatmap.html exists
        if open_heatmap():
            return "Location History Selected"
        else:
            run_geo_heatmap()
            return "Generating Location History..."
    else:
        return layout
    
youtube_callbacks(app)

if __name__ == '__main__':
    app.run_server(debug=True)
