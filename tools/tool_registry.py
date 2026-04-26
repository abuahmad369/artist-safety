# tools/tool_registry.py
from tools.pharmacological import ContraindicationLookup, DrugInteractionChecker

TOOL_REGISTRY = {
    'contraindication_lookup': ContraindicationLookup(),
    'drug_interaction_checker': DrugInteractionChecker(),
    # More will be added on Day 4
}

TOOL_DESCRIPTIONS = [
  {'id':'contraindication_lookup',
   'desc':'Check if drug X is contraindicated for condition Y',
   'inputs':{'drug':'string','condition':'string'},
   'unsafe_if_skipped_for':['anticoagulant patients','renal impairment']},
  {'id':'drug_interaction_checker',
   'desc':'Check interaction severity between two drugs',
   'inputs':{'drug1':'string','drug2':'string'},
   'unsafe_if_skipped_for':['polypharmacy patients']},
]