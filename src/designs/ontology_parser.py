from os import wait
from src.tools.appraisal import StepContext
from src.tools.common import *
from src.designs.rule_creator import RuleCreator
from src.tools.logger import get_logger
from src.tools.metrics import OntologyEvaluator

import uuid
import pdb
import time 
import gc
import pandas as pd
import tracemalloc

from owlready2 import *

logger = get_logger("aiq_onto")

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


    def get_or_create_actor(self): 
        #TODO: If actor is already inside the ontology as an individual we need to access the UID and find it inside the dataset. 

        id = uuid.uuid4().hex
        if not self.ontology.Actor.instances(): 
            actor = self.ontology.Actor(f"actor_{id}")
            actor.hasUniqueIdentifier = [id] 
            logger.debug("Created Actor")
            print("Created Actor")
        else: 
            actor = self.ontology.Actor.instances()[0] 
            if len(getattr(actor, "hasUniqueIdentifier")) == 0:
                actor.hasUniqueIdentifier = [id]
            logger.debug(f"Found Actor and assigned UUID->{id}")

        return actor 


    def get_or_create_obs(self): 
        # Create the main instance of the Observations class
        if not self.ontology.Observations.instances(): 
            obs = self.ontology.Observations(f"observation_{0}")
        else: 
            obs = self.ontology.Observations.instances()[0]
        return obs


    
    def parse_observations(self, dataset_path, batching=True, reasoning_thr=5, save=False):
        """
        This method parses the observations from the given dataset and creates instances of the Observation class.
        Then translates the rules established in the ontology with the reasoner and saves the results.
        
        Args:
          - dataset_path: The path to the dataset file.
          - batching: If we want to opt for batching multiple rows together and calling the reasoner once 
          - reasoning_thr: The multitude of objects to reason
        """
        assets_dir = get_assets_path()
        dataset = pd.read_csv(dataset_path)
        filepath = assets_dir + "/labels"
        tracemalloc.start()
        save_path = os.path.join(assets_dir,"ontologies/snapshot_0.1.owl") if save else None
        last_state = {}

        batch_states = []

        with StepContext(name='Initialize Onto', catch=(Exception, )): 
            with self.ontology: 
                
                # Create instances for Label and Monitoring Sensor 
                self.rule_parser.create_instances("Label")
                self.rule_parser.create_instances("MonitoringSensor")

                # Create the main instance for OBS and Actor. 
                obs = self.get_or_create_obs()
                actor = self.get_or_create_actor()
            
                with StepContext(name="SetUp all Initial Indis", catch=(RuntimeError,)): 
                    self.rule_parser.generate_all_nece_instances()

                with StepContext(name="Setting up Rules", catch=(RuntimeError,)):
                    self.rule_parser.set_up_rules()
    
            self.rule_parser.synchronize_ontology()
            gc.collect()

        # With this process we do NOT account for Obs inside SWRL. 
        with self.ontology:       

            # Main loop to go through the observations. 
            for index, row in dataset.iterrows():

                ts_iso =(iso_format(row['TIME']))
                ts_iso_date = get_ts_iso_value(ts_iso)
                # Here we create the PHY instances (hr_instance, hrv_instance, ...) 
                phy_vocab = create_Physiological_inds(self.ontology, ts_iso_date) 
                actor_vocab = create_Actor_inds(self.ontology, ts_iso_date) 

                actor_state = new_actor_state(
                    onto = self.ontology, 
                    actor = actor, 
                    ts_iso=ts_iso_date,
                    last_state=last_state.get(actor), 
                )

                logger.info(f"DATASET ROW:{row}")
                last_state[actor.hasUniqueIdentifier[0]] = actor_state
                with StepContext(name="Dataset -> Observation", catch=(RuntimeError,), verbose=True):
                        # Read the data into Observations. 
                        obs_state = attach_values_to_observations(
                            onto=self.ontology, 
                            obs_state=obs,
                            cols=dataset.columns, 
                            row=row, 
                            idx=index
                        )
                with StepContext(name="Process Observation", catch=(IndexError, RuntimeError)): 

                    # DON'T use rules to pass the observation values to the states 
                    obs_state = attach_obs_to_phy_state(obs_state,phy_vocab) 
                    obs_state = attach_obs_to_actor_state(obs_state, actor_vocab) 
                    batch_states.append(actor_state)

                    # self.rule_parser.re_create_indi(
                    #     ts_iso=ts_iso_date, 
                    #     unique=None, 
                    #     regenerate=True
                    # )

                    # Assign values to the subclasses instances based on the observations
                    self.rule_parser.assign_values(obs_state,"ObsIsDividedIntoPhS","hasNumericalValue")
                    self.rule_parser.assign_values(obs_state,"ObsIsDividedIntoActor","hasStringValue")
                
                with StepContext(name="Parse Instances to Actor State", catch=(Exception, RuntimeError)): 
                    self.rule_parser.connect_actor_state_to_values(
                        actor_state=actor_state, 
                        phy_vocab=phy_vocab, 
                        actor_vocab=actor_vocab
                    )
                
               
                with StepContext(name="Batching Ontology Inference", catch=(RuntimeError,)):
                    need_sync =  (len(batch_states)>= reasoning_thr) or (index == len(dataset)-1)
                    
                    if need_sync: 
                        gc.collect() 
                        pdb.set_trace()
                        # Run the reasoner to update the ontology with the new values                       # Run the reasoner to update the ontology with the new values     
                        self.rule_parser.synchronize_ontology()
                        
                        # Create the description of the actor and save it in JSON format
                        with StepContext(name="Crate Label", catch=(RuntimeError,)):
                            for j, _ in enumerate(batch_states): 
                                self.rule_parser.create_label(actor, filepath, index=index-len(batch_states) +1 +j)
                
                        batch_states.clear() 

                self.rule_parser.clear_obs(obs)  
            # Remove the previous values from the ontology to avoid conflicts
            # self.rule_parser.remove_prev_values(obs, actor)

        # Save the parsed ontology to a file for vizualization of the rules' results. 
                    # self.save_onto(0)    
        #self.rule_parser.determine_trends() 

        logger.info("[checked] Memory Allocated")
        logger.info(tracemalloc.get_traced_memory())
        tracemalloc.stop()
        return f"Ontology finished processing dataset observations."
        


    def save_onto(self, index, file_path="assets/ontologies/snapshot_2.owl"): 

        if index == 0 or index % 10 == 0: 
            parent_directory = os.getcwd() 
            save_path = f"{parent_directory}/{file_path}" 
            self.ontology.save(file=save_path)
            logger.info(f"[checked] Ontology Saved at {index}.")


    

    
