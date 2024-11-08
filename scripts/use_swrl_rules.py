from owlready2 import * 
from rdflib import Graph, URIRef,Literal
from simulate_scenario import load_ontology, search_class_ontology,check_property,create_new_rdf
from simulate_scenario import create_individual, linking_to_HRM,target_property_checking, define_unresponsivness_rules
from simulate_scenario import save_rules_into_ontology, syncrhonize_ontology, define_fatigue_rules, define_attention_rules
from simulate_scenario import define_respiratory_rate_rules, define_heart_rate_rules,define_heart_rate_variability_rules,define_blood_saturation_rules
import pdb  
import uuid 


ontology_path = "../ontologies/"
file = "ConnectingInCabin.rdf"
onto = load_ontology(ontology_path + file) 

# get classes 
Actor = search_class_ontology(onto.classes(), "Actor")
Vehicle = search_class_ontology(onto.classes(), "Vehicle")

# Add values to properties we want to check. 
search_properties = ["hasAttentionLevels", "hasFatigueLevels",
                     "hasHeartRate", "hasHeartRateVariability",
                     "hasRespitoryRate", "hasAge", 
                     "hasUniqueIdentifier"]

#check if properties exist
individual_properties_values = dict()
for prop in search_properties: 
    individual_properties_values[prop] = check_property(onto, Actor, prop)
try: 
        
    #Define fatigue rules 
    define_fatigue_rules(onto)
    define_attention_rules(onto)
    define_unresponsivness_rules(onto)
    define_respiratory_rate_rules(onto) 
    define_heart_rate_rules(onto)
    define_heart_rate_variability_rules(onto)
    define_blood_saturation_rules(onto)

    #Save rules into anew ontology 
    new_ontology_name = save_rules_into_ontology(onto,directory=ontology_path,
                                                filename="InCabin_New_Rules.rdf")
except Exception as e:
    print(f"Error Saving Rules: {e}")
print("Saved the refined with rules ontology")

# #Create Individuals 
# driver_1 = Actor("John")
# occupant_1 = Actor("Mary")

# if any(individual_properties_values.values()):
#     for prop,value in individual_properties_values.items():
#         driver_1.prop = value
#         occupant_1.prop = value

# #Create a Thresholds Class 
# search_classes = ["RespitoryRateThreshold","FatigueLevelThreshold",
#                   "HeartRateThreshold","HeartRateVariabilityThreshold","AttentionLevelThreshold"]
# Thresholds_classes = {cls:search_class_ontology(onto.classes(), cls) for cls in search_classes}

# #Create Threshold Individuals 
# respitory_rate_threshold = Thresholds_classes["RespitoryRateThreshold"]("rp") if Thresholds_classes["RespitoryRateThreshold"] else None
# fatigue_level_threshold = Thresholds_classes["FatigueLevelThreshold"]("fl") if Thresholds_classes["FatigueLevelThreshold"] else None
# heart_rate_threshold = Thresholds_classes["HeartRateThreshold"]("hr") if Thresholds_classes["HeartRateThreshold"] else None
# heart_rate_variability_threshold = Thresholds_classes["HeartRateVariabilityThreshold"]("hrv") if Thresholds_classes["HeartRateVariabilityThreshold"] else None  
# attention_level_threshold = Thresholds_classes["AttentionLevelThreshold"]("al") if Thresholds_classes["AttentionLevelThreshold"] else None  

# #Set Initial Values 
# driver_1.hasID.append(str(uuid.uuid4()))
# occupant_1.hasID.append(str(uuid.uuid4()))
# driver_1.hasAge.append(25)
# occupant_1.hasAge.append(25.0)
# driver_1.hasFatigueLevels.append(60.0)
# occupant_1.hasFatigueLevels.append(90.0)
# driver_1.hasHeartRate.append(160.0)
# occupant_1.hasHeartRate.append(110.0)
# driver_1.hasHeartRateVariability.append(60.0)
# occupant_1.hasHeartRateVariability.append(70.0)
# driver_1.hasRespitoryRate.append(18.0)
# occupant_1.hasRespitoryRate.append(25.0)
# driver_1.hasAttentionLevels.append(1.0)
# occupant_1.hasAttentionLevels.append(1.0)

