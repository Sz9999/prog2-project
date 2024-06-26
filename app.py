from subprocess import run
run(["pip", "install", "-r", "requirements.txt"])

import os
import sys
import zipfile
import shutil
from dash import dcc, html, Input, Output
from dash.exceptions import PreventUpdate
from dash import Dash
from location_history import open_heatmap, run_geo_heatmap
from layout import layout
from bs4 import BeautifulSoup
import re
import pandas as pd
import mailbox
from email.utils import parsedate_to_datetime
from tqdm import tqdm
import webbrowser

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

def process_mbox(mbox_path):
    email_file = "email.csv"
    
    if not os.path.exists(mbox_path):
        return "Invalid path provided."

    if not os.path.exists(email_file):
        mbox = mailbox.mbox(mbox_path)
        data = []
        for message in tqdm(mbox):
            if message['date'] and message['from'] and message['subject']:
                payload = message.get_payload(decode=True)
                body = payload.decode(errors='ignore') if payload else ''
                data.append({
                    'date': parsedate_to_datetime(message['date']),
                    'from': message['from'],
                    'subject': message['subject'],
                    'body': body
                })
        df = pd.DataFrame(data)
        df.to_csv('email.csv', index=False)

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content'),
    dcc.Store(id='dummy-output')  # Added dcc.Store to serve as a dummy output
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
            return html.Div([
                html.Button("Open Heatmap", id="open-heatmap-btn")
            ])
        else:
            return html.Div("Heatmap does not exist.")
    elif pathname == '/email-history':
        return email_layout
    else:
        return layout

@app.callback(
    Output('dummy-output', 'data'),  # Using dcc.Store to avoid unnecessary updates to the layout
    [Input('open-heatmap-btn', 'n_clicks')]
)
def open_heatmap_on_click(n_clicks):
    if n_clicks is None:
        raise PreventUpdate
    open_heatmap()
    return ""

# Capture the takeout path from command-line arguments
if len(sys.argv) != 3:
    print("Usage: python app.py <path_to_takeout_zip> <path_to_email.mbox>")
    sys.exit(1)

takeout_path = sys.argv[1]
mbox_path = sys.argv[2]
# Process takeout with the provided path
process_takeout(takeout_path)
process_mbox(mbox_path)

heatmap_path = os.path.join("geo-heatmap-master", "heatmap.html")
if not os.path.exists(heatmap_path):
    run_geo_heatmap()
    os.chdir(os.path.join(os.getcwd(), '..'))

# Check if history.xlsx exists, if not, create it
history_path = os.path.join("history.xlsx")
if not os.path.exists(history_path) and os.path.exists('watch_history.html'):
    # Process watch_history.html
    with open('watch_history.html', 'r', encoding='utf-8') as file:
        content = file.read()

    soup = BeautifulSoup(content, 'lxml')
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

from youtube_history import youtube_callbacks
from youtube_history import youtube_layout
from email_history import email_callbacks
from email_history import email_layout

# Register YouTube callbacks
youtube_callbacks(app)
email_callbacks(app)

if __name__ == '__main__':
    webbrowser.open_new("http://127.0.0.1:8050/")
    app.run_server(debug=False)
