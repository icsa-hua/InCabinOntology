from src.designs.ontology_parser import OntologyParser
from src.designs.individuals_generation import IndGenerator
from src.tools.logger import get_logger 

import os

from owlready2 import * 


logger = get_logger("aiq_onto")

def main():
    logger.info(os.getcwd())
    parent_dir = os.getcwd()
    assets_dir = os.path.join(parent_dir, "assets")
    ontology_path = os.path.join(assets_dir,"ontologies" )
    file = os.path.join(ontology_path, "in_cabin_ontology.owl")
    dataset_path = os.path.join(assets_dir, "data")
    dataset_file = os.path.join(dataset_path, "test_set_ontology.csv")
    parser = OntologyParser(file, logger)
    
    if not getattr(parser.ontology, "HR_THR").instances():
        ind_generator = IndGenerator(f'{assets_dir}/data/metrics_thresholds.csv', parser.ontology)
        ind_generator.create_individuals()

    message = parser.parse_observations(dataset_path=dataset_file)
    logger.info(message)
    parser.print_results()


if __name__ == "__main__":
    main()
