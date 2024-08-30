from rdflib import Graph, URIRef, Literal, Namespace, RDF, RDFS, OWL 
from rdflib.namespace import XSD 
import csv
import logging 


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logging.info("Starting conversion of CSV to OWL...")

#Create a new graph which holds the information about the csv ontology 
graph = Graph() 

# Define the namespace to connect with the ontology. 
ns = Namespace("http://test.org/vehicleOntology#")

#Create the class of the ontology 
converted_class = URIRef(ns["Thresholds"]) #Give the name of the class you want to merge with 
graph.add((converted_class, RDF.type, OWL.Class))

#Define the Data Properties. 
hasHeartRateThreshold = URIRef(ns["hasHeartRateThreshold"])
hasOxygenLevelThreshold = URIRef(ns["hasOxygenLevelThreshold"])

#Add the datatype properties to the ontology
graph.add((hasHeartRateThreshold, RDF.type, OWL.DatatypeProperty))
graph.add((hasHeartRateThreshold, RDFS.domain, converted_class))
graph.add((hasHeartRateThreshold, RDFS.range, XSD.float))

graph.add((hasOxygenLevelThreshold, RDF.type, OWL.DatatypeProperty))
graph.add((hasOxygenLevelThreshold, RDFS.domain, converted_class))
graph.add((hasOxygenLevelThreshold, RDFS.range, XSD.float))

logging.debug("Class and Data Properties added to the ontology.")
with open('../data_SAT_20240603.csv', 'r') as file: #Give the /path/to/your/csv/file.csv 
    reader = csv.DictReader(file)
    for index, row in enumerate(reader):

        #Naming the individuals
        threshold_uri = URIRef(ns["Thresholds_" + str(index)]) 
        
        #Specifying the class/type of the individuals
        graph.add((threshold_uri, RDF.type, converted_class))

        #Adding them to the new ontology. 
        graph.add((threshold_uri, ns.hasHeartRateThreshold, Literal(row["HR"], datatype=XSD.float)))
        graph.add((threshold_uri, ns.hasOxygenLevelThreshold, Literal(row["RR"], datatype=XSD.float)))
        
        # Add other properties as needed

# Serialize the graph to an RDF file or load directly into Protege
graph.serialize("../thresholds.ttl")
logging.info("Conversion completed successfully.")
