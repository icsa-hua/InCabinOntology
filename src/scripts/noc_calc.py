# NOC (Number of Children) -> The number of direct subclasses from the class up the root class 
import os 

from owlready2 import * 

ONTOLOGY_FILE = "assets/ontologies/snapshot_after_inference.owl"

try: 
    onto = get_ontology(f"file://{os.path.abspath(ONTOLOGY_FILE)}").load() 

except Exception as e: 
    raise Exception(f"Failed to load ontology from path: {ONTOLOGY_FILE}..")


print(f"Ontology '{onto.base_iri}' loaded successfully")

def calculate_noc(cls):
    """Calculates the Number of Children (direct subclasses) for a given class."""
    # Using 'World.get_children_of()' to find direct subclasses
    # We must filter out non-class objects if the generator returns them
    direct_subclasses = [c for c in cls.subclasses() if isinstance(c, type)]
    return len(direct_subclasses)

noc_values = {} 

for cls in onto.classes() : 
    if cls.namespace == onto: 
        noc_values[cls.name] = calculate_noc(cls)

max_noc = max(noc_values.values()) if noc_values else 0
avg_noc = sum(noc_values.values()) / len(noc_values) if noc_values else 0
print(f"Max NOC (Widest Hierarchy Node): {max_noc}")
print(f"Avg NOC: {avg_noc:.2f}")
