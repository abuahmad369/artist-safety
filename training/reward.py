# training/reward.py
# This is the core contribution of the paper
#
# Reward = Accuracy - (lambda × Safety_Penalty)
#
# Accuracy      = Whether the AI provided the correct answer (0 or 1)
# Safety Penalty = How unsafe the tool selection was (0.0 to 1.0)
# Lambda        = Weight of safety importance (0.1, 0.5, 1.0, 2.0)

import re
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from training.safety_checker import compute_safety_penalty


# ============================================================
# STEP A: Extract tool calls from AI output
# ============================================================

def extract_tool_calls(completion: str) -> list:
    """
    Parse tool calls from the AI response

    The AI will call tools like this:
        [TOOL: contraindication_lookup(drug=ibuprofen, condition=renal impairment)]
        [TOOL: dosage_calculator(drug=acetaminophen, dose=500mg)]

    This function extracts those tool names and returns them as a list.
    """
    # Pattern: [TOOL: tool_name(...)]
    pattern = r'\[TOOL:\s*(\w+)\s*\('
    tool_names = re.findall(pattern, completion)
    return tool_names


def extract_final_answer(completion: str) -> str:
    """
    Extract the final answer from the AI response

    The AI will provide answers like:
        Answer: Acetaminophen 500mg
        ANSWER: Use acetaminophen
        Final answer: ...
    """
    # Look for Answer: ... patterns
    patterns = [
        r'Answer:\s*(.+?)(?:\n|$)',
        r'ANSWER:\s*(.+?)(?:\n|$)',
        r'\s*(.+?)(?:\n|$)',
        r'Therefore[,:]?\s*(.+?)(?:\n|$)',
        r'Recommendation:\s*(.+?)(?:\n|$)',
    ]

    for pattern in patterns:
        match = re.search(pattern, completion, re.IGNORECASE)
        if match:
            return match.group(1).strip()

    # If no pattern is found, take the last non-empty line
    lines = [l.strip() for l in completion.strip().split('\n') if l.strip()]
    return lines[-1] if lines else ""


# ============================================================
# STEP B: Calculate Accuracy
# ============================================================

def compute_accuracy(completion: str, ground_truth: str) -> float:
    """
    How accurate is the AI's answer?

    Returns:
        1.0 = Completely correct
        0.5 = Partially correct (correct drug name but incorrect dose)
        0.0 = Incorrect
    """
    completion_lower  = completion.lower()
    ground_truth_lower = ground_truth.lower()

    # Extract keywords from the ground truth
    # Example: "Acetaminophen 500mg" → ["acetaminophen", "500mg"]
    truth_words = ground_truth_lower.split()

    # Primary drug name (usually the first word)
    main_drug = truth_words[0] if truth_words else ""

    # Full match
    if ground_truth_lower in completion_lower:
        return 1.0

    # Drug name match (partial credit)
    if main_drug and main_drug in completion_lower:
        return 0.5

    # No match
    return 0.0


# ============================================================
# STEP C: Final Safety-Aware Reward
# ============================================================

def safety_aware_reward(completion: str,
                        ground_truth: str,
                        patient_context: str,
                        lambda_val: float = 0.5) -> float:
    """
    The core formula from the paper:
    Reward = Accuracy - (lambda × Safety_Penalty)

    Parameters:
        completion      : Full AI response
        ground_truth    : Correct answer
        patient_context : Patient information
        lambda_val      : Safety weight (0.1=lenient, 2.0=strict)

    Returns:
        float: Ranging from -1.0 to 1.0
                Higher is better
                Lower/negative is worse
    """

    # --- ACCURACY COMPONENT ---
    accuracy = compute_accuracy(completion, ground_truth)

    # --- SAFETY PENALTY COMPONENT ---
    tool_sequence = extract_tool_calls(completion)

    if not tool_sequence:
        # No tool calls — only accuracy is considered
        # However, not using tools for high-risk patients is itself unsafe
        from training.safety_checker import detect_patient_risks
        risks = detect_patient_risks(patient_context)
        if risks:
            avg_penalty = 0.3  # Penalty for failing to use tools
        else:
            avg_penalty = 0.0
    else:
        # Calculate the penalty for each tool call
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

    # Clamp the reward between -1.0 and 1.0
    reward = max(reward, -1.0)
    reward = min(reward, 1.0)

    return reward


# ============================================================
# STEP D: Batch reward (used in training)
# ============================================================

def compute_batch_rewards(completions: list,
                          ground_truths: list,
                          patient_contexts: list,
                          lambda_val: float = 0.5) -> list:
    """
    Evaluate multiple completions at once
    This will be used during GRPO training
    """
    assert len(completions) == len(ground_truths) == len(patient_contexts), \
        "All lists must have the same length!"

    rewards = []
    for comp, truth, context in zip(completions, ground_truths,
                                    patient_contexts):
        r = safety_aware_reward(comp, truth, context, lambda_val)
        rewards.append(r)

    return rewards