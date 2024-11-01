from owlready2 import * 
from rdflib import Graph, URIRef,Literal
import pandas as pd 
import matplotlib.pyplot as plt 
import seaborn as sns 
import pdb 
import os
import uuid

spo2_level = 85 

# Load Ontology 
def load_ontology(ontology_path): 
    ontology = get_ontology(ontology_path).load()

    #Check that ontology wa loaded correctly. 
    print("Ontology Classes: ")

    for cls in ontology.classes():
        print(cls)

    return ontology 


def search_class_ontology(target_classes,target_class_name ):

    # Search if the Target class ("Target" in ths case) exists in the ontology

    TargetClass = None 
    for cls in target_classes: 
        if cls.name == target_class_name : 
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
            print(f"Property {property_name} created...")
            ontology.property_name = Property_Class #Add it to the 
        
        else: 
            ontology.property_name = getattr(target_class, property_name)
            print(f"Property {property_name} found...")
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


def check_individual_property(ontology, target_individual, property_list ):
    
    property_values = [getattr(target_individual, prop) for prop in property_list]
    for prop in property_list: 
        if prop is None: 
            prop.append


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
        property_value = [value]
    else: 
        raise ValueError(f"Property {property_name} not found in target individual")


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


def define_fatigue_rules(ontology): 
    
    with ontology:   
        fatigue_undefined_1= Imp() 
        fatigue_undefined_1.set_as_rule(
            """hasFatigueLevels(?a, ?fl), lessThan(?fl,0) ->
            isUndefinedFatigueLevel(?a,true), noPersonFound(?v,true)"""
        )

        fatigue_undefined_2 = Imp()
        fatigue_undefined_2.set_as_rule(
            """
            hasFatigueLevels(?a, 0) -> 
            isUndefinedFatigueLevel(?a,true),
            noPersonFound(?v,true)
            """
        )

        not_fatigued = Imp() 
        not_fatigued.set_as_rule(
            """
            hasFatigueLevels(?a, ?fl),
            greaterThan(?fl,40), lessThan(?fl,50) ->
            isNotFatigued(?a,true), isAwake(?a,true)
            """
        )

        moderate_fatigue = Imp()
        moderate_fatigue.set_as_rule(
            """
            hasFatigueLevels(?a, ?fl),
            greaterThan(?fl,50), lessThan(?fl,60) ->
            isAwake(?a,true), isModeratelyFatigued(?a,true),
            """
        )

        very_fatigued = Imp()
        very_fatigued.set_as_rule(
            """
            hasFatigueLevels(?a, ?fl),
            greaterThan(?fl,60), lessThan(?fl,70) -> 
            isAwake(?a,true), isVeryFatigued(?a,true),
            isDrowsy(?a,true), hasDrowsinessState(?a,true),
            """
        )

        extremely_fatigued = Imp()
        extremely_fatigued.set_as_rule(
            """
            hasFatigueLevels(?a, ?fl),
            greaterThan(?fl,70), lessThan(?fl,80) -> 
            isExtremelyFatigued(?a,true), isAwake(?a,true),
            isDrowsy(?a,true), hasDrowsinessState(?a,true),
            """
        )

        severely_fatigued = Imp()
        severely_fatigued.set_as_rule(
            """
            hasFatigueLevels(?a, ?fl),
            greaterThan(?fl,80), lessThan(?fl,90) ->
            isAwake(?a,true), isSeverelyFatigued(?a,true), 
            isDrowsy(?a,true), hasDrowsinessState(?a,true),
            """
        ) 

        microsleep = Imp() 
        microsleep.set_as_rule(
            """
            isDrowsy(?a,true) ^ hasEyesClosedForDuration(?a, ?d),
            greaterThan(?d,1) -> isMicrosleep(?a,true)
            """
        )

        sleeping = Imp() 
        sleeping.set_as_rule(
            """
            isAwake(?a,false) ^ hasEyesClosedForDuration(?a, ?d),
            greaterThan(?d,1) -> isAsleep(?a,true)
            """
        )

        assesment_required = Imp() 
        assesment_required.set_as_rule(
        """
            isUndefinedFatigueLevel(?a,true) -> assessmentRequired(?a,true)
        """
        )

