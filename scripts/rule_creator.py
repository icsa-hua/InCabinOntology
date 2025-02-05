from owlready2 import *
from rdflib import Graph, URIRef, Literal
import os 
import uuid 
import json 
import random
import pdb


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
        self.logger = ontology_parser.logger
        self.age_groups = None 


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
        self.logger("Refined Rules Saved.")
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
            self.logger.info(f"New instance of {ind_class} created.")
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
            

    def observations_to_classes(self, obs, cls_name, property_name):
        """
        This function connects the observation to every class corresponding to a column in the 
        dataset. It uses the object property name to connect to the Actor or Physiological State class. 
        Args:
            obs (Observation): The observation to connect to the class.
            cls_name (str): The name of the class to connect to (Actor or Physiological State).
            property_name (str): The name of the property to connect to.
        """

        if obs is None: 
            return None 
        
        # Get the subclasses for the desired class. 
        phs_class = next(cls for cls in self.ontology.classes() if cls.name.strip() == cls_name)

        # Check the property and connect the observation to the class.
        for prop in obs.get_properties():
            try: 
                name_prop = prop.name.split('has')[1]
            except: 
                self.logger.info("Property already in ontology...")
                continue

            name_prop = "Drowsiness" if name_prop == "DROWSY" else name_prop

            # Flag is raised when Physiological State class iterates through subclasses not in the dataset.
            flag = [True for cls in phs_class.subclasses() if cls.name == name_prop]
    
            if not flag:
                continue

            # Connect Observation to each subclass 
            with self.ontology:
                
                # Instance of the subclass (e.g. HR, Accessories, ..., etc.)
                instance = self.create_instances(name_prop)
                
                # Check if instance was created.
                if instance is None: 
                    continue
               
                # Define the SWRL rule for the property. 
                rule = Imp() 
                rule.set_as_rule(
                    f"""
                        Observations(?obs_ind),
                        {prop.name}(?obs_ind,?Val),
                        {name_prop}(?{name_prop.lower()})
                        -> {property_name}(?obs_ind,?{name_prop.lower()})
                    """
                )

                self.logger.info(f"Rule created for Observations(?obs_ind),{prop.name}(?obs_ind,?Val),{name_prop}(?{name_prop.lower()})-> {property_name}(?obs_ind,?{name_prop.lower()})")
        
        return True  

            
    def assign_values(self, obs, cls_property, property_name):
        """
        This function assigns the values of the observations to the instances of the classes, 
        previously created in the ontology. Requires the reasoner to have been executed, otherwise 
        it will not find the newly created instances.
        Args:
            obs (Observation): The observation to storing the numerical values from the dataset. 
            cls_property (str): The name of the object property to use. 
            property_name (str): The name of the data property to pass the values. 
        """

        with self.ontology: 
            # Check if the observation has the object property.
            if not hasattr(obs, cls_property):
                return None 
            
            ind_property = getattr(obs, cls_property)
            
            if len(ind_property)==0:
                return None 
            
            # Iterate through the instances of the object property.
            for instance in ind_property:
                
                if not hasattr(instance,property_name): 
                    continue

                name_of_ind = instance.name.split('_')[0]
                instance_property = getattr(instance, property_name)

                # Pass the value of the observation to the instance.
                if name_of_ind == 'spo2': 
                    instance_property.append(int(obs.hasSpO2.pop(0)))
                elif name_of_ind == 'hr':
                    instance_property.append(int(obs.hasHR.pop(0)))
                elif name_of_ind == 'rr':
                    instance_property.append(int(obs.hasRR.pop(0)))
                elif name_of_ind == 'hrv':
                    instance_property.append(int(obs.hasHRV.pop(0)))
                elif name_of_ind == 'sex':
                    instance_property.append(obs.hasSex.pop(0))
                elif name_of_ind == 'age':
                    # Because Age is a subclass of actor with numerical value, explicitly use a distinct property name. 
                    if hasattr(instance, 'hasAgeValue'):
                        instance_property = getattr(instance, 'hasAgeValue')
                        instance_property.append(int(obs.hasAge.pop(0)))
                elif name_of_ind == 'facecharacteristics':
                    instance_property.append(obs.hasFaceCharacteristics.pop(0))
                elif name_of_ind == 'demographic':
                    instance_property.append(obs.hasDemographic.pop(0))
                elif name_of_ind == 'accessories':
                    instance_property.append(obs.hasAccessories.pop(0))
                elif name_of_ind == 'drowsiness':
                    instance_property.append(int(obs.hasDROWSY.pop(0)))


    def determine_age(self): 
        """
        This funciton creates the rules to categorize the age of the actor into 
        a group : 
        * Young (0-18) 
        * Adult (18-65)
        * Old (>65) 
        """

        with self.ontology: 

            if self.ontology.Age is not None: 
                age_rules = [
                    ("Young", "lessThanOrEqual", 18),
                    ("Adult", "greaterThanOrEqual", 18, "lessThanOrEqual", 65),
                    ("Old", "greaterThan", 65)
                ]
                
                for rule in age_rules:
                    self.create_instances(rule[0])
                    age_rule = Imp()
                    age_rule.set_as_rule(
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

        with self.ontology: 
            for i,group in enumerate(self.age_group_names): 
                age = self.age_groups[i]

                hr_rule_low = Imp()
                self.create_instances("Low_HR")
                hr_rule_low.set_as_rule(
                    f"""
                    Actor(?actor), 
                    ActorHasCharacteristics(?actor, age_instance),
                    AgeBelongsToGroup(age_instance, ?group),
                    {group}(?group),

                    HR(hr_instance),
                    hasNumericalValue(hr_instance, ?hr_value),
                    greaterThan(?hr_value, 0),
                    HR_THR(low_hr_{age}), 
                    hasThrValue(low_hr_{age}, ?low_value),
                    lessThan(?hr_value, ?low_value),

                    Low_HR(?low_hr) ->  HRis(hr_instance, ?low_hr)
                    """)
                
                hr_rule_slightly_low = Imp()
                self.create_instances("Slightly_Low_HR")
                hr_rule_slightly_low.set_as_rule(
                    f"""
                    Actor(?actor), 
                    ActorHasCharacteristics(?actor, age_instance),
                    AgeBelongsToGroup(age_instance, ?group),
                    {group}(?group),

                    HR(?hr),
                    hasNumericalValue(?hr, ?hr_value),
                    HR_THR(low_hr_{age}), 
                    hasThrValue(low_hr_{age}, ?low_value),
                    greaterThanOrEqual(?hr_value, ?low_value),
                    HR_THR(moderate_hr_{age}),
                    hasThrValue(moderate_hr_{age}, ?moderate_value),
                    lessThan(?hr_value,?moderate_value),

                    Slightly_Low_HR(?slightly_low_instance) -> HRis(?hr, ?slightly_low_instance)
                    """)
            
                hr_rule_moderate = Imp()
                self.create_instances("Moderate_HR")
                hr_rule_moderate.set_as_rule(
                    f"""
                    Actor(?actor), 
                    ActorHasCharacteristics(?actor, ?age),
                    AgeBelongsToGroup(?age, ?group),
                    {group}(?group),

                    HR(?hr),
                    hasNumericalValue(?hr, ?hr_value),
                    HR_THR(moderate_hr_{age}),
                    hasThrValue(moderate_hr_{age}, ?moderate_value),
                    greaterThanOrEqual(?hr_value, ?moderate_value),
                    HR_THR(high_hr_{age}),
                    hasThrValue(high_hr_{age}, ?high_value),
                    lessThan(?hr_value,?high_value), 

                    Moderate_HR(?moderate_hr) ->  HRis(?hr,?moderate_hr)
                    """)
                
                hr_rule_high = Imp()
                self.create_instances("High_HR")
                hr_rule_high.set_as_rule(
                    f"""
                    Actor(?actor), 
                    ActorHasCharacteristics(?actor, ?age),
                    AgeBelongsToGroup(?age, ?group),
                    {group}(?group),

                    HR(?hr),
                    hasNumericalValue(?hr, ?hr_value),
                    HR_THR(high_hr_{age}),
                    hasThrValue(high_hr_{age}, ?high_value),
                    greaterThanOrEqual(?hr_value, ?high_value),

                    High_HR(?high_hr) ->  HRis(?hr, ?high_hr)
                    """)

    
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

        with self.ontology: 
            
            for i,group in enumerate(self.age_group_names):     
                age = self.age_groups[i]
                hrv_rule_very_low = Imp()
                self.create_instances("Very_Low_HRV")
                hrv_rule_very_low.set_as_rule(
                    f"""
                    Actor(?actor), 
                    ActorHasCharacteristics(?actor, ?age),
                    AgeBelongsToGroup(?age, ?group),
                    {group}(?group),

                    HRV(?hrv),
                    hasNumericalValue(?hrv, ?hrv_value),
                    greaterThan(?hrv_value, 0),
                    HRV_THR(low_hrv_{age}), 
                    hasThrValue(low_hrv_{age}, ?low_value),
                    lessThan(?hrv_value,?low_value),

                    Very_Low_HRV(?very_low_hrv) -> HRVis(?hrv,?very_low_hrv)
                    """)
                
                hrv_rule_low = Imp()
                self.create_instances("Low_HRV")
                hrv_rule_low.set_as_rule(
                    f"""
                    Actor(?actor), 
                    ActorHasCharacteristics(?actor, ?age),
                    AgeBelongsToGroup(?age, ?group),
                    {group}(?group),

                    HRV(?hrv),
                    hasNumericalValue(?hrv, ?hrv_value),
                    HRV_THR(low_hrv_{age}), 
                    hasThrValue(low_hrv_{age}, ?low_value),
                    greaterThanOrEqual(?hrv_value, ?low_value),
                    HRV_THR(moderate_hrv_{age}),
                    hasThrValue(moderate_hrv_{age}, ?moderate_value),
                    lessThan(?hrv_value,?moderate_value), 

                    Low_HRV(?low_hrv) -> HRVis(?hrv,?low_hrv)
                    """)
            
                hrv_rule_moderate = Imp()
                self.create_instances("Moderate_HRV")
                hrv_rule_moderate.set_as_rule(
                    f"""
                    Actor(?actor), 
                    ActorHasCharacteristics(?actor, ?age),
                    AgeBelongsToGroup(?age, ?group),
                    {group}(?group),

                    HRV(?hrv),
                    hasNumericalValue(?hrv, ?hrv_value),
                    HRV_THR(moderate_hrv_{age}),
                    hasThrValue(moderate_hrv_{age}, ?moderate_value),
                    greaterThanOrEqual(?hrv_value, ?moderate_value),
                    HRV_THR(high_hrv_{age}),
                    hasThrValue(high_hrv_{age}, ?high_value),
                    lessThan(?hrv_value,?high_value),

                    Moderate_HRV(?moderate_hrv) -> HRVis(?hrv,?moderate_hrv)
                    """)
                
                hrv_rule_high = Imp()
                self.create_instances("High_HRV")
                hrv_rule_high.set_as_rule(
                    f"""
                    Actor(?actor), 
                    ActorHasCharacteristics(?actor, ?age),
                    AgeBelongsToGroup(?age, ?group),
                    {group}(?group),

                    HRV(?hrv),
                    hasNumericalValue(?hrv, ?hrv_value),
                    HRV_THR(high_hrv_{age}),
                    hasThrValue(high_hrv_{age}, ?high_value),
                    greaterThanOrEqual(?hrv_value, ?high_value),

                    High_HRV(?high_hrv) -> HRVis(?hrv,?high_hrv)
                    """)


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

        with self.ontology: 
            for i,group in enumerate(self.age_group_names):

                age = self.age_groups[i]

                rr_rule_very_low = Imp()
                self.create_instances("Very_Low_RR")
                rr_rule_very_low.set_as_rule(
                    f"""
                    Actor(?actor), 
                    ActorHasCharacteristics(?actor, ?age),
                    AgeBelongsToGroup(?age, ?group),
                    {group}(?group),

                    RR(?rr),
                    hasNumericalValue(?rr, ?rr_value),
                    greaterThan(?rr_value, 0),
                    RR_THR(low_rr_{age}), 
                    hasThrValue(low_rr_{age}, ?low_value),
                    lessThan(?rr_value, ?low_value), 

                    Very_Low_RR(?very_low_rr)  -> RRis(?rr,?very_low_rr)
                    """)
                
                rr_rule_low = Imp()
                self.create_instances("Low_RR")
                rr_rule_low.set_as_rule(
                    f"""
                    Actor(?actor), 
                    ActorHasCharacteristics(?actor, ?age),
                    AgeBelongsToGroup(?age, ?group),
                    {group}(?group),

                    RR(?rr),
                    hasNumericalValue(?rr, ?rr_value),
                    RR_THR(low_rr_{age}), 
                    hasThrValue(low_rr_{age}, ?low_value),
                    greaterThanOrEqual(?rr_value, ?low_value),
                    RR_THR(moderate_rr_{age}),
                    hasThrValue(moderate_rr_{age}, ?moderate_value),
                    lessThan(?rr_value,?moderate_value), 

                    Low_RR(?low_rr) -> RRis(?rr,?low_rr)
                    """)
            
                rr_rule_moderate = Imp()
                self.create_instances("Moderate_RR")
                rr_rule_moderate.set_as_rule(
                    f"""
                    Actor(?actor), 
                    ActorHasCharacteristics(?actor, ?age),
                    AgeBelongsToGroup(?age, ?group),
                    {group}(?group),

                    RR(?rr),
                    hasNumericalValue(?rr, ?rr_value),
                    RR_THR(moderate_rr_{age}),
                    hasThrValue(moderate_rr_{age}, ?moderate_value),
                    greaterThanOrEqual(?rr_value, ?moderate_value),
                    RR_THR(high_rr_{age}),
                    hasThrValue(high_rr_{age}, ?high_value),
                    lessThan(?rr_value, ?high_value), 

                    Moderate_RR(?moderate_rr) -> RRis(?rr,?moderate_rr)
                    """)
                
                rr_rule_high = Imp()
                self.create_instances("High_RR")
                rr_rule_high.set_as_rule(
                    f"""
                    Actor(?actor), 
                    ActorHasCharacteristics(?actor, ?age),
                    AgeBelongsToGroup(?age, ?group),
                    {group}(?group),

                    RR(?rr),
                    hasNumericalValue(?rr, ?rr_value),
                    RR_THR(high_rr_{age}),
                    hasThrValue(high_rr_{age}, ?high_value),
                    greaterThanOrEqual(?rr_value, ?high_value),

                    High_RR(?high_rr) -> RRis(?rr,?high_rr)
                    """)
       

    def determine_spo2(self): 
        """
        This function creates the rules to categorize the SPO2 of the actor into
        threshold ranges: 
        * Normal 
        * Slightly_Low
        * Critical

        These threshold ranges change based on the Age group of the actor.
        """

        with self.ontology: 
           
            for i,group in enumerate(self.age_group_names): 
                
                age = self.age_groups[i]

                spo2_rule_normal = Imp()
                self.create_instances("Normal_SpO2")
                spo2_rule_normal.set_as_rule(
                    f"""
                    Actor(?actor), 
                    ActorHasCharacteristics(?actor, ?age),
                    AgeBelongsToGroup(?age, ?group),
                    {group}(?group),

                    SpO2(?spo2),
                    hasNumericalValue(?spo2, ?spo2_value),
                    SpO2_THR(moderate_spo2_{age}), 
                    hasThrValue(moderate_spo2_{age}, ?moderate_value),
                    greaterThanOrEqual(?spo2_value, ?moderate_value), 
                    SpO2_THR(high_spo2_{age}),
                    hasThrValue(high_spo2_{age}, ?high_value),
                    lessThanOrEqual(?spo2_value, ?high_value), 

                    Normal_SpO2(?normal_spo2) -> SpO2is(?spo2, ?normal_spo2)
                    """)
                
                spo2_rule_low = Imp()
                self.create_instances("Low_SpO2")
                spo2_rule_low.set_as_rule(
                    f"""
                    Actor(?actor), 
                    ActorHasCharacteristics(?actor, ?age),
                    AgeBelongsToGroup(?age, ?group),
                    {group}(?group),

                    SpO2(?spo2),
                    hasNumericalValue(?spo2, ?spo2_value),
                    SpO2_THR(low_spo2_{age}), 
                    hasThrValue(low_spo2_{age}, ?low_value),
                    greaterThanOrEqual(?spo2_value, ?low_value),
                    SpO2_THR(moderate_spo2_{age}),
                    hasThrValue(moderate_spo2_{age}, ?moderate_value),
                    lessThan(?spo2_value,?moderate_value),

                    Low_SpO2(?low_spo2) -> SpO2is(?spo2, ?low_spo2)
                    """)
            
                spo2_rule_critical = Imp()
                self.create_instances("Critical_SpO2")
                spo2_rule_critical.set_as_rule(
                    f"""
                    Actor(?actor), 
                    ActorHasCharacteristics(?actor, ?age),
                    AgeBelongsToGroup(?age, ?group),
                    {group}(?group),

                    SpO2(?spo2),
                    hasNumericalValue(?spo2, ?spo2_value),
                    SpO2_THR(low_spo2_{age}),
                    hasThrValue(low_spo2_{age}, ?low_value),
                    lessThan(?spo2_value, ?low_value),

                    Critical_SpO2(?critical_spo2) -> SpO2is(?spo2, ?critical_spo2)
                    """)
                
                
    def determine_drowsiness(self): 
        """
        This function creates the rules to categorize the Drowsiness of the actor into
        threshold ranges based on Karolinska Sleep Scale (KSS)
        * Level_3 (actor is awake) 
        * Level_5 (actor is neither asleep or awake)
        * Level_7 (actor is asleep with no effor of waking up)
        * Level_9 (actor is asleep with effort of waking up)
        """

        with self.ontology:
            drowsiness_state_with_value_1 = Imp() 
            self.create_instances("Level_3_KSS")
            drowsiness_state_with_value_1.set_as_rule(
                """
                Drowsiness(?ds),
                hasNumericalValue(?ds, ?ds_value),
                lessThanOrEqual(?ds_value, 1), 
                greaterThan(?ds_value, 0),
                Level_3_KSS(?level_3_kss)  ->  DrowsinessIs(?ds, ?level_3_kss)
                """
            )

            drowsiness_state_with_value_2 = Imp() 
            self.create_instances("Level_5_KSS")
            drowsiness_state_with_value_2.set_as_rule(
                """
                Drowsiness(?ds),
                hasNumericalValue(?ds, ?ds_value),
                lessThanOrEqual(?ds_value, 2),
                greaterThan(?ds_value, 1),
                Level_5_KSS(?level_5_kss) -> DrowsinessIs(?ds, ?level_5_kss)
                """ 
            )

            drowsiness_state_with_value_3 = Imp() 
            self.create_instances("Level_7_KSS")
            drowsiness_state_with_value_3.set_as_rule(
                """
                Drowsiness(?ds),
                hasNumericalValue(?ds, ?ds_value),
                lessThanOrEqual(?ds_value, 3),
                greaterThan(?ds_value, 2),
                Level_7_KSS(?level_7_kss) -> DrowsinessIs(?ds, ?level_7_kss)
                """
            )

            drowsiness_state_with_value_4 = Imp() 
            self.create_instances("Level_9_KSS")
            drowsiness_state_with_value_4.set_as_rule(
                """
                Drowsiness(?ds),
                hasNumericalValue(?ds, ?ds_value),
                lessThanOrEqual(?ds_value, 4),
                greaterThan(?ds_value, 3),
                Level_9_KSS(?level_9_kss) -> DrowsinessIs(?ds, ?level_9_kss)
                """
            )


    def connect_actor_to_values(self): 
        """
        This function creates the rules to connect the actor to the physiological values, 
        and characteristics of the actor. This uses the instances of each class, to improve 
        reasoner performance. 
        
        NOTE: This solution means that the instances remain the same during the iterative execution. 
        If an instance is deleted or non existent the reasoner will detect an inconsistency error in this 
        class. 
        """

        with self.ontology: 
            phs_state = Imp() 
            phs_state.set_as_rule(
                """
                Actor(driver), 
                HR(hr_instance), 
                HRV(hrv_instance),
                RR(rr_instance),
                SpO2(spo2_instance),
                Drowsiness(drowsiness_instance)
                 -> ActorHasPhysiologicalState(driver,hr_instance), 
                    ActorHasPhysiologicalState(driver,hrv_instance),
                    ActorHasPhysiologicalState(driver,rr_instance),
                    ActorHasPhysiologicalState(driver,spo2_instance),
                    ActorHasPhysiologicalState(driver,drowsiness_instance) 
                """
            )

            actor_chars = Imp() 
            actor_chars.set_as_rule(
                """
                Actor(driver),
                Accessories(accessories_instance),
                Age(age_instance),
                Demographic(demographic_instance),
                FaceCharacteristics(facecharacteristics_instance),
                Sex(sex_instance)
                 -> ActorHasCharacteristics(driver,age_instance),
                    ActorHasCharacteristics(driver,accessories_instance),
                    ActorHasCharacteristics(driver,facecharacteristics_instance),
                    ActorHasCharacteristics(driver,demographic_instance),
                    ActorHasCharacteristics(driver,sex_instance)
                """
            )

        
    def determine_fatigue(self): 
        """
        This function is used to create the rules to categorize the fatigue of the actor into
        threshold ranges based on the previous physiological values.
        * Awake 
        * Sleeping 
        * Microsleep
        * Drowsy 
        * Drowsiness Suspected 
        * Undefined State
        """
        
        with self.ontology:
            self.ontology.Fatigue("fatigue_instance")

            # First Option where HR is Low and RR is High with corresponding KSS
            fatigue_sleep_state_1 = Imp()
            self.create_instances("Sleep")
            fatigue_sleep_state_1.set_as_rule(
                """
                Actor(?actor), 
                ActorHasPhysiologicalState(?actor, ?hr),
                ActorHasPhysiologicalState(?actor, ?hrv),
                ActorHasPhysiologicalState(?actor, ?rr),
                ActorHasPhysiologicalState(?actor, ?spo2),
                ActorHasPhysiologicalState(?actor, ?ds),
                HRis(?hr, ?low_hr), Low_HR(?low_hr),
                HRVis(?hrv, ?low_hrv), Low_HRV(?low_hrv),
                RRis(?rr, ?low_rr), Low_RR(?low_rr),
                SpO2is(?spo2, ?low_spo2), Low_SpO2(?low_spo2),
                DrowsinessIs(?ds, ?low_ds), Level_7_KSS(?low_ds),
                Fatigue(fatigue_instance),
                Sleep(?fatigue)
                ->  ActorHasPhysiologicalState(?actor, fatigue_instance),
                    FatigueIs(fatigue_instance, ?fatigue),
                """)
            
            
            
            # Third Option for sleeping where HR is High and RR is High with High KSS
            fatigue_sleep_state_2 = Imp()
            fatigue_sleep_state_2.set_as_rule(
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
                SpO2is(?spo2, ?low_spo2), Low_SpO2(?low_spo2),
                DrowsinessIs(?ds, ?low_ds), Level_7_KSS(?low_ds),
                Fatigue(fatigue_instance),
                Sleep(?fatigue)
                ->  ActorHasPhysiologicalState(?actor, fatigue_instance),FatigueIs(fatigue_instance, ?fatigue),
                """)
            

            # Third Option wher HR is High and RR is Low
            fatigue_sleep_state_3 = Imp()
            fatigue_sleep_state_3.set_as_rule(
                """
                Actor(?actor), 
                ActorHasPhysiologicalState(?actor, ?hr),
                ActorHasPhysiologicalState(?actor, ?hrv),
                ActorHasPhysiologicalState(?actor, ?rr),
                ActorHasPhysiologicalState(?actor, ?spo2),
                ActorHasPhysiologicalState(?actor, ?ds),
                HRis(?hr, ?low_hr), High_HR(?low_hr),
                HRVis(?hrv, ?low_hrv), Low_HRV(?low_hrv),
                RRis(?rr, ?low_rr), Low_RR(?low_rr),
                SpO2is(?spo2, ?low_spo2), Low_SpO2(?low_spo2),
                DrowsinessIs(?ds, ?low_ds), Level_7_KSS(?low_ds),
                Fatigue(fatigue_instance),
                Sleep(?fatigue)
                ->  ActorHasPhysiologicalState(?actor, fatigue_instance), FatigueIs(fatigue_instance, ?fatigue),
                """)
            
            # Fourth Option where HR is Low and RR is Low
            fatigue_sleep_state_4 = Imp()
            fatigue_sleep_state_4.set_as_rule(
                """
                Actor(?actor), 
                ActorHasPhysiologicalState(?actor, ?hr),
                ActorHasPhysiologicalState(?actor, ?hrv),
                ActorHasPhysiologicalState(?actor, ?rr),
                ActorHasPhysiologicalState(?actor, ?spo2),
                ActorHasPhysiologicalState(?actor, ?ds),
                HRis(?hr, ?low_hr), Low_HR(?low_hr),
                HRVis(?hrv, ?low_hrv), Low_HRV(?low_hrv),
                RRis(?rr, ?low_rr), High_RR(?low_rr),
                SpO2is(?spo2, ?low_spo2), Low_SpO2(?low_spo2),
                DrowsinessIs(?ds, ?low_ds), Level_7_KSS(?low_ds),
                Fatigue(fatigue_instance),
                Sleep(?fatigue)
                ->  ActorHasPhysiologicalState(?actor, fatigue_instance),FatigueIs(fatigue_instance, ?fatigue)
                """)
            
            fatigue_awake_state_1 = Imp()
            self.create_instances("Awake")
            fatigue_awake_state_1.set_as_rule(
                """
                Actor(?actor), 
                ActorHasPhysiologicalState(?actor, ?hr),
                ActorHasPhysiologicalState(?actor, ?hrv),
                ActorHasPhysiologicalState(?actor, ?rr),
                ActorHasPhysiologicalState(?actor, ?spo2),
                ActorHasPhysiologicalState(?actor, ?ds),
                HRis(?hr, ?hr_val), Moderate_HR(?hr_val),
                HRVis(?hrv, ?hrv_val), Moderate_HRV(?hrv_val),
                RRis(?rr, ?rr_val), Moderate_RR(?rr_val),
                SpO2is(?spo2, ?spo2_val), Normal_SpO2(?spo2_val),
                DrowsinessIs(?ds, ?ds_val), Level_3_KSS(?ds_val),
                Fatigue(fatigue_instance),
                Awake(?fatigue)
                ->  ActorHasPhysiologicalState(?actor, fatigue_instance),
                    FatigueIs(fatigue_instance, ?fatigue),
                """)
            
            fatigue_awake_state_1 = Imp() 
            fatigue_awake_state_1.set_as_rule(
                """
                Actor(?actor), 
                ActorHasPhysiologicalState(?actor, ?hr),
                ActorHasPhysiologicalState(?actor, ?hrv),
                ActorHasPhysiologicalState(?actor, ?rr),
                ActorHasPhysiologicalState(?actor, ?spo2),
                ActorHasPhysiologicalState(?actor, ?ds),
                HRis(?hr, ?hr_val), Moderate_HR(?hr_val),
                HRVis(?hrv, ?hrv_val), Moderate_HRV(?hrv_val),
                RRis(?rr, ?rr_val), Moderate_RR(?rr_val),
                SpO2is(?spo2, ?spo2_val), Normal_SpO2(?spo2_val),
                DrowsinessIs(?ds, ?ds_val), Level_3_KSS(?ds_val),
                Fatigue(fatigue_instance),
                Awake(?fatigue)
                ->  ActorHasPhysiologicalState(?actor, fatigue_instance),
                    FatigueIs(fatigue_instance, ?fatigue),
                """)

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

        with self.ontology: 
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


    def set_up_rules(self, index): 
        """
        This function is used tp set up the rules for the ontology.
        The rules are created only on the first iteration of the loop.
        Args: 
            index: The index of the iteration.
        """

        try: 
            if index == 0: 
                self.connect_actor_to_values()
                self.determine_age()
                self.determine_HR()
                self.determine_HRV()
                self.determine_RR()
                self.determine_spo2()
                self.determine_drowsiness() 
                self.determine_fatigue()
                self.determine_eye_state() 
        except Exception as e:
            self.logger.info(e)
                


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
            self.logger.info("Preparing data for label")
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
                self.logger.info(f"Label created successfully: {label.hasDescription[0]}")
            self.logger.info("Label created successfully with name: label.json")
        
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

            for state in self.ontology.EyeClosure.instances(): 
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








