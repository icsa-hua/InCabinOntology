# InCabinOntology
An in cabin ontology for in cabin vehicle environment. 
![Version](https://img.shields.io/badge/version-0.1.5-brightgreen.svg)

## Overview
This repository creates an OWL representation or ontology for an in-cabin vehicle environment, set to have sensors which capture the state of the air and driver. 
This work was implemented and illustrated for the purposes of the AIQ-READY European Project and for SC3-UC2. 

## Components
- **ConnectingInCabin.rdf (`Main Onrology`)**: Represents the main ontology using OWL in XML. 
- **merged_ontology.rdf (`Merged with CSV Individuals`)**: Represents the main ontology with the csv indiciduals. 
- **scipts (`Python scripts`)**: Contains conversion.py (convert csv into individuals) and merge.py (merge the two ontologies). 
- **thresholds.ttl (`OWL from CSV`)**: Turtle representation of the converted ontology.

 
## Technologies
The main technologies used for this project are: 
* Python
* Protege
* OWL/RDF

## SetUp
1. Clone the repository:
```sh
git clone -b ontology https://github.com/icsa-hua/InCabinOntology.git
```

2. Navigate to the project directory:
```sh
cd InCabinOntology
```

3. Install the dependencies:
```sh
pip install -r requirements.txt
```

4. Use the ontology with Protege. Open Protege
5. File->Open->Select the ontology to open
   

