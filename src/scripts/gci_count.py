import os 

from owlready2 import * 

ONTOLOGY_FILE = "assets/ontologies/snapshot_after_inference.owl"

try: 
    onto = get_ontology(f"file://{os.path.abspath(ONTOLOGY_FILE)}").load() 

except Exception as e: 
    raise Exception(f"Failed to load ontology from path: {ONTOLOGY_FILE}..")

gci_axioms = list(onto.general_class_axioms())
gci_count = len(gci_axioms)

print("\n--- GCI Count ---")
print(f"Total Number of General Concept Inclusion (GCI) Axioms: {gci_count}")

print("\n--- GCI Interpretation ---")
print(f"This count ({gci_count}) measures the number of complex definitional axioms.")
print("A high number of GCIs is a primary indicator of the complexity and high")
print("reasoning time required for TBox Classification in an OWL 2 DL ontology.")
