# tools/api_test.py
# এই file টা দিয়ে আমরা দেখবো 3টি API কাজ করছে কিনা

import requests  # এই library দিয়ে internet থেকে data আনা হয়

print("=" * 50)
print("API Test শুরু হচ্ছে...")
print("=" * 50)

# =====================
# TEST 1: OpenFDA API
# =====================
# OpenFDA হলো US government এর drug database
# আমরা এখান থেকে ওষুধের warning পাবো
print("\n[1] OpenFDA test করছি...")

try:
    response = requests.get(
        "https://api.fda.gov/drug/label.json",
        params={"search": "ibuprofen", "limit": 1},
        timeout=10  # 10 seconds এর বেশি wait করবো না
    )
    
    if response.status_code == 200:
        data = response.json()
        print("✓ OpenFDA OK! Status:", response.status_code)
        # ibuprofen এর warning এর প্রথম 100 character দেখাও
        warning = data['results'][0].get('warnings', ['কোনো warning নেই'])[0]
        print("  ibuprofen warning:", warning[:100], "...")
    else:
        print("✗ OpenFDA FAILED! Status:", response.status_code)

except Exception as e:
    print("✗ OpenFDA ERROR:", e)


# =====================
# TEST 2: RxNorm API
# =====================
# RxNorm হলো NIH (National Institute of Health) এর drug database
# আমরা এখান থেকে দুটো ওষুধের interaction দেখবো
print("\n[2] RxNorm test করছি...")

try:
    # Step A: আগে warfarin এর ID (RxCUI) বের করো
    response_w = requests.get(
        "https://rxnav.nlm.nih.gov/REST/rxcui.json",
        params={"name": "warfarin"},
        timeout=10
    )
    
    warfarin_id = response_w.json()["idGroup"]["rxnormId"][0]
    print("  Warfarin এর RxCUI ID:", warfarin_id)  # 202433 দেখাবে
    
    # Step B: ibuprofen এর ID বের করো
    response_i = requests.get(
        "https://rxnav.nlm.nih.gov/REST/rxcui.json",
        params={"name": "ibuprofen"},
        timeout=10
    )
    
    ibuprofen_id = response_i.json()["idGroup"]["rxnormId"][0]
    print("  Ibuprofen এর RxCUI ID:", ibuprofen_id)  # 5640 দেখাবে
    
    # Step C: এখন দুটোর interaction check করো
    response_int = requests.get(
        "https://rxnav.nlm.nih.gov/REST/interaction/list.json",
        params={"rxcuis": f"{warfarin_id} {ibuprofen_id}"},  # space দিয়ে আলাদা
        timeout=10
    )
    
    if response_int.status_code == 200:
        print("✓ RxNorm OK! Status:", response_int.status_code)
        # Interaction এর description দেখাও
        try:
            interaction_data = response_int.json()
            pairs = interaction_data["fullInteractionTypeGroup"][0]["fullInteractionType"][0]["interactionPair"]
            severity = pairs[0]["severity"]
            print(f"  Warfarin + Ibuprofen interaction: {severity}")
            # HIGH বা N-A দেখাবে — warfarin + ibuprofen dangerous!
        except:
            print("  Interaction data পাওয়া যায়নি (হয়তো কোনো interaction নেই)")
    else:
        print("✗ RxNorm FAILED! Status:", response_int.status_code)

except Exception as e:
    print("✗ RxNorm ERROR:", e)


# =====================
# TEST 3: LOINC API
# =====================
# LOINC হলো lab test এর database
# আমরা এখান থেকে blood test এর normal range পাবো
print("\n[3] LOINC test করছি...")

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
print("Test শেষ!")
print("=" * 50)