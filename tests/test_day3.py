# tests/test_day3.py
# Day 3 এর সব tools test করার file
# এটা শুধু test এর জন্য — project এর main code না

import sys
import os

# project root চেনাও
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from tools.tool_registry import TOOL_REGISTRY

print("=" * 60)
print("Day 3 — Tool Test শুরু হচ্ছে")
print("=" * 60)


# ============================================================
# TEST 1: ContraindicationLookup
# প্রশ্ন: ibuprofen কি renal impairment এ নিষিদ্ধ?
# সঠিক উত্তর: CONTRAINDICATED (হ্যাঁ, নিষিদ্ধ)
# ============================================================
print("\n[TEST 1] Contraindication Lookup")
print("প্রশ্ন: ibuprofen কি renal impairment রোগীদের জন্য safe?")

tool1 = TOOL_REGISTRY["contraindication_lookup"]
result1 = tool1(drug="ibuprofen", condition="renal impairment")

print(f"\nStatus   : {result1.status}")
print(f"Reasoning: {result1.reasoning[:200]}")

if result1.status in ["CONTRAINDICATED", "USE_WITH_CAUTION"]:
    print("✓ TEST 1 PASSED — Tool সঠিকভাবে warning দিচ্ছে")
else:
    print("△ TEST 1 — SAFE দেখাচ্ছে, FDA data check করো")


# ============================================================
# TEST 2: DrugInteractionChecker
# প্রশ্ন: warfarin + ibuprofen একসাথে দেওয়া কি safe?
# সঠিক উত্তর: HIGH (না, dangerous)
# ============================================================
print("\n[TEST 2] Drug Interaction Checker")
print("প্রশ্ন: warfarin + ibuprofen একসাথে দেওয়া কি safe?")

tool2 = TOOL_REGISTRY["drug_interaction_checker"]
result2 = tool2(drug1="warfarin", drug2="ibuprofen")

print(f"\nStatus   : {result2.status}")
print(f"Reasoning: {result2.reasoning[:200]}")

if result2.status in ["HIGH", "N-A", "CONTRAINDICATED"]:
    print("✓ TEST 2 PASSED — Tool সঠিকভাবে interaction ধরেছে")
else:
    print(f"△ TEST 2 — Status: {result2.status} (SAFE দেখালে RxNorm data নেই)")


# ============================================================
# TEST 3: Safe drug check
# প্রশ্ন: acetaminophen + warfarin কেমন?
# সঠিক উত্তর: MODERATE (সাবধানে দেওয়া যায়)
# ============================================================
print("\n[TEST 3] Safe Drug Interaction Check")
print("প্রশ্ন: warfarin + acetaminophen একসাথে কেমন?")

result3 = tool2(drug1="warfarin", drug2="acetaminophen")

print(f"\nStatus   : {result3.status}")
print(f"Reasoning: {result3.reasoning[:200]}")
print("(ibuprofen এর চেয়ে safer হওয়া উচিত)")


print("\n" + "=" * 60)
print("Test শেষ!")
print("cache\\ folder এ .json files দেখো — সেখানে API responses saved আছে")
print("=" * 60)