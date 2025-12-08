from owlready2 import *
import os

# --- Configuration ---
ONTOLOGY_FILE = "assets/ontologies/snapshot_after_inference.owl"

try: 
    onto = get_ontology(f"file://{os.path.abspath(ONTOLOGY_FILE)}").load() 

except Exception as e: 
    raise Exception(f"Failed to load ontology from path: {ONTOLOGY_FILE}..")
swrl_rule_count = len(list(onto.rules()))


print("--- SWRL Rule Count ---")
print(f"Total Number of SWRL Rules: {swrl_rule_count}")

print("\n--- SWRL Interpretation ---")
print(f"This count ({swrl_rule_count}) represents the number of axioms that require")
print("a separate rule engine (like a built-in SWRL engine or an external mapping)")
print("and contributes directly to the performance cost beyond standard DL reasoning.")
