import requests
import subprocess
from datetime import datetime

url = "https://api.scryfall.com/sets"
response = requests.get(url)
response.raise_for_status()
sets = response.json()["data"]

filtered_sets = [
    s for s in sets
    if s.get("released_at")
    and datetime.fromisoformat(s["released_at"]).year >= 2025
    and s["set_type"] == "expansion"
]

for s in filtered_sets:
    subprocess.run(
        ["python", "build_deck.py", "-s", s["code"], "-o", "decks"],
        check=True
)
