from graphviz import Digraph 
from docx import Document
from docx.shared import Inches


dot = Digraph(comment='Ontology Representation')
dot.attr(rankdir='TB', size='8,6', dpi='175', nodesep='0.', ranksep='1.5', aspect='0.8')

# dot.node('Thing', 'Thing', shape='ellipse', style='filled', fillcolor='lightgray')

dot.node('Actor', 'Actor', shape='ellipse', style='filled', fillcolor='beige')
dot.node('Accessories', 'Accessories', shape='ellipse', style='filled', fillcolor='lightblue')
dot.node('Age', 'Age', shape='ellipse', style='filled', fillcolor='lightblue')
dot.node('Demographic', 'Demographic', shape='ellipse', style='filled', fillcolor='lightblue')
dot.node('EyeState', 'EyeState', shape='ellipse', style='filled', fillcolor='lightblue')
dot.node('FaceCharacteristics', 'FaceCharacteristics', shape='ellipse', style='filled', fillcolor='lightblue')
dot.node('MouthState', 'MouthState', shape='ellipse', style='filled', fillcolor='lightblue') 
dot.node('Sex', 'Sex', shape='ellipse', style='filled', fillcolor='lightblue')

dot.node('Thresholds', 'Thresholds', shape='ellipse', style='filled', fillcolor='beige')
dot.node('HR_THR', 'HR_THR', shape='ellipse', style='filled', fillcolor='lightblue')
dot.node('HRV_THR', 'HRV_THR', shape='ellipse', style='filled', fillcolor='lightblue')
dot.node('RR_THR', 'RR_THR', shape='ellipse', style='filled', fillcolor='lightblue')
dot.node('SpO2_THR', 'SpO2_THR', shape='ellipse', style='filled', fillcolor='lightblue')
dot.node('ThresholdProfile', 'ThresholdProfile', shape='ellipse', style='filled', fillcolor='lightblue')

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

dot.node('DataContainer', 'DataContainer', shape='box', style='filled', fillcolor='beige')
dot.node('ActorState', 'ActorState', shape='ellipse', style='filled', fillcolor='beige')
dot.node('Label', 'Label', shape='ellipse', style='filled', fillcolor='lightblue')
dot.node('MetaData', 'MetaData', shape='ellipse', style='filled', fillcolor='lightblue')
dot.node('TemporalContext', 'TemporalContext', shape='ellipse', style='filled', fillcolor='lightgreen')
dot.node('WeatherCondition', 'WeatherCondition', shape='ellipse', style='filled', fillcolor='lightgreen')

dot.node('Observations', 'Observations', shape='ellipse', style='filled', fillcolor='beige')

dot.node('Attentive', 'Attentive', shape='ellipse', style='filled', fillcolor='beige')
dot.node('Inattentive', 'Inattentive', shape='ellipse', style='filled', fillcolor='beige')
dot.node('Undefined', 'Undefined', shape='ellipse', style='filled', fillcolor='beige')

dot.node('Awake', 'Awake', shape='ellipse', style='filled', fillcolor='beige')
dot.node('Sleep', 'Sleep', shape='ellipse', style='filled', fillcolor='beige')
dot.node('DrowsinessSuspected', 'DrowsinessSuspected', shape='ellipse', style='filled', fillcolor='beige')
dot.node('UndefinedState', 'UndefinedState', shape='ellipse', style='filled', fillcolor='beige')

dot.node('Responsive', 'Responsive', shape='ellipse', style='filled', fillcolor='beige')
dot.node('AtRisk', 'AtRisk', shape='ellipse', style='filled', fillcolor='beige')
dot.node('Imminent', 'Imminent', shape='ellipse', style='filled', fillcolor='beige')
dot.node('Unresponsive', 'Unresponsive', shape='ellipse', style='filled', fillcolor='beige')

dot.node('VeryLow', 'VeryLow', shape='ellipse', style='filled', fillcolor='beige')
dot.node('Low', 'Low', shape='ellipse', style='filled', fillcolor='beige')
dot.node('Moderate', 'Moderate', shape='ellipse', style='filled', fillcolor='beige')
dot.node('High', 'High', shape='ellipse', style='filled', fillcolor='beige')

dot.node('ClosedState', 'ClosedState', shape='ellipse', style='filled', fillcolor='beige')
dot.node('OpenState', 'OpenState', shape='ellipse', style='filled', fillcolor='beige')
dot.node('SlowClosure', 'SlowClosure', shape='ellipse', style='filled', fillcolor='beige')

