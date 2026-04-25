# ARTIST Safety: Safety-Aware Reinforcement Learning for Agentic Tool Use in Clinical Decision Support

## Abstract

Large language models (LLMs) augmented with tool-calling capabilities show 
promise for clinical decision support, but existing frameworks optimize 
solely for answer accuracy without penalizing unsafe tool selection. We 
present ARTIST Safety, a safety-aware extension of reinforcement learning 
for agentic tool use in clinical settings. Our key contributions are: 
(1) a safety-aware reward function that penalizes unsafe tool calls using 
the formula Reward = Accuracy - lambda x Safety_Penalty, (2) a hierarchical 
medical tool taxonomy with 12 clinical tools grounded in OpenFDA, RxNorm, 
and LOINC APIs, and (3) MedQA-Tools, a benchmark of 100 clinical scenarios 
with safety annotations derived from USMLE-style questions. Training 
Qwen2.5-0.5B-Instruct with GRPO using our safety-aware reward improved 
Safety@5 from 0.0% to 98.3% (+98.3%) while improving accuracy from 10.0% 
to 35.0% on our benchmark. Our results demonstrate that explicit safety 
penalties in the reward function are critical for deploying agentic AI 
in high-stakes clinical environments.

---

## 1. Introduction

Medical errors cause approximately 250,000 deaths annually in the United 
States, representing the third leading cause of death (Makary & Daniel, 
2016). A significant portion of these errors stem from incorrect drug 
prescriptions, missed contraindications, and failure to check drug 
interactions before dosing.

Recent advances in LLM-based agentic frameworks, such as ARTIST (Microsoft, 
2025), demonstrate that language models can learn to autonomously select and 
invoke external tools to solve complex reasoning tasks. However, these 
frameworks are evaluated exclusively on mathematical and general 
function-calling benchmarks, where errors carry no real-world consequences.

We ask: what happens when such frameworks are deployed in clinical decision 
support? Consider a 68-year-old patient on warfarin with chronic kidney 
disease presenting with knee pain. An AI agent that calls dosage_calculator 
directly without first checking contraindications may recommend ibuprofen, 
which is contraindicated with warfarin and nephrotoxic in renal impairment. 
The answer may appear correct in format, yet the tool selection pathway 
is clinically dangerous.

Existing reward functions cannot distinguish between these two scenarios:
- Agent A: checks contraindication -> checks interaction -> calculates dose (SAFE)
- Agent B: directly calculates dose without safety checks (UNSAFE)

Both may produce the same final answer, yet only Agent A follows safe 
clinical practice.

We address this gap with three contributions:

1. Safety-Aware Reward Function: We extend the GRPO reward signal with 
an explicit safety penalty term, penalizing unsafe tool selection pathways 
in high-risk patient contexts.

2. Hierarchical Medical Tool Taxonomy: We implement 12 clinical tools 
organized by category (pharmacological, diagnostic, clinical reference) 
grounded in real medical APIs.

3. MedQA-Tools Benchmark: We construct 100 clinical scenarios with 
tool-level safety annotations for evaluating agentic clinical AI.

---

## 2. Background

### 2.1 Reinforcement Learning for LLMs

Reinforcement Learning from Human Feedback (RLHF) has become standard 
for aligning LLMs with human preferences. Recent work on Group Relative 
Policy Optimization (GRPO) eliminates the need for a separate critic 
network by using group-relative advantage estimation:

A_i = (r_i - mean(r)) / std(r)

where r_i is the reward for the i-th completion in a group of G completions. 
This approach is more memory-efficient than PPO and has shown strong 
results in mathematical reasoning (DeepSeek-R1) and tool use (ARTIST).

### 2.2 ARTIST Framework

ARTIST (Agentic Reasoning and Tool Integration in Self-improving 
Transformers) trains LLMs to autonomously invoke external tools using GRPO. 
The reward function is binary: +1 for correct final answers, 0 otherwise. 
This design is appropriate for mathematical benchmarks but inadequate for 
clinical settings where the tool selection pathway itself carries safety 
implications independent of the final answer.

### 2.3 Clinical Decision Support

Clinical decision support systems (CDSS) assist clinicians with drug 
prescribing, dosing, and interaction checking. Key safety requirements 
include contraindication checking before prescribing, drug interaction 
verification before combining medications, and dose adjustment for 
renal/hepatic impairment. Current AI-based CDSS do not explicitly 
train models to follow these safety-first tool selection patterns.

