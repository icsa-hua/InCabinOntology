# InCabinOntology
An in cabin ontology for in cabin vehicle environment. 
![Version](https://img.shields.io/badge/version-0.1.7-brightgreen.svg)

## Overview
This repository creates an OWL representation or ontology for an in-cabin vehicle environment, set to have sensors which capture the state of the air and driver. 
This work was implemented and illustrated for the purposes of the AIQ-READY European Project and for SC3-UC2. 

## Components
- **ConnectingInCabin.rdf (`Main Onrology`)**: Represents the main ontology using OWL in XML. 
- **scipts (`Python scripts`)**: Contains conversion.py (convert csv into individuals) and merge.py (merge the two ontologies). 
- **data (`CSV and TTL data`)**: Contains the available csv files and the conversion results as ttl (Turtle format).
- **ontologies (`OWL ontologies`)**: Contains the main and merged ontologies in OWL/RDF format. 

 
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
6. To use the simulated scenarios:
   ```sh
   cd scipts
   python3 main.py
   ```
This executes a python script that creates a graph, adds target individuals, 
executes queries and creates links between individuals. 

*** 
## Synthetic Data geberation

Uses the TimeGAN solution as implemented in [TimeGAN](https://github.com/flaviagiammarino/time-gan-tensorflow)
TensorFlow implementation of synthetic time series generation model introduced in Yoon, J., Jarrett, D. and Van der Schaar, M., 2019. Time-series generative adversarial networks. Advances in neural information processing systems, 32.

   

