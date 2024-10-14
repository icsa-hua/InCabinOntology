from simulate_scenario import load_ontology,search_class_ontology,check_property,create_new_rdf
from simulate_scenario import create_individual, linking_to_HRM,target_property_checking
from simulate_scenario import add_value_to_property, associate_target_class, get_all_target_properties
from simulate_scenario import add_target_to_graph, add_data, plot_results, plot_pie_chart
from rdflib import URIRef
import pdb


ontology_path = "../ontologies/ConnectingInCabin.rdf"
ontology = [] 

#load ontology 
try:
    ontology = load_ontology(ontology_path)

    print("Ontology Loaded Successfully")

except Exception as e:
    print(f"Error Loading Ontology: {e}")

TargetClass =  search_class_ontology(ontology.classes(), "Target")

#Check if a specified property exists in the ontology 
ind_property= check_property(ontology, TargetClass,"measureOxygenSaturation" )
print(f"Property Checked {ind_property._name}")

#Create Individual 
try:
    spo2_level = 85
    new_individual = create_individual(ontology, TargetClass, ind_property,spo2_level)
except Exception as e:
    print(f"Error Creating Individual: {e}")

print(f"New indiividual created: {new_individual}")

# Link the new individual to another individual 
linking_to_HRM(ontology,"HeartRateMonitor", new_individual)

#Check properties of the new individuals 

target_property_checking(ontology, "target_A","isDizzy",85)

add_value_to_property(new_individual, "measureHeartRateLevels", 110)

#Associate target class to the new individual
target_class, property_value = associate_target_class(ontology, "Vehicle",new_individual,"VehicleHasTarget")

#Search target individual and get all target properties
get_all_target_properties(ontology, "target_A")

# Add target as an instance of Target Class 
target_A = URIRef("http://test.org/vehicleOntology#target_A")
target_class = URIRef("http://test.org/vehicleOntology#Target")
target_name = "Target A"
property_uri = URIRef("http://test.org/vehicleOntology#hasName")
graph, target_A = create_new_rdf(target_A, target_class, property_uri, target_name)

#Add two new targets and link them with each other. (Fixed values)
property_names = ['hasName', 'monitors', 'hasCondition']
graph = add_target_to_graph(graph, target_A, property_names,"Target" )
print("Successfully added target to graph")


#Add Data 
data_path = "../data/data_SAT_20240603.csv"
results = add_data(data_path)
plot_results(results)
plot_pie_chart(results)