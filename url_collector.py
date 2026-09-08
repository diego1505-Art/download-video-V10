import requests
import re
import json

url = "https://franime.fr/recherche"

r = requests.get(url, headers={
    "User-Agent": "Mozilla/5.0"
})

print("Status:", r.status_code)

# Cherche les données Next.js
match = re.search(
    r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
    r.text,
    re.DOTALL
)

if match:
    data = json.loads(match.group(1))
    print("NEXT_DATA trouvé")

    with open(
        "next_data.json",
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            data,
            f,
            indent=2,
            ensure_ascii=False
        )

    print("Sauvé dans next_data.json")
else:
    print("Aucune donnée NEXT_DATA trouvée")