---

## 3. Method

### 3.1 Safety-Aware Reward Function

We extend the ARTIST reward function with an explicit safety penalty:

Reward = Accuracy - (lambda x Safety_Penalty)

where:
- Accuracy = 1.0 if ground truth answer is in completion, 0.5 for 
  partial match (correct drug, wrong dose), 0.0 otherwise
- Safety_Penalty = penalty for unsafe tool selection (0.0=safe, 
  0.5=caution, 1.0=unsafe)
- lambda = safety weight hyperparameter

Safety_Penalty is computed using a rule-based safety checker grounded 
in established clinical guidelines. For high-risk patients (anticoagulant 
therapy, renal impairment, pregnancy, pediatric, hepatic disease, cardiac 
failure), calling dosage_calculator without first invoking 
contraindication_lookup or drug_interaction_checker incurs maximum penalty 
(1.0). This design choice prioritizes interpretability over learned 
representations, a critical requirement in clinical AI systems.

We evaluate four values of lambda: {0.1, 0.5, 1.0, 2.0} and find that 
lambda=2.0 produces the best safety improvement while maintaining 
competitive accuracy.

### 3.2 Hierarchical Medical Tool Taxonomy

We implement 12 clinical tools organized in a three-level hierarchy:

Pharmacological:
  Drug Safety: contraindication_lookup, drug_interaction_checker
  Dosing: dosage_calculator, weight_adjusted_dose

Diagnostic:
  Lab Values: normal_range_lookup, critical_value_checker
  Imaging: imaging_guideline_lookup

Clinical Reference:
  Guidelines: guideline_lookup, risk_score_calculator
  Coding: icd10_code_lookup, cpt_code_lookup
  Patient: allergy_checker

Tools are grounded in real medical APIs: OpenFDA for drug warnings and 
contraindications, RxNorm (NIH) for drug interaction data, and LOINC 
for laboratory test reference ranges. All APIs are publicly available 
at no cost.

### 3.3 MedQA-Tools Benchmark

We construct MedQA-Tools, a benchmark of 100 clinical scenarios derived 
from USMLE-style pharmacology questions. Each scenario contains:

- patient_context: demographics, current medications, comorbidities
- question: clinical decision question
- correct_tool_path: ordered sequence of tool calls for safe resolution
- unsafe_tools_for_patient: tools that are dangerous for this patient
- ground_truth_answer: correct clinical answer
- safety_annotation: explanation of why certain tools are unsafe

Scenarios cover six high-risk patient categories: anticoagulant therapy 
(warfarin, heparin), renal impairment (CKD stages 1-5), pregnancy 
(all trimesters), pediatric patients, hepatic disease, and cardiac 
failure. The benchmark is released publicly on HuggingFace.

### 3.4 Training Setup

We train Qwen2.5-0.5B-Instruct using GRPO with our safety-aware reward 
function. Training details:

- Base model: Qwen2.5-0.5B-Instruct
- Fine-tuning: LoRA (r=8, alpha=16, target: q_proj, v_proj)
- Trainable parameters: 540,672 (0.11% of total)
- Batch size: 4, gradient accumulation: 4 (effective batch: 16)
- Learning rate: 1e-4 with warmup
- Generations per prompt: 4
- Epochs: 2
- Hardware: NVIDIA Tesla T4 (15GB VRAM), Kaggle free tier
- Training time: ~8 minutes per lambda value

---

## 4. Experiments

### 4.1 Evaluation Metrics

We evaluate on two primary metrics:

Accuracy: Proportion of test scenarios where the model produces the 
correct drug recommendation. Partial credit (0.5) is awarded for 
correct drug name with incorrect dose.

Safety@k: Our novel metric measuring the proportion of safe tool 
selections in the first k tool calls:

Safety@k = (safe tools in top-k) / k

where a tool is considered unsafe if it appears in the 
unsafe_tools_for_patient list for that scenario. We report Safety@5.

### 4.2 Baselines

We compare against one baseline:

Vanilla Qwen2.5-0.5B: The base model without any safety-aware training, 
evaluated zero-shot on our benchmark.

### 4.3 Results

Table 1: Main Results on MedQA-Tools Benchmark

| Model              | Accuracy | Safety@5 |
|--------------------|----------|----------|
| Vanilla (baseline) | 10.0%    | 0.0%     |
| Ours (lambda=2.0)  | 35.0%    | 98.3%    |
| Improvement        | +25.0%   | +98.3%   |

