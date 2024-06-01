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
df['Week'] = df['Date'].dt.isocalendar().week  # Extract week

# Aggregate data by year, month, day, hour, and week
agg_df_week = df.groupby(['Year', 'Week']).size().reset_index(name='Count')
video_counts_per_year = df['Year'].value_counts().sort_index()

youtube_layout = html.Div([
    html.H1("YouTube Viewing History Heatmap"),
    html.Div([
        html.Label('Select Year and Month:'),
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
    ]),
    dcc.Graph(id='heatmap'),
    html.Div([
        html.Label('Select Year and Week:'),
        dcc.Dropdown(
            id='week-year-dropdown',
            options=[{'label': str(year), 'value': year} for year in sorted(df['Year'].unique())],
            value=df['Year'].max(),
            clearable=False
        ),
        dcc.Dropdown(
            id='week-dropdown',
            options=[{'label': str(week), 'value': week} for week in sorted(df['Week'].unique())],
            value=df['Week'].max(),
            clearable=False
        ),
    ]),
    dcc.Graph(id='weekly-graph'),
    html.Button('Update Heatmaps', id='update-button'),
    dcc.Graph(id='heatmap-1'),
    dcc.Graph(id='heatmap-2'),
    dcc.Graph(id='heatmap-3'),
    dcc.Graph(
        id='bar-chart',
        figure={
            'data': [
                {
                    'x': video_counts_per_year.index,
                    'y': video_counts_per_year.values,
                    'type': 'bar',
                    'name': 'Videos Watched',
                    'marker': {'color': 'skyblue'}
                }
            ],
            'layout': {
                'title': 'Number of YouTube Videos Watched Per Year',
                'xaxis': {'title': 'Year', 'tickangle': 45},
                'yaxis': {'title': 'Number of Videos Watched'},
                'plot_bgcolor': 'white',
                'paper_bgcolor': 'white',
                'grid': {'y': {'gridcolor': 'lightgrey'}}
            }
        }
    )
])

def youtube_callbacks(app):
    @app.callback(
        Output('heatmap', 'figure'),
        [Input('year-dropdown', 'value'),
         Input('month-dropdown', 'value')]
    )
    def update_heatmap(selected_year, selected_month):
        # Extract year and month for filtering
        df['Year'] = df['Date'].dt.year
        df['Month'] = df['Date'].dt.month
        df['Day'] = df['Date'].dt.day
        df['Hour'] = df['Date'].dt.hour

        # Aggregate data by year, month, day, and hour
        agg_df = df.groupby(['Year', 'Month', 'Day', 'Hour']).size().reset_index(name='Count')
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
    
    @app.callback(
        Output('weekly-graph', 'figure'),
        [Input('week-year-dropdown', 'value'),
         Input('week-dropdown', 'value')]
    )
    def update_weekly_graph(selected_year, selected_week):
        df['Year'] = df['Date'].dt.year
        df['Week'] = df['Date'].dt.isocalendar().week
        df['DayOfWeek'] = df['Date'].dt.dayofweek
        df['Hour'] = df['Date'].dt.hour
        df['DayOfMonth'] = df['Date'].dt.day
        df['Month'] = df['Date'].dt.month
        agg_df = df.groupby(['Year', 'Week', 'DayOfWeek', 'Hour']).size().reset_index(name='Count')
        day_summary_df = df.groupby(['Year', 'Week', 'DayOfWeek', 'Month', 'DayOfMonth']).size().reset_index(name='DayCount')
        agg_df = agg_df.merge(day_summary_df, on=['Year', 'Week', 'DayOfWeek'], how='left')
        filtered_df = agg_df[(agg_df['Year'] == selected_year) & (agg_df['Week'] == selected_week)]
        
        heatmap_data = filtered_df.pivot(index='Hour', columns='DayOfWeek', values='Count').fillna(0)
        day_summary = filtered_df[['DayOfWeek', 'Month', 'DayOfMonth', 'DayCount']].drop_duplicates().sort_values('DayOfWeek')
        day_labels = [
            f"{['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][row.DayOfWeek]} ({row.Month}/{row.DayOfMonth}) - {row.DayCount} videos"
            for _, row in day_summary.iterrows()
        ]
        heatmap_data.columns = day_labels
        
        fig = px.imshow(
            heatmap_data,
            labels=dict(x="Day of Week", y="Hour of Day", color="Video Count"),
            x=heatmap_data.columns,
            y=heatmap_data.index,
            color_continuous_scale='Viridis'
        )
        fig.update_layout(title=f'Videos Watched in Week {selected_week}, {selected_year}', xaxis_nticks=7)

        return fig
    

    def generate_heatmap(selected_year, selected_week, total_videos):
        # Extract year, week, day, hour, and day of month for filtering
        df['Year'] = df['Date'].dt.year
        df['Week'] = df['Date'].dt.isocalendar().week
        df['DayOfWeek'] = df['Date'].dt.dayofweek
        df['Hour'] = df['Date'].dt.hour
        df['DayOfMonth'] = df['Date'].dt.day
        df['Month'] = df['Date'].dt.month

        # Aggregate data by year, week, day, and hour
        agg_df = df.groupby(['Year', 'Week', 'DayOfWeek', 'Hour']).size().reset_index(name='Count')
        day_summary_df = df.groupby(['Year', 'Week', 'DayOfWeek', 'Month', 'DayOfMonth']).size().reset_index(name='DayCount')

        # Merge the summary to get the DayCount for each day
        agg_df = agg_df.merge(day_summary_df, on=['Year', 'Week', 'DayOfWeek'], how='left')

        filtered_df = agg_df[(agg_df['Year'] == selected_year) & (agg_df['Week'] == selected_week)]
        
        heatmap_data = filtered_df.pivot(index='Hour', columns='DayOfWeek', values='Count').fillna(0)
        day_summary = filtered_df[['DayOfWeek', 'Month', 'DayOfMonth', 'DayCount']].drop_duplicates().sort_values('DayOfWeek')
        day_labels = [
            f"{['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][row.DayOfWeek]} ({row.Month}/{row.DayOfMonth}) - {row.DayCount} videos"
            for _, row in day_summary.iterrows()
        ]
        heatmap_data.columns = day_labels
        
        fig = px.imshow(
            heatmap_data,
            labels=dict(x="Day of Week", y="Hour of Day", color="Video Count"),
            x=heatmap_data.columns,
            y=heatmap_data.index,
            color_continuous_scale='Viridis'
        )
        fig.update_layout(title=f'Videos Watched in Week {selected_week}, {selected_year} ({total_videos} videos)', xaxis_nticks=7)

        return fig

    @app.callback(
        [Output('heatmap-1', 'figure'),
        Output('heatmap-2', 'figure'),
        Output('heatmap-3', 'figure')],
        [Input('update-button', 'n_clicks')]
    )
    def update_heatmaps(n_clicks):
        df['Year'] = df['Date'].dt.year
        df['Week'] = df['Date'].dt.isocalendar().week
        weekly_summary = df.groupby(['Year', 'Week']).size().reset_index(name='TotalCount')
        top_weeks = weekly_summary.nlargest(3, 'TotalCount')
        figures = []
        for _, row in top_weeks.iterrows():
            year, week, total_videos = row['Year'], row['Week'], row['TotalCount']
            fig = generate_heatmap(year, week, total_videos)
            figures.append(fig)
        return figures