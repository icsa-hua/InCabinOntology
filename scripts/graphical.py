from graphviz import Digraph 

dot = Digraph(comment='Ontology Representation')
dot.attr(rankdir='TB', size='10', dpi='175', nodesep='0.', ranksep='1.5', aspect='0.8')

dot.node('Thing', 'Thing', shape='ellipse', style='filled', fillcolor='lightgray')

dot.node('Actor', 'Actor', shape='ellipse', style='filled', fillcolor='beige')
dot.node('Accessories', 'Accessories', shape='ellipse', style='filled', fillcolor='lightblue')
dot.node('Age', 'Age', shape='ellipse', style='filled', fillcolor='lightblue')
dot.node('Demographic', 'Demographic', shape='ellipse', style='filled', fillcolor='lightblue')
dot.node('EyeClosure', 'EyeClosure', shape='ellipse', style='filled', fillcolor='lightblue')
dot.node('FaceCharacteristics', 'FaceCharacteristics', shape='ellipse', style='filled', fillcolor='lightblue')
dot.node('Sex', 'Sex', shape='ellipse', style='filled', fillcolor='lightblue')

dot.node('Thresholds', 'Thresholds', shape='ellipse', style='filled', fillcolor='beige')
dot.node('HR_THR', 'HR_THR', shape='ellipse', style='filled', fillcolor='lightblue')
dot.node('HRV_THR', 'HRV_THR', shape='ellipse', style='filled', fillcolor='lightblue')
dot.node('RR_THR', 'RR_THR', shape='ellipse', style='filled', fillcolor='lightblue')
dot.node('SpO2_THR', 'SpO2_THR', shape='ellipse', style='filled', fillcolor='lightblue')

dot.node('PhysiologicalState', 'PhysiologicalState', shape='ellipse', style='filled', fillcolor='beige')
dot.node('AttentionLevels', 'AttentionLevels', shape='ellipse', style='filled', fillcolor='lightblue')
dot.node('Drowsiness', 'Drowsiness', shape='ellipse', style='filled', fillcolor='lightblue')
dot.node('Fatigue', 'Fatigue', shape='ellipse', style='filled', fillcolor='lightblue')
dot.node('HR', 'HR', shape='ellipse', style='filled', fillcolor='lightblue')
dot.node('HRV', 'HRV', shape='ellipse', style='filled', fillcolor='lightblue')
dot.node('RR', 'RR', shape='ellipse', style='filled', fillcolor='lightblue')
dot.node('SpO2', 'SpO2', shape='ellipse', style='filled', fillcolor='lightblue')
dot.node('Unresponsiveness', 'Unresponsiveness', shape='ellipse', style='filled', fillcolor='lightblue')

dot.node('MonitoringManagement', 'MonitoringManagement', shape='ellipse', style='filled', fillcolor='beige')
dot.node('DataAnalysisUnit', 'DataAnalysisUnit', shape='ellipse', style='filled', fillcolor='lightblue')
dot.node('MonitoringSensor', 'MonitoringSensor', shape='ellipse', style='filled', fillcolor='lightblue')

dot.node('DataContainer', 'DataContainer', shape='ellipse', style='filled', fillcolor='beige')
dot.node('Label', 'Label', shape='ellipse', style='filled', fillcolor='lightblue')
dot.node('MetaData', 'MetaData', shape='ellipse', style='filled', fillcolor='lightblue')

dot.node('Observations', 'Observations', shape='ellipse', style='filled', fillcolor='beige')

dot.edge('Actor', 'Thing', label='is a', color='grey')
dot.edge('PhysiologicalState', 'Thing', label='is a', color='grey')
dot.edge('DataContainer', 'Thing', label='is a', color='grey')
dot.edge('MonitoringManagement', 'Thing', label='is a', color='grey')
dot.edge('Observations', 'Thing', label='is a', color='grey')
dot.edge('Thresholds', 'Thing', label='is a', color='grey')

