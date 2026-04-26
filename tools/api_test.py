# tools/api_test.py
# This file is used to check if the three APIs are working correctly

import requests  # This library is used to fetch data from the internet

print("=" * 50)
print("Starting API Test...")
print("=" * 50)

# =====================
# TEST 1: OpenFDA API
# =====================
# OpenFDA is the US government's drug database
# We use this to retrieve drug warnings
print("\n[1] Testing OpenFDA...")

try:
    response = requests.get(
        "https://api.fda.gov/drug/label.json",
        params={"search": "ibuprofen", "limit": 1},
        timeout=10  # Do not wait longer than 10 seconds
    )
    
    if response.status_code == 200:
        data = response.json()
        print("✓ OpenFDA OK! Status:", response.status_code)
        # Display the first 100 characters of the ibuprofen warning
        warning = data['results'][0].get('warnings', ['No warnings found'])[0]
        print("  ibuprofen warning:", warning[:100], "...")
    else:
        print("✗ OpenFDA FAILED! Status:", response.status_code)

except Exception as e:
    print("✗ OpenFDA ERROR:", e)


# =====================
# TEST 2: RxNorm API
# =====================
# RxNorm is a drug database from the NIH (National Institute of Health)
# We use this to check interactions between two drugs
print("\n[2] Testing RxNorm...")

try:
    # Step A: First, find the ID (RxCUI) for warfarin
    response_w = requests.get(
        "https://rxnav.nlm.nih.gov/REST/rxcui.json",
        params={"name": "warfarin"},
        timeout=10
    )
    
    warfarin_id = response_w.json()["idGroup"]["rxnormId"][0]
    print("  Warfarin RxCUI ID:", warfarin_id)  # Should display 202433
    
    # Step B: Find the ID for ibuprofen
    response_i = requests.get(
        "https://rxnav.nlm.nih.gov/REST/rxcui.json",
        params={"name": "ibuprofen"},
        timeout=10
    )
    
    ibuprofen_id = response_i.json()["idGroup"]["rxnormId"][0]
    print("  Ibuprofen RxCUI ID:", ibuprofen_id)  # Should display 5640
    
    # Step C: Now check the interaction between the two
    response_int = requests.get(
        "https://rxnav.nlm.nih.gov/REST/interaction/list.json",
        params={"rxcuis": f"{warfarin_id} {ibuprofen_id}"},  # Separated by space
        timeout=10
    )
    
    if response_int.status_code == 200:
        print("✓ RxNorm OK! Status:", response_int.status_code)
        # Display interaction description
        try:
            interaction_data = response_int.json()
            pairs = interaction_data["fullInteractionTypeGroup"][0]["fullInteractionType"][0]["interactionPair"]
            severity = pairs[0]["severity"]
            print(f"  Warfarin + Ibuprofen interaction: {severity}")
            # Likely to show HIGH or N-A — warfarin + ibuprofen is dangerous!
        except:
            print("  Interaction data not found (perhaps no interaction exists)")
    else:
        print("✗ RxNorm FAILED! Status:", response_int.status_code)

except Exception as e:
    print("✗ RxNorm ERROR:", e)


# =====================
# TEST 3: LOINC API
# =====================
# LOINC is a database for lab tests
# We use this to get normal ranges for blood tests
print("\n[3] Testing LOINC...")

try:
    response = requests.get(
        "https://clinicaltables.nlm.nih.gov/api/loinc_items/v3/search",
        params={"terms": "hemoglobin", "df": "LOINC_NUM,LONG_COMMON_NAME"},
        timeout=10
    )
    
    if response.status_code == 200:
        data = response.json()
        print("✓ LOINC OK! Status:", response.status_code)
        print("  Hemoglobin test LOINC code:", data[1][0][0] if data[1] else "N/A")
    else:
        print("✗ LOINC FAILED! Status:", response.status_code)

except Exception as e:
    print("✗ LOINC ERROR:", e)


print("\n" + "=" * 50)
print("Test Complete!")
print("=" * 50)