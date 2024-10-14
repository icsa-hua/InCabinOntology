from owlready2 import * 
from rdflib import Graph, URIRef,Literal
import pandas as pd 
import matplotlib.pyplot as plt 
import seaborn as sns 
import pdb 

spo2_level = 85 

# Load Ontology 
def load_ontology(ontology_path): 
    ontology = get_ontology(ontology_path).load()

    #Check that ontology wa loaded correctly. 
    print("Ontology Classes: ")

    for cls in ontology.classes():
        print(cls)

    return ontology 


def search_class_ontology(target_classes, target_class_name):

    # Search if the Target class ("Target" in ths case) exists in the ontology

    TargetClass = None 
    for cls in target_classes: 
        if cls.name == "Target" : 
            TargetClass = cls 
            break 

    return TargetClass


# Check if a property 
def check_property(ontology,target_class, property_name): 
    with ontology: 
        # Define the property if it does not exist
        if not hasattr(target_class, property_name): 
            Property_Class = type(property_name, (DataProperty,),
                                  {'__init__':lambda self: (super(Property_Class, self).__init__(), print(f"{property_name} initialized"))
            })

            Property_Class.domain = [target_class]
            Property_Class.range = [float]

            ontology.property_name = Property_Class #Add it to the 
        
    return ontology.property_name
    

def create_individual(ontology, target_class, property_name,value,threshold=90):
    with ontology: 
        targetA = target_class("target_A")
        targetA.measureHeartRateLevels.append(110)

        if not hasattr(targetA, property_name._name):
            targetA.measureOxygenSaturation = [] 
            targetA.measureOxygenSaturation.append(value)
        else:
            property_value = getattr(targetA, property_name._name)
            property_value.append(value)
        
        
        if value <threshold: 
            targetA.isDizzy.append(True) 
            print(targetA.isDizzy) 
        else: 
            targetA.isDizzy.append(False)
            print(targetA.isDizzy)
        
    return targetA


def linking_to_HRM(ontology, cls_name="HeartRateMonitor", link_target=None):
    HeartRateMonitor_ind = []
    with ontology:
        heart_Rate_monitor_classes = [cls for cls in ontology.classes() if cls_name in cls.name]
        if heart_Rate_monitor_classes: 
            HeartRateMonitorClass = heart_Rate_monitor_classes[0]
            HeartRateMonitor_ind = HeartRateMonitorClass("hr_monitor_1")
            HeartRateMonitor_ind.captureNumericalData = [link_target] 
            print(f"Created individual: {HeartRateMonitor_ind}")
        else: 
            print("Class not Found")

    return HeartRateMonitor_ind   




def target_property_checking(ontology, target_name=None, prop_to_check=None,value=None, threshold=90): 

    try: 
        target_A_individual = ontology.target_A if hasattr(ontology, target_name) else None
        if target_A_individual is not None:
            property_value = getattr(target_A_individual, prop_to_check)
            
            print("Target A Individual Found")

            # if 'spo2_levels' in locals() and value < threshold: 
            if value is not None and value < threshold:
                property_value.append(True)
            else:
                property_value.append(False)
    except Exception as e: 
        print(f"Error: {e}")


def add_value_to_property(target_ind, property, value):     
    if hasattr(target_ind, property):
        property_value = getattr(target_ind, property)
    else: 
        property_value = [] 

    property_value.append(value)
    print(property_value)



def update_property(target, property_name, value): 
    if hasattr(target, property_name): 
        property_value = getattr(target, property_name)
        property_value.append(value)
    else: 
        add_data

def associate_target_class(ontology,target_class_name, target_ind, property_name ): 
    target_classes = [cls for cls in ontology.classes() if target_class_name in cls.name]

    if target_classes:
        target_class = target_classes[0]
        Target_Class = target_class("my_individual")
        property_value = getattr(Target_Class, property_name)
        property_value = [target_ind]
        print(f"Created individual: {Target_Class}, linked to target: {target_ind}")
        return Target_Class, property_value
    else: 
        print("Vehicle class not found")



def get_all_target_properties(ontology, target_name): 
    target_individual = ontology.search(iri="*" + target_name)[0]
    for prop in target_individual.get_properties(): 
        print(prop)


