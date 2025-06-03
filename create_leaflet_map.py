import psycopg2
import subprocess
import sys
from config import DB_PARAMS
from config_dev import DB_PARAMS_DEV
from datetime import datetime
import json

timestamp = datetime.now().strftime("%d%m%Y")

# Verbindung zur Datenbank
try:
    conn = psycopg2.connect(**DB_PARAMS)
    print("Verbindung erfolgreich!")
except Exception as e:
    print("Verbindung fehlgeschlagen:", e)

# Verbindung zur Datenbank
try:
    conn_dev = psycopg2.connect(**DB_PARAMS_DEV)
    print("Verbindung erfolgreich!")
except Exception as e:
    print("Verbindung fehlgeschlagen:", e)

# Funktion, um geojson aus der Datenbank holen je nach Subprojekt ID
def fetch_geojson_db(subprojekt_id):
    query = """
    SELECT json_build_object(
    'type', 'FeatureCollection',
     'features', json_agg(
       json_build_object(
         'type', 'Feature',
        'geometry', geo,
        'properties',  json_build_object('dgn_phase', dgn_phase) 
      )
     )
    ) AS geojson
    FROM (
      SELECT ST_AsGeoJSON(ST_Transform(geom, 4326))::json AS geo, dgn_phase
      FROM gis_planung.dgn_phase
      WHERE dgn_phase.teilprojekt_id = %s
      AND dgn_phase IN ('1', '2')
    ) t;"""

    with conn.cursor() as cursor:
        cursor.execute(query, (subprojekt_id,))
        result = cursor.fetchone()
    if result:
        geojson_data = result[0]
    else:
        geojson_data = {}
    # print(geojson_data)
    return geojson_data
    conn.close()


# Funktion, um die Tabelle create_map zu updaten (false->true & +geojson)
def update_table(geojson, sp_id):
    query = """
    UPDATE dgn_cso_ame.t_dgn_create_map
    SET geojson = %s,
        created = TRUE
    WHERE subprojekt_id = %s
    """
    with conn_dev.cursor() as cursor:
        cursor.execute(query, (geojson, sp_id))
        # print("Tabelle geupdatet")
        conn_dev.commit()
    conn_dev.close()


# Funktion, um Datei zu erstellen
def create_or_update_file(file_path, content):
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    # print(f"✅ Datei '{file_path}' wurde erstellt/überschrieben.")


# Funktion, um Datei auf github zu pushen
def git_add_commit_push(commit_message):
    try:
        # Dateien zum Staging hinzufügen
        subprocess.run(["git", "add", file_path], check=True)
        # print("✅ Dateien zum Staging hinzugefügt.")

        # Commit erstellen
        subprocess.run(["git", "commit", "--allow-empty", "-m", commit_message], check=True)
        # print("✅ Commit erstellt.")

        # Push zu GitHub
        subprocess.run(["git", "push", "--set-upstream", "origin", "main"], check=True)
        # print("✅ Änderungen erfolgreich zu GitHub gepusht!")

    except subprocess.CalledProcessError as e:
        print("❌ Fehler bei einem Git-Befehl:", e)


# Abfrage Subprojekt-ID
subprojekt_input = input("Bitte gib die Subprojekt-ID ein: ")
try:
    subprojekt_id = int(subprojekt_input)
except ValueError:
    print("Ungültige Eingabe! Bitte eine Zahl eingeben.")
    sys.exit(1)

# Funktion fetch geojson ausführen
fetch_geojson_db(subprojekt_id)
with conn.cursor() as cursor:
    geojson_data = fetch_geojson_db(subprojekt_id)
    geojson_str = json.dumps(geojson_data)
    geojson_str_single = geojson_str.replace('"', "'")
    # print(geojson_str)

# Funktion update table ausführen
update_table(geojson_str_single, subprojekt_id)
conn.close()

