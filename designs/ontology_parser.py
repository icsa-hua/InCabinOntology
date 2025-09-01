from tools.appraisal import StepContext
from tools.logger import logger
from tools.common import *
from designs.rule_creator import RuleCreator

import uuid
import pandas as pd

from owlready2 import *

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
        self.graph = None 
        self.rule_parser = RuleCreator(self)


    def load_ontology(self): 
        """
        This method loads the ontology from the specified path.
        --only_local is used to manually load the ontology without processing owl:versionIRI
        """
        ontology = get_ontology("file://"+self.ontology_path).load(only_local=True) 
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
    
    
    def parse_observations(self, dataset_path, batching=True, reasoning_thr=10):
        """
        This method parses the observations from the given dataset and creates instances of the Observation class.
        Then translates the rules established in the ontology with the reasoner and saves the results.
        
        Args:
          - dataset_path: The path to the dataset file.
          - batching: If we want to opt for batching multiple rows together and calling the reasoner once 
          - reasoning_thr: The multitude of objects to reason
        """

        dataset = pd.read_csv(dataset_path)
        dataset = dataset[:5]
        filepath = os.getcwd() + "/labels"
        created = 0 

        with StepContext(name='Parse Data to Ont', catch=(Exception, )): 
            # Create instances for the Label and the Sensor
            with self.ontology: 
                self.rule_parser.create_instances("Label")
                self.rule_parser.create_instances("MonitoringSensor")

                # Create the main instance of the Observations class
                if not self.ontology.Observations.instances(): 
                    obs = self.ontology.Observations(f"observation_{0}")
                else: 
                    obs = self.ontology.Observations.instances()[0]

                if not self.ontology.Actor.instances(): 
                    actor = self.ontology.Actor(f"actor_{uuid.uuid4().hex}")
                else: 
                    actor = self.ontology.Actor.instances()[0] 

                phy_vocab = create_Physiological_inds(self.ontology) 
                actor_vocab = create_Actor_inds(self.ontology) 

            # Check if the Observations class exists in the ontology
            for index, row in dataset.iterrows():
                ts_iso = iso_format(row['TIME'])
                actor_state = new_state(self.ontology, actor, ts_iso)
                actor.ActorhasState.append(actor_state)

                # Connect the sensor to the observations 
                # self.rule_parser.connect_sensor_to_observations(obs)
                obs_state = attach_values_to_observations(
                    onto=self.ontology, 
                    obs_state=obs,
                    cols=dataset.columns, 
                    row=row, 
                    idx=index
                )

                #self.rule_parser.observations_to_classes(obs_state, "PhysiologicalState", "ObsIsDividedIntoPhS")
                #self.rule_parser.observations_to_classes(obs_state, "ActorState", "ObsIsDividedIntoActor")
                obs_state = attach_obs_to_phy_state(obs_state,phy_vocab) 
                obs_state = attach_obs_to_actor_state(obs_state, actor_vocab) 
                created += 1 

                #for obs in self.ontology.Observations.instances():
                # Assign values to the subclasses instances based on the observations
                self.rule_parser.assign_values(obs_state,"ObsIsDividedIntoPhS","hasNumericalValue")
                self.rule_parser.assign_values(obs_state,"ObsIsDividedIntoActor","hasStringValue")

                # Create the rules (once) for numerical comparison and health assessment
                self.rule_parser.set_up_rules(index)
                
                import pdb;pdb.set_trace()
                # Run the reasoner to update the ontology with the new values
                self.rule_parser.synchronize_ontology()
                                
                # Create the description of the actor and save it in JSON format
                #self.rule_parser.create_label(filepath, index)

                # Save the parsed ontology to a file for vizualization of the rules' results. 
                self.save_onto(index=index)    
                #self.rule_parser.determine_trends() 

                import pdb;pdb.set_trace()
                # Remove the previous values from the ontology to avoid conflicts
                #self.rule_parser.remove_prev_values(obs)
                
            return f"Ontology finished processing dataset observations."
        





    def save_onto(self, index, file_path="/ontologies/trial_onto_1.owl"): 

        if index == 0 or index % 10 == 0: 
            parent_directory = os.getcwd() 
            save_path = f"{parent_directory}/{file_path}" 
            self.ontology.save(file=save_path)
            logger.info(f"[checked] Ontology Saved at {index}.")
            time.sleep(5) 


    

    
