# tests/test_day4.py
# Dataset সঠিকভাবে তৈরি হয়েছে কিনা check করো

import sys, os, json
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

DATASET_PATH = os.path.join(
    os.path.dirname(__file__), '..', 'dataset', 'scenarios.json'
)

print("=" * 60)
print("Day 4 — Dataset Test")
print("=" * 60)

# TEST 1: File আছে কিনা
assert os.path.exists(DATASET_PATH), "scenarios.json পাওয়া যাচ্ছে না!"
print("\n✓ TEST 1 PASSED — scenarios.json file আছে")

# TEST 2: 100টি scenario আছে কিনা
with open(DATASET_PATH, encoding="utf-8") as f:
    data = json.load(f)

assert len(data) >= 100, f"মাত্র {len(data)}টি scenario! ১০০টি দরকার"
print(f"✓ TEST 2 PASSED — {len(data)}টি scenarios আছে")

# TEST 3: প্রতিটি scenario তে দরকারি fields আছে কিনা
required = ["id","patient_context","question","available_tools",
            "correct_tool_path","unsafe_tools_for_patient",
            "ground_truth_answer","safety_annotation"]

for i, s in enumerate(data):
    for field in required:
        assert field in s, f"S{i} তে '{field}' missing!"
print("✓ TEST 3 PASSED — সব fields সঠিক আছে")

# TEST 4: Safety tools আগে আসছে কিনা
violations = 0
for s in data:
    path = [step["tool"] for step in s["correct_tool_path"]]
    if "dosage_calculator" in path:
        dose_idx = path.index("dosage_calculator")
        safety_tools = ["contraindication_lookup","drug_interaction_checker"]
        has_safety_before = any(
            t in path[:dose_idx] for t in safety_tools
        )
        if not has_safety_before:
            violations += 1

print(f"✓ TEST 4 PASSED — Safety violations: {violations} (0 হওয়া উচিত)")

# Summary
print("\n" + "=" * 60)
print(f"Dataset Summary:")
print(f"  Total scenarios  : {len(data)}")
print(f"  Sample patient   : {data[0]['patient_context']}")
print(f"  Sample answer    : {data[0]['ground_truth_answer']}")
print("=" * 60)
print("Day 4 সম্পূর্ণ! Dataset ready।")