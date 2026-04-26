# tests/test_day3.py
# File to test all tools for Day 3
# This is for testing purposes only — not the main project code

import sys
import os

# Identify project root
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from tools.tool_registry import TOOL_REGISTRY

print("=" * 60)
print("Day 3 — Tool Test Starting")
print("=" * 60)


# ============================================================
# TEST 1: ContraindicationLookup
# Question: Is ibuprofen contraindicated in renal impairment?
# Expected Result: CONTRAINDICATED (Yes, restricted)
# ============================================================
print("\n[TEST 1] Contraindication Lookup")
print("Question: Is ibuprofen safe for patients with renal impairment?")

tool1 = TOOL_REGISTRY["contraindication_lookup"]
result1 = tool1(drug="ibuprofen", condition="renal impairment")

print(f"\nStatus   : {result1.status}")
print(f"Reasoning: {result1.reasoning[:200]}")

if result1.status in ["CONTRAINDICATED", "USE_WITH_CAUTION"]:
    print("✓ TEST 1 PASSED — Tool is correctly providing a warning")
else:
    print("△ TEST 1 — Showing SAFE, please check FDA data")


# ============================================================
# TEST 2: DrugInteractionChecker
# Question: Is it safe to give warfarin + ibuprofen together?
# Expected Result: HIGH (No, dangerous)
# ============================================================
print("\n[TEST 2] Drug Interaction Checker")
print("Question: Is it safe to combine warfarin + ibuprofen?")

tool2 = TOOL_REGISTRY["drug_interaction_checker"]
result2 = tool2(drug1="warfarin", drug2="ibuprofen")

print(f"\nStatus   : {result2.status}")
print(f"Reasoning: {result2.reasoning[:200]}")

if result2.status in ["HIGH", "N-A", "CONTRAINDICATED"]:
    print("✓ TEST 2 PASSED — Tool correctly detected the interaction")
else:
    print(f"△ TEST 2 — Status: {result2.status} (If showing SAFE, RxNorm data is missing)")


# ============================================================
# TEST 3: Safe drug check
# Question: How is acetaminophen + warfarin?
# Expected Result: MODERATE (Can be given with caution)
# ============================================================
print("\n[TEST 3] Safe Drug Interaction Check")
print("Question: How is the combination of warfarin + acetaminophen?")

result3 = tool2(drug1="warfarin", drug2="acetaminophen")

print(f"\nStatus   : {result3.status}")
print(f"Reasoning: {result3.reasoning[:200]}")
print("(Should be safer than ibuprofen)")


print("\n" + "=" * 60)
print("Test Complete!")
print("Check the cache\\ folder for .json files — API responses are saved there")
print("=" * 60)