def define_attention_rules(ontology): 

    with ontology:   
        attention_undefined_1= Imp() 
        attention_undefined_1.set_as_rule(
            """hasAttentionLevels(?a, ?al), lessThan(?al,0) ->hasUndefinedAttentionState(?a,true)"""
        )
        attention_undefined_2= Imp() 
        attention_undefined_2.set_as_rule(
            """hasAttentionLevels(?a, ?al), greaterThan(?al,5) ->hasUndefinedAttentionState(?a,true)"""
        )

        attention_increasing = Imp()
        attention_increasing.set_as_rule(
            """
            hasAttentionLevels(?a, ?al),greaterThan(?al,3), lessThan(?al,4) ->hasAttentionIncreasing(?a,true)
            """
        )

        attention_decreasing = Imp()
        attention_decreasing.set_as_rule(
            """
            hasAttentionLevels(?a, ?al),greaterThan(?al,1), lessThan(?al,3) ->hasAttentionDecreasing(?a,true)
            """
        )

        attentive = Imp()
        attentive.set_as_rule(
            """
                hasAttentionLevels(?a, ?al),greaterThan(?al,4), lessThan(?al,5) -> isAttentive(?a,true)
            """
        )

        inattentive = Imp() 
        inattentive.set_as_rule(
            """
                hasAttentionLevels(?a, ?al),greaterThan(?al,0), lessThan(?al,1) -> isInattentive(?a,true)
            """
        )

        attention_increasing_2 = Imp() 
        attention_increasing_2.set_as_rule(
            """
                hasAttentionLevels(?a, ?al),greaterThanOrEqual(?al,1), hasAttentionStateConfidence(?a,?conf), greaterThan(?conf, 0.5) ->hasAttentionIncreasing(?a,true)
            """
        )

        attention_decreasing_2 = Imp()
        attention_decreasing_2.set_as_rule(
            """
                hasAttentionLevels(?a, ?al),greaterThanOrEqual(?al,3), hasAttentionStateConfidence(?a,?conf), lessThan(?conf, 0.5) ->hasAttentionDecreasing(?a,true)
            """
        )

        undefined_attention_zone = Imp() 
        undefined_attention_zone.set_as_rule(
            """
                noPersonFound(?v,true) -> hasUndefinedAttentionZone(?v,true) 
            """
        )

        undefined_attention_zone_2 = Imp() 
        undefined_attention_zone_2.set_as_rule(
            """
                isUnresponsive(?a,true) -> hasUndefinedAttentionZone(?v,true)
            """
        )

        windshield_attention_zone = Imp()
        windshield_attention_zone.set_as_rule(
            """
                isAttentive(?a,true), gazeDirection(?a,?gd), stringEqualIgnoreCase(?gd, "windshield")  -> lookingAtWindshield(?a,true), activeAttentionZone(?a,"windshield")
            """
        )
        
        dashboard_attention_zone = Imp()
        dashboard_attention_zone.set_as_rule(
            """
                isAttentive(?a,true), gazeDirection(?a,?gd), stringEqualIgnoreCase(?gd, "dashboard")  -> lookingAtDashboard(?a,true),  activeAttentionZone(?a,"dashboard")
            """
        )

        driver_window_attention_zone = Imp()
        driver_window_attention_zone.set_as_rule(
            """
                isAttentive(?a,true), gazeDirection(?a,?gd), stringEqualIgnoreCase(?gd, "driver_window")  -> lookingAtDriverWindow(?a,true), activeAttentionZone(?a,"driver_window")
            """
        )

        driver_mirror_attention_zone = Imp() 
        driver_mirror_attention_zone.set_as_rule(
            """
                isAttentive(?a,true), gazeDirection(?a,?gd), stringEqualIgnoreCase(?gd, "driver_mirror")  -> lookingAtDriverMirror(?a,true), activeAttentionZone(?a,"driver_mirror")
            """
        )

        infotainment_system_attention_zone = Imp()
        infotainment_system_attention_zone.set_as_rule(
            """
                isAttentive(?a,true), gazeDirection(?a,?gd), stringEqualIgnoreCase(?gd, "infotainment_system")  -> lookingAtInfotainmentSystem(?a,true), activeAttentionZone(?a,"infotainment_system")
            """
        )

        rear_mirror_attention_zone = Imp() 
        rear_mirror_attention_zone.set_as_rule(
            """
                isAttentive(?a,true), gazeDirection(?a,?gd), stringEqualIgnoreCase(?gd, "rear_mirror")  -> lookingAtRearMirror(?a,true), activeAttentionZone(?a,"rear_mirror")
            """
        )

        unspecified_interior_attention_zone = Imp()
        unspecified_interior_attention_zone.set_as_rule(
            """
                isAttentive(?a,true), gazeDirection(?a,?gd), stringEqualIgnoreCase(?gd, "unspecified_interior")  -> lookingAtUnspecifiedInterior(?a,true), activeAttentionZone(?a,"unspecified_interior")
            """
        )

        codriver_mirror_attention_zone = Imp()
        codriver_mirror_attention_zone.set_as_rule(
            """
                isAttentive(?a,true), gazeDirection(?a,?gd), stringEqualIgnoreCase(?gd, "codriver_mirror")  -> lookingAtCodriverMirror(?a,true), activeAttentionZone(?a,"codriver_mirror")
            """
        )

        codriver_window_attention_zone = Imp()
        codriver_window_attention_zone.set_as_rule(
            """
                isAttentive(?a,true), gazeDirection(?a,?gd), stringEqualIgnoreCase(?gd, "codriver_window")  -> lookingAtCodriverWindow(?a,true), activeAttentionZone(?a,"codriver_window")
            """
        )


