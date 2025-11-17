from src.tools.logger import get_logger 
from src.tools.common import get_assets_path

import os 
import pandas as pd 

from owlready2 import * 


logger = get_logger("aiq_onto")


class IndGenerator: 

    def __init__(self, df_path, ontology): 

        try: 
            self.dataset = pd.read_csv(df_path, sep=',')
        except Exception as e: 
            assets_dir = get_assets_path()
            data_filepath = os.path.join(assets_dir,"data/metrics_thresholds.csv")
            self.dataset = pd.read_csv(data_filepath)
            logger.exception("Error while reading the dataset: {}".format(e))
        
        self.ontology = ontology 
        self.age_group = [] 
        self.sex_group = [] 
        self.temp_group = []


    def check_if_individuals_exist(self, Superclass):
        try: 
            entity = getattr(self.ontology, Superclass)
            list_ind = entity.instances()
            if list_ind is None: 
                return False
            return True 

        except ValueError as v : 
            logger.exception(f"Error while checking if individuals exist: {v}")
            return False  
        

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
            logger.info(f"New instance of {ind_class} created.")
            return new_instance 
        return None


    def create_individuals(self): 
        with self.ontology: 
            subclasses = self.ontology.classes() 
            if subclasses is None: 
                logger.info("")
                return 
            
            if "Age" in subclasses: 
                self.age_group = [entity.name for entity in self.ontology.Age.subclasses()]
            else: 
                self.age_group = ["Young", "Middle-Aged", "Elderly"]

            if "Sex" in subclasses: 
                self.sex_group = [entity.name for entity in self.ontology.Sex.subclasses()]
            else: 
                self.sex_group = ["Male", "Female"]

            if "Temperature" in subclasses: 
                self.temp_group_group = [entity.name for entity in self.ontology.WeatherConditions.subclasses()]
            else: 
                self.temp_group = ["ColdTemp", "ModerateTemp","HotTemp"]

            for row in self.dataset.iterrows():
                try: 
                    name = f"{row[1]['Temperature '].lower().strip()}_{row[1]['Category'].lower().strip()}_{row[1]['Type'].lower().strip()}_{row[1]['Age Group '].lower().strip()}_{row[1]['Sex '].lower().strip()}"
                    new_instance = getattr(self.ontology, row[1]['Type'].strip()+"_THR")(name)
                    if "<=" in row[1]['Final Value']:
                        new_instance.hasThrValue = [int(row[1]['Final Value'].split("<=")[-1].strip())]
                    elif ">=" in row[1]['Final Value']:
                        new_instance.hasThrValue = [int(row[1]['Final Value'].split(">=")[-1].strip())]
                    elif "<" in row[1]['Final Value']:
                        new_instance.hasThrValue = [int(row[1]['Final Value'].split("<")[-1].strip())]
                    elif ">" in row[1]['Final Value']:
                        new_instance.hasThrValue = [int(row[1]['Final Value'].split(">")[-1].strip())]
                    logger.info(f"New instance {name} created.")

                except Exception as e:
                    logger.exception(f"Error: {e}")
                    continue

        self.synchronize_ontology()
        self.save_ontology()

            
    def synchronize_ontology(self): 
        """
        Synchronizes the ontology with the reasoner.
        Uses the PELLET reasoner to infer property values and synchronize the ontology, 
        as only PELLET supports numerical conditions for SWRL rules. 
        """
        with self.ontology: 
            sync_reasoner_pellet(infer_property_values=True)


    def save_ontology(self, filename='in_cabin_ontology.owl', format_save="rdfxml", format="xml"):
        assets_dir = get_assets_path() 
        ontology_save_path =  f"{assets_dir}/ontologies/{filename}"
        self.ontology.save(file=ontology_save_path) 
        logger.info(f"Ontology saved to {ontology_save_path}")


                

