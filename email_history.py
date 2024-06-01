import pandas as pd
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objs as go
import mailbox
from email.utils import parsedate_to_datetime
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
from concurrent.futures import ThreadPoolExecutor, as_completed
import plotly.graph_objs as go

df = pd.read_csv('email.csv')
df['date'] = pd.to_datetime(df['date'], utc=True)
df['year'] = df['date'].dt.year
df['month'] = df['date'].dt.month

monthly_counts = df.groupby(['year', 'month']).size().unstack(level=0)
email_counts_per_year = df['year'].value_counts().sort_index()

traces = []
for year in monthly_counts.columns:
    traces.append(go.Scatter(
        x=monthly_counts.index,
        y=monthly_counts[year],
        mode='lines+markers',
        name=str(year)
    ))


email_layout = html.Div([
    html.H1("Email History Heatmap"),
    html.Div([
        html.Label('Select Year and Week:'),
        dcc.Dropdown(
            id='week-year-dropdown',
            options=[{'label': str(year), 'value': year} for year in sorted(df['year'].unique())],
            value=df['year'].max(),
            clearable=False
        ),
        dcc.Dropdown(
            id='week-dropdown',
            options=[{'label': str(week), 'value': week} for week in sorted(df['week'].unique())],
            value=df['week'].max(),
            clearable=False
        ),
    ]),
    dcc.Graph(id='weekly-graph1'),
    dcc.Graph(id='heatmap1'),
    dcc.Graph(id='heatmap2'),
    dcc.Graph(id='heatmap3'),
    dcc.Graph(
        id='bar-chart',
        figure={
            'data': [
                go.Bar(
                    x=email_counts_per_year.index,
                    y=email_counts_per_year.values,
                    marker=dict(color='skyblue')
                )
            ],
            'layout': go.Layout(
                title='Number of Emails Received Per Year',
                xaxis={'title': 'Year', 'tickangle': 45},
                yaxis={'title': 'Number of Emails'},
                plot_bgcolor='white',
                paper_bgcolor='white',
                yaxis_showgrid=True,
                yaxis_gridcolor='lightgrey'
            )
        }
    ),
    dcc.Graph(
        id='line-chart',
        figure={
            'data': traces,
            'layout': go.Layout(
                title='Number of Emails Received Per Month for Each Year',
                xaxis={'title': 'Month', 'tickmode': 'array', 'tickvals': list(range(1, 13)), 'ticktext': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']},
                yaxis={'title': 'Number of Emails'},
                plot_bgcolor='white',
                paper_bgcolor='white',
                hovermode='closest'
            )
        }
    )
])

def email_callbacks(app):

    @app.callback(
        Output('weekly-graph1', 'figure'),
        Input('week-year-dropdown', 'value'),
        Input('week-dropdown', 'value')
    )
    def update_heatmap(selected_year, selected_week):
        filtered_df = df.loc[(df['year'] == selected_year) & (df['week'] == selected_week)].copy()
        filtered_df['day_of_week'] = filtered_df['date'].dt.day_name() + ' (' + filtered_df['date'].dt.month.astype(str) + '/' + filtered_df['date'].dt.day.astype(str) + ')'
        
        heatmap_data = filtered_df.groupby(['day_of_week', 'hour']).size().reset_index(name='count')
        days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        # Create a mapping of day names to the specific format with dates
        day_mapping = {}
        for day in days_order:
            day_data = filtered_df[filtered_df['date'].dt.day_name() == day]
            if not day_data.empty:
                day_mapping[day] = day + ' (' + day_data['date'].dt.month.iloc[0].astype(str) + '/' + day_data['date'].dt.day.iloc[0].astype(str) + ')'

        # Ensure all days of the week are represented in the columns
        all_days = [day_mapping.get(day, day) for day in days_order]

        heatmap_data_pivot = heatmap_data.pivot(index='hour', columns='day_of_week', values='count').fillna(0)
        heatmap_data_pivot = heatmap_data_pivot.reindex(index=range(24), columns=all_days, fill_value=0)

        fig = px.imshow(heatmap_data_pivot, labels=dict(x="Day of Week", y="Hour of Day", color="Number of Emails"), aspect="auto")
        return fig



    def generate_heatmap(df, selected_year, selected_week, email_count):
        df['year'] = df['date'].dt.year
        df['week'] = df['date'].dt.isocalendar().week
        df['day'] = df['date'].dt.day
        df['month'] = df['date'].dt.month
        df['day_of_week'] = df['date'].dt.day_name()
        df['hour'] = df['date'].dt.hour

        # Számítsd ki a legsűrűbb heteket
        weekly_counts = df.groupby(['year', 'week']).size().reset_index(name='email_count')
        top_weeks = weekly_counts.nlargest(3, 'email_count')[['year', 'week', 'email_count']]
        filtered_df = df.loc[(df['year'] == selected_year) & (df['week'] == selected_week)].copy()
        
        # Számold meg az emailek számát minden napra
        day_counts = filtered_df['day_of_week'].value_counts().to_dict()
        
        # Frissítsd a day_of_week oszlopot az email számokkal
        filtered_df['day_of_week'] = filtered_df.apply(
            lambda row: f"{row['day_of_week']} ({row['month']}/{row['day']}, {day_counts[row['day_of_week']]} emails)", axis=1
        )
        
        heatmap_data = filtered_df.groupby(['day_of_week', 'hour']).size().reset_index(name='count')
        days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        # Create a mapping of day names to the specific format with dates and email counts
        day_mapping = {}
        for day in days_order:
            day_data = filtered_df[filtered_df['date'].dt.day_name() == day]
            if not day_data.empty:
                day_counts_for_day = day_data.groupby(['day_of_week']).size().to_dict()
                day_of_week_str = day_data['day_of_week'].iloc[0]
                day_mapping[day] = f"{day} ({day_data['month'].iloc[0]}/{day_data['day'].iloc[0]}, {day_counts_for_day[day_of_week_str]} emails)"
        
        # Ensure all days of the week are represented in the columns
        all_days = [day_mapping.get(day, day) for day in days_order]

        heatmap_data_pivot = heatmap_data.pivot(index='hour', columns='day_of_week', values='count').fillna(0)
        heatmap_data_pivot = heatmap_data_pivot.reindex(index=range(24), columns=all_days, fill_value=0)

        fig = px.imshow(heatmap_data_pivot, labels=dict(x="Day of Week", y="Hour of Day", color="Number of Emails"), aspect="auto")
        fig.update_layout(title=f"Week {selected_week}, {selected_year} ({email_count} emails)")
        return fig

    @app.callback(
        [Output('heatmap1', 'figure'),
        Output('heatmap2', 'figure'),
        Output('heatmap3', 'figure')],
        [Input('heatmap1', 'id')]  # Just to trigger the callback, we don't actually use the input
    )
    def update_heatmaps(_):
        df['year'] = df['date'].dt.year
        df['week'] = df['date'].dt.isocalendar().week
        weekly_counts = df.groupby(['year', 'week']).size().reset_index(name='email_count')
        top_weeks = weekly_counts.nlargest(3, 'email_count')[['year', 'week', 'email_count']]
        figures = []
        for _, row in top_weeks.iterrows():
            figures.append(generate_heatmap(df, row['year'], row['week'], row['email_count']))
        return figures