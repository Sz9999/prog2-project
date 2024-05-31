import os
import pandas as pd
from dash import dcc, html
from dash.dependencies import Input, Output
from location_history import open_heatmap, run_geo_heatmap
from layout import layout
from bs4 import BeautifulSoup
import re

import dash  # This import was missing

app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.title = "History Dashboard"

# Check if history.xlsx exists, if not, create it
if not os.path.exists('history.xlsx'):
    # to format get the information from the html
    with open('watch_history.html', 'r', encoding='utf-8') as file:
        content = file.read()

    soup = BeautifulSoup(content, 'html.parser')
    data = []

    # Minden YouTube megtekintéshez tartozó elem megtalálása
    for item in soup.find_all('div', class_='outer-cell mdl-cell mdl-cell--12-col mdl-shadow--2dp'):
        title_element = item.find('a', href=True)
        title = title_element.text if title_element else None
        
        date_element = item.find('div', class_='content-cell mdl-cell mdl-cell--6-col mdl-typography--body-1')
        date = date_element.text if date_element else None
        
        data.append({
            'Title': title,
            'Date': date
        })
    
    # Adatok DataFrame-be rendezése
    df = pd.DataFrame(data)

    # Hónapok magyar neveinek és számuknak megfeleltetése
    month_map = {
        'jan': '01',
        'febr': '02',
        'márc': '03',
        'ápr': '04',
        'máj': '05',
        'jún': '06',
        'júl': '07',
        'aug': '08',
        'szept': '09',
        'okt': '10',
        'nov': '11',
        'dec': '12'
    }

    # Függvény a hónapok átalakítására
    def convert_month(text):
        for month_name, month_num in month_map.items():
            text = re.sub(month_name, month_num, text)
        return text

    # Dátumok átalakítása
    df['Date'] = df['Date'].apply(convert_month)

    # Mintázat, hogy csak a dátumot tartsuk meg a szövegből
    date_pattern = re.compile(r'\d{4}\. \d{2}\. \d{1,2}\. \d{1,2}:\d{2}:\d{2} CEST')

    def extract_date(text):
        match = date_pattern.search(text)
        if match:
            return match.group(0)
        return None

    df['Date'] = df['Date'].apply(extract_date)

    # Átalakítás datetime formátumba
    df['Date'] = pd.to_datetime(df['Date'], format='%Y. %m. %d. %H:%M:%S CEST', errors='coerce')
    
    # Save the dataframe as an Excel file
    df.to_excel('history.xlsx', index=False)

from youtube_history import youtube_layout, youtube_callbacks

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
        # Check if heatmap.html exists and handle appropriately
        if open_heatmap():
            return html.Div("Opening heatmap...", id="heatmap-loading")
        else:
            return html.Div("Generating heatmap...", id="heatmap-loading")
    else:
        return layout

# Register YouTube callbacks
youtube_callbacks(app)

if __name__ == '__main__':
    app.run_server(debug=True)
