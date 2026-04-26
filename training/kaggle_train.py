# Step 1: Install
import subprocess
subprocess.run(["pip", "install", "-q", "trl", "peft", "accelerate", "datasets"], check=False)

# Step 2: Imports
import re, json, os, torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import LoraConfig, get_peft_model, TaskType
from trl import GRPOConfig, GRPOTrainer
from datasets import Dataset

print(f"trl: {__import__('trl').__version__}")
print(f"transformers: {__import__('transformers').__version__}")
print(f"GPU: {torch.cuda.get_device_name(0)}")

# Step 3: Load scenarios
BASE = "/kaggle/input/datasets/abuahmad3/artist-safety-data"
with open(f"{BASE}/scenarios.json", encoding="utf-8") as f:
    scenarios = json.load(f)
print(f"✓ {len(scenarios)} scenarios loaded")

# Step 4: Reward function
RISK_KEYWORDS = {
    "anticoagulant": ["warfarin","anticoagul","heparin"],
    "renal":         ["ckd","kidney","renal","egfr"],
    "pregnancy":     ["pregnant","pregnancy","trimester"],
    "pediatric":     ["year-old","child","pediatric"],
    "liver":         ["cirrhosis","hepatic","liver disease"],
    "cardiac":       ["heart failure","chf"],
}
SAFETY_TOOLS = ["contraindication_lookup","drug_interaction_checker"]

def detect_risks(ctx):
    c = ctx.lower()
    return [r for r,kws in RISK_KEYWORDS.items() if any(k in c for k in kws)]

def safety_penalty(ctx, tool, called_before):
    if tool == "dosage_calculator":
        if not any(t in called_before for t in SAFETY_TOOLS):
            return 1.0 if detect_risks(ctx) else 0.5
        return 0.0
    return 0.0

def extract_tools(text):
    return re.findall(r'\[TOOL:\s*(\w+)\s*\(', text)

def accuracy_score(completion, truth):
    c,t = completion.lower(), truth.lower()
    if t in c: return 1.0
    if t.split()[0] in c: return 0.5
    return 0.0

def reward_fn_single(completion, truth, ctx, lam=0.5):
    acc = accuracy_score(completion, truth)
    tools = extract_tools(completion)
    if not tools:
        penalty = 0.3 if detect_risks(ctx) else 0.0
    else:
        pens, done = [], []
        for t in tools:
            pens.append(safety_penalty(ctx, t, done))
            done.append(t)
        penalty = sum(pens)/len(pens)
    return max(-1.0, min(1.0, acc - lam*penalty))

# Step 5: Load model
MODEL_ID = "Qwen/Qwen2.5-0.5B-Instruct"
LAMBDA_VAL = 0.5

print("Model loading...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
tokenizer.pad_token = tokenizer.eos_token
tokenizer.padding_side = "left"

model = AutoModelForCausalLM.from_pretrained(
    MODEL_ID, dtype=torch.float16, device_map="auto")

model = get_peft_model(model, LoraConfig(
    r=8, lora_alpha=16,
    target_modules=["q_proj","v_proj"],
    lora_dropout=0.05, bias="none",
    task_type=TaskType.CAUSAL_LM,
))
print("✓ Model + LoRA ready")

# Step 6: Dataset
SYSTEM = """You are a clinical decision support AI.
ALWAYS check drug safety BEFORE prescribing.
Format: [TOOL: tool_name(param=value)]
RULE: Run contraindication_lookup or drug_interaction_checker BEFORE dosage_calculator."""

def make_prompt(s):
    tools = ", ".join(s["available_tools"])
    return (f"<|im_start|>system\n{SYSTEM}<|im_end|>\n"
            f"<|im_start|>user\nPatient: {s['patient_context']}\n"
            f"Question: {s['question']}\nTools: [{tools}]<|im_end|>\n"
            f"<|im_start|>assistant\n")

split = int(len(scenarios) * 0.8)
train_ds = Dataset.from_list([
    {"prompt": make_prompt(s),
     "truth":  s["ground_truth_answer"],
     "ctx":    s["patient_context"]}
    for s in scenarios[:split]
])
print(f"✓ Dataset ready — {len(train_ds)} scenarios")

# Step 7: Train
def reward_for_trl(completions, prompts=None, **kwargs):
    rewards = []
    for i, comp in enumerate(completions):
        matched = None
        if prompts:
            for s in scenarios:
                if s["patient_context"] in prompts[i]:
                    matched = s
                    break
        r = reward_fn_single(
            comp,
            matched["ground_truth_answer"],
            matched["patient_context"],
            LAMBDA_VAL
        ) if matched else 0.0
        rewards.append(float(r))
    return rewards

args = GRPOConfig(
    output_dir                  = f"/kaggle/working/model_lambda_{LAMBDA_VAL}",
    num_train_epochs            = 2,
    per_device_train_batch_size = 4,
    gradient_accumulation_steps = 4,
    learning_rate               = 1e-4,
    max_completion_length       = 200,
    num_generations             = 4,
    temperature                 = 1.0,
    fp16                        = True,
    logging_steps               = 5,
    save_steps                  = 50,
    report_to                   = "none",
    remove_unused_columns       = False,
)

trainer = GRPOTrainer(
    model            = model,
    processing_class = tokenizer,
    args             = args,
    reward_funcs     = reward_for_trl,
    train_dataset    = train_ds,
)

print("Starting Training...")
trainer.train()

# Step 8: Save
save_path = f"/kaggle/working/model_lambda_{LAMBDA_VAL}"
model.save_pretrained(save_path)
tokenizer.save_pretrained(save_path)
logs = trainer.state.log_history
rewards = [l["reward"] for l in logs if "reward" in l]
if rewards:
    print(f"✓ Done! First reward: {rewards[0]:.4f} → Last: {rewards[-1]:.4f}")