dot.node('Closed', 'Closed', shape='ellipse', style='filled', fillcolor='beige')
dot.node('Open', 'Open', shape='ellipse', style='filled', fillcolor='beige')
dot.node('Yawning', 'Yawning', shape='ellipse', style='filled', fillcolor='beige')

# dot.edge('Actor', 'Thing', label='is a', color='grey')
# dot.edge('PhysiologicalState', 'Thing', label='is a', color='grey')
# dot.edge('DataContainer', 'Thing', label='is a', color='grey')
# dot.edge('MonitoringManagement', 'Thing', label='is a', color='grey')
# dot.edge('Observations', 'Thing', label='is a', color='grey')
# dot.edge('Thresholds', 'Thing', label='is a', color='grey')

dot.edge('Accessories', 'Actor', label='is a', color='grey')
dot.edge('Age', 'Actor', label='is a', color='grey')
dot.edge('Demographic', 'Actor', label='is a', color='grey')
dot.edge('EyeState', 'Actor', label='is a', color='grey')
dot.edge('MouthState', 'Actor', label='is a', color='grey')
dot.edge('FaceCharacteristics', 'Actor', label='is a', color='grey')
dot.edge('Sex', 'Actor', label='is a', color='grey')

dot.edge('HR_THR', 'Thresholds', label='is a', color='grey')
dot.edge('HRV_THR', 'Thresholds', label='is a', color='grey')
dot.edge('RR_THR', 'Thresholds', label='is a', color='grey')
dot.edge('SpO2_THR', 'Thresholds', label='is a', color='grey')
dot.edge('ThresholdProfile', 'Thresholds', label='is a', color='grey')

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

dot.edge('ActorState', 'DataContainer', label='is a', color='grey')
dot.edge('Label', 'DataContainer', label='is a', color='grey')
dot.edge('MetaData', 'DataContainer', label='is a', color='grey')

dot.edge('TemporalContext', 'MetaData', label='is a', color='grey')
dot.edge('WeatherCondition', 'MetaData', label='is a', color='grey')

dot.edge('Closed', 'MouthState', label='is a', color='grey')
dot.edge('Open', 'MouthState', label='is a', color='grey')
dot.edge('Yawning', 'MouthState', label='is a', color='grey')

dot.edge('ClosedState', 'EyeState', label='is a', color='grey')
dot.edge('OpenState', 'EyeState', label='is a', color='grey')
dot.edge('SlowClosure', 'EyeState', label='is a', color='grey')

dot.edge('Awake', 'Fatigue', label='is a', color='grey')
dot.edge('Sleep', 'Fatigue', label='is a', color='grey')
dot.edge('DrowsinessSuspected', 'Fatigue', label='is a', color='grey')
dot.edge('UndefinedState', 'Fatigue', label='is a', color='grey')

dot.edge('Attentive', 'Attention', label='is a', color='grey')
dot.edge('Inattentive', 'Attention', label='is a', color='grey')
dot.edge('Undefined', 'Attention', label='is a', color='grey')

dot.edge('Responsive', 'Unresponsiveness', label='is a', color='grey')
dot.edge('Unresponsive', 'Unresponsiveness', label='is a', color='grey')
dot.edge('AtRisk', 'Unresponsiveness', label='is a', color='grey')
dot.edge('Imminent', 'Unresponsiveness', label='is a', color='grey')


