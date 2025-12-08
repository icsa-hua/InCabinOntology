import os
from unicodedata import name 

from owlready2 import * 

ONTOLOGY_FILE = "assets/ontologies/snapshot_after_inference.owl"

try: 
    onto = get_ontology(f"file://{os.path.abspath(ONTOLOGY_FILE)}").load() 

except Exception as e: 
    raise Exception(f"Failed to load ontology from path: {ONTOLOGY_FILE}..")



def calculate_rch(onto): 

    named_classes_count = 0 
    anonymous_expressions_count = 0 

    # Count Named classes 
    named_classes_count = len([cls for cls in onto.classes() if cls.namespace==onto])

    # Count Anonymous Expressions 
    def count_expressions_in_list(expressions): 
        """ 
            Recursive count expressions in list of superclasses/equivalents. 
        """

        count = 0 
        for expr in expressions: 
            if isinstance(expr, Restriction): 
                count += 1 

            elif isinstance(expr, And) or isinstance(expr, Or): 
                count += 1 
                count += count_expressions_in_list(expr.Classes)

        return count 

    for cls in onto.classes() : 

        if cls.namespace == onto:  

            # Count expressions under subclass axioms 
            anonymous_expressions_count += count_expressions_in_list(cls.is_a)

            # Count expressions in equivalent class axioms 
            anonymous_expressions_count += count_expressions_in_list(cls.equivalent_to)

            # Count expressions in disjoint union axioms 
            if hasattr(cls, 'disjoint_unions') and cls.disjoint_unions: 
                for du_list in cls.disjoint_unions: 
                    
                    # Count the Dosjoint Union construct 
                    anonymous_expressions_count += 1 

                    # Count expressions within the list 
                    anonymous_expressions_count += count_expressions_in_list(du_list)

    if named_classes_count == 0 : 
        return 0, 0, 0 

    rch = anonymous_expressions_count / named_classes_count 
    return rch, anonymous_expressions_count, named_classes_count


rch_value, total_expressions, total_classes = calculate_rch(onto)

print("\n--- Expression Richness Metric ---")
print(f"Total Named Classes: {total_classes}")
print(f"Total Anonymous Class Expressions (Restrictions, Intersections, Unions): {total_expressions}")
print(f"RCH (Expression Richness): {rch_value:.3f}")
print("A higher RCH value indicates more complex logical definitions per named class.")