dot.edge('Accessories', 'Actor', label='is a', color='grey')
dot.edge('Age', 'Actor', label='is a', color='grey')
dot.edge('Demographic', 'Actor', label='is a', color='grey')
dot.edge('EyeClosure', 'Actor', label='is a', color='grey')
dot.edge('FaceCharacteristics', 'Actor', label='is a', color='grey')
dot.edge('Sex', 'Actor', label='is a', color='grey')

dot.edge('HR_THR', 'Thresholds', label='is a', color='grey')
dot.edge('HRV_THR', 'Thresholds', label='is a', color='grey')
dot.edge('RR_THR', 'Thresholds', label='is a', color='grey')
dot.edge('SpO2_THR', 'Thresholds', label='is a', color='grey')

dot.edge('AttentionLevels', 'PhysiologicalState', label='is a', color='grey')
dot.edge('Drowsiness', 'PhysiologicalState', label='is a', color='grey')
dot.edge('Fatigue', 'PhysiologicalState', label='is a', color='grey')
dot.edge('HR', 'PhysiologicalState', label='is a', color='grey')
dot.edge('HRV', 'PhysiologicalState', label='is a', color='grey')
dot.edge('RR', 'PhysiologicalState', label='is a', color='grey')
dot.edge('SpO2', 'PhysiologicalState', label='is a', color='grey')
dot.edge('Unresponsiveness', 'PhysiologicalState', label='is a', color='grey')

dot.edge('DataAnalysisUnit', 'MonitoringManagement', label='is a', color='grey')
dot.edge('MonitoringSensor', 'MonitoringManagement', label='is a', color='grey')

dot.edge('Label', 'DataContainer', label='is a', color='grey')
dot.edge('MetaData', 'DataContainer', label='is a', color='grey')

dot.node('ActorFromObservations', 'ActorFromObservations', shape='box', style='filled', fillcolor='khaki')
dot.node('ActorHasCharacteristics', 'ActorHasCharacteristics', shape='box', style='filled', fillcolor='khaki')
dot.node('ActorHasEyeState', 'ActorHasEyeState', shape='box', style='filled', fillcolor='khaki')
dot.node('ActorHasPhysiologicalState', 'ActorHasPhysiologicalState', shape='box', style='filled', fillcolor='khaki')
dot.node('ActorIsMonitoredBySensor', 'ActorIsMonitoredBySensor', shape='box', style='filled', fillcolor='khaki')
dot.node('ActorIsTargetedByLabel', 'ActorIsTargetedByLabel', shape='box', style='filled', fillcolor='khaki')
dot.node('AgeBelongsToGroup', 'AgeBelongsToGroup', shape='box', style='filled', fillcolor='khaki')
dot.node('CharacteristicsDescribeActor', 'CharacteristicsDescribeActor', shape='box', style='filled', fillcolor='khaki')
dot.node('DrowsinessIs', 'DrowsinessIs', shape='box', style='filled', fillcolor='khaki')
dot.node('EyeStateForActor', 'EyeStateForActor', shape='box', style='filled', fillcolor='khaki')
dot.node('FatigueIs', 'FatigueIs', shape='box', style='filled', fillcolor='khaki')
dot.node('GroupHasAge', 'GroupHasAge', shape='box', style='filled', fillcolor='khaki')
dot.node('HasThreshold', 'HasThreshold', shape='box', style='filled', fillcolor='khaki')
dot.node('HRis', 'HRis', shape='box', style='filled', fillcolor='khaki')
dot.node('HRVis', 'HRVis', shape='box', style='filled', fillcolor='khaki')
dot.node('isForDrowsiness', 'isForDrowsiness', shape='box', style='filled', fillcolor='khaki')
dot.node('isForFatigue', 'isForFatigue', shape='box', style='filled', fillcolor='khaki')
dot.node('isForHR', 'isForHR', shape='box', style='filled', fillcolor='khaki')
dot.node('isForHRV', 'isForHRV', shape='box', style='filled', fillcolor='khaki')
dot.node('isForRR', 'isForRR', shape='box', style='filled', fillcolor='khaki')
dot.node('isForSpO2', 'isForSpO2', shape='box', style='filled', fillcolor='khaki')
dot.node('isThreshold', 'isThreshold', shape='box', style='filled', fillcolor='khaki')
dot.node('LabelTargetsActor', 'LabelTargetsActor', shape='box', style='filled', fillcolor='khaki')
dot.node('ObservationsAreCapturedBySensor', 'ObservationsAreCapturedBySensor', shape='box', style='filled', fillcolor='khaki')
dot.node('ObservationsHasPhysiologicalData', 'ObservationsHasPhysiologicalData', shape='box', style='filled', fillcolor='khaki')
dot.node('ObsIsDividedIntoActor', 'ObsIsDividedIntoActor', shape='box', style='filled', fillcolor='khaki')
dot.node('ObsIsDividedIntoPhS', 'ObsIsDividedIntoPhS', shape='box', style='filled', fillcolor='khaki')
dot.node('PersonIsOfSex', 'PersonIsOfSex', shape='box', style='filled', fillcolor='khaki')
dot.node('PhSFromObservations', 'PhSFromObservations', shape='box', style='filled', fillcolor='khaki')
dot.node('PhysiologicalStateDescribesActor', 'PhysiologicalStateDescribesActor', shape='box', style='filled', fillcolor='khaki')
dot.node('RRis', 'RRis', shape='box', style='filled', fillcolor='khaki')
dot.node('SensorCapturesObservations', 'SensorCapturesObservations', shape='box', style='filled', fillcolor='khaki')
dot.node('SensorMonitorsActor', 'SensorMonitorsActor', shape='box', style='filled', fillcolor='khaki')
dot.node('SexBelongsToPerson', 'SexBelongsToPerson', shape='box', style='filled', fillcolor='khaki')
dot.node('SpO2is', 'SpO2is', shape='box', style='filled', fillcolor='khaki')


