from owlready2 import * 
from designs.ontology_parser import OntologyParser
from designs.individuals_generation import IndGenerator
from tools.logger import logger 

def main():
    logger.info(os.getcwd())
    parent_dir = os.getcwd()

    ontology_path = os.path.join(parent_dir,"ontologies" )
    file = os.path.join(ontology_path, "in_cabin_ontology.owl")
    dataset_path = os.path.join(parent_dir, "data")
    dataset_file = os.path.join(dataset_path, "test_set_ontology.csv")
    parser = OntologyParser(file, logger)
    
    if not getattr(parser.ontology, "HR_THR").instances():
        ind_generator = IndGenerator('data/metrics_thresholds.csv', parser.ontology)
        ind_generator.create_individuals()

    message = parser.parse_observations(dataset_path=dataset_file)
    print(message)

if __name__ == "__main__":
    main()