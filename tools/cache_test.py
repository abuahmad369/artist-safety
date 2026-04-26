# tools/cache_test.py
# Use this file to verify if the caching mechanism is working

import sys
import os

# Point Python to the project root folder
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from tools.cache_client import client

print("=" * 50)
print("Starting Cache Test...")
print("=" * 50)

# First attempt — API call should trigger and save to cache
print("\n--- Executing first call ---")
data1 = client.get(
    "https://rxnav.nlm.nih.gov/REST/rxcui.json",
    params={"name": "warfarin"}
)
print("Warfarin ID:", data1["idGroup"]["rxnormId"][0])

# Second attempt — Should retrieve from cache without an API call
print("\n--- Executing same call a second time ---")
data2 = client.get(
    "https://rxnav.nlm.nih.gov/REST/rxcui.json",
    params={"name": "warfarin"}
)
print("Warfarin ID:", data2["idGroup"]["rxnormId"][0])

print("\n" + "=" * 50)
print("If [CACHE HIT] appeared on the second call, caching is functional!")
print("Check the cache folder for the generated .json files")
print("=" * 50)