import csv
import time
import random
import psycopg2
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

conn = psycopg2.connect(user="ame",
                              password="0bacf635fb988a55582ed01b99008109",
                              host="pgeuwgispr004.postgres.database.azure.com",
                              port="5432",
                              database="dgn_gis")

cur = conn.cursor()

# Erstelle einen Cursor
cur = conn.cursor()

# SQL-Abfrage, um Adressen aus der materialisierten Ansicht zu holen
sql_query = """
SELECT ags8, ort, stn, hnr, plz, longitude, latitude, geom
FROM dgn_cso_ame.mv_crawler_community_addresses WHERE LEFT(ags8, 2) = '05' OR LEFT(ags8, 2) = '03'
ORDER BY ags8;
"""

cur.execute(sql_query)
adressen = cur.fetchall()

# Pfad zum Webdriver (Chrome, Firefox, etc.)
# Wenn chromedriver im Systempfad ist
driver = webdriver.Chrome()

# CSV-Datei erstellen und Header schreiben
with open('C:/Users/AnnaPillinDeutscheGi/Downloads/results.csv', mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(['ags8', 'ort', 'selected_street', 'hnr', 'plz', 'longitude', 'latitude', 'result'])

    try:
        batch_size = 10  # Größe jedes Batches
        min_delay = 30  # Minimale Wartezeit in Sekunden zwischen den Batches
        max_delay = 60  # Maximale Wartezeit in Sekunden zwischen den Batches
        min_request_delay = 2  # Minimale Wartezeit in Sekunden zwischen den Anfragen
        max_request_delay = 5  # Maximale Wartezeit in Sekunden zwischen den Anfragen

        for i in range(0, len(adressen), batch_size):
            batch = adressen[i:i + batch_size]
            for adresse in batch:
                ags8, ort, stn, hnr, plz, longitude, latitude, geom = adresse

                # Öffne die Website
                driver.get('https://glasfaser-nordwest.de/')

                try:
                    # Warte, bis das PLZ-Eingabefeld sichtbar ist
                    plz_field = WebDriverWait(driver, 10).until(
                        EC.visibility_of_element_located((By.ID, 'check_city_1'))  # Hier die ID des PLZ-Eingabefelds anpassen
                    )
                    plz_field.send_keys(plz)  # PLZ aus der Datenbank

                    # Warte kurz, um die Autovervollständigung zu ermöglichen
                    time.sleep(2)

                    try:
                        # Wähle ein zufälliges Element in der PLZ Autovervollständigungsliste aus
                        plz_suggestions = WebDriverWait(driver, 10).until(
                            EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.js-select-city'))
                        )
                        random.choice(plz_suggestions).click()

                        # Warte, bis das Straßen-Eingabefeld sichtbar ist
                        street_field = WebDriverWait(driver, 10).until(
                            EC.visibility_of_element_located((By.ID, 'check_street_1'))  # Hier die ID des Straßen-Eingabefelds anpassen
                        )
                        street_field.send_keys("sch")  # Eingabe der ersten Buchstaben der Straße

                        # Warte kurz, um die Autovervollständigung zu ermöglichen
                        time.sleep(2)

                        # Wähle ein zufälliges Element in der Straßen-Autovervollständigungsliste aus
                        street_suggestions = WebDriverWait(driver, 10).until(
                            EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.js-select-street'))
                        )
                        selected_street_element = random.choice(street_suggestions)
                        selected_street = selected_street_element.get_attribute("data-street")
                        selected_street_element.click()

                        # Warte, bis das Hausnummern-Eingabefeld sichtbar ist
                        house_number_field = WebDriverWait(driver, 10).until(
                            EC.visibility_of_element_located((By.ID, 'check_houseNumber_1'))  # Hier die ID des Hausnummern-Eingabefelds anpassen
                        )
                        random_house_number = random.randint(1, 90)
                        house_number_field.send_keys(str(random_house_number))  # Zufällige Hausnummer

                        # Klicke auf den Verfügbarkeit prüfen Button
                        check_availability_button = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, '.uk-button.uk-button-primary.fr-button-inverted.js-check-availability'))
                        )
                        check_availability_button.click()

                        # Warte, bis die Informationen geladen sind
                        result_element = WebDriverWait(driver, 10).until(
                            EC.visibility_of_element_located((By.ID, 'js-result-headline'))  # Hier die ID des Ergebniselements anpassen
                        )

                        # Extrahiere die gewünschten Informationen
                        result_text = result_element.text

                        if "Verfügbar" in result_text:
                            print(f"Verfügbar für {plz}, {selected_street} {random_house_number}: {result_text}")
                            # Schreibe die Ergebnisse in die CSV-Datei
                            writer.writerow([ags8, ort, selected_street, str(random_house_number), plz, longitude, latitude, result_text])
                        else:
                            print(f"Nicht verfügbar für {plz}, {selected_street} {random_house_number}")

                        # Fenster schließen
                        close_button = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.ID, 'icon-cancel-1'))  # Hier die ID des Schließen-Buttons anpassen
                        )
                        close_button.click()

                    except Exception as e:
                        print(f"Fehler bei der Überprüfung von {plz}, {stn} {hnr}: {str(e)}")
                        # Zufällige Wartezeit zwischen den Anfragen
                        time.sleep(random.uniform(min_request_delay, max_request_delay))
                        continue

                except Exception as e:
                    print(f"PLZ {plz} nicht gefunden: {str(e)}")
                    # Zufällige Wartezeit zwischen den Anfragen
                    time.sleep(random.uniform(min_request_delay, max_request_delay))
                    continue

                # Zufällige Wartezeit zwischen den Anfragen
                time.sleep(random.uniform(min_request_delay, max_request_delay))

            # Zufällige Wartezeit zwischen den Batches
            time.sleep(random.uniform(min_delay, max_delay))

    finally:
        # Schließe den Browser
        driver.quit()
        # Schließe die Datenbankverbindung
        cur.close()
        conn.close()