dot.node('AccessoriesIncludeWearables', 'AccessoriesIncludeWearables', shape='box', style='filled', fillcolor='khaki')
dot.node('ActorFromObservations', 'ActorFromObservations', shape='box', style='filled', fillcolor='khaki')
dot.node('ActorHasEyeState', 'ActorHasEyeState', shape='box', style='filled', fillcolor='khaki')
dot.node('ActorHasMouthState', 'ActorHasMouthState', shape='box', style='filled', fillcolor='khaki')
dot.node('ActorhasState', 'ActorhasState', shape='box', style='filled', fillcolor='khaki')
dot.node('ActorIsAffectedByTemp', 'ActorIsAffectedByTemp', shape='box', style='filled', fillcolor='khaki')
dot.node('ActorIsMonitoredBySensor', 'ActorIsMonitoredBySensor', shape='box', style='filled', fillcolor='khaki')
dot.node('ActorIsTargetedByLabel', 'ActorIsTargetedByLabel', shape='box', style='filled', fillcolor='khaki')
dot.node('ActorStateHasAttention', 'ActorStateHasAttention', shape='box', style='filled', fillcolor='khaki')
dot.node('ActorStateHasCharacteristics', 'ActorStateHasCharacteristics', shape='box', style='filled', fillcolor='khaki')
dot.node('ActorStateHasFatigue', 'ActorStateHasFatigue', shape='box', style='filled', fillcolor='khaki')
dot.node('ActorStateHasPhysiologicalState', 'ActorStateHasPhysiologicalState', shape='box', style='filled', fillcolor='khaki')
dot.node('ActorStateHasUnresponsiveness', 'ActorStateHasUnresponsiveness', shape='box', style='filled', fillcolor='khaki')
dot.node('AgeBelongsToGroup', 'AgeBelongsToGroup', shape='box', style='filled', fillcolor='khaki')
dot.node('appliesHRHigh', 'appliesHRHigh', shape='box', style='filled', fillcolor='khaki')


dot.node('appliesHRLow', 'appliesHRLow', shape='box', style='filled', fillcolor='khaki')
dot.node('appliesHRModerate', 'appliesHRModerate', shape='box', style='filled', fillcolor='khaki')
dot.node('appliesHRVHigh', 'appliesHRVHigh', shape='box', style='filled', fillcolor='khaki')
dot.node('appliesHRVLow', 'appliesHRVLow', shape='box', style='filled', fillcolor='khaki')
dot.node('appliesHRVModerate', 'appliesHRVModerate', shape='box', style='filled', fillcolor='khaki')
dot.node('appliesRRHigh', 'appliesRRHigh', shape='box', style='filled', fillcolor='khaki')
dot.node('appliesRRLow', 'appliesRRLow', shape='box', style='filled', fillcolor='khaki')
dot.node('appliesRRModerate', 'appliesRRModerate', shape='box', style='filled', fillcolor='khaki')
dot.node('appliesSPO2High', 'appliesSPO2High', shape='box', style='filled', fillcolor='khaki')
dot.node('appliesSPO2Low', 'appliesSPO2Low', shape='box', style='filled', fillcolor='khaki')
dot.node('appliesSPO2Moderate', 'appliesSPO2Moderate', shape='box', style='filled', fillcolor='khaki')


dot.node('AttentionIs', 'AttentionIs', shape='box', style='filled', fillcolor='khaki')
dot.node('DenotesTemperature', 'DenotesTemperature', shape='box', style='filled', fillcolor='khaki')
dot.node('DrowsinessIs', 'DrowsinessIs', shape='box', style='filled', fillcolor='khaki')
dot.node('EyeStateForActor', 'EyeStateForActor', shape='box', style='filled', fillcolor='khaki')
dot.node('EyeStateIs', 'EyeStateIs', shape='box', style='filled', fillcolor='khaki')
dot.node('FatigueIs', 'FatigueIs', shape='box', style='filled', fillcolor='khaki')
dot.node('GroupHasAge', 'GroupHasAge', shape='box', style='filled', fillcolor='khaki')

dot.node('HasThreshold', 'HasThreshold', shape='box', style='filled', fillcolor='khaki')

dot.node('HRis', 'HRis', shape='box', style='filled', fillcolor='khaki')
dot.node('HRVis', 'HRVis', shape='box', style='filled', fillcolor='khaki')

dot.node('isForAttention', 'isForAttention', shape='box', style='filled', fillcolor='khaki')
dot.node('isForDrowsiness', 'isForDrowsiness', shape='box', style='filled', fillcolor='khaki')

dot.node('isForEyeState', 'isForEyeState', shape='box', style='filled', fillcolor='khaki')
dot.node('isForFatigue', 'isForFatigue', shape='box', style='filled', fillcolor='khaki')
dot.node('isForHR', 'isForHR', shape='box', style='filled', fillcolor='khaki')
dot.node('isForHRV', 'isForHRV', shape='box', style='filled', fillcolor='khaki')

dot.node('isForMouthState', 'isForMouthState', shape='box', style='filled', fillcolor='khaki')
dot.node('isForRR', 'isForRR', shape='box', style='filled', fillcolor='khaki')
dot.node('isForSpO2', 'isForSpO2', shape='box', style='filled', fillcolor='khaki')

