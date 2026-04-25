# tests/test_day6.py
# Kaggle training এর আগে সব কিছু ঠিক আছে কিনা check করো

import sys, os, json
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from training.reward import safety_aware_reward, extract_tool_calls
from training.safety_checker import detect_patient_risks

print("=" * 60)
print("Day 6 — Training Setup Test")
print("=" * 60)

# TEST 1: Dataset load হচ্ছে কিনা
with open("dataset/scenarios.json", encoding="utf-8") as f:
    scenarios = json.load(f)
assert len(scenarios) >= 100
print(f"\n✓ TEST 1 PASSED — {len(scenarios)} scenarios loaded")

# TEST 2: Reward function ঠিকমতো কাজ করছে কিনা
good = """
[TOOL: contraindication_lookup(drug=ibuprofen, condition=anticoagulation)]
[TOOL: drug_interaction_checker(drug1=warfarin, drug2=acetaminophen)]
Answer: Acetaminophen 500mg
"""
bad = """
[TOOL: dosage_calculator(drug=ibuprofen, dose=400mg)]
Answer: Ibuprofen 400mg
"""
patient = "68F, warfarin 5mg/day, CKD stage 3"
truth   = "Acetaminophen 500mg"

r_good = safety_aware_reward(good, truth, patient, 0.5)
r_bad  = safety_aware_reward(bad,  truth, patient, 0.5)

assert r_good > r_bad, "Good path এ reward বেশি হওয়া উচিত!"
print(f"✓ TEST 2 PASSED — Good: {r_good:.2f}, Bad: {r_bad:.2f}")

# TEST 3: সব scenarios এ required fields আছে কিনা
for s in scenarios:
    assert "patient_context" in s
    assert "ground_truth_answer" in s
    assert "correct_tool_path" in s
print("✓ TEST 3 PASSED — সব scenarios valid")

# TEST 4: Lambda sweep simulation
print("\nLambda sweep simulation:")
for lam in [0.1, 0.5, 1.0, 2.0]:
    r = safety_aware_reward(bad, truth, patient, lam)
    print(f"  λ={lam}: unsafe path reward = {r:.3f}")

print("\n" + "=" * 60)
print("সব PASSED! Kaggle এ training দিতে পারো।")
print("\nPlan:")
print("  Run 1: LAMBDA = 0.1  (lenient)")
print("  Run 2: LAMBDA = 0.5  (balanced) ← best হবে সম্ভবত")
print("  Run 3: LAMBDA = 1.0  (strict)")
print("=" * 60)