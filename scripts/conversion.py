from rdflib import Graph, URIRef, Literal, Namespace, RDF, RDFS, OWL 
from rdflib.namespace import XSD 
import csv
import logging 
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("Starting conversion of CSV to OWL...")

#Create a new graph which holds the information about the csv ontology 
graph = Graph() 

#Get parent directory of the current file
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

#Provide CSV file name 
csv_file = input("Enter the name of the CSV file: ")

result = [] 
path = []
for root, dir, files in os.walk(parent_dir):
    if csv_file in files:
        result.append(os.path.join(root, csv_file))
        path = root

csv_file = result[0]

if result is None: 
    logger.error("File not found")
    exit(1)

csv_name = (csv_file.split(".")[-2]).split("/")[-1]
captured_data_file = csv_name + ".ttl"
captured_data_file = os.path.join(path, captured_data_file)


# Define the namespace to connect with the ontology. 
ns = Namespace("http://test.org/vehicleOntology#")

#Create the class of the ontology 
converted_class = URIRef(ns["Thresholds"]) #Give the name of the class you want to merge with 
graph.add((converted_class, RDF.type, OWL.Class))

#Define the Data Properties. 
hasHeartRateThreshold = URIRef(ns["hasHeartRateThreshold"])
hasOxygenLevelThreshold = URIRef(ns["hasOxygenLevelThreshold"])
hasResponeRateThreshold = URIRef(ns["hasResponeRateThreshold"])
hasHeartRateVariabilityThreshold = URIRef(ns["hasHeartRateVariabilityThreshold"])

#Add the datatype properties to the ontology
graph.add((hasHeartRateThreshold, RDF.type, OWL.DatatypeProperty))
graph.add((hasHeartRateThreshold, RDFS.domain, converted_class))
graph.add((hasHeartRateThreshold, RDFS.range, XSD.float))

graph.add((hasOxygenLevelThreshold, RDF.type, OWL.DatatypeProperty))
graph.add((hasOxygenLevelThreshold, RDFS.domain, converted_class))
graph.add((hasOxygenLevelThreshold, RDFS.range, XSD.int))

graph.add((hasResponeRateThreshold, RDF.type, OWL.DatatypeProperty))
graph.add((hasResponeRateThreshold, RDFS.domain, converted_class))
graph.add((hasResponeRateThreshold, RDFS.range, XSD.float))

graph.add((hasHeartRateVariabilityThreshold, RDF.type, OWL.DatatypeProperty))
graph.add((hasHeartRateVariabilityThreshold, RDFS.domain, converted_class))
graph.add((hasHeartRateVariabilityThreshold, RDFS.range, XSD.float))

logger.debug("Class and Data Properties added to the ontology.")

with open(csv_file, 'r') as file: #Give the /path/to/your/csv/file.csv 
    reader = csv.DictReader(file)
    for index, row in enumerate(reader):

        #Naming the individuals
        threshold_uri = URIRef(ns["Thresholds_" + str(index)]) 
        
        #Specifying the class/type of the individuals
        graph.add((threshold_uri, RDF.type, converted_class))

        #Adding them to the new ontology. 
        graph.add((threshold_uri, ns.hasHeartRateThreshold, Literal(row["Maximum-HR"], datatype=XSD.float)))
        graph.add((threshold_uri, ns.hasHeartRateThreshold, Literal(row["Minimum-HR"], datatype=XSD.float)))
        
        graph.add((threshold_uri, ns.hasResponeRateThreshold, Literal(row["Maximum-RR"], datatype=XSD.float)))
        graph.add((threshold_uri, ns.hasResponeRateThreshold, Literal(row["Minimum-RR"], datatype=XSD.float)))
        
        graph.add((threshold_uri, ns.hasHeartRateVariabilityThreshold, Literal(row["Maximum-HRV"], datatype=XSD.float)))
        graph.add((threshold_uri, ns.hasHeartRateVariabilityThreshold, Literal(row["Minimum-HRV"], datatype=XSD.float)))
        
        graph.add((threshold_uri, ns.hasOxygenLevelThreshold, Literal(row["Maximum-SPO2"], datatype=XSD.int)))
        graph.add((threshold_uri, ns.hasOxygenLevelThreshold, Literal(row["Minimum-SPO2"], datatype=XSD.int)))
        
        # Add other properties as needed
 
# Serialize the graph to an RDF file or load directly into Protege
graph.serialize(captured_data_file)
logger.info("Conversion completed successfully.")