# Zoom der Karte auf Mittelpunkt der Polygone einstellen
lats = []
lngs = []
for feature in geojson_data['features']:
    geometry = feature['geometry']
    if geometry['type'] == 'MultiPolygon':
        for polygon in geometry['coordinates']:
            for ring in polygon:
                for coord in ring:
                    lon, lat = coord
                    lats.append(lat)
                    lngs.append(lon)
    elif geometry['type'] == 'Polygon':
        for ring in geometry['coordinates']:
            for coord in ring:
                lon, lat = coord
                lats.append(lat)
                lngs.append(lon)
    elif geometry['type'] == 'Point':
        lon, lat = geometry['coordinates']
        lats.append(lat)
        lngs.append(lon)
center_lat = sum(lats) / len(lats)
center_lon = sum(lngs) / len(lngs)
# print(f"Center: {center_lat}, {center_lon}")

# html-Datei
if __name__ == "__main__":
    file_path = f"{subprojekt_id}_{timestamp}.html"
    content = f"""
        <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Karte {subprojekt_id} </title>
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <script src="https://unpkg.com/leaflet-control-geocoder/dist/Control.Geocoder.js"></script>
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css" rel="stylesheet">
        <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600&display=swap" rel="stylesheet">
        <style>
            html, body {{
                height: 100%;
                margin: 0;
            }}
            .leaflet-container {{
                height: 100%;
                width: 100%;
                max-width: 100%;
                max-height: 100%;
            }}
            .leaflet-control-zoom {{
                background: none !important;
                box-shadow: none !important;
                border: none !important;
            }}

            /*+ und - button formatierung*/
            .leaflet-control-zoom-in, .leaflet-control-zoom-out {{
                background-color: white !important; /*hintergrundfarbe*/
                color: grey !important; /*button farbe*/
                border: none !important; /*keine umrandung*/
                width: 30px;
                height: 30px;
                display: flex;
                justify-content: center;
                align-items: center;
                font-size: 15px; /*symbolgröße*/
                font-weight: 20;
                font-family: 'Montserrat', sans-serif; /*dgn font*/
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3); /*schatten*/
            }}

            .leaflet-control-zoom-in:hover, .leaflet-control-zoom-out:hover {{
                background-color: #f0f0f0 !important; /* hover maus effekt */
            }}
            /*zurück zu ausgangskarte zoomen button formatieren*/
            .custom-control {{
                position: absolute;
                bottom: -40px;
                left:0px;
                background: white;
                padding: 5px;
                border-radius: 2px;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
                cursor: pointer;
                display: flex;
                justify-content: center;
                align-items: center;
                width: 20px;
                height: 20px;
                color: grey
            }}

            /*legenden button formatieren*/
            .custom-control2 {{
                position: absolute;
                bottom: -320px;
                left: 0px;
                background: white;
                padding: 5px;
                border-radius:2px;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
                cursor: pointer;
                display: flex;
                justify-content: center;
                align-items: center;
                width: 20px;
                height: 20px;
                color: grey
            }}
            .custom-control:hover, .custom-control2:hover {{
                background-color: #f0f0f0 !important;
            }}
                /* formatieren suchen button */
            .leaflet-control-geocoder-icon {{
                background-color: white !important;
                color: grey !important;
                border: none !important;
                width: 20px;
                height: 20px;
                display: flex;
                justify-content: center;
                align-items: center;
                font-size: 15px;
                font-family: 'Montserrat', sans-serif;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
                border-radius: 2px;
                cursor: pointer;
            }}
            .leaflet-control-geocoder-icon:hover {{
                background-color: #f0f0f0 !important;
            }}

            /*formatieren grauer marker*/
            .custom-marker {{
                width: 15px;
                height: 15px;
                background-color: grey;
                border-radius: 50%;
                border: 1px solid white;
            }}
            /*legende formatieren*/
            #legend {{
                position: absolute;
                bottom: 80px;
                left: 55px;
                display: none;
                z-index: 1000;
                background: white;
                padding: 10px;
                border-radius: 5px;
                box-shadow: 0px 2px 5px rgba(0, 0, 0, 0.2);
                font-family: 'Montserrat', sans-serif;
            }}

            #legend div {{
                font-size: 12px;
                line-height: 18px;
            }}
        </style>
          <link rel="stylesheet" href="https://unpkg.com/leaflet-control-geocoder/dist/Control.Geocoder.css" />
    </head>
    <body>
    <div id="map"></div>
    <div id="legend">
        <div><span style="display:inline-block; width:20px; height:10px; background:#E8B899; margin-right:5px;"></span>Ausbauphase 1: Ausbau bei ausreichender Nachfrage</div>
        <div><span style="display:inline-block;width:20px; height:10px; background:#BCBCBB; margin-right:5px;"></span>Ausbauphase 2: Interessenbekundung möglich</div>
    </div>
    <script>
        const initialCoordinates = [{center_lat}, {center_lon}];
        const initialZoomLevel = 13;

        const map = L.map('map',{{
        zoomControl: false //default zoom - + rausnehmen
    }}).setView(initialCoordinates, initialZoomLevel);


        const CartoDB_Positron = L.tileLayer('https://{{s}}.basemaps.cartocdn.com/light_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
            subdomains: 'abcd',
            maxZoom: 30
        }}).addTo(map);

        L.control.zoom({{
            position: 'topleft'
        }}).addTo(map);

      const geoJsonData = {geojson_data};

        const geoLayer = L.geoJSON(geoJsonData, {{
            style: feature => {{
                if (feature.properties.dgn_phase === 2) {{
                    return {{ stroke: false, fillColor: 'grey', fillOpacity: 0.5 }};
                }} else {{
                    return {{ stroke: false, fillColor: '#ED782B', fillOpacity: 0.4 }};
                }}
            }}
        }});

        geoLayer.addTo(map);
       // map.fitBounds(geoLayer.getBounds());

        //button der auf ausgangskarte zurück zoomt auf karte bringen
        const zoomFullExtentControl = L.Control.extend({{
            options: {{ position: 'topleft' }},
            onAdd: function () {{
                const container = L.DomUtil.create('div', 'custom-control');
                container.innerHTML = '<i class="fas fa-home"></i>';
                L.DomEvent.on(container, 'click', () => map.setView(initialCoordinates, initialZoomLevel));
                return container;
            }}
        }});
        map.addControl(new zoomFullExtentControl());

        //legende button auf karte bringen
        const legendControl = L.Control.extend({{
            options: {{ position: 'topleft' }},
            onAdd: function () {{
                const container = L.DomUtil.create('div', 'custom-control2');
                container.innerHTML = '<i class="fas fa-list"></i>';
                L.DomEvent.on(container, 'click', () => {{
                    const legend = document.getElementById('legend');
                    legend.style.display = legend.style.display === 'none' ? 'block' : 'none';
                }});
                return container;
            }}
        }});
        map.addControl(new legendControl());

        const markerLayerGroup = L.layerGroup().addTo(map);

        //grauer kreis als marker
        const geocoder = L.Control.geocoder({{
            defaultMarkGeocode: false //default rausnehmen
        }})
            .on('markgeocode', function (e) {{
                //existierende marker löschen
                markerLayerGroup.clearLayers();

                const latlng = e.geocode.center;

                //grauer kreis als custom marker
                const customMarker = L.divIcon({{
                    className: 'custom-marker'
                }});

                const marker = L.marker(latlng, {{ icon: customMarker }});
                markerLayerGroup.addLayer(marker);

                //zoom auf ausgewählte adresse
                map.setView(latlng, 14);
            }})
            .addTo(map);

    </script>
    </body>
    </html>
        """

    # Datei kreieren
    create_or_update_file(file_path, content)
    # Datei auf Github pushen
    commit_message = f"Automatischer Commit: Karte für {subprojekt_id} erstellt"
    git_add_commit_push(commit_message)

# iframe Snippet für Einbindung
print(f"""

iframe für Subprojekt {subprojekt_id}:
    '
    <iframe src="https://dgnsalesservice.github.io/git_connect_test/{file_path}"
    style="width: 100%; height: 100%; border: none; position: absolute; top: 0; left: 0"></iframe> 
    '

""")

