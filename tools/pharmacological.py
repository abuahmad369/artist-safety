# tools/pharmacological.py

import sys
import os
import requests

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from tools.base import ToolResult
from tools.cache_client import client


# ============================================================
# TOOL 1: Contraindication Lookup
# ============================================================

class ContraindicationLookup:
    name = "contraindication_lookup"

    # manually known contraindications
    # The FDA API is not always accurate, so this backup database is maintained
    KNOWN_CONTRAINDICATIONS = {
        ("ibuprofen", "renal impairment"):     True,
        ("ibuprofen", "kidney disease"):        True,
        ("ibuprofen", "anticoagulation"):       True,
        ("ibuprofen", "warfarin"):              True,
        ("ibuprofen", "peptic ulcer"):          True,
        ("aspirin",   "renal impairment"):      True,
        ("aspirin",   "peptic ulcer"):          True,
        ("aspirin",   "children"):              True,
        ("metformin", "renal impairment"):      True,
        ("metformin", "kidney disease"):        True,
        ("naproxen",  "renal impairment"):      True,
        ("naproxen",  "anticoagulation"):       True,
        ("codeine",   "respiratory depression"): True,
    }

    def __call__(self, drug: str, condition: str) -> ToolResult:
        print(f"  → ContraindicationLookup: {drug} + {condition}")

        drug_lower      = drug.lower().strip()
        condition_lower = condition.lower().strip()

        # Step 1: Check the known database first
        for (d, c), is_contra in self.KNOWN_CONTRAINDICATIONS.items():
            if d in drug_lower and c in condition_lower:
                return ToolResult(
                    tool_name=self.name,
                    status="CONTRAINDICATED",
                    data={"drug": drug, "condition": condition},
                    reasoning=f"{drug} is contraindicated in patients with "
                              f"{condition}. This is a well-established "
                              f"clinical contraindication."
                )

        # Step 2: Attempt to use the FDA API
        try:
            data = client.get(
                "https://api.fda.gov/drug/label.json",
                params={"search": f'warnings:"{drug_lower}"', "limit": 1}
            )

            if "results" in data and data["results"]:
                result = data["results"][0]

                # Check all relevant warning fields
                all_text = ""
                for field in ["warnings_and_cautions", "warnings",
                              "contraindications", "boxed_warning",
                              "precautions"]:
                    if field in result and result[field]:
                        all_text += " ".join(result[field]) + " "

                if all_text:
                    # Check for condition keywords in the text
                    keywords = condition_lower.replace("-", " ").split()
                    found = any(kw in all_text.lower() for kw in keywords)

                    if found:
                        return ToolResult(
                            tool_name=self.name,
                            status="CONTRAINDICATED",
                            data={"drug": drug, "condition": condition},
                            reasoning=all_text[:300]
                        )

        except Exception as e:
            print(f"    FDA API error: {e}")

        # Step 3: Be cautious if no explicit data is found
        return ToolResult(
            tool_name=self.name,
            status="USE_WITH_CAUTION",
            data={"drug": drug, "condition": condition},
            reasoning=f"No explicit contraindication found for {drug} in "
                      f"{condition}, but always verify with clinical guidelines."
        )


# ============================================================
# TOOL 2: Drug Interaction Checker
# ============================================================

class DrugInteractionChecker:
    name = "drug_interaction_checker"

    # Backup for manually known interactions
    KNOWN_INTERACTIONS = {
        ("warfarin", "ibuprofen"):      ("HIGH",     "Ibuprofen increases bleeding risk with warfarin significantly."),
        ("warfarin", "aspirin"):         ("HIGH",     "Aspirin increases bleeding risk with warfarin."),
        ("warfarin", "naproxen"):        ("HIGH",     "Naproxen increases anticoagulant effect of warfarin."),
        ("warfarin", "acetaminophen"):   ("MODERATE", "Acetaminophen may mildly increase INR. Monitor closely."),
        ("warfarin", "paracetamol"):     ("MODERATE", "Paracetamol may mildly increase INR. Monitor closely."),
        ("metformin", "alcohol"):        ("HIGH",     "Alcohol increases risk of lactic acidosis with metformin."),
        ("digoxin",  "amiodarone"):      ("HIGH",     "Amiodarone increases digoxin levels significantly."),
        ("ssri",     "tramadol"):        ("HIGH",     "Risk of serotonin syndrome."),
    }

    def _get_rxcui(self, drug_name: str):
        """Retrieve the RxNorm ID from the drug name"""
        try:
            data = client.get(
                "https://rxnav.nlm.nih.gov/REST/rxcui.json",
                params={"name": drug_name}
            )
            ids = data.get("idGroup", {}).get("rxnormId", [])
            if ids:
                return ids[0]
        except Exception as e:
            print(f"    RxCUI lookup error: {e}")
        return None

    def _check_known(self, drug1: str, drug2: str):
        """Check the known interaction database"""
        d1 = drug1.lower().strip()
        d2 = drug2.lower().strip()

        for (a, b), (severity, reason) in self.KNOWN_INTERACTIONS.items():
            if (a in d1 and b in d2) or (a in d2 and b in d1):
                return severity, reason
        return None, None

    def __call__(self, drug1: str, drug2: str) -> ToolResult:
        print(f"  → DrugInteractionChecker: {drug1} + {drug2}")

        # Step 1: Check known database
        severity, reason = self._check_known(drug1, drug2)
        if severity:
            return ToolResult(
                tool_name=self.name,
                status=severity,
                data={"drug1": drug1, "drug2": drug2},
                reasoning=reason
            )

        # Step 2: Attempt to use RxNorm API
        try:
            cui1 = self._get_rxcui(drug1)
            cui2 = self._get_rxcui(drug2)

            print(f"    RxCUI: {drug1}={cui1}, {drug2}={cui2}")

            if cui1 and cui2:
                # Interaction endpoint — requesting in JSON format
                url = (f"https://rxnav.nlm.nih.gov/REST/interaction/"
                       f"interaction.json?rxcui={cui1}&sources=ONCHigh")

                resp = requests.get(url, timeout=10)

                if resp.status_code == 200 and resp.text.strip():
                    data = resp.json()
                    groups = data.get("interactionTypeGroup", [])

                    for group in groups:
                        for itype in group.get("interactionType", []):
                            for pair in itype.get("interactionPair", []):
                                # Verify if the second drug is present
                                concepts = pair.get("interactionConcept", [])
                                names = [
                                    c.get("minConceptItem", {})
                                     .get("name", "").lower()
                                    for c in concepts
                                ]
                                if any(drug2.lower() in n for n in names):
                                    sev = pair.get("severity", "MODERATE")
                                    desc = pair.get("description",
                                                    "Interaction found")
                                    return ToolResult(
                                        self.name,
                                        sev.upper(),
                                        {"drug1": drug1, "drug2": drug2},
                                        desc[:300]
                                    )

        except Exception as e:
            print(f"    RxNorm API error: {e}")

        # Step 3: If no data is found
        return ToolResult(
            tool_name=self.name,
            status="SAFE",
            data={"drug1": drug1, "drug2": drug2},
            reasoning=f"No known interaction found between {drug1} and "
                      f"{drug2} in available databases. Always verify clinically."
        )