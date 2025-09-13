from tools.appraisal import StepContext
from tools.logger import logger
from tools.common import *
from designs.rule_creator import RuleCreator
from tools.metrics import OntologyEvaluator

import uuid
import pdb
import gc
import pandas as pd
import tracemalloc

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
        self.ev = OntologyEvaluator(self.ontology)


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
    
    
    def parse_observations(self, dataset_path, batching=True, reasoning_thr=10, save=False):
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
        tracemalloc.start()
        save_path = os.path.join(os.getcwd(),"ontologies/snapshot.owl") if save else None
        last_state = None
        batch_states = []

        with StepContext(name='Initialize Onto', catch=(Exception, )): 
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

        with self.ontology:       

            for index, row in dataset.iterrows():

                ts_iso = str(iso_format(row['TIME']))
                actor_state = new_actor_state(
                    onto = self.ontology, 
                    actor = actor, 
                    last_state = last_state, 
                    ts_iso=ts_iso
                )

                # Connect the sensor to the observations 
                obs_state = attach_values_to_observations(
                    onto=self.ontology, 
                    obs_state=obs,
                    cols=dataset.columns, 
                    row=row, 
                    idx=index
                )

                obs_state = attach_obs_to_phy_state(obs_state,phy_vocab) 
                obs_state = attach_obs_to_actor_state(obs_state, actor_vocab) 

                # Assign values to the subclasses instances based on the observations
                self.rule_parser.assign_values(obs_state,"ObsIsDividedIntoPhS","hasNumericalValue")
                self.rule_parser.assign_values(obs_state,"ObsIsDividedIntoActor","hasStringValue")

                # Create the rules (once) for numerical comparison and health assessment
                with StepContext(name="Setting up Rules", catch=(RuntimeError,)):
                    self.rule_parser.set_up_rules(index)
                
                


                batch_states.append(actor_state)

                # Run the reasoner to update the ontology with the new values
                if len(batch_states) >= reasoning_thr or (index == len(dataset)-1) or (index == 0):
                    with StepContext(name="Synchronize Ontology", catch=(RuntimeError,)): 
                        gc.collect()
                        self.rule_parser.synchronize_ontology()
                                
                # Create the description of the actor and save it in JSON format
                with StepContext(name="Crate Label", catch=(RuntimeError,)):
                    for s in batch_states:
                        self.rule_parser.create_label(actor, filepath, index)


                # Get Metrics for the ontology. 
                
                last_state = batch_states[-1]
                batch_states.clear()

            
            # Remove the previous values from the ontology to avoid conflicts
            # self.rule_parser.remove_prev_values(obs, actor)
                
                if index == 10: 
                    pdb.set_trace()


        # Save the parsed ontology to a file for vizualization of the rules' results. 
        self.save_onto(0)    
        #self.rule_parser.determine_trends() 

        return f"Ontology finished processing dataset observations."
        





    def save_onto(self, index, file_path="/ontologies/trial_onto_1.owl"): 

        if index == 0 or index % 10 == 0: 
            parent_directory = os.getcwd() 
            save_path = f"{parent_directory}/{file_path}" 
            self.ontology.save(file=save_path)
            logger.info(f"[checked] Ontology Saved at {index}.")
            time.sleep(5) 


    

    
