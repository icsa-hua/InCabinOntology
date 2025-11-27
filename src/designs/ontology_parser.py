from src.tools.appraisal import StepContext
from src.tools.common import *
from src.designs.rule_creator import RuleCreator
from src.tools.logger import get_logger
from src.tools.metrics import OntologyEvaluator
from src.tools.trend_analysis import analysis, gci_trends, trends

import uuid
import pdb
import time 
import os 
import gc
import pandas as pd
import tracemalloc

from owlready2 import *
from collections import defaultdict

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
    

    def get_or_create_actor(self): 

        id = uuid.uuid4().hex
        if not self.ontology.Actor.instances(): 
            actor = self.ontology.Actor(f"actor_{id}")
            actor.hasUniqueIdentifier = [id] 
            logger.debug("Created Actor")
        else: 
            actor = self.ontology.Actor.instances()[0] 
            if len(getattr(actor, "hasUniqueIdentifier")) == 0:
                actor.hasUniqueIdentifier = [id]
            logger.debug(f"Found Actor and assigned UUID->{id}")

        return actor 


    def get_or_create_obs(self): 
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
        save_path = os.path.join(assets_dir,"ontologies/inference_1_1.owl") if save else None
        last_state = {}
        trend_analysis_flag = False
        batch_states = []
        ts_iso_dates = [] 

        with StepContext(name='Initialize Onto', catch=(Exception, )): 
            with self.ontology: 
                
                # Create instances for Label and Monitoring Sensor 
                self.rule_parser.create_instances("MonitoringSensor")

                # Create the main instance for OBS and Actor. 
                obs = self.get_or_create_obs()
                actor = self.get_or_create_actor()
            
                with StepContext(name="SetUp all Initial Indis", catch=(RuntimeError,)): 
                    self.rule_parser.generate_all_nece_instances()

                with StepContext(name="Setting up Rules", catch=(RuntimeError,)):
                    self.rule_parser.set_up_rules()
    
                with StepContext(name="Analysis GCI trends", catch=(Exception, RuntimeError)): 
                    gci_trends(self.ontology)
                    trend_analysis_flag = True

            self.rule_parser.synchronize_ontology()
            self.save_onto(0, "assets/ontologies/snapshot_after_rules_pre_inference.owl")        

        # With this process we do NOT account for Obs inside SWRL. 
        with self.ontology:       

            # Main loop to go through the observations. 
            for index, row in dataset.iterrows():

                ts_iso =(iso_format(row['TIME']))
                ts_iso_date = get_ts_iso_value(ts_iso)
                
                # Here we create the PHY instances (hr_instance, hrv_instance, ...) 
                with StepContext(name="Create Physiological State Attributes", catch=(RuntimeError, ), verbose=False):
                    phy_vocab = create_Physiological_inds(self.ontology, ts_iso_date) 

                with StepContext(name="Create ActorStates Demographic Attributes", catch=(RuntimeError, ), verbose=False):
                    actor_vocab = create_Actor_inds(self.ontology, ts_iso_date) 

                label = create_Label_ind(self.ontology, ts_iso_date) 

                with StepContext(name="Create ActorState", catch=(Exception, RuntimeError)): 
                    actor_state = new_actor_state(
                        onto = self.ontology, 
                        actor = actor, 
                        ts_iso=ts_iso_date,
                        last_state=last_state.get(actor), 
                    )

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
                    ts_iso_dates.append(ts_iso_date)

                    # Assign values to the subclasses instances based on the observations
                    self.rule_parser.assign_values(obs_state,"ObsIsDividedIntoPhS","hasNumericalValue")
                    self.rule_parser.assign_values(obs_state,"ObsIsDividedIntoActor","hasStringValue")

                with StepContext(name="Parse Instances to Actor State", catch=(Exception, RuntimeError)): 
                    self.rule_parser.connect_actor_state_to_values(
                        actor_state=actor_state, 
                        phy_vocab=phy_vocab, 
                        actor_vocab=actor_vocab, 
                        label_inst=label
                    )

                with StepContext(name="Batching Ontology Inference", catch=(RuntimeError,)):
                    need_sync =  (len(batch_states)>= reasoning_thr) or (index == len(dataset)-1)
                    
                    if need_sync: 
                        gc.collect() 

                        # Run the reasoner to update the ontology with the new values                       # Run the reasoner to update the ontology with the new values     
                        # self.rule_parser.synchronize_ontology()
                        print("INDEX AT THIS MOMENT (ONLY GOD KNOWS): ", index)
                        if index == 24: 
                            pdb.set_trace()
                        self.ev.sync_reasoner(len(batch_states))
                        
                        # Create the description of the actor and save it in JSON format
                        with StepContext(name="Crate Label", catch=(RuntimeError,)):
                            data = self.rule_parser.create_labels(actor, filepath, len(batch_states))

                        with StepContext(name="Trend Analysis", catch=(RuntimeError, )): 
                            if trend_analysis_flag:
                                analysis(trends(), data)


                        with StepContext(name="Prepare Batched Results", catch=(RuntimeError,)): 
                            self.ev.metrics.snapshot_memory()
                            self.ev.snapshot_size()
                            self.ev.check_functional_violations()
                            self.ev.undefined_label_ratios()
                            self.ev.run_cq()
                            self.ev.label_distributions()
                            self.ev.crosstab()
                        self.save_onto(0, "assets/ontologies/snapshot_after_inference.owl")
                        self.rule_parser.remove_prev_values(ts_iso_dates, batch_states)
                        batch_states.clear() 
                    self.rule_parser.clear_obs(obs)  

                if index == 200: 
                    break
        self.print_results()
        logger.info("[checked] Memory Allocated")
        logger.info(tracemalloc.get_traced_memory())
        tracemalloc.stop()
        return f"Ontology finished processing dataset observations."
        

    def save_onto(self, index, file_path="assets/ontologies/snapshot_3.owl"): 
        if index == 0 or index % 10 == 0: 
            parent_directory = os.getcwd() 
            save_path = f"{parent_directory}/{file_path}" 
            self.ontology.save(file=save_path)
            logger.info(f"[checked] Ontology Saved at {index}.")


    def print_results(self): 
        logger.info(f"Reason times (s): {self.ev.metrics.reason_times}")
        logger.info(f"Throughput (states/s): {self.ev.metrics.throughput}")
        logger.info(f"Memory (KB): {self.ev.metrics.mem_snapshots[-1] if self.ev.metrics.mem_snapshots else None}")
        logger.info(f"Undefined ratios: {self.ev.metrics.undefined_ratios[-1] if self.ev.metrics.undefined_ratios else None}")
        logger.info(f"Functional violations (last): {self.ev.metrics.functional_violations[-1] if self.ev.metrics.functional_violations else None}")
        logger.info(f"Label distributions: {self.ev.metrics.distributions}")
        crostab = defaultdict()
        for k, v in self.ev.metrics.crosstabs.items():
            crostab[k] = list(v.items())[:5]
        logger.info(f"Crosstabs sample: {crostab}")

            
