from owlready2 import *
from rdflib import Graph, URIRef, Literal
from scripts.rule_creator import RuleCreator
import pandas as pd



class OntologyParser: 
    """
    OntologyParser class for parsing and interacting with an ontology, 
    including loading, parsing rules, and saving the results.
    """

    def __init__(self, ontology_path, logger):
        """
        The constructor for the OntologyParser class.
        """

        self.ontology_path = ontology_path
        self.ontology = self.load_ontology()
        self.logger = logger  
        self.graph = None 
        self.rule_parser = RuleCreator(self)


    def load_ontology(self): 
        """
        This method loads the ontology from the specified path.
        --only_local is used to manually load the ontology without processing owl:versionIRI
        """
        ontology = get_ontology("file://"+self.ontology_path).load(only_local=True) 
        #Validate that ontology was correctly loaded:         
        return ontology
    

    def search_class_ontology(self, target_class_name):
        """
        Search if the Target class ("Target" in ths case) exists in the ontology
        NOTE: only used for debugging purposes
        """
        target_class = None
        for cls in self.ontology.classes():
            if cls.name == target_class_name :
                target_class = cls 
                break 
        
        if target_class is None:
            raise ValueError(f"Target class '{target_class_name}' not found in the ontology.")
        return target_class
    
    
    def parse_observations(self, dataset_path):
        """
        This method parses the observations from the given dataset and creates instances of the Observation class.
        Then translates the rules established in the ontology with the reasoner and saves the results.
        
        Args:
          - dataset_path: The path to the dataset file.
        """

        dataset = pd.read_csv(dataset_path)
        dataset = dataset[:5]
        filepath = os.getcwd() + "/labels"
        
        try: 
            # Create instances for the Label and the Sensor
            with self.ontology: 
                self.rule_parser.create_instances("Label")
                self.rule_parser.create_instances("MonitoringSensor")

            # Check if the Observations class exists in the ontology
            for cls in self.ontology.classes():
                if cls.name == "Observations":
                    self.logger.info(f"Class {cls.name} found.")
                    break
            else:
                self.logger.error(f"Class Observation not found in the ontology.")
                return
            
            # Create the main instance of the Observations class
            obs = self.ontology.Observations(f"observation_{0}")
            for index, row in dataset.iterrows():
                
                # Connect the sensor to the observations 
                # self.rule_parser.connect_sensor_to_observations(obs)

                #Pass health factors 
                obs.hasHR.append(row['HR'] if "HR" in dataset.columns and isinstance(row['HR'],int) else [-1])
                obs.hasHRV.append(row['HRV'] if "HRV" in dataset.columns and isinstance(row['HRV'],int) else [-1])
                obs.hasRR.append(row['RR'] if "RR" in dataset.columns and isinstance(row['RR'],int) else [-1])
                obs.hasSpO2.append(row["SPO2"] if "SPO2" in dataset.columns and isinstance(row['SPO2'],int) else [-1])
                obs.hasDROWSY.append(row['DROWSY'] if "DROWSY" in dataset.columns and isinstance(row['DROWSY'],int) else [-1])
                
                # Pass Actor's Characteristics
                obs.hasAccessories.append(row['Accessories'] if "Accessories" in dataset.columns and isinstance(row['Accessories'],str)  else [-1])
                obs.hasAge.append(row['Age'] if "Age" in dataset.columns and isinstance(row['Age'],int) else [-1])
                obs.hasSex.append(row['Sex'] if "Sex" in dataset.columns and isinstance(row['Sex'],str) else [-1])
                obs.hasFaceCharacteristics.append(row["Characteristics"] if "Characteristics" in dataset.columns and isinstance(row['Characteristics'],str) else [-1])
                obs.hasDemographic.append(row["Demographic"] if "Demographic" in dataset.columns and isinstance(row['Demographic'],str)  else [-1])

                # Connect the observation to the corresponding subclasses inside the ontology, based on the super class they belong to. 
                self.rule_parser.observations_to_classes(obs, "PhysiologicalState", "ObsIsDividedIntoPhS")
                self.rule_parser.observations_to_classes(obs, "Actor", "ObsIsDividedIntoActor")
                
                # Run the reasoner for each updated observation
                self.rule_parser.synchronize_ontology()

                # Assign values to the subclasses instances based on the observations
                for obs in self.ontology.Observations.instances(): 
                    self.rule_parser.assign_values(obs,"ObsIsDividedIntoPhS","hasNumericalValue")
                    self.rule_parser.assign_values(obs,"ObsIsDividedIntoActor","hasStringValue")
                
                # Create the rules (once) for numerical comparison and health assessment
                self.rule_parser.set_up_rules(index)
            
                # Run the reasoner to update the ontology with the new values
                self.rule_parser.synchronize_ontology()

                # Create the description of the actor and save it in JSON format
                self.rule_parser.create_label(filepath, index)
                
                # Save the parsed ontology to a file for vizualization of the rules' results. 
                if index ==0: 
                    ontology_save_path =  os.getcwd() + "/ontologies/updated_ontology.owl"
                    self.ontology.save(file=ontology_save_path) 

                # Remove the previous values from the ontology to avoid conflicts
                self.rule_parser.remove_prev_values(obs)
                

            self.logger.info("Ontology saved.")
            return f"Ontology finished processing dataset observations."
        except Exception as e:
                self.logger.error(f"Error parsing the ontology: {e}")
                return f"Error parsing the ontology: {e}"









    

    