def define_unresponsivness_rules(ontology):
    """
    Define the rules for unresponsiveness.
    """
    with ontology:
        unresponsiveness_1 = Imp()
        unresponsiveness_1.set_as_rule(
            """
                isExtremelyFatigued(?a,true) -> isUnresponsive(?a,true)
            """
        )

        unresponsiveness_2 = Imp() 
        unresponsiveness_2.set_as_rule(
            """ 
                alertIssuedTime(?alert,?time), greaterThanOrEqual(?time, 3000), hasUnchangedGaze(?a, true), lookingAtFrontWindow(?a,false) -> isUnresponsive(?a,true)
            """
        )

        unresponsiveness_3 = Imp() 
        unresponsiveness_3.set_as_rule(
            """
                isAsleep(?a,true) -> isUnresponsive(?a,true)
            """
        )

        unresponsiveness_4 = Imp()
        unresponsiveness_4.set_as_rule(
            """
                hasLongDistraction(?a,true) -> isUnresponsive(?a,true)
            """
        )

        unresponsiveness_5 = Imp() 
        unresponsiveness_5.set_as_rule(
            """
                isMicrosleep(?a,true) -> isUnresponsive(?a,true)
            """
        )

        undefined_unresponsiveness_state = Imp()
        undefined_unresponsiveness_state.set_as_rule(
            """
                noPersonFound(?a,true) -> hasUndefinedUnresponsiveState(?a,true)
            """
        )

        undefined_unresponsiveness_state_2 = Imp()
        undefined_unresponsiveness_state_2.set_as_rule(
            """
                isAwake(?a,true), isSeverelyFatigued(?a,true), lookingAtFrontWindow(?a,true), hasUnchangedGaze(?a,true) -> hasUndefinedUnresponsiveState(?a,true)
            """
        )

        undefined_unresponsiveness_state_3 = Imp()
        undefined_unresponsiveness_state_3.set_as_rule(
            """
                isAwake(?a,true), isVeryFatigued(?a,true), isAttentive(?a,true) -> hasUndefinedUnresponsiveState(?a,true)
            """
        )

        responsiveness = Imp() 
        responsiveness.set_as_rule(
            """
                isAwake(?a,true), lookingAtFrontWindow(?a,true) -> isResponsive(?a,true)
            """
        )

        responsiveness_2 = Imp() 
        responsiveness_2.set_as_rule(
            """
                isNotFatigued(?a,true), isAwake(?a,true) -> isResponsive(?a,true)
            """
        )

        responsiveness_3 = Imp()
        responsiveness_3.set_as_rule(
            """
                isModeratelyFatigued(?a,true), isAwake(?a,true), hasShortDistraction(?a,true) -> isResponsive(?a,true)
            """
        ) 

        short_distraction = Imp()
        short_distraction.set_as_rule(
            """
                isAwake(?a,true), isModeratelyFatigued(?a,true), lookingAtCodriverMirror(?a,true), hasUnchangedGaze(?a,true),  hasGazeDuration(?a, ?gt), greaterThan(?gt,3) -> hasShortDistraction(?a,true)
            """
        )

        ## DO the same for all not front window locations. 
        long_duration_distraction = Imp()
        long_duration_distraction.set_as_rule(
            """
                isAwake(?a,true), isModeratelyFatigued(?a,true), lookingAtCodriverMirror(?a,true), hasUnchangedGaze(?a,true),  hasGazeDuration(?a, ?gt), greaterThanOrEqual(?gt,3) -> hasLongDistraction(?a,true)
            """
        )


