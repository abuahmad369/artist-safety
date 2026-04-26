# demo.py
# Check if your project is working correctly

import sys
sys.path.append(".")

from tools.tool_registry import TOOL_REGISTRY
from training.reward import safety_aware_reward

print("="*60)
print("ARTIST Safety - Live Demo")
print("="*60)

# Case 1: Dangerous path (dosage given without safety check)
dangerous_completion = """
[TOOL: dosage_calculator(drug=ibuprofen, weight=70)]
Answer: Ibuprofen 400mg three times daily
"""

# Case 2: Safe path (safety check performed before dosage)
safe_completion = """
[TOOL: contraindication_lookup(drug=ibuprofen, condition=anticoagulation)]
Result: CONTRAINDICATED

[TOOL: drug_interaction_checker(drug1=warfarin, drug2=acetaminophen)]
Result: MODERATE

Answer: Acetaminophen 500mg with INR monitoring
"""

patient = "68F, warfarin 5mg/day, CKD stage 3"
truth   = "Acetaminophen 500mg with INR monitoring"

r_dangerous = safety_aware_reward(dangerous_completion, truth, patient, 0.5)
r_safe      = safety_aware_reward(safe_completion, truth, patient, 0.5)

print(f"\nPatient: {patient}")
print(f"\nDangerous path reward: {r_dangerous:.3f}")
print(f"Safe path reward      : {r_safe:.3f}")

if r_safe > r_dangerous:
    print("\nSYSTEM WORKS! Safe path gets higher reward.")
else:
    print("\nSomething went wrong.")

# Real tool test
print("\n--- Real Tool Test ---")
tool = TOOL_REGISTRY["contraindication_lookup"]
result = tool(drug="ibuprofen", condition="renal impairment")
print(f"ibuprofen + renal impairment = {result.status}")

tool2 = TOOL_REGISTRY["drug_interaction_checker"]
result2 = tool2(drug1="warfarin", drug2="ibuprofen")
print(f"warfarin + ibuprofen = {result2.status}")