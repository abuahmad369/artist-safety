# training/reward.py
# এটাই paper এর core contribution
#
# Reward = Accuracy - (lambda × Safety_Penalty)
#
# Accuracy     = AI সঠিক উত্তর দিয়েছে কিনা (0 বা 1)
# Safety Penalty = tool selection কতটা unsafe ছিল (0.0 থেকে 1.0)
# Lambda       = safety কতটা গুরুত্বপূর্ণ (0.1, 0.5, 1.0, 2.0)

import re
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from training.safety_checker import compute_safety_penalty


# ============================================================
# STEP A: AI এর output থেকে tool calls বের করো
# ============================================================

def extract_tool_calls(completion: str) -> list:
    """
    AI এর response থেকে tool calls parse করো

    AI এভাবে tool call করবে:
        [TOOL: contraindication_lookup(drug=ibuprofen, condition=renal impairment)]
        [TOOL: dosage_calculator(drug=acetaminophen, dose=500mg)]

    এই function সেই tool names গুলো বের করে list হিসেবে দেয়
    """
    # Pattern: [TOOL: tool_name(...)]
    pattern = r'\[TOOL:\s*(\w+)\s*\('
    tool_names = re.findall(pattern, completion)
    return tool_names


def extract_final_answer(completion: str) -> str:
    """
    AI এর response থেকে final answer বের করো

    AI এভাবে answer দেবে:
        Answer: Acetaminophen 500mg
        ANSWER: Use acetaminophen
        Final answer: ...
    """
    # Answer: ... pattern খোঁজো
    patterns = [
        r'Answer:\s*(.+?)(?:\n|$)',
        r'ANSWER:\s*(.+?)(?:\n|$)',
        r'Final answer:\s*(.+?)(?:\n|$)',
        r'Therefore[,:]?\s*(.+?)(?:\n|$)',
        r'Recommendation:\s*(.+?)(?:\n|$)',
    ]

    for pattern in patterns:
        match = re.search(pattern, completion, re.IGNORECASE)
        if match:
            return match.group(1).strip()

    # কোনো pattern না পেলে শেষ line নাও
    lines = [l.strip() for l in completion.strip().split('\n') if l.strip()]
    return lines[-1] if lines else ""


# ============================================================
# STEP B: Accuracy calculate করো
# ============================================================

def compute_accuracy(completion: str, ground_truth: str) -> float:
    """
    AI এর answer কতটা সঠিক?

    Returns:
        1.0 = সম্পূর্ণ সঠিক
        0.5 = আংশিক সঠিক (drug name ঠিক কিন্তু dose ভুল)
        0.0 = ভুল
    """
    completion_lower  = completion.lower()
    ground_truth_lower = ground_truth.lower()

    # Ground truth এর key words বের করো
    # উদাহরণ: "Acetaminophen 500mg" → ["acetaminophen", "500mg"]
    truth_words = ground_truth_lower.split()

    # Drug name (প্রথম word সাধারণত drug name)
    main_drug = truth_words[0] if truth_words else ""

    # সম্পূর্ণ match
    if ground_truth_lower in completion_lower:
        return 1.0

    # Drug name match (partial credit)
    if main_drug and main_drug in completion_lower:
        return 0.5

    # কোনো match নেই
    return 0.0


# ============================================================
# STEP C: Final Safety-Aware Reward
# ============================================================

def safety_aware_reward(completion: str,
                        ground_truth: str,
                        patient_context: str,
                        lambda_val: float = 0.5) -> float:
    """
    Paper এর core formula:
    Reward = Accuracy - (lambda × Safety_Penalty)

    Parameters:
        completion     : AI এর পুরো response
        ground_truth   : সঠিক উত্তর
        patient_context: রোগীর তথ্য
        lambda_val     : safety weight (0.1=lenient, 2.0=strict)

    Returns:
        float: -1.0 থেকে 1.0 এর মধ্যে
               বেশি মানে ভালো
               কম/negative মানে খারাপ
    """

    # --- ACCURACY COMPONENT ---
    accuracy = compute_accuracy(completion, ground_truth)

    # --- SAFETY PENALTY COMPONENT ---
    tool_sequence = extract_tool_calls(completion)

    if not tool_sequence:
        # কোনো tool call নেই — accuracy শুধু
        # কিন্তু high-risk রোগীতে tool না ব্যবহার করা নিজেই unsafe
        from training.safety_checker import detect_patient_risks
        risks = detect_patient_risks(patient_context)
        if risks:
            avg_penalty = 0.3  # tool ব্যবহার না করার penalty
        else:
            avg_penalty = 0.0
    else:
        # প্রতিটি tool এর penalty calculate করো
        penalties = []
        called_so_far = []

        for tool_name in tool_sequence:
            penalty = compute_safety_penalty(
                patient_context, tool_name, called_so_far
            )
            penalties.append(penalty)
            called_so_far.append(tool_name)

        avg_penalty = sum(penalties) / len(penalties)

    # --- FINAL REWARD ---
    reward = accuracy - (lambda_val * avg_penalty)

    # -1.0 থেকে 1.0 এর মধ্যে রাখো
    reward = max(reward, -1.0)
    reward = min(reward, 1.0)

    return reward


# ============================================================
# STEP D: Batch reward (training এ use হবে)
# ============================================================

def compute_batch_rewards(completions: list,
                          ground_truths: list,
                          patient_contexts: list,
                          lambda_val: float = 0.5) -> list:
    """
    একসাথে অনেকগুলো completion evaluate করো
    GRPO training এ এটা use হবে
    """
    assert len(completions) == len(ground_truths) == len(patient_contexts), \
        "সব list এর length same হতে হবে!"

    rewards = []
    for comp, truth, context in zip(completions, ground_truths,
                                    patient_contexts):
        r = safety_aware_reward(comp, truth, context, lambda_val)
        rewards.append(r)

    return rewards