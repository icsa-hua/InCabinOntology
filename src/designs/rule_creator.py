from src.tools.common import *
from src.tools.appraisal import StepContext 
from src.tools.logger import get_logger

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


    # Don't use this UNLESS completely necessary. Keep observations outside of logical reasoning (only provenance)
    def observations_to_classes(self, obs_state=None, cls_name="", property_name=""):
        """
        This function connects the observation to every class corresponding to a column in the 
        dataset. It uses the object property name to connect to the Actor or Physiological State class. 
        Args:
            obs (Observation): The observation to connect to the class.
            cls_name (str): The name of the class to connect to (Actor or Physiological State).
            property_name (str): The name of the property to connect to.
        """

        if obs_state is None: 
            logger.error("The observation data is empty...")
            exit(1) 
        
        # Get the subclasses for the desired class. 
        phs_class = next(cls for cls in self.ontology.classes() if cls.name.strip() == cls_name)

        # Check the property and connect the observation to the class.
        for prop in obs_state.get_properties():

            try: 
                name_prop = prop.name.split('has')[1]
            except: 
                logger.debug(f"Property {prop} already exists in ontology...")
                continue

            name_prop = "Drowsiness" if name_prop == "Drowsy" else name_prop

            # Flag is raised when Physiological State class iterates through subclasses not in the dataset.
            flag = [True for cls in phs_class.subclasses() if cls.name == name_prop]
    
            if not flag:
                logger.debug("Subclasses not in dataset...")
                continue

            # Connect Observation to each subclass 
            with self.ontology:
                # Instance of the subclass (e.g. HR, Accessories, ..., etc.)
                instance = self.create_instances(name_prop)
                
                # Check if instance was created.
                if instance is None:
                    logger.debug(f"Instance of {name_prop} was not created...")
                    continue
               
                # Define the SWRL rule for the property. 
                rule_name = f"{prop.name}_{name_prop}" 

                if not has_rule_named(self.ontology,name=rule_name):  
                    rule = Imp(rule_name, namespace=self.ontology) 

                    rule.set_as_rule(
                        f"""
                            Observations(?obs_ind),
                            {prop.name}(?obs_ind,?Val),
                            {name_prop}(?{name_prop.lower()})
                            -> {property_name}(?obs_ind,?{name_prop.lower()})
                        """
                    )
                    logger.debug(f"[checked] Observation rulle with name {rule_name} added")
                else: 
                    logger.debug(f"[!] Observation rule with name {rule_name} already exists")

        return True

    
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
                # self.create_instances(rule[0])
                rule_name = f"{rule[0]}_group_rule"
                
                if not has_rule_named(self.ontology, name=rule_name): 
                    Imp(rule_name).set_as_rule(
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
                rule_name =  f"{name.lower()}_rule"
                if not has_rule_named(self.ontology, name=rule_name):

                    Imp(rule_name).set_as_rule(
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

        for indx, name in enumerate(names): 
            if not  has_rule_named(self.ontology, name=name): 
                Imp(name).set_as_rule(
                    f"""
                        ActorState(?act_state), validAt(?act_state, ?s),
                        ActorStateHasAccessories(?act_state, ?acc_inst),
                        hasStringValue(?acc_inst, ?acc_value),
                        stringEqualIgnoreCase(?acc_value, "{accs[indx]}"),
                        -> 
                        AccessoriesIncludeWearables(?acc_inst, {accs[indx].lower()}_instance), 
                    """
                )

            if not has_rule_named(self.ontology, name=f"{name}_temp"): 
                Imp(f"{name}_temp").set_as_rule(
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

                    rule_name = f"profile_{age}_{sex}_{temp}"

                    if "temp" in temp: temp = temp.replace("temp", "")

                    if not has_rule_named(self.ontology, name=rule_name): 
                        rules.append(rule_name)
                        if "cold" in temp: 
                            access =  "coldtemp_instance"
                        elif "hot" in temp: 
                            access = "hottemp_instance"
                        else: 
                            access = "moderatetemp_instance" 

                        Imp(rule_name).set_as_rule(
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
        """
        This function creates the rules to categorize the HR of the actor into
        threshold ranges: 
        * Low 
        * Slightly Low 
        * Moderate (Normal) 
        * High 

        These threshold ranges change based on the Age group of the actor.
        """

        # self.create_instances("Very_Low_HR") 
        if not has_rule_named(onto=self.ontology, name="very_low_hr_rule"): 
            Imp("very_low_hr_rule").set_as_rule(
                f""" 
                ActorState(?act_st), validAt(?act_st, ?t),
                StateHasThresholdProfile(?act_st, ?tp), 
                ActorStateHasPhysiologicalState(?act_st, ?hr_inst), HR(?hr_inst), 
                hasNumericalValue(?hr_inst, ?value), phyValidAt(?hr_inst, ?phy_t), 
                appliesHRLow(?tp, ?hr_low), hasThrValue(?hr_low, ?low), 
                greaterThanOrEqual(?value, 0), 
                lessThan(?value, ?low), 
                stringEqualIgnoreCase(?t, ?phy_t),
                Very_Low_HR(?vrl_hr)
                ->  HRis(?hr_inst, ?vrl_hr) 
                """
            )

        # self.create_instances("Low_HR") 
        if not has_rule_named(onto=self.ontology, name="low_hr_rule"): 
            Imp("low_hr_rule").set_as_rule(
                 f""" 
                ActorState(?act_st), validAt(?act_st, ?t), StateHasThresholdProfile(?act_st, ?tp), 
                ActorStateHasPhysiologicalState(?act_st, ?hr_inst), HR(?hr_inst), 
                hasNumericalValue(?hr_inst, ?value), phyValidAt(?hr_inst, ?phy_t), 
                appliesHRLow(?tp, ?hr_low), hasThrValue(?hr_low, ?low), 
                appliesHRModerate(?tp, ?hr_mod), hasThrValue(?hr_mod, ?mod), 
                greaterThanOrEqual(?value, ?low),
                lessThan(?value, ?mod), 
                stringEqualIgnoreCase(?t, ?phy_t),
                Low_HR(?l_hr)
                ->  HRis(?hr_inst, ?l_hr) 
                """
            )

        # self.create_instances("Moderate_HR") 
        if not has_rule_named(onto=self.ontology, name="moderate_hr_rule"): 
            Imp("moderate_hr_rule").set_as_rule(
                f""" 
                ActorState(?act_st), validAt(?act_st,?t), StateHasThresholdProfile(?act_st, ?tp), 
                ActorStateHasPhysiologicalState(?act_st, ?hr_inst), HR(?hr_inst), 
                hasNumericalValue(?hr_inst, ?value), phyValidAt(?hr_inst, ?phy_t), 
                appliesHRModerate(?tp, ?hr_mod), hasThrValue(?hr_mod, ?mod), 
                appliesHRHigh(?tp, ?hr_high), hasThrValue(?hr_high, ?high), 
                greaterThanOrEqual(?value, ?mod),
                lessThan(?value, ?high), 
                stringEqualIgnoreCase(?t, ?phy_t),
                Moderate_HR(?mod_hr)
                -> HRis(?hr_inst, ?mod_hr) 
                """
            )

        # self.create_instances("High_HR") 
        if not has_rule_named(onto=self.ontology, name="high_hr_rule"): 
            Imp("high_hr_rule").set_as_rule(
                f""" 
                ActorState(?act_st),  validAt(?act_st, ?t), StateHasThresholdProfile(?act_st, ?tp), 
                ActorStateHasPhysiologicalState(?act_st, ?hr_inst), HR(?hr_inst), 
                hasNumericalValue(?hr_inst, ?value), phyValidAt(?hr_inst, ?phy_t), 
                appliesHRHigh(?tp, ?hr_high), hasThrValue(?hr_high, ?high), 
                greaterThanOrEqual(?value, ?high),
                lessThan(?value, 250), 
                stringEqualIgnoreCase(?t, ?phy_t),
                High_HR(?high_hr)
                -> HRis(?hr_inst, ?high_hr) 
                """
            )

        
    def __determine_HRV(self): 
        """
        This function creates the rules to categorize the HRV of the actor into
        threshold ranges: 
        * Very Low 
        * Low 
        * Moderate (Normal) 
        * High 

        These threshold ranges change based on the Age group of the actor.
        """
      
        # self.create_instances("Very_Low_HRV") 
        if not has_rule_named(onto=self.ontology, name="very_low_hrv_rule"): 
            Imp("very_low_hrv_rule").set_as_rule(
                f"""
                ActorState(?act_st), validAt(?act_st, ?t), StateHasThresholdProfile(?act_st, ?tp), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv_inst), HRV(?hrv_inst),
                hasNumericalValue(?hrv_inst, ?value), phyValidAt(?hrv_inst, ?phy_t), 
                appliesHRVLow(?tp, ?hrv_low), hasThrValue(?hrv_low, ?low), 
                greaterThanOrEqual(?value, 0), 
                lessThan(?value, ?low),
                stringEqualIgnoreCase(?t, ?phy_t),
                Very_Low_HRV(?vrl_hrv)
                -> HRVis(?hrv_inst, ?vrl_hrv)
                """
            )

        # self.create_instances("Low_HRV") 
        if not has_rule_named(onto=self.ontology, name="low_hrv_rule"): 
            Imp("low_hrv_rule").set_as_rule(
                f"""
                ActorState(?act_st),  validAt(?act_st, ?t), StateHasThresholdProfile(?act_st, ?tp), 
                ActorStateHasPhysiologicalState(?act_st,?hrv_inst), HRV(?hrv_inst), 
                hasNumericalValue(?hrv_inst, ?value), phyValidAt(?hrv_inst, ?phy_t), 
                appliesHRVLow(?tp, ?hrv_low), hasThrValue(?hrv_low, ?low), 
                appliesHRVModerate(?tp, ?hrv_mod), hasThrValue(?hrv_mod, ?mod), 
                greaterThanOrEqual(?value, ?low), 
                lessThan(?value, ?mod), 
                stringEqualIgnoreCase(?t, ?phy_t),
                Low_HRV(?l_hrv)
                -> HRVis(?hrv_inst, ?l_hrv)
                """
            )

        # self.create_instances("Moderate_HRV") 
        if not has_rule_named(onto=self.ontology, name="moderate_hrv_rule"): 
            Imp("moderate_hrv_rule").set_as_rule(
                """
                ActorState(?act_st),  validAt(?act_st, ?t), StateHasThresholdProfile(?act_st, ?tp), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv_inst), HRV(?hrv_inst), 
                hasNumericalValue(?hrv_inst, ?value), phyValidAt(?hrv_inst, ?phy_t), 
                appliesHRVModerate(?tp, ?hrv_mod), hasThrValue(?hrv_mod, ?mod), 
                appliesHRVHigh(?tp, ?hrv_high), hasThrValue(?hrv_high, ?high), 
                greaterThanOrEqual(?value, ?mod), 
                lessThan(?value, ?high),
                stringEqualIgnoreCase(?t, ?phy_t),
                Moderate_HRV(?mod_hrv)
                -> HRVis(?hrv_inst, ?mod_hrv)
                """
            )

        # self.create_instances("High_HRV")
        if not has_rule_named(onto=self.ontology, name="high_hrv_rule"): 
            Imp("high_hrv_rule").set_as_rule(
                f"""
                ActorState(?act_st), validAt(?act_st, ?t), StateHasThresholdProfile(?act_st, ?tp), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv_inst), HRV(?hrv_inst), 
                hasNumericalValue(?hrv_inst, ?value), phyValidAt(?hrv_inst, ?phy_t), 
                appliesHRVHigh(?tp, ?hrv_high), hasThrValue(?hrv_high, ?high), 
                greaterThanOrEqual(?value, ?high),
                lessThan(?value, 250), 
                stringEqualIgnoreCase(?t, ?phy_t),
                High_HRV(?high_hrv)
                -> HRVis(?hrv_inst, ?high_hrv)
                """
            )

          
    def __determine_RR(self):
        """
        This function creates the rules to categorize the RR of the actor into
        threshold ranges: 
        * Very Low 
        * Low 
        * Moderate (Normal) 
        * High 

        These threshold ranges change based on the Age group of the actor.
        """

        # self.create_instances("Very_Low_RR") 
        if not has_rule_named(onto=self.ontology, name="very_low_rr_rule"):
            Imp("very_low_rr_rule").set_as_rule(
                f"""
                ActorState(?act_st), validAt(?act_st, ?t), StateHasThresholdProfile(?act_st, ?tp), 
                ActorStateHasPhysiologicalState(?act_st, ?rr_inst), RR(?rr_inst), 
                hasNumericalValue(?rr_inst, ?value), phyValidAt(?rr_inst, ?phy_t), 
                appliesRRLow(?tp, ?rr_low), hasThrValue(?rr_low, ?low), 
                greaterThanOrEqual(?value, 0), 
                lessThan(?value, ?low), 
                stringEqualIgnoreCase(?t, ?phy_t),
                Very_Low_RR(?vrl_rr)
                ->  RRis(?rr_inst, ?vrl_rr) 
                """
            )

        # self.create_instances("Low_RR") 
        if not has_rule_named(onto=self.ontology, name="low_rr_rule"): 
             Imp("low_rr_rule").set_as_rule(
                f"""
                ActorState(?act_st), validAt(?act_st, ?t), StateHasThresholdProfile(?act_st, ?tp), 
                ActorStateHasPhysiologicalState(?act_st, ?rr_inst), RR(?rr_inst), 
                hasNumericalValue(?rr_inst, ?value), phyValidAt(?rr_inst, ?phy_t), 
                appliesRRLow(?tp, ?rr_low), hasThrValue(?rr_low, ?low), 
                appliesRRModerate(?tp, ?rr_mod), hasThrValue(?rr_mod, ?mod), 
                greaterThanOrEqual(?value, ?low),
                lessThan(?value, ?mod), 
                stringEqualIgnoreCase(?t, ?phy_t),
                Low_RR(?l_rr)
                ->  RRis(?rr_inst, ?l_rr)
                """
             )
        
        # self.create_instances("Moderate_RR") 
        if not has_rule_named(onto=self.ontology, name="moderate_rr_rule"): 
             Imp("moderate_rr_rule").set_as_rule(
                f"""
                ActorState(?act_st), validAt(?act_st, ?t), StateHasThresholdProfile(?act_st, ?tp), 
                ActorStateHasPhysiologicalState(?act_st, ?rr_inst), RR(?rr_inst), 
                hasNumericalValue(?rr_inst, ?value), phyValidAt(?rr_inst, ?phy_t), 
                appliesRRModerate(?tp, ?rr_mod), hasThrValue(?rr_mod, ?mod), 
                appliesRRHigh(?tp, ?rr_high), hasThrValue(?rr_high, ?high), 
                greaterThanOrEqual(?value, ?mod),
                lessThan(?value, ?high), 
                stringEqualIgnoreCase(?t, ?phy_t),
                Moderate_RR(?mod_rr) 
                ->  RRis(?rr_inst, ?mod_rr)
                """
             )

        # self.create_instances("High_RR") 
        if not has_rule_named(onto=self.ontology, name="high_rr_rule"): 
             Imp("high_rr_rule").set_as_rule(
                f"""
                ActorState(?act_st), validAt(?act_st, ?t), StateHasThresholdProfile(?act_st, ?tp), 
                ActorStateHasPhysiologicalState(?act_st, ?rr_inst), RR(?rr_inst), 
                hasNumericalValue(?rr_inst, ?value), phyValidAt(?rr_inst, ?phy_t), 
                appliesRRHigh(?tp, ?rr_high), hasThrValue(?rr_high, ?high), 
                greaterThanOrEqual(?value, ?high),  
                lessThan(?value, 50), 
                stringEqualIgnoreCase(?t, ?phy_t),
                High_RR(?high_rr),
                ->  RRis(?rr_inst, ?high_rr)
                """
             )
                   

    def __determine_spo2(self): 
        """
        This function creates the rules to categorize the SPO2 of the actor into
        threshold ranges: 
        * Normal 
        * Slightly_Low
        * Critical

        These threshold ranges change based on the Age group of the actor.
        """

        # self.create_instances("Normal_SpO2") 
        if not has_rule_named(onto=self.ontology, name="normal_spo2_rule"): 
             Imp("normal_spo2_rule").set_as_rule(
                f"""
                ActorState(?act_st), validAt(?act_st, ?t), StateHasThresholdProfile(?act_st, ?tp), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2_inst), SpO2(?spo2_inst), 
                hasNumericalValue(?spo2_inst, ?value), phyValidAt(?spo2_inst, ?phy_t), 
                appliesSpO2High(?tp, ?spo2_high), hasThrValue(?spo2_high, ?high), 
                greaterThanOrEqual(?value, ?high),
                lessThanOrEqual(?value, 100), 
                stringEqualIgnoreCase(?t, ?phy_t),
                Normal_SpO2(?n_spo2) 
                ->  SpO2is(?spo2_inst, ?n_spo2)
                """
             )

        # self.create_instances("Low_SpO2") 
        if not has_rule_named(onto=self.ontology, name="low_spo2_rule"): 
             Imp("low_spo2_rule").set_as_rule(
                f"""
                ActorState(?act_st),validAt(?act_st, ?t), StateHasThresholdProfile(?act_st, ?tp), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2_inst), SpO2(?spo2_inst), 
                hasNumericalValue(?spo2_inst, ?value), phyValidAt(?spo2_inst, ?phy_t), 
                appliesSpO2High(?tp, ?spo2_high), hasThrValue(?spo2_high, ?high), 
                appliesSpO2Moderate(?tp, ?spo2_mod), hasThrValue(?spo2_mod, ?mod), 
                greaterThanOrEqual(?value, ?mod),
                lessThan(?value, ?high), 
                stringEqualIgnoreCase(?t, ?phy_t),
                Low_SpO2(?l_spo2) 
                ->  SpO2is(?spo2_inst, ?l_spo2)
                """
             )


        # self.create_instances("Critical_SpO2") 
        if not has_rule_named(onto=self.ontology, name="critical_spo2_rule"): 
             Imp("critical_spo2_rule").set_as_rule(
                f"""
                ActorState(?act_st),validAt(?act_st, ?t), StateHasThresholdProfile(?act_st, ?tp), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2_inst), SpO2(?spo2_inst), 
                hasNumericalValue(?spo2_inst, ?value), phyValidAt(?spo2_inst, ?phy_t), 
                appliesSpO2Moderate(?tp, ?spo2_mod), hasThrValue(?spo2_mod, ?mod),
                appliesSpO2Low(?tp, ?spo2_low), hasThrValue(?spo2_low, ?low),
                greaterThanOrEqual(?value, ?low),
                lessThan(?value, ?mod),  
                stringEqualIgnoreCase(?t, ?phy_t),
                Critical_SpO2(?c_spo2) 
                -> SpO2is(?spo2_inst, ?c_spo2)
                """
             )
          
        if not has_rule_named(onto=self.ontology, name="critical_spo2_rule_2"): 
             Imp("critical_spo2_rule").set_as_rule(
                f"""
                ActorState(?act_st),validAt(?act_st, ?t), StateHasThresholdProfile(?act_st, ?tp), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2_inst), SpO2(?spo2_inst), 
                hasNumericalValue(?spo2_inst, ?value), phyValidAt(?spo2_inst, ?phy_t), 
                appliesSpO2Low(?tp, ?spo2_low), hasThrValue(?spo2_low, ?low),
                lessThan(?value, ?low),  
                stringEqualIgnoreCase(?t, ?phy_t),
                Critical_SpO2(?c_spo2) 
                -> SpO2is(?spo2_inst, ?c_spo2)
                """
             )
                
    def __determine_drowsiness(self): 
        """
        This function creates the rules to categorize the Drowsiness of the actor into
        threshold ranges based on Karolinska Sleep Scale (KSS)
        * Level_3 (actor is awake) 
        * Level_5 (actor is neither asleep or awake)
        * Level_7 (actor is asleep with no effor of waking up)
        * Level_9 (actor is asleep with effort of waking up)
        """

        # self.create_instances('Level_3_KSS')

        rule_name = "level_3_kss_rule" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_state), validAt(?act_state, ?t),
                ActorStateHasPhysiologicalState(?act_state, ?dr_inst),Drowsiness(?dr_inst), 
                hasNumericalValue(?dr_inst, ?v), phyValidAt(?dr_inst, ?phy_t), 
                lessThanOrEqual(?v, 1),
                greaterThan(?v, 0), 
                stringEqualIgnoreCase(?t, ?phy_t)
                -> DrowsinessIs(?dr_inst, level_3_kss_instance) 
                """
            )

        # self.create_instances('Level_5_KSS')

        rule_name = "level_5_kss_rule" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_state), validAt(?act_state, ?t),
                ActorStateHasPhysiologicalState(?act_state, ?dr_inst),Drowsiness(?dr_inst), 
                hasNumericalValue(?dr_inst, ?v), phyValidAt(?dr_inst, ?phy_t), 
                lessThanOrEqual(?v, 2), 
                greaterThan(?v, 1), 
                stringEqualIgnoreCase(?t, ?phy_t)
                ->  DrowsinessIs(?dr_inst, level_5_kss_instance) 
                """
            )

        # self.create_instances('Level_7_KSS')

        rule_name = "level_7_kss_rule" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_state), validAt(?act_state, ?t),
                ActorStateHasPhysiologicalState(?act_state, ?dr_inst),Drowsiness(?dr_inst), 
                hasNumericalValue(?dr_inst, ?v), phyValidAt(?dr_inst, ?phy_t),
                lessThanOrEqual(?v, 3), 
                greaterThan(?v, 2), 
                stringEqualIgnoreCase(?t, ?phy_t)
                -> DrowsinessIs(?dr_inst, level_7_kss_instance) 
                """
            )

        # self.create_instances('Level_9_KSS')

        rule_name = "level_9_kss_rule" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_state), validAt(?act_state, ?t),
                ActorStateHasPhysiologicalState(?act_state, ?dr_inst),Drowsiness(?dr_inst), 
                hasNumericalValue(?dr_inst, ?v), phyValidAt(?dr_inst, ?phy_t),
                lessThanOrEqual(?v, 4),
                greaterThan(?v, 3), 
                stringEqualIgnoreCase(?t, ?phy_t)
                ->  DrowsinessIs(?dr_inst, level_9_kss_instance) 
                """
            )


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

        # DON'T require LIST casting since these are Functional 
        actor_state.ActorStateHasFatigue = phy_vocab['fatigue']
        actor_state.ActorStateHasAttention = phy_vocab['attention']
        actor_state.ActorStateHasUnresponsiveness = phy_vocab['unresponsiveness']
    
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
        self.create_instances("Fatigue", ts_iso=ts_iso, unique=unique, regenerate=regenerate)
        self.create_instances("AttentionLevels", ts_iso=ts_iso, unique=unique, regenerate=regenerate)
        self.create_instances("Unresponsiveness", ts_iso=ts_iso, unique=unique, regenerate=regenerate)
        self.create_instances("EyeState", ts_iso=ts_iso, unique=unique, regenerate=regenerate)
        self.create_instances("MouthState", ts_iso=ts_iso, unique=unique, regenerate=regenerate)
        self.create_instances("Accessories", ts_iso=ts_iso, unique=unique, regenerate=regenerate)
        self.create_instances("Sex", ts_iso=ts_iso, unique=unique, regenerate=regenerate)
        self.create_instances("Age", ts_iso=ts_iso, unique=unique, regenerate=regenerate)
        self.create_instances("Demographic", ts_iso=ts_iso, unique=unique, regenerate=regenerate)
        self.create_instances("FaceCharacteristics", ts_iso=ts_iso, unique=unique, regenerate=regenerate)


    # def connect_actor_to_values(self): 
    #     """
    #     This function creates the rules to connect the actor to the physiological values, 
    #     and characteristics of the actor. This uses the instances of each class, to improve 
    #     reasoner performance. 
        
    #     NOTE: This solution means that the instances remain the same during the iterative execution. 
    #     If an instance is deleted or non existent the reasoner will detect an inconsistency error in this 
    #     class. 
    #     """
        
    #     Imp().set_as_rule("""ActorState(?act_state), HR(?hr_inst)     ->ActorStateHasPhysiologicalState(?act_state, ?hr_inst)""") 
    #     Imp().set_as_rule("""ActorState(?act_state), HRV(?hrv_inst)   ->ActorStateHasPhysiologicalState(?act_state, ?hrv_inst)""") 
    #     Imp().set_as_rule("""ActorState(?act_state), RR(?rr_inst)     ->ActorStateHasPhysiologicalState(?act_state, ?rr_inst)""") 
    #     Imp().set_as_rule("""ActorState(?act_state), SpO2(?spo2_inst) ->ActorStateHasPhysiologicalState(?act_state, ?spo2_inst)""") 
    #     Imp().set_as_rule("""ActorState(?act_state), Drowsiness(?dr_inst)->ActorStateHasPhysiologicalState(?act_state, ?dr_inst)""") 

    #     Imp().set_as_rule("""ActorState(?act_state), FaceCharacteristics(?fc_inst)->ActorStateHasCharacteristics(?act_state, ?fc_inst)""") 
    #     Imp().set_as_rule("""ActorState(?act_state), Sex(?sex_inst)->ActorStateHasCharacteristics(?act_state, ?sex_inst)""") 
    #     Imp().set_as_rule("""ActorState(?act_state), Age(?age_inst)->ActorStateHasCharacteristics(?act_state, ?age_inst)""") 
    #     Imp().set_as_rule("""ActorState(?act_state), Demographic(?demo_inst)->ActorStateHasCharacteristics(?act_state, ?demo_inst)""") 
    #     Imp().set_as_rule("""ActorState(?act_state), Accessories(?acc_inst)->ActorStateHasCharacteristics(?act_state, ?acc_inst)""")

    #     Imp().set_as_rule("""ActorState(?act_state), Fatigue(?fatigue_inst)->ActorStateHasFatigue(?act_state, ?fatigue_inst)""")
    #     Imp().set_as_rule("""ActorState(?act_state), AttentionLevels(?att_inst)->ActorStateHasAttention(?act_state, ?att_inst)""") 
    #     Imp().set_as_rule("""ActorState(?act_state), Unresponsiveness(?unr_inst)->ActorStateHasUnresponsiveness(?act_state, ?unr_inst)""")
    #     Imp().set_as_rule("""ActorState(?act_state), EyeState(?eye_inst) -> ActorHasEyeState(?act_state, ?eye_inst)""")
    #     Imp().set_as_rule("""ActorState(?act_state), MouthState(?mouth_inst) -> ActorHasMouthState(?act_state, ?mouth_inst)""")


    def __determine_fatigue(self): 
        """ This function is used to create the rules to categorize the fatigue of the actor into threshold ranges based on the previous physiological values. * Awake * Sleeping 
        * Microsleep
        * Drowsy 
        * Drowsiness Suspected 
        * Undefined State
        """
    
        # self.create_instances("Fatigue")
        rule_name = "undefined_critical_spo2"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), validAt(?act_st, ?t),
                ActorStateHasPhysiologicalState(?act_st, ?spo2),
                SpO2(?spo2), SpO2is(?spo2, critical_spo2_instance),
                phyValidAt(?spo2, ?spo2_t),   
                stringEqualIgnoreCase(?t, ?spo2_t),
                ActorStateHasFatigue(?act_st, ?fatigue_inst), 
                Fatigue(?fatigue_inst),
                -> FatigueIs(?fatigue_inst, undefinedstate_instance)
                """
            )

        rule_name = "awake_rule_1" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), validAt(?act_st, ?t),
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_3_kss_instance),
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, moderate_hr_instance),
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, moderate_hrv_instance),
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, moderate_rr_instance),
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, normal_spo2_instance),
                phyValidAt(?dr, ?dr_t), phyValidAt(?hr, ?hr_t), phyValidAt(?hrv, ?hrv_t),      
                phyValidAt(?rr, ?rr_t), phyValidAt(?spo2, ?spo2_t),   
                stringEqualIgnoreCase(?t, ?dr_t),stringEqualIgnoreCase(?t, ?hr_t),stringEqualIgnoreCase(?t, ?hrv_t),
                stringEqualIgnoreCase(?t, ?rr_t),stringEqualIgnoreCase(?t, ?spo2_t),
                ActorStateHasFatigue(?act_st, ?fatigue_inst), Fatigue(?fatigue_inst)
                ->  FatigueIs(?fatigue_inst, awake_instance)
                """
            )

        rule_name = "awake_rule_2" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), validAt(?act_st, ?t),
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr, level_3_kss_instance),
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, low_hr_instance),
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, moderate_hrv_instance),
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, moderate_rr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, normal_spo2_instance ), 
                phyValidAt(?dr, ?dr_t), phyValidAt(?hr, ?hr_t), phyValidAt(?hrv, ?hrv_t),      
                phyValidAt(?rr, ?rr_t), phyValidAt(?spo2, ?spo2_t),   
                stringEqualIgnoreCase(?t, ?dr_t),stringEqualIgnoreCase(?t, ?hr_t),stringEqualIgnoreCase(?t, ?hrv_t),
                stringEqualIgnoreCase(?t, ?rr_t),stringEqualIgnoreCase(?t, ?spo2_t),
                ActorStateHasFatigue(?act_st, ?fatigue_inst),  Fatigue(?fatigue_inst)
                ->  FatigueIs(?fatigue_inst, awake_instance)
                """
            )

        rule_name = "awake_rule_3" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), validAt(?act_st,?t),
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr, level_3_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, low_hr_instance),
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, high_hrv_instance),
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, moderate_rr_instance),
                ActorStateHasPhysiologicalState(?act_st, ?spo2),SpO2(?spo2), SpO2is(?spo2, normal_spo2_instance), 
                phyValidAt(?dr, ?dr_t), phyValidAt(?hr, ?hr_t), phyValidAt(?hrv, ?hrv_t),      
                phyValidAt(?rr, ?rr_t), phyValidAt(?spo2, ?spo2_t),   
                stringEqualIgnoreCase(?t, ?dr_t),stringEqualIgnoreCase(?t, ?hr_t),stringEqualIgnoreCase(?t, ?hrv_t),
                stringEqualIgnoreCase(?t, ?rr_t),stringEqualIgnoreCase(?t, ?spo2_t),
                ActorStateHasFatigue(?act_st, ?fatigue_inst), Fatigue(?fatigue_inst) 
                ->  FatigueIs(?fatigue_inst, awake_instance)
                """
            )

        rule_name = "awake_rule_4" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), validAt(?act_st,?t),
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr),  DrowsinessIs(?dr, level_3_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, low_hr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, moderate_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, low_rr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, normal_spo2_instance), 
                phyValidAt(?dr, ?dr_t), phyValidAt(?hr, ?hr_t), phyValidAt(?hrv, ?hrv_t),      
                phyValidAt(?rr, ?rr_t), phyValidAt(?spo2, ?spo2_t),   
                stringEqualIgnoreCase(?t, ?dr_t),stringEqualIgnoreCase(?t, ?hr_t),stringEqualIgnoreCase(?t, ?hrv_t),
                stringEqualIgnoreCase(?t, ?rr_t),stringEqualIgnoreCase(?t, ?spo2_t),
                ActorStateHasFatigue(?act_st, ?fatigue_inst), Fatigue(?fatigue_inst) 
                ->  FatigueIs(?fatigue_inst, awake_instance)
                """
            )

        rule_name = "awake_rule_5" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), validAt(?act_st,?t),
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr, level_3_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, low_hr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, high_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, low_rr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, normal_spo2_instance), 
                phyValidAt(?dr, ?dr_t), phyValidAt(?hr, ?hr_t), phyValidAt(?hrv, ?hrv_t),      
                phyValidAt(?rr, ?rr_t), phyValidAt(?spo2, ?spo2_t),   
                stringEqualIgnoreCase(?t, ?dr_t),stringEqualIgnoreCase(?t, ?hr_t),stringEqualIgnoreCase(?t, ?hrv_t),
                stringEqualIgnoreCase(?t, ?rr_t),stringEqualIgnoreCase(?t, ?spo2_t),
                ActorStateHasFatigue(?act_st, ?fatigue_inst), Fatigue(?fatigue_inst)
                ->  FatigueIs(?fatigue_inst, awake_instance)
                """

            )

        rule_name = "awake_rule_6" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
               """
                ActorState(?act_st), validAt(?act_st, ?t),
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr, level_3_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, moderate_hr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, high_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr),RRis(?rr, moderate_rr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, normal_spo2_instance), 
                phyValidAt(?dr, ?dr_t), phyValidAt(?hr, ?hr_t), phyValidAt(?hrv, ?hrv_t),      
                phyValidAt(?rr, ?rr_t), phyValidAt(?spo2, ?spo2_t),   
                stringEqualIgnoreCase(?t, ?dr_t),stringEqualIgnoreCase(?t, ?hr_t),stringEqualIgnoreCase(?t, ?hrv_t),
                stringEqualIgnoreCase(?t, ?rr_t),stringEqualIgnoreCase(?t, ?spo2_t),
                ActorStateHasFatigue(?act_st, ?fatigue_inst), Fatigue(?fatigue_inst)
                -> FatigueIs(?fatigue_inst, awake_instance)
                """
            )


        rule_name = "awake_rule_7" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), validAt(?act_st, ?t),
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr, level_3_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, moderate_hr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, high_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, low_rr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, normal_spo2_instance), 
                phyValidAt(?dr, ?dr_t), phyValidAt(?hr, ?hr_t), phyValidAt(?hrv, ?hrv_t),      
                phyValidAt(?rr, ?rr_t), phyValidAt(?spo2, ?spo2_t),   
                stringEqualIgnoreCase(?t, ?dr_t),stringEqualIgnoreCase(?t, ?hr_t),stringEqualIgnoreCase(?t, ?hrv_t),
                stringEqualIgnoreCase(?t, ?rr_t),stringEqualIgnoreCase(?t, ?spo2_t),
                ActorStateHasFatigue(?act_st, ?fatigue_inst), Fatigue(?fatigue_inst)
                -> FatigueIs(?fatigue_inst, awake_instance)
                """
            )

        rule_name = "awake_rule_8" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), validAt(?act_st, ?t),
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr, level_3_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, moderate_hr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, moderate_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, low_rr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, normal_spo2_instance), 
                phyValidAt(?dr, ?dr_t), phyValidAt(?hr, ?hr_t), phyValidAt(?hrv, ?hrv_t),      
                phyValidAt(?rr, ?rr_t), phyValidAt(?spo2, ?spo2_t),   
                stringEqualIgnoreCase(?t, ?dr_t),stringEqualIgnoreCase(?t, ?hr_t),stringEqualIgnoreCase(?t, ?hrv_t),
                stringEqualIgnoreCase(?t, ?rr_t),stringEqualIgnoreCase(?t, ?spo2_t),
                ActorStateHasFatigue(?act_st, ?fatigue_inst), Fatigue(?fatigue_inst)
                -> FatigueIs(?fatigue_inst, awake_instance)
                """
            )

        rule_name = "drowsy_awake_rule_1" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), validAt(?act_st, ?t),
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_5_kss_instance),
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, moderate_hr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, moderate_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, moderate_rr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, normal_spo2_instance), 
                phyValidAt(?dr, ?dr_t), phyValidAt(?hr, ?hr_t), phyValidAt(?hrv, ?hrv_t),      
                phyValidAt(?rr, ?rr_t), phyValidAt(?spo2, ?spo2_t),   
                stringEqualIgnoreCase(?t, ?dr_t),stringEqualIgnoreCase(?t, ?hr_t),stringEqualIgnoreCase(?t, ?hrv_t),
                stringEqualIgnoreCase(?t, ?rr_t),stringEqualIgnoreCase(?t, ?spo2_t),
                ActorStateHasFatigue(?act_st, ?fatigue_inst), Fatigue(?fatigue_inst)
                ->  FatigueIs(?fatigue_inst, awake_instance), DrowsinessLevelSuggested(?dr, level_3_kss_instance) 
                """
            )


        rule_name = "drowsy_awake_rule_2" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), validAt(?act_st, ?t),
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_5_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, moderate_hr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, high_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, moderate_rr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, normal_spo2_instance), 
                phyValidAt(?dr, ?dr_t), phyValidAt(?hr, ?hr_t), phyValidAt(?hrv, ?hrv_t),      
                phyValidAt(?rr, ?rr_t), phyValidAt(?spo2, ?spo2_t),   
                stringEqualIgnoreCase(?t, ?dr_t),stringEqualIgnoreCase(?t, ?hr_t),stringEqualIgnoreCase(?t, ?hrv_t),
                stringEqualIgnoreCase(?t, ?rr_t),stringEqualIgnoreCase(?t, ?spo2_t),
                ActorStateHasFatigue(?act_st, ?fatigue_inst),  Fatigue(?fatigue_inst)
                ->  FatigueIs(?fatigue_inst, awake_instance), DrowsinessLevelSuggested(?dr, level_3_kss_instance) 
                """
            )

        rule_name = "sleep_rule_1"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), validAt(?act_st, ?t), 
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr, level_7_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, very_low_hr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, low_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, very_low_rr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, normal_spo2_instance), 
                phyValidAt(?dr, ?dr_t), phyValidAt(?hr, ?hr_t), phyValidAt(?hrv, ?hrv_t),      
                phyValidAt(?rr, ?rr_t), phyValidAt(?spo2, ?spo2_t),   
                stringEqualIgnoreCase(?t, ?dr_t),stringEqualIgnoreCase(?t, ?hr_t),stringEqualIgnoreCase(?t, ?hrv_t),
                stringEqualIgnoreCase(?t, ?rr_t),stringEqualIgnoreCase(?t, ?spo2_t),
                ActorStateHasFatigue(?act_st, ?fatigue_inst), Fatigue(?fatigue_inst) 
                ->  FatigueIs(?fatigue_inst, sleep_instance), DrowsinessLevelSuggested(?dr, level_9_kss_instance) 
                """
            )

        rule_name = "sleep_rule_2"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), validAt(?act_st, ?t),
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_7_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, very_low_hr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, low_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, high_rr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, normal_spo2_instance), 
                phyValidAt(?dr, ?dr_t), phyValidAt(?hr, ?hr_t), phyValidAt(?hrv, ?hrv_t),      
                phyValidAt(?rr, ?rr_t), phyValidAt(?spo2, ?spo2_t),   
                stringEqualIgnoreCase(?t, ?dr_t),stringEqualIgnoreCase(?t, ?hr_t),stringEqualIgnoreCase(?t, ?hrv_t),
                stringEqualIgnoreCase(?t, ?rr_t),stringEqualIgnoreCase(?t, ?spo2_t),
                ActorStateHasFatigue(?act_st, ?fatigue_inst),  Fatigue(?fatigue_inst)
                -> FatigueIs(?fatigue_inst, sleep_instance), DrowsinessLevelSuggested(?dr, level_9_kss_instance) 
                """
            )

        rule_name = "sleep_rule_3"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),validAt(?act_st, ?t),  
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_7_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, high_hr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, low_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, high_rr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, normal_spo2_instance), 
                phyValidAt(?dr, ?dr_t), phyValidAt(?hr, ?hr_t), phyValidAt(?hrv, ?hrv_t),      
                phyValidAt(?rr, ?rr_t), phyValidAt(?spo2, ?spo2_t),   
                stringEqualIgnoreCase(?t, ?dr_t),stringEqualIgnoreCase(?t, ?hr_t),stringEqualIgnoreCase(?t, ?hrv_t),
                stringEqualIgnoreCase(?t, ?rr_t),stringEqualIgnoreCase(?t, ?spo2_t),
                ActorStateHasFatigue(?act_st, ?fatigue_inst), Fatigue(?fatigue_inst)
                ->  FatigueIs(?fatigue_inst, sleep_instance), DrowsinessLevelSuggested(?dr, level_9_kss_instance) 
                """
            )

        rule_name = "sleep_rule_4"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), validAt(?act_st, ?t),
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_7_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, high_hr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, low_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, very_low_rr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, normal_spo2_instance), 
                phyValidAt(?dr, ?dr_t), phyValidAt(?hr, ?hr_t), phyValidAt(?hrv, ?hrv_t),      
                phyValidAt(?rr, ?rr_t), phyValidAt(?spo2, ?spo2_t),   
                stringEqualIgnoreCase(?t, ?dr_t),stringEqualIgnoreCase(?t, ?hr_t),stringEqualIgnoreCase(?t, ?hrv_t),
                stringEqualIgnoreCase(?t, ?rr_t),stringEqualIgnoreCase(?t, ?spo2_t),
                ActorStateHasFatigue(?act_st, ?fatigue_inst), Fatigue(?fatigue_inst)
                -> FatigueIs(?fatigue_inst, sleep_instance), DrowsinessLevelSuggested(?dr, level_9_kss_instance) 
                """
            )

        rule_name = "sleep_rule_5"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), validAt(?act_st, ?t), 
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_7_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, high_hr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, very_low_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, high_rr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, normal_spo2_instance), 
                phyValidAt(?dr, ?dr_t), phyValidAt(?hr, ?hr_t), phyValidAt(?hrv, ?hrv_t),      
                phyValidAt(?rr, ?rr_t), phyValidAt(?spo2, ?spo2_t),   
                stringEqualIgnoreCase(?t, ?dr_t),stringEqualIgnoreCase(?t, ?hr_t),stringEqualIgnoreCase(?t, ?hrv_t),
                stringEqualIgnoreCase(?t, ?rr_t),stringEqualIgnoreCase(?t, ?spo2_t),
                ActorStateHasFatigue(?act_st, ?fatigue_inst), Fatigue(?fatigue_inst)
                -> FatigueIs(?fatigue_inst, sleep_instance), DrowsinessLevelSuggested(?dr, level_9_kss_instance) 
                """
            )

        rule_name = "sleep_rule_6"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), validAt(?act_st, ?t), 
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_7_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, high_hr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, very_low_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, very_low_rr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2),  SpO2is(?spo2, normal_spo2_instance), 
                phyValidAt(?dr, ?dr_t), phyValidAt(?hr, ?hr_t), phyValidAt(?hrv, ?hrv_t),      
                phyValidAt(?rr, ?rr_t), phyValidAt(?spo2, ?spo2_t),   
                stringEqualIgnoreCase(?t, ?dr_t),stringEqualIgnoreCase(?t, ?hr_t),stringEqualIgnoreCase(?t, ?hrv_t),
                stringEqualIgnoreCase(?t, ?rr_t),stringEqualIgnoreCase(?t, ?spo2_t),
                ActorStateHasFatigue(?act_st, ?fatigue_inst), Fatigue(?fatigue_inst)
                -> FatigueIs(?fatigue_inst, sleep_instance), DrowsinessLevelSuggested(?dr, level_9_kss_instance) 
                """
            )

        rule_name = "sleep_rule_7"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), validAt(?act_st, ?t),  
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_7_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, very_low_hr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, very_low_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, high_rr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, normal_spo2_instance), 
                phyValidAt(?dr, ?dr_t), phyValidAt(?hr, ?hr_t), phyValidAt(?hrv, ?hrv_t),      
                phyValidAt(?rr, ?rr_t), phyValidAt(?spo2, ?spo2_t),   
                stringEqualIgnoreCase(?t, ?dr_t),stringEqualIgnoreCase(?t, ?hr_t),stringEqualIgnoreCase(?t, ?hrv_t),
                stringEqualIgnoreCase(?t, ?rr_t),stringEqualIgnoreCase(?t, ?spo2_t),
                ActorStateHasFatigue(?act_st, ?fatigue_inst),  Fatigue(?fatigue_inst) 
                -> FatigueIs(?fatigue_inst, sleep_instance), DrowsinessLevelSuggested(?dr, level_9_kss_instance) 
                """
            )

        rule_name = "sleep_rule_8"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), validAt(?act_st, ?t),
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_7_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, very_low_hr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, very_low_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, very_low_rr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, normal_spo2_instance), 
                phyValidAt(?dr, ?dr_t), phyValidAt(?hr, ?hr_t), phyValidAt(?hrv, ?hrv_t),      
                phyValidAt(?rr, ?rr_t), phyValidAt(?spo2, ?spo2_t),   
                stringEqualIgnoreCase(?t, ?dr_t),stringEqualIgnoreCase(?t, ?hr_t),stringEqualIgnoreCase(?t, ?hrv_t),
                stringEqualIgnoreCase(?t, ?rr_t),stringEqualIgnoreCase(?t, ?spo2_t),
                ActorStateHasFatigue(?act_st, ?fatigue_inst), Fatigue(?fatigue_inst)
                -> FatigueIs(?fatigue_inst, sleep_instance), DrowsinessLevelSuggested(?dr, level_9_kss_instance) 
                """
            )

        rule_name = "sleep_rule_9"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), validAt(?act_st, ?t),
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_7_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, moderate_hr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, very_low_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, moderate_rr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, low_spo2_instance), 
                phyValidAt(?dr, ?dr_t), phyValidAt(?hr, ?hr_t), phyValidAt(?hrv, ?hrv_t),      
                phyValidAt(?rr, ?rr_t), phyValidAt(?spo2, ?spo2_t),   
                stringEqualIgnoreCase(?t, ?dr_t),stringEqualIgnoreCase(?t, ?hr_t),stringEqualIgnoreCase(?t, ?hrv_t),
                stringEqualIgnoreCase(?t, ?rr_t),stringEqualIgnoreCase(?t, ?spo2_t),
                ActorStateHasFatigue(?act_st, ?fatigue_inst), Fatigue(?fatigue_inst)
                -> FatigueIs(?fatigue_inst, sleep_instance), DrowsinessLevelSuggested(?dr, level_9_kss_instance) 
                
                """
            )
    
        rule_name = "sleep_rule_10"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), validAt(?act_st, ?t),
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_7_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, moderate_hr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, high_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, moderate_rr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, low_spo2_instance), 
                phyValidAt(?dr, ?dr_t), phyValidAt(?hr, ?hr_t), phyValidAt(?hrv, ?hrv_t),      
                phyValidAt(?rr, ?rr_t), phyValidAt(?spo2, ?spo2_t),   
                stringEqualIgnoreCase(?t, ?dr_t),stringEqualIgnoreCase(?t, ?hr_t),stringEqualIgnoreCase(?t, ?hrv_t),
                stringEqualIgnoreCase(?t, ?rr_t),stringEqualIgnoreCase(?t, ?spo2_t),
                ActorStateHasFatigue(?act_st, ?fatigue_inst), Fatigue(?fatigue_inst)
                -> FatigueIs(?fatigue_inst, sleep_instance), DrowsinessLevelSuggested(?dr, level_9_kss_instance) 
                
                """
            )
        
        rule_name = "drowsiness_suspected_10"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),validAt(?act_st, ?t), 
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_5_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, moderate_hr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, very_low_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, moderate_rr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, low_spo2_instance), 
                phyValidAt(?dr, ?dr_t), phyValidAt(?hr, ?hr_t), phyValidAt(?hrv, ?hrv_t),      
                phyValidAt(?rr, ?rr_t), phyValidAt(?spo2, ?spo2_t),   
                stringEqualIgnoreCase(?t, ?dr_t),stringEqualIgnoreCase(?t, ?hr_t),stringEqualIgnoreCase(?t, ?hrv_t),
                stringEqualIgnoreCase(?t, ?rr_t),stringEqualIgnoreCase(?t, ?spo2_t),
                ActorStateHasFatigue(?act_st, ?fatigue_inst), Fatigue(?fatigue_inst)
                -> FatigueIs(?fatigue_inst, drowsinesssuspected_instance), DrowsinessLevelSuggested(?dr, level_7_kss_instance) 
                """
            ) 

        rule_name = "drowsiness_suspected_11"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), validAt(?act_st, ?v), 
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_5_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, moderate_hr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, low_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, moderate_rr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, low_spo2_instance), 
                phyValidAt(?dr, ?dr_t), phyValidAt(?hr, ?hr_t), phyValidAt(?hrv, ?hrv_t),      
                phyValidAt(?rr, ?rr_t), phyValidAt(?spo2, ?spo2_t),   
                stringEqualIgnoreCase(?t, ?dr_t),stringEqualIgnoreCase(?t, ?hr_t),stringEqualIgnoreCase(?t, ?hrv_t),
                stringEqualIgnoreCase(?t, ?rr_t),stringEqualIgnoreCase(?t, ?spo2_t),
                ActorStateHasFatigue(?act_st, ?fatigue_inst), Fatigue(?fatigue_inst)
                -> FatigueIs(?fatigue_inst, drowsinesssuspected_instance), DrowsinessLevelSuggested(?dr, level_7_kss_instance) 
                """
            )
 
        rule_name = "drowsiness_suspected_1"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), validAt(?act_st, ?t),
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_3_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, very_low_hr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, low_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, high_rr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, normal_spo2_instance), 
                phyValidAt(?dr, ?dr_t), phyValidAt(?hr, ?hr_t), phyValidAt(?hrv, ?hrv_t),      
                phyValidAt(?rr, ?rr_t), phyValidAt(?spo2, ?spo2_t),   
                stringEqualIgnoreCase(?t, ?dr_t),stringEqualIgnoreCase(?t, ?hr_t),stringEqualIgnoreCase(?t, ?hrv_t),
                stringEqualIgnoreCase(?t, ?rr_t),stringEqualIgnoreCase(?t, ?spo2_t),
                ActorStateHasFatigue(?act_st, ?fatigue_inst), Fatigue(?fatigue_inst)
                -> FatigueIs(?fatigue_inst, drowsinesssuspected_instance), DrowsinessLevelSuggested(?dr, level_5_kss_instance) 
                """
            ) 

        rule_name = "drowsiness_suspected_2"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), validAt(?act_st, ?t), 
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_3_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, very_low_hr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, low_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, very_low_rr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, normal_spo2_instance), 
                phyValidAt(?dr, ?dr_t), phyValidAt(?hr, ?hr_t), phyValidAt(?hrv, ?hrv_t),      
                phyValidAt(?rr, ?rr_t), phyValidAt(?spo2, ?spo2_t),   
                stringEqualIgnoreCase(?t, ?dr_t),stringEqualIgnoreCase(?t, ?hr_t),stringEqualIgnoreCase(?t, ?hrv_t),
                stringEqualIgnoreCase(?t, ?rr_t),stringEqualIgnoreCase(?t, ?spo2_t),
                ActorStateHasFatigue(?act_st, ?fatigue_inst), Fatigue(?fatigue_inst)
                -> FatigueIs(?fatigue_inst, drowsinesssuspected_instance), DrowsinessLevelSuggested(?dr, level_5_kss_instance) 
                """
            ) 
            
        rule_name = "drowsiness_suspected_3"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),validAt(?act_st, ?t),
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_3_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, high_hr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, low_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, high_rr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, normal_spo2_instance), 
                phyValidAt(?dr, ?dr_t), phyValidAt(?hr, ?hr_t), phyValidAt(?hrv, ?hrv_t),      
                phyValidAt(?rr, ?rr_t), phyValidAt(?spo2, ?spo2_t),   
                stringEqualIgnoreCase(?t, ?dr_t),stringEqualIgnoreCase(?t, ?hr_t),stringEqualIgnoreCase(?t, ?hrv_t),
                stringEqualIgnoreCase(?t, ?rr_t),stringEqualIgnoreCase(?t, ?spo2_t),
                ActorStateHasFatigue(?act_st, ?fatigue_inst), Fatigue(?fatigue_inst)
                -> FatigueIs(?fatigue_inst, drowsinesssuspected_instance), DrowsinessLevelSuggested(?dr, level_5_kss_instance) 
                """
            ) 

        rule_name = "drowsiness_suspected_4"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), validAt(?act_st, ?t), 
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_3_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, high_hr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv),HRVis(?hrv, low_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, very_low_rr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, normal_spo2_instance),
                phyValidAt(?dr, ?dr_t), phyValidAt(?hr, ?hr_t), phyValidAt(?hrv, ?hrv_t),      
                phyValidAt(?rr, ?rr_t), phyValidAt(?spo2, ?spo2_t),   
                stringEqualIgnoreCase(?t, ?dr_t),stringEqualIgnoreCase(?t, ?hr_t),stringEqualIgnoreCase(?t, ?hrv_t),
                stringEqualIgnoreCase(?t, ?rr_t),stringEqualIgnoreCase(?t, ?spo2_t),
                ActorStateHasFatigue(?act_st, ?fatigue_inst), Fatigue(?fatigue_inst)
                -> FatigueIs(?fatigue_inst, drowsinesssuspected_instance), DrowsinessLevelSuggested(?dr,level_5_kss_instance) 
                """
            ) 

        rule_name = "drowsiness_suspected_5"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), validAt(?act_st, ?t),
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_3_kss_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, high_hr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv),HRVis(?hrv, very_low_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, high_rr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, normal_spo2_instance), 
                phyValidAt(?dr, ?dr_t), phyValidAt(?hr, ?hr_t), phyValidAt(?hrv, ?hrv_t),      
                phyValidAt(?rr, ?rr_t), phyValidAt(?spo2, ?spo2_t),   
                stringEqualIgnoreCase(?t, ?dr_t),stringEqualIgnoreCase(?t, ?hr_t),stringEqualIgnoreCase(?t, ?hrv_t),
                stringEqualIgnoreCase(?t, ?rr_t),stringEqualIgnoreCase(?t, ?spo2_t),
                ActorStateHasFatigue(?act_st, ?fatigue_inst), Fatigue(?fatigue_inst)
                -> FatigueIs(?fatigue_inst, drowsinesssuspected_instance), DrowsinessLevelSuggested(?dr, level_5_kss_instance) 
                """
            )
        
        rule_name = "drowsiness_suspected_6"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), validAt(?act_st, ?t),
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_3_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, high_hr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, very_low_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, very_low_rr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, normal_spo2_instance), 
                phyValidAt(?dr, ?dr_t), phyValidAt(?hr, ?hr_t), phyValidAt(?hrv, ?hrv_t),      
                phyValidAt(?rr, ?rr_t), phyValidAt(?spo2, ?spo2_t),   
                stringEqualIgnoreCase(?t, ?dr_t),stringEqualIgnoreCase(?t, ?hr_t),stringEqualIgnoreCase(?t, ?hrv_t),
                stringEqualIgnoreCase(?t, ?rr_t),stringEqualIgnoreCase(?t, ?spo2_t),
                ActorStateHasFatigue(?act_st, ?fatigue_inst), Fatigue(?fatigue_inst)
                -> FatigueIs(?fatigue_inst,drowsinesssuspected_instance), DrowsinessLevelSuggested(?dr, level_5_kss_instance) 
                """
            )

        rule_name = "drowsiness_suspected_7"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), validAt(?act_st, ?t),
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_3_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, very_low_hr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, very_low_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, very_low_rr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, normal_spo2_instance), 
                phyValidAt(?dr, ?dr_t), phyValidAt(?hr, ?hr_t), phyValidAt(?hrv, ?hrv_t),      
                phyValidAt(?rr, ?rr_t), phyValidAt(?spo2, ?spo2_t),   
                stringEqualIgnoreCase(?t, ?dr_t),stringEqualIgnoreCase(?t, ?hr_t),stringEqualIgnoreCase(?t, ?hrv_t),
                stringEqualIgnoreCase(?t, ?rr_t),stringEqualIgnoreCase(?t, ?spo2_t),
                ActorStateHasFatigue(?act_st, ?fatigue_inst), Fatigue(?fatigue_inst)
                -> FatigueIs(?fatigue_inst, drowsinesssuspected_instance), DrowsinessLevelSuggested(?dr, level_5_kss_instance) 
                """
            )

        rule_name = "drowsiness_suspected_8"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), validAt(?act_st, ?t),
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_3_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, very_low_hr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, very_low_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, high_rr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2,normal_spo2_instance), 
                phyValidAt(?dr, ?dr_t), phyValidAt(?hr, ?hr_t), phyValidAt(?hrv, ?hrv_t),      
                phyValidAt(?rr, ?rr_t), phyValidAt(?spo2, ?spo2_t),   
                stringEqualIgnoreCase(?t, ?dr_t),stringEqualIgnoreCase(?t, ?hr_t),stringEqualIgnoreCase(?t, ?hrv_t),
                stringEqualIgnoreCase(?t, ?rr_t),stringEqualIgnoreCase(?t, ?spo2_t),
                ActorStateHasFatigue(?act_st, ?fatigue_inst), Fatigue(?fatigue_inst)
                -> FatigueIs(?fatigue_inst, drowsinesssuspected_instance), DrowsinessLevelSuggested(?dr, level_5_kss_instance) 
                """
            )

        rule_name = "drowsy_low_spo2_1" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),validAt(?act_st, ?t),
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_5_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, moderate_hr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, moderate_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, moderate_rr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, low_spo2_instance), 
                phyValidAt(?dr, ?dr_t), phyValidAt(?hr, ?hr_t), phyValidAt(?hrv, ?hrv_t),      
                phyValidAt(?rr, ?rr_t), phyValidAt(?spo2, ?spo2_t),   
                stringEqualIgnoreCase(?t, ?dr_t),stringEqualIgnoreCase(?t, ?hr_t),stringEqualIgnoreCase(?t, ?hrv_t),
                stringEqualIgnoreCase(?t, ?rr_t),stringEqualIgnoreCase(?t, ?spo2_t),
                ActorStateHasFatigue(?act_st, ?fatigue_inst), Fatigue(?fatigue_inst) 
                -> FatigueIs(?fatigue_inst, drowsinesssuspected_instance), DrowsinessLevelSuggested(?dr, level_7_kss_instance)
                """
            )

        rule_name = "drowsy_low_spo2_2" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),validAt(?act_st, ?t),
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_5_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, moderate_hr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, high_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr,moderate_rr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, low_spo2_instance), 
                phyValidAt(?dr, ?dr_t), phyValidAt(?hr, ?hr_t), phyValidAt(?hrv, ?hrv_t),      
                phyValidAt(?rr, ?rr_t), phyValidAt(?spo2, ?spo2_t),   
                stringEqualIgnoreCase(?t, ?dr_t),stringEqualIgnoreCase(?t, ?hr_t),stringEqualIgnoreCase(?t, ?hrv_t),
                stringEqualIgnoreCase(?t, ?rr_t),stringEqualIgnoreCase(?t, ?spo2_t),
                ActorStateHasFatigue(?act_st, ?fatigue_inst), Fatigue(?fatigue_inst)
                ->  FatigueIs(?fatigue_inst, drowsinesssuspected_instance), DrowsinessLevelSuggested(?dr, level_7_kss_instance)
                """
            )

        rule_name = "drowsy_low_spo2_3" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),validAt(?act_st, ?t),
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_3_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, moderate_hr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, high_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr,moderate_rr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, low_spo2_instance), 
                phyValidAt(?dr, ?dr_t), phyValidAt(?hr, ?hr_t), phyValidAt(?hrv, ?hrv_t),      
                phyValidAt(?rr, ?rr_t), phyValidAt(?spo2, ?spo2_t),   
                stringEqualIgnoreCase(?t, ?dr_t),stringEqualIgnoreCase(?t, ?hr_t),stringEqualIgnoreCase(?t, ?hrv_t),
                stringEqualIgnoreCase(?t, ?rr_t),stringEqualIgnoreCase(?t, ?spo2_t),
                ActorStateHasFatigue(?act_st, ?fatigue_inst), Fatigue(?fatigue_inst)
                ->  FatigueIs(?fatigue_inst, drowsinesssuspected_instance), DrowsinessLevelSuggested(?dr, level_5_kss_instance)
                """
            )

        rule_name = "drowsy_low_spo2_4" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),validAt(?act_st, ?t),
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_3_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, moderate_hr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, moderate_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr,moderate_rr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, low_spo2_instance), 
                phyValidAt(?dr, ?dr_t), phyValidAt(?hr, ?hr_t), phyValidAt(?hrv, ?hrv_t),      
                phyValidAt(?rr, ?rr_t), phyValidAt(?spo2, ?spo2_t),   
                stringEqualIgnoreCase(?t, ?dr_t),stringEqualIgnoreCase(?t, ?hr_t),stringEqualIgnoreCase(?t, ?hrv_t),
                stringEqualIgnoreCase(?t, ?rr_t),stringEqualIgnoreCase(?t, ?spo2_t),
                ActorStateHasFatigue(?act_st, ?fatigue_inst), Fatigue(?fatigue_inst)
                ->  FatigueIs(?fatigue_inst, drowsinesssuspected_instance), DrowsinessLevelSuggested(?dr, level_5_kss_instance)
                """
            )


    def __determine_attention(self): 

        # self.create_instances("AttentionLevels")

        rule_name = "undefined_att_1" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), validAt(?act_st, ?t),
                ActorStateHasPhysiologicalState(?act_st, ?spo2), phyValidAt(?spo2, ?spo2_t),   
                SpO2is(?spo2, critical_spo2_instance),stringEqualIgnoreCase(?t, ?spo2_t),
                ActorStateHasAttention(?act_st, ?att), AttentionLevels(?att)
                ->  AttentionIs(?att, undefined_instance)
                """
            )

        rule_name = "attentive_1" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),validAt(?act_st, ?t),
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_3_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, moderate_hr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, moderate_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr,moderate_rr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, low_spo2_instance), 
                phyValidAt(?dr, ?dr_t), phyValidAt(?hr, ?hr_t), phyValidAt(?hrv, ?hrv_t),      
                phyValidAt(?rr, ?rr_t), phyValidAt(?spo2, ?spo2_t),   
                stringEqualIgnoreCase(?t, ?dr_t),stringEqualIgnoreCase(?t, ?hr_t),stringEqualIgnoreCase(?t, ?hrv_t),
                stringEqualIgnoreCase(?t, ?rr_t),stringEqualIgnoreCase(?t, ?spo2_t),
                ActorStateHasAttention(?act_st, ?attention_inst), AttentionLevels(?attention_inst)
                -> AttentionIs(?attention_inst, attentive_instance)
                """
            )

        
        rule_name = "attentive_2" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),validAt(?act_st, ?t),
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_3_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, low_hr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, moderate_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr,moderate_rr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, low_spo2_instance), 
                phyValidAt(?dr, ?dr_t), phyValidAt(?hr, ?hr_t), phyValidAt(?hrv, ?hrv_t),      
                phyValidAt(?rr, ?rr_t), phyValidAt(?spo2, ?spo2_t),   
                stringEqualIgnoreCase(?t, ?dr_t),stringEqualIgnoreCase(?t, ?hr_t),stringEqualIgnoreCase(?t, ?hrv_t),
                stringEqualIgnoreCase(?t, ?rr_t),stringEqualIgnoreCase(?t, ?spo2_t),
                ActorStateHasAttention(?act_st, ?attention_inst), AttentionLevels(?attention_inst),  
                 -> AttentionIs(?attention_inst, attentive_instance)
                """
            )

        rule_name = "attentive_3" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),validAt(?act_st, ?t),
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_3_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, moderate_hr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, high_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr,moderate_rr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, low_spo2_instance), 
                phyValidAt(?dr, ?dr_t), phyValidAt(?hr, ?hr_t), phyValidAt(?hrv, ?hrv_t),      
                phyValidAt(?rr, ?rr_t), phyValidAt(?spo2, ?spo2_t),   
                stringEqualIgnoreCase(?t, ?dr_t),stringEqualIgnoreCase(?t, ?hr_t),stringEqualIgnoreCase(?t, ?hrv_t),
                stringEqualIgnoreCase(?t, ?rr_t),stringEqualIgnoreCase(?t, ?spo2_t),
                ActorStateHasAttention(?act_st, ?attention_inst), AttentionLevels(?attention_inst), 
                -> AttentionIs(?attention_inst, attentive_instance)
                """
            )

        rule_name = "attentive_4" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),validAt(?act_st, ?t),
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_3_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, low_hr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, high_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, low_rr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, low_spo2_instance), 
                phyValidAt(?dr, ?dr_t), phyValidAt(?hr, ?hr_t), phyValidAt(?hrv, ?hrv_t),      
                phyValidAt(?rr, ?rr_t), phyValidAt(?spo2, ?spo2_t),   
                stringEqualIgnoreCase(?t, ?dr_t),stringEqualIgnoreCase(?t, ?hr_t),stringEqualIgnoreCase(?t, ?hrv_t),
                stringEqualIgnoreCase(?t, ?rr_t),stringEqualIgnoreCase(?t, ?spo2_t),
                ActorStateHasAttention(?act_st, ?attention_inst), AttentionLevels(?attention_inst)
                -> AttentionIs(?attention_inst, attentive_instance)
                """
            )

        rule_name = "attentive_5" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),validAt(?act_st, ?t),
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_3_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, moderate_hr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, high_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, low_rr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, low_spo2_instance), 
                phyValidAt(?dr, ?dr_t), phyValidAt(?hr, ?hr_t), phyValidAt(?hrv, ?hrv_t),      
                phyValidAt(?rr, ?rr_t), phyValidAt(?spo2, ?spo2_t),   
                stringEqualIgnoreCase(?t, ?dr_t),stringEqualIgnoreCase(?t, ?hr_t),stringEqualIgnoreCase(?t, ?hrv_t),
                stringEqualIgnoreCase(?t, ?rr_t),stringEqualIgnoreCase(?t, ?spo2_t),
                ActorStateHasAttention(?act_st, ?attention_inst), AttentionLevels(?attention_inst)
                -> AttentionIs(?attention_inst, attentive_instance)
                """
            )

        # rule_name = "attentive_3_1" 
        # if not has_rule_named(onto=self.ontology, name=rule_name): 
        #     Imp(rule_name).set_as_rule(
        #         """
        #         ActorState(?act_st),validAt(?act_st, ?t),
        #         ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_3_kss_instance), 
        #         ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, moderate_hr_instance), 
        #         ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, moderate_hrv_instance), 
        #         ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, moderate_rr_instance), 
        #         ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, low_spo2_instance), 
        #         ActorStateHasAttention(?act_st, ?attention_inst), AttentionLevels(?attention_inst)
        #         -> AttentionIs(?attention_inst, attentive_instance)
        #         """
        #     )

        rule_name = "attentive_4_1" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),validAt(?act_st, ?t),
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_3_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, low_hr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, moderate_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, low_rr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, low_spo2_instance), 
                phyValidAt(?dr, ?dr_t), phyValidAt(?hr, ?hr_t), phyValidAt(?hrv, ?hrv_t),      
                phyValidAt(?rr, ?rr_t), phyValidAt(?spo2, ?spo2_t),   
                stringEqualIgnoreCase(?t, ?dr_t),stringEqualIgnoreCase(?t, ?hr_t),stringEqualIgnoreCase(?t, ?hrv_t),
                stringEqualIgnoreCase(?t, ?rr_t),stringEqualIgnoreCase(?t, ?spo2_t),
                ActorStateHasAttention(?act_st, ?attention_inst), AttentionLevels(?attention_inst)
                -> AttentionIs(?attention_inst, attentive_instance)
                """
            )

        rule_name = "attentive_5_1" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),validAt(?act_st, ?t),
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_3_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, moderate_hr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, moderate_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, low_rr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, low_spo2_instance), 
                phyValidAt(?dr, ?dr_t), phyValidAt(?hr, ?hr_t), phyValidAt(?hrv, ?hrv_t),      
                phyValidAt(?rr, ?rr_t), phyValidAt(?spo2, ?spo2_t),   
                stringEqualIgnoreCase(?t, ?dr_t),stringEqualIgnoreCase(?t, ?hr_t),stringEqualIgnoreCase(?t, ?hrv_t),
                stringEqualIgnoreCase(?t, ?rr_t),stringEqualIgnoreCase(?t, ?spo2_t),
                ActorStateHasAttention(?act_st, ?attention_inst), AttentionLevels(?attention_inst), 
                -> AttentionIs(?attention_inst, attentive_instance)
                """
            )

        # return 
        rule_name = "attentive_6" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),validAt(?act_st, ?t),
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_3_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, moderate_hr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, moderate_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, moderate_rr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, normal_spo2_instance), 
                phyValidAt(?dr, ?dr_t), phyValidAt(?hr, ?hr_t), phyValidAt(?hrv, ?hrv_t),      
                phyValidAt(?rr, ?rr_t), phyValidAt(?spo2, ?spo2_t),   
                stringEqualIgnoreCase(?t, ?dr_t),stringEqualIgnoreCase(?t, ?hr_t),stringEqualIgnoreCase(?t, ?hrv_t),
                stringEqualIgnoreCase(?t, ?rr_t),stringEqualIgnoreCase(?t, ?spo2_t),
                ActorStateHasAttention(?act_st, ?attention_inst), AttentionLevels(?attention_inst)
                -> AttentionIs(?attention_inst, attentive_instance)
                """
            )

        rule_name = "attentive_7" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),validAt(?act_st, ?t),
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_5_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, moderate_hr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, moderate_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, moderate_rr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, normal_spo2_instance), 
                phyValidAt(?dr, ?dr_t), phyValidAt(?hr, ?hr_t), phyValidAt(?hrv, ?hrv_t),      
                phyValidAt(?rr, ?rr_t), phyValidAt(?spo2, ?spo2_t),   
                stringEqualIgnoreCase(?t, ?dr_t),stringEqualIgnoreCase(?t, ?hr_t),stringEqualIgnoreCase(?t, ?hrv_t),
                stringEqualIgnoreCase(?t, ?rr_t),stringEqualIgnoreCase(?t, ?spo2_t),
                ActorStateHasAttention(?act_st, ?attention_inst), AttentionLevels(?attention_inst)
                -> AttentionIs(?attention_inst, attentive_instance)
                """
            )

        rule_name = "attentive_8" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),validAt(?act_st, ?t),
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_5_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, moderate_hr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, high_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, moderate_rr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, normal_spo2_instance),  
                phyValidAt(?dr, ?dr_t), phyValidAt(?hr, ?hr_t), phyValidAt(?hrv, ?hrv_t),      
                phyValidAt(?rr, ?rr_t), phyValidAt(?spo2, ?spo2_t),   
                stringEqualIgnoreCase(?t, ?dr_t),stringEqualIgnoreCase(?t, ?hr_t),stringEqualIgnoreCase(?t, ?hrv_t),
                stringEqualIgnoreCase(?t, ?rr_t),stringEqualIgnoreCase(?t, ?spo2_t),
                ActorStateHasAttention(?act_st, ?attention_inst), AttentionLevels(?attention_inst)
                -> AttentionIs(?attention_inst, attentive_instance)
                """
            )

        # return
        rule_name = "attentive_9" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),validAt(?act_st, ?t),
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_3_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, moderate_hr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, high_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, moderate_rr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, normal_spo2_instance), 
                phyValidAt(?dr, ?dr_t), phyValidAt(?hr, ?hr_t), phyValidAt(?hrv, ?hrv_t),      
                phyValidAt(?rr, ?rr_t), phyValidAt(?spo2, ?spo2_t),   
                stringEqualIgnoreCase(?t, ?dr_t),stringEqualIgnoreCase(?t, ?hr_t),stringEqualIgnoreCase(?t, ?hrv_t),
                stringEqualIgnoreCase(?t, ?rr_t),stringEqualIgnoreCase(?t, ?spo2_t),
                ActorStateHasAttention(?act_st, ?attention_inst), AttentionLevels(?attention_inst)
                -> AttentionIs(?attention_inst, attentive_instance) 
                """
            )

        rule_name = "attentive_10" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),validAt(?act_st, ?t),
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_3_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, high_hr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, low_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, high_rr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, normal_spo2_instance), 
                phyValidAt(?dr, ?dr_t), phyValidAt(?hr, ?hr_t), phyValidAt(?hrv, ?hrv_t),      
                phyValidAt(?rr, ?rr_t), phyValidAt(?spo2, ?spo2_t),   
                stringEqualIgnoreCase(?t, ?dr_t),stringEqualIgnoreCase(?t, ?hr_t),stringEqualIgnoreCase(?t, ?hrv_t),
                stringEqualIgnoreCase(?t, ?rr_t),stringEqualIgnoreCase(?t, ?spo2_t),
                ActorStateHasAttention(?act_st, ?attention_inst), AttentionLevels(?attention_inst)
                -> AttentionIs(?attention_inst, attentive_instance)
                """
            )

        rule_name = "attentive_11" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),validAt(?act_st, ?t),
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_3_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, very_low_hr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, low_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, high_rr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, normal_spo2_instance), 
                phyValidAt(?dr, ?dr_t), phyValidAt(?hr, ?hr_t), phyValidAt(?hrv, ?hrv_t),      
                phyValidAt(?rr, ?rr_t), phyValidAt(?spo2, ?spo2_t),   
                stringEqualIgnoreCase(?t, ?dr_t),stringEqualIgnoreCase(?t, ?hr_t),stringEqualIgnoreCase(?t, ?hrv_t),
                stringEqualIgnoreCase(?t, ?rr_t),stringEqualIgnoreCase(?t, ?spo2_t),
                ActorStateHasAttention(?act_st, ?attention_inst), AttentionLevels(?attention_inst)
                -> AttentionIs(?attention_inst, attentive_instance)
                """
            )

        rule_name = "attentive_12" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),validAt(?act_st, ?t),
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_3_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, very_low_hr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, low_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, very_low_rr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, normal_spo2_instance), 
                phyValidAt(?dr, ?dr_t), phyValidAt(?hr, ?hr_t), phyValidAt(?hrv, ?hrv_t),      
                phyValidAt(?rr, ?rr_t), phyValidAt(?spo2, ?spo2_t),   
                stringEqualIgnoreCase(?t, ?dr_t),stringEqualIgnoreCase(?t, ?hr_t),stringEqualIgnoreCase(?t, ?hrv_t),
                stringEqualIgnoreCase(?t, ?rr_t),stringEqualIgnoreCase(?t, ?spo2_t),
                ActorStateHasAttention(?act_st, ?attention_inst), AttentionLevels(?attention_inst)
                -> AttentionIs(?attention_inst, attentive_instance)                
                """
            )

        # return
        rule_name = "attentive_13" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), validAt(?act_st, ?t),
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_3_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, high_hr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, low_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, very_low_rr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, normal_spo2_instance), 
                phyValidAt(?dr, ?dr_t), phyValidAt(?hr, ?hr_t), phyValidAt(?hrv, ?hrv_t),      
                phyValidAt(?rr, ?rr_t), phyValidAt(?spo2, ?spo2_t),   
                stringEqualIgnoreCase(?t, ?dr_t),stringEqualIgnoreCase(?t, ?hr_t),stringEqualIgnoreCase(?t, ?hrv_t),
                stringEqualIgnoreCase(?t, ?rr_t),stringEqualIgnoreCase(?t, ?spo2_t),
                ActorStateHasAttention(?act_st, ?attention_inst), AttentionLevels(?attention_inst),
                phyValidAt(?attention_inst, ?att_t),stringEqualIgnoreCase(?t, ?att_t)
                -> AttentionIs(?attention_inst, attentive_instance)                
                """
            )

        rule_name = "attentive_10_1" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),validAt(?act_st, ?t),
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_3_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, high_hr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, very_low_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, high_rr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, normal_spo2_instance), 
                phyValidAt(?dr, ?dr_t), phyValidAt(?hr, ?hr_t), phyValidAt(?hrv, ?hrv_t),      
                phyValidAt(?rr, ?rr_t), phyValidAt(?spo2, ?spo2_t),   
                stringEqualIgnoreCase(?t, ?dr_t),stringEqualIgnoreCase(?t, ?hr_t),stringEqualIgnoreCase(?t, ?hrv_t),
                stringEqualIgnoreCase(?t, ?rr_t),stringEqualIgnoreCase(?t, ?spo2_t),
                ActorStateHasAttention(?act_st, ?attention_inst), AttentionLevels(?attention_inst), 
                phyValidAt(?attention_inst, ?att_t),stringEqualIgnoreCase(?t, ?att_t)
                -> AttentionIs(?attention_inst, attentive_instance)                
                """
            )



        # This is the problem with the consistency
        # rule_name = "undefined_11_1" 
        # if not has_rule_named(onto=self.ontology, name=rule_name): 
        #     Imp(rule_name).set_as_rule(
        #         """
        #         ActorState(?act_st),validAt(?act_st, ?t),
        #         ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_3_kss_instance), 
        #         ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, very_low_hr_instance),  
        #         ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, very_low_hrv_instance), 
        #         ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, high_rr_instance),  
        #         ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, normal_spo2_instance), 
        #         phyValidAt(?dr, ?dr_t), phyValidAt(?hr, ?hr_t), phyValidAt(?hrv, ?hrv_t),      
        #         phyValidAt(?rr, ?rr_t), phyValidAt(?spo2, ?spo2_t),   
        #         stringEqualIgnoreCase(?t, ?dr_t),stringEqualIgnoreCase(?t, ?hr_t),stringEqualIgnoreCase(?t, ?hrv_t),
        #         stringEqualIgnoreCase(?t, ?rr_t),stringEqualIgnoreCase(?t, ?spo2_t),
        #         ActorStateHasAttention(?act_st, ?attention_inst), AttentionLevels(?attention_inst),
        #         phyValidAt(?attention_inst, ?att_t),stringEqualIgnoreCase(?t, ?att_t)
        #         -> AttentionIs(?attention_inst, undefined_instance)                
        #         """
        #     )
    
        rule_name = "attentive_12_1" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),validAt(?act_st, ?t),
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_3_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, very_low_hr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, very_low_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, very_low_rr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, normal_spo2_instance), 
                phyValidAt(?dr, ?dr_t), phyValidAt(?hr, ?hr_t), phyValidAt(?hrv, ?hrv_t),      
                phyValidAt(?rr, ?rr_t), phyValidAt(?spo2, ?spo2_t),   
                stringEqualIgnoreCase(?t, ?dr_t),stringEqualIgnoreCase(?t, ?hr_t), stringEqualIgnoreCase(?t, ?hrv_t),
                stringEqualIgnoreCase(?t, ?rr_t),stringEqualIgnoreCase(?t, ?spo2_t),
                ActorStateHasAttention(?act_st, ?attention_inst), AttentionLevels(?attention_inst),
                phyValidAt(?attention_inst, ?att_t),stringEqualIgnoreCase(?t, ?att_t)
                -> AttentionIs(?attention_inst, attentive_instance) 
                """
            )

        return
        rule_name = "attentive_13_1" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),validAt(?act_st, ?t),
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_3_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, high_hr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, very_low_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, very_low_rr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, normal_spo2_instance), 
                phyValidAt(?dr, ?dr_t), phyValidAt(?hr, ?hr_t), phyValidAt(?hrv, ?hrv_t),      
                phyValidAt(?rr, ?rr_t), phyValidAt(?spo2, ?spo2_t),   
                stringEqualIgnoreCase(?t, ?dr_t),stringEqualIgnoreCase(?t, ?hr_t),stringEqualIgnoreCase(?t, ?hrv_t),
                stringEqualIgnoreCase(?t, ?rr_t),stringEqualIgnoreCase(?t, ?spo2_t),
                ActorStateHasAttention(?act_st, ?attention_inst), AttentionLevels(?attention_inst)
                -> AttentionIs(?attention_inst, attentive_instance) 
                """
            )


        rule_name = "attentive_10_2" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),validAt(?act_st, ?t),
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_3_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, low_hr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, very_low_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, high_rr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, normal_spo2_instance), 
                phyValidAt(?dr, ?dr_t), phyValidAt(?hr, ?hr_t), phyValidAt(?hrv, ?hrv_t),      
                phyValidAt(?rr, ?rr_t), phyValidAt(?spo2, ?spo2_t),   
                stringEqualIgnoreCase(?t, ?dr_t),stringEqualIgnoreCase(?t, ?hr_t),stringEqualIgnoreCase(?t, ?hrv_t),
                stringEqualIgnoreCase(?t, ?rr_t),stringEqualIgnoreCase(?t, ?spo2_t),
                ActorStateHasAttention(?act_st, ?attention_inst), AttentionLevels(?attention_inst)
                -> AttentionIs(?attention_inst, attentive_instance) 
                """
            )

        rule_name = "attentive_11_2" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),validAt(?act_st, ?t),
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_3_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, low_hr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, very_low_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, very_low_rr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, normal_spo2_instance),  
                phyValidAt(?dr, ?dr_t), phyValidAt(?hr, ?hr_t), phyValidAt(?hrv, ?hrv_t),      
                phyValidAt(?rr, ?rr_t), phyValidAt(?spo2, ?spo2_t),   
                stringEqualIgnoreCase(?t, ?dr_t),stringEqualIgnoreCase(?t, ?hr_t),stringEqualIgnoreCase(?t, ?hrv_t),
                stringEqualIgnoreCase(?t, ?rr_t),stringEqualIgnoreCase(?t, ?spo2_t),
                ActorStateHasAttention(?act_st, ?attention_inst), AttentionLevels(?attention_inst)
                -> AttentionIs(?attention_inst, attentive_instance)
                """
            )

        rule_name = "attentive_12_2" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),validAt(?act_st, ?t),
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_3_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, very_low_hr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, very_low_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, low_rr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, normal_spo2_instance),  
                phyValidAt(?dr, ?dr_t), phyValidAt(?hr, ?hr_t), phyValidAt(?hrv, ?hrv_t),      
                phyValidAt(?rr, ?rr_t), phyValidAt(?spo2, ?spo2_t),   
                stringEqualIgnoreCase(?t, ?dr_t),stringEqualIgnoreCase(?t, ?hr_t),stringEqualIgnoreCase(?t, ?hrv_t),
                stringEqualIgnoreCase(?t, ?rr_t),stringEqualIgnoreCase(?t, ?spo2_t),
                ActorStateHasAttention(?act_st, ?attention_inst), AttentionLevels(?attention_inst)
                -> AttentionIs(?attention_inst, attentive_instance)
                """
            )

        rule_name = "attentive_13_2" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),validAt(?act_st, ?t),
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_3_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, high_hr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, very_low_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, very_low_rr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, normal_spo2_instance), 
                phyValidAt(?dr, ?dr_t), phyValidAt(?hr, ?hr_t), phyValidAt(?hrv, ?hrv_t),      
                phyValidAt(?rr, ?rr_t), phyValidAt(?spo2, ?spo2_t),   
                stringEqualIgnoreCase(?t, ?dr_t),stringEqualIgnoreCase(?t, ?hr_t),stringEqualIgnoreCase(?t, ?hrv_t),
                stringEqualIgnoreCase(?t, ?rr_t),stringEqualIgnoreCase(?t, ?spo2_t),
                ActorStateHasAttention(?act_st, ?attention_inst),AttentionLevels(?attention_inst)
                -> AttentionIs(?attention_inst, attentive_instance)
                """
            )


        rule_name = "attentive_10_3" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),validAt(?act_st, ?t),
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_3_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, low_hr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, low_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, high_rr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, normal_spo2_instance), 
                phyValidAt(?dr, ?dr_t), phyValidAt(?hr, ?hr_t), phyValidAt(?hrv, ?hrv_t),      
                phyValidAt(?rr, ?rr_t), phyValidAt(?spo2, ?spo2_t),   
                stringEqualIgnoreCase(?t, ?dr_t),stringEqualIgnoreCase(?t, ?hr_t),stringEqualIgnoreCase(?t, ?hrv_t),
                stringEqualIgnoreCase(?t, ?rr_t),stringEqualIgnoreCase(?t, ?spo2_t),
                ActorStateHasAttention(?act_st, ?attention_inst), AttentionLevels(?attention_inst)
                -> AttentionIs(?attention_inst, attentive_instance)
                """
            )

        rule_name = "attentive_11_3" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),validAt(?act_st, ?t),
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_3_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, low_hr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, low_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, very_low_rr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, normal_spo2_instance), 
                phyValidAt(?dr, ?dr_t), phyValidAt(?hr, ?hr_t), phyValidAt(?hrv, ?hrv_t),      
                phyValidAt(?rr, ?rr_t), phyValidAt(?spo2, ?spo2_t),   
                stringEqualIgnoreCase(?t, ?dr_t),stringEqualIgnoreCase(?t, ?hr_t),stringEqualIgnoreCase(?t, ?hrv_t),
                stringEqualIgnoreCase(?t, ?rr_t),stringEqualIgnoreCase(?t, ?spo2_t),
                ActorStateHasAttention(?act_st, ?attention_inst), AttentionLevels(?attention_inst)
                -> AttentionIs(?attention_inst, attentive_instance)
                """
            )

        rule_name = "attentive_12_3" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),validAt(?act_st, ?t),
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_3_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, very_low_hr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, low_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, low_rr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, normal_spo2_instance), 
                phyValidAt(?dr, ?dr_t), phyValidAt(?hr, ?hr_t), phyValidAt(?hrv, ?hrv_t),      
                phyValidAt(?rr, ?rr_t), phyValidAt(?spo2, ?spo2_t),   
                stringEqualIgnoreCase(?t, ?dr_t),stringEqualIgnoreCase(?t, ?hr_t),stringEqualIgnoreCase(?t, ?hrv_t),
                stringEqualIgnoreCase(?t, ?rr_t),stringEqualIgnoreCase(?t, ?spo2_t),
                ActorStateHasAttention(?act_st, ?attention_inst),AttentionLevels(?attention_inst)
                -> AttentionIs(?attention_inst, attentive_instance)
                """
            )

        rule_name = "attentive_13_3" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),validAt(?act_st, ?t),
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_3_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, high_hr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, low_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, very_low_rr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, normal_spo2_instance), 
                phyValidAt(?dr, ?dr_t), phyValidAt(?hr, ?hr_t), phyValidAt(?hrv, ?hrv_t),      
                phyValidAt(?rr, ?rr_t), phyValidAt(?spo2, ?spo2_t),   
                stringEqualIgnoreCase(?t, ?dr_t),stringEqualIgnoreCase(?t, ?hr_t),stringEqualIgnoreCase(?t, ?hrv_t),
                stringEqualIgnoreCase(?t, ?rr_t),stringEqualIgnoreCase(?t, ?spo2_t),
                ActorStateHasAttention(?act_st, ?attention_inst), AttentionLevels(?attention_inst)
                -> AttentionIs(?attention_inst, attentive_instance)
                """
            )

        rule_name = "attentive_14" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),validAt(?act_st, ?t),
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_3_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, low_hr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, low_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, low_rr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, normal_spo2_instance), 
                phyValidAt(?dr, ?dr_t), phyValidAt(?hr, ?hr_t), phyValidAt(?hrv, ?hrv_t),      
                phyValidAt(?rr, ?rr_t), phyValidAt(?spo2, ?spo2_t),   
                stringEqualIgnoreCase(?t, ?dr_t),stringEqualIgnoreCase(?t, ?hr_t),stringEqualIgnoreCase(?t, ?hrv_t),
                stringEqualIgnoreCase(?t, ?rr_t),stringEqualIgnoreCase(?t, ?spo2_t),
                ActorStateHasAttention(?act_st, ?attention_inst),AttentionLevels(?attention_inst)
                -> AttentionIs(?attention_inst, attentive_instance)
                """
            )

        rule_name = "attentive_15" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),validAt(?act_st, ?t),
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_3_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, low_hr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, very_low_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, low_rr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, normal_spo2_instance), 
                phyValidAt(?dr, ?dr_t), phyValidAt(?hr, ?hr_t), phyValidAt(?hrv, ?hrv_t),      
                phyValidAt(?rr, ?rr_t), phyValidAt(?spo2, ?spo2_t),   
                stringEqualIgnoreCase(?t, ?dr_t),stringEqualIgnoreCase(?t, ?hr_t),stringEqualIgnoreCase(?t, ?hrv_t),
                stringEqualIgnoreCase(?t, ?rr_t),stringEqualIgnoreCase(?t, ?spo2_t),
                ActorStateHasAttention(?act_st, ?attention_inst), AttentionLevels(?attention_inst)
                -> AttentionIs(?attention_inst, attentive_instance)
                """
            )

        rule_name = "inattentive_1" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), validAt(?act_st, ?t),
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_9_kss_instance), 
                phyValidAt(?dr, ?dr_t), stringEqualIgnoreCase(?t, ?dr_t),
                ActorStateHasAttention(?act_st, ?attention_inst), AttentionLevels(?attention_inst)
                -> AttentionIs(?attention_inst, inattentive_instance)
                """
            )

        rule_name = "inattentive_2" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), validAt(?act_st, ?t), 
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_7_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, moderate_hr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, moderate_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, moderate_rr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, normal_spo2_instance), 
                phyValidAt(?dr, ?dr_t), phyValidAt(?hr, ?hr_t), phyValidAt(?hrv, ?hrv_t),      
                phyValidAt(?rr, ?rr_t), phyValidAt(?spo2, ?spo2_t),   
                stringEqualIgnoreCase(?t, ?dr_t),stringEqualIgnoreCase(?t, ?hr_t),stringEqualIgnoreCase(?t, ?hrv_t),
                stringEqualIgnoreCase(?t, ?rr_t),stringEqualIgnoreCase(?t, ?spo2_t),
                ActorStateHasAttention(?act_st, ?attention_inst)
                -> AttentionIs(?attention_inst, inattentive_instance)
                """
            )

        rule_name = "inattentive_3" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),validAt(?act_st, ?t), 
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_7_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, moderate_hr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, moderate_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, moderate_rr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, low_spo2_instance), 
                phyValidAt(?dr, ?dr_t), phyValidAt(?hr, ?hr_t), phyValidAt(?hrv, ?hrv_t),      
                phyValidAt(?rr, ?rr_t), phyValidAt(?spo2, ?spo2_t),   
                stringEqualIgnoreCase(?t, ?dr_t),stringEqualIgnoreCase(?t, ?hr_t),stringEqualIgnoreCase(?t, ?hrv_t),
                stringEqualIgnoreCase(?t, ?rr_t),stringEqualIgnoreCase(?t, ?spo2_t),
                ActorStateHasAttention(?act_st, ?attention_inst), AttentionLevels(?attention_inst)
                -> AttentionIs(?attention_inst, inattentive_instance)
                """
            )

        rule_name = "inattentive_4" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),validAt(?act_st, ?t), 
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_7_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, moderate_hr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, high_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, moderate_rr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, low_spo2_instance),  
                phyValidAt(?dr, ?dr_t), phyValidAt(?hr, ?hr_t), phyValidAt(?hrv, ?hrv_t),      
                phyValidAt(?rr, ?rr_t), phyValidAt(?spo2, ?spo2_t),   
                stringEqualIgnoreCase(?t, ?dr_t),stringEqualIgnoreCase(?t, ?hr_t),stringEqualIgnoreCase(?t, ?hrv_t),
                stringEqualIgnoreCase(?t, ?rr_t),stringEqualIgnoreCase(?t, ?spo2_t),
                ActorStateHasAttention(?act_st, ?attention_inst), AttentionLevels(?attention_inst)
                -> AttentionIs(?attention_inst, inattentive_instance)
                """
            )

        rule_name = "inattentive_5" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),validAt(?act_st, ?t), 
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_7_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, high_hr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, low_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, high_rr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, low_spo2_instance),  
                phyValidAt(?dr, ?dr_t), phyValidAt(?hr, ?hr_t), phyValidAt(?hrv, ?hrv_t),      
                phyValidAt(?rr, ?rr_t), phyValidAt(?spo2, ?spo2_t),   
                stringEqualIgnoreCase(?t, ?dr_t),stringEqualIgnoreCase(?t, ?hr_t),stringEqualIgnoreCase(?t, ?hrv_t),
                stringEqualIgnoreCase(?t, ?rr_t),stringEqualIgnoreCase(?t, ?spo2_t),
                ActorStateHasAttention(?act_st, ?attention_inst), AttentionLevels(?attention_inst)
                -> AttentionIs(?attention_inst, inattentive_instance)
                """
            )

        rule_name = "inattentive_6" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),validAt(?act_st, ?t), 
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_7_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, very_low_hr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, low_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, high_rr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, low_spo2_instance),  
                phyValidAt(?dr, ?dr_t), phyValidAt(?hr, ?hr_t), phyValidAt(?hrv, ?hrv_t),      
                phyValidAt(?rr, ?rr_t), phyValidAt(?spo2, ?spo2_t),   
                stringEqualIgnoreCase(?t, ?dr_t),stringEqualIgnoreCase(?t, ?hr_t),stringEqualIgnoreCase(?t, ?hrv_t),
                stringEqualIgnoreCase(?t, ?rr_t),stringEqualIgnoreCase(?t, ?spo2_t),
                ActorStateHasAttention(?act_st, ?attention_inst), AttentionLevels(?attention_inst)
                -> AttentionIs(?attention_inst, inattentive_instance)
                """
            )

        rule_name = "inattentive_7" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),validAt(?act_st, ?t), 
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_7_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, very_low_hr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, low_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, very_low_rr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, low_spo2_instance),  
                phyValidAt(?dr, ?dr_t), phyValidAt(?hr, ?hr_t), phyValidAt(?hrv, ?hrv_t),      
                phyValidAt(?rr, ?rr_t), phyValidAt(?spo2, ?spo2_t),   
                stringEqualIgnoreCase(?t, ?dr_t),stringEqualIgnoreCase(?t, ?hr_t),stringEqualIgnoreCase(?t, ?hrv_t),
                stringEqualIgnoreCase(?t, ?rr_t),stringEqualIgnoreCase(?t, ?spo2_t),
                ActorStateHasAttention(?act_st, ?attention_inst), AttentionLevels(?attention_inst)
                -> AttentionIs(?attention_inst, inattentive_instance)
                """
            )
    
        rule_name = "inattentive_8" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),validAt(?act_st, ?t), 
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_7_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, high_hr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, low_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, very_low_rr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, low_spo2_instance),  
                phyValidAt(?dr, ?dr_t), phyValidAt(?hr, ?hr_t), phyValidAt(?hrv, ?hrv_t),      
                phyValidAt(?rr, ?rr_t), phyValidAt(?spo2, ?spo2_t),   
                stringEqualIgnoreCase(?t, ?dr_t),stringEqualIgnoreCase(?t, ?hr_t),stringEqualIgnoreCase(?t, ?hrv_t),
                stringEqualIgnoreCase(?t, ?rr_t),stringEqualIgnoreCase(?t, ?spo2_t),
                ActorStateHasAttention(?act_st, ?attention_inst), AttentionLevels(?attention_inst)
                -> AttentionIs(?attention_inst, inattentive_instance)
                """
            )

        rule_name = "inattentive_9" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),validAt(?act_st, ?t), 
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_7_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, high_hr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, very_low_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, high_rr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, low_spo2_instance),  
                phyValidAt(?dr, ?dr_t), phyValidAt(?hr, ?hr_t), phyValidAt(?hrv, ?hrv_t),      
                phyValidAt(?rr, ?rr_t), phyValidAt(?spo2, ?spo2_t),   
                stringEqualIgnoreCase(?t, ?dr_t),stringEqualIgnoreCase(?t, ?hr_t),stringEqualIgnoreCase(?t, ?hrv_t),
                stringEqualIgnoreCase(?t, ?rr_t),stringEqualIgnoreCase(?t, ?spo2_t),
                ActorStateHasAttention(?act_st, ?attention_inst), AttentionLevels(?attention_inst)
                -> AttentionIs(?attention_inst, inattentive_instance)
                """
            )

        rule_name = "inattentive_10" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),validAt(?act_st, ?t), 
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_7_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, very_low_hr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, very_low_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, high_rr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, low_spo2_instance),   
                phyValidAt(?dr, ?dr_t), phyValidAt(?hr, ?hr_t), phyValidAt(?hrv, ?hrv_t),      
                phyValidAt(?rr, ?rr_t), phyValidAt(?spo2, ?spo2_t),   
                stringEqualIgnoreCase(?t, ?dr_t),stringEqualIgnoreCase(?t, ?hr_t),stringEqualIgnoreCase(?t, ?hrv_t),
                stringEqualIgnoreCase(?t, ?rr_t),stringEqualIgnoreCase(?t, ?spo2_t),
                ActorStateHasAttention(?act_st, ?attention_inst),AttentionLevels(?attention_inst)
                -> AttentionIs(?attention_inst, inattentive_instance)
                """
            )

        rule_name = "inattentive_11" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),validAt(?act_st, ?t), 
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_7_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, very_low_hr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, very_low_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, very_low_rr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, normal_spo2_instance),   
                phyValidAt(?dr, ?dr_t), phyValidAt(?hr, ?hr_t), phyValidAt(?hrv, ?hrv_t),      
                phyValidAt(?rr, ?rr_t), phyValidAt(?spo2, ?spo2_t),   
                stringEqualIgnoreCase(?t, ?dr_t),stringEqualIgnoreCase(?t, ?hr_t),stringEqualIgnoreCase(?t, ?hrv_t),
                stringEqualIgnoreCase(?t, ?rr_t),stringEqualIgnoreCase(?t, ?spo2_t),
                ActorStateHasAttention(?act_st, ?attention_inst),AttentionLevels(?attention_inst)
                -> AttentionIs(?attention_inst, inattentive_instance)
                """
            )

        rule_name = "inattentive_12" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),validAt(?act_st, ?t), 
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_7_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, high_hr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, very_low_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, very_low_rr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, normal_spo2_instance),   
                phyValidAt(?dr, ?dr_t), phyValidAt(?hr, ?hr_t), phyValidAt(?hrv, ?hrv_t),      
                phyValidAt(?rr, ?rr_t), phyValidAt(?spo2, ?spo2_t),   
                stringEqualIgnoreCase(?t, ?dr_t),stringEqualIgnoreCase(?t, ?hr_t),stringEqualIgnoreCase(?t, ?hrv_t),
                stringEqualIgnoreCase(?t, ?rr_t),stringEqualIgnoreCase(?t, ?spo2_t),
                ActorStateHasAttention(?act_st, ?attention_inst),AttentionLevels(?attention_inst)
                -> AttentionIs(?attention_inst, inattentive_instance)
                """
            )

        rule_name = "inattentive_13" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),validAt(?act_st, ?t), 
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_5_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, high_hr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, very_low_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, very_low_rr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, normal_spo2_instance),   
                phyValidAt(?dr, ?dr_t), phyValidAt(?hr, ?hr_t), phyValidAt(?hrv, ?hrv_t),      
                phyValidAt(?rr, ?rr_t), phyValidAt(?spo2, ?spo2_t),   
                stringEqualIgnoreCase(?t, ?dr_t),stringEqualIgnoreCase(?t, ?hr_t),stringEqualIgnoreCase(?t, ?hrv_t),
                stringEqualIgnoreCase(?t, ?rr_t),stringEqualIgnoreCase(?t, ?spo2_t),
                ActorStateHasAttention(?act_st, ?attention_inst),AttentionLevels(?attention_inst)
                -> AttentionIs(?attention_inst, inattentive_instance)
                """
            )

        rule_name = "inattentive_14" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),validAt(?act_st, ?t), 
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_5_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, very_low_hr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, very_low_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, very_low_rr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, normal_spo2_instance),   
                phyValidAt(?dr, ?dr_t), phyValidAt(?hr, ?hr_t), phyValidAt(?hrv, ?hrv_t),      
                phyValidAt(?rr, ?rr_t), phyValidAt(?spo2, ?spo2_t),   
                stringEqualIgnoreCase(?t, ?dr_t),stringEqualIgnoreCase(?t, ?hr_t),stringEqualIgnoreCase(?t, ?hrv_t),
                stringEqualIgnoreCase(?t, ?rr_t),stringEqualIgnoreCase(?t, ?spo2_t),
                ActorStateHasAttention(?act_st, ?attention_inst), AttentionLevels(?attention_inst)
                -> AttentionIs(?attention_inst, inattentive_instance)
                """
            )

        rule_name = "inattentive_15" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),validAt(?act_st, ?t), 
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_5_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, very_low_hr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, very_low_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, high_rr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, normal_spo2_instance),   
                phyValidAt(?dr, ?dr_t), phyValidAt(?hr, ?hr_t), phyValidAt(?hrv, ?hrv_t),      
                phyValidAt(?rr, ?rr_t), phyValidAt(?spo2, ?spo2_t),   
                stringEqualIgnoreCase(?t, ?dr_t),stringEqualIgnoreCase(?t, ?hr_t),stringEqualIgnoreCase(?t, ?hrv_t),
                stringEqualIgnoreCase(?t, ?rr_t),stringEqualIgnoreCase(?t, ?spo2_t),
                ActorStateHasAttention(?act_st, ?attention_inst), AttentionLevels(?attention_inst)
                -> AttentionIs(?attention_inst, inattentive_instance)
                """
            )

        rule_name = "inattentive_16" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),validAt(?act_st, ?t), 
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_5_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, high_hr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, very_low_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, high_rr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, normal_spo2_instance),   
                phyValidAt(?dr, ?dr_t), phyValidAt(?hr, ?hr_t), phyValidAt(?hrv, ?hrv_t),      
                phyValidAt(?rr, ?rr_t), phyValidAt(?spo2, ?spo2_t),   
                stringEqualIgnoreCase(?t, ?dr_t),stringEqualIgnoreCase(?t, ?hr_t),stringEqualIgnoreCase(?t, ?hrv_t),
                stringEqualIgnoreCase(?t, ?rr_t),stringEqualIgnoreCase(?t, ?spo2_t),
                ActorStateHasAttention(?act_st, ?attention_inst), AttentionLevels(?attention_inst)
                -> AttentionIs(?attention_inst, inattentive_instance)
                """
            )

        rule_name = "inattentive_17" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),validAt(?act_st, ?t), 
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_5_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, moderate_hr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, moderate_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, moderate_rr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, low_spo2_instance),   
                phyValidAt(?dr, ?dr_t), phyValidAt(?hr, ?hr_t), phyValidAt(?hrv, ?hrv_t),      
                phyValidAt(?rr, ?rr_t), phyValidAt(?spo2, ?spo2_t),   
                stringEqualIgnoreCase(?t, ?dr_t),stringEqualIgnoreCase(?t, ?hr_t),stringEqualIgnoreCase(?t, ?hrv_t),
                stringEqualIgnoreCase(?t, ?rr_t),stringEqualIgnoreCase(?t, ?spo2_t),
                ActorStateHasAttention(?act_st, ?attention_inst), AttentionLevels(?attention_inst)
                -> AttentionIs(?attention_inst, inattentive_instance)
                """
            )

        rule_name = "inattentive_18" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),validAt(?act_st, ?t), 
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_5_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, moderate_hr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, high_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, moderate_rr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, low_spo2_instance),   
                phyValidAt(?dr, ?dr_t), phyValidAt(?hr, ?hr_t), phyValidAt(?hrv, ?hrv_t),      
                phyValidAt(?rr, ?rr_t), phyValidAt(?spo2, ?spo2_t),   
                stringEqualIgnoreCase(?t, ?dr_t),stringEqualIgnoreCase(?t, ?hr_t),stringEqualIgnoreCase(?t, ?hrv_t),
                stringEqualIgnoreCase(?t, ?rr_t),stringEqualIgnoreCase(?t, ?spo2_t),
                ActorStateHasAttention(?act_st, ?attention_inst),AttentionLevels(?attention_inst)
                -> AttentionIs(?attention_inst, inattentive_instance)
                """
            )

        rule_name = "inattentive_19" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), validAt(?act_st,?t),
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_5_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, high_hr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, low_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, high_rr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, low_spo2_instance),   
                phyValidAt(?dr, ?dr_t), phyValidAt(?hr, ?hr_t), phyValidAt(?hrv, ?hrv_t),      
                phyValidAt(?rr, ?rr_t), phyValidAt(?spo2, ?spo2_t),   
                stringEqualIgnoreCase(?t, ?dr_t),stringEqualIgnoreCase(?t, ?hr_t),stringEqualIgnoreCase(?t, ?hrv_t),
                stringEqualIgnoreCase(?t, ?rr_t),stringEqualIgnoreCase(?t, ?spo2_t),
                ActorStateHasAttention(?act_st, ?attention_inst), AttentionLevels(?attention_inst)
                -> AttentionIs(?attention_inst, inattentive_instance)
                """
            )

        rule_name = "inattentive_20" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), validAt(?act_st,?t),
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_5_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, very_low_hr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, low_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, high_rr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, low_spo2_instance),   
                 phyValidAt(?dr, ?dr_t), phyValidAt(?hr, ?hr_t), phyValidAt(?hrv, ?hrv_t),      
                phyValidAt(?rr, ?rr_t), phyValidAt(?spo2, ?spo2_t),   
                stringEqualIgnoreCase(?t, ?dr_t),stringEqualIgnoreCase(?t, ?hr_t),stringEqualIgnoreCase(?t, ?hrv_t),
                stringEqualIgnoreCase(?t, ?rr_t),stringEqualIgnoreCase(?t, ?spo2_t),
                ActorStateHasAttention(?act_st, ?attention_inst),AttentionLevels(?attention_inst)
                -> AttentionIs(?attention_inst, inattentive_instance)
                """
            )

        rule_name = "inattentive_21" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), validAt(?act_st,?t),
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_5_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, very_low_hr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, low_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, very_low_rr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, low_spo2_instance),   
                phyValidAt(?dr, ?dr_t), phyValidAt(?hr, ?hr_t), phyValidAt(?hrv, ?hrv_t),      
                phyValidAt(?rr, ?rr_t), phyValidAt(?spo2, ?spo2_t),   
                stringEqualIgnoreCase(?t, ?dr_t),stringEqualIgnoreCase(?t, ?hr_t),stringEqualIgnoreCase(?t, ?hrv_t),
                stringEqualIgnoreCase(?t, ?rr_t),stringEqualIgnoreCase(?t, ?spo2_t),
                ActorStateHasAttention(?act_st, ?attention_inst),AttentionLevels(?attention_inst)
                -> AttentionIs(?attention_inst, inattentive_instance)
                """
            )

        rule_name = "inattentive_22" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),validAt(?act_st,?t),
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_5_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, high_hr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, low_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, very_low_rr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, low_spo2_instance),   
                phyValidAt(?dr, ?dr_t), phyValidAt(?hr, ?hr_t), phyValidAt(?hrv, ?hrv_t),      
                phyValidAt(?rr, ?rr_t), phyValidAt(?spo2, ?spo2_t),   
                stringEqualIgnoreCase(?t, ?dr_t),stringEqualIgnoreCase(?t, ?hr_t),stringEqualIgnoreCase(?t, ?hrv_t),
                stringEqualIgnoreCase(?t, ?rr_t),stringEqualIgnoreCase(?t, ?spo2_t),
                ActorStateHasAttention(?act_st, ?attention_inst),AttentionLevels(?attention_inst)
                -> AttentionIs(?attention_inst, inattentive_instance)
                """
            )

        rule_name = "inattentive_23" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_5_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, very_low_hr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, very_low_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, high_rr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, low_spo2_instance),   
                phyValidAt(?dr, ?dr_t), phyValidAt(?hr, ?hr_t), phyValidAt(?hrv, ?hrv_t),      
                phyValidAt(?rr, ?rr_t), phyValidAt(?spo2, ?spo2_t),   
                stringEqualIgnoreCase(?t, ?dr_t),stringEqualIgnoreCase(?t, ?hr_t),stringEqualIgnoreCase(?t, ?hrv_t),
                stringEqualIgnoreCase(?t, ?rr_t),stringEqualIgnoreCase(?t, ?spo2_t),
                ActorStateHasAttention(?act_st, ?attention_inst),AttentionLevels(?attention_inst)
                -> AttentionIs(?attention_inst, inattentive_instance)
                """
            )

        rule_name = "inattentive_24" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), validAt(?act_st),
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_5_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, very_low_hr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, very_low_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, very_low_rr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, low_spo2_instance),   
                phyValidAt(?dr, ?dr_t), phyValidAt(?hr, ?hr_t), phyValidAt(?hrv, ?hrv_t),      
                phyValidAt(?rr, ?rr_t), phyValidAt(?spo2, ?spo2_t),   
                stringEqualIgnoreCase(?t, ?dr_t),stringEqualIgnoreCase(?t, ?hr_t),stringEqualIgnoreCase(?t, ?hrv_t),
                stringEqualIgnoreCase(?t, ?rr_t),stringEqualIgnoreCase(?t, ?spo2_t),
                ActorStateHasAttention(?act_st, ?attention_inst),AttentionLevels(?attention_inst)
                -> AttentionIs(?attention_inst, inattentive_instance)
                """
            )

        rule_name = "inattentive_25" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), validAt(?act_st, ?t), 
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_5_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, high_hr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, very_low_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, very_low_rr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, low_spo2_instance),   
                phyValidAt(?dr, ?dr_t), phyValidAt(?hr, ?hr_t), phyValidAt(?hrv, ?hrv_t),      
                phyValidAt(?rr, ?rr_t), phyValidAt(?spo2, ?spo2_t),   
                stringEqualIgnoreCase(?t, ?dr_t),stringEqualIgnoreCase(?t, ?hr_t),stringEqualIgnoreCase(?t, ?hrv_t),
                stringEqualIgnoreCase(?t, ?rr_t),stringEqualIgnoreCase(?t, ?spo2_t),
                ActorStateHasAttention(?act_st, ?attention_inst),AttentionLevels(?attention_inst)
                -> AttentionIs(?attention_inst, inattentive_instance)
                """
            )

        rule_name = "inattentive_26" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), validAt(?act_st, ?t),
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_5_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, high_hr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, very_low_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, high_rr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, low_spo2_instance),
                phyValidAt(?dr, ?dr_t), phyValidAt(?hr, ?hr_t), phyValidAt(?hrv, ?hrv_t),      
                phyValidAt(?rr, ?rr_t), phyValidAt(?spo2, ?spo2_t),   
                stringEqualIgnoreCase(?t, ?dr_t),stringEqualIgnoreCase(?t, ?hr_t),stringEqualIgnoreCase(?t, ?hrv_t),
                stringEqualIgnoreCase(?t, ?rr_t),stringEqualIgnoreCase(?t, ?spo2_t),
                ActorStateHasAttention(?act_st, ?attention_inst), AttentionLevels(?attention_inst)
                -> AttentionIs(?attention_inst, inattentive_instance)
                """
            )

    
    def determine_unresponsiveness(self): 

        # self.create_instances("Unresponsiveness")

        rule_name = "responsive_1" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), validAt(?act_st, ?t),
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_3_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, moderate_hr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, moderate_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, moderate_rr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, normal_spo2_instance),   
                ActorStateHasUnresponsiveness(?act_st, ?unresp_inst)
                ->  UnresponsiveIs(?unresp_inst, responsive_instance)
                """
            )

        rule_name = "responsive_2" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), validAt(?act_st, ?t),
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_3_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, moderate_hr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, high_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, moderate_rr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, normal_spo2_instance),   
                ActorStateHasUnresponsiveness(?act_st, ?unresp_inst)
                ->  UnresponsiveIs(?unresp_inst, responsive_instance)
                """
            )

        rule_name = "responsive_3" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), validAt(?act_st, ?t),
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_3_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, low_hr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, high_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, moderate_rr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, normal_spo2_instance),   
                ActorStateHasUnresponsiveness(?act_st, ?unresp_inst)
                ->  UnresponsiveIs(?unresp_inst, responsive_instance)                
                """
            )

        rule_name = "responsive_4" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), validAt(?act_st, ?t),
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_3_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, moderate_hr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, high_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, low_rr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, normal_spo2_instance),   
                ActorStateHasUnresponsiveness(?act_st, ?unresp_inst)
                ->  UnresponsiveIs(?unresp_inst, responsive_instance)                   
                """
            )

        rule_name = "responsive_5" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), validAt(?act_st, ?t),
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_3_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, low_hr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, high_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, low_rr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, normal_spo2_instance),
                ActorStateHasUnresponsiveness(?act_st, ?unresp_inst)
                ->  UnresponsiveIs(?unresp_inst, responsive_instance)                     
                """
            )

        rule_name = "responsive_6" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), validAt(?act_st, ?t),
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_3_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, moderate_hr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, moderate_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, low_rr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, normal_spo2_instance),
                ActorStateHasUnresponsiveness(?act_st, ?unresp_inst)
                ->  UnresponsiveIs(?unresp_inst, responsive_instance)                 
                """
            )

        rule_name = "responsive_7" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), validAt(?act_st, ?t),
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_3_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, low_hr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, moderate_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, low_rr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, normal_spo2_instance),
                ActorStateHasUnresponsiveness(?act_st, ?unresp_inst)
                ->  UnresponsiveIs(?unresp_inst, responsive_instance)                 
                """
            )

        rule_name = "at_risk_1"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),validAt(?act_st, ?t),
                ActorStateHasPhysiologicalState(?act_st,?dr), DrowsinessIs(?dr, level_5_kss_instance), 
                ActorStateHasUnresponsiveness(?act_st, ?unresp_inst)
                ->  UnresponsiveIs(?unresp_inst, atrisk_instance)        
                """
            )

        rule_name = "at_risk_2"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),validAt(?act_st, ?t),
                ActorStateHasPhysiologicalState(?act_st,?dr), DrowsinessIs(?dr, level_3_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, low_hr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, low_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, low_rr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, low_spo2_instance),
                ActorStateHasUnresponsiveness(?act_st, ?unresp_inst)
                ->  UnresponsiveIs(?unresp_inst, atrisk_instance)                 
                """
            )

        rule_name = "at_risk_3"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),validAt(?act_st, ?t),
                ActorStateHasPhysiologicalState(?act_st,?dr), DrowsinessIs(?dr, level_3_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, moderate_hr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, low_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, low_rr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, low_spo2_instance),
                ActorStateHasUnresponsiveness(?act_st, ?unresp_inst)
                ->  UnresponsiveIs(?unresp_inst, atrisk_instance)                                 
                """
            )

        rule_name = "at_risk_4"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),validAt(?act_st, ?t),
                ActorStateHasPhysiologicalState(?act_st,?dr), DrowsinessIs(?dr, level_3_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, low_hr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, low_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, high_rr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, low_spo2_instance),
                ActorStateHasUnresponsiveness(?act_st, ?unresp_inst)
                ->  UnresponsiveIs(?unresp_inst, atrisk_instance)                  
                """
            )

        rule_name = "at_risk_5"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),validAt(?act_st, ?t),
                ActorStateHasPhysiologicalState(?act_st,?dr), DrowsinessIs(?dr, level_3_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, moderate_hr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, low_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, high_rr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, low_spo2_instance),
                ActorStateHasUnresponsiveness(?act_st, ?unresp_inst)
                ->  UnresponsiveIs(?unresp_inst, atrisk_instance)                  
                """
            )

        rule_name = "critical_unre_1"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), validAt(?act_st, ?t),
                ActorStateHasPhysiologicalState(?act_st,?dr), DrowsinessIs(?dr, level_3_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, high_hr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, very_low_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, very_low_rr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, low_spo2_instance),
                ,ActorStateHasUnresponsiveness(?act_st, ?unresp_inst)
                -> UnresponsiveIs(?unresp_inst, imminent_instance)
                """
            )
            
        rule_name = "critical_unre_2"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), validAt(?act_st, ?t),
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_3_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, high_hr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, very_low_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, high_rr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, low_spo2_instance),
                ActorStateHasUnresponsiveness(?act_st, ?unresp_inst)
                -> UnresponsiveIs(?unresp_inst, imminent_instance)                
                """
            )
        
        rule_name = "critical_unre_3"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), validAt(?act_st, ?t),
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_3_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, very_low_hr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, very_low_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, very_low_rr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, low_spo2_instance),
                ActorStateHasUnresponsiveness(?act_st, ?unresp_inst)
                -> UnresponsiveIs(?unresp_inst, imminent_instance)        
                """
            )

        rule_name = "critical_unre_4"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), validAt(?act_st, ?t),
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_3_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, very_low_hr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, very_low_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, high_rr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, low_spo2_instance),
                ActorStateHasUnresponsiveness(?act_st, ?unresp_inst)
                -> UnresponsiveIs(?unresp_inst, imminent_instance)                 
                """
            )

        rule_name = "critical_unre_5"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), validAt(?act_st, ?t),
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_5_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, high_hr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, very_low_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, very_low_rr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, low_spo2_instance),
                ActorStateHasUnresponsiveness(?act_st, ?unresp_inst)
                -> UnresponsiveIs(?unresp_inst, imminent_instance) 
                """
            )
            
        rule_name = "critical_unre_6"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), validAt(?act_st, ?t),
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_5_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, high_hr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, very_low_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, high_rr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, low_spo2_instance),
                ActorStateHasUnresponsiveness(?act_st, ?unresp_inst)
                -> UnresponsiveIs(?unresp_inst, imminent_instance) 
                """
            )
        
        rule_name = "critical_unre_7"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), validAt(?act_st, ?t),
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_5_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, very_low_hr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, very_low_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, very_low_rr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, low_spo2_instance),
                ActorStateHasUnresponsiveness(?act_st, ?unresp_inst)
                -> UnresponsiveIs(?unresp_inst, imminent_instance) 
                """
            )

        rule_name = "critical_unre_8"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), validAt(?act_st, ?t),
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_5_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, very_low_hr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, very_low_hrv_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, high_rr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, low_spo2_instance),
                ActorStateHasUnresponsiveness(?act_st, ?unresp_inst)
                -> UnresponsiveIs(?unresp_inst, imminent_instance) 
                """
            )

        rule_name = "critical_unre_9"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), validAt(?act_st, ?t),
                ActorStateHasPhysiologicalState(?act_st, ?dr),  DrowsinessIs(?dr, level_5_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, low_spo2_instance), 
                ActorStateHasUnresponsiveness(?act_st, ?unresp_inst)
                -> UnresponsiveIs(?unresp_inst, imminent_instance) 
                """
            )

        rule_name = "unresponsive_1" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), validAt(?act_st, ?t),
                ActorStateHasPhysiologicalState(?act_st, ?dr),  DrowsinessIs(?dr, level_7_kss_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, low_spo2_instance), 
                ActorStateHasUnresponsiveness(?act_st, ?unresp_inst)
                -> UnresponsiveIs(?unresp_inst, unresponsive_instance)                 
                """
            )

        rule_name = "unresponsive_2" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), validAt(?act_st, ?t),
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_9_kss_instance), 
                ActorStateHasUnresponsiveness(?act_st, ?unresp_inst)
                -> UnresponsiveIs(?unresp_inst, unresponsive_instance)                  
                """
            )

        rule_name = "unresponsive_3" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), validAt(?act_st, ?t),
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_3_kss_instance),
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, very_low_hr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, very_low_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, very_low_rr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, critical_spo2_instance), 
                ActorStateHasUnresponsiveness(?act_st, ?unresp_inst)
                -> UnresponsiveIs(?unresp_inst, unresponsive_instance)                        
                """
            )

        rule_name = "unresponsive_4" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), validAt(?act_st, ?t),
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_5_kss_instance),
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, very_low_hr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, very_low_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, very_low_rr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, critical_spo2_instance), 
                ActorStateHasUnresponsiveness(?act_st, ?unresp_inst)
                -> UnresponsiveIs(?unresp_inst, unresponsive_instance)      
                """
            )

        rule_name = "unresponsive_5" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), validAt(?act_st, ?t),
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_7_kss_instance),
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, very_low_hr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, very_low_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, very_low_rr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, critical_spo2_instance), 
                ActorStateHasUnresponsiveness(?act_st, ?unresp_inst)
                -> UnresponsiveIs(?unresp_inst, unresponsive_instance)                    
                """
            )

        rule_name = "unresponsive_6" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), validAt(?act_st, ?t),
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_3_kss_instance),
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, high_hr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, very_low_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, very_low_rr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, critical_spo2_instance), 
                ActorStateHasUnresponsiveness(?act_st, ?unresp_inst)
                -> UnresponsiveIs(?unresp_inst, unresponsive_instance)                       
                """
            )

        rule_name = "unresponsive_7" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), validAt(?act_st, ?t),
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_5_kss_instance),
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, high_hr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, very_low_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, very_low_rr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, critical_spo2_instance), 
                ActorStateHasUnresponsiveness(?act_st, ?unresp_inst)
                -> UnresponsiveIs(?unresp_inst, unresponsive_instance)                     
                """
            )

        rule_name = "unresponsive_8" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), validAt(?act_st, ?t),
                ActorStateHasPhysiologicalState(?act_st, ?dr), DrowsinessIs(?dr, level_7_kss_instance),
                ActorStateHasPhysiologicalState(?act_st, ?hr), HRis(?hr, high_hr_instance),  
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRVis(?hrv, very_low_hrv_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, very_low_rr_instance), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, critical_spo2_instance), 
                ActorStateHasUnresponsiveness(?act_st, ?unresp_inst)
                -> UnresponsiveIs(?unresp_inst, unresponsive_instance)  
                """
            )


    def determine_eye_state(self): 
        """
        This function determines the eye state of an actor based on the fatigue state.

        NOTE: In later stages the eye state will be determined by the fatigue, attention 
        and ?unresp_inst state of the actor based on the physiological values. 
        """
      
        # self.create_instances("EyeState") 

        rule_name = "close_state_1"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
               """
               ActorState(?act_st),validAt(?act_st, ?t),
               ActorStateHasFatigue(?act_st, ?ftg), FatigueIs(?ftg, ?sleep), Sleep(?sleep), 
               ActorHasEyeState(?act_st,?eye_inst), EyeState(?eye_inst), ClosedState(?close) -> EyeStateIs(?eye_inst, ?close)
               """
            )
        
        rule_name = "close_state_2"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
               """
               ActorState(?act_st),validAt(?act_st, ?t),
               ActorStateHasUnresponsiveness(?act_st, ?unr), UnresponsiveIs(?unr, ?not), Unresponsive(?not), 
               ActorHasEyeState(?act_st,?eye_inst), EyeState(?eye_inst), ClosedState(?close) ->  EyeStateIs(?eye_inst, ?close)
               """
            )

        rule_name = "close_state_3"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
               """
               ActorState(?act_st),validAt(?act_st, ?t),
               ActorStateHasFatigue(?act_st, ?ftg), FatigueIs(?ftg, ?dr_sus), DrowsinessSuspected(?dr_sus), 
               ActorHasEyeState(?act_st,?eye_inst), EyeState(?eye_inst), ClosedState(?close) -> EyeStateIs(?eye_inst, ?close)
               """
            )
        
        rule_name = "close_state_4"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
               """
               ActorState(?act_st),validAt(?act_st, ?t),
               ActorStateHasFatigue(?act_st, ?ftg), FatigueIs(?ftg, ?dr_sus), DrowsinessSuspected(?dr_sus), 
               ActorStateHasAttention(?act_st, ?att),  AttentionIs(?att, ?attentive), Attentive(?attentive), 
               ActorStateHasUnresponsiveness(?act_st, ?unr), UnresponsiveIs(?unr, ?immi), Imminent(?immi), 
               ActorHasEyeState(?act_st,?eye_inst), EyeState(?eye_inst), ClosedState(?close)-> EyeStateIs(?eye_inst, ?close)
               """
            )

        rule_name = "close_state_5"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
               """
               ActorState(?act_st),validAt(?act_st, ?t),
               ActorStateHasFatigue(?act_st, ?ftg),  FatigueIs(?ftg, ?awake), Awake(?awake), 
               ActorStateHasAttention(?act_st, ?att),  AttentionIs(?att, ?inat), Inattentive(?inat), 
               ActorStateHasUnresponsiveness(?act_st, ?unr), UnresponsiveIs(?unr, ?immi), Imminent(?immi), 
               ActorHasEyeState(?act_st,?eye_inst), EyeState(?eye_inst), ClosedState(?close) -> EyeStateIs(?eye_inst, ?close)
               """
            )
    
        rule_name = "close_state_6"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
               """
               ActorState(?act_st),validAt(?act_st, ?t),
               ActorStateHasFatigue(?act_st, ?ftg), FatigueIs(?ftg, ?dr_sus), DrowsinessSuspected(?dr_sus), 
               ActorStateHasAttention(?act_st, ?att),  AttentionIs(?att, ?attentive), Attentive(?attentive), 
               ActorStateHasUnresponsiveness(?act_st, ?unr),  UnresponsiveIs(?unr, ?atrisk), AtRisk(?atrisk), 
               ActorHasEyeState(?act_st,?eye_inst), EyeState(?eye_inst), ClosedState(?close)-> EyeStateIs(?eye_inst, ?close)
               """
            )
        rule_name = "close_state_7"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
               """
               ActorState(?act_st),validAt(?act_st, ?t),
               ActorStateHasFatigue(?act_st, ?ftg), FatigueIs(?ftg, ?awake), Awake(?awake), 
               ActorStateHasAttention(?act_st, ?att),  AttentionIs(?att, ?inat), Inattentive(?inat), 
               ActorStateHasUnresponsiveness(?act_st, ?unr), UnresponsiveIs(?unr, ?atrisk), AtRisk(?atrisk), 
               ActorHasEyeState(?act_st,?eye_inst), EyeState(?eye_inst), ClosedState(?close) -> EyeStateIs(?eye_inst, ?close)
               """
            )

        rule_name = "open_state_1"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), validAt(?act_st, ?t),
                ActorStateHasFatigue(?act_st, ?ftg), FatigueIs(?ftg, ?awake), Awake(?awake), 
                ActorStateHasUnresponsiveness(?act_st, ?unr), UnresponsiveIs(?unr, ?repo), Responsive(?repo), 
                ActorStateHasAttention(?act_st, ?att), AttentionIs(?att, ?attentive), Attentive(?attentive), 
                ActorHasEyeState(?act_st,?eye_inst), EyeState(?eye_inst), OpenState(?open) ->  EyeStateIs(?eye_inst, ?open)
                """
            )
        
        rule_name = "open_state_2"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),validAt(?act_st, ?t),
                ActorStateHasFatigue(?act_st, ?ftg), FatigueIs(?ftg, ?dr_sus), DrowsinessSuspected(?dr_sus), 
                ActorStateHasUnresponsiveness(?act_st, ?unr), UnresponsiveIs(?unr, ?repo), Responsive(?repo), 
                ActorStateHasAttention(?act_st, ?att), AttentionIs(?att, ?attentive), Attentive(?attentive), 
                ActorHasEyeState(?act_st,?eye_inst), EyeState(?eye_inst), OpenState(?open) -> EyeStateIs(?eye_inst, ?open)
                """
            )
        
        rule_name = "open_state_3 "
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),validAt(?act_st, ?t),
                ActorStateHasFatigue(?act_st, ?ftg),  FatigueIs(?ftg, ?awake), Awake(?awake), 
                ActorStateHasUnresponsiveness(?act_st, ?unr), UnresponsiveIs(?unr, ?atrisk), AtRisk(?atrisk), 
                ActorStateHasAttention(?act_st, ?att),  AttentionIs(?att, ?attentive), Attentive(?attentive), 
                ActorHasEyeState(?act_st,?eye_inst), EyeState(?eye_inst), OpenState(?open) -> EyeStateIs(?eye_inst, ?open)
                """
            )

        rule_name = "open_state_4"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),validAt(?act_st, ?t),
                ActorStateHasFatigue(?act_st, ?ftg),FatigueIs(?ftg, ?dr_sus), DrowsinessSuspected(?dr_sus), 
                ActorStateHasUnresponsiveness(?act_st, ?unr),  UnresponsiveIs(?unr, ?repo), Responsive(?repo), 
                ActorStateHasAttention(?act_st, ?att), AttentionIs(?att, ?attentive), Attentive(?attentive), 
                ActorHasEyeState(?act_st,?eye_inst), EyeState(?eye_inst), OpenState(?open) ->  EyeStateIs(?eye_inst, ?open)
                """
            )

        rule_name = "open_state_5"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),validAt(?act_st, ?t),
                ActorStateHasFatigue(?act_st, ?ftg), FatigueIs(?ftg, ?awake), Awake(?awake), 
                ActorStateHasUnresponsiveness(?act_st, ?unr),  UnresponsiveIs(?unr, ?repo), Responsive(?repo), 
                ActorStateHasAttention(?act_st, ?att), AttentionIs(?att, ?inat), Inattentive(?inat), 
                ActorHasEyeState(?act_st,?eye_inst), EyeState(?eye_inst), OpenState(?open) ->  EyeStateIs(?eye_inst, ?open)
                """
            )

        rule_name = "undefined_eye_1" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), validAt(?act_st, ?t),
                ActorStateHasUnresponsiveness(?act_st, ?unr),  UnresponsiveIs(?unr, ?repo), Responsive(?repo), 
                ActorStateHasAttention(?act_st, ?att),  AttentionIs(?att, ?undef), Undefined(?undef), 
                ActorStateHasFatigue(?act_st, ?ftg), FatigueIs(?ftg, ?und), UndefinedState(?und), 
                ActorHasEyeState(?act_st,?eye_inst), EyeState(?eye_inst), SlowClosure(?slow) -> EyeStateIs(?eye_inst, ?slow)
                """
            )

        rule_name = "undefined_eye_2"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), validAt(?act_st, ?t),
                ActorStateHasUnresponsiveness(?act_st, ?unr),  UnresponsiveIs(?unr, ?not), Unresponsive(?not), 
                ActorStateHasAttention(?act_st, ?att),  AttentionIs(?att, ?undef), Undefined(?undef), 
                ActorStateHasFatigue(?act_st, ?ftg), FatigueIs(?ftg, ?und), UndefinedState(?und), 
                ActorHasEyeState(?act_st,?eye_inst), EyeState(?eye_inst), SlowClosure(?slow) -> EyeStateIs(?eye_inst, ?slow)
                """
            )

        rule_name = "undefined_eye_3"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), validAt(?act_st, ?t),
                ActorStateHasUnresponsiveness(?act_st, ?unr), UnresponsiveIs(?unr, ?immi), Imminent(?immi), 
                ActorStateHasAttention(?act_st, ?att), AttentionIs(?att, ?undef), Undefined(?undef), 
                ActorStateHasFatigue(?act_st, ?ftg), FatigueIs(?ftg, ?und), UndefinedState(?und), 
                ActorHasEyeState(?act_st,?eye_inst), EyeState(?eye_inst), SlowClosure(?slow) -> EyeStateIs(?eye_inst, ?slow)
                """
            )

        rule_name = "undefined_eye_4"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), validAt(?act_st, ?t),
                ActorStateHasUnresponsiveness(?act_st, ?unr),  UnresponsiveIs(?unr, ?atrisk), AtRisk(?atrisk), 
                ActorStateHasAttention(?act_st, ?att), AttentionIs(?att, ?undef), Undefined(?undef), 
                ActorStateHasFatigue(?act_st, ?ftg),FatigueIs(?ftg, ?und), UndefinedState(?und), 
                ActorHasEyeState(?act_st,?eye_inst), EyeState(?eye_inst), SlowClosure(?slow)-> EyeStateIs(?eye_inst, ?slow)
                """
            )


    
    def determine_mouth_state(self): 

        # self.create_instances("MouthState") 

        rule_name = "mouth_open_1" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), validAt(?act_st, ?t),
                ActorStateHasUnresponsiveness(?act_st, ?unr), UnresponsiveIs(?unr, ?notrepo), Unresponsive(?notrepo), 
                ActorHasMouthState(?act_st, ?mouth_inst),MouthState(?mouth_inst), Open(?open)->  MouthStateIs(?mouth_inst, ?open) 
                """
            )

        rule_name = "mouth_open_2" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), validAt(?act_st, ?t),
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, ?critical), Critical_SpO2(?critical),
                ActorHasMouthState(?act_st, ?mouth_inst),MouthState(?mouth_inst), Open(?open) ->  MouthStateIs(?mouth_inst, ?open) 
                """
            )

        rule_name = "mouth_open_3" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), validAt(?act_st, ?t),
                ActorStateHasFatigue(?act_st, ?ftg), FatigueIs(?ftg, ?sleep), Sleep(?sleep), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, ?vrl_rr), Very_Low_HR(?vrl_rr),
                ActorHasMouthState(?act_st, ?mouth_inst),MouthState(?mouth_inst), Open(?open) ->  MouthStateIs(?mouth_inst, ?open) 
                """
            )

        rule_name = "mouth_open_4" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), validAt(?act_st, ?t),
                ActorStateHasFatigue(?act_st, ?ftg), FatigueIs(?ftg, ?sleep), Sleep(?sleep), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, ?high_rr), High_RR(?high_rr),
                ActorHasMouthState(?act_st, ?mouth_inst),MouthState(?mouth_inst), Open(?open) -> MouthStateIs(?mouth_inst, ?open) 
                """
            )

      
        rule_name = "mouth_open_5" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), validAt(?act_st, ?t),
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, ?high_rr), High_RR(?high_rr),
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, ?l_spo2), Low_SpO2(?l_spo2),
                ActorHasMouthState(?act_st, ?mouth_inst),MouthState(?mouth_inst), Open(?open) -> MouthStateIs(?mouth_inst, ?open) 
                """
            )


        rule_name = "mouth_open_6" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), validAt(?act_st, ?t),
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, ?high_rr), High_RR(?high_rr),
                ActorStateHasUnresponsiveness(?act_st, ?unr), UnresponsiveIs(?unr, ?immi), Imminent(?immi), 
                ActorHasMouthState(?act_st, ?mouth_inst),MouthState(?mouth_inst), Open(?open) ->  MouthStateIs(?mouth_inst, ?open) 
                """
            )


        rule_name = "mouth_closed_1" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), validAt(?act_st, ?t),
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, ?mod_rr), Moderate_RR(?mod_rr),
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, ?nor), Normal_SpO2(?nor), 
                ActorStateHasFatigue(?act_st, ?ftg), FatigueIs(?ftg, ?awake), Awake(?awake), 
                ActorStateHasAttention(?act_st, ?att), AttentionIs(?att, ?attent), Attentive(?attent), 
                ActorHasMouthState(?act_st, ?mouth_inst),MouthState(?mouth_inst), Open(?open) ->  MouthStateIs(?mouth_inst, ?open) 
                """
            )

        
        rule_name = "mouth_closed_2" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), validAt(?act_st, ?t),
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, ?mod_rr), Moderate_RR(?mod_rr),
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, ?nor), Normal_SpO2(?nor), 
                ActorStateHasUnresponsiveness(?act_st, ?unr), UnresponsiveIs(?unr, ?repo), Responsive(?repo),
                ActorHasMouthState(?act_st, ?mouth_inst),MouthState(?mouth_inst), Open(?open) -> MouthStateIs(?mouth_inst, ?open) 
                """
            )

        rule_name = "mouth_closed_3" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), validAt(?act_st, ?t),
                ActorStateHasFatigue(?act_st, ?ftg), FatigueIs(?ftg, ?awake), Awake(?awake), 
                ActorStateHasAttention(?act_st, ?att), AttentionIs(?att, ?attent), Attentive(?attent), 
                ActorStateHasUnresponsiveness(?act_st, ?unr), UnresponsiveIs(?unr, ?repo), Responsive(?repo),
                ActorHasMouthState(?act_st, ?mouth_inst),MouthState(?mouth_inst), Open(?open) -> MouthStateIs(?mouth_inst, ?open) 
                """
            )


        rule_name = "mouth_yawn_1"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), validAt(?act_st, ?t),
                ActorStateHasAttention(?act_st, ?att), AttentionIs(?att, ?und), Undefined(?und), 
                ActorStateHasFatigue(?act_st, ?ftg), FatigueIs(?ftg, ?undef), UndefinedState(?undef), 
                ActorHasMouthState(?act_st, ?mouth_inst),MouthState(?mouth_inst), Yawning(?yawn) ->  MouthStateIs(?mouth_inst, ?yawn)
                """
            )


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

        with StepContext(name="Define Fatigue Rules", catch=(RuntimeError,)):
            self.__determine_fatigue()

        with StepContext(name="Define Attention Rules", catch=(RuntimeError,)): 
            self.__determine_attention()

        # with StepContext(name="Define Unresponsive Rules", catch=(RuntimeError,)): 
        #     self.determine_unresponsiveness()
        
        return
        return
        with StepContext(name="Define Eye State Rules", catch=(RuntimeError,)): 
            self.determine_eye_state()

        with StepContext(name="Define Mouth State Rules", catch=(RuntimeError,)): 
            self.determine_mouth_state()

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




    def save_onto(self, index, file_path="/ontologies/trial_onto_1.owl"): 

        if index == 0 or index % 10 == 0: 
            parent_directory = os.getcwd() 
            save_path = f"{parent_directory}/{file_path}" 
            self.ontology.save(file=save_path)
            logger.info(f"[checked] Ontology Saved at {index}.")
            time.sleep(5) 