dot.node('isForUnresponsive', 'isForUnresponsive', shape='box', style='filled', fillcolor='khaki')
dot.node('isThreshold', 'isThreshold', shape='box', style='filled', fillcolor='khaki')
dot.node('LabelTargetsActor', 'LabelTargetsActor', shape='box', style='filled', fillcolor='khaki')


dot.node('MouthStateIs', 'MouthStateIs', shape='box', style='filled', fillcolor='khaki')

dot.node('ObservationsAreCapturedBySensor', 'ObservationsAreCapturedBySensor', shape='box', style='filled', fillcolor='khaki')
dot.node('ObsIsDividedIntoActor', 'ObsIsDividedIntoActor', shape='box', style='filled', fillcolor='khaki')
dot.node('ObsIsDividedIntoPhS', 'ObsIsDividedIntoPhS', shape='box', style='filled', fillcolor='khaki')
dot.node('PersonIsOfSex', 'PersonIsOfSex', shape='box', style='filled', fillcolor='khaki')
dot.node('PhSFromObservations', 'PhSFromObservations', shape='box', style='filled', fillcolor='khaki')

dot.node('prevState', 'prevState', shape='box', style='filled', fillcolor='khaki')
dot.node('RRis', 'RRis', shape='box', style='filled', fillcolor='khaki')

dot.node('SensorCapturesObservations', 'SensorCapturesObservations', shape='box', style='filled', fillcolor='khaki')
dot.node('SensorMonitorsActor', 'SensorMonitorsActor', shape='box', style='filled', fillcolor='khaki')
dot.node('SexBelongsToPerson', 'SexBelongsToPerson', shape='box', style='filled', fillcolor='khaki')
dot.node('SpO2is', 'SpO2is', shape='box', style='filled', fillcolor='khaki')


dot.node('StateHasThresholdProfile', 'StateHasThresholdProfile', shape='box', style='filled', fillcolor='khaki')
dot.node('StateOfActor', 'StateOfActor', shape='box', style='filled', fillcolor='khaki')
dot.node('TempAffectActor', 'TempAffectActor', shape='box', style='filled', fillcolor='khaki')
dot.node('TemperatureDenotedBy', 'TemperatureDenotedBy', shape='box', style='filled', fillcolor='khaki')
dot.node('UnresponsiveIs', 'UnresponsiveIs', shape='box', style='filled', fillcolor='khaki')
dot.node('WearablesIncludedInAccessories', 'WearablesIncludedInAccessories', shape='box', style='filled', fillcolor='khaki')





# Define edges (Relationships)

dot.edge('Accessories', 'AccessoriesIncludeWearables', label='', color='black')
dot.edge( 'AccessoriesIncludeWearables', 'Accessories', label='', color='black')

dot.edge('Accessories', 'ActorFromObservations', label='', color='black')
dot.edge('ActorFromObservations', 'Observations', label='', color='black')
dot.edge('Age', 'ActorFromObservations', label='', color='black')
dot.edge('ActorFromObservations', 'Observations', label='', color='black')
dot.edge('Demographic', 'ActorFromObservations', label='', color='black')
dot.edge('ActorFromObservations', 'Observations', label='', color='black')
dot.edge('FaceCharacteristics', 'ActorFromObservations', label='', color='black')
dot.edge('ActorFromObservations', 'Observations', label='', color='black')
dot.edge('Sex', 'ActorFromObservations', label='', color='black')
dot.edge('ActorFromObservations', 'Observations', label='', color='black')

dot.edge('ActorState', 'ActorHasEyeState', label='', color='black')
dot.edge('ActorHasEyeState', 'EyeState', label='', color='black')
dot.edge('ActorState', 'ActorHasMouthState', label='', color='black')
dot.edge('ActorHasMouthState', 'MouthState', label='', color='black')
dot.edge('Actor', 'ActorHasState', label='', color='black')
dot.edge('ActorHasState', 'ActorState', label='', color='black')
dot.edge('ActorState', 'TempAffectActor', label='', color='black')
dot.edge('TempAffectActor', 'WeatherCondition', label='', color='black')

dot.edge('ActorState', 'ActorIsMonitoredBySensor', label='', color='black')
dot.edge('ActorIsMonitoredBySensor', 'MonitoringSensor', label='', color='black')
dot.edge('ActorState', 'ActorIsTargetedByLabel', label='', color='black')
dot.edge('ActorIsTargetedByLabel', 'Label', label='', color='black')

