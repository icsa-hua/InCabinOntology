from src.tools.common import *
from src.tools.appraisal import StepContext 
from src.tools.logger import get_logger
from src.designs.helper import *

import os 
import pdb
import uuid 
import json 
import random


from typing import Any
from owlready2 import *
from owlready2 import destroy_entity
from rdflib import Graph
from collections import defaultdict

logger = get_logger("aiq_onto")

class RuleCreator: 

    """
        This class is responsible for creating rules based on the ontology. 
        SWRL rules are utilized to perform numerical comparisons between 
        the values received from the Observations class and the predefined 
        threshold values based on internet articles and medical guidelines. 

        These rules are then saved into the ontology, allowing the user to 
        check the format and results of the rules after the reasoner is synchronized. 

        The rules are actively checking: 
        - Heart Rate (HR) 
        - Heart Rate Variability (HRV)
        - Respiratory Rate (RR)
        - Oxygen Saturation (SpO2)
        - Drowsiness (DS)
        - Age group for the actor 
        - Characteristics of the Actor 

        Additionally through the rules we can assess the health state of the actor, 
        estimating: 
        - Fatigue 
        - Attention 
        - Unresponsiveness 
        - Eye state (if the actor's eyes are open or closed) 

        Finally this class produces __Labels__ that describe the 
        actor's health and appearance for later classification. 
    """


    def __init__(self, ontology_parser):
        """
        Initializes the RuleCreator class with the provided ontology parser.
        Sets up the necessary attributes to interact with the ontology,
        including the ontology instance, ontology path, logger, and age groups.
        Args:
            ontology_parser (OntologyParser): An instance of the OntologyParser class.
        """ 
        self.ontology = ontology_parser.ontology 
        self.ontology_path = ontology_parser.ontology_path
        self.age_groups = None 
        self.sex_groups = None 
        self.age_group_names = None 
        self.sex_group_names = None
        self.temp_groups = None 
        self.temp_group_names = None 
        


    def save_rules_into_ontology(self, filename, format_save="rdfxml", format="xml"):
        """
        Save the rules from the ontology into a file.
        Enable this when you want to save the rules in a different file, 
        than the one in the OntologyParser. 
        """ 
        filepath = self.ontology_path + filename 
        destination = self.ontology_path + "in_cabin.rdf"
        self.ontology.save(file=filepath, format=format_save)
        graph = Graph() 
        graph.parse(filepath, format=format)
        graph.serialize(destination=destination, format=format) 
        logger.info("Refined Rules Saved...")
        os.remove(filepath)
        return destination 
    
    
    def synchronize_ontology(self): 
        """
        Synchronizes the ontology with the reasoner.
        Uses the PELLET reasoner to infer property values and synchronize the ontology, 
        as only PELLET supports numerical conditions for SWRL rules. 
        """
        with self.ontology: 
            sync_reasoner_pellet(infer_property_values=True, infer_data_property_values=True)


    def create_instances(self, ind_class, ts_iso=None, unique=None, regenerate=False): 
        """
        This function creates instances of classes that are not yet created in the initial ontology. 
        If however an instance of the desired class exists then it checks if the instance already exists,
        and if not, it creates a new instance. 

        Args:
            ind_class (str): The name of the class to create an instance of.
        """
 
        if not list(getattr(self.ontology, ind_class).instances()) and not regenerate: 
            new_instance = getattr(self.ontology, ind_class)(f"{ind_class.lower()}_instance")
            logger.debug(f"New Instance created for {ind_class}.")
        else: 
            if ts_iso is None: 
                unique_id = unique if unique is not None else uuid.uuid4().hex 
                new_instance = getattr(self.ontology, ind_class)(f"{ind_class.lower()}_inst_{unique_id}")
            else: 
                new_instance = getattr(self.ontology, ind_class)(f"{ind_class.lower()}_inst_{ts_iso}")
            logger.debug(f"Regenerate instance of {ind_class} created.")

        return new_instance 


    def connect_sensor_to_observations(self,obs): 
        """
        This function connects the observations to the MonitoringSensor class.
        This is disabled for now as the MonitoringClass is not yet used. 
        Args:
            obs (Observation): The observation to connect to the MonitoringSensor class.
        """

        with self.ontology: 
            sensor_instance = getattr(self.ontology, "MonitoringSensor").instances()[0]
            sensor_instance.SensorCapturesObservations = [obs] 
            sensor_instance.SensorMonitorsActor = [self.ontology.Actor.instances()[0]]
        logger.debug("Monitoring Management system initialized based on observations...")


    
    def assign_values(self, obs_state:Any=None, cls_property:str="", property_name:str=""):
        """
        This function assigns the values of the observations to the instances of the classes, 
        previously created in the ontology. Requires the reasoner to have been executed, otherwise 
        it will not find the newly created instances.
        Args:
            obs (Observation): The observation to storing the numerical values from the dataset. 
            cls_property (str): The name of the object property to use. 
            property_name (str): The name of the data property to pass the values. 
        """

        # Check if the observation has the object property.
        if not hasattr(obs_state, cls_property):
            logger.debug(f"Observation does not have the object property {cls_property}...")
            raise ValueError(f"Observation does not have the object property {cls_property}...")

        with StepContext(name=f'Assign Values From Obs : {cls_property}', catch=(KeyError, )): 

            with self.ontology: 
                ind_property = getattr(obs_state, cls_property)

                if len(ind_property) == 0:
                    logger.debug(f"Empty observation property {cls_property}...")
                    raise ValueError(f"Empty observation property {cls_property}...")
                
                # Iterate through the instances of the object property.
                for instance in ind_property:
                    if not hasattr(instance,property_name): 
                        logger.debug(f"Instance {instance} does not have the property {property_name}...")
                        continue

                    # access the physical property values from the OBS
                    obs_to_PHY_instance(
                        obs_state=obs_state, 
                        instance=instance, 
                        property_name=property_name
                    )


    def __determine_age(self): 
        """
        This funciton creates the rules to categorize the age of the actor into 
        a group : 
        * Young (0-18) 
        * Middle-Aged (18-65)
        * Elderly (>65) 
        """
        

        if self.ontology.Age is not None: 

            age_rules = [
                ("Young", "greaterThanOrEqual", 0, "lessThan", 18),
                ("Middle-Aged", "greaterThanOrEqual", 18, "lessThan", 65),
                ("Elderly", "greaterThanOrEqual", 65, "lessThanOrEqual", 110)
            ]

            for rule in age_rules:                
                Imp().set_as_rule(
                    f"""
                    ActorState(?act_state), 
                    ActorStateHasAge(?act_state, ?age_inst),
                    hasAgeValue(?age_inst, ?age_value),
                    {rule[1]}(?age_value, {rule[2]})
                    {f', {rule[3]}(?age_value, {rule[4]})' if len(rule) > 3 else ''},

                        -> AgeBelongsToGroup(?age_inst, {rule[0].lower()}_instance)
                    """
                )
                print(                    f"""
                        ActorState(?act_state), 
                        ActorStateHasAge(?act_state, ?age_inst),
                        hasAgeValue(?age_inst, ?age_value),
                        {rule[1]}(?age_value, {rule[2]})
                        {f', {rule[3]}(?age_value, {rule[4]})' if len(rule) > 3 else ''},

                            -> AgeBelongsToGroup(?age_inst, {rule[0].lower()}_instance)
                        """)

        pdb.set_trace()

         # Keep the age groups in a list to get the corresponding threshold instance later. 
        self.age_groups = [age.name.lower() for age in self.ontology.Age.subclasses()]        
        self.age_group_names = [age.name for age in self.ontology.Age.subclasses() ]

        
    def __determine_gender(self): 

        person_sex = {
            "Male": ["Man"],
            "Female": ["Woman"]
        } 
        for name in person_sex:
            if not hasattr(self.ontology, name):
                type(name, (self.ontology.Sex,), {})

        for name, value in person_sex.items(): 
            for val in value:

                Imp().set_as_rule(
                    f"""
                    ActorState(?act_state), validAt(?act_state, ?s), 
                    ActorStateHasSex(?act_state, ?sex_inst),
                    hasStringValue(?sex_inst, ?sex_value),
                    stringEqualIgnoreCase(?sex_value, "{val}"),
                        -> SexBelongsToGroup(?sex_inst, {name.lower()}_instance)
                    """
                )

        self.sex_groups = [gen.name.lower() for gen in self.ontology.Sex.subclasses()]
        self.sex_group_names = [gen.name for gen in self.ontology.Sex.subclasses()]

        logger.debug("Determine Gender | Rules Created successfully...")
        

    def __determine_acc_and_temp(self): 
        
        names = ["scarf_cold_rule", "hat_hot_rule", "glasses_normaltemp_rule"]
        temps = ["ColdTemp", "HotTemp","ModerateTemp"]
        accs = ["Scarf", "Hat", "Glasses"]

        for indx, _ in enumerate(names): 
            Imp().set_as_rule(
                f"""
                    ActorState(?act_state), validAt(?act_state, ?s),
                    ActorStateHasAccessories(?act_state, ?acc_inst),
                    hasStringValue(?acc_inst, ?acc_value),
                    stringEqualIgnoreCase(?acc_value, "{accs[indx]}"),
                    -> 
                    AccessoriesIncludeWearables(?acc_inst, {accs[indx].lower()}_instance), 
                """
            )


            Imp().set_as_rule(
                f"""
                ActorState(?act_state), validAt(?act_state, ?t), 
                ActorStateHasAccessories(?act_state, ?acc_inst), 
                ActorIsAffectedByTemp(?act_state, ?temp_inst), 
                AccessoriesIncludeWearables(?acc_inst, {accs[indx].lower()}_instance) 
                -> 
                TemperatureBelongsToGroup(?temp_inst, {temps[indx].lower()}_instance), 
                """

            )
    
        self.ontology.scarf_instance.DenotesTemperature = self.ontology.coldtemp_instance 
        self.ontology.hat_instance.DenotesTemperature = self.ontology.hottemp_instance 
        self.ontology.glasses_instance.DenotesTemperature = self.ontology.moderatetemp_instance
        self.temp_groups = [gen.name.lower() for gen in self.ontology.WeatherCondition.subclasses()]
        self.temp_group_names = [gen.name for gen in self.ontology.WeatherCondition.subclasses()]


    def find_threshold_profile_rules(self): 

        if not self.age_group_names or not self.age_groups: 
            logger.debug("Age Groups are not Defined") 
            return 

        if not self.sex_group_names or not self.sex_groups: 
            logger.debug("Sex Groups are not Defined") 
            return 

        if not self.temp_group_names or not self.temp_groups:
            logger.debug("Temp Groups are not Defined") 
            return 

        rules = [] 
        for i,age_group in enumerate(self.age_group_names): 
            age = self.age_groups[i] 

            for jj,sex_group in enumerate(self.sex_group_names): 
                sex = self.sex_groups[jj] 

                for tt, temp_group in enumerate(self.temp_group_names): 
                    temp = self.temp_groups[tt] 

                    if "temp" in temp: temp = temp.replace("temp", "")

                    if "cold" in temp: 
                        access =  "coldtemp_instance"
                    elif "hot" in temp: 
                        access = "hottemp_instance"
                    else: 
                        access = "moderatetemp_instance" 

                    Imp().set_as_rule(
                            f"""
                            ActorState(?act_state), 
                            ActorStateHasAge(?act_state, ?age_inst), AgeBelongsToGroup(?age_inst, {age}_instance),  
                            ActorStateHasSex(?act_state, ?sex_inst), SexBelongsToGroup(?sex_inst, {sex}_instance), 
                            ActorIsAffectedByTemp(?act_state, ?temp_inst), TemperatureBelongsToGroup(?temp_inst, {access}), 
                            -> StateHasThresholdProfile(?act_state, tp_{age}_{sex}_{temp}) 
                        """
                    )


    def __determine_thresholds_profile(self):
        thr_values = capture_thr_values_from_individuals(self.ontology) 
        parse_thr_profiles(self.ontology, thr_values) 
        self.find_threshold_profile_rules()
        

    def __determine_HR(self):
        set_up_HR_rules()

        
    def __determine_HRV(self): 
        set_up_HRV_rules()

          
    def __determine_RR(self):
        set_up_RR_rules()
                   

    def __determine_spo2(self): 
        set_up_SpO2_rules()
        
                
    def __determine_drowsiness(self): 
        set_up_Drowsiness_rules()


    def __determine_ftg_att_unr(self):
        single_attribute_pattern_classes(self.ontology)


    def __determine_eye_mouth_state(self):
        eye_mouth_state_rules()




    def set_up_trends(self):  
        # self.create_instances('CurrentReading')
        # self.create_instances('PreviousReading') 
        ph_factors = ["HR", "HRV", "RR"]
        for ph in ph_factors:
            for sub in getattr(self.ontology,ph).subclasses(): 
                sub = sub.name
                curr_state = Imp() 
                state = sub.split(ph)[0]
                state = state[:-1]
                curr_state.set_as_rule(
                    f"""
                    {ph}({ph.lower()}_instance),
                    {ph}is({ph.lower()}_instance,?sub_instance),
                    {sub}(?sub_instance),
                    CurrentReading(?curr_reading), 
                    PreviousReading(?previous) -> CurrentHas{ph}Trend(?curr_reading, ?sub_instance), CurrentReadingBecomesPrevious(?curr_reading, ?previous)
                    """
                )
            

    def connect_actor_state_to_values(self, actor_state, phy_vocab, actor_vocab, label_inst):
        
        actor_state.ActorStateHasPhysiologicalState.append(phy_vocab['hr'])
        actor_state.ActorStateHasPhysiologicalState.append(phy_vocab['hrv'])
        actor_state.ActorStateHasPhysiologicalState.append(phy_vocab['rr'])
        actor_state.ActorStateHasPhysiologicalState.append(phy_vocab['spo2'])
        actor_state.ActorStateHasPhysiologicalState.append(phy_vocab['drowsiness'])

        actor_state.ActorStateHasAge = actor_vocab['age']
        actor_state.ActorStateHasSex = actor_vocab['sex']
        actor_state.ActorStateHasCharacteristics.append(actor_vocab['demographic']) 
        actor_state.ActorStateHasCharacteristics.append(actor_vocab['facecharacteristics']) 
        actor_state.ActorStateHasAccessories = actor_vocab['accessories']
        actor_state.ActorIsAffectedByTemp = actor_vocab['temp']

        actor_state.ActorHasEyeState = actor_vocab['eye_state'] 
        actor_state.ActorHasMouthState = actor_vocab['mouth_state']
        actor_state.ActorIsTargetedByLabel = label_inst 

        logger.debug(f"the Actor State Characteristics Voc {actor_vocab}")
    

    def generate_all_nece_instances(self): 
        
        # The categories for HR
        for sub in self.ontology.HR.subclasses(): 
            self.create_instances(sub.name)

        # The categories for HRV
        for sub in self.ontology.HRV.subclasses(): 
            self.create_instances(sub.name)

        # The categories for RR 
        for sub in self.ontology.RR.subclasses(): 
            self.create_instances(sub.name)

        # The categories for RR 
        for sub in self.ontology.SpO2.subclasses(): 
            self.create_instances(sub.name)

        # The categories for drowsiness 
        for sub in self.ontology.Drowsiness.subclasses():
            self.create_instances(sub.name)

        # The categories for Fatigue 
        for sub in self.ontology.Fatigue.subclasses(): 
            self.create_instances(sub.name)

        # The categories for Attention 
        for sub in self.ontology.AttentionLevels.subclasses(): 
            self.create_instances(sub.name)

        # The categories for Unresponsiveness 
        for sub in self.ontology.Unresponsiveness.subclasses(): 
            self.create_instances(sub.name)

        # The categories for EyeState 
        for sub in self.ontology.EyeState.subclasses(): 
            self.create_instances(sub.name)

        # The categories for MouthState
        for sub in self.ontology.MouthState.subclasses(): 
            self.create_instances(sub.name)

        # The categories Accessories
        for sub in self.ontology.Accessories.subclasses(): 
            self.create_instances(sub.name)

        # The categories for Temperature 
        self.create_instances("WeatherCondition") 
        wht_class = getattr(self.ontology, "WeatherCondition")
        for wth in wht_class.subclasses(): 
            self.create_instances(wth.name) 

        # The categories for Temporal Context 
        self.create_instances("TemporalContext") 
        temp_class = getattr(self.ontology, "TemporalContext")
        for temp in temp_class.subclasses(): 
            self.create_instances(temp.name) 

        # The categories for biologial sex 
        for sub in self.ontology.Sex.subclasses(): 
            self.create_instances(sub.name)

        # The categories for Age 
        for sub in self.ontology.Age.subclasses():
            self.create_instances(sub.name)
                

    def re_create_indi(self, ts_iso:str, unique=None, regenerate=True): 
        # Regenerate these individuals per State 
        self.create_instances("HR", ts_iso=ts_iso, unique=unique, regenerate=regenerate)
        self.create_instances("HRV", ts_iso=ts_iso, unique=unique, regenerate=regenerate)
        self.create_instances("RR", ts_iso=ts_iso, unique=unique, regenerate=regenerate)
        self.create_instances("SpO2", ts_iso=ts_iso, unique=unique, regenerate=regenerate)
        self.create_instances("Drowsiness", ts_iso=ts_iso, unique=unique, regenerate=regenerate)
        # self.create_instances("Fatigue", ts_iso=ts_iso, unique=unique, regenerate=regenerate)
        # self.create_instances("AttentionLevels", ts_iso=ts_iso, unique=unique, regenerate=regenerate)
        # self.create_instances("Unresponsiveness", ts_iso=ts_iso, unique=unique, regenerate=regenerate)
        self.create_instances("EyeState", ts_iso=ts_iso, unique=unique, regenerate=regenerate)
        self.create_instances("MouthState", ts_iso=ts_iso, unique=unique, regenerate=regenerate)
        self.create_instances("Accessories", ts_iso=ts_iso, unique=unique, regenerate=regenerate)
        self.create_instances("Sex", ts_iso=ts_iso, unique=unique, regenerate=regenerate)
        self.create_instances("Age", ts_iso=ts_iso, unique=unique, regenerate=regenerate)
        self.create_instances("Demographic", ts_iso=ts_iso, unique=unique, regenerate=regenerate)
        self.create_instances("FaceCharacteristics", ts_iso=ts_iso, unique=unique, regenerate=regenerate)
        self.create_instances("Labels",ts_iso=ts_iso, unique=unique, regenerate=regenerate)


    def set_up_rules(self): 

        with StepContext(name="Preprocess_Temp_Age_Gender", catch=(RuntimeError,)):
            self.__determine_age()
            self.__determine_gender()
            self.__determine_acc_and_temp()

        with StepContext(name="Threshold_Profiles", catch=(RuntimeError,)): 
            self.__determine_thresholds_profile()

        with StepContext(name="HR|HRV|RR|SPO2|Drowsiness", catch=(RuntimeError, )): 
            self.__determine_HR()
            self.__determine_HRV() 
            self.__determine_RR() 
            self.__determine_spo2() 
            self.__determine_drowsiness()
        
        with StepContext(name="Create All GCI statements", catch=(RuntimeError, Exception)): 
            self.__determine_ftg_att_unr()

        with StepContext(name="Define Fatigue Rules", catch=(RuntimeError,)):
            self.__determine_eye_mouth_state()


    def create_labels(self, actor, filepath:str,  batch_size:int): 
        """
        This function creates a label, describing the actor based on the results 
        of the SWRL rules in the ontology. Requires reasoner to previously have 
        been synchronized, otherwise the last changes will not be reflected in the label.
        
        Args:
            filepath (str): The filepath to the ontology file.
            index (int): The index of the ontology file.
        """

        act_states = actor.ActorhasState[:-1]
        
        if len(act_states) != batch_size: 
            raise RuntimeError("The batch size and the number of actor states is different")
        
        chars = { pos:val.ActorStateHasCharacteristics for pos, val in enumerate(act_states)}
        phys = { pos:val.ActorStateHasPhysiologicalState for pos, val in enumerate(act_states)}
        
        data = defaultdict() 

        for ind, act_st in enumerate(act_states): 
            data[act_st] = {}
            for char in chars[ind]:
                data[act_st][char.name.split('_')[0]] = char.hasStringValue[0] if char.name != "age_instance" else char.hasAgeValue[0] 

            for phy in phys[ind]: 
                    data[act_st][phy.name.split('_')[0]] = phy.hasNumericalValue[0] 

            data[act_st]['age'] = act_st.ActorStateHasAge.AgeBelongsToGroup.name.split("_")[0] 
            data[act_st]['sex'] = act_st.ActorStateHasSex.SexBelongsToGroup.name.split("_")[0] 
            data[act_st]['accessories'] = act_st.ActorStateHasAccessories.AccessoriesIncludeWearables.name.split("_")[0] 
            try: 

                data[act_st]['fatigue'] = act_st.ActorStateHasFatigue.name.split("_")[0]
            except: 
                pdb.set_trace()
            try:
                data[act_st]['attention'] = act_st.ActorStateHasAttention.name.split("_")[0]
            except: 
                print("Attention") 
                pdb.set_trace()
            try: 
                data[act_st]['unresponsiveness'] = act_st.ActorStateHasUnresponsiveness.name.split("_")[0]
            except:
                print("Unresponsiveness")
                pdb.set_trace()
            data[act_st]['driver_id'] = act_st.name

            try: 
                eye_inst = act_st.ActorHasEyeState.EyeStateIs[0].name.split("_")[0] 
            except: 
                logger.warn("WARNING: Eye instance for this actor state could not be determined") 
                logger.debug(f"The actorState has {data[act_st]['fatigue']} | {data[act_st]['attention']} | {data[act_st]['unresponsiveness']}") 
                eye_inst = "openstate" 
            data[act_st]['eye_state']  = eye_inst.replace("state", "")
            
            try: 

                data[act_st]['mouth_state'] = act_st.ActorHasMouthState.MouthStateIs[0].name.split("_")[0]
            except: 
                logger.warn("WARNING: Mouth instance for this actor state could not be determined") 
                logger.debug(f"The actorState has {data[act_st]['fatigue']} | {data[act_st]['attention']} | {data[act_st]['unresponsiveness']}") 
                data[act_st]['mouth_state'] = "open"  

            actor_data = {
                "prompt_details": {
                    "seed":random.randint(1,1000000), 
                    "steps": random.randint(1,100), 
                    "prompt":"Lorem ipsum...", 
                    "response":"Lorem ipsum...",
                    "view_point":"front", 
                    "object_name": "person", 
                    "time_of_day":"morning", 
                    "sky_condition":"clear", 
                    "weather_condition":"sunny",
                },

                "label":{
                    "actor_id":data[act_st]['driver_id'] ,
                    "eye_inst": data[act_st]['eye_state'],
                    "mouth_inst":data[act_st]['mouth_state'],
                    "age":data[act_st]["age"], 
                    "face":data[act_st]["facecharacteristics"], 
                    "sex":data[act_st]['sex'], 
                    "demographic": data[act_st]["demographic"], 
                    "accessories": data[act_st]['accessories'], 
                    "fatigue":data[act_st]['fatigue'], 
                    "attention":data[act_st]['attention'], 
                    "unresponsiveness":data[act_st]['unresponsiveness'],
                    "bounding_box":"...", 
                    "bounding_polygon":"...", 
                }
            } 

            if not os.path.exists(filepath): 
                os.mkdir(filepath)

            json_file = filepath + f"/label_{ind}.json"
            with self.ontology: 
                label = act_st.ActorIsTargetedByLabel
                with open(json_file, "w") as f:
                    json.dump(actor_data, f, indent=4)
                label.hasDescription.append(json.dumps(actor_data))
                

            logger.debug(f"Label for Actor {actor.name} created succesfully")
        
        return data


    def clear_obs(self, obs): 
        with self.ontology: 
            obs.hasAge.clear()
            obs.hasSex.clear()
            obs.hasDemographic.clear()
            obs.hasAccessories.clear()
            obs.hasFaceCharacteristics.clear()
            obs.ObsIsDividedIntoActor.clear()
            obs.ObsIsDividedIntoPhS.clear()


    def remove_prev_values(self, ts_iso_dates, actor_states): 
 
        with self.ontology: 
            for identifier in ts_iso_dates: 
                for individual in list(self.ontology.individuals()): 
                    if identifier in individual.name or  individual in actor_states: 
                        destroy_entity(individual) 



