# InCabinOntology
In cabin ontology for driver's health monitoring, using a 4D architecture to parse time series physiological measurements, through a DL approach. The ontology uses SWRL logical reasoning enhanced with GCI contextual reasoning to determine the Fatigue/Attention/Unresponsiveness of the driver. Validation includes CQ and consistency reporting, through a series of SPARQL statements that determine the completeness and accuracy plus adaptability (indirectly). ![Version](https://img.shields.io/badge/version-0.3.0-brightgreen.svg)
Specifically to infer physiological, cognitive and behavioral state of a vehicle driver using: 
* Physiological signals (HR, HRV, RR, SpO2, Drowsiness (KSS)) 
* Behavioral indicators (eye state, mouth state) 
* High-Level states (fatigue, attention, unresponsiveness) 
* Demographic characteristics (age, biological sex, accessories, face characteristics) 
![Version](https://img.shields.io/badge/version-0.3.0-brightgreen.svg)
![clean-branch-4D](https://github.com/user-attachments/assets/c16c4034-c624-41dd-8cb7-ad284425a7d4)

## Ontology Structure (Short summary) 
- __ActorState__: Snapshot of the driver at specific moments (4D-time slice) 
Each state contains exactly one first-order individual (not class) of each attribute:
* HR, HRV, RR, SpO2, Drowsiness
* Fatigue, Attention, Unresponsiveness 
* EyeState, MouthState
* Demographics 
- __Physiological Attributes__: A raw data value for the physiological parameters is used to categorize them into a threshold-classified level and then link them back to one actor states
`GCIs enforce that as: HR with value X -> classification Y`
- From physiological + behavioral data the ontology infers Fatigue/Attention/Unresponsiveness into classification individuals
- __4D-DL Time Slice Architecture__: 4D Endurant/Perdurant 
- General Concept Inclusions (GCIs) in Manchester Syntax (reduces Java Heap load ~ more stable than SWRL) 
- Semantic Web Rule Language (SWRL) finalize special cases through post-inference implications 

## Requirements
* python3 >= 3.10  
* pellet reasoner (bundled with Protege)  
* owlready2 >=0.46 
* rdflib >= 7.1.3 
* reportlab >= 4.4.5 (optional) 

## SetUp
1. Clone the repository:
```sh
git clone -b clean-branch-4D https://github.com/icsa-hua/InCabinOntology.git
```

2. Navigate to the project directory:
```sh
cd InCabinOntology
```

3. Install the package with `setup.py`:
```sh
pip3 install -e . 
```

4. To execute the ontology reasoning with the default ontology and ontology, run:
```sh
python src/scripts/test_parser.py 
```
5. (Optional) To see the results of the ontology inference in a more easy-to-understand way use Protege and open the ontologies. 
*** 
Resulting Labels are as follows: 
![Screenshot 2025-02-05 142432](https://github.com/user-attachments/assets/aea12cb3-9e27-4c3e-8098-5acb3fca3a0d)



   



