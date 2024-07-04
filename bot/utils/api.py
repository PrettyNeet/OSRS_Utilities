import requests
from config.settings import HEADERS


# Grabs latest prices from wiki API, returns the entire list of all items to save an API resource
def fetch_latest_prices():
    url = "https://prices.runescape.wiki/api/v1/osrs/latest"
    response = requests.get(url, headers=HEADERS)  # OSRS wiki demands custom user-agent headers, defined in config.yaml. python requests are blocked by default
    data = response.json()

    if "data" not in data:
        raise ValueError("Error fetching data from API")
    return data["data"]


def fetch_1h_prices():
    url = "https://prices.runescape.wiki/api/v1/osrs/1h"
    response = requests.get(url, headers=HEADERS)
    data = response.json()
    if "data" not in data:
        raise ValueError("Error fetching data from API")
    return data["data"]