# Define edges (Relationships)
dot.edge('Actor', 'ActorFromObservations', label='', color='black')
dot.edge('ActorFromObservations', 'Observations', label='', color='black')

dot.edge('Observations', 'ObsIsDividedIntoActor', label='', color='blue')
dot.edge('ObsIsDividedIntoActor', 'Actor', label='', color='blue')

dot.edge('Actor', 'ActorHasCharacteristics', label='', color='black')
dot.edge('ActorHasCharacteristics', 'Actor', label='', color='black')

dot.edge('Actor', 'CharacteristicsDescribeActor', label='', color='blue')
dot.edge('CharacteristicsDescribeActor', 'Actor', label='', color='blue')

dot.edge('Actor', 'ActorHasEyeState', label='', color='black')
dot.edge('ActorHasEyeState', 'EyeState', label='', color='black')

dot.edge('EyeState', 'EyeStateForActor', label='', color='blue')
dot.edge('EyeStateForActor', 'Actor', label='', color='blue')

dot.edge('Actor', 'ActorHasPhysiologicalState', label='', color='black')
dot.edge('ActorHasPhysiologicalState', 'PhysiologicalState', label='', color='black')

dot.edge('PhysiologicalState', 'PhysiologicalStateDescribesActor', label='', color='blue')
dot.edge('PhysiologicalStateDescribesActor', 'Actor', label='', color='blue')

dot.edge('Actor', 'ActorIsMonitoredBySensor', label='', color='black')
dot.edge('ActorIsMonitoredBySensor', 'MonitoringSensor', label='', color='black')

dot.edge('MonitoringSensor', 'SensorMonitorsActor', label='', color='blue')
dot.edge('SensorMonitorsActor', 'Actor', label='', color='blue')

dot.edge('Actor', 'ActorIsTargetedByLabel', label='', color='black')
dot.edge('ActorIsTargetedByLabel', 'Label', label='', color='black')