dot.edge('ActorState', 'ActorHasAttention', label='', color='black')
dot.edge('ActorHasAttention', 'Attention', label='', color='black')
dot.edge('ActorState', 'ActorStateHasCharacteristics', label='', color='black')
dot.edge('ActorStateHasCharacteristics', 'Accessories', label='', color='black')
dot.edge('ActorState', 'ActorStateHasCharacteristics', label='', color='black')
dot.edge('ActorStateHasCharacteristics', 'Age', label='', color='black')
dot.edge('ActorState', 'ActorStateHasCharacteristics', label='', color='black')
dot.edge('ActorStateHasCharacteristics', 'Demographic', label='', color='black')
dot.edge('ActorState', 'ActorStateHasCharacteristics', label='', color='black')
dot.edge('ActorStateHasCharacteristics', 'FaceCharacteristics', label='', color='black')
dot.edge('ActorState', 'ActorStateHasCharacteristics', label='', color='black')
dot.edge('ActorStateHasCharacteristics', 'Sex', label='', color='black')

dot.edge('ActorState', 'ActorStateHasFatigue', label='', color='black')
dot.edge('ActorHasAttention', 'Fatigue', label='', color='black')

dot.edge('ActorState', 'ActorStateHasPhysiologicalState', label='', color='black')
dot.edge('ActorStateHasPhysiologicalState', 'HR', label='', color='black')
dot.edge('ActorState', 'ActorStateHasPhysiologicalState', label='', color='black')
dot.edge('ActorStateHasPhysiologicalState', 'HRV', label='', color='black')
dot.edge('ActorState', 'ActorStateHasPhysiologicalState', label='', color='black')
dot.edge('ActorStateHasPhysiologicalState', 'RR', label='', color='black')
dot.edge('ActorState', 'ActorStateHasPhysiologicalState', label='', color='black')
dot.edge('ActorStateHasPhysiologicalState', 'SPO2', label='', color='black')
dot.edge('ActorState', 'ActorStateHasPhysiologicalState', label='', color='black')
dot.edge('ActorStateHasPhysiologicalState', 'Drowsiness', label='', color='black')

dot.edge('ActorState', 'ActorStateHasUnresponsiveness', label='', color='black')
dot.edge('ActorStateHasUnresponsiveness', 'Unresponsiveness', label='', color='black')
dot.edge('Age', 'AgeBelongsToGroup', label='', color='black')
dot.edge('AgeBelongsToGroup', 'Age', label='', color='black')

dot.edge('ThresholdProfile', 'appliesHRHigh', label='', color='black')
dot.edge('appliesHRHigh', 'HR_THR', label='', color='black')
dot.edge('ThresholdProfile', 'appliesHRLow', label='', color='black')
dot.edge('appliesHRLow', 'HR_THR', label='', color='black')
dot.edge('ThresholdProfile', 'appliesHRModerate', label='', color='black')
dot.edge('appliesHRModerate', 'HR_THR', label='', color='black')

dot.edge('ThresholdProfile', 'appliesHRVHigh', label='', color='black')
dot.edge('appliesHRVHigh', 'HRV_THR', label='', color='black')
dot.edge('ThresholdProfile', 'appliesHRVLow', label='', color='black')
dot.edge('appliesHRVLow', 'HRV_THR', label='', color='black')
dot.edge('ThresholdProfile', 'appliesHRVModerate', label='', color='black')
dot.edge('appliesHRVModerate', 'HRV_THR', label='', color='black')

dot.edge('ThresholdProfile', 'appliesRRHigh', label='', color='black')
dot.edge('appliesRRHigh', 'RR_THR', label='', color='black')
dot.edge('ThresholdProfile', 'appliesRRLow', label='', color='black')
dot.edge('appliesRRLow', 'RR_THR', label='', color='black')
dot.edge('ThresholdProfile', 'appliesRRModerate', label='', color='black')
dot.edge('appliesRRModerate', 'RR_THR', label='', color='black')

dot.edge('ThresholdProfile', 'appliesSPO2High', label='', color='black')
dot.edge('appliesSPO2High', 'SpO2_THR', label='', color='black')
dot.edge('ThresholdProfile', 'appliesSPO2Low', label='', color='black')
dot.edge('appliesSPO2Low', 'SpO2_THR', label='', color='black')
dot.edge('ThresholdProfile', 'appliesSPO2Moderate', label='', color='black')
dot.edge('appliesSPO2Moderate', 'SpO2_THR', label='', color='black')

