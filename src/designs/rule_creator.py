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
from rdflib import Graph

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
                ("Young", "lessThanOrEqual", 18),
                ("Middle-Aged", "greaterThanOrEqual", 18, "lessThanOrEqual", 65),
                ("Elderly", "greaterThan", 65)
            ]

            for rule in age_rules:                
                Imp().set_as_rule(
                    f"""
                    ActorState(?act_state), validAt(?act_state, ?s),
                    ActorStateHasAge(?act_state, ?age_inst),
                    hasAgeValue(?age_inst, ?age_value),
                    {rule[1]}(?age_value, {rule[2]})
                    {f', {rule[3]}(?age_value, {rule[4]})' if len(rule) > 3 else ''},

                        -> AgeBelongsToGroup(?age_inst, {rule[0].lower()}_instance)
                    """
                )

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
            
    
    # def trend_analysis(self): 
    #     rule_name = "trend_analysis" 
    #     if not  has_rule_named(self.ontology, name=rule_name): 
    #         Imp(rule_name).set_as_rule()
    #

    def connect_actor_state_to_values(self, actor_state, phy_vocab, actor_vocab):
        
        # pdb.set_trace()
        # if not getattr(actor_state, "ActorStateHasPhysiologicalState") or \
        #     not getattr(actor_state, "ActorStateHasCharacteristics"): 
        #         logger.debug("Not initialized correctly for actor") 
        #         raise RuntimeError("Actor initialized incorrectly")
        
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



    def determine_trends(self):

        current_trend = self.ontology.CurrentReading.instances()[0] # Get the currenttreading_instance 
        prev_trend = self.ontology.PreviousReading.instances()[0] 
        level = ["high", "low", "moderate","very_low"]
        rank = {v:r for r,v in enumerate(level)} 
        
        logger.debug(current_trend.hasHRRank)
        logger.debug(current_trend.hasHRVRank)
        logger.debug(current_trend.hasRRRank)
        logger.debug(prev_trend.hasHRRank)
        logger.debug(prev_trend.hasHRVRank)        
        logger.debug(prev_trend.hasRRRank)
        
        # Access the individual HR,HRV, RR instances 
        hr_inst = current_trend.CurrentHasHRTrend.pop(0) 
        hrv_inst = current_trend.CurrentHasHRVTrend.pop(0)
        rr_inst = current_trend.CurrentHasRRTrend.pop(0)

        # List of individuals accessed through temporal Context 
        comp = [hr_inst, hrv_inst, rr_inst] 

        # Get the level based on the name of each instance (high, low, moderate, very_low)
        for individual in comp : 
            if "very_low" in individual.name:
                level_name = individual.name.split("_")[0:2]
                level_name = "_".join(level_name)
                name_ph = individual.name.split("_")[2]
            else: 
                level_name = individual.name.split("_")[0] 
                name_ph = individual.name.split("_")[1] 

            rank_level = rank[level_name] 
            has_temporal_value = getattr(current_trend, f"has{name_ph.upper()}Rank")

            if len(has_temporal_value)==0 : 
                has_temporal_value.append(rank_level)

            else: 
                property_prev = getattr(prev_trend, f"has{name_ph.upper()}Rank")

                if len(property_prev) == 0 : 
                    property_prev.append(has_temporal_value.pop(0))
                else:
                    property_prev[0] = has_temporal_value.pop(0)
                has_temporal_value.append(rank_level)

        logger.debug("Determine Trends | Finished setting up trends...")


    def set_up_rules(self): 

        # with StepContext(name="Connect_State_To_Values", catch=(RuntimeError,)):
        #     self.connect_actor_to_values()

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


        # self.set_up_trends()
        # self.update_trends()

        # self.determine_trends() 



    def create_label(self, actor, filepath:str,  index:int): 
        """
        This function creates a label, describing the actor based on the results 
        of the SWRL rules in the ontology. Requires reasoner to previously have 
        been synchronized, otherwise the last changes will not be reflected in the label.
        
        Args:
            filepath (str): The filepath to the ontology file.
            index (int): The index of the ontology file.
        """

        
        act_st = actor.ActorhasState[0]
        chars = act_st.ActorStateHasCharacteristics
        phys = act_st.ActorStateHasPhysiologicalState 
        data = defaultdict() 

        for char in chars: 
            data[char.name] = char.hasStringValue[0] if char.name != "age_inst" else char.hasAgeValue[0] 
        
        for phy in phys: 
            data[phy.name] = phy.hasNumericalValue[0]

        data['fatigue'] = act_st.ActorStateHasFatigue[0].FatigueIs[0].name.split("_")[0]
        data['attention'] = act_st.ActorStateHasAttention[0].AttentionIs[0].name.split("_")[0]
        data['?unresp_inst'] = act_st.ActorStateHasUnresponsiveness[0].UnresponsiveIs[0].name.split("_")[0]
        data['driver_id'] = act_st.name
        eye_inst = act_st.ActorHasEyeState[0].EyeStateIs[0].name.split("_")[0] 
        eye_inst = eye_inst.replace("state", "")
        mouth_inst = act_st.ActorHasMouthState[0].MouthStateIs[0].name.split("_")[0]

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
                "actor_id": data['driver_id'],
                "?eye_inst": eye_inst,
                "?mouth_inst":mouth_inst,
                "age":data["age_inst"], 
                "face":data["facecharacteristics_instance"], 
                "sex":data["sex_inst"], 
                "demographic": data["demographic_instance"], 
                "accessories": data["acc_inst"], 
                "fatigue":data['fatigue'], 
                "attention":data['attention'], 
                "unresponsive":data['?unresp_inst'],
                "bounding_box":"...", 
                "bounding_polygon":"...", 
            }
        } 

        json_file = filepath + f"/label_{index}.json"
        with self.ontology: 
            label = self.ontology.Label.instances()[0]
            with open(json_file, "w") as f:
                json.dump(actor_data, f, indent=4)
            label.hasDescription.append(json.dumps(actor_data))
            label.LabelTargetsActor = [actor]

        logger.debug(f"Label for Actor {actor.name} created succesfully")
        

    def clear_obs(self, obs): 
        with self.ontology: 
            obs.hasAge.clear()
            obs.hasSex.clear()
            obs.hasDemographic.clear()
            obs.hasAccessories.clear()
            obs.hasFaceCharacteristics.clear()
            obs.ObsIsDividedIntoActor.clear()
            obs.ObsIsDividedIntoPhS.clear()


    def remove_prev_values(self, obs, actor): 

        with self.ontology: 

            # Remove the values from the observations
            obs.hasAge = [] 
            obs.hasAccessories = [] 
            obs.hasSex = [] 
            obs.hasDemographic = []
            obs.hasFaceCharacteristics = []
            obs.ObsIsDividedIntoActor = [] 
            obs.ObsIsDividedIntoPhS = []

            # Remove the values from the main instances for the physical properties
            numerical_indi = ['hr_inst', 'hrv_inst', 'rr_inst', 'spo2_inst', 'dr_inst'] 
            for indi in numerical_indi: 
                individual = getattr(self.ontology, indi) 
                individual.PhysiologicalStateDescribesActor = []
                individual.PhSFromObservations = [] 
                
                if "hr_inst" == indi: 
                    individual.HRis = [] 
                elif "hrv_inst" == indi: 
                    individual.HRVis = [] 
                elif "rr_inst" == indi: 
                    individual.RRis = [] 
                elif "spo2_inst" == indi: 
                    individual.SpO2is = [] 
                elif "dr_inst" == indi: 
                    individual.DrowsinessIs = [] 

            string_indi = ['acc_inst', 'demographic_instance', 'sex_inst', 'facecharacteristics_instance']
            for indi in string_indi:
                individual = getattr(self.ontology, indi)
                individual.hasStringValue = []

            age_indi = getattr(self.ontology, "age_inst")
            age_indi.hasAgeValue = []
            for group in self.ontology.Age.instances(): 
                if group.name != "age_inst": 
                    group.GroupHasAge = [] 
            
            sex_indi = getattr(self.ontology, "sex_inst") 
            for group in self.ontology.Sex.instances(): 
                if group.name != sex_indi.name: 
                    group.SexBelongsToPerson = [] 

            actor.ActorHasState = []

            fatigue_indi = getattr(self.ontology, "?fatigue_inst") 
            fatigue_indi.FatigueIs = [] 

            attention = getattr(self.ontology, "?attention_inst") 
            attention.AttentionIs = [] 

            unresponsive = getattr(self.ontology, "?unresp_inst") 
            unresponsive.UnresponsiveIs = [] 

            eyestate = getattr(self.ontology, "?eye_inst") 
            eyestate.EyeStateIs = [] 

            mouthstate = getattr(self.ontology, "?mouth_inst")
            mouthstate.MouthStateIs = [] 

            label = self.ontology.Label.instances()[0]
            label.hasDescription = [] 
            label.LabelTargetsActor = []


    def update_trends(self): 
        with self.ontology: 
            current_trend = self.ontology.CurrentReading.instances()[0] 
            for property in current_trend.get_properties(): 
                name_for_prev = property.name.replace("Current", "Previous")
                if "Becomes" in property.name:
                    continue
                rule = Imp() 
                rule.set_as_rule(
                    f"""
                    CurrentReading(?current), 
                    {property.name}(?current, ?reading), 
                    CurrentReadingBecomesPrevious(?current, ?previous),
                    PreviousReading(?previous) -> {name_for_prev}(?previous, ?reading)
                    """
                )