def create_new_rdf(target_ind_uri,target_class, property_uri, target_name_class): 
    
    # Create an RDF graph
    g = Graph()

    # Add target as an instance of Target Class 
    target_A = URIRef(target_ind_uri)
    g.add((target_A, URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"), URIRef(target_class)))
    g.add((target_A, URIRef(property_uri), Literal(target_name_class)))

    # Verify by querying instances of Target class
    query_instances = """
    SELECT ?target
    WHERE {{
        ?target a <{0}> .
    }}
    """.format(target_class)

    results_instances = g.query(query_instances)

    print("\nInstances of Target Class:")
    if results_instances:
        for row in results_instances:
            target_name = row.target.split('#')[-1]
            print(f"Target: {target_name}")

    query_properties(g, target_ind_uri)    
    query_all_targets(g, target_class, property_uri)

    return g, target_A


def query_properties(graph, target_uri): 
    # Query to get all properties of target_A
    query_properties = """
    SELECT ?p ?o
    WHERE {{
        <{0}> ?p ?o.
    }}""".format(target_uri)

    results_properties = graph.query(query_properties)
    if results_properties:
        print("\nProperties of target_A from RDF:")
        for result in results_properties:
            predicate = result['p'].split('#')[-1]  # Extracting the property name
            object_value = result['o'].split('#')[-1] if isinstance(result['o'], URIRef) else result['o']
            print(f"{predicate}: {object_value}")


def query_all_targets(graph, target_class, property_uri): 
    # Example query to retrieve all targets and their names
    query = """
    SELECT ?target ?name
    WHERE {{
        ?target a <{0}> .
        ?target <{1}> ?name .
    }}
    """.format(target_class, property_uri)
    results = graph.query(query)

    print("\nAll Targets and Their Names:")
    for row in results:
        print(f"Target: {row.target}, Name: {row.name}")


def add_target_to_graph(graph, target_A, property_names, target_class):
    
    # Example: Add two new targets
    target_class_uri = f"http://test.org/vehicleOntology#{target_class}"
    properties_uri = [f"http://test.org/vehicleOntology#{prop}" for prop in property_names]
    rdf_uri = "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"
    
    target_B = URIRef("http://test.org/vehicleOntology#target_B")
    graph.add((target_B, URIRef(rdf_uri), URIRef(target_class_uri)))
    graph.add((target_B, URIRef(properties_uri[0]), Literal("Target B")))

    # Example of adding another target and linking it
    target_C = URIRef("http://test.org/vehicleOntology#target_C")
    graph.add((target_C, URIRef(rdf_uri), URIRef(target_class_uri)))
    graph.add((target_C, URIRef(properties_uri[0]), Literal("Target C")))
    graph.add((target_B, URIRef(properties_uri[1]), target_C))

    # Add a monitoring relationship between target_A and target_B
    graph.add((target_A, URIRef(properties_uri[1]), target_B))

    # Set a condition for target_B
    graph.add((target_B, URIRef(properties_uri[2]), Literal("Active")))
    query_all_targets(graph, target_class, properties_uri[0])
    verify_properties(graph,target_class_uri,properties_uri)

    return graph


def verify_properties(graph,target_class_uri,properties_uri):
    # Verify the properties again
    query_all_details = """
    SELECT ?target ?name ?condition ?monitors
    WHERE {{
            ?target a <{0}> .
            OPTIONAL {{ ?target <{1}> ?name . }}
            OPTIONAL {{ ?target <{3}> ?condition . }}
            OPTIONAL {{ ?target <{2}> ?monitors . }}
        }}
    """.format(target_class_uri, properties_uri[0], properties_uri[1], properties_uri[2])

    results_all_details = graph.query(query_all_details)

    print("\nDetails of All Targets and Their Connections After Updates:")
    for row in results_all_details:
        target_name = row.target.split('#')[-1]
        name = row.name if row.name else "N/A"
        condition = row.condition if row.condition else "N/A"
        monitors = row.monitors.split('#')[-1] if row.monitors else "None"
        print(f"Target: {target_name}, Name: {name}, Condition: {condition}, Monitors: {monitors}")


# Define fatigue states from the document UC1_In-cabin_sensing_data_list_V2 # Undefined because we don't have a column for it
def determine_fatigue_state(fatigue_level):
    fatigue_states = {
        0: "UNDEFINED_FATIGUE_LEVEL",
        1: "AWAKE",
        2: "DROWSINESS_SUSPECTED",
        3: "DROWSY",
        4: "SLEEP",
        5: "MICROSLEEP"
    }
    return fatigue_states.get(fatigue_level, "UNKNOWN")


# Define attention states from the document UC1_In-cabin_sensing_data_list_V2 # Undefined because we don't have a column for it
def determine_attention_state(attention_level):
    attention_states = {
        0: "UNDEFINED_ATTENTION_STATE",
        1: "ATTENTIVE",
        2: "INATTENTIVE",
        3: "ATTENTION_INCREASING",
        4: "ATTENTION_DECREASING"
    }
    return attention_states.get(attention_level, "UNKNOWN")


# Define unresponsive person detection states # Undefined because we don't have a column for it
def determine_unresponsive_state(state):
    unresponsive_states = {
        0: "UNDEFINED_UNRESPONSIVE_STATE",
        1: "NO_PERSON",
        2: "RESPONSIVE",
        3: "SHORT_DISTRACTION",
        4: "LONG_DISTRACTION",
        5: "NOT_RESPONSIVE"
    }
    return unresponsive_states.get(state, "UNKNOWN")


def determine_condition(heart_rate, spo2, rr):
    if heart_rate > 100:
        condition_hr = "High"
    elif heart_rate < 60:
        condition_hr = "Low"
    else:
        condition_hr = "Normal"

    if spo2 < 90:
        condition_spo2 = "Critical"
    elif 90 <= spo2 <= 95:
        condition_spo2 = "Low"
    else:
        condition_spo2 = "Normal"

    if rr > 20:
        condition_rr = "High"
    elif rr < 12:
        condition_rr = "Low"
    else:
        condition_rr = "Normal"

    # You can return a composite condition or individual conditions
    return condition_hr, condition_spo2, condition_rr


def query_all_details(graph):
    # SPARQL query to retrieve all targets and their full details, including new parameters
    query_all_details = """
    SELECT ?target ?name ?conditionHR ?conditionSPO2 ?conditionRR ?fatigueLevel ?attentionState ?unresponsiveState
    WHERE {
        ?target a <http://test.org/vehicleOntology#Target> .
        ?target <http://test.org/vehicleOntology#hasName> ?name .
        OPTIONAL { ?target <http://test.org/vehicleOntology#hasConditionHR> ?conditionHR . }
        OPTIONAL { ?target <http://test.org/vehicleOntology#hasConditionSPO2> ?conditionSPO2 . }
        OPTIONAL { ?target <http://test.org/vehicleOntology#hasConditionRR> ?conditionRR . }
        OPTIONAL { ?target <http://test.org/vehicleOntology#fatigueLevel> ?fatigueLevel . }
        OPTIONAL { ?target <http://test.org/vehicleOntology#attentionState> ?attentionState . }
        OPTIONAL { ?target <http://test.org/vehicleOntology#unresponsiveState> ?unresponsiveState . }
    }
    """
    # Execute the SPARQL query and print all details
    results_all_details = graph.query(query_all_details)

    print("\nDetails of All Targets and Their Full Parameters:")
    for row in results_all_details:
        target_name = row.target.split('#')[-1]
        print(f"Target: {target_name}, Name: {row.name}, Condition HR: {row.conditionHR}, Condition SPO2: {row.conditionSPO2}, Condition RR: {row.conditionRR}, "
            f"Fatigue: {row.fatigueLevel}, Attention: {row.attentionState}, Unresponsive: {row.unresponsiveState}")


def add_data(path):
    
    # Load SAT data from a CSV file
    sat_data = pd.read_csv(path)
    processed_data = []
    g = Graph() 

    for index, row in sat_data.iterrows():
        target_name = f"target_{index+1}"
        
        heart_rate = row['HR']
        spo2 = row['SPO2']
        rr = row['RR']
        condition = "Normal"

        # Get Additional parameters if present 
        fatigue_level = row.get("FatigueLevel", 0)
        attention_level = row.get("AttentionState", 0)
        unresponsive_state = row.get("UnresponsiveState", 0)

        # Determine conditions based on parameters 
        condition_hr, condition_spo2, condition_rr = determine_condition(heart_rate, spo2, rr)
        fatigue_state = determine_fatigue_state(fatigue_level)
        attention_state = determine_attention_state(attention_level)
        unresponsive_state = determine_unresponsive_state(unresponsive_state)

        # Store the processed data
        processed_data.append({
            'target_name': f"target_{index + 1}",
            'heart_rate': heart_rate,
            'condition_hr': condition_hr,
            'condition_spo2': condition_spo2,
            'condition_rr': condition_rr,
        })

        #create a new target URI and add to the graph 
        new_target_uri = URIRef(f"http://test.org/vehicleOntology#{target_name}")
        g.add((new_target_uri, URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"), URIRef("http://test.org/vehicleOntology#Target")))
        g.add((new_target_uri, URIRef("http://test.org/vehicleOntology#hasName"), Literal(target_name)))
        g.add((new_target_uri, URIRef("http://test.org/vehicleOntology#measureHeartRateLevels"), Literal(heart_rate)))
        g.add((new_target_uri, URIRef("http://test.org/vehicleOntology#hasConditionHR"), Literal(condition_hr)))
        g.add((new_target_uri, URIRef("http://test.org/vehicleOntology#hasConditionSPO2"), Literal(condition_spo2)))
        g.add((new_target_uri, URIRef("http://test.org/vehicleOntology#hasConditionRR"), Literal(condition_rr)))

        # Add the new parameters to the ontology
        g.add((new_target_uri, URIRef("http://test.org/vehicleOntology#fatigueLevel"), Literal(fatigue_state)))
        g.add((new_target_uri, URIRef("http://test.org/vehicleOntology#attentionState"), Literal(attention_state)))
        g.add((new_target_uri, URIRef("http://test.org/vehicleOntology#unresponsiveState"), Literal(unresponsive_state)))

    results_df = pd.DataFrame(processed_data)
    query_all_details(g)
    # Display the processed DataFrame
    print(results_df.head(20))
    return results_df

def plot_results(results_df): 
    # Limit to the first 20 targets for quicker visualization - because of the large size of dataset
    limited_df = results_df.head(20)
    
    plt.figure(figsize=(10, 6))
    plt.bar(limited_df['target_name'], limited_df['heart_rate'], color='blue')
    plt.title('Heart Rate Levels of Targets (Limited to First 20)')
    plt.xlabel('Target Name')
    plt.ylabel('Heart Rate (BPM)')
    plt.axhline(y=100, color='r', linestyle='--', label='High Threshold')
    plt.axhline(y=60, color='g', linestyle='--', label='Low Threshold')
    plt.legend()
    plt.xticks(rotation=45)  # Rotate x-axis labels for better visibility
    plt.tight_layout()  # Adjust layout to prevent clipping
    plt.show()


def plot_pie_chart(results_df):

    # Count the conditions
    condition_counts = results_df['condition_spo2'].value_counts()

    # Pie chart for conditions
    plt.figure(figsize=(8, 6))

    # Explode the slices for better visibility
    explode = [0.1] * len(condition_counts)  # Slightly separate all slices

    
    # Create the pie chart with improved aesthetics
    plt.pie(condition_counts,
            labels=condition_counts.index,
            autopct='%1.1f%%',
            startangle=90,
            explode=explode,
            shadow=True,
            colors=sns.color_palette("Set2", n_colors=len(condition_counts)),
            textprops={'fontsize': 12},  # Increase text size for better readability
            labeldistance=1.1)  # Adjust label distance
    
    # Example of custom explode values for better separation
    explode = [0.1, 0.1, 0.2]  # Adjust these values based on your specific slices

    plt.title('Distribution of SPO2 Conditions Among Targets', fontsize=16, fontweight='bold')  # Increase title font size and make it bold
    plt.axis('equal')  # Equal aspect ratio ensures that pie chart is circular
    plt.tight_layout()  # Automatically adjust subplot parameters to give specified padding
    plt.show()