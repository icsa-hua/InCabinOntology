# InCabinOntology
An in cabin ontology for in cabin vehicle environment. 
![Version](https://img.shields.io/badge/version-0.2.0-brightgreen.svg)

## Overview
This repository creates an OWL representation or ontology for an in-cabin vehicle environment, set to have sensors
which capture the state of the driver.

## Components
- **/data** &rarr; Stores the datasets used for testing the ontology capabilities.  
- **/scipts** &rarr; (`Python scripts`) Stores the python scripts to create and parse SWRL rules in the ontology 
to allow numerical and logical reasoning.
- **/labels** &rarr; Stores the results of reasoning in the ontology in JSON format. 
- **/ontologies** &rarr; Stores the ontologies in OWL format. `in_cabin_ontology.rdf` is the original ontology 
used in the reasoning, whereas the `updated_ontology.owl` is an the result of processing the SWRL rules. 

 
## Technologies
The main technologies used for this project are: 
* Python &rarr; used for creating the SWRL rules and executing the reasoning.
* Protege &rarr; used for crafting the ontology and visualising it along with the reasoning results.
* owlready2 &rarr; used for creating the ontology in python 

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

   

