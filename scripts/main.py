from simulate_scenario import load_ontology,search_class_ontology,check_property,create_new_rdf
from simulate_scenario import create_individual, linking_to_HRM,target_property_checking
from simulate_scenario import add_value_to_property, associate_target_class, get_all_target_properties
from simulate_scenario import add_target_to_graph, add_data, plot_results, plot_pie_chart
from synthetic_data_generator import SyntheticDataGenerator
from rdflib import URIRef
import pdb
import pandas as pd 

ontology_path = "../ontologies/ConnectingInCabin.rdf"
ontology = [] 

#load ontology 
try:
    ontology = load_ontology(ontology_path)

    print("Ontology Loaded Successfully")

except Exception as e:
    print(f"Error Loading Ontology: {e}")

# TargetClass =  search_class_ontology(ontology.classes(), "Target")

# #Check if a specified property exists in the ontology 
# ind_property= check_property(ontology, TargetClass,"measureOxygenSaturation" )
# print(f"Property Checked {ind_property._name}")

# #Create Individual 
# try:
#     spo2_level = 85
#     new_individual = create_individual(ontology, TargetClass, ind_property,spo2_level)
# except Exception as e:
#     print(f"Error Creating Individual: {e}")

# print(f"New indiividual created: {new_individual}")

# # Link the new individual to another individual 
# linking_to_HRM(ontology,"HeartRateMonitor", new_individual)

# #Check properties of the new individuals 

# target_property_checking(ontology, "target_A","isDizzy",85)

# add_value_to_property(new_individual, "measureHeartRateLevels", 110)

# #Associate target class to the new individual
# target_class, property_value = associate_target_class(ontology, "Vehicle",new_individual,"VehicleHasTarget")

# #Search target individual and get all target properties
# get_all_target_properties(ontology, "target_A")

# # Add target as an instance of Target Class 
# target_A = URIRef("http://test.org/vehicleOntology#target_A")
# target_class = URIRef("http://test.org/vehicleOntology#Target")
# target_name = "Target A"
# property_uri = URIRef("http://test.org/vehicleOntology#hasName")
# graph, target_A = create_new_rdf(target_A, target_class, property_uri, target_name)

# #Add two new targets and link them with each other. (Fixed values)
# property_names = ['hasName', 'monitors', 'hasCondition']
# graph = add_target_to_graph(graph, target_A, property_names,"Target" )
# print("Successfully added target to graph")


# #Add Data 
# data_path = "../data/data_SAT_20240603.csv"
# results = add_data(data_path)
# plot_results(results)
# plot_pie_chart(results)

# Generating Synthetic Data 
# Create syntehtic data for 100 samples 
data_generator = SyntheticDataGenerator(1000) 
# Example: Respiratory rate for adults
adult_resp_rate_data = data_generator.generate_resp_rate_by_age("adults")
print("Synthetic Respiratory Rate Data for Adults:", adult_resp_rate_data)

# Example: Heart rate data for a 40-year-old
heart_rate_data_40 = data_generator.generate_heart_rate_by_age(40)
print("Synthetic Heart Rate Data for 40-year-olds:", heart_rate_data_40)

# Example: Heart rate variability (HRV) data for a 25-year-old
hrv_data_25 = data_generator.generate_hrv_by_age(40)
print("Synthetic HRV Data for 25-year-olds:", hrv_data_25)

# Generate and print attention levels
attention_levels = data_generator.generate_attention_levels()
print("Attention Levels:", attention_levels)

# Generate and print blood saturation levels
blood_saturation_levels = data_generator.generate_blood_saturation_levels()
print("Blood Saturation Levels:", blood_saturation_levels)

# Example: Simulate fatigue levels
faid_scores, fast_scores, fatigue_levels = data_generator.simulate_fatigue()
print("FAID Scores:", faid_scores)
print("FAST Scores:", fast_scores)
print("Fatigue Levels:", fatigue_levels)

# driver state
driver_states = data_generator.simulate_driver_state()
print("Simulated Driver States:", driver_states)

# Generate timestamps
timestamps = data_generator.generate_timestamps() 
print("Generated Timestamps:", timestamps)

# Generate a column for age 
age_column = [40] * len(timestamps)


df = pd.DataFrame({
    'Timestamp': timestamps,
    'Age': age_column,
    'HeartRate': heart_rate_data_40,
    'RespiratoryRate': adult_resp_rate_data,
    'AttentionLevel': attention_levels,
    'BloodSaturation': blood_saturation_levels,
    'FatigueLevel': fatigue_levels,
    'DriverState': driver_states
})

df.set_index('Timestamp', drop=True)
# Save the DataFrame to a CSV file
df.to_csv('../data/synthetic_data.csv', index=False)
pdb.set_trace()