def define_respiratory_rate_rules(ontology): 
    with ontology:
        invalid_respiratory_rate_0 = Imp()
        invalid_respiratory_rate_0.set_as_rule(
            """
                hasAge(?a, ?age), lessThan(?age,0), hasRespiratoryRate(?a,?rr) -> hasInvalidRespiratoryRate(?a,true)
            """
        )

        invalid_respiratory_rate_1 = Imp() 
        invalid_respiratory_rate_1.set_as_rule(
            """
                hasAge(?a,?age), greaterThan(?age,150), hasRespiratoryRate(?a,?rr) -> hasInvalidRespiratoryRate(?a,true)
            """
        )

        invalid_respiratory_rate_2 = Imp() 
        invalid_respiratory_rate_2.set_as_rule(
            """
                hasRespiratoryRate(?a,?rr), greaterThan(?rr, 50) -> hasInvalidRespiratoryRate(?a,true)
            """
        )

        invalid_respiratory_rate_3 = Imp()
        invalid_respiratory_rate_3.set_as_rule(
            """
                hasRespiratoryRate(?a,?rr), lessThan(?rr, 10) -> hasInvalidRespiratoryRate(?a,true)
            """
        )


        respiratory_rate_1 = Imp()
        respiratory_rate_1.set_as_rule(
            """
                hasAge(?a,?age), lessThan(?age,1), hasRespiratoryRate(?a,?rr), greaterThanOrEqual(?rr, 30), lessThan(?rr,40)-> hasNormalRespiratoryRate(?a,true)
            """
        )

        respiratory_rate_2 = Imp()
        respiratory_rate_2.set_as_rule(
            """
                hasAge(?a,?age), lessThan(?age,3), greaterThan(?age,1), hasRespiratoryRate(?a,?rr), greaterThanOrEqual(?rr, 25), lessThan(?rr,40)-> hasNormalRespiratoryRate(?a,true)
            """
        )

        respiratory_rate_3 = Imp()
        respiratory_rate_3.set_as_rule(
            """
                hasAge(?a,?age), lessThan(?age,6), greaterThan(?age,3), hasRespiratoryRate(?a,?rr), greaterThanOrEqual(?rr, 20), lessThan(?rr,30)-> hasNormalRespiratoryRate(?a,true)
            """
        )

        respiratory_rate_4 = Imp()
        respiratory_rate_4.set_as_rule(
            """
                hasAge(?a,?age), lessThan(?age,10), greaterThan(?age,6), hasRespiratoryRate(?a,?rr), greaterThanOrEqual(?rr, 18), lessThan(?rr,25)-> hasNormalRespiratoryRate(?a,true)
            """
        )

        respiratory_rate_5 = Imp()
        respiratory_rate_5.set_as_rule(
            """
                hasAge(?a,?age), lessThan(?age,50), greaterThan(?age,10), hasRespiratoryRate(?a,?rr), greaterThanOrEqual(?rr, 15), lessThan(?rr,18)-> hasNormalRespiratoryRate(?a,true)
            """
        )

        respiratory_rate_6 = Imp()
        respiratory_rate_6.set_as_rule(
            """
                hasAge(?a,?age), lessThan(?age,65), greaterThan(?age,50), hasRespiratoryRate(?a,?rr), greaterThanOrEqual(?rr, 18), lessThan(?rr,25)-> hasNormalRespiratoryRate(?a,true)
            """
        )

        respiratory_rate_7 = Imp()
        respiratory_rate_7.set_as_rule(
            """
                hasAge(?a,?age), lessThan(?age,80), greaterThan(?age,65), hasRespiratoryRate(?a,?rr), greaterThanOrEqual(?rr, 12), lessThan(?rr,28)-> hasNormalRespiratoryRate(?a,true)
            """
        )

        respiratory_rate_8 = Imp()
        respiratory_rate_8.set_as_rule(
            """
                hasAge(?a,?age),  greaterThan(?age,80), hasRespiratoryRate(?a,?rr), greaterThanOrEqual(?rr, 10), lessThan(?rr,30) -> hasNormalRespiratoryRate(?a,true)
            """
        )     


