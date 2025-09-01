from tools.common import *
from tools.appraisal import StepContext 
from tools.logger import logger 

import os 
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
        self.temp_groups_names = None 


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
                                Age(?age_instance), AgeBelongsToGroup(age_instance, ?age_g), {age_group}(?age_g), 
                                Sex(?sex_instance),SexBelongsToPerson(sex_instance, ?sex_g), {sex_group}(?sex_g), 
                                Accessories(?accessories_instance), 
                                AccessoriesIncludeWearables(?accessories_instance, ?v), 
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

        if not self.ontology.search(iri="Very_Low_HR"): self.create_instances("Very_Low_HR") 
        if not has_rule_named(onto=self.ontology, name="very_low_hr_rule"): 
            Imp("very_low_hr_rule").set_as_rule(
                f""" 
                ActorState(?act_st), StateHasThresholdProfile(?act_st, ?tp), 
                appliesHRLow(?tp, ?hr_low), hasThrValue(?hr_low, ?low), 
                HR(?hr), hasNumericalValue(?hr, ?value), 
                lessThan(?value, ?low), 
                Very_Low_HR(?vrl_hr)  -> HRis(hr_instance, ?vrl_hr) 
                """
            )

        if not self.ontology.search(iri="Low_HR"): self.create_instances("Low_HR") 
        if not has_rule_named(onto=self.ontology, name="low_hr_rule"): 
            Imp("low_hr_rule").set_as_rule(
                 f""" 
                ActorState(?act_st), StateHasThresholdProfile(?act_st, ?tp), 
                appliesHRLow(?tp, ?hr_low), hasThrValue(?hr_low, ?low), 
                appliesHRModerate(?tp, ?hr_mod), hasThrValue(?hr_mod, ?mod), 
                HR(?hr), hasNumericalValue(?hr, ?value), 
                greaterThanOrEqual(?value, ?hr_low),
                lessThan(?value, ?hr_mod), 
                Low_HR(?l_hr)  -> HRis(hr_instance, ?l_hr) 
                """
            )

        if not self.ontology.search(iri="Moderate_HR"): self.create_instances("Moderate_HR") 
        if not has_rule_named(onto=self.ontology, name="moderate_hr_rule"): 
            Imp("moderate_hr_rule").set_as_rule(
                f""" 
                ActorState(?act_st), StateHasThresholdProfile(?act_st, ?tp), 
                appliesHRModerate(?tp, ?hr_mod), hasThrValue(?hr_mod, ?mod), 
                appliesHRHigh(?tp, ?hr_high), hasThrValue(?hr_high, ?high), 
                HR(?hr), hasNumericalValue(?hr, ?value), 
                greaterThanOrEqual(?value, ?hr_mod),
                lessThan(?value, ?hr_high), 
                Moderate_HR(?m_hr)  -> HRis(hr_instance, ?m_hr) 
                """
            )

        if not self.ontology.search(iri="High_HR"): self.create_instances("High_HR") 
        if not has_rule_named(onto=self.ontology, name="high_hr_rule"): 
            Imp("high_hr_rule").set_as_rule(
                f""" 
                ActorState(?act_st), StateHasThresholdProfile(?act_st, ?tp), 
                appliesHRHigh(?tp, ?hr_high), hasThrValue(?hr_high, ?high), 
                HR(?hr), hasNumericalValue(?hr, ?value), 
                greaterThanOrEqual(?value, ?hr_high),
                High_HR(?h_hr)  -> HRis(hr_instance, ?h_hr) 
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
      
        if not self.ontology.search(iri="Very_Low_HRV"): self.create_instances("Very_Low_HRV") 
        if not has_rule_named(onto=self.ontology, name="very_low_hrv_rule"): 
            Imp("very_low_hrv_rule").set_as_rule(
                f"""
                ActorState(?act_st), StateHasThresholdProfile(?act_st, ?tp), 
                appliesHRVLow(?tp, ?hrv_low), hasThrValue(?hrv_low, ?low), 
                HRV(?hrv), hasNumericalValue(?hrv, ?value), 
                lessThan(?value, ?low), 
                Very_Low_HRV(?vrl_hrv) -> HRVis(hrv_instance, ?vrl_hrv) 
                """
            )


        if not self.ontology.search(iri="Low_HRV"): self.create_instances("Low_HRV") 
        if not has_rule_named(onto=self.ontology, name="low_hrv_rule"): 
            Imp("low_hrv_rule").set_as_rule(
                f"""
                ActorState(?act_st), StateHasThresholdProfile(?act_st, ?tp), 
                appliesHRVLow(?tp, ?hrv_low), hasThrValue(?hrv_low, ?low), 
                appliesHRVModerate(?tp, ?hrv_mod), hasThrValue(?hrv_mod, ?mod), 
                HRV(?hrv), hasNumericalValue(?hrv, ?value), 
                greaterThanOrEqual(?value, ?low), lessThan(?value, ?mod), 
                Low_HRV(?l_hrv) -> HRVis(hrv_instance, ?l_hrv) 
                """
            )

        if not self.ontology.search(iri="Moderate_HRV"): self.create_instances("Moderate_HRV") 
        if not has_rule_named(onto=self.ontology, name="moderate_hrv_rule"): 
            Imp("moderate_hrv_rule").set_as_rule(
                f"""
                ActorState(?act_st), StateHasThresholdProfile(?act_st, ?tp), 
                appliesHRVModerate(?tp, ?hrv_mod), hasThrValue(?hrv_mod, ?mod), 
                appliesHRVHigh(?tp, ?hrv_high), hasThrValue(?hrv_high, ?high), 
                HRV(?hrv), hasNumericalValue(?hrv, ?value), 
                greaterThanOrEqual(?value, ?mod), lessThan(?value, ?high), 
                Moderate_HRV(?mod_hrv) -> HRVis(hrv_instance, ?mod_hrv) 
                """
            )

        if not self.ontology.search(iri="High_HRV"): self.create_instances("High_HRV")
        if not has_rule_named(onto=self.ontology, name="high_hrv_rule"): 
            Imp("high_hrv_rule").set_as_rule(
                f"""
                ActorState(?act_st), StateHasThresholdProfile(?act_st, ?tp), 
                appliesHRHigh(?tp, ?hrv_high), hasThrValue(?high_hrv, ?high), 
                HRV(?hrv), hasNumericalValue(?hrv, ?value), 
                greaterThanOrEqual(?value, ?high),
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


        if not self.ontology.search(iri="Very_Low_RR"):self.create_instances("Very_Low_RR") 
        if not has_rule_named(onto=self.ontology, name="very_low_rr_rule"):
            Imp("very_low_rr_rule").set_as_rule(
                f"""
                ActorState(?act_st), StateHasThresholdProfile(?act_st, ?tp), 
                appliesRRLow(?tp, ?rr_low), hasThrValue(?rr_low, ?low), 
                RR(?rr), hasNumericalValue(?rr, ?value), 
                lessThan(?value, ?low), 
                Very_Low_RR(?vrl_rr) -> RRis(rr_instance, ?vrl_rr) 
                """
            )


        if not self.ontology.search(iri="Low_RR"):self.create_instances("Low_RR") 
        if not has_rule_named(onto=self.ontology, name="low_rr_rule"): 
             Imp("low_rr_rule").set_as_rule(
                f"""
                ActorState(?act_st), StateHasThresholdProfile(?act_st, ?tp), 
                appliesRRLow(?tp, ?rr_low), hasThrValue(?rr_low, ?low), 
                appliesRRModerate(?tp, ?rr_mod), hasThrValue(?rr_mod, ?mod), 
                RR(?rr), hasNumericalValue(?rr, ?value), 
                greaterThanOrEqual(?value, ?low), lessThan(?value, ?mod), 
                Low_RR(?l_rr) -> RRis(rr_instance, ?l_rr)
                """
             )
        
        if not self.ontology.search(iri="Moderate_RR"):self.create_instances("Moderate_RR") 
        if not has_rule_named(onto=self.ontology, name="moderate_rr_rule"): 
             Imp("moderate_rr_rule").set_as_rule(
                f"""
                ActorState(?act_st), StateHasThresholdProfile(?act_st, ?tp), 
                appliesRRModerate(?tp, ?rr_mod), hasThrValue(?rr_mod, ?mod), 
                appliesRRHigh(?tp, ?rr_high), hasThrValue(?rr_high, ?high), 
                RR(?rr), hasNumericalValue(?rr, ?value), 
                greaterThanOrEqual(?value, ?mod), lessThan(?value, ?high), 
                Moderate_RR(?mod_rr) -> RRis(rr_instance, ?mod_rr)
                """
             )

        if not self.ontology.search(iri="High_RR"):self.create_instances("High_RR") 
        if not has_rule_named(onto=self.ontology, name="high_rr_rule"): 
             Imp("high_rr_rule").set_as_rule(
                f"""
                ActorState(?act_st), StateHasThresholdProfile(?act_st, ?tp), 
                appliesRRHigh(?tp, ?rr_high), hasThrValue(?rr_high, ?high), 
                RR(?rr), hasNumericalValue(?rr, ?value), 
                greaterThanOrEqual(?value, ?high),  
                High_RR(?high_rr) -> RRis(rr_instance, ?high_rr)
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

        if not self.ontology.search(iri="Normal_SpO2"):self.create_instances("Normal_SpO2") 
        if not has_rule_named(onto=self.ontology, name="normal_spo2_rule"): 
             Imp("normal_spo2_rule").set_as_rule(
                f"""
                ActorState(?act_st), StateHasThresholdProfile(?act_st, ?tp), 
                appliesSPO2Moderate(?tp, ?spo2_mod), hasThrValue(?spo2_mod, ?mod), 
                appliesSPO2High(?tp, ?spo2_high), hasThrValue(?spo2_high, ?high), 
                SpO2(?spo2), hasNumericalValue(?spo2, ?value), 
                greaterThanOrEqual(?value, ?mod), lessThanOrEqual(?value, ?high), 
                Normal_SpO2(?nrm_spo2) -> SpO2is(spo2_instance, ?nrm_spo2)
                """
             )

        if not self.ontology.search(iri="Low_SpO2"):self.create_instances("Low_SpO2") 
        if not has_rule_named(onto=self.ontology, name="low_spo2_rule"): 
             Imp("low_spo2_rule").set_as_rule(
                f"""
                ActorState(?act_st), StateHasThresholdProfile(?act_st, ?tp), 
                appliesSPO2Low(?tp, ?spo2_low), hasThrValue(?spo2_low, ?low), 
                appliesSPO2Moderate(?tp, ?spo2_mod), hasThrValue(?spo2_mod, ?mod), 
                SpO2(?spo2), hasNumericalValue(?spo2, ?value), 
                greaterThanOrEqual(?value, ?low), lessThan(?value, ?mod), 
                Low_SpO2(?l_spo2) -> SpO2is(spo2_instance, ?l_spo2)
                """
             )


        if not self.ontology.search(iri="Critical_SpO2"):self.create_instances("Critical_SpO2") 
        if not has_rule_named(onto=self.ontology, name="critical_spo2_rule"): 
             Imp("critical_spo2_rule").set_as_rule(
                f"""
                ActorState(?act_st), StateHasThresholdProfile(?act_st, ?tp), 
                appliesSPO2Low(?tp, ?spo2_low), hasThrValue(?spo2_low, ?low), 
                SpO2(?spo2), hasNumericalValue(?spo2, ?value), 
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

        rule_name = "level_3_kss_rule" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_state), 
                Drowsiness(?dr_instance), hasNumericalValue(?dr_instance, ?v), 
                lessThanOrEqual(?v, 1), greaterThan(?v, 0), Level_3_KSS(?l3kss) 
                -> ActorStateHasPhysiologicalState(?act_state, ?dr_instance), DrowsinessIs(?dr_instance, ?l3kss) 
                """
            )

        rule_name = "level_5_kss_rule" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_state), 
                Drowsiness(?dr_instance), hasNumericalValue(?dr_instance, ?v), 
                lessThanOrEqual(?v, 2), greaterThan(?v, 1), Level_5_KSS(?l5kss) 
                -> ActorStateHasPhysiologicalState(?act_state, ?dr_instance), DrowsinessIs(?dr_instance, ?l5kss) 
                """
            )


        rule_name = "level_7_kss_rule" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_state), 
                Drowsiness(?dr_instance), hasNumericalValue(?dr_instance, ?v), 
                lessThanOrEqual(?v, 3), greaterThan(?v, 2), Level_7_KSS(?l7kss) 
                -> ActorStateHasPhysiologicalState(?act_state, ?dr_instance), DrowsinessIs(?dr_instance, ?l7kss) 
                """
            )

        rule_name = "level_9_kss_rule" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_state), 
                Drowsiness(?dr_instance), hasNumericalValue(?dr_instance, ?v), 
                lessThanOrEqual(?v, 4), greaterThan(?v, 3), Level_9_KSS(?l9kss) 
                -> ActorStateHasPhysiologicalState(?act_state, ?dr_instance), DrowsinessIs(?dr_instance, ?l9kss) 
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
            
    
    def trend_analysis(self): 
        rule_name = "trend_analysis" 
        if not  has_rule_named(self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule()

                

    def connect_actor_to_values(self): 
        """
        This function creates the rules to connect the actor to the physiological values, 
        and characteristics of the actor. This uses the instances of each class, to improve 
        reasoner performance. 
        
        NOTE: This solution means that the instances remain the same during the iterative execution. 
        If an instance is deleted or non existent the reasoner will detect an inconsistency error in this 
        class. 
        """
        Imp().set_as_rule("""ActorState(?act_state), HR(?hr_instance)->ActorStateHasPhysiologicalState(?act_state, ?hr_instance)""") 
        Imp().set_as_rule("""ActorState(?act_state), HRV(?hrv_instance)->ActorStateHasPhysiologicalState(?act_state, ?hrv_instance)""") 
        Imp().set_as_rule("""ActorState(?act_state), RR(?rr_instance)->ActorStateHasPhysiologicalState(?act_state, ?rr_instance)""") 
        Imp().set_as_rule("""ActorState(?act_state), SpO2(?spo2_instance)->ActorStateHasPhysiologicalState(?act_state, ?spo2_instance)""") 
        Imp().set_as_rule("""ActorState(?act_state), Drowsiness(?drowsiness_instance)->ActorStateHasPhysiologicalState(?act_state, ?drowsiness_instance)""") 
        Imp().set_as_rule("""ActorState(?act_state), FaceCharacteristics(?facecharacteristics_instance)->ActorStateHasCharacteristics(?act_state, ?facecharacteristics_instance)""") 
        Imp().set_as_rule("""ActorState(?act_state), Sex(?sex_instance)->ActorStateHasCharacteristics(?act_state, ?sex_instance)""") 
        Imp().set_as_rule("""ActorState(?act_state), Age(?age_instance)->ActorStateHasCharacteristics(?act_state, ?age_instance)""") 
        Imp().set_as_rule("""ActorState(?act_state), Demographic(?demographic_instance)->ActorStateHasCharacteristics(?act_state, ?demographic_instance)""") 
        Imp().set_as_rule("""ActorState(?act_state), Accessories(?accessories_instance)->ActorStateHasCharacteristics(?act_state, ?accessories_instance)""")



    def determine_fatigue(self): 
        """ This function is used to create the rules to categorize the fatigue of the actor into threshold ranges based on the previous physiological values. * Awake * Sleeping 
        * Microsleep
        * Drowsy 
        * Drowsiness Suspected 
        * Undefined State
        """
    
        if not self.ontology.search(iri="fatigue_instance"): 
            self.create_instances("Fatigue")

        # First Option where HR is Low and RR is High with corresponding KSS
        if not self.ontology.Sleep.instances(): 
            self.create_instances("Sleep") 

        if not self.ontology.Awake.instances(): 
            self.create_instances("Awake") 

        if not self.ontology.Drowsiness_Suspected.instances(): 
            self.create_instances("Drowsiness_Suspected")

        import pdb;pdb.set_trace()
        rule_name = "sleep_rule_1" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_state), StateHasThresholdProfile(?act_state, ?tp), 
                appliesHRLow(?tp, ?hr_instance), ActorStateHasPhysiologicalState(?act_state, ?hr), HRis(?hr, ?hr_instance), 
                appliesHRVLow(?tp, ?hrv_instance), ActorStateHasPhysiologicalState(?act_state, ?hrv), HRVis(?hrv, ?hrv_instance), 
                appliesRRLow(?tp, ?rr_instance), ActorStateHasPhysiologicalState(?act_state, ?rr), RRis(?rr, ?rr_instance), 
                appliesSPO2Low(?tp, ?spo2_instance), ActorStateHasPhysiologicalState(?act_state, ?spo2), SpO2is(?spo2, ?spo2_instance), 
                
                """
            )

        return

        rule_name = "sleep_rule_2" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_state), 
                ActorStateHasPhysiologicalState(?act_state, ?hr), HRis(?hr, ?hr_instance), High_HR(?hr_instance),  
                ActorStateHasPhysiologicalState(?act_state, ?hrv), HRVis(?hrv, ?hrv_instance), Low_HRV(?hrv_instance),  
                ActorStateHasPhysiologicalState(?act_state, ?rr), RRis(?rr, ?rr_instance), High_RR(?rr_instance), 
                ActorStateHasPhysiologicalState(?act_state, ?ds), DrowsinessIs(?ds, ?dr_instance), Level_7_KSS(?dr_instance), 
                ActorStateHasPhysiologicalState(?act_state, ?spo2), SpO2is(?spo2, ?spo2_instance), Low_SpO2(?spo2_instance),  
                Sleep(?sleep) -> ActorStateHasPhysiologicalState(?act_state, fatigue_instance), FatigueIs(fatigue_instance, ?sleep) 
                """
            )
        
        rule_name = "sleep_rule_3" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_state), 
                ActorStateHasPhysiologicalState(?act_state, ?hr), HRis(?hr, ?hr_instance), High_HR(?hr_instance),  
                ActorStateHasPhysiologicalState(?act_state, ?hrv), HRVis(?hrv, ?hrv_instance), Low_HRV(?hrv_instance),  
                ActorStateHasPhysiologicalState(?act_state, ?rr), RRis(?rr, ?rr_instance), Low_RR(?rr_instance), 
                ActorStateHasPhysiologicalState(?act_state, ?ds), DrowsinessIs(?ds, ?dr_instance), Level_7_KSS(?dr_instance), 
                ActorStateHasPhysiologicalState(?act_state, ?spo2), SpO2is(?spo2, ?spo2_instance), Low_SpO2(?spo2_instance),  
                Sleep(?sleep) -> ActorStateHasPhysiologicalState(?act_state, fatigue_instance), FatigueIs(fatigue_instance, ?sleep) 
                """
            )

        rule_name = "sleep_rule_4" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_state), 
                ActorStateHasPhysiologicalState(?act_state, ?hr), HRis(?hr, ?hr_instance), Very_Low_HR(?hr_instance),  
                ActorStateHasPhysiologicalState(?act_state, ?hrv), HRVis(?hrv, ?hrv_instance), Low_HRV(?hrv_instance),  
                ActorStateHasPhysiologicalState(?act_state, ?rr), RRis(?rr, ?rr_instance), High_RR(?rr_instance), 
                ActorStateHasPhysiologicalState(?act_state, ?ds), DrowsinessIs(?ds, ?dr_instance), Level_7_KSS(?dr_instance), 
                ActorStateHasPhysiologicalState(?act_state, ?spo2), SpO2is(?spo2, ?spo2_instance), Low_SpO2(?spo2_instance),  
                Sleep(?sleep) -> ActorStateHasPhysiologicalState(?act_state, fatigue_instance), FatigueIs(fatigue_instance, ?sleep) 
                """
            )

        rule_name = "awake_rule_1" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_state), 
                ActorStateHasPhysiologicalState(?act_state, ?hr), HRis(?hr, ?hr_instance), Moderate_HR(?hr_instance),  
                ActorStateHasPhysiologicalState(?act_state, ?hrv), HRVis(?hrv, ?hrv_instance), Moderate_HRV(?hrv_instance),  
                ActorStateHasPhysiologicalState(?act_state, ?rr), RRis(?rr, ?rr_instance), Moderate_RR(?rr_instance), 
                ActorStateHasPhysiologicalState(?act_state, ?ds), DrowsinessIs(?ds, ?dr_instance), Level_3_KSS(?dr_instance), 
                ActorStateHasPhysiologicalState(?act_state, ?spo2), SpO2is(?spo2, ?spo2_instance), Normal_SpO2(?spo2_instance),  
                Awake(?awake) -> ActorStateHasPhysiologicalState(?act_state, fatigue_instance), FatigueIs(fatigue_instance, ?awake) 
                """
            )

        rule_name = "drowsiness_suspected_rule_1" 
        if not has_rule_named(onto=self.ontology, name=rule_name): 
            Imp(rule_name).set_as_rule(
                """
                ActorState(?act_state), 
                ActorStateHasPhysiologicalState(?act_state, ?hr), HRis(?hr, ?hr_instance), Moderate_HR(?hr_instance),  
                ActorStateHasPhysiologicalState(?act_state, ?hrv), HRVis(?hrv, ?hrv_instance), High_HRV(?hrv_instance),  
                ActorStateHasPhysiologicalState(?act_state, ?rr), RRis(?rr, ?rr_instance), Moderate_RR(?rr_instance), 
                ActorStateHasPhysiologicalState(?act_state, ?ds), DrowsinessIs(?ds, ?dr_instance), Level_3_KSS(?dr_instance), 
                ActorStateHasPhysiologicalState(?act_state, ?spo2), SpO2is(?spo2, ?spo2_instance), Normal_SpO2(?spo2_instance),  
                Drowsiness_Suspected(?drowsy_sus) -> ActorStateHasPhysiologicalState(?act_state, fatigue_instance), FatigueIs(fatigue_instance, ?drowsy_sus) 
                """
            )

        return  
        

        # Second Option for sleeping where HR is High and RR is High with Low KSS              
        fatigue_awake_state_2 = Imp()
        self.create_instances("Drowsiness_Suspected")
        fatigue_awake_state_2.set_as_rule(
            """
            Actor(?actor), 
            ActorHasPhysiologicalState(?actor, ?hr),
            ActorHasPhysiologicalState(?actor, ?hrv),
            ActorHasPhysiologicalState(?actor, ?rr),
            ActorHasPhysiologicalState(?actor, ?spo2),
            ActorHasPhysiologicalState(?actor, ?ds),
            HRis(?hr, ?low_hr), Moderate_HR(?low_hr),
            HRVis(?hrv, ?low_hrv), High_HRV(?low_hrv),
            RRis(?rr, ?low_rr), Moderate_RR(?low_rr),
            SpO2is(?spo2, ?low_spo2), Normal_SpO2(?low_spo2),
            DrowsinessIs(?ds, ?low_ds), Level_3_KSS(?low_ds),
            Fatigue(fatigue_instance),
            Drowsiness_Suspected(?fatigue) 
            ->  ActorHasPhysiologicalState(?actor, fatigue_instance),
                FatigueIs(fatigue_instance, ?fatigue), 
            """)
        
        fatigue_awake_state_3 = Imp()
        fatigue_awake_state_3.set_as_rule(
            """
            Actor(?actor), 
            ActorHasPhysiologicalState(?actor, ?hr),
            ActorHasPhysiologicalState(?actor, ?hrv),
            ActorHasPhysiologicalState(?actor, ?rr),
            ActorHasPhysiologicalState(?actor, ?spo2),
            ActorHasPhysiologicalState(?actor, ?ds),
            HRis(?hr, ?low_hr), High_HR(?low_hr),
            HRVis(?hrv, ?low_hrv), Low_HRV(?low_hrv),
            RRis(?rr, ?low_rr), High_RR(?low_rr),
            SpO2is(?spo2, ?low_spo2), Normal_SpO2(?low_spo2),
            DrowsinessIs(?ds, ?low_ds), Level_3_KSS(?low_ds),
            Fatigue(fatigue_instance),
            Awake(?fatigue)
            ->  ActorHasPhysiologicalState(?actor, fatigue_instance), 
            FatigueIs(fatigue_instance, ?fatigue),
            """)    

        fatigue_awake_state_3 = Imp()
        fatigue_awake_state_3.set_as_rule(
            """
            Actor(?actor), 
            ActorHasPhysiologicalState(?actor, ?hr),
            ActorHasPhysiologicalState(?actor, ?hrv),
            ActorHasPhysiologicalState(?actor, ?rr),
            ActorHasPhysiologicalState(?actor, ?spo2),
            ActorHasPhysiologicalState(?actor, ?ds),
            HRis(?hr, ?low_hr), Moderate_HR(?low_hr),
            HRVis(?hrv, ?low_hrv), Low_HRV(?low_hrv),
            RRis(?rr, ?low_rr), High_RR(?low_rr),
            SpO2is(?spo2, ?low_spo2), Normal_SpO2(?low_spo2),
            DrowsinessIs(?ds, ?low_ds), Level_3_KSS(?low_ds),
            Fatigue(fatigue_instance),
            Awake(?fatigue)
            ->  ActorHasPhysiologicalState(?actor, fatigue_instance),
                FatigueIs(fatigue_instance, ?fatigue),
            """)       
        
    logger.debug("Determining Fatigue State | Rules Created Successfully...")
        

    def determine_eye_state(self): 
        """
        This function determines the eye state of an actor based on the fatigue state.
        The categories are: 
        * Blinking
        * Sleeping
        * Microsleeping 
        * Slow Closure 

        NOTE: In later stages the eye state will be determined by the fatigue, attention 
        and unresponsiveness state of the actor based on the physiological values. 
        """

      
        rule = Imp() 
        self.create_instances("Blinking")
        rule.set_as_rule(
            """
            Actor(?actor),
            ActorHasPhysiologicalState(?actor, fatigue_instance),
            FatigueIs(fatigue_instance, ?fatigue),
            Awake(?fatigue),
            Blinking(?eye_state)-> EyeStateForActor(?eye_state, ?actor)
            """
        )

        rule = Imp()
        self.create_instances("Sleeping")
        rule.set_as_rule(
            """
            Actor(?actor),
            ActorHasPhysiologicalState(?actor, fatigue_instance),
            FatigueIs(fatigue_instance, ?fatigue),
            Sleep(?fatigue), 
            Sleeping(?eye_state)-> EyeStateForActor(?eye_state, ?actor)
            """
        )
    
        rule = Imp()
        self.create_instances("MicroSleeping")
        rule.set_as_rule(
            """
            Actor(?actor),
            ActorHasPhysiologicalState(?actor, fatigue_instance),
            FatigueIs(fatigue_instance, ?fatigue),
            Microsleep(?fatigue), 
            MicroSleeping(?eye_state)-> EyeStateForActor(?eye_state, ?actor)
            """
        )
    
        rule = Imp()
        self.create_instances("Slow_Closure")
        rule.set_as_rule(
            """
            Actor(?actor),
            ActorHasPhysiologicalState(?actor, fatigue_instance),
            FatigueIs(fatigue_instance, ?fatigue),
            Drowsiness_Suspected(?fatigue), 
            Slow_Closure(?eye_state)-> EyeStateForActor(?eye_state, ?actor)
            """
        )
    logger.debug("Determine Eye State | Rules Created successfully...")


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

        try: 
            if index == 0:

                with self.ontology: 
                    self.connect_actor_to_values()
                    self.denote_temperature()
                    self.determine_age()
                    self.determine_gender()
                    self.determine_acc_and_temp()
                    self.determine_thresholds_profile()
                    self.determine_HR()
                    self.determine_HRV() 
                    self.determine_RR() 
                    self.determine_spo2() 
                    self.determine_drowsiness()
                    import pdb; pdb.set_trace()
                    self.determine_fatigue()
                    import pdb;pdb.set_trace()
                    self.determine_age()
                    self.determine_gender()
                    self.determine_acc_and_temp()
                    self.determine_HR()
                    self.determine_HRV()
                    self.determine_RR()
                    self.determine_spo2()
                    self.determine_drowsiness() 
                    self.set_up_trends()
                    self.determine_fatigue()
                    self.determine_eye_state() 
                    self.update_trends()
                    # self.determine_trends() 

        except Exception as e:
            logger.exception(e)
                


    def create_label(self, filepath,  index): 
        """
        This function creates a label, describing the actor based on the results 
        of the SWRL rules in the ontology. Requires reasoner to previously have 
        been synchronized, otherwise the last changes will not be reflected in the label.
        
        Args:
            filepath (str): The filepath to the ontology file.
            index (int): The index of the ontology file.
        """

        try: 
            driver = self.ontology.Actor.instances()[0]
            driver_chars = driver.ActorHasCharacteristics
            data = {}
            for val in driver_chars:
            
                if val.name == "age_instance":
                    data[val.name] = val.hasAgeValue[0]
                    continue
                data[val.name] = val.hasStringValue[0]
            
            driver.hasUniqueIdentifier.append(str(uuid.uuid4()))
            logger.debug("Preparing data for label")
            try: 
                eye_state =  driver.ActorHasEyeState[0].name.split("_")[0]
            except: 
                eye_state = "Undefined"
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
                    "actor_id": driver.hasUniqueIdentifier[0],
                    "eye_state": eye_state,
                    "age":data["age_instance"], 
                    "face":data["facecharacteristics_instance"], 
                    "sex":data["sex_instance"], 
                    "demographic": data["demographic_instance"], 
                    "accessories": data["accessories_instance"], 
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
                # label.hasUniqueIdentifier.append(str(uuid.uuid4()))
                label.LabelTargetsActor = [driver]
                logger.debug(f"Label created successfully: {label.hasDescription[0]}")
            logger.debug("Label created successfully with name: label.json")
        
        except Exception as e:
            print(e)
            print("Error creating label")
            return


    def remove_prev_values(self, obs): 
        """
        This function deletes all previously established relationships between 
        class' instances and also removes all the numerical values originating 
        from the Observation class instance. 

        NOTE: This is necessary to acoid the creation of duplicate relationships 
        and to minimize the number of instances that have to be created in this 
        iterative way of operation. Otherwise the length of the dataset will 
        determine the number of instances that will be created for each class. 
        """
        with self.ontology: 
            obs.hasAge = [] 
            obs.hasAccessories = [] 
            obs.hasSex = [] 
            obs.hasDemographic = []
            obs.hasFaceCharacteristics = []
            obs.ObsIsDividedIntoActor = [] 
            obs.ObsIsDividedIntoPhS = []
            numerical_indi = ['hr_instance', 'hrv_instance', 'rr_instance', 'spo2_instance', 'drowsiness_instance'] 
            numerical_dict = {}
            for indi in numerical_indi: 
                individual = getattr(self.ontology, indi) 
                individual.hasNumericalValue = [] 
                numerical_dict[indi] = individual
                individual.PhysiologicalStateDescribesActor = []
                individual.PhSFromObservations = [] 
                
            string_indi = ['accessories_instance', 'demographic_instance', 'sex_instance', 'facecharacteristics_instance']
            string_dict = {} 
            for indi in string_indi:
                individual = getattr(self.ontology, indi)
                individual.hasStringValue = []
                string_dict[indi] = individual 

            age_indi = getattr(self.ontology, "age_instance")
            age_indi.hasAgeValue = []
            for group in self.ontology.Age.instances(): 
                if group.name == "age_instance": 
                    continue 
                group.GroupHasAge = [] 
            driver = self.ontology.Actor.instances()[0]
            driver.ActorHasEyeState = []
            driver.ActorHasPhysiologicalState = []
            driver.ActorHasCharacteristics = []
            driver.ActorFromObservations = []
            driver.hasUniqueIdentifier = []
            fatigue_indi = getattr(self.ontology, "fatigue_instance") 
            fatigue_indi.FatigueIs = [] 
            fatigue_indi.PhysiologicalStateDescribesActor = []

            for state in self.ontology.EyeState.instances(): 
                state.EyeStateForActor = [] 

            for num, indi in numerical_dict.items():
                if num == 'hr_instance': 
                    indi.HRis = [] 
                elif num == 'hrv_instance':
                    indi.HRVis = []
                elif num == 'rr_instance':
                    indi.RRis = []
                elif num == 'spo2_instance':
                    for spo2 in self.ontology.SpO2.instances(): 
                        if spo2.name != num: 
                            spo2.isForSpO2 = []
                elif num == 'drowsiness_instance':
                    indi.DrowsinessIs = []

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