Our safety-aware reward function achieves 98.3% Safety@5 compared to 
0.0% for the untrained baseline, a improvement of +98.3 percentage points. 
Accuracy also improves from 10.0% to 35.0% (+25.0%), demonstrating that 
safety training does not sacrifice answer quality.

Table 2: Lambda Ablation Study

| Lambda | First Reward | Last Reward | Improvement |
|--------|-------------|-------------|-------------|
| 0.1    | -0.041      | +0.035      | +0.076      |
| 0.5    | +0.055      | +0.063      | +0.008      |
| 1.0    | +0.055      | +0.063      | +0.008      |
| 2.0    | +0.030      | +0.113      | +0.083      |

Lambda=2.0 shows the highest reward improvement (+0.083), indicating 
that stronger safety penalties produce better learning signals when 
training on clinical scenarios with high-risk patients.

---

## 5. Analysis

### 5.1 Why Safety@5 Improved Dramatically

The baseline model (0.0% Safety@5) never uses tool calls in its 
responses, defaulting to direct text answers without invoking any 
tools. This is expected for a zero-shot evaluation of a general-purpose 
model not trained for tool use.

Our trained model (98.3% Safety@5) learns to invoke safety tools 
(contraindication_lookup, drug_interaction_checker) before dosing tools, 
following the correct clinical pathway. This behavior emerges from the 
safety penalty in the reward function, which explicitly punishes skipping 
safety checks for high-risk patients.

### 5.2 Interpretability Advantage

Our rule-based safety checker provides full interpretability: every 
penalty can be traced to a specific clinical rule (e.g., "warfarin 
patients require contraindication check before NSAID dosing"). This 
contrasts with learned safety classifiers (e.g., BiomedBERT-based NLI) 
which function as black boxes. In clinical AI, interpretability is not 
optional — clinicians must understand why an AI recommendation was made.

### 5.3 Limitations

Dataset size: Our benchmark contains 100 scenarios. Larger evaluation 
sets (500+) would provide more robust estimates.

Model size: We evaluate Qwen2.5-0.5B due to compute constraints. 
Larger models (7B, 70B) may show different accuracy-safety tradeoffs.

Real API validation: Our safety checker uses rule-based logic with 
OpenFDA/RxNorm as backup. A prospective clinical validation study 
would strengthen the safety claims.

---

## 6. Conclusion

We presented ARTIST Safety, a safety-aware reinforcement learning 
framework for clinical tool use. Our safety-aware reward function 
(Reward = Accuracy - lambda x Safety_Penalty) improved Safety@5 from 
0.0% to 98.3% while improving accuracy from 10.0% to 35.0% on our 
MedQA-Tools benchmark. These results demonstrate that explicit safety 
penalties in the RL reward signal are critical for deploying agentic AI 
in clinical settings.

We release all code, datasets, and trained models publicly to facilitate 
reproducibility and future research in safe clinical AI.

---

## References

Makary MA, Daniel M. Medical error—the third leading cause of death 
in the US. BMJ. 2016;353:i2139.

Shao Z, et al. DeepSeekMath: Pushing the Limits of Mathematical 
Reasoning in Open Language Models. arXiv:2402.03300. 2024.

Wei J, et al. Chain-of-Thought Prompting Elicits Reasoning in Large 
Language Models. NeurIPS 2022.

Hu EJ, et al. LoRA: Low-Rank Adaptation of Large Language Models. 
ICLR 2022.

Jin D, et al. What Disease does this Patient Have? A Large-scale 
Open Domain Question Answering Dataset from Medical Exams. 
arXiv:2009.13081. 2020.

---

## Appendix: Example Scenario

Patient: 68F, warfarin 5mg/day, CKD stage 3, knee osteoarthritis
Question: What is the safest analgesic for this patient's knee pain?

Correct tool path:
  Step 1: contraindication_lookup(drug=ibuprofen, condition=anticoagulation)
          -> CONTRAINDICATED
  Step 2: drug_interaction_checker(drug1=warfarin, drug2=acetaminophen)
          -> MODERATE (use with monitoring)

Ground truth answer: Acetaminophen 500mg with INR monitoring

Safety annotation: NSAIDs contraindicated with warfarin due to bleeding 
risk; ibuprofen also nephrotoxic in CKD stage 3.