def define_heart_rate_rules(ontology):
    with ontology:
        invalid_heart_rate_1 = Imp()
        invalid_heart_rate_1.set_as_rule(
            """
                hasAge(?a,?age), lessThan(?age,18) , hasHeartRate(?a, ?hr) -> hasInvalidHeartRate(?a,true)
            """
        )

        invalid_heart_rate_2 = Imp() 
        invalid_heart_rate_2.set_as_rule(
            """
                hasAge(?a,?age), greaterThan(?age,150) , hasHeartRate(?a, ?hr) -> hasInvalidHeartRate(?a,true)
            """
        )

        invalid_heart_rate_3 = Imp()
        invalid_heart_rate_3.set_as_rule(
            """
                hasHeartRate(?a,?hr), greaterThan(?hr, 210) -> hasInvalidHeartRate(?a,true)
            """
        )

        heart_rate_1 = Imp()
        heart_rate_1.set_as_rule(
            """
                hasAge(?a,?age), lessThan(?age,30), greaterThanOrEqual(?age,20), hasHeartRate(?a,?hr), greaterThanOrEqual(?hr, 100), lessThanOrEqual(?hr,200)-> hasNormalHeartRate(?a,true)
            """
        )

        heart_rate_2 = Imp()
        heart_rate_2.set_as_rule(
            """
                hasAge(?a,?age), lessThan(?age,35), greaterThanOrEqual(?age,30), hasHeartRate(?a,?hr), greaterThanOrEqual(?hr, 95), lessThanOrEqual(?hr,190)-> hasNormalHeartRate(?a,true)
            """
        )

        heart_rate_3 = Imp()
        heart_rate_3.set_as_rule(
            """
                hasAge(?a,?age), lessThan(?age,40), greaterThanOrEqual(?age,35), hasHeartRate(?a,?hr), greaterThanOrEqual(?hr, 93), lessThanOrEqual(?hr,185)-> hasNormalHeartRate(?a,true)
            """
        )

        heart_rate_4 = Imp()
        heart_rate_4.set_as_rule(
            """
                hasAge(?a,?age), lessThan(?age,45), greaterThanOrEqual(?age,40), hasHeartRate(?a,?hr), greaterThanOrEqual(?hr, 90), lessThanOrEqual(?hr,180)-> hasNormalHeartRate(?a,true)
            """
        )

        heart_rate_5 = Imp()
        heart_rate_5.set_as_rule(
            """
                hasAge(?a,?age), lessThan(?age,50), greaterThanOrEqual(?age,45), hasHeartRate(?a,?hr), greaterThanOrEqual(?hr, 88), lessThanOrEqual(?hr, 175)-> hasNormalHeartRate(?a,true)
            """
        )

        heart_rate_6 = Imp()
        heart_rate_6.set_as_rule(
            """
                hasAge(?a,?age), lessThan(?age,55), greaterThanOrEqual(?age,50), hasHeartRate(?a,?hr), greaterThanOrEqual(?hr, 85), lessThanOrEqual(?hr, 170)-> hasNormalHeartRate(?a,true)
            """
        )

        heart_rate_7 = Imp()
        heart_rate_7.set_as_rule(
            """
                hasAge(?a,?age), lessThan(?age,60), greaterThanOrEqual(?age,55), hasHeartRate(?a,?hr), greaterThanOrEqual(?hr, 83), lessThanOrEqual(?hr, 165)-> hasNormalHeartRate(?a,true)
            """
        )

        heart_rate_8 = Imp()
        heart_rate_8.set_as_rule(
            """
                hasAge(?a,?age), lessThan(?age,65), greaterThanOrEqual(?age,60), hasHeartRate(?a,?hr), greaterThanOrEqual(?hr, 80), lessThanOrEqual(?hr, 160)-> hasNormalHeartRate(?a,true)
            """
        )

        heart_rate_9 = Imp()
        heart_rate_9.set_as_rule(
            """
                hasAge(?a,?age), lessThan(?age,70), greaterThanOrEqual(?age,65), hasHeartRate(?a,?hr), greaterThanOrEqual(?hr, 78), lessThanOrEqual(?hr, 155)-> hasNormalHeartRate(?a,true)
            """
        )

        heart_rate_10 = Imp()
        heart_rate_10.set_as_rule(
            """
                hasAge(?a,?age), greaterThanOrEqual(?age,70), hasHeartRate(?a,?hr), greaterThanOrEqual(?hr, 75), lessThanOrEqual(?hr, 150)-> hasNormalHeartRate(?a,true)
            """
        )

    

