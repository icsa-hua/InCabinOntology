from rdflib import Graph
import logging
import os
import pdb
import time 
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

#Get parent directory of the current file
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ontologies_dir = os.path.join(parent_dir, "ontologies")

logger.info("Starting merging of ontologies...")

# Load OWL ontology (RDF/XML format)
g1 = Graph()
g1.parse("../ConnectingInCabin.rdf", format="xml")

logger.debug("Ontology 1 loaded.")

on2_file = input("Enter the name of the seconds ontology to merge with: ")
if on2_file.endswith(".csv") or on2_file.endswith(".txt"):
    logger.error("Please provide a valid ontology file.")
    exit(1)

result = [] 
path = []
for root, dir, files in os.walk(parent_dir):
    if on2_file in files:
        result.append(os.path.join(root, on2_file))
        path = root

# Load RDF ontology (Turtle format as an example)
g2 = Graph()
if on2_file.endswith(".ttl"):
    g2.parse(result[0], format="turtle")
else:
    g2.parse(result[0], format="xml")

logger.debug("Ontology 2 loaded.")

# Merge the two graphs
g1 += g2

id = time.strftime("%Y%m%d-%H%M%S")
new_on_name = f"merged_ontology_{id}.rdf"

# Save the merged ontology
g1.serialize(os.path.join(ontologies_dir,new_on_name ), format="xml")

logger.info("Merging of ontologies completed.")