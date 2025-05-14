from owlready2 import * 
from scripts.ontology_parser import OntologyParser
from scripts.individuals_generation import IndGenerator
import logging 

logger = logging.getLogger("owlready2").setLevel(logging.ERROR)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    logger.info(os.getcwd())
    parent_dir = os.getcwd()

    ontology_path = os.path.join(parent_dir,"ontologies" )
    file = os.path.join(ontology_path, "in_cabin_ontology.owl")
    dataset_path = os.path.join(parent_dir, "data")
    dataset_file = os.path.join(dataset_path, "test_set_ontology.csv")
    parser = OntologyParser(file, logger)
    
    if not getattr(parser.ontology, "HR_THR").instances():
        ind_generator = IndGenerator('data/metrics_thresholds.csv', parser.ontology,logger)
        ind_generator.create_individuals()

    message = parser.parse_observations(dataset_path=dataset_file)
    print(message)

if __name__ == "__main__":
    main()