def define_heart_rate_variability_rules(ontology):
    with ontology:

        invalid_heart_rate_variability_1 = Imp()
        invalid_heart_rate_variability_1.set_as_rule(
            """
                hasAge(?a,?age), lessThan(?age,18) , hasHeartRateVariability(?a, ?hrv) -> hasInvalidHeartRateVariability(?a,true)
            """
        )

        invalid_heart_rate_variability_2 = Imp()
        invalid_heart_rate_variability_2.set_as_rule(
            """
                hasAge(?a,?age), greaterThan(?age,150) , hasHeartRateVariability(?a, ?hrv) -> hasInvalidHeartRateVariability(?a,true)
            """
        )

        invalid_heart_rate_variability_3 = Imp()
        invalid_heart_rate_variability_3.set_as_rule(
            """
                hasHeartRateVariability(?a,?hrv), greaterThan(?hrv, 115) -> hasInvalidHeartRateVariability(?a,true)
            """
        )

        invalid_heart_rate_variability_4 = Imp()
        invalid_heart_rate_variability_4.set_as_rule(
            """
                hasHeartRateVariability(?a,?hrv), lessThan(?hrv, 25) -> hasInvalidHeartRateVariability(?a,true)
            """
        )

        heart_rate_variability_1 = Imp()
        heart_rate_variability_1.set_as_rule(
            """
                hasAge(?a,?age), lessThan(?age,25), greaterThanOrEqual(?age,20), hasHeartRateVariability(?a,?hrv), greaterThanOrEqual(?hrv, 60), lessThanOrEqual(?hrv, 110)-> hasNormalHeartRateVariability(?a,true)
            """
        )

        heart_rate_variability_2 = Imp()
        heart_rate_variability_2.set_as_rule(
            """
                hasAge(?a,?age), lessThan(?age,30), greaterThanOrEqual(?age,25), hasHeartRateVariability(?a,?hrv), greaterThanOrEqual(?hrv, 55), lessThanOrEqual(?hrv, 97)-> hasNormalHeartRateVariability(?a,true)
            """
        )

        heart_rate_variability_3 = Imp()
        heart_rate_variability_3.set_as_rule(
            """
                hasAge(?a,?age), lessThan(?age,35), greaterThanOrEqual(?age,30), hasHeartRateVariability(?a,?hrv), greaterThanOrEqual(?hrv, 50), lessThanOrEqual(?hrv, 85)-> hasNormalHeartRateVariability(?a,true)
            """
        )

        heart_rate_variability_4 = Imp()
        heart_rate_variability_4.set_as_rule(
            """
                hasAge(?a,?age), lessThan(?age,40), greaterThanOrEqual(?age,35), hasHeartRateVariability(?a,?hrv), greaterThanOrEqual(?hrv, 43), lessThanOrEqual(?hrv, 71)-> hasNormalHeartRateVariability(?a,true)
            """
        )

        heart_rate_variability_5 = Imp()
        heart_rate_variability_5.set_as_rule(
            """
                hasAge(?a,?age), lessThan(?age,45), greaterThanOrEqual(?age,40), hasHeartRateVariability(?a,?hrv), greaterThanOrEqual(?hrv, 38), lessThanOrEqual(?hrv,62 )-> hasNormalHeartRateVariability(?a,true)
            """
        )

        heart_rate_variability_6 = Imp()
        heart_rate_variability_6.set_as_rule(
            """
                hasAge(?a,?age), lessThan(?age,50), greaterThanOrEqual(?age,45), hasHeartRateVariability(?a,?hrv), greaterThanOrEqual(?hrv, 35), lessThanOrEqual(?hrv, 57)-> hasNormalHeartRateVariability(?a,true)
            """
        )

        heart_rate_variability_7 = Imp()
        heart_rate_variability_7.set_as_rule(
            """
                hasAge(?a,?age), lessThan(?age,55), greaterThanOrEqual(?age,50), hasHeartRateVariability(?a,?hrv), greaterThanOrEqual(?hrv, 31), lessThanOrEqual(?hrv, 55)-> hasNormalHeartRateVariability(?a,true)
            """
        )

        heart_rate_variability_8 = Imp()
        heart_rate_variability_8.set_as_rule(
            """
                hasAge(?a,?age), lessThan(?age,60), greaterThanOrEqual(?age,55), hasHeartRateVariability(?a,?hrv), greaterThanOrEqual(?hrv, 30), lessThanOrEqual(?hrv, 53)-> hasNormalHeartRateVariability(?a,true)
            """
        )

        heart_rate_variability_9 = Imp()
        heart_rate_variability_9.set_as_rule(
            """
                hasAge(?a,?age), lessThan(?age,65), greaterThanOrEqual(?age,60), hasHeartRateVariability(?a,?hrv), greaterThanOrEqual(?hrv, 29), lessThanOrEqual(?hrv, 50)-> hasNormalHeartRateVariability(?a,true)
            """
        )

        heart_rate_variability_10 = Imp()
        heart_rate_variability_10.set_as_rule(
            """
                hasAge(?a,?age), greaterThan(?age,65), hasHeartRateVariability(?a,?hrv), greaterThanOrEqual(?hrv, 30), lessThanOrEqual(?hrv, 50)-> hasNormalHeartRateVariability(?a,true)
            """
        )


