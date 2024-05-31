import os
import webbrowser
from subprocess import run

# Path to the directory containing the location_history.py script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Path to the geo_heatmap.py script
GEO_HEATMAP_SCRIPT_PATH = os.path.join(SCRIPT_DIR, "geo-heatmap-master", "geo_heatmap.py")

# Path to the heatmap.html file
HEATMAP_HTML_PATH = os.path.join(SCRIPT_DIR, "geo-heatmap-master", "heatmap.html")

def open_heatmap():
    """Open the heatmap.html file in the web browser."""
    if os.path.exists(HEATMAP_HTML_PATH):
        try:
            webbrowser.open("file://" + os.path.realpath(HEATMAP_HTML_PATH))
            return True
        except webbrowser.Error:
            print("No runnable browser found. Open heatmap.html manually.")
    return False

def run_geo_heatmap():
    """Run the geo_heatmap.py script to generate the heatmap.html file."""
    try:
        # Change directory to geo-heatmap-master
        os.chdir(os.path.join(SCRIPT_DIR, "geo-heatmap-master"))
        
        # Install requirements
        run(["pip", "install", "-r", "requirements.txt"])

        # Run geo_heatmap.py with Records.json as argument
        run(["python", "geo_heatmap.py", "Records.json"])
    except FileNotFoundError:
        print("Geo heatmap script not found at specified path.")