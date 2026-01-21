import requests
import json

API_KEY = "2DhdX43LQnvJVqkUEtshqr2umFFqkPJC"
BASE_URL = "https://apiservice1.gsignalx.cloud"

headers = {"Authorization": f"Bearer {API_KEY}"}
all_signals = []
page = 1
per_page = 100  # Adjust as needed based on API's max page size

while True:
    params = {"page": page, "per_page": per_page}
    response = requests.get(f"{BASE_URL}/api/third-party/signals", headers=headers, params=params)
    if response.status_code != 200:
        print(f"❌ Error on page {page}: {response.status_code}")
        print(response.json())
        break

    data = response.json()
    symbols = data.get('symbols', [])
    all_signals.extend(symbols)

    total_count = data.get('data_count', 0)
    print(f"Fetched page {page}: {len(symbols)} signals (Total: {len(all_signals)}/{total_count})")

    # If we've fetched all signals or no more symbols returned, stop
    if len(all_signals) >= total_count or not symbols:
        break
    page += 1

# Save all signals to a JSON file
with open("all_signals.json", "w") as f:
    json.dump(all_signals, f, indent=2)

print(f"✅ Success! Saved {len(all_signals)} signals to all_signals.json")