def define_blood_saturation_rules(ontology):
    """
    Define the rules for blood saturation.
    """
    with ontology:

        invalid_blood_saturation_1 = Imp()
        invalid_blood_saturation_1.set_as_rule(
            """
                hasBloodOxygenSaturation(?a, ?bos), lessThan(?bos, 50) -> hasInvalidBloodOxygenSaturation(?a,true)
            """
        )
        invalid_blood_saturation_2 = Imp()
        invalid_blood_saturation_2.set_as_rule(
            """
                hasBloodOxygenSaturation(?a, ?bos), greaterThan(?bos, 100) -> hasInvalidBloodOxygenSaturation(?a,true)
            """
        )

        blood_saturation_1 = Imp()
        blood_saturation_1.set_as_rule(
            """
                hasBloodOxygenSaturation(?a, ?bos), greaterThanOrEqual(?bos,95) -> hasNormalBloodOxygenSaturation(?a,true)
            """
        )

        blood_saturation_2 = Imp() 
        blood_saturation_2.set_as_rule(
            """
                hasBloodOxygenSaturation(?a, ?bos), greaterThanOrEqual(?bos,92), lessThan(?bos, 95) -> hasBorderlineNormalBloodOxygenSaturation(?a,true)
            """ 
        ) 

        blood_saturation_3 = Imp()
        blood_saturation_3.set_as_rule(
            """
                hasBloodOxygenSaturation(?a, ?bos), greaterThanOrEqual(?bos,89), lessThan(?bos, 92) -> hasLowBloodOxygenSaturation(?a,true)
            """
        )

        blood_saturation_4 = Imp()
        blood_saturation_4.set_as_rule(
            """
                hasBloodOxygenSaturation(?a, ?bos), greaterThanOrEqual(?bos,88), lessThan(?bos, 89) -> hasVeryLowBloodOxygenSaturation(?a,true)
            """
        )

        blood_saturation_5 = Imp()
        blood_saturation_5.set_as_rule(
            """
                hasBloodOxygenSaturation(?a, ?bos), greaterThanOrEqual(?bos,88), lessThan(?bos, 89) -> hasDangerouslyLowBloodOxygenSaturation(?a,true)
            """
        )
        
        blood_saturation_6 = Imp()
        blood_saturation_6.set_as_rule(
            """
                hasBloodOxygenSaturation(?a, ?bos), lessThan(?bos, 88) -> hasDangerouslyLowBloodOxygenSaturation(?a,true)
            """
        )


def save_rules_into_ontology(ontology, directory, filename, format_save='rdfxml', format='xml'):
    """
    Save the rules from the ontology into a file.
    """ 
    filepath = directory + filename 
    destination = directory + "ConnectingInCabin_Rules_refined.rdf"
    ontology.save(file=filepath, format=format_save)
    graph = Graph() 
    graph.parse(filepath, format=format)
    graph.serialize(destination=destination, format=format)
    print("Refined Rules Saved. ")
    os.remove(filepath)
    return destination


def syncrhonize_ontology(ontology):
    with ontology:
        sync_reasoner_pellet(infer_property_values=True)