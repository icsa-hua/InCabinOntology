# DIT (Depth of Inheritance Tree) -> The maximum number of superclasses from the class up to the root 
# class (owl:Thing)

import os 

from owlready2 import * 

# ONTOLOGY_FILE = "assets/ontologies/in_cabin_ontology.owl"
# ONTOLOGY_FILE = "assets/ontologies/snapshot_after_rules_pre_inference.owl"
ONTOLOGY_FILE = "assets/ontologies/snapshot_after_inference.owl"



try: 
    onto = get_ontology(f"file://{os.path.abspath(ONTOLOGY_FILE)}").load() 

except Exception as e: 
    raise Exception(f"Failed to load ontology from path: {ONTOLOGY_FILE}..")


print(f"Ontology '{onto.base_iri}' loaded successfully")

def calculate_dit(cls):

    if cls == Thing: 
        # Base case: owl:Thing is the root (DIT = 1, or 0 depending on convention)
        # We will use the convention where the root is level 1, direct subclass is level 2.
        return 1 


    superclasses = [c for c in cls.is_a if isinstance(c, type) and c != Thing] 

    if not superclasses: 
        # If no superclass other than Thing is found, DIT is 2 (e.g., Car is_a Thing)
        return 2


    return 1 + max(calculate_dit(sc) for sc in superclasses)

dit_values = {} 

for cls in onto.classes() : 
    if cls.namespace == onto: 
        dit_values[cls.name] = calculate_dit(cls)


max_dit = max(dit_values.values()) if dit_values else 0
avg_dit = sum(dit_values.values()) / len(dit_values) if dit_values else 0
print(f"Total Named Classes Analyzed: {len(dit_values)}")
print(f"Max DIT (Deepest Hierarchy): {max_dit}")
print(f"Avg DIT: {avg_dit:.2f}")
