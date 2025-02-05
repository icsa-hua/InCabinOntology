from owlready2 import * 
from scripts.ontology_parser import OntologyParser
import logging 

logger = logging.getLogger("owlready2").setLevel(logging.ERROR)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    logger.info(os.getcwd())
    parent_dir = os.getcwd()

    ontology_path = os.path.join(parent_dir,"ontologies" )
    file = os.path.join(ontology_path, "in_cabin_domain.rdf")
    dataset_path = os.path.join(parent_dir, "data")
    dataset_file = os.path.join(dataset_path, "test_set_ontology.csv")
    parser = OntologyParser(file, logger)
    message = parser.parse_observations(dataset_path=dataset_file)
    print(message)

if __name__ == "__main__":
    main()