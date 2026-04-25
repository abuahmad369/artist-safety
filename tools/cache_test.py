# tools/cache_test.py
# এই file দিয়ে cache কাজ করছে কিনা দেখবো

import sys
import os

# project root folder টা Python কে চেনাও
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from tools.cache_client import client

print("=" * 50)
print("Cache Test শুরু হচ্ছে...")
print("=" * 50)

# প্রথমবার — API call হবে এবং cache-এ save হবে
print("\n--- প্রথমবার call করছি ---")
data1 = client.get(
    "https://rxnav.nlm.nih.gov/REST/rxcui.json",
    params={"name": "warfarin"}
)
print("Warfarin ID:", data1["idGroup"]["rxnormId"][0])

# দ্বিতীয়বার — Cache থেকে নেবে, API call হবে না
print("\n--- দ্বিতীয়বার same call করছি ---")
data2 = client.get(
    "https://rxnav.nlm.nih.gov/REST/rxcui.json",
    params={"name": "warfarin"}
)
print("Warfarin ID:", data2["idGroup"]["rxnormId"][0])

print("\n" + "=" * 50)
print("দ্বিতীয়বার [CACHE HIT] দেখালে cache কাজ করছে!")
print("cache folder এ .json file দেখো")
print("=" * 50)