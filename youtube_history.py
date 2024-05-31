import pandas as pd
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px

# Load your data
df = pd.read_excel('history.xlsx')

# Convert the 'Date' column to datetime
df['Date'] = pd.to_datetime(df['Date'])

# Extract year, month, day, and hour for filtering
df['Year'] = df['Date'].dt.year
df['Month'] = df['Date'].dt.month
df['Day'] = df['Date'].dt.day
df['Hour'] = df['Date'].dt.hour

# Aggregate data by year, month, day, and hour
agg_df = df.groupby(['Year', 'Month', 'Day', 'Hour']).size().reset_index(name='Count')

youtube_layout = html.Div([
    html.H1("YouTube Viewing History Heatmap"),
    dcc.Dropdown(
        id='year-dropdown',
        options=[{'label': str(year), 'value': year} for year in sorted(df['Year'].unique())],
        value=df['Year'].max(),
        clearable=False
    ),
    dcc.Dropdown(
        id='month-dropdown',
        options=[{'label': str(month), 'value': month} for month in range(1, 13)],
        value=df['Month'].max(),
        clearable=False
    ),
    dcc.Graph(id='heatmap')
])

def youtube_callbacks(app):
    @app.callback(
        Output('heatmap', 'figure'),
        [Input('year-dropdown', 'value'),
         Input('month-dropdown', 'value')]
    )
    def update_heatmap(selected_year, selected_month):
        filtered_df = agg_df[(agg_df['Year'] == selected_year) & (agg_df['Month'] == selected_month)]
        
        heatmap_data = filtered_df.pivot(index='Hour', columns='Day', values='Count').fillna(0)

        fig = px.imshow(
            heatmap_data,
            labels=dict(x="Day of Month", y="Hour of Day", color="Video Count"),
            x=heatmap_data.columns,
            y=heatmap_data.index,
            color_continuous_scale='Viridis'
        )
        fig.update_layout(title=f'Videos Watched in {selected_month}/{selected_year}', xaxis_nticks=31)

        return fig
