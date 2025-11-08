"""Get the city latitude and longitude from the internet."""

# %%
import json
import re

from requests import get

url = "https://www.latlong.net/category/cities-76-15.html"
response = get(url)


data = response.text
# match the entire <a href="/place/..."> ... </a>
matches = re.findall(r'<a href="/place/(.+?)</a>', data)

all_data = []
for m in matches:
    info = m.strip()
    title_raw = info.split("title=")[1].split(">")[0][1:-2].split(",")[0]
    info = info.split()
    informations = {"title": title_raw, "lat_long": info[-1]}
    all_data.append(informations)


def handle_lat_long(raw_lat_long: str) -> tuple[float, float]:
    """Convert string to real cooridnates."""
    # input : 'class="latlong">50.954468,1.862801</span></div>'
    # output : (50.954468,1.862801)
    lat, long = raw_lat_long.split(">")[1].split("<")[0].split(",")
    return (float(lat), float(long))


for i, info in enumerate(all_data):
    lat_long = handle_lat_long(info["lat_long"])
    all_data[i]["lat_long"] = lat_long
    print(all_data[i])

# %%

with open("data/french_cities_coord.json", "w", encoding="utf-8") as f:
    json.dump(all_data, f, indent=4, ensure_ascii=False)
# %%