dot.edge('AttentionLevels', 'AttentionIs', label='', color='black')
dot.edge('AttentionIs', 'AttentionLevels', label='', color='black')

dot.edge('Accessories', 'DenotesTemperature', label='', color='black')
dot.edge('DenotesTemperature', 'WeatherCondition', label='', color='black')

dot.edge('Drowsiness', 'DrowsinessIs', label='', color='black')
dot.edge('DrowsinessIs', 'Drowsiness', label='', color='black')
dot.edge('EyeState', 'EyeStateForActor', label='', color='blue')
dot.edge('EyeStateForActor', 'ActorState', label='', color='blue')
dot.edge('EyeState', 'EyeStateIs', label='', color='black')
dot.edge('EyeStateIs', 'EyeState', label='', color='black')
dot.edge('Fatigue', 'FatigueIs', label='', color='black')
dot.edge('FatigueIs', 'Fatigue', label='', color='black')
dot.edge('Age', 'GroupHasAge', label='', color='blue')
dot.edge('GroupHasAge', 'Age', label='', color='blue')

dot.edge('HR', 'HasThreshold', label='', color='blue')
dot.edge('HasThreshold', 'Thresholds', label='', color='blue')
dot.edge('HRV', 'HasThreshold', label='', color='blue')
dot.edge('HasThreshold', 'Thresholds', label='', color='blue')
dot.edge('RR', 'HasThreshold', label='', color='blue')
dot.edge('HasThreshold', 'Thresholds', label='', color='blue')
dot.edge('SpO2', 'HasThreshold', label='', color='blue')
dot.edge('HasThreshold', 'Thresholds', label='', color='blue')

dot.edge('HR', 'HRis', label='', color='black')
dot.edge('HRis', 'HR', label='', color='black')
dot.edge('HRV', 'HRVis', label='', color='black')
dot.edge('HRVis', 'HRV', label='', color='black')
dot.edge('AttentionLevels', 'isForAttention', label='', color='black')
dot.edge('isForAttention', 'AttentionLevels', label='', color='black')
dot.edge('Drowsiness', 'isForDrowsiness', label='', color='blue')
dot.edge('isForDrowsiness', 'Drowsiness', label='', color='blue')
dot.edge('EyeState', 'isForEyeState', label='', color='black')
dot.edge('isForEyeState', 'EyeState', label='', color='black')
dot.edge('Fatigue', 'isForFatigue', label='', color='blue')
dot.edge('isForFatigue', 'Fatigue', label='', color='blue')
dot.edge('HR', 'isForHR', label='', color='blue')
dot.edge('isForHR', 'HR', label='', color='blue')
dot.edge('HRV', 'isForHRV', label='', color='blue')
dot.edge('isForHRV', 'HRV', label='', color='blue')

dot.edge('MouthState', 'isForMouthState', label='', color='black')
dot.edge('isForMouthState', 'MouthState', label='', color='black')
dot.edge('RR', 'isForRR', label='', color='blue')
dot.edge('isForRR', 'RR', label='', color='blue')
dot.edge('SpO2', 'isForSpO2', label='', color='blue')
dot.edge('isForSpO2', 'SpO2', label='', color='blue')
dot.edge('Unresponsiveness', 'isForUnresponsive', label='', color='black')
dot.edge('isForUnresponsive', 'Unresponsiveness', label='', color='black')
dot.edge('Thresholds', 'isThreshold', label='', color='blue')
dot.edge('isThreshold', 'HR', label='', color='blue')
dot.edge('Thresholds', 'isThreshold', label='', color='blue')
dot.edge('isThreshold', 'HRV', label='', color='blue')
dot.edge('Thresholds', 'isThreshold', label='', color='blue')
dot.edge('isThreshold', 'RR', label='', color='blue')
dot.edge('Thresholds', 'isThreshold', label='', color='blue')
dot.edge('isThreshold', 'SpO2', label='', color='blue')
dot.edge('Label', 'LabelTargetsActor', label='', color='blue')
dot.edge('LabelTargetsActor', 'Actor', label='', color='blue')
dot.edge('MouthState', 'MouthStateIs', label='', color='black')
dot.edge('MouthStateIs', 'MouthState', label='', color='black')
dot.edge('Observations', 'ObservationsAreCapturedBySensor', label='', color='black')
dot.edge('ObservationsAreCapturedBySensor', 'MonitoringSensor', label='', color='black')
dot.edge('Observations', 'ObsIsDividedIntoActor', label='', color='blue')
dot.edge('ObsIsDividedIntoActor', 'Accessories', label='', color='blue')
dot.edge('Observations', 'ObsIsDividedIntoActor', label='', color='blue')
dot.edge('ObsIsDividedIntoActor', 'Age', label='', color='blue')
dot.edge('Observations', 'ObsIsDividedIntoActor', label='', color='blue')
dot.edge('ObsIsDividedIntoActor', 'Demographic', label='', color='blue')
dot.edge('Observations', 'ObsIsDividedIntoActor', label='', color='blue')
dot.edge('ObsIsDividedIntoActor', 'FaceCharacteristics', label='', color='blue')
dot.edge('Observations', 'ObsIsDividedIntoActor', label='', color='blue')
dot.edge('ObsIsDividedIntoActor', 'Sex', label='', color='blue')