dot.edge('Label', 'LabelTargetsActor', label='', color='blue')
dot.edge('LabelTargetsActor', 'Actor', label='', color='blue')

dot.edge('Age', 'AgeBelongsToGroup', label='', color='black')
dot.edge('AgeBelongsToGroup', 'Age', label='', color='black')

dot.edge('Age', 'GroupHasAge', label='', color='blue')
dot.edge('GroupHasAge', 'Age', label='', color='blue')

dot.edge('Drowsiness', 'DrowsinessIs', label='', color='black')
dot.edge('DrowsinessIs', 'Drowsiness', label='', color='black')

dot.edge('Drowsiness', 'isForDrowsiness', label='', color='blue')
dot.edge('isForDrowsiness', 'Drowsiness', label='', color='blue')

dot.edge('Fatigue', 'FatigueIs', label='', color='black')
dot.edge('FatigueIs', 'Fatigue', label='', color='black')

dot.edge('Fatigue', 'isForFatigue', label='', color='blue')
dot.edge('isForFatigue', 'Fatigue', label='', color='blue')

dot.edge('PhysiologicalState', 'HasThreshold', label='', color='black')
dot.edge('HasThreshold', 'Thresholds', label='', color='black')

dot.edge('Thresholds', 'isThreshold', label='', color='blue')
dot.edge('isThreshold', 'PhysiologicalState', label='', color='blue')

dot.edge('HR', 'HRis', label='', color='black')
dot.edge('HRis', 'HR', label='', color='black')

dot.edge('HR', 'isForHR', label='', color='blue')
dot.edge('isForHR', 'HR', label='', color='blue')

dot.edge('HRV', 'HRVis', label='', color='black')
dot.edge('HRVis', 'HRV', label='', color='black')

dot.edge('HRV', 'isForHRV', label='', color='blue')
dot.edge('isForHRV', 'HRV', label='', color='blue')

dot.edge('RR', 'RRis', label='', color='black')
dot.edge('RRis', 'RR', label='', color='black')

dot.edge('RR', 'isForRR', label='', color='blue')
dot.edge('isForRR', 'RR', label='', color='blue')

dot.edge('SpO2', 'SpO2is', label='', color='black')
dot.edge('SpO2is', 'SpO2', label='', color='black')

dot.edge('SpO2', 'isForSpO2', label='', color='blue')
dot.edge('isForSpO2', 'SpO2', label='', color='blue')

dot.edge('Observations', 'ObservationsAreCapturedBySensor', label='', color='black')
dot.edge('ObservationsAreCapturedBySensor', 'MonitoringSensor', label='', color='black')

dot.edge('MonitoringSensor', 'SensorCapturesObservations', label='', color='blue')
dot.edge('SensorCapturesObservations', 'Observations', label='', color='blue')

dot.edge('Observations', 'ObservationsHasPhysiologicalData', label='', color='black')
dot.edge('ObservationsHasPhysiologicalData', 'PhysiologicalState', label='', color='black')

dot.edge('PhysiologicalState', 'PhysiologicalStateDescribesActor', label='', color='blue')
dot.edge('PhysiologicalStateDescribesActor', 'Observations', label='', color='blue')

dot.edge('Observations', 'ObsIsDividedIntoPhS', label='', color='black')
dot.edge('ObsIsDividedIntoPhS', 'PhysiologicalState', label='', color='black')

dot.edge('PhysiologicalState', 'PhSFromObservations', label='', color='blue')
dot.edge('PhSFromObservations', 'Observations', label='', color='blue')

dot.edge('Sex', 'PersonIsOfSex', label='', color='black')
dot.edge('PersonIsOfSex', 'Sex', label='', color='black')

dot.edge('Sex', 'SexBelongsToPerson', label='', color='blue')
dot.edge('SexBelongsToPerson', 'Sex', label='', color='blue')

# Render and display
dot.render('ontology_graph', format='png', view=True)

















