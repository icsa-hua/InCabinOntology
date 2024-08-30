from rdflib import Graph
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logging.info("Starting merging of ontologies...")

# Load OWL ontology (RDF/XML format)
g1 = Graph()
g1.parse("../ConnectingInCabin.rdf", format="xml")

logging.debug("Ontology 1 loaded.")

# Load RDF ontology (Turtle format as an example)
g2 = Graph()
g2.parse("../thresholds.ttl", format="turtle")

logging.debug("Ontology 2 loaded.")

# Merge the two graphs
g1 += g2

# Save the merged ontology
g1.serialize("../merged_ontology.rdf", format="xml")

logging.info("Merging of ontologies completed.")