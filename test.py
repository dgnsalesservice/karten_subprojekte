from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
# URL of the website to scrape
url = 'https://glasfaser-nordwest.de/'




# Set up the web driver (ensure chromedriver is in your PATH or provide the executable path)
driver = webdriver.Chrome()

# Open the website
driver.get(url)

# Wait for the map element to load
WebDriverWait(driver, 100).until(
    EC.presence_of_element_located((By.ID, 'map-geolocation'))
)

# Perform a series of zoom actions to ensure the map is fully loaded
map_element = driver.find_element(By.ID, 'map-geolocation')
actions = ActionChains(driver)

for _ in range(5):  # Adjust the range for the required zoom level
    actions.move_to_element(map_element).click().perform()

# Wait for the popups to load within the map
WebDriverWait(driver, 10).until(
    EC.presence_of_all_elements_located((By.CLASS_NAME, 'leaflet-popup-content'))
)

# Find all popup elements
popups = driver.find_elements(By.CLASS_NAME, 'leaflet-popup-content')

# Extract text from each popup
popup_texts = [popup.text for popup in popups]

# Save the texts to a file
with open('popup_texts.txt', 'w', encoding='utf-8') as file:
    for text in popup_texts:
        file.write(text + '\n')

print('Popup texts have been exported to popup_texts.txt')

# Close the browser
driver.quit()
