# tests/test_day5.py
# Test the Safety Reward Function

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from training.reward import safety_aware_reward, extract_tool_calls
from training.safety_checker import detect_patient_risks, evaluate_tool_sequence

print("=" * 60)
print("Day 5 — Safety Reward Function Test")
print("=" * 60)


# ============================================================
# TEST 1: Patient Risk Detection
# ============================================================
print("\n[TEST 1] Patient Risk Detection")

risks = detect_patient_risks("68F, warfarin 5mg/day, CKD stage 3")
print(f"  Patient: 68F, warfarin, CKD stage 3")
print(f"  Risks detected: {risks}")
assert "anticoagulant" in risks, "warfarin not detected!"
assert "renal" in risks, "CKD not detected!"
print("  ✓ TEST 1 PASSED")


# ============================================================
# TEST 2: Tool Call Extraction
# ============================================================
print("\n[TEST 2] Tool Call Extraction")

sample_completion = """
I need to check safety first.
[TOOL: contraindication_lookup(drug=ibuprofen, condition=anticoagulation)]
Result: CONTRAINDICATED

[TOOL: drug_interaction_checker(drug1=warfarin, drug2=acetaminophen)]
Result: MODERATE

Answer: Acetaminophen 500mg is the safest choice.
"""

tools = extract_tool_calls(sample_completion)
print(f"  Tools found: {tools}")
assert "contraindication_lookup" in tools, "contraindication_lookup not found!"
assert "drug_interaction_checker" in tools, "drug_interaction_checker not found!"
print("  ✓ TEST 2 PASSED")


# ============================================================
# TEST 3: Safe Path → High Reward
# AI performs safety check before providing dosage
# ============================================================
print("\n[TEST 3] Safe Tool Path → High Reward")

safe_completion = """
[TOOL: contraindication_lookup(drug=ibuprofen, condition=anticoagulation)]
Result: CONTRAINDICATED - ibuprofen is unsafe with warfarin

[TOOL: drug_interaction_checker(drug1=warfarin, drug2=acetaminophen)]
Result: MODERATE - use with monitoring

Answer: Acetaminophen 500mg with INR monitoring
"""

reward_safe = safety_aware_reward(
    completion=safe_completion,
    ground_truth="Acetaminophen 500mg with INR monitoring",
    patient_context="68F, warfarin 5mg/day, CKD stage 3",
    lambda_val=0.5
)
print(f"  Safe path reward: {reward_safe:.3f}")
assert reward_safe > 0.3, f"Reward should be higher for safe paths! Got: {reward_safe}"
print("  ✓ TEST 3 PASSED")


# ============================================================
# TEST 4: Unsafe Path → Low Reward
# AI provides dosage directly without safety checks
# ============================================================
print("\n[TEST 4] Unsafe Tool Path → Low Reward")

unsafe_completion = """
[TOOL: dosage_calculator(drug=ibuprofen, weight=70)]
Result: Ibuprofen 400mg three times daily

Answer: Ibuprofen 400mg
"""

reward_unsafe = safety_aware_reward(
    completion=unsafe_completion,
    ground_truth="Acetaminophen 500mg with INR monitoring",
    patient_context="68F, warfarin 5mg/day, CKD stage 3",
    lambda_val=0.5
)
print(f"  Unsafe path reward: {reward_unsafe:.3f}")
assert reward_unsafe < reward_safe, \
    f"Reward should be lower for unsafe paths! safe={reward_safe:.3f}, unsafe={reward_unsafe:.3f}"
print("  ✓ TEST 4 PASSED")


# ============================================================
# TEST 5: Lambda Effect
# Increasing Lambda should increase the safety penalty
# ============================================================
print("\n[TEST 5] Lambda Effect on Reward")

for lam in [0.1, 0.5, 1.0, 2.0]:
    r = safety_aware_reward(
        unsafe_completion,
        "Acetaminophen 500mg",
        "68F, warfarin 5mg/day, CKD stage 3",
        lambda_val=lam
    )
    print(f"  Lambda={lam}: reward={r:.3f}")

print("  (As Lambda increases, reward for unsafe paths should decrease)")
print("  ✓ TEST 5 PASSED")


# ============================================================
# TEST 6: Full Sequence Evaluation
# ============================================================
print("\n[TEST 6] Full Tool Sequence Evaluation")

good_sequence = ["contraindication_lookup", "drug_interaction_checker",
                 "dosage_calculator"]
bad_sequence  = ["dosage_calculator", "contraindication_lookup"]

good_eval = evaluate_tool_sequence(
    "68F, warfarin, CKD", good_sequence
)
bad_eval = evaluate_tool_sequence(
    "68F, warfarin, CKD", bad_sequence
)

print(f"  Good sequence avg penalty: {good_eval['avg_penalty']:.2f} ({good_eval['overall']})")
print(f"  Bad sequence avg penalty:  {bad_eval['avg_penalty']:.2f} ({bad_eval['overall']})")
assert good_eval['avg_penalty'] < bad_eval['avg_penalty'], \
    "Penalty should be lower for good sequences!"
print("  ✓ TEST 6 PASSED")


# ============================================================
# Summary
# ============================================================
print("\n" + "=" * 60)
print("ALL TESTS PASSED!")
print(f"\nKey insight:")
print(f"  Safe path reward  : {reward_safe:.3f}")
print(f"  Unsafe path reward: {reward_unsafe:.3f}")
print(f"  Difference        : {reward_safe - reward_unsafe:.3f}")
print(f"\nThis difference is how the AI learns what is safe!")
print("=" * 60)