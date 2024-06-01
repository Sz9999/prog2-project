from subprocess import run
run(["pip", "install", "-r", "requirements.txt"])

import os
import sys
import zipfile
import shutil
from dash import dcc, html, Input, Output, State
from dash.exceptions import PreventUpdate
from dash import Dash
from location_history import open_heatmap, run_geo_heatmap
from layout import layout
from bs4 import BeautifulSoup
import re
import pandas as pd

app = Dash(__name__, suppress_callback_exceptions=True)
app.title = "History Dashboard"

def process_takeout(takeout_path):
    extracted_folder = "takeout_extracted"
    
    if not os.path.exists(takeout_path):
        return "Invalid path provided."

    if not os.path.exists(extracted_folder):
        with zipfile.ZipFile(takeout_path, 'r') as zip_ref:
            zip_ref.extractall(extracted_folder)

    takeout_dir = os.path.join(extracted_folder, "Takeout")

    # Process Location History
    location_history_src = os.path.join(takeout_dir, "Helyelőzmények (idővonal)", "Records.json")
    location_history_dst = os.path.join("geo-heatmap-master", "Records.json")
    if os.path.exists(location_history_src) and not os.path.exists(location_history_dst):
        print(f"Copying {location_history_src} to {location_history_dst}")
        shutil.copy(location_history_src, location_history_dst)
    else:
        #print(f"File {location_history_src} does not exist or {location_history_dst} already exists.")
        pass

    # Process YouTube History
    youtube_history_src = os.path.join(takeout_dir, "YouTube és YouTube Music", "előzmények", "megtekintési előzmények.html")
    youtube_history_dst = "watch_history.html"
    if os.path.exists(youtube_history_src) and not os.path.exists(youtube_history_dst):
        print(f"Copying {youtube_history_src} to {youtube_history_dst}")
        shutil.copy(youtube_history_src, youtube_history_dst)
    else:
        #print(f"File {youtube_history_src} does not exist or {youtube_history_dst} already exists.")
        pass
    return "Takeout processed successfully."

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content'),
])

@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname')]
)

def display_page(pathname):
    heatmap_path = os.path.join("geo-heatmap-master", "heatmap.html")
    if pathname == '/youtube-history':
        return youtube_layout
    elif pathname == '/location-history':
        # Check if heatmap.html exists and handle appropriately
        if os.path.exists(heatmap_path):
            open_heatmap()
            return layout
        else:
            return html.Div("Heatmap does not exist.")
    else:
        return layout

# Capture the takeout path from command-line arguments
if len(sys.argv) != 2:
    print("Usage: python app.py <path_to_takeout_zip>")
    sys.exit(1)

takeout_path = sys.argv[1]

# Process takeout with the provided path
process_takeout(takeout_path)

heatmap_path = os.path.join("geo-heatmap-master", "heatmap.html")
if not os.path.exists(heatmap_path):
    run_geo_heatmap()
    os.chdir(os.path.join(os.getcwd(), '..'))

# Check if history.xlsx exists, if not, create it
history_path = os.path.join("history.xlsx")
if not os.path.exists(history_path) and os.path.exists('watch_history.html'):
    # Process watch_history.html
    # to format get the information from the html
    with open('watch_history.html', 'r', encoding='utf-8') as file:
        content = file.read()
    print("1")

    soup = BeautifulSoup(content, 'lxml')
    data = []
    print("2")

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
    print("3")

    # Adatok DataFrame-be rendezése
    df = pd.DataFrame(data)
    print("4")

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
    print("5")

    # Függvény a hónapok átalakítására
    def convert_month(text):
        for month_name, month_num in month_map.items():
            text = re.sub(month_name, month_num, text)
        return text
    print("6")

    # Dátumok átalakítása
    df['Date'] = df['Date'].apply(convert_month)
    print("7")

    # Mintázat, hogy csak a dátumot tartsuk meg a szövegből
    date_pattern = re.compile(r'\d{4}\. \d{2}\. \d{1,2}\. \d{1,2}:\d{2}:\d{2} CEST')

    def extract_date(text):
        match = date_pattern.search(text)
        if match:
            return match.group(0)
        return None

    df['Date'] = df['Date'].apply(extract_date)
    print("8")

    # Átalakítás datetime formátumba
    df['Date'] = pd.to_datetime(df['Date'], format='%Y. %m. %d. %H:%M:%S CEST', errors='coerce')
    print("9")

    # Save the dataframe as an Excel file
    df.to_excel('history.xlsx', index=False)
    print("10")

from youtube_history import youtube_callbacks
from youtube_history import youtube_layout

# Register YouTube callbacks
youtube_callbacks(app)

if __name__ == '__main__':
    app.run_server(debug=True)
