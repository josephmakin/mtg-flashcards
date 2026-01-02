import argparse
import requests
import genanki
import os
from jinja2 import Environment, FileSystemLoader

def fetch_cards(set_code):
    cards = []
    url = "https://api.scryfall.com/cards/search"
    params = {"q": f"s:{set_code} -type:basic"}

    while url:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        cards.extend(data['data'])
        url = data.get('next_page')
        params = None

    return cards


def build_deck(cards):
    deck_id = abs(hash(SET_CODE)) % 10**10

    deck = genanki.Deck(
        deck_id=deck_id,
        name=SET_CODE.upper()  # Deck name is the set code
    )

    model = genanki.Model(
        model_id=1607392319,
        name="Card Model",
        fields=[
            {"name": "Front"},
            {"name": "Back"},
        ],
        templates=[
            {
                "name": "Card 1",
                "qfmt": "{{Front}}",
                "afmt": "{{FrontSide}}<hr id='answer'>{{Back}}",
            },
        ],
    )

    for card in cards:
        front_html = front_template.render(card=card)
        back_html = back_template.render(card=card)

        type_line = card.get("type_line", "")
        keywords = card.get("keywords", [])
        colors = card.get("color_identity", [])

        tags = [t.title()
        for t in (type_line.split("—")[0].strip().split() +
                  (type_line.split("—")[1].strip().split() if "—" in type_line else []))]

        tags += [keyword.replace(" ", "_").title() for keyword in keywords]
        tags += [c.title() for c in colors]
        rarity = card.get("rarity", "")
        if rarity:
            tags.append(rarity.title())

        note = genanki.Note(
            model=model,
            fields=[front_html, back_html],
            tags=tags
        )
        deck.add_note(note)

    return deck

env = Environment(loader=FileSystemLoader("templates"))
front_template = env.get_template("front.html")
back_template = env.get_template("back.html")

parser = argparse.ArgumentParser()
parser.add_argument(
    "-s", "--set",
    type=str,
    required=True
)
parser.add_argument(
    "-o", "--output",
    type=str,
    default="."
)

args = parser.parse_args()

SET_CODE = args.set
OUTPUT_DIRECTORY = args.output

os.makedirs(OUTPUT_DIRECTORY, exist_ok=True)

try:
    cards = fetch_cards(SET_CODE)
except Exception as e:
    print(f"Error fetching cards for set {SET_CODE}: {e}")
else:
    print(f"Fetched {len(cards)} cards from set {SET_CODE.upper()}.")
    deck = build_deck(cards)


filename = f"{SET_CODE.upper()}.apkg"
try:
    package = genanki.Package(deck)
    css_path = "templates/styles.css"
    if os.path.exists(css_path):
        package.media_files = [css_path]

    package.write_to_file(f"{OUTPUT_DIRECTORY}/{filename}")

    print(f"Anki deck created: {filename} ({len(cards)} cards)")
    print(f"Deck saved to: {os.path.abspath(os.path.join(OUTPUT_DIRECTORY, filename))}")
except Exception as e:
    print(f"Failed to write deck: {e}")