dot.edge('Observations', 'ObsIsDividedIntoPhS', label='', color='black')
dot.edge('ObsIsDividedIntoPhS', 'HR', label='', color='black')
dot.edge('Observations', 'ObsIsDividedIntoPhS', label='', color='black')
dot.edge('ObsIsDividedIntoPhS', 'HRV', label='', color='black')
dot.edge('Observations', 'ObsIsDividedIntoPhS', label='', color='black')
dot.edge('ObsIsDividedIntoPhS', 'RR', label='', color='black')
dot.edge('Observations', 'ObsIsDividedIntoPhS', label='', color='black')
dot.edge('ObsIsDividedIntoPhS', 'SpO2', label='', color='black')
dot.edge('Sex', 'PersonIsOfSex', label='', color='black')
dot.edge('PersonIsOfSex', 'Sex', label='', color='black')


dot.edge('HR', 'PhSFromObservations', label='', color='black')
dot.edge('PhSFromObservations', 'Observations', label='', color='black')
dot.edge('HRV', 'PhSFromObservations', label='', color='black')
dot.edge('PhSFromObservations', 'Observations', label='', color='black')
dot.edge('RR', 'PhSFromObservations', label='', color='black')
dot.edge('PhSFromObservations', 'Observations', label='', color='black')
dot.edge('SpO2', 'PhSFromObservations', label='', color='black')
dot.edge('PhSFromObservations', 'Observations', label='', color='black')

dot.edge('ActorState', 'prevState', label='', color='black')
dot.edge('prevState', 'ActorState', label='', color='black')
dot.edge('RR', 'RRis', label='', color='black')
dot.edge('RRis', 'RR', label='', color='black')
dot.edge('MonitoringSensor', 'SensorCapturesObservations', label='', color='blue')
dot.edge('SensorCapturesObservations', 'Observations', label='', color='blue')
dot.edge('MonitoringSensor', 'SensorMonitorsActor', label='', color='blue')
dot.edge('SensorMonitorsActor', 'ActorState', label='', color='blue')

dot.edge('Sex', 'SexBelongsToPerson', label='', color='blue')
dot.edge('SexBelongsToPerson', 'Sex', label='', color='blue')
dot.edge('SpO2', 'SpO2is', label='', color='black')
dot.edge('SpO2is', 'SpO2', label='', color='black')

dot.edge('ActorState', 'StateHasThresholdProfile', label='', color='black')
dot.edge('StateHasThresholdProfile', 'ThresholdProfile', label='', color='black')

dot.edge('ActorState', 'StateOfActor', label='', color='black')
dot.edge('StateOfActor', 'Actor', label='', color='black')
dot.edge('WeatherCondition', 'TempAffectActor', label='', color='black')
dot.edge('TempAffectActor', 'ActorState', label='', color='black')
dot.edge('WeatherCondition', 'TemperatureDenotedBy', label='', color='black')
dot.edge('TemperatureDenotedBy', 'Accessories', label='', color='black')
dot.edge('Unresponsiveness', 'UnresponsiveIs', label='', color='black')
dot.edge('UnresponsiveIs', 'Unresponsiveness', label='', color='black')

dot.edge('Accessories', 'WearablesIncludedInAccessories', label='', color='black')
dot.edge('WearablesIncludedInAccessories', 'Accessories', label='', color='black')


# Render and display
dot.render('assets/ontology_graph', format='png', view=True)

doc = Document()
doc.add_picture("assets/ontology_graph.png", width=Inches(5))
doc.save("assets/ontology.docx")












