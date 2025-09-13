from tools.common import *
from tools.appraisal import StepContext 
from tools.logger import logger 

import os 
import pdb
import uuid 
import json 
import random

from typing import Any
from owlready2 import *
from rdflib import Graph


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
            sync_reasoner_pellet(infer_property_values=True)


    def create_instances(self, ind_class): 
        """
        This function creates instances of classes that are not yet created in the initial ontology. 
        If however an instance of the desired class exists then it checks if the instance already exists,
        and if not, it creates a new instance. 

        Args:
            ind_class (str): The name of the class to create an instance of.
        """
        
        if not list(getattr(self.ontology, ind_class).instances()): 
            new_instance = getattr(self.ontology, ind_class)(f"{ind_class.lower()}_instance")
            logger.debug(f"New instance of {ind_class} created.")
            return new_instance 
        return None


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

        with StepContext(name='Assign Values From Obs', catch=(KeyError, )): 

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

                    obs_to_PHY_instance(
                        obs_state=obs_state, 
                        instance=instance, 
                        property_name=property_name
                    )


    def determine_age(self): 
        """
        This funciton creates the rules to categorize the age of the actor into 
        a group : 
        * Young (0-18) 
        * Middle-Aged (18-65)
        * Elderly (>65) 
        """

        with self.ontology: 

            if self.ontology.Age is not None: 

                age_rules = [
                    ("Young", "lessThanOrEqual", 18),
                    ("Middle-Aged", "greaterThanOrEqual", 18, "lessThanOrEqual", 65),
                    ("Elderly", "greaterThan", 65)
                ]

                for rule in age_rules:
                    self.create_instances(rule[0])
                    rule_name = f"{rule[0]}_group_rule"
                    
                    if not has_rule_named(self.ontology, name=rule_name): 
                        Imp(rule_name).set_as_rule(
                            f"""
                            Age(age_instance),
                            hasAgeValue(age_instance, ?age_value),
                            {rule[1]}(?age_value, {rule[2]})
                            {f', {rule[3]}(?age_value, {rule[4]})' if len(rule) > 3 else ''},
                            {rule[0]}(?age_group) -> AgeBelongsToGroup(age_instance, ?age_group)
                            """
                        )

            # Keep the age groups in a list to get the corresponding threshold instance later. 
            self.age_groups = [age.name.lower() for age in self.ontology.Age.subclasses()]        
            self.age_group_names = [age.name for age in self.ontology.Age.subclasses() ]

        
    def determine_gender(self): 

        with self.ontology:
            person_sex = {
                "Male": ["Man"],
                "Female": ["Woman"]
            } 

            for name in person_sex:
                if not hasattr(self.ontology, name):
                    type(name, (self.ontology.Sex,), {})

                for name, value in person_sex.items(): 
                    self.create_instances(name)
                    for val in value:

                        rule = Imp() 
                        rule.set_as_rule(
                            f"""
                            Sex(sex_instance),
                            hasStringValue(sex_instance, ?sex_value),
                            stringEqualIgnoreCase(?sex_value, "{val}"),
                            {name}(?sex_group) -> SexBelongsToPerson(sex_instance, ?sex_group)
                            """)

            self.sex_groups = [gen.name.lower() for gen in self.ontology.Sex.subclasses()]
            self.sex_group_names = [gen.name for gen in self.ontology.Sex.subclasses()]

        logger.debug("Determine Gender | Rules Created successfully...")
        

    def denote_temperature(self): 

        acc_class = getattr(self.ontology, "Accessories")
        if acc_class is None: 
            self.create_instances("Accessories")

        # Create all subclasses instances 
        for acc in acc_class.subclasses():
            self.create_instances(acc.name) 

        temp_class = getattr(self.ontology,"WeatherCondition")
        if temp_class is None: 
            self.create_instances("WeatherCondition")

        # Create all subclasses instances 
        for temp in temp_class.subclasses():
            self.create_instances(temp.name)
            
        temp_class = getattr(self.ontology,"TemporalContext")
        if temp_class is None: 
            self.create_instances("TemporalContext")

        for temp in temp_class.subclasses():
            self.create_instances(temp.name)

        self.temp_groups = [gen.name.lower() for gen in self.ontology.WeatherCondition.subclasses()]
        self.temp_group_names = [gen.name for gen in self.ontology.WeatherCondition.subclasses()]


    def determine_acc_and_temp(self): 
        
        rule_name = "scarf_cold_rule" 
        
        names = ["scarf_cold_rule", "hat_hot_rule", "glasses_normaltemp_rule"]
        temps = ["ColdTemp", "HotTemp","ModerateTemp"]
        accs = ["Scarf", "Hat", "Glasses"]

        for indx, name in enumerate(names): 
            if not  has_rule_named(self.ontology, name=rule_name): 
                Imp(name).set_as_rule(
                    f"""
                        Accessories(?accessories_instance), hasStringValue(?accessories_instance, ?acc_value),
                        stringEqualIgnoreCase(?acc_value, "{accs[indx]}"), {accs[indx]}(?accs), {temps[indx]}(?temp) -> 
                        AccessoriesIncludeWearables(?accessories_instance, ?accs), DenotesTemperature(?accs,?temp)
                    """
                )
                

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

        for i, age_group in enumerate(self.age_group_names): 
            age = self.age_groups[i] 

            for jj, sex_group in enumerate(self.sex_group_names): 
                sex = self.sex_groups[jj] 
                for tt, temp_group in enumerate(self.temp_group_names): 
                    temp = self.temp_groups[tt] 
                    rule_name = f"profile_{age}_{sex}_{temp}"
                    if "temp" in temp: temp = temp.replace("temp", "")
                    if not has_rule_named(self.ontology, name=rule_name): 
                        Imp(rule_name).set_as_rule(
                            f"""
                                ActorState(?act_state),
                                Age(age_instance), AgeBelongsToGroup(age_instance, ?age_g), {age_group}(?age_g), 
                                Sex(sex_instance),SexBelongsToPerson(sex_instance, ?sex_g), {sex_group}(?sex_g), 
                                Accessories(accessories_instance), 
                                AccessoriesIncludeWearables(accessories_instance, ?v), 
                                DenotesTemperature(?v, ?temp), {temp_group}(?temp), 
                                -> StateHasThresholdProfile(?act_state, tp_{age}_{sex}_{temp}) 
                            """
                        )


    def determine_thresholds_profile(self):
        thr_values = capture_thr_values_from_individuals(self.ontology) 
        parse_thr_profiles(self.ontology, thr_values) 
        self.find_threshold_profile_rules()
        

    def determine_HR(self):
        """
        This function creates the rules to categorize the HR of the actor into
        threshold ranges: 
        * Low 
        * Slightly Low 
        * Moderate (Normal) 
        * High 

        These threshold ranges change based on the Age group of the actor.
        """

        self.create_instances("Very_Low_HR") 
        if not has_rule_named(onto=self.ontology, name="very_low_hr_rule"): 
            Imp("very_low_hr_rule").set_as_rule(
                f""" 
                ActorState(?act_st), StateHasThresholdProfile(?act_st, ?tp), 
                ActorStateHasPhysiologicalState(?act_st, hr_instance), 
                HR(hr_instance), hasNumericalValue(hr_instance, ?value), 
                appliesHRLow(?tp, ?hr_low), hasThrValue(?hr_low, ?low), 
                greaterThanOrEqual(?value, 0), 
                lessThan(?value, ?low), 
                Very_Low_HR(?vrl_hr)  ->  HRis(hr_instance, ?vrl_hr) 
                """
            )

        self.create_instances("Low_HR") 
        if not has_rule_named(onto=self.ontology, name="low_hr_rule"): 
            Imp("low_hr_rule").set_as_rule(
                 f""" 
                ActorState(?act_st), StateHasThresholdProfile(?act_st, ?tp), 
                ActorStateHasPhysiologicalState(?act_st, hr_instance), 
                HR(hr_instance), hasNumericalValue(hr_instance, ?value), 
                appliesHRLow(?tp, ?hr_low), hasThrValue(?hr_low, ?low), 
                appliesHRModerate(?tp, ?hr_mod), hasThrValue(?hr_mod, ?mod), 
                greaterThanOrEqual(?value, ?low),
                lessThan(?value, ?mod), 
                Low_HR(?l_hr)  -> HRis(hr_instance, ?l_hr) 
                """
            )

        self.create_instances("Moderate_HR") 
        if not has_rule_named(onto=self.ontology, name="moderate_hr_rule"): 
            Imp("moderate_hr_rule").set_as_rule(
                f""" 
                ActorState(?act_st), StateHasThresholdProfile(?act_st, ?tp), 
                ActorStateHasPhysiologicalState(?act_st, hr_instance),
                HR(hr_instance), hasNumericalValue(hr_instance, ?value), 
                appliesHRModerate(?tp, ?hr_mod), hasThrValue(?hr_mod, ?mod), 
                appliesHRHigh(?tp, ?hr_high), hasThrValue(?hr_high, ?high), 
                greaterThanOrEqual(?value, ?mod),
                lessThan(?value, ?high), 
                Moderate_HR(?m_hr)  ->  HRis(hr_instance, ?m_hr) 
                """
            )

        self.create_instances("High_HR") 
        if not has_rule_named(onto=self.ontology, name="high_hr_rule"): 
            Imp("high_hr_rule").set_as_rule(
                f""" 
                ActorState(?act_st), StateHasThresholdProfile(?act_st, ?tp), 
                ActorStateHasPhysiologicalState(?act_st,hr_instance),
                HR(hr_instance), hasNumericalValue(hr_instance, ?value), 
                appliesHRHigh(?tp, ?hr_high), hasThrValue(?hr_high, ?high), 
                greaterThanOrEqual(?value, ?high),
                lessThan(?value, 250), 
                High_HR(?h_hr)  ->  HRis(hr_instance, ?h_hr) 
                """
            )

        
    def determine_HRV(self): 
        """
        This function creates the rules to categorize the HRV of the actor into
        threshold ranges: 
        * Very Low 
        * Low 
        * Moderate (Normal) 
        * High 

        These threshold ranges change based on the Age group of the actor.
        """
      
        self.create_instances("Very_Low_HRV") 
        if not has_rule_named(onto=self.ontology, name="very_low_hrv_rule"): 
            Imp("very_low_hrv_rule").set_as_rule(
                f"""
                ActorState(?act_st), StateHasThresholdProfile(?act_st, ?tp), 
                ActorStateHasPhysiologicalState(?act_st, hrv_instance),
                HRV(hrv_instance), hasNumericalValue(hrv_instance, ?value), 
                appliesHRVLow(?tp, ?hrv_low), hasThrValue(?hrv_low, ?low), 
                greaterThanOrEqual(?value, 0), 
                lessThan(?value, ?low), 
                Very_Low_HRV(?vrl_hrv) ->  HRVis(hrv_instance, ?vrl_hrv)
                """
            )

        self.create_instances("Low_HRV") 
        if not has_rule_named(onto=self.ontology, name="low_hrv_rule"): 
            Imp("low_hrv_rule").set_as_rule(
                f"""
                ActorState(?act_st), StateHasThresholdProfile(?act_st, ?tp), 
                ActorStateHasPhysiologicalState(?act_st,hrv_instance),
                HRV(hrv_instance), hasNumericalValue(hrv_instance, ?value), 
                appliesHRVLow(?tp, ?hrv_low), hasThrValue(?hrv_low, ?low), 
                appliesHRVModerate(?tp, ?hrv_mod), hasThrValue(?hrv_mod, ?mod), 
                greaterThanOrEqual(?value, ?low), 
                lessThan(?value, ?mod), 
                Low_HRV(?l_hrv) ->  HRVis(hrv_instance, ?l_hrv)
                """
            )

        self.create_instances("Moderate_HRV") 
        if not has_rule_named(onto=self.ontology, name="moderate_hrv_rule"): 
            Imp("moderate_hrv_rule").set_as_rule(
                """
                ActorState(?act_st), StateHasThresholdProfile(?act_st, ?tp), 
                ActorStateHasPhysiologicalState(?act_st, hrv_instance),
                HRV(hrv_instance), hasNumericalValue(hrv_instance, ?value), 
                appliesHRVModerate(?tp, ?hrv_mod), hasThrValue(?hrv_mod, ?mod), 
                appliesHRVHigh(?tp, ?hrv_high), hasThrValue(?hrv_high, ?high), 
                greaterThanOrEqual(?value, ?mod), 
                lessThan(?value, ?high), 
                Moderate_HRV(?mod_hrv) -> HRVis(hrv_instance, ?mod_hrv)
                """
            )

        self.create_instances("High_HRV")
        if not has_rule_named(onto=self.ontology, name="high_hrv_rule"): 
            Imp("high_hrv_rule").set_as_rule(
                f"""
                ActorState(?act_st), StateHasThresholdProfile(?act_st, ?tp), 
                ActorStateHasPhysiologicalState(?act_st, hrv_instance),
                HRV(hrv_instance), hasNumericalValue(hrv_instance, ?value), 
                appliesHRVHigh(?tp, ?hrv_high), hasThrValue(?hrv_high, ?high), 
                greaterThanOrEqual(?value, ?high),
                lessThan(?value, 250), 
                High_HRV(?high_hrv) -> HRVis(hrv_instance, ?high_hrv)
                """
            )


    def determine_RR(self):
        """
        This function creates the rules to categorize the RR of the actor into
        threshold ranges: 
        * Very Low 
        * Low 
        * Moderate (Normal) 
        * High 

        These threshold ranges change based on the Age group of the actor.
        """

        self.create_instances("Very_Low_RR") 
        if not has_rule_named(onto=self.ontology, name="very_low_rr_rule"):
            Imp("very_low_rr_rule").set_as_rule(
                f"""
                ActorState(?act_st), StateHasThresholdProfile(?act_st, ?tp), 
                ActorStateHasPhysiologicalState(?act_st, rr_instance),
                RR(rr_instance), hasNumericalValue(rr_instance, ?value), 
                appliesRRLow(?tp, ?rr_low), hasThrValue(?rr_low, ?low), 
                greaterThanOrEqual(?value, 0), 
                lessThan(?value, ?low), 
                Very_Low_RR(?vrl_rr) ->  RRis(rr_instance, ?vrl_rr) 
                """
            )

        self.create_instances("Low_RR") 
        if not has_rule_named(onto=self.ontology, name="low_rr_rule"): 
             Imp("low_rr_rule").set_as_rule(
                f"""
                ActorState(?act_st), StateHasThresholdProfile(?act_st, ?tp), 
                ActorStateHasPhysiologicalState(?act_st, rr_instance),
                RR(rr_instance), hasNumericalValue(rr_instance, ?value), 
                appliesRRLow(?tp, ?rr_low), hasThrValue(?rr_low, ?low), 
                appliesRRModerate(?tp, ?rr_mod), hasThrValue(?rr_mod, ?mod), 
                greaterThanOrEqual(?value, ?low),
                lessThan(?value, ?mod), 
                Low_RR(?l_rr) ->  RRis(rr_instance, ?l_rr)
                """
             )
        
        self.create_instances("Moderate_RR") 
        if not has_rule_named(onto=self.ontology, name="moderate_rr_rule"): 
             Imp("moderate_rr_rule").set_as_rule(
                f"""
                ActorState(?act_st), StateHasThresholdProfile(?act_st, ?tp), 
                ActorStateHasPhysiologicalState(?act_st, rr_instance),
                RR(rr_instance), hasNumericalValue(rr_instance, ?value), 
                appliesRRModerate(?tp, ?rr_mod), hasThrValue(?rr_mod, ?mod), 
                appliesRRHigh(?tp, ?rr_high), hasThrValue(?rr_high, ?high), 
                greaterThanOrEqual(?value, ?mod),
                lessThan(?value, ?high), 
                Moderate_RR(?mod_rr) ->  RRis(rr_instance, ?mod_rr)
                """
             )

        self.create_instances("High_RR") 
        if not has_rule_named(onto=self.ontology, name="high_rr_rule"): 
             Imp("high_rr_rule").set_as_rule(
                f"""
                ActorState(?act_st), StateHasThresholdProfile(?act_st, ?tp), 
                ActorStateHasPhysiologicalState(?act_st, rr_instance),
                RR(rr_instance), hasNumericalValue(rr_instance, ?value), 
                appliesRRHigh(?tp, ?rr_high), hasThrValue(?rr_high, ?high), 
                greaterThanOrEqual(?value, ?high),  
                lessThan(?value, 50), 
                High_RR(?high_rr) ->  RRis(rr_instance, ?high_rr)
                """
             )
                   

    def determine_spo2(self): 
        """
        This function creates the rules to categorize the SPO2 of the actor into
        threshold ranges: 
        * Normal 
        * Slightly_Low
        * Critical

        These threshold ranges change based on the Age group of the actor.
        """

        self.create_instances("Normal_SpO2") 
        if not has_rule_named(onto=self.ontology, name="normal_spo2_rule"): 
             Imp("normal_spo2_rule").set_as_rule(
                f"""
                ActorState(?act_st), StateHasThresholdProfile(?act_st, ?tp), 
                ActorStateHasPhysiologicalState(?act_st, spo2_instance),
                SpO2(spo2_instance), hasNumericalValue(spo2_instance, ?value), 
                appliesSPO2Moderate(?tp, ?spo2_mod), hasThrValue(?spo2_mod, ?mod), 
                appliesSPO2High(?tp, ?spo2_high), hasThrValue(?spo2_high, ?high), 
                greaterThanOrEqual(?value, ?mod),
                lessThanOrEqual(?value, ?high), 
                Normal_SpO2(?nrm_spo2) ->  SpO2is(spo2_instance, ?nrm_spo2)
                """
             )

        self.create_instances("Low_SpO2") 
        if not has_rule_named(onto=self.ontology, name="low_spo2_rule"): 
             Imp("low_spo2_rule").set_as_rule(
                f"""
                ActorState(?act_st), StateHasThresholdProfile(?act_st, ?tp), 
                ActorStateHasPhysiologicalState(?act_st, spo2_instance),
                SpO2(spo2_instance), hasNumericalValue(spo2_instance, ?value), 
                appliesSPO2Low(?tp, ?spo2_low), hasThrValue(?spo2_low, ?low), 
                appliesSPO2Moderate(?tp, ?spo2_mod), hasThrValue(?spo2_mod, ?mod), 
                greaterThanOrEqual(?value, ?low), lessThan(?value, ?mod), 
                Low_SpO2(?l_spo2) ->  SpO2is(spo2_instance, ?l_spo2)
                """
             )


        self.create_instances("Critical_SpO2") 
        if not has_rule_named(onto=self.ontology, name="critical_spo2_rule"): 
             Imp("critical_spo2_rule").set_as_rule(
                f"""
                ActorState(?act_st), StateHasThresholdProfile(?act_st, ?tp), 
                ActorStateHasPhysiologicalState(?act_st, spo2_instance), 
                appliesSPO2Low(?tp, ?spo2_low), hasThrValue(?spo2_low, ?low), 
                SpO2(spo2_instance), hasNumericalValue(spo2_instance, ?value), 
                lessThan(?value, ?low),  
                Critical_SpO2(?critical_spo2) -> SpO2is(spo2_instance, ?critical_spo2)
                """
             )
          
                
    def determine_drowsiness(self): 
        """
        This function creates the rules to categorize the Drowsiness of the actor into
        threshold ranges based on Karolinska Sleep Scale (KSS)
        * Level_3 (actor is awake) 
        * Level_5 (actor is neither asleep or awake)
        * Level_7 (actor is asleep with no effor of waking up)
        * Level_9 (actor is asleep with effort of waking up)
        """

        self.create_instances('Level_3_KSS')

        rule_name = "level_3_kss_rule" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_state), ActorStateHasPhysiologicalState(?act_state, drowsiness_instance),
                Drowsiness(drowsiness_instance), hasNumericalValue(drowsiness_instance, ?v), 
                lessThanOrEqual(?v, 1), greaterThan(?v, 0), Level_3_KSS(?l3kss) 
                -> DrowsinessIs(drowsiness_instance, ?l3kss) 
                """
            )

        self.create_instances('Level_5_KSS')

        rule_name = "level_5_kss_rule" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_state), ActorStateHasPhysiologicalState(?act_state, drowsiness_instance),
                Drowsiness(drowsiness_instance), hasNumericalValue(drowsiness_instance, ?v), 
                lessThanOrEqual(?v, 2), greaterThan(?v, 1), Level_5_KSS(?l5kss) 
                ->  DrowsinessIs(drowsiness_instance, ?l5kss) 
                """
            )

        self.create_instances('Level_7_KSS')

        rule_name = "level_7_kss_rule" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_state), ActorStateHasPhysiologicalState(?act_state, drowsiness_instance),
                Drowsiness(drowsiness_instance), hasNumericalValue(drowsiness_instance, ?v), 
                lessThanOrEqual(?v, 3), greaterThan(?v, 2), Level_7_KSS(?l7kss) 
                -> DrowsinessIs(drowsiness_instance, ?l7kss) 
                """
            )

        self.create_instances('Level_9_KSS')

        rule_name = "level_9_kss_rule" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_state), ActorStateHasPhysiologicalState(?act_state, drowsiness_instance), 
                Drowsiness(drowsiness_instance), hasNumericalValue(?dr_instance, ?v), 
                lessThanOrEqual(?v, 4), greaterThan(?v, 3), Level_9_KSS(?l9kss) 
                ->  DrowsinessIs(drowsiness_instance, ?l9kss) 
                """
            )


    def set_up_trends(self):  
        self.create_instances('CurrentReading')
        self.create_instances('PreviousReading') 
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
                

    def connect_actor_to_values(self): 
        """
        This function creates the rules to connect the actor to the physiological values, 
        and characteristics of the actor. This uses the instances of each class, to improve 
        reasoner performance. 
        
        NOTE: This solution means that the instances remain the same during the iterative execution. 
        If an instance is deleted or non existent the reasoner will detect an inconsistency error in this 
        class. 
        """
        
        Imp().set_as_rule("""ActorState(?act_state), HR(hr_instance)     ->ActorStateHasPhysiologicalState(?act_state, hr_instance)""") 
        Imp().set_as_rule("""ActorState(?act_state), HRV(hrv_instance)   ->ActorStateHasPhysiologicalState(?act_state, hrv_instance)""") 
        Imp().set_as_rule("""ActorState(?act_state), RR(rr_instance)     ->ActorStateHasPhysiologicalState(?act_state, rr_instance)""") 
        Imp().set_as_rule("""ActorState(?act_state), SpO2(spo2_instance) ->ActorStateHasPhysiologicalState(?act_state, spo2_instance)""") 
        Imp().set_as_rule("""ActorState(?act_state), Drowsiness(drowsiness_instance)->ActorStateHasPhysiologicalState(?act_state, drowsiness_instance)""") 

        Imp().set_as_rule("""ActorState(?act_state), FaceCharacteristics(facecharacteristics_instance)->ActorStateHasCharacteristics(?act_state, facecharacteristics_instance)""") 
        Imp().set_as_rule("""ActorState(?act_state), Sex(sex_instance)->ActorStateHasCharacteristics(?act_state, sex_instance)""") 
        Imp().set_as_rule("""ActorState(?act_state), Age(age_instance)->ActorStateHasCharacteristics(?act_state, age_instance)""") 
        Imp().set_as_rule("""ActorState(?act_state), Demographic(demographic_instance)->ActorStateHasCharacteristics(?act_state, demographic_instance)""") 
        Imp().set_as_rule("""ActorState(?act_state), Accessories(accessories_instance)->ActorStateHasCharacteristics(?act_state, accessories_instance)""")



    def determine_fatigue(self): 
        """ This function is used to create the rules to categorize the fatigue of the actor into threshold ranges based on the previous physiological values. * Awake * Sleeping 
        * Microsleep
        * Drowsy 
        * Drowsiness Suspected 
        * Undefined State
        """
    
        self.create_instances("Fatigue")
        # First Option where HR is Low and RR is High with corresponding KSS
        self.create_instances("Sleep") 

        self.create_instances("Awake") 

        self.create_instances("DrowsinessSuspected")

        self.create_instances("UndefinedState")

        rule_name = "undefined_critical_spo2"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), ActorStateHasPhysiologicalState(?act_st, ?spo2), 
                SpO2(?spo2), SpO2is(?spo2, ?critical), Critical_SpO2(?critical), 
                Fatigue(fatigue_instance), UndefinedState(?und)-> ActorStateHasFatigue(?act_st, fatigue_instance), FatigueIs(fatigue_instance, ?und)
                """
            )
        
        rule_name = "awake_rule_1" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr, ?lvl3), Level_3_KSS(?lvl3), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?mod_hr), Moderate_HR(?mod_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?mod_hrv), Moderate_HRV(?mod_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?mod_rr), Moderate_RR(?mod_rr), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?nor), Normal_SpO2(?nor), 
                Fatigue(fatigue_instance), Awake(?awake) -> ActorStateHasFatigue(?act_st, fatigue_instance), FatigueIs(fatigue_instance, ?awake) 
                """
            )


        rule_name = "awake_rule_2" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr, ?lvl3), Level_3_KSS(?lvl3), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?l_hr), Low_HR(?l_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?mod_hrv), Moderate_HRV(?mod_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?mod_rr), Moderate_RR(?mod_rr), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?nor), Normal_SpO2(?nor), 
                Fatigue(fatigue_instance), Awake(?awake) -> ActorStateHasFatigue(?act_st, fatigue_instance), FatigueIs(fatigue_instance, ?awake) 
                """
            )

        rule_name = "awake_rule_3" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr, ?lvl3), Level_3_KSS(?lvl3), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?l_hr), Low_HR(?l_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?high_hrv), High_HRV(?high_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?mod_rr), Moderate_RR(?mod_rr), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?nor), Normal_SpO2(?nor), 
                Fatigue(fatigue_instance), Awake(?awake) -> ActorStateHasFatigue(?act_st, fatigue_instance), FatigueIs(fatigue_instance, ?awake) 
                """
            )

        rule_name = "awake_rule_4" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr, ?lvl3), Level_3_KSS(?lvl3), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?l_hr), Low_HR(?l_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv),HRV(?hrv), HRVis(?hrv, ?mod_hrv), Moderate_HRV(?mod_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?l_rr), Low_RR(?l_rr), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?nor), Normal_SpO2(?nor), 
                Fatigue(fatigue_instance), Awake(?awake) -> ActorStateHasFatigue(?act_st, fatigue_instance), FatigueIs(fatigue_instance, ?awake) 
                """
            )

        rule_name = "awake_rule_5" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr, ?lvl3), Level_3_KSS(?lvl3), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?l_hr), Low_HR(?l_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?high_hrv), High_HRV(?high_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?l_rr), Low_RR(?l_rr), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?nor), Normal_SpO2(?nor), 
                Fatigue(fatigue_instance), Awake(?awake) -> ActorStateHasFatigue(?act_st, fatigue_instance), FatigueIs(fatigue_instance, ?awake) 
                """
            )
        
        rule_name = "awake_rule_6" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                # """
                # ActorState(?act_st),
                # ActorStateHasPhysiologicalState(?act_st, drowsiness_instance), Drowsiness(drowsiness_instance),DrowsinessIs(drowsiness_instance, ?lvl3), Level_3_KSS(?lvl3), 
                # ActorStateHasPhysiologicalState(?act_st, hr_instance), HR(hr_instance), HRis(hr_instance, ?mod_hr), Moderate_HR(?mod_hr), 
                # ActorStateHasPhysiologicalState(?act_st, hrv_instance), HRV(hrv_instance), HRVis(hrv_instance, ?high_hrv), High_HRV(?high_hrv), 
                # ActorStateHasPhysiologicalState(?act_st, rr_instance), RR(rr_instance), RRis(rr_instance, ?mod_rr), Moderate_RR(?mod_rr), 
                # ActorStateHasPhysiologicalState(?act_st, spo2_instance), SpO2(spo2_instance), SpO2is(spo2_instance, ?nor), Normal_SpO2(?nor), 
                # Fatigue(fatigue_instance), Awake(?awake) -> ActorStateHasFatigue(?act_st, fatigue_instance), FatigueIs(fatigue_instance, ?awake) 
                # """
                """
                ActorState(?act_st), ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr, ?lvl3), Level_3_KSS(?lvl3), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?mod_hr), Moderate_HR(?mod_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?high_hrv), High_HRV(?high_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?mod_rr), Moderate_RR(?mod_rr), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?nor), Normal_SpO2(?nor), 
                Fatigue(fatigue_instance), Awake(?awake) -> ActorStateHasFatigue(?act_st, fatigue_instance), FatigueIs(fatigue_instance, ?awake)

                """
            )

        rule_name = "awake_rule_7" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr, ?lvl3), Level_3_KSS(?lvl3), 
                ActorStateHasPhysiologicalState(?act_st, ?hr),HR(?hr), HRis(?hr, ?mod_hr), Moderate_HR(?mod_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hr), HRVis(?hrv, ?high_hrv), High_HRV(?high_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?l_rr), Low_RR(?l_rr), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?nor), Normal_SpO2(?nor), 
                Fatigue(fatigue_instance), Awake(?awake) -> ActorStateHasFatigue(?act_st, fatigue_instance), FatigueIs(fatigue_instance, ?awake) 
                """
            )

        rule_name = "awake_rule_8" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr, ?lvl3), Level_3_KSS(?lvl3), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?mod_hr), Moderate_HR(?mod_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?mod_hrv), Moderate_HRV(?mod_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?l_rr), Low_RR(?l_rr), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?nor), Normal_SpO2(?nor), 
                Fatigue(fatigue_instance), Awake(?awake) -> ActorStateHasFatigue(?act_st, fatigue_instance), FatigueIs(fatigue_instance, ?awake) 
                """
            )

        rule_name = "drowsy_awake_rule_1" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr, ?lvl5), Level_5_KSS(?lvl5), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?mod_hr), Moderate_HR(?mod_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?mod_hrv), Moderate_HRV(?mod_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?mod_rr), Moderate_RR(?mod_rr), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?nor), Normal_SpO2(?nor), 
                Fatigue(fatigue_instance), Awake(?awake), Level_3_KSS(?lvl3) -> ActorStateHasFatigue(?act_st, fatigue_instance), FatigueIs(fatigue_instance, ?awake), DrowsinessIs(?dr, ?lvl3) 
                """
            )


        rule_name = "drowsy_awake_rule_2" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr, ?lvl5), Level_5_KSS(?lvl5), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?mod_hr), Moderate_HR(?mod_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?l_hrv), High_HRV(?high_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?mod_rr), Moderate_RR(?mod_rr), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?nor), Normal_SpO2(?nor), 
                Fatigue(fatigue_instance), Awake(?awake), Level_3_KSS(?lvl3) -> ActorStateHasFatigue(?act_st, fatigue_instance), FatigueIs(fatigue_instance, ?awake), DrowsinessIs(?dr, ?lvl3) 
                """
            )

        rule_name = "sleep_rule_1"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), 
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr, ?lvl7), Level_7_KSS(?lvl7), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?vrl_hr), Very_Low_HR(?vrl_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?l_hrv), Low_HRV(?l_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?vlr_rr), Very_Low_RR(?vrl_rr), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?nor), Normal_SpO2(?nor), 
                Fatigue(fatigue_instance), Sleep(?sleep), Level_9_KSS(?lvl9) -> ActorStateHasFatigue(?act_st, fatigue_instance), FatigueIs(fatigue_instance, ?sleep), DrowsinessIs(?dr, ?lvl9) 
                """
            )

        rule_name = "sleep_rule_2"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), 
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr, ?lvl7), Level_7_KSS(?lvl7), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?vrl_hr), Very_Low_HR(?vrl_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?l_hrv), Low_HRV(?l_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?high_rr), High_RR(?high_rr), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?nor), Normal_SpO2(?nor), 
                Fatigue(fatigue_instance), Sleep(?sleep), Level_9_KSS(?lvl9) -> ActorStateHasFatigue(?act_st, fatigue_instance), FatigueIs(fatigue_instance, ?sleep), DrowsinessIs(?dr, ?lvl9) 
                """
            )

        rule_name = "sleep_rule_3"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), 
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr, ?lvl7), Level_7_KSS(?lvl7), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?high_hr), High_HR(?high_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?l_hrv), Low_HRV(?l_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?high_rr), High_RR(?high_rr), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?nor), Normal_SpO2(?nor), 
                Fatigue(fatigue_instance), Sleep(?sleep), Level_9_KSS(?lvl9) -> ActorStateHasFatigue(?act_st, fatigue_instance), FatigueIs(fatigue_instance, ?sleep), DrowsinessIs(?dr, ?lvl9) 
                """
            )

        rule_name = "sleep_rule_4"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), 
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr, ?lvl7), Level_7_KSS(?lvl7), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?high_hr), High_HR(?high_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?l_hrv), Low_HRV(?l_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?vrl_rr), Very_Low_RR(?vrl_rr), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?nor), Normal_SpO2(?nor), 
                Fatigue(fatigue_instance), Sleep(?sleep), Level_9_KSS(?lvl9) -> ActorStateHasFatigue(?act_st, fatigue_instance), FatigueIs(fatigue_instance, ?sleep), DrowsinessIs(?dr, ?lvl9) 
                """
            )

        rule_name = "sleep_rule_5"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), 
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr, ?lvl7), Level_7_KSS(?lvl7), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?high_hr), High_HR(?high_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?vrl_hrv), Very_Low_HRV(?vrl_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?high_rr), High_RR(?high_rr), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?nor), Normal_SpO2(?nor), 
                Fatigue(fatigue_instance), Sleep(?sleep), Level_9_KSS(?lvl9) -> ActorStateHasFatigue(?act_st, fatigue_instance), FatigueIs(fatigue_instance, ?sleep), DrowsinessIs(?dr, ?lvl9) 
                """
            )

        rule_name = "sleep_rule_6"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), 
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr, ?lvl7), Level_7_KSS(?lvl7), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?high_hr), High_HR(?high_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?vrl_hrv), Very_Low_HRV(?vrl_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?vrl_rr), Very_Low_RR(?vrl_rr), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?nor), Normal_SpO2(?nor), 
                Fatigue(fatigue_instance), Sleep(?sleep), Level_9_KSS(?lvl9) -> ActorStateHasFatigue(?act_st, fatigue_instance), FatigueIs(fatigue_instance, ?sleep), DrowsinessIs(?dr, ?lvl9) 
                """
            )

        rule_name = "sleep_rule_7"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), 
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr, ?lvl7), Level_7_KSS(?lvl7), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?vrl_hr), Very_Low_HR(?vrl_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?vrl_hrv), Very_Low_HRV(?vrl_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?high_rr), High_RR(?high_rr), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?nor), Normal_SpO2(?nor), 
                Fatigue(fatigue_instance), Sleep(?sleep), Level_9_KSS(?lvl9) -> ActorStateHasFatigue(?act_st, fatigue_instance), FatigueIs(fatigue_instance, ?sleep), DrowsinessIs(?dr, ?lvl9) 
                """
            )

        rule_name = "sleep_rule_8"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), 
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr, ?lvl7), Level_7_KSS(?lvl7), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?vrl_hr), Very_Low_HR(?vrl_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?vrl_hrv), Very_Low_HRV(?vrl_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?vrl_rr), Very_Low_RR(?vrl_rr), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?nor), Normal_SpO2(?nor), 
                Fatigue(fatigue_instance), Sleep(?sleep), Level_9_KSS(?lvl9) -> ActorStateHasFatigue(?act_st, fatigue_instance), FatigueIs(fatigue_instance, ?sleep), DrowsinessIs(?dr, ?lvl9) 
                """
            )
 
        rule_name = "drowsiness_suspected_1"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), 
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr, ?lvl3), Level_3_KSS(?lvl3), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?vrl_hr), Very_Low_HR(?vrl_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?l_hrv), Low_HRV(?l_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?high_rr), High_RR(?high_rr), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?nor), Normal_SpO2(?nor), 
                Fatigue(fatigue_instance), DrowsinessSuspected(?dr_sus), Level_5_KSS(?lvl5) -> ActorStateHasFatigue(?act_st, fatigue_instance), FatigueIs(fatigue_instance, ?dr_sus), DrowsinessIs(?dr, ?lvl5) 
                """
            ) 

        rule_name = "drowsiness_suspected_2"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), 
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr, ?lvl3), Level_3_KSS(?lvl3), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?vrl_hr), Very_Low_HR(?vrl_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?l_hrv), Low_HRV(?l_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?vrl_rr), Very_Low_RR(?vrl_rr), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?nor), Normal_SpO2(?nor), 
                Fatigue(fatigue_instance), DrowsinessSuspected(?dr_sus), Level_5_KSS(?lvl5) -> ActorStateHasFatigue(?act_st, fatigue_instance), FatigueIs(fatigue_instance, ?dr_sus), DrowsinessIs(?dr, ?lvl5) 
                """
            ) 

        rule_name = "drowsiness_suspected_3"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), 
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr, ?lvl3), Level_3_KSS(?lvl3), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?high_rr), High_HR(?high_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?l_hrv), Low_HRV(?l_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?high_rr), High_RR(?high_rr), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?nor), Normal_SpO2(?nor), 
                Fatigue(fatigue_instance), DrowsinessSuspected(?dr_sus), Level_5_KSS(?lvl5) -> ActorStateHasFatigue(?act_st, fatigue_instance), FatigueIs(fatigue_instance, ?dr_sus), DrowsinessIs(?dr, ?lvl5) 
                """
            ) 

        rule_name = "drowsiness_suspected_4"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), 
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr, ?lvl3), Level_3_KSS(?lvl3), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?high_rr), High_HR(?high_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?l_hrv), Low_HRV(?l_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?vrl_rr), Very_Low_RR(?vrl_rr), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?nor), Normal_SpO2(?nor), 
                Fatigue(fatigue_instance), DrowsinessSuspected(?dr_sus), Level_5_KSS(?lvl5) -> ActorStateHasFatigue(?act_st, fatigue_instance), FatigueIs(fatigue_instance, ?dr_sus), DrowsinessIs(?dr, ?lvl5) 
                """
            ) 

        rule_name = "drowsiness_suspected_5"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), 
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr, ?lvl3), Level_3_KSS(?lvl3), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?high_rr), High_HR(?high_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?vrl_hrv), Very_Low_HRV(?vrl_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?high_rr), High_RR(?high_rr), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?nor), Normal_SpO2(?nor), 
                Fatigue(fatigue_instance), DrowsinessSuspected(?dr_sus), Level_5_KSS(?lvl5) -> ActorStateHasFatigue(?act_st, fatigue_instance), FatigueIs(fatigue_instance, ?dr_sus), DrowsinessIs(?dr, ?lvl5) 
                """
            )

        rule_name = "drowsiness_suspected_6"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), 
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr, ?lvl3), Level_3_KSS(?lvl3), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?high_rr), High_HR(?high_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?vrl_hrv), Very_Low_HRV(?vrl_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?vrl_rr), Very_Low_RR(?vrl_rr), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?nor), Normal_SpO2(?nor), 
                Fatigue(fatigue_instance), DrowsinessSuspected(?dr_sus), Level_5_KSS(?lvl5) -> ActorStateHasFatigue(?act_st, fatigue_instance), FatigueIs(fatigue_instance, ?dr_sus), DrowsinessIs(?dr, ?lvl5) 
                """
            )

        rule_name = "drowsiness_suspected_7"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), 
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr, ?lvl3), Level_3_KSS(?lvl3), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?vrl_hr), Very_Low_HR(?vrl_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?vrl_hrv), Very_Low_HRV(?vrl_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?vrl_rr), Very_Low_RR(?vrl_rr), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?nor), Normal_SpO2(?nor), 
                Fatigue(fatigue_instance), DrowsinessSuspected(?dr_sus), Level_5_KSS(?lvl5) -> ActorStateHasFatigue(?act_st, fatigue_instance), FatigueIs(fatigue_instance, ?dr_sus), DrowsinessIs(?dr, ?lvl5) 
                """
            )

        rule_name = "drowsiness_suspected_8"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), 
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr, ?lvl3), Level_3_KSS(?lvl3), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?vrl_hr), Very_Low_HR(?vrl_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?vrl_hrv), Very_Low_HRV(?vrl_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?high_rr), High_RR(?high_rr), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?nor), Normal_SpO2(?nor), 
                Fatigue(fatigue_instance), DrowsinessSuspected(?dr_sus), Level_5_KSS(?lvl5) -> ActorStateHasFatigue(?act_st, fatigue_instance), FatigueIs(fatigue_instance, ?dr_sus), DrowsinessIs(?dr, ?lvl5) 
                """
            )

        rule_name = "drowsy_low_spo2_1" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr,?lvl5), Level_5_KSS(?lvl5), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?l_spo2), Low_SpO2(?l_spo2), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?mod_hr), Moderate_HR(?mod_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?mod_hrv), Moderate_HRV(?mod_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?mod_rr), Moderate_RR(?mod_rr), 
                Fatigue(fatigue_instance), DrowsinessSuspected(?dr_sus), Level_7_KSS(?lvl7) -> ActorStateHasFatigue(?act_st, fatigue_instance), FatigueIs(fatigue_instance, ?dr_sus), DrowsinessIs(?dr, ?lvl7)
                """
            )

        rule_name = "drowsy_low_spo2_2" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr,?lvl5), Level_5_KSS(?lvl5), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?l_spo2), Low_SpO2(?l_spo2), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?mod_hr), Moderate_HR(?mod_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?high_hrv), High_HRV(?high_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?mod_rr), Moderate_RR(?mod_rr), 
                Fatigue(fatigue_instance), DrowsinessSuspected(?dr_sus), Level_7_KSS(?lvl7) -> ActorStateHasFatigue(?act_st, fatigue_instance), FatigueIs(fatigue_instance, ?dr_sus), DrowsinessIs(?dr, ?lvl7)
                """
            )

        rule_name = "drowsy_low_spo2_3" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr,?lvl3), Level_3_KSS(?lvl3), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?l_spo2), Low_SpO2(?l_spo2), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?mod_hr), Moderate_HR(?mod_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?high_hrv), High_HRV(?high_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?mod_rr), Moderate_RR(?mod_rr), 
                Fatigue(fatigue_instance), DrowsinessSuspected(?dr_sus), Level_5_KSS(?lvl5) -> ActorStateHasFatigue(?act_st, fatigue_instance), FatigueIs(fatigue_instance, ?dr_sus), DrowsinessIs(?dr, ?lvl5)
                """
            )


        rule_name = "drowsy_low_spo2_3" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr,?lvl3), Level_3_KSS(?lvl3), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?l_spo2), Low_SpO2(?l_spo2), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?mod_hr), Moderate_HR(?mod_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?mod_hrv), Moderate_HRV(?mod_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?mod_rr), Moderate_RR(?mod_rr), 
                Fatigue(fatigue_instance), DrowsinessSuspected(?dr_sus), Level_5_KSS(?lvl5) -> ActorStateHasFatigue(?act_st, fatigue_instance), FatigueIs(fatigue_instance, ?dr_sus), DrowsinessIs(?dr, ?lvl5)
                """
            )


    def determine_attention(self): 
        self.create_instances("AttentionLevels")
        # First Option where HR is Low and RR is High with corresponding KSS
        self.create_instances("Attentive") 

        self.create_instances("Inattentive") 

        self.create_instances("Undefined")

        rule_name = "undefined_att_1" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), ActorStateHasPhysiologicalState(?act_st, ?spo2), 
                SpO2(?spo2), SpO2is(?spo2, ?crit), Critical_SpO2(?crit), 
                AttentionLevels(?att), UndefinedState(?dnf) -> ActorStateHasAttention(?act_st, ?att), AttentionIs(?att, ?dnf)
                """
            )

        rule_name = "attentive_1" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr,?lvl3), Level_3_KSS(?lvl3), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?l_spo2), Low_SpO2(?l_spo2), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?mod_hr), Moderate_HR(?mod_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?mod_hrv), Moderate_HRV(?mod_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?mod_rr), Moderate_RR(?mod_rr), 
                AttentionLevels(attention_instance), Attentive(?mod_att), Level_5_KSS(?lvl5) ->
                ActorStateHasAttention(?act_st, attention_instance), AttentionIs(attention_instance, ?mod_att), DrowsinessIs(?dr, ?lvl5)
                """
            )

        
        rule_name = "attentive_2" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr,?lvl3), Level_3_KSS(?lvl3), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?l_spo2), Low_SpO2(?l_spo2), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?l_hr), Low_HR(?l_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?mod_hrv), Moderate_HRV(?mod_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?mod_rr), Moderate_RR(?mod_rr), 
                AttentionLevels(attention_instance), Attentive(?mod_att), Level_5_KSS(?lvl5) ->
                ActorStateHasAttention(?act_st, attention_instance), AttentionIs(attention_instance, ?mod_att), DrowsinessIs(?dr, ?lvl5)
                """
            )


        rule_name = "attentive_3" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr,?lvl3), Level_3_KSS(?lvl3), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?l_spo2), Low_SpO2(?l_spo2), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?mod_hr), Moderate_HR(?mod_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?high_hrv), High_HRV(?high_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?mod_rr), Moderate_RR(?mod_rr), 
                AttentionLevels(attention_instance), Attentive(?mod_att), Level_5_KSS(?lvl5) ->
                ActorStateHasAttention(?act_st, attention_instance), AttentionIs(attention_instance, ?mod_att), DrowsinessIs(?dr, ?lvl5)
                """
            )

        rule_name = "attentive_4" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr,?lvl3), Level_3_KSS(?lvl3), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?l_spo2), Low_SpO2(?l_spo2), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?l_hr), Low_HR(?l_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?high_hrv), High_HRV(?high_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?l_rr), Low_RR(?l_rr), 
                AttentionLevels(attention_instance), Attentive(?mod_att), Level_5_KSS(?lvl5) ->
                ActorStateHasAttention(?act_st, attention_instance), AttentionIs(attention_instance, ?mod_att), DrowsinessIs(?dr, ?lvl5)
                """
            )

        rule_name = "attentive_5" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr,?lvl3), Level_3_KSS(?lvl3), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?l_spo2), Low_SpO2(?l_spo2), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?mod_hr), Moderate_HR(?mod_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?high_hrv), High_HRV(?high_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?l_rr), Low_RR(?l_rr), 
                AttentionLevels(attention_instance), Attentive(?mod_att), Level_5_KSS(?lvl5) ->
                ActorStateHasAttention(?act_st, attention_instance), AttentionIs(attention_instance, ?mod_att), DrowsinessIs(?dr, ?lvl5)
                """
            )

        rule_name = "attentive_3_1" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr,?lvl3), Level_3_KSS(?lvl3), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?l_spo2), Low_SpO2(?l_spo2), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?mod_hr), Moderate_HR(?mod_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?mod_hrv), Moderate_HRV(?mod_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?mod_rr), Moderate_RR(?mod_rr), 
                AttentionLevels(attention_instance), Attentive(?mod_att), Level_5_KSS(?lvl5) ->
                ActorStateHasAttention(?act_st, attention_instance), AttentionIs(attention_instance, ?mod_att), DrowsinessIs(?dr, ?lvl5)
                """
            )

        rule_name = "attentive_4_1" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr,?lvl3), Level_3_KSS(?lvl3), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?l_spo2), Low_SpO2(?l_spo2), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?l_hr), Low_HR(?l_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?mod_hrv), Moderate_HRV(?mod_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?l_rr), Low_RR(?l_rr), 
                AttentionLevels(attention_instance), Attentive(?mod_att), Level_5_KSS(?lvl5) ->
                ActorStateHasAttention(?act_st, attention_instance), AttentionIs(attention_instance, ?mod_att), DrowsinessIs(?dr, ?lvl5)
                """
            )

        rule_name = "attentive_5_1" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr,?lvl3), Level_3_KSS(?lvl3), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?l_spo2), Low_SpO2(?l_spo2), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?mod_hr), Moderate_HR(?mod_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?mod_hrv), Moderate_HRV(?mod_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?l_rr), Low_RR(?l_rr), 
                AttentionLevels(attention_instance), Attentive(?mod_att), Level_5_KSS(?lvl5) ->
                ActorStateHasAttention(?act_st, attention_instance), AttentionIs(attention_instance, ?mod_att), DrowsinessIs(?dr, ?lvl5)
                """
            )

        rule_name = "attentive_6" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr,?lvl3), Level_3_KSS(?lvl3), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?nor_spo2), Normal_SpO2(?nor_spo2), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?mod_hr), Moderate_HR(?mod_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?mod_hrv), Moderate_HRV(?mod_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?mod_rr), Moderate_RR(?mod_rr), 
                AttentionLevels(attention_instance), Attentive(?high_att) ->
                ActorStateHasAttention(?act_st, attention_instance), AttentionIs(attention_instance, ?high_att)
                """
            )

        rule_name = "attentive_7" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr,?lvl5), Level_5_KSS(?lvl5), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?nor_spo2), Normal_SpO2(?nor_spo2), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?mod_hr), Moderate_HR(?mod_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?mod_hrv), Moderate_HRV(?mod_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?mod_rr), Moderate_RR(?mod_rr), 
                AttentionLevels(attention_instance), Attentive(?high_att), Level_3_KSS(?lvl3) ->
                ActorStateHasAttention(?act_st, attention_instance), AttentionIs(attention_instance, ?high_att), DrowsinessIs(?dr, ?lvl3)
                """
            )

        rule_name = "attentive_8" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr,?lvl5), Level_5_KSS(?lvl5), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?nor_spo2), Normal_SpO2(?nor_spo2), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?mod_hr), Moderate_HR(?mod_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?high_hrv), High_HRV(?high_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?mod_rr), Moderate_RR(?mod_rr), 
                AttentionLevels(attention_instance), Attentive(?high_att), Level_3_KSS(?lvl3) ->
                ActorStateHasAttention(?act_st, attention_instance), AttentionIs(attention_instance, ?high_att), DrowsinessIs(?dr, ?lvl3)
                """
            )

        rule_name = "attentive_9" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr),  DrowsinessIs(?dr, ?lvl3), Level_3_KSS(?lvl3), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2),  SpO2is(?spo2, ?nor_spo2), Normal_SpO2(?nor_spo2), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr),  HRis(?hr, ?mod_hr), Moderate_HR(?mod_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?high_hrv), High_HRV(?high_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?mod_rr), Moderate_RR(?mod_rr), 
                AttentionLevels(attention_instance), Attentive(?mod_att) -> ActorStateHasAttention(?act_st, attention_instance), AttentionIs(attention_instance, ?mod_att) 
                """
            )

        rule_name = "attentive_10" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr,?lvl3), Level_3_KSS(?lvl3), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?nor_spo2), Normal_SpO2(?nor_spo2), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?high_hr), High_HR(?high_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?l_hrv), Low_HRV(?l_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?high_rr), High_RR(?high_rr), 
                AttentionLevels(attention_instance), Attentive(?mod_att), Level_5_KSS(?lvl5) ->
                ActorStateHasAttention(?act_st, attention_instance), AttentionIs(attention_instance, ?mod_att), DrowsinessIs(?dr, ?lvl5)
                """
            )

        rule_name = "attentive_11" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr,?lvl3), Level_3_KSS(?lvl3), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?nor_spo2), Normal_SpO2(?nor_spo2), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?vrl_hr), Very_Low_HR(?vrl_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?l_hrv), Low_HRV(?l_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?high_rr), High_RR(?high_rr), 
                AttentionLevels(attention_instance), Attentive(?mod_att), Level_5_KSS(?lvl5) ->
                ActorStateHasAttention(?act_st, attention_instance), AttentionIs(attention_instance, ?mod_att), DrowsinessIs(?dr, ?lvl5)
                """
            )

        rule_name = "attentive_12" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr,?lvl3), Level_3_KSS(?lvl3), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?nor_spo2), Normal_SpO2(?nor_spo2), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?vrl_hr), Very_Low_HR(?vrl_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?l_hrv), Low_HRV(?l_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?vrl_rr), Very_Low_RR(?vrl_rr), 
                AttentionLevels(attention_instance), Attentive(?mod_att), Level_5_KSS(?lvl5) ->
                ActorStateHasAttention(?act_st, attention_instance), AttentionIs(attention_instance, ?mod_att), DrowsinessIs(?dr, ?lvl5)
                """
            )

        rule_name = "attentive_13" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr,?lvl3), Level_3_KSS(?lvl3), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?nor_spo2), Normal_SpO2(?nor_spo2), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?high_hr), High_HR(?high_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?l_hrv), Low_HRV(?l_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?vrl_rr), Very_Low_RR(?vrl_rr), 
                AttentionLevels(attention_instance), Attentive(?mod_att), Level_5_KSS(?lvl5) ->
                ActorStateHasAttention(?act_st, attention_instance), AttentionIs(attention_instance, ?mod_att), DrowsinessIs(?dr, ?lvl5)
                """
            )

        rule_name = "attentive_10_1" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr,?lvl3), Level_3_KSS(?lvl3), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?nor_spo2), Normal_SpO2(?nor_spo2), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?high_hr), High_HR(?high_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?vrl_hrv), Very_Low_HRV(?vrl_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?high_rr), High_RR(?high_rr), 
                AttentionLevels(attention_instance), Attentive(?mod_att), Level_5_KSS(?lvl5) ->
                ActorStateHasAttention(?act_st, attention_instance), AttentionIs(attention_instance, ?mod_att), DrowsinessIs(?dr, ?lvl5)
                """
            )

        rule_name = "attentive_11_1" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr,?lvl3), Level_3_KSS(?lvl3), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?nor_spo2), Normal_SpO2(?nor_spo2), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?vrl_hr), Very_Low_HR(?vrl_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?vrl_hrv), Very_Low_HRV(?vrl_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?high_rr), High_RR(?high_rr), 
                AttentionLevels(attention_instance), Attentive(?mod_att), Level_5_KSS(?lvl5) ->
                ActorStateHasAttention(?act_st, attention_instance), AttentionIs(attention_instance, ?mod_att), DrowsinessIs(?dr, ?lvl5)
                """
            )
    
        rule_name = "attentive_12_1" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr,?lvl3), Level_3_KSS(?lvl3), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?nor_spo2), Normal_SpO2(?nor_spo2), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?vrl_hr), Very_Low_HR(?vrl_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?vrl_hrv), Very_Low_HRV(?vrl_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?vrl_rr), Very_Low_RR(?vrl_rr), 
                AttentionLevels(attention_instance), Attentive(?mod_att), Level_5_KSS(?lvl5) ->
                ActorStateHasAttention(?act_st, attention_instance), AttentionIs(attention_instance, ?mod_att), DrowsinessIs(?dr, ?lvl5)
                """
            )

        rule_name = "attentive_13_1" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr,?lvl3), Level_3_KSS(?lvl3), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?nor_spo2), Normal_SpO2(?nor_spo2), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?high_hr), High_HR(?high_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?vrl_hrv), Very_Low_HRV(?vrl_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?vrl_rr), Very_Low_RR(?vrl_rr), 
                AttentionLevels(attention_instance), Attentive(?mod_att), Level_5_KSS(?lvl5) ->
                ActorStateHasAttention(?act_st, attention_instance), AttentionIs(attention_instance, ?mod_att), DrowsinessIs(?dr, ?lvl5)
                """
            )


        rule_name = "attentive_10_2" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr,?lvl3), Level_3_KSS(?lvl3), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?nor_spo2), Normal_SpO2(?nor_spo2), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?l_hr), Low_HR(?l_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?vrl_hrv), Very_Low_HRV(?vrl_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?high_rr), High_RR(?high_rr), 
                AttentionLevels(attention_instance), Attentive(?mod_att), Level_5_KSS(?lvl5) ->
                ActorStateHasAttention(?act_st, attention_instance), AttentionIs(attention_instance, ?mod_att), DrowsinessIs(?dr, ?lvl5)
                """
            )

        rule_name = "attentive_11_2" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr,?lvl3), Level_3_KSS(?lvl3), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?nor_spo2), Normal_SpO2(?nor_spo2), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?l_hr), Low_HR(?l_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?vrl_hrv), Very_Low_HRV(?vrl_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?vrl_rr), Very_Low_RR(?vrl_rr), 
                AttentionLevels(attention_instance), Attentive(?mod_att), Level_5_KSS(?lvl5) ->
                ActorStateHasAttention(?act_st, attention_instance), AttentionIs(attention_instance, ?mod_att), DrowsinessIs(?dr, ?lvl5)
                """
            )

        rule_name = "attentive_12_2" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr,?lvl3), Level_3_KSS(?lvl3), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?nor_spo2), Normal_SpO2(?nor_spo2), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?vrl_hr), Very_Low_HR(?vrl_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?vrl_hrv), Very_Low_HRV(?vrl_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?l_rr), Low_RR(?l_rr), 
                AttentionLevels(attention_instance), Attentive(?mod_att), Level_5_KSS(?lvl5) ->
                ActorStateHasAttention(?act_st, attention_instance), AttentionIs(attention_instance, ?mod_att), DrowsinessIs(?dr, ?lvl5)
                """
            )

        rule_name = "attentive_13_2" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr,?lvl3), Level_3_KSS(?lvl3), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?nor_spo2), Normal_SpO2(?nor_spo2), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?high_hr), High_HR(?high_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?vrl_hrv), Very_Low_HRV(?vrl_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?vrl_rr), Very_Low_RR(?vrl_rr), 
                AttentionLevels(attention_instance), Attentive(?mod_att), Level_5_KSS(?lvl5) ->
                ActorStateHasAttention(?act_st, attention_instance), AttentionIs(attention_instance, ?mod_att), DrowsinessIs(?dr, ?lvl5)
                """
            )


        rule_name = "attentive_10_3" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr,?lvl3), Level_3_KSS(?lvl3), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?nor_spo2), Normal_SpO2(?nor_spo2), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?l_hr), Low_HR(?l_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?l_hrv), Low_HRV(?l_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?high_rr), High_RR(?high_rr), 
                AttentionLevels(attention_instance), Attentive(?mod_att), Level_5_KSS(?lvl5) ->
                ActorStateHasAttention(?act_st, attention_instance), AttentionIs(attention_instance, ?mod_att), DrowsinessIs(?dr, ?lvl5)
                """
            )

        rule_name = "attentive_11_3" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr,?lvl3), Level_3_KSS(?lvl3), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?nor_spo2), Normal_SpO2(?nor_spo2), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?l_hr), Low_HR(?l_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?l_hrv), Low_HRV(?l_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?vrl_rr), Very_Low_RR(?vrl_rr), 
                AttentionLevels(attention_instance), Attentive(?mod_att), Level_5_KSS(?lvl5) ->
                ActorStateHasAttention(?act_st, attention_instance), AttentionIs(attention_instance, ?mod_att), DrowsinessIs(?dr, ?lvl5)
                """
            )

        rule_name = "attentive_12_3" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr,?lvl3), Level_3_KSS(?lvl3), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?nor_spo2), Normal_SpO2(?nor_spo2), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?vrl_hr), Very_Low_HR(?vrl_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?l_hrv), Low_HRV(?l_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?l_rr), Low_RR(?l_rr), 
                AttentionLevels(attention_instance), Attentive(?mod_att), Level_5_KSS(?lvl5) ->
                ActorStateHasAttention(?act_st, attention_instance), AttentionIs(attention_instance, ?mod_att), DrowsinessIs(?dr, ?lvl5)
                """
            )

        rule_name = "attentive_13_3" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr,?lvl3), Level_3_KSS(?lvl3), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?nor_spo2), Normal_SpO2(?nor_spo2), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?high_hr), High_HR(?high_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?l_hrv), Low_HRV(?l_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?vrl_rr), Very_Low_RR(?vrl_rr), 
                AttentionLevels(attention_instance), Attentive(?mod_att), Level_5_KSS(?lvl5) ->
                ActorStateHasAttention(?act_st, attention_instance), AttentionIs(attention_instance, ?mod_att), DrowsinessIs(?dr, ?lvl5)
                """
            )

        rule_name = "attentive_14" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr,?lvl3), Level_3_KSS(?lvl3), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?nor_spo2), Normal_SpO2(?nor_spo2), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?l_hr), Low_HR(?l_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?l_hrv), Low_HRV(?l_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?l_rr), Low_RR(?l_rr), 
                AttentionLevels(attention_instance), Attentive(?mod_att), Level_5_KSS(?lvl5) ->
                ActorStateHasAttention(?act_st, attention_instance), AttentionIs(attention_instance, ?mod_att), DrowsinessIs(?dr, ?lvl5)
                """
            )

        rule_name = "attentive_15" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr,?lvl3), Level_3_KSS(?lvl3), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?nor_spo2), Normal_SpO2(?nor_spo2), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?l_hr), Low_HR(?l_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?vrl_hrv), Very_Low_HRV(?vrl_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?l_rr), Low_RR(?l_rr), 
                AttentionLevels(attention_instance), Attentive(?mod_att), Level_5_KSS(?lvl5) ->
                ActorStateHasAttention(?act_st, attention_instance), AttentionIs(attention_instance, ?mod_att), DrowsinessIs(?dr, ?lvl5)
                """
            )
        
        rule_name = "inattentive_1" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr, ?lvl9), 
                Level_9_KSS(?lvl9), AttentionLevels(attention_instance), Inattentive(?inatt) ->
                ActorStateHasAttention(?act_st, attention_instance), AttentionIs(attention_instance, ?inatt)
                """
            )

        rule_name = "inattentive_2" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr, ?lvl7), Level_7_KSS(?lvl7),
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?nor_spo2), Normal_SpO2(?nor_spo2), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?mod_hr), Moderate_HR(?mod_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?mod_hrv), Moderate_HRV(?mod_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?mod_rr), Moderate_RR(?mod_rr), 
                AttentionLevels(attention_instance), Inattentive(?inatt) ->
                ActorStateHasAttention(?act_st, attention_instance), AttentionIs(attention_instance, ?inatt)
                """
            )

        rule_name = "inattentive_3" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr, ?lvl7), Level_7_KSS(?lvl7),
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?l_spo2), Low_SpO2(?l_spo2), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?mod_hr), Moderate_HR(?mod_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?mod_hrv), Moderate_HRV(?mod_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?mod_rr), Moderate_RR(?mod_rr), 
                AttentionLevels(attention_instance), Inattentive(?inatt), Level_9_KSS(?lvl9) ->
                ActorStateHasAttention(?act_st, attention_instance), AttentionIs(attention_instance, ?inatt), DrowsinessIs(?dr, ?lvl9)
                """
            )

        rule_name = "inattentive_4" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr, ?lvl7), Level_7_KSS(?lvl7),
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?l_spo2), Low_SpO2(?l_spo2), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?mod_hr), Moderate_HR(?mod_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?high_hrv), High_HRV(?high_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?mod_rr), Moderate_RR(?mod_rr), 
                AttentionLevels(attention_instance), Inattentive(?inatt), Level_9_KSS(?lvl9) ->
                ActorStateHasAttention(?act_st, attention_instance), AttentionIs(attention_instance, ?inatt), DrowsinessIs(?dr, ?lvl9)
                """
            )

        rule_name = "inattentive_5" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr, ?lvl7), Level_7_KSS(?lvl7),
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?nor_spo2), Normal_SpO2(?nor_spo2), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?high_hr), High_HR(?high_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?l_hrv), Low_HRV(?l_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?high_rr), High_RR(?high_rr), 
                AttentionLevels(attention_instance), Inattentive(?inatt), Level_9_KSS(?lvl9) ->
                ActorStateHasAttention(?act_st, attention_instance), AttentionIs(attention_instance, ?inatt), DrowsinessIs(?dr, ?lvl9)
                """
            )

        rule_name = "inattentive_6" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr, ?lvl7), Level_7_KSS(?lvl7),
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?nor_spo2), Normal_SpO2(?nor_spo2), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?vrl_hr), Very_Low_HR(?vrl_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?l_hrv), Low_HRV(?l_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?high_rr), High_RR(?high_rr), 
                AttentionLevels(attention_instance), Inattentive(?inatt), Level_9_KSS(?lvl9) ->
                ActorStateHasAttention(?act_st, attention_instance), AttentionIs(attention_instance, ?inatt), DrowsinessIs(?dr, ?lvl9)
                """
            )

        rule_name = "inattentive_7" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr, ?lvl7), Level_7_KSS(?lvl7),
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?nor_spo2), Normal_SpO2(?nor_spo2), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?vrl_hr), Very_Low_HR(?vrl_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?l_hrv), Low_HRV(?l_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?vrl_rr), Very_Low_RR(?vrl_rr), 
                AttentionLevels(attention_instance), Inattentive(?inatt), Level_9_KSS(?lvl9) ->
                ActorStateHasAttention(?act_st, attention_instance), AttentionIs(attention_instance, ?inatt), DrowsinessIs(?dr, ?lvl9)
                """
            )

        rule_name = "inattentive_8" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr, ?lvl7), Level_7_KSS(?lvl7),
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?nor_spo2), Normal_SpO2(?nor_spo2), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?high_hr), High_HR(?high_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?l_hrv), Low_HRV(?l_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?vrl_rr), Very_Low_RR(?vrl_rr), 
                AttentionLevels(attention_instance), Inattentive(?inatt), Level_9_KSS(?lvl9) ->
                ActorStateHasAttention(?act_st, attention_instance), AttentionIs(attention_instance, ?inatt), DrowsinessIs(?dr, ?lvl9)
                """
            )

        rule_name = "inattentive_9" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr, ?lvl7), Level_7_KSS(?lvl7),
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?nor_spo2), Normal_SpO2(?nor_spo2), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?high_hr), High_HR(?high_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?vrl_hrv), Very_Low_HRV(?vrl_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?high_rr), High_RR(?high_rr), 
                AttentionLevels(attention_instance), Inattentive(?inatt), Level_9_KSS(?lvl9) ->
                ActorStateHasAttention(?act_st, attention_instance), AttentionIs(attention_instance, ?inatt), DrowsinessIs(?dr, ?lvl9)
                """
            )

        rule_name = "inattentive_10" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr, ?lvl7), Level_7_KSS(?lvl7),
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?nor_spo2), Normal_SpO2(?nor_spo2), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?vrl_hr), Very_Low_HR(?vrl_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?vrl_hrv), Very_Low_HRV(?vrl_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?high_rr), High_RR(?high_rr), 
                AttentionLevels(attention_instance), Inattentive(?inatt), Level_9_KSS(?lvl9) ->
                ActorStateHasAttention(?act_st, attention_instance), AttentionIs(attention_instance, ?inatt), DrowsinessIs(?dr, ?lvl9)
                """
            )

        rule_name = "inattentive_11" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr, ?lvl7), Level_7_KSS(?lvl7),
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?nor_spo2), Normal_SpO2(?nor_spo2), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?vrl_hr), Very_Low_HR(?vrl_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?vrl_hrv), Very_Low_HRV(?vrl_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?vrl_rr), Very_Low_RR(?vrl_rr), 
                AttentionLevels(attention_instance), Inattentive(?inatt), Level_9_KSS(?lvl9) ->
                ActorStateHasAttention(?act_st, attention_instance), AttentionIs(attention_instance, ?inatt), DrowsinessIs(?dr, ?lvl9)
                """
            )

        rule_name = "inattentive_12" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr, ?lvl7), Level_7_KSS(?lvl7),
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?nor_spo2), Normal_SpO2(?nor_spo2), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?high_hr), High_HR(?high_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?vrl_hrv), Very_Low_HRV(?vrl_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?vrl_rr), Very_Low_RR(?vrl_rr), 
                AttentionLevels(attention_instance), Inattentive(?inatt), Level_9_KSS(?lvl9) ->
                ActorStateHasAttention(?act_st, attention_instance), AttentionIs(attention_instance, ?inatt), DrowsinessIs(?dr, ?lvl9)
                """
            )

        rule_name = "inattentive_13" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr, ?lvl5), Level_5_KSS(?lvl5),
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?nor_spo2), Normal_SpO2(?nor_spo2), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?high_hr), High_HR(?high_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?vrl_hrv), Very_Low_HRV(?vrl_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?vrl_rr), Very_Low_RR(?vrl_rr), 
                AttentionLevels(attention_instance), Inattentive(?inatt), Level_7_KSS(?lvl7) ->
                ActorStateHasAttention(?act_st, attention_instance), AttentionIs(attention_instance, ?inatt), DrowsinessIs(?dr, ?lvl7)
                """
            )

        rule_name = "inattentive_14" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr, ?lvl5), Level_5_KSS(?lvl5),
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?nor_spo2), Normal_SpO2(?nor_spo2), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?vrl_hr), Very_Low_HR(?vrl_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?vrl_hrv), Very_Low_HRV(?vrl_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?vrl_rr), Very_Low_RR(?vrl_rr), 
                AttentionLevels(attention_instance), Inattentive(?inatt), Level_7_KSS(?lvl7) ->
                ActorStateHasAttention(?act_st, attention_instance), AttentionIs(attention_instance, ?inatt), DrowsinessIs(?dr, ?lvl7)
                """
            )

        rule_name = "inattentive_15" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr, ?lvl5), Level_5_KSS(?lvl5),
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?nor_spo2), Normal_SpO2(?nor_spo2), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?vrl_hr), Very_Low_HR(?vrl_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?vrl_hrv), Very_Low_HRV(?vrl_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?high_rr), High_RR(?high_rr), 
                AttentionLevels(attention_instance), Inattentive(?inatt), Level_7_KSS(?lvl7) ->
                ActorStateHasAttention(?act_st, attention_instance), AttentionIs(attention_instance, ?inatt), DrowsinessIs(?dr, ?lvl7)
                """
            )

        rule_name = "inattentive_16" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr, ?lvl5), Level_5_KSS(?lvl5),
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?nor_spo2), Normal_SpO2(?nor_spo2), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?high_hr), High_HR(?high_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?vrl_hrv), Very_Low_HRV(?vrl_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?high_rr), High_RR(?high_rr), 
                AttentionLevels(attention_instance), Inattentive(?inatt), Level_7_KSS(?lvl7) ->
                ActorStateHasAttention(?act_st, attention_instance), AttentionIs(attention_instance, ?inatt), DrowsinessIs(?dr, ?lvl7)
                """
            )

        rule_name = "inattentive_17" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr, ?lvl5), Level_5_KSS(?lvl5),
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?l_spo2), Low_SpO2(?l_spo2), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?mod_hr), Moderate_HR(?mod_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?mod_hrv), Moderate_HRV(?mod_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?mod_rr), Moderate_RR(?mod_rr), 
                AttentionLevels(attention_instance), Inattentive(?inatt), Level_7_KSS(?lvl7) ->
                ActorStateHasAttention(?act_st, attention_instance), AttentionIs(attention_instance, ?inatt), DrowsinessIs(?dr, ?lvl7)
                """
            )

        rule_name = "inattentive_18" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr, ?lvl5), Level_5_KSS(?lvl5),
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?l_spo2), Low_SpO2(?l_spo2), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?mod_hr), Moderate_HR(?mod_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?high_hrv), High_HR(?high_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?mod_rr), Moderate_RR(?mod_rr), 
                AttentionLevels(attention_instance), Inattentive(?inatt), Level_7_KSS(?lvl7) ->
                ActorStateHasAttention(?act_st, attention_instance), AttentionIs(attention_instance, ?inatt), DrowsinessIs(?dr, ?lvl7)
                """
            )

        rule_name = "inattentive_19" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr, ?lvl5), Level_5_KSS(?lvl5),
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?l_spo2), Low_SpO2(?l_spo2), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?high_hr), High_HR(?high_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?l_hrv), Low_HRV(?l_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?high_rr), High_RR(?high_rr), 
                AttentionLevels(attention_instance), Inattentive(?inatt), Level_9_KSS(?lvl9) ->
                ActorStateHasAttention(?act_st, attention_instance), AttentionIs(attention_instance, ?inatt), DrowsinessIs(?dr, ?lvl9)
                """
            )

        rule_name = "inattentive_20" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr, ?lvl5), Level_5_KSS(?lvl5),
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?l_spo2), Low_SpO2(?l_spo2), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?vrl_hr), Very_Low_HR(?vrl_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?l_hrv), Low_HRV(?l_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?high_rr), High_RR(?high_rr), 
                AttentionLevels(attention_instance), Inattentive(?inatt), Level_9_KSS(?lvl9) ->
                ActorStateHasAttention(?act_st, attention_instance), AttentionIs(attention_instance, ?inatt), DrowsinessIs(?dr, ?lvl9)
                """
            )

        rule_name = "inattentive_21" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr, ?lvl5), Level_5_KSS(?lvl5),
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?l_spo2), Low_SpO2(?l_spo2), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?vrl_hr), Very_Low_HR(?vrl_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?l_hrv), Low_HRV(?l_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?vrl_rr), Very_Low_RR(?vrl_rr), 
                AttentionLevels(attention_instance), Inattentive(?inatt), Level_9_KSS(?lvl9) ->
                ActorStateHasAttention(?act_st, attention_instance), AttentionIs(attention_instance, ?inatt), DrowsinessIs(?dr, ?lvl9)
                """
            )

        rule_name = "inattentive_22" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr, ?lvl5), Level_5_KSS(?lvl5),
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?l_spo2), Low_SpO2(?l_spo2), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?high_hr), High_HR(?high_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?l_hrv), Low_HRV(?l_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?vrl_rr), Very_Low_RR(?vrl_rr), 
                AttentionLevels(attention_instance), Inattentive(?inatt), Level_9_KSS(?lvl9) ->
                ActorStateHasAttention(?act_st, attention_instance), AttentionIs(attention_instance, ?inatt), DrowsinessIs(?dr, ?lvl9)
                """
            )

        rule_name = "inattentive_23" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr, ?lvl5), Level_5_KSS(?lvl5),
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?l_spo2), Low_SpO2(?l_spo2), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?vrl_hr), Very_Low_HR(?vrl_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?vrl_hrv), Very_Low_HRV(?vrl_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?high_rr), High_RR(?high_rr), 
                AttentionLevels(attention_instance), Inattentive(?inatt), Level_9_KSS(?lvl9) ->
                ActorStateHasAttention(?act_st, attention_instance), AttentionIs(attention_instance, ?inatt), DrowsinessIs(?dr, ?lvl9)
                """
            )

        rule_name = "inattentive_24" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr, ?lvl5), Level_5_KSS(?lvl5),
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?l_spo2), Low_SpO2(?l_spo2), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?vrl_hr), Very_Low_HR(?vrl_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?vrl_hrv), Very_Low_HRV(?vrl_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?vrl_rr), Very_Low_RR(?vrl_rr), 
                AttentionLevels(attention_instance), Inattentive(?inatt), Level_9_KSS(?lvl9) ->
                ActorStateHasAttention(?act_st, attention_instance), AttentionIs(attention_instance, ?inatt), DrowsinessIs(?dr, ?lvl9)
                """
            )

        rule_name = "inattentive_25" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr, ?lvl5), Level_5_KSS(?lvl5),
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?l_spo2), Low_SpO2(?l_spo2), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?high_hr), High_HR(?high_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?vrl_hrv), Very_Low_HRV(?vrl_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?vrl_rr), Very_Low_RR(?vrl_rr), 
                AttentionLevels(attention_instance), Inattentive(?inatt), Level_9_KSS(?lvl9) ->
                ActorStateHasAttention(?act_st, attention_instance), AttentionIs(attention_instance, ?inatt), DrowsinessIs(?dr, ?lvl9)
                """
            )

        rule_name = "inattentive_26" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr, ?lvl5), Level_5_KSS(?lvl5),
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?l_spo2), Low_SpO2(?l_spo2), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?high_hr), High_HR(?high_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?vrl_hrv), Very_Low_HRV(?vrl_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?high_rr), High_RR(?high_rr), 
                AttentionLevels(attention_instance), Inattentive(?inatt), Level_9_KSS(?lvl9) ->
                ActorStateHasAttention(?act_st, attention_instance), AttentionIs(attention_instance, ?inatt), DrowsinessIs(?dr, ?lvl9)
                """
            )

    
    def determine_unresponsiveness(self): 

        self.create_instances("Unresponsiveness")
        # First Option where HR is Low and RR is High with corresponding KSS
        self.create_instances("Responsive") 

        self.create_instances("Unresponsive") 

        self.create_instances("Imminent")

        self.create_instances("AtRisk")
        
        rule_name = "responsive_1" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), 
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr, ?lvl3), Level_3_KSS(?lvl3), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?mod_hr), Moderate_HR(?mod_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?mod_hrv), Moderate_HRV(?mod_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?mod_rr), Moderate_RR(?mod_rr), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?nor), Normal_SpO2(?nor), 
                Unresponsiveness(unresponsiveness), Responsive(?repo) -> ActorStateHasUnresponsiveness(?act_st, unresponsiveness), UnresponsiveIs(unresponsiveness, ?repo)
                """
            )

        rule_name = "responsive_2" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), 
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr, ?lvl3), Level_3_KSS(?lvl3), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?mod_hr), Moderate_HR(?mod_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?high_hr), High_HRV(?high_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?mod_rr), Moderate_RR(?mod_rr), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?nor), Normal_SpO2(?nor), 
                Unresponsiveness(unresponsiveness), Responsive(?repo) -> ActorStateHasUnresponsiveness(?act_st, unresponsiveness), UnresponsiveIs(unresponsiveness, ?repo)
                """
            )

        rule_name = "responsive_3" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), 
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr, ?lvl3), Level_3_KSS(?lvl3), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?l_hr), Low_HR(?l_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?high_hr), High_HRV(?high_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?mod_rr), Moderate_RR(?mod_rr), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?nor), Normal_SpO2(?nor), 
                Unresponsiveness(unresponsiveness), Responsive(?repo) -> ActorStateHasUnresponsiveness(?act_st, unresponsiveness), UnresponsiveIs(unresponsiveness, ?repo)
                """
            )


        rule_name = "responsive_4" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), 
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr, ?lvl3), Level_3_KSS(?lvl3), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?mod_hr), Moderate_HR(?mod_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?high_hr), High_HRV(?high_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?l_rr), Low_RR(?l_rr), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?nor), Normal_SpO2(?nor), 
                Unresponsiveness(unresponsiveness), Responsive(?repo) -> ActorStateHasUnresponsiveness(?act_st, unresponsiveness), UnresponsiveIs(unresponsiveness, ?repo)
                """
            )

        rule_name = "responsive_5" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), 
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr, ?lvl3), Level_3_KSS(?lvl3), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?l_hr), Low_HR(?l_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?high_hr), High_HRV(?high_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?mod_rr), Low_RR(?l_rr), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?nor), Normal_SpO2(?nor), 
                Unresponsiveness(unresponsiveness), Responsive(?repo) -> ActorStateHasUnresponsiveness(?act_st, unresponsiveness), UnresponsiveIs(unresponsiveness, ?repo)
                """
            )

        rule_name = "responsive_6" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), 
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr, ?lvl3), Level_3_KSS(?lvl3), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?mod_hr), Moderate_HR(?mod_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?mod_hrv), Moderate_HRV(?mod_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?l_rr), Low_RR(?l_rr), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?nor), Normal_SpO2(?nor), 
                Unresponsiveness(unresponsiveness), Responsive(?repo) -> ActorStateHasUnresponsiveness(?act_st, unresponsiveness), UnresponsiveIs(unresponsiveness, ?repo)
                """
            )

        rule_name = "responsive_7" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), 
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr, ?lvl3), Level_3_KSS(?lvl3), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?l_hr), Low_HR(?l_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?mod_hr), Moderate_HRV(?mod_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?mod_rr), Low_RR(?l_rr), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?nor), Normal_SpO2(?nor), 
                Unresponsiveness(unresponsiveness), Responsive(?repo) -> ActorStateHasUnresponsiveness(?act_st, unresponsiveness), UnresponsiveIs(unresponsiveness, ?repo)
                """
            )

        rule_name = "at_risk_1"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),
                ActorStateHasPhysiologicalState(?dr), Drowsiness(?dr), DrowsinessIs(?dr, ?lvl5), Level_5_KSS(?lvl5), 
                Unresponsiveness(unresponsiveness), AtRisk(?atrisk) -> ActorStateHasUnresponsiveness(?act_st, unresponsiveness), UnresponsiveIs(unresponsiveness, ?atrisk)
                """
            )

        rule_name = "at_risk_2"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),
                ActorStateHasPhysiologicalState(?dr), Drowsiness(?dr), DrowsinessIs(?dr, ?lvl3), Level_3_KSS(?lvl3), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?l_hr), Low_HR(?l_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?l_hrv), Low_HRV(?l_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?l_rr), Low_RR(?l_rr), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?l_spo2), Low_SpO2(?l_spo2), 
                Unresponsiveness(unresponsiveness), AtRisk(?atrisk) -> ActorStateHasUnresponsiveness(?act_st, unresponsiveness), UnresponsiveIs(unresponsiveness, ?atrisk)
                """
            )

        rule_name = "at_risk_3"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),
                ActorStateHasPhysiologicalState(?dr), Drowsiness(?dr), DrowsinessIs(?dr, ?lvl3), Level_3_KSS(?lvl3), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?mod_hr), Moderate_HR(?mod_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?l_hrv), Low_HRV(?l_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?l_rr), Low_RR(?l_rr), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?l_spo2), Low_SpO2(?l_spo2), 
                Unresponsiveness(unresponsiveness), AtRisk(?atrisk) -> ActorStateHasUnresponsiveness(?act_st, unresponsiveness), UnresponsiveIs(unresponsiveness, ?atrisk)
                """
            )

        rule_name = "at_risk_4"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),
                ActorStateHasPhysiologicalState(?dr), Drowsiness(?dr), DrowsinessIs(?dr, ?lvl3), Level_3_KSS(?lvl3), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?l_hr), Low_HR(?l_hr),  
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?l_hrv), Low_HRV(?l_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?l_rr), High_RR(?l_rr), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?l_spo2), Low_SpO2(?l_spo2), 
                Unresponsiveness(unresponsiveness), AtRisk(?atrisk) -> ActorStateHasUnresponsiveness(?act_st, unresponsiveness), UnresponsiveIs(unresponsiveness, ?atrisk)
                """
            )

        rule_name = "at_risk_5"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),
                ActorStateHasPhysiologicalState(?dr), Drowsiness(?dr), DrowsinessIs(?dr, ?lvl3), Level_3_KSS(?lvl3), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?mod_hr), Moderate_HR(?mod_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?l_hrv), Low_HRV(?l_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?l_rr), High_RR(?l_rr), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?l_spo2), Low_SpO2(?l_spo2), 
                Unresponsiveness(unresponsiveness), AtRisk(?atrisk) -> ActorStateHasUnresponsiveness(?act_st, unresponsiveness), UnresponsiveIs(unresponsiveness, ?atrisk)
                """
            )

        rule_name = "critical_unre_1"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), 
                ActorStateHasPhysiologicalState(?dr), Drowsiness(?dr), DrowsinessIs(?dr, ?lvl3), Level_3_KSS(?lvl3), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?high_rr), High_HR(?high_hr),  
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?vrl_hrv), Very_Low_HRV(?vrl_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?vrl_rr), Very_Low_RR(?vrl_rr), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?l_spo2), Low_SpO2(?l_spo2), 
                Unresponsiveness(unresponsiveness), Imminent(?immi) -> ActorStateHasUnresponsiveness(?act_st, unresponsiveness), UnresponsiveIs(unresponsiveness, ?immi)
                """
            )
            
        rule_name = "critical_unre_2"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), 
                ActorStateHasPhysiologicalState(?dr), Drowsiness(?dr), DrowsinessIs(?dr, ?lvl3), Level_3_KSS(?lvl3), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?high_hr), High_HR(?high_hr),  
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?vrl_hrv), Very_Low_HRV(?vrl_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?high_rr), High_RR(?high_rr), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?l_spo2), Low_SpO2(?l_spo2), 
                Unresponsiveness(unresponsiveness), Imminent(?immi) -> ActorStateHasUnresponsiveness(?act_st, unresponsiveness), UnresponsiveIs(unresponsiveness, ?immi)
                """
            )
        
        rule_name = "critical_unre_3"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), 
                ActorStateHasPhysiologicalState(?dr), Drowsiness(?dr), DrowsinessIs(?dr, ?lvl3), Level_3_KSS(?lvl3), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?vrl_hr), Very_Low_HR(?vrl_hr),  
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?vrl_hrv), Very_Low_HRV(?vrl_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?vrl_rr), Very_Low_RR(?vrl_rr), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?l_spo2), Low_SpO2(?l_spo2), 
                Unresponsiveness(unresponsiveness), Imminent(?immi) -> ActorStateHasUnresponsiveness(?act_st, unresponsiveness), UnresponsiveIs(unresponsiveness, ?immi)
                """
            )

        rule_name = "critical_unre_4"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), 
                ActorStateHasPhysiologicalState(?dr), Drowsiness(?dr), DrowsinessIs(?dr, ?lvl3), Level_3_KSS(?lvl3), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?vrl_hr), Very_Low_HR(?vrl_hr),  
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?vrl_hrv), Very_Low_HRV(?vrl_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?high_rr), High_RR(?high_rr), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?l_spo2), Low_SpO2(?l_spo2), 
                Unresponsiveness(unresponsiveness), Imminent(?immi) -> ActorStateHasUnresponsiveness(?act_st, unresponsiveness), UnresponsiveIs(unresponsiveness, ?immi)
                """
            )

        rule_name = "critical_unre_5"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), 
                ActorStateHasPhysiologicalState(?dr), Drowsiness(?dr), DrowsinessIs(?dr, ?lvl5), Level_5_KSS(?lvl5), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?high_rr), High_HR(?high_hr),  
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?vrl_hrv), Very_Low_HRV(?vrl_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?vrl_rr), Very_Low_RR(?vrl_rr), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?l_spo2), Low_SpO2(?l_spo2), 
                Unresponsiveness(unresponsiveness), Imminent(?immi) -> ActorStateHasUnresponsiveness(?act_st, unresponsiveness), UnresponsiveIs(unresponsiveness, ?immi)
                """
            )
            
        rule_name = "critical_unre_6"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), 
                ActorStateHasPhysiologicalState(?dr), Drowsiness(?dr), DrowsinessIs(?dr, ?lvl5), Level_5_KSS(?lvl5), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?high_hr), High_HR(?high_hr),  
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?vrl_hrv), Very_Low_HRV(?vrl_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?high_rr), High_RR(?high_rr), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?l_spo2), Low_SpO2(?l_spo2), 
                Unresponsiveness(unresponsiveness), Imminent(?immi) -> ActorStateHasUnresponsiveness(?act_st, unresponsiveness), UnresponsiveIs(unresponsiveness, ?immi)
                """
            )
        
        rule_name = "critical_unre_7"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), 
                ActorStateHasPhysiologicalState(?dr), Drowsiness(?dr), DrowsinessIs(?dr, ?lvl5), Level_5_KSS(?lvl5), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?vrl_hr), Very_Low_HR(?vrl_hr),  
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?vrl_hrv), Very_Low_HRV(?vrl_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?vrl_rr), Very_Low_RR(?vrl_rr), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?l_spo2), Low_SpO2(?l_spo2), 
                Unresponsiveness(unresponsiveness), Imminent(?immi) -> ActorStateHasUnresponsiveness(?act_st, unresponsiveness), UnresponsiveIs(unresponsiveness, ?immi)
                """
            )

        rule_name = "critical_unre_8"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), 
                ActorStateHasPhysiologicalState(?dr), Drowsiness(?dr), DrowsinessIs(?dr, ?lvl5), Level_5_KSS(?lvl5), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?vrl_hr), Very_Low_HR(?vrl_hr),  
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?vrl_hrv), Very_Low_HRV(?vrl_hrv), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?high_rr), High_RR(?high_rr), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?l_spo2), Low_SpO2(?l_spo2), 
                Unresponsiveness(unresponsiveness), Imminent(?immi) -> ActorStateHasUnresponsiveness(?act_st, unresponsiveness), UnresponsiveIs(unresponsiveness, ?immi)
                """
            )

        rule_name = "critical_unre_9"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), 
                ActorStateHasPhysiologicalState(?dr), Drowsiness(?dr), DrowsinessIs(?dr, ?lvl5), Level_5_KSS(?lvl5), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?l_spo2), Low_SpO2(?l_spo2), 
                Unresponsiveness(unresponsiveness), Imminent(?immi) -> ActorStateHasUnresponsiveness(?act_st, unresponsiveness), UnresponsiveIs(unresponsiveness, ?immi)
                """
            )

        rule_name = "unresponsive_1" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), 
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr, ?lvl7), Level_7_KSS(?lvl7), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?l_spo2), Low_SpO2(?l_spo2), 
                Unresponsiveness(unresponsiveness), Unresponsive(?not) -> ActorStateHasUnresponsiveness(?act_st, unresponsiveness), UnresponsiveIs(unresponsiveness, ?not)
                """
            )

        rule_name = "unresponsive_2" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), 
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr, ?lvl9), Level_9_KSS(?lvl9), 
                Unresponsiveness(unresponsiveness), Unresponsive(?not) -> ActorStateHasUnresponsiveness(?act_st, unresponsiveness), UnresponsiveIs(unresponsiveness, ?not)
                """
            )

        rule_name = "unresponsive_3" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?crit), Critical_SpO2(?crit), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?vrl_hr), Very_Low_HR(?vrl_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?vrl_hrv), Very_Low_HRV(?vrl_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?vrl_rr), Very_Low_RR(?vrl_rr), 
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr, ?lvl3), Level_3_KSS(?lvl3), 
                Unresponsiveness(unresponsiveness), Unresponsive(?not) -> ActorStateHasUnresponsiveness(?act_st, unresponsiveness), UnresponsiveIs(unresponsiveness, ?not)
                """
            )

        rule_name = "unresponsive_4" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?crit), Critical_SpO2(?crit), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?vrl_hr), Very_Low_HR(?vrl_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?vrl_hrv), Very_Low_HRV(?vrl_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?vrl_rr), Very_Low_RR(?vrl_rr), 
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr, ?lvl5), Level_5_KSS(?lvl5), 
                Unresponsiveness(unresponsiveness), Unresponsive(?not) -> ActorStateHasUnresponsiveness(?act_st, unresponsiveness), UnresponsiveIs(unresponsiveness, ?not)
                """
            )

        rule_name = "unresponsive_5" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?crit), Critical_SpO2(?crit), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?vrl_hr), Very_Low_HR(?vrl_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?vrl_hrv), Very_Low_HRV(?vrl_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?vrl_rr), Very_Low_RR(?vrl_rr), 
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr, ?lvl7), Level_7_KSS(?lvl7), 
                Unresponsiveness(unresponsiveness), Unresponsive(?not) -> ActorStateHasUnresponsiveness(?act_st, unresponsiveness), UnresponsiveIs(unresponsiveness, ?not)
                """
            )

        rule_name = "unresponsive_6" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?crit), Critical_SpO2(?crit), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?high_hr), High_HR(?high_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?vrl_hrv), Very_Low_HRV(?vrl_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?vrl_rr), Very_Low_RR(?vrl_rr), 
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr, ?lvl3), Level_3_KSS(?lvl3), 
                Unresponsiveness(unresponsiveness), Unresponsive(?not) -> ActorStateHasUnresponsiveness(?act_st, unresponsiveness), UnresponsiveIs(unresponsiveness, ?not)
                """
            )

        rule_name = "unresponsive_7" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?crit), Critical_SpO2(?crit), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?high_hr), High_HR(?high_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?vrl_hrv), Very_Low_HRV(?vrl_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?vrl_rr), Very_Low_RR(?vrl_rr), 
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr, ?lvl5), Level_5_KSS(?lvl5), 
                Unresponsiveness(unresponsiveness), Unresponsive(?not) -> ActorStateHasUnresponsiveness(?act_st, unresponsiveness), UnresponsiveIs(unresponsiveness, ?not)
                """
            )

        rule_name = "unresponsive_8" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2(?spo2), SpO2is(?spo2, ?crit), Critical_SpO2(?crit), 
                ActorStateHasPhysiologicalState(?act_st, ?hr), HR(?hr), HRis(?hr, ?high_hr), High_HR(?high_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?hrv), HRV(?hrv), HRVis(?hrv, ?vrl_hrv), Very_Low_HRV(?vrl_hr), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RR(?rr), RRis(?rr, ?vrl_rr), Very_Low_RR(?vrl_rr), 
                ActorStateHasPhysiologicalState(?act_st, ?dr), Drowsiness(?dr), DrowsinessIs(?dr, ?lvl7), Level_7_KSS(?lvl5), 
                Unresponsiveness(unresponsiveness), Unresponsive(?not) -> ActorStateHasUnresponsiveness(?act_st, unresponsiveness), UnresponsiveIs(unresponsiveness, ?not)
                """
            )



    def determine_eye_state(self): 
        """
        This function determines the eye state of an actor based on the fatigue state.

        NOTE: In later stages the eye state will be determined by the fatigue, attention 
        and unresponsiveness state of the actor based on the physiological values. 
        """
      
        self.create_instances("EyeState") 
        self.create_instances("OpenState") 
        self.create_instances("ClosedState") 
        self.create_instances("SlowClosure")

        rule_name = "close_state_1"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
               """
               ActorState(?act_st),
               ActorStateHasFatigue(?act_st, ?ftg),FatigueIs(?ftg, ?sleep), Sleep(?sleep), 
               EyeState(eye_state), ClosedState(?close) -> EyeStateIs(eye_state, ?close), ActorHasEyeState(?act_st,eye_state)
               """
            )
        
        rule_name = "close_state_2"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
               """
               ActorState(?act_st),
               ActorStateHasUnresponsiveness(?act_st, ?unr), UnresponsiveIs(?unr, ?not), Unresponsive(?not), 
               EyeState(eye_state), ClosedState(?close) ->  EyeStateIs(eye_state, ?close), ActorHasEyeState(?act_st,eye_state)
               """
            )

        rule_name = "close_state_3"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
               """
               ActorState(?act_st),
               ActorStateHasFatigue(?act_st, ?ftg), FatigueIs(?ftg, ?dr_sus), DrowsinessSuspected(?dr_sus), 
               EyeState(eye_state), ClosedState(?close) -> EyeStateIs(eye_state, ?close), ActorHasEyeState(?act_st,eye_state)
               """
            )
        
        rule_name = "close_state_4"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
               """
               ActorState(?act_st),
               ActorStateHasFatigue(?act_st, ?ftg), FatigueIs(?ftg, ?dr_sus), DrowsinessSuspected(?dr_sus), 
               ActorStateHasAttention(?act_st, ?att),  AttentionIs(?att, ?attentive), Attentive(?attentive), 
               ActorStateHasUnresponsiveness(?act_st, ?unr), UnresponsiveIs(?unr, ?immi), Imminent(?immi), 
               EyeState(eye_state), ClosedState(?close) -> EyeStateIs(eye_state, ?close), ActorHasEyeState(?act_st,eye_state)
               """
            )

        rule_name = "close_state_5"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
               """
               ActorState(?act_st),
               ActorStateHasFatigue(?act_st, ?ftg),  FatigueIs(?ftg, ?awake), Awake(?awake), 
               ActorStateHasAttention(?act_st, ?att),  AttentionIs(?att, ?inat), Inattentive(?inat), 
               ActorStateHasUnresponsiveness(?act_st, ?unr), UnresponsiveIs(?unr, ?immi), Imminent(?immi), 
               EyeState(eye_state), ClosedState(?close) -> EyeStateIs(eye_state, ?close), ActorHasEyeState(?act_st,eye_state)
               """
            )
    
        rule_name = "close_state_6"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
               """
               ActorState(?act_st),
               ActorStateHasFatigue(?act_st, ?ftg), FatigueIs(?ftg, ?dr_sus), DrowsinessSuspected(?dr_sus), 
               ActorStateHasAttention(?act_st, ?att),  AttentionIs(?att, ?attentive), Attentive(?attentive), 
               ActorStateHasUnresponsiveness(?act_st, ?unr),  UnresponsiveIs(?unr, ?atrisk), AtRisk(?atrisk), 
               EyeState(eye_state), ClosedState(?close) -> EyeStateIs(eye_state, ?close), ActorHasEyeState(?act_st,eye_state)
               """
            )

        rule_name = "close_state_7"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
               """
               ActorState(?act_st),
               ActorStateHasFatigue(?act_st, ?ftg), FatigueIs(?ftg, ?awake), Awake(?awake), 
               ActorStateHasAttention(?act_st, ?att),  AttentionIs(?att, ?inat), Inattentive(?inat), 
               ActorStateHasUnresponsiveness(?act_st, ?unr), UnresponsiveIs(?unr, ?atrisk), AtRisk(?atrisk), 
               EyeState(eye_state), ClosedState(?close) ->EyeStateIs(eye_state, ?close), ActorHasEyeState(?act_st,eye_state)
               """
            )

        rule_name = "open_state_1"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), 
                ActorStateHasFatigue(?act_st, ?ftg), FatigueIs(?ftg, ?awake), Awake(?awake), 
                ActorStateHasUnresponsiveness(?act_st, ?unr), UnresponsiveIs(?unr, ?repo), Responsive(?repo), 
                ActorStateHasAttention(?act_st, ?att), AttentionIs(?att, ?attentive), Attentive(?attentive), 
                EyeState(eye_state), OpenState(?open) ->  EyeStateIs(eye_state, ?open),ActorHasEyeState(?act_st,eye_state)
                """
            )
        
        rule_name = "open_state_2"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),
                ActorStateHasFatigue(?act_st, ?ftg), FatigueIs(?ftg, ?dr_sus), DrowsinessSuspected(?dr_sus), 
                ActorStateHasUnresponsiveness(?act_st, ?unr), UnresponsiveIs(?unr, ?repo), Responsive(?repo), 
                ActorStateHasAttention(?act_st, ?att), AttentionIs(?att, ?attentive), Attentive(?attentive), 
                EyeState(eye_state), OpenState(?open) ->EyeStateIs(eye_state, ?open), ActorHasEyeState(?act_st,eye_state)
                """
            )

        rule_name = "open_state_3"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),
                ActorStateHasFatigue(?act_st, ?ftg),  FatigueIs(?ftg, ?awake), Awake(?awake), 
                ActorStateHasUnresponsiveness(?act_st, ?unr), UnresponsiveIs(?unr, ?atrisk), AtRisk(?atrisk), 
                ActorStateHasAttention(?act_st, ?att),  AttentionIs(?att, ?attentive), Attentive(?attentive), 
                EyeState(eye_state), OpenState(?open) ->  EyeStateIs(eye_state, ?open), ActorHasEyeState(?act_st,eye_state)
                """
            )

        rule_name = "open_state_4"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),
                ActorStateHasFatigue(?act_st, ?ftg),FatigueIs(?ftg, ?dr_sus), DrowsinessSuspected(?dr_sus), 
                ActorStateHasUnresponsiveness(?act_st, ?unr),  UnresponsiveIs(?unr, ?repo), Responsive(?repo), 
                ActorStateHasAttention(?act_st, ?att), AttentionIs(?att, ?attentive), Attentive(?attentive), 
                EyeState(eye_state), OpenState(?open) ->  EyeStateIs(eye_state, ?open), ActorHasEyeState(?act_st,eye_state)
                """
            )

        rule_name = "open_state_5"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st),
                ActorStateHasFatigue(?act_st, ?ftg), FatigueIs(?ftg, ?awake), Awake(?awake), 
                ActorStateHasUnresponsiveness(?act_st, ?unr),  UnresponsiveIs(?unr, ?repo), Responsive(?repo), 
                ActorStateHasAttention(?act_st, ?att), AttentionIs(?att, ?inat), Inattentive(?inat), 
                EyeState(eye_state), OpenState(?open) ->  EyeStateIs(eye_state, ?open), ActorHasEyeState(?act_st,eye_state)
                """
            )

        rule_name = "undefined_eye_1" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), 
                ActorStateHasUnresponsiveness(?act_st, ?unr),  UnresponsiveIs(?unr, ?repo), Responsive(?repo), 
                ActorStateHasAttention(?act_st, ?att),  AttentionIs(?att, ?undef), Undefined(?undef), 
                ActorStateHasFatigue(?act_st, ?ftg), FatigueIs(?ftg, ?und), UndefinedState(?und), 
                EyeState(eye_state), SlowClosure(?slow) -> EyeStateIs(eye_state, ?slow), ActorHasEyeState(?act_st,eye_state)
                """
            )

        rule_name = "undefined_eye_2"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), 
                ActorStateHasUnresponsiveness(?act_st, ?unr),  UnresponsiveIs(?unr, ?not), Unresponsive(?not), 
                ActorStateHasAttention(?act_st, ?att),  AttentionIs(?att, ?undef), Undefined(?undef), 
                ActorStateHasFatigue(?act_st, ?ftg), FatigueIs(?ftg, ?und), UndefinedState(?und), 
                EyeState(eye_state), SlowClosure(?slow) -> EyeStateIs(eye_state, ?slow), ActorHasEyeState(?act_st,eye_state)
                """
            )

        rule_name = "undefined_eye_3"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), 
                ActorStateHasUnresponsiveness(?act_st, ?unr), UnresponsiveIs(?unr, ?immi), Imminent(?immi), 
                ActorStateHasAttention(?act_st, ?att), AttentionIs(?att, ?undef), Undefined(?undef), 
                ActorStateHasFatigue(?act_st, ?ftg), FatigueIs(?ftg, ?und), UndefinedState(?und), 
                EyeState(eye_state), SlowClosure(?slow) -> EyeStateIs(eye_state, ?slow), ActorHasEyeState(?act_st,eye_state)
                """
            )

        rule_name = "undefined_eye_4"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), 
                ActorStateHasUnresponsiveness(?act_st, ?unr),  UnresponsiveIs(?unr, ?atrisk), AtRisk(?atrisk), 
                ActorStateHasAttention(?act_st, ?att), AttentionIs(?att, ?undef), Undefined(?undef), 
                ActorStateHasFatigue(?act_st, ?ftg),FatigueIs(?ftg, ?und), UndefinedState(?und), 
                EyeState(eye_state), SlowClosure(?slow) -> EyeStateIs(eye_state, ?slow), ActorHasEyeState(?act_st, eye_state)
                """
            )


    
    def determine_mouth_state(self): 

        self.create_instances("MouthState") 
        self.create_instances("Closed") 
        self.create_instances("Open")
        self.create_instances("Yawning") 

        rule_name = "mouth_open_1" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), 
                ActorStateHasUnresponsiveness(?act_st, ?unr), UnresponsiveIs(?unr, ?notrepo), Unresponsive(?notrepo), 
                MouthState(mouth_state), Open(?open) -> ActorHasMouthState(?act_st, mouth_state), MouthStateIs(mouth_state, ?open) 
                """
            )

        rule_name = "mouth_open_2" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), 
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, ?critical), Critical_SpO2(?critical),
                MouthState(mouth_state), Open(?open) -> ActorHasMouthState(?act_st, mouth_state), MouthStateIs(mouth_state, ?open) 
                """
            )

        rule_name = "mouth_open_3" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), 
                ActorStateHasFatigue(?act_st, ?ftg), FatigueIs(?ftg, ?sleep), Sleep(?sleep), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, ?vrl_rr), Very_Low_HR(?vrl_rr),
                MouthState(mouth_state), Open(?open) -> ActorHasMouthState(?act_st, mouth_state), MouthStateIs(mouth_state, ?open) 
                """
            )

        rule_name = "mouth_open_4" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), 
                ActorStateHasFatigue(?act_st, ?ftg), FatigueIs(?ftg, ?sleep), Sleep(?sleep), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, ?high_rr), High_RR(?high_rr),
                MouthState(mouth_state), Open(?open) -> ActorHasMouthState(?act_st, mouth_state), MouthStateIs(mouth_state, ?open) 
                """
            )

      
        rule_name = "mouth_open_5" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, ?high_rr), High_RR(?high_rr),
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, ?l_spo2), Low_SpO2(?l_spo2),
                MouthState(mouth_state), Open(?open) -> ActorHasMouthState(?act_st, mouth_state), MouthStateIs(mouth_state, ?open) 
                """
            )


        rule_name = "mouth_open_6" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, ?high_rr), High_RR(?high_rr),
                ActorStateHasUnresponsiveness(?act_st, ?unr), UnresponsiveIs(?unr, ?immi), Imminent(?immi), 
                MouthState(mouth_state), Open(?open) -> ActorHasMouthState(?act_st, mouth_state), MouthStateIs(mouth_state, ?open) 
                """
            )


        rule_name = "mouth_closed_1" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, ?mod_rr), Moderate_RR(?mod_rr),
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, ?nor), Normal_SpO2(?nor), 
                ActorStateHasFatigue(?act_st, ?ftg), FatigueIs(?ftg, ?awake), Awake(?awake), 
                ActorStateHasAttention(?act_st, ?att), AttentionIs(?att, ?attent), Attentive(?attent), 
                MouthState(mouth_state), Open(?open) -> ActorHasMouthState(?act_st, mouth_state), MouthStateIs(mouth_state, ?open) 
                """
            )

        
        rule_name = "mouth_closed_2" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), 
                ActorStateHasPhysiologicalState(?act_st, ?rr), RRis(?rr, ?mod_rr), Moderate_RR(?mod_rr),
                ActorStateHasPhysiologicalState(?act_st, ?spo2), SpO2is(?spo2, ?nor), Normal_SpO2(?nor), 
                ActorStateHasUnresponsiveness(?act_st, ?unr), UnresponsiveIs(?unr, ?repo), Responsive(?repo),
                MouthState(mouth_state), Open(?open) -> ActorHasMouthState(?act_st, mouth_state), MouthStateIs(mouth_state, ?open) 
                """
            )

        rule_name = "mouth_closed_3" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), 
                ActorStateHasFatigue(?act_st, ?ftg), FatigueIs(?ftg, ?awake), Awake(?awake), 
                ActorStateHasAttention(?act_st, ?att), AttentionIs(?att, ?attent), Attentive(?attent), 
                ActorStateHasUnresponsiveness(?act_st, ?unr), UnresponsiveIs(?unr, ?repo), Responsive(?repo),
                MouthState(mouth_state), Open(?open) -> ActorHasMouthState(?act_st, mouth_state), MouthStateIs(mouth_state, ?open) 
                """
            )


        rule_name = "mouth_yawn_1"
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_st), 
                ActorStateHasAttention(?act_st, ?att), AttentionIs(?att, ?und), Undefined(?und), 
                ActorStateHasFatigue(?act_st, ?ftg), FatigueIs(?ftg, ?undef), UndefinedState(?undef), 
                MouthState(mouth_state), Yawning(?yawn) -> ActorHasMouthState(?act_st, mouth_state), MouthStateIs(mouth_state, ?yawn)
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
        hr_instance = current_trend.CurrentHasHRTrend.pop(0) 
        hrv_instance = current_trend.CurrentHasHRVTrend.pop(0)
        rr_instance = current_trend.CurrentHasRRTrend.pop(0)

        # List of individuals accessed through temporal Context 
        comp = [hr_instance, hrv_instance, rr_instance] 

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


    def set_up_rules(self, index): 
        """
        This function is used tp set up the rules for the ontology.
        The rules are created only on the first iteration of the loop.
        Args: 
            index: The index of the iteration.
        """

        with self.ontology: 

            with StepContext(name="Connect_State_To_Values", catch=(RuntimeError,)):
                self.connect_actor_to_values()

            with StepContext(name="Preprocess_Temp_Age_Gender", catch=(RuntimeError,)):
                self.denote_temperature()
                self.determine_age()
                self.determine_gender()
                self.determine_acc_and_temp()

            with StepContext(name="Threshold_Profiles", catch=(RuntimeError,)): 
                self.determine_thresholds_profile()

            with StepContext(name="HR|HRV|RR|SPO2|Drowsiness", catch=(RuntimeError, )): 
                self.determine_HR()
                self.determine_HRV() 
                self.determine_RR() 
                self.determine_spo2() 
                self.determine_drowsiness()

            with StepContext(name="Define Fatigue Rules", catch=(RuntimeError,)):
                self.determine_fatigue()

            with StepContext(name="Define Attention Rules", catch=(RuntimeError,)): 
                self.determine_attention()

            with StepContext(name="Define Unresponsive Rules", catch=(RuntimeError,)): 
                self.determine_unresponsiveness()

            with StepContext(name="Define Eye State Rules", catch=(RuntimeError,)): 
                self.determine_eye_state()

            with StepContext(name="Define Mouth State Rules", catch=(RuntimeError,)): 
                self.determine_mouth_state()

            # self.set_up_trends()
            # self.determine_eye_state() 
            # self.update_trends()

            # self.determine_trends() 

       


    def create_label(self, actor, filepath,  index): 
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
            data[char.name] = char.hasStringValue[0] if char.name != "age_instance" else char.hasAgeValue[0] 
        
        for phy in phys: 
            data[phy.name] = phy.hasNumericalValue[0]

        data['fatigue'] = act_st.ActorStateHasFatigue[0].FatigueIs[0].name.split("_")[0]
        data['attention'] = act_st.ActorStateHasAttention[0].AttentionIs[0].name.split("_")[0]
        data['unresponsiveness'] = act_st.ActorStateHasUnresponsiveness[0].UnresponsiveIs[0].name.split("_")[0]
        data['driver_id'] = act_st.name
        eye_state = act_st.ActorHasEyeState[0].EyeStateIs[0].name.split("_")[0] 
        eye_state = eye_state.replace("state", "")
        mouth_state = act_st.ActorHasMouthState[0].MouthStateIs[0].name.split("_")[0]

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
                "eye_state": eye_state,
                "mouth_state":mouth_state,
                "age":data["age_instance"], 
                "face":data["facecharacteristics_instance"], 
                "sex":data["sex_instance"], 
                "demographic": data["demographic_instance"], 
                "accessories": data["accessories_instance"], 
                "fatigue":data['fatigue'], 
                "attention":data['attention'], 
                "unresponsive":data['unresponsiveness'],
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
            numerical_indi = ['hr_instance', 'hrv_instance', 'rr_instance', 'spo2_instance', 'drowsiness_instance'] 
            for indi in numerical_indi: 
                individual = getattr(self.ontology, indi) 
                individual.PhysiologicalStateDescribesActor = []
                individual.PhSFromObservations = [] 
                
                if "hr_instance" == indi: 
                    individual.HRis = [] 
                elif "hrv_instance" == indi: 
                    individual.HRVis = [] 
                elif "rr_instance" == indi: 
                    individual.RRis = [] 
                elif "spo2_instance" == indi: 
                    individual.SpO2is = [] 
                elif "drowsiness_instance" == indi: 
                    individual.DrowsinessIs = [] 



            string_indi = ['accessories_instance', 'demographic_instance', 'sex_instance', 'facecharacteristics_instance']
            for indi in string_indi:
                individual = getattr(self.ontology, indi)
                individual.hasStringValue = []

            age_indi = getattr(self.ontology, "age_instance")
            age_indi.hasAgeValue = []
            for group in self.ontology.Age.instances(): 
                if group.name != "age_instance": 
                    group.GroupHasAge = [] 
            
            sex_indi = getattr(self.ontology, "sex_instance") 
            for group in self.ontology.Sex.instances(): 
                if group.name != sex_indi.name: 
                    group.SexBelongsToPerson = [] 

            actor.ActorHasState = []

            fatigue_indi = getattr(self.ontology, "fatigue_instance") 
            fatigue_indi.FatigueIs = [] 

            attention = getattr(self.ontology, "attention_instance") 
            attention.AttentionIs = [] 

            unresponsive = getattr(self.ontology, "unresponsiveness") 
            unresponsive.UnresponsiveIs = [] 

            eyestate = getattr(self.ontology, "eye_state") 
            eyestate.EyeStateIs = [] 

            mouthstate = getattr(self.ontology, "mouth_state")
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





