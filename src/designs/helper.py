from owlready2 import * 
from src.tools.common import * 
from src.tools.appraisal import StepContext
from src.tools.logger import get_logger 

logger = get_logger("aiq_onto")

def single_attribute_pattern_classes(onto): 

    with onto:

        # HR DIFFERENT CATEGORIES 
        class ActorState_Very_Low_HR(onto.ActorState):
            equivalent_to = [(onto.ActorState
                                & onto.ActorStateHasPhysiologicalState.some( onto.HR & onto.HRis.value(onto.very_low_hr_instance))
                              )]

        class ActorState_Moderate_HR(onto.ActorState):
            equivalent_to = [(onto.ActorState
                                & onto.ActorStateHasPhysiologicalState.some( onto.HR & onto.HRis.value(onto.moderate_hr_instance))
                              )]   

        class ActorState_Low_HR(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & onto.ActorStateHasPhysiologicalState.some( onto.HR  & onto.HRis.value(onto.low_hr_instance))
                )]

        class ActorState_High_HR(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & onto.ActorStateHasPhysiologicalState.some( onto.HR  & onto.HRis.value(onto.high_hr_instance))
                )]
        
        # HRV DIFFERENT CATEGORIES
        class ActorState_High_HRV(onto.ActorState):
            equivalent_to = [(onto.ActorState
                                & onto.ActorStateHasPhysiologicalState.some( onto.HRV & onto.HRVis.value(onto.high_hrv_instance))
                              )]   
        class ActorState_Moderate_HRV(onto.ActorState):
            equivalent_to = [(onto.ActorState
                                & onto.ActorStateHasPhysiologicalState.some( onto.HRV & onto.HRVis.value(onto.moderate_hrv_instance))
                              )]  

        class ActorState_Low_HRV(onto.ActorState):
            equivalent_to = [(onto.ActorState
                                & onto.ActorStateHasPhysiologicalState.some( onto.HRV & onto.HRVis.value(onto.low_hrv_instance))
                              )]  

        class ActorState_Very_Low_HRV(onto.ActorState):
            equivalent_to = [(onto.ActorState
                                & onto.ActorStateHasPhysiologicalState.some( onto.HRV & onto.HRVis.value(onto.very_low_hrv_instance))
                              )]  

        # RR DIFFERENT CATEGORIES
        class ActorState_High_RR(onto.ActorState):
            equivalent_to = [(onto.ActorState
                                & onto.ActorStateHasPhysiologicalState.some( onto.RR & onto.RRis.value(onto.high_rr_instance))
                              )]   

        class ActorState_Moderate_RR(onto.ActorState):
            equivalent_to = [(onto.ActorState
                                & onto.ActorStateHasPhysiologicalState.some( onto.RR & onto.RRis.value(onto.moderate_rr_instance))
                              )]   

        class ActorState_Low_RR(onto.ActorState):
            equivalent_to = [(onto.ActorState
                                & onto.ActorStateHasPhysiologicalState.some( onto.RR & onto.RRis.value(onto.low_rr_instance))
                              )]   

        class ActorState_Very_Low_RR(onto.ActorState):
            equivalent_to = [(onto.ActorState
                                & onto.ActorStateHasPhysiologicalState.some( onto.RR & onto.RRis.value(onto.very_low_rr_instance))
                              )]   

        # SpO2 DIFFERENT CATEGORIES
        class ActorState_Normal_SpO2(onto.ActorState):
            equivalent_to = [(onto.ActorState
                                & onto.ActorStateHasPhysiologicalState.some( onto.SpO2 & onto.SpO2is.value(onto.normal_spo2_instance))
                              )]   

        class ActorState_Low_SpO2(onto.ActorState):
            equivalent_to = [(onto.ActorState
                                & onto.ActorStateHasPhysiologicalState.some( onto.SpO2 & onto.SpO2is.value(onto.low_spo2_instance))
                              )]   

        class ActorState_Critical_SpO2(onto.ActorState):
            equivalent_to = [(onto.ActorState
                                & onto.ActorStateHasPhysiologicalState.some( onto.SpO2 & onto.SpO2is.value(onto.critical_spo2_instance))
                              )]   

        # Drowsiness DIFFERENT CATEGORIES 
        class ActorState_Drowsiness_Level_3(onto.ActorState):
            equivalent_to = [(onto.ActorState
                                & onto.ActorStateHasPhysiologicalState.some( onto.Drowsiness & onto.DrowsinessIs.value(onto.level_3_kss_instance))
                              )]   

        class ActorState_Drowsiness_Level_5(onto.ActorState):
            equivalent_to = [(onto.ActorState
                                & onto.ActorStateHasPhysiologicalState.some( onto.Drowsiness & onto.DrowsinessIs.value(onto.level_5_kss_instance))
                              )]  

        class ActorState_Drowsiness_Level_7(onto.ActorState):
            equivalent_to = [(onto.ActorState
                                & onto.ActorStateHasPhysiologicalState.some( onto.Drowsiness & onto.DrowsinessIs.value(onto.level_7_kss_instance))
                              )]  

        class ActorState_Drowsiness_Level_9(onto.ActorState):
            equivalent_to = [(onto.ActorState
                                & onto.ActorStateHasPhysiologicalState.some( onto.Drowsiness & onto.DrowsinessIs.value(onto.level_9_kss_instance))
            )] 

        # unified signature 1 
        class ActorState_HighHR_LowHRV_HighRR_NormalSpO2_LVL3(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_High_HR
                & ActorState_Low_HRV
                & ActorState_High_RR 
                & ActorState_Normal_SpO2
                & ActorState_Drowsiness_Level_3 
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.drowsinesssuspected_instance), 
                    onto.ActorStateHasAttention.value(onto.attentive_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.undefined_atrisk_instance)
                ]
        # unified signature 2 
        class ActorState_HighHR_LowHRV_VeryLowRR_NormalSpO2_LVL3(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_High_HR
                & ActorState_Low_HRV
                & ActorState_Very_Low_RR 
                & ActorState_Normal_SpO2
                & ActorState_Drowsiness_Level_3 
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.drowsinesssuspected_instance), 
                    onto.ActorStateHasAttention.value(onto.attentive_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.responsive_instance)
                ]
        # unified signature 3 
        class ActorState_HighHR_VeryLowHRV_HighRR_LowSpO2_LVL3(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_High_HR
                & ActorState_Very_Low_HRV
                & ActorState_High_RR 
                & ActorState_Low_SpO2
                & ActorState_Drowsiness_Level_3 
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.undefinedstate_instance), 
                    onto.ActorStateHasAttention.value(onto.undefined_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.imminent_instance)
                ]

        # unified signature 4  
        class ActorState_HighHR_VeryLowHRV_HighRR_NormalSpO2_LVL3(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_High_HR
                & ActorState_Very_Low_HRV
                & ActorState_High_RR 
                & ActorState_Normal_SpO2
                & ActorState_Drowsiness_Level_3 
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.drowsinesssuspected_instance), 
                    onto.ActorStateHasAttention.value(onto.attentive_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.undefined_atrisk_instance)
                ]

        # unified signature 5
        class ActorState_HighHR_VeryLowHRV_VeryLowRR_CriticalSpO2_LVL3(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_High_HR
                & ActorState_Very_Low_HRV
                & ActorState_Very_Low_RR 
                & ActorState_Critical_SpO2
                & ActorState_Drowsiness_Level_3 
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.undefinedstate_instance), 
                    onto.ActorStateHasAttention.value(onto.undefined_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.unresponsive_instance)
                ]

        # unified signature 6 
        class ActorState_HighHR_VeryLowHRV_VeryLowRR_LowSpO2_LVL3(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_High_HR
                & ActorState_Very_Low_HRV
                & ActorState_Very_Low_RR 
                & ActorState_Low_SpO2
                & ActorState_Drowsiness_Level_3 
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.undefinedstate_instance), 
                    onto.ActorStateHasAttention.value(onto.undefined_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.imminent_instance)
                ]

        # unified signature 7 
        class ActorState_HighHR_VeryLowHRV_VeryLowRR_NormalSpO2_LVL3(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_High_HR
                & ActorState_Very_Low_HRV
                & ActorState_Very_Low_RR 
                & ActorState_Normal_SpO2
                & ActorState_Drowsiness_Level_3 
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.drowsinesssuspected_instance), 
                    onto.ActorStateHasAttention.value(onto.attentive_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.undefined_atrisk_instance)
                ]


        # unified signature 8 
        class ActorState_LowHR_HighHRV_LowRR_LowSpO2_LVL3(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_Low_HR
                & ActorState_High_HRV
                & ActorState_Low_RR 
                & ActorState_Low_SpO2
                & ActorState_Drowsiness_Level_3 
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.undefinedstate_instance), 
                    onto.ActorStateHasAttention.value(onto.attentive_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.undefined_atrisk_instance)
                ]

        # unified signature 9
        class ActorState_LowHR_HighHRV_LowRR_NormalSpO2_LVL3(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_Low_HR
                & ActorState_High_HRV
                & ActorState_Low_RR 
                & ActorState_Normal_SpO2
                & ActorState_Drowsiness_Level_3 
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.awake_instance), 
                    onto.ActorStateHasAttention.value(onto.undefined_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.responsive_instance)
                ]


        # unified signature 10 
        class ActorState_LowHR_HighHRV_ModerateRR_NormalSpO2_LVL3(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_Low_HR
                & ActorState_High_HRV
                & ActorState_Moderate_RR 
                & ActorState_Normal_SpO2
                & ActorState_Drowsiness_Level_3 
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.awake_instance), 
                    onto.ActorStateHasAttention.value(onto.undefined_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.responsive_instance)
                ]

        # unified signature 11
        class ActorState_LowHR_LowHRV_HighRR_LowSpO2_LVL3(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_Low_HR
                & ActorState_Low_HRV
                & ActorState_High_RR 
                & ActorState_Low_SpO2
                & ActorState_Drowsiness_Level_3 
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.undefinedstate_instance), 
                    onto.ActorStateHasAttention.value(onto.undefined_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.undefined_atrisk_instance)
                ]
        
        # unified signature 12  
        class ActorState_LowHR_LowHRV_HighRR_NormalSpO2_LVL3(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_Low_HR
                & ActorState_Low_HRV
                & ActorState_High_RR 
                & ActorState_Normal_SpO2
                & ActorState_Drowsiness_Level_3 
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.undefinedstate_instance), 
                    onto.ActorStateHasAttention.value(onto.attentive_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.undefined_atrisk_instance)
                ]
        # unified signature 13  
        class ActorState_LowHR_LowHRV_LowRR_LowSpO2_LVL3(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_Low_HR
                & ActorState_Low_HRV
                & ActorState_Low_RR 
                & ActorState_Low_SpO2
                & ActorState_Drowsiness_Level_3 
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.undefinedstate_instance), 
                    onto.ActorStateHasAttention.value(onto.undefined_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.undefined_atrisk_instance)
                ]

        # unified signature 14  
        class ActorState_LowHR_LowHRV_LowRR_NormalSpO2_LVL3(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_Low_HR
                & ActorState_Low_HRV
                & ActorState_Low_RR 
                & ActorState_Normal_SpO2
                & ActorState_Drowsiness_Level_3 
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.undefinedstate_instance), 
                    onto.ActorStateHasAttention.value(onto.attentive_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.undefined_atrisk_instance)
                ]

        # unified signature 15
        class ActorState_LowHR_LowHRV_VeryLowRR_NormalSpO2_LVL3(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_Low_HR
                & ActorState_Low_HRV
                & ActorState_Very_Low_RR 
                & ActorState_Normal_SpO2
                & ActorState_Drowsiness_Level_3 
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.undefinedstate_instance), 
                    onto.ActorStateHasAttention.value(onto.attentive_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.undefined_atrisk_instance)
                ]

        # unified signature 16 
        class ActorState_LowHR_ModerateHRV_LowRR_LowSpO2_LVL3(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_Low_HR
                & ActorState_Moderate_HRV
                & ActorState_Low_RR 
                & ActorState_Low_SpO2
                & ActorState_Drowsiness_Level_3 
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.undefinedstate_instance), 
                    onto.ActorStateHasAttention.value(onto.attentive_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.undefined_atrisk_instance)
                ]

        # unified signature 17 
        class ActorState_LowHR_ModerateHRV_LowRR_NormalSpO2_LVL3(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_Low_HR
                & ActorState_Moderate_HRV
                & ActorState_Low_RR 
                & ActorState_Normal_SpO2
                & ActorState_Drowsiness_Level_3 
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.awake_instance), 
                    onto.ActorStateHasAttention.value(onto.undefined_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.responsive_instance)
                ]


        # unified signature 18 
        class ActorState_LowHR_ModerateHRV_ModerateRR_LowSpO2_LVL3(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_Low_HR
                & ActorState_Moderate_HRV
                & ActorState_Moderate_RR 
                & ActorState_Low_SpO2
                & ActorState_Drowsiness_Level_3 
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.undefinedstate_instance), 
                    onto.ActorStateHasAttention.value(onto.attentive_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.undefined_atrisk_instance)
                ]
                
        # unified signature 018    
        class ActorState_LowHR_ModerateHRV_ModerateRR_NormalSpO2_LVL3(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_Low_HR
                & ActorState_Moderate_HRV
                & ActorState_Moderate_RR 
                & ActorState_Normal_SpO2
                & ActorState_Drowsiness_Level_3 
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.drowsinesssuspected_instance), 
                    onto.ActorStateHasAttention.value(onto.attentive_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.undefined_atrisk_instance)
                ]

        # unified signature 19
        class ActorState_LowHR_VeryLowHRV_HighRR_NormalSpO2_LVL3(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_Low_HR
                & ActorState_Very_Low_HRV
                & ActorState_High_RR 
                & ActorState_Normal_SpO2
                & ActorState_Drowsiness_Level_3 
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.undefinedstate_instance), 
                    onto.ActorStateHasAttention.value(onto.attentive_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.undefined_atrisk_instance)
                ]


        # unified signature 20 
        class ActorState_LowHR_VeryLowHRV_LowRR_NormalSpO2_LVL3(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_Low_HR
                & ActorState_Very_Low_HRV
                & ActorState_Low_RR 
                & ActorState_Normal_SpO2
                & ActorState_Drowsiness_Level_3 
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.undefinedstate_instance), 
                    onto.ActorStateHasAttention.value(onto.attentive_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.undefined_atrisk_instance)
                ]


        # unified signature 21
        class ActorState_LowHR_VeryLowHRV_VeryLowhRR_NormalSpO2_LVL3(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_Low_HR
                & ActorState_Very_Low_HRV
                & ActorState_Very_Low_RR 
                & ActorState_Normal_SpO2
                & ActorState_Drowsiness_Level_3 
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.undefinedstate_instance), 
                    onto.ActorStateHasAttention.value(onto.attentive_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.undefined_atrisk_instance)
                ]
        
        # unified signature 22  
        class ActorState_ModerateHR_HighHRV_LowRR_LowSpO2_LVL3(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_Moderate_HR
                & ActorState_High_HRV
                & ActorState_Low_RR 
                & ActorState_Low_SpO2
                & ActorState_Drowsiness_Level_3 
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.undefinedstate_instance), 
                    onto.ActorStateHasAttention.value(onto.attentive_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.undefined_atrisk_instance)
                ]
        # unified signature 23  
        class ActorState_ModerateHR_HighHRV_LowRR_NormalSpO2_LVL3(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_Moderate_HR
                & ActorState_High_HRV
                & ActorState_Low_RR 
                & ActorState_Normal_SpO2
                & ActorState_Drowsiness_Level_3 
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.undefinedstate_instance), 
                    onto.ActorStateHasAttention.value(onto.undefined_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.undefined_atrisk_instance)
                ]

        # unified signature 24  
        class ActorState_ModerateHR_HighHRV_ModerateRR_LowSpO2_LVL3(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_Moderate_HR
                & ActorState_High_HRV
                & ActorState_Moderate_RR 
                & ActorState_Low_SpO2
                & ActorState_Drowsiness_Level_3 
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.drowsinesssuspected_instance), 
                    onto.ActorStateHasAttention.value(onto.attentive_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.undefined_atrisk_instance)
                ]

        # unified signature 25
        class ActorState_ModerateHR_HighHRV_ModerateRR_NormalSpO2_LVL3(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_Moderate_HR
                & ActorState_High_HRV
                & ActorState_Moderate_RR 
                & ActorState_Normal_SpO2
                & ActorState_Drowsiness_Level_3 
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.awake_instance), 
                    onto.ActorStateHasAttention.value(onto.attentive_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.responsive_instance)
                ]

        # unified signature 26 
        class ActorState_ModerateHR_LowHRV_HighRR_LowSpO2_LVL3(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_Moderate_HR
                & ActorState_Low_HRV
                & ActorState_High_RR 
                & ActorState_Low_SpO2
                & ActorState_Drowsiness_Level_3 
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.undefinedstate_instance), 
                    onto.ActorStateHasAttention.value(onto.undefined_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.undefined_atrisk_instance)
                ]

        # unified signature 27 
        class ActorState_ModerateHR_LowHRV_LowRR_LowSpO2_LVL3(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_Moderate_HR
                & ActorState_Low_HRV
                & ActorState_Low_RR 
                & ActorState_Low_SpO2
                & ActorState_Drowsiness_Level_3 
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.undefinedstate_instance), 
                    onto.ActorStateHasAttention.value(onto.undefined_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.undefined_atrisk_instance)
                ]


        # unified signature 28 
        class ActorState_ModerateHR_ModerateHRV_LowRR_LowSpO2_LVL3(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_Moderate_HR
                & ActorState_Moderate_HRV
                & ActorState_Low_RR 
                & ActorState_Low_SpO2
                & ActorState_Drowsiness_Level_3 
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.undefinedstate_instance), 
                    onto.ActorStateHasAttention.value(onto.attentive_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.undefined_atrisk_instance)
                ]

        # unified signature 29
        class ActorState_ModerateHR_ModerateHRV_LowRR_NormalSpO2_LVL3(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_Moderate_HR
                & ActorState_Moderate_HRV
                & ActorState_Low_RR 
                & ActorState_Normal_SpO2
                & ActorState_Drowsiness_Level_3 
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.awake_instance), 
                    onto.ActorStateHasAttention.value(onto.undefined_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.responsive_instance)
                ]


        # unified signature 30 
        class ActorState_ModerateHR_ModerateHRV_ModerateRR_LowSpO2_LVL3(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_Moderate_HR
                & ActorState_Moderate_HRV
                & ActorState_Moderate_RR 
                & ActorState_Low_SpO2
                & ActorState_Drowsiness_Level_3 
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.drowsinesssuspected_instance), 
                    onto.ActorStateHasAttention.value(onto.attentive_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.undefined_atrisk_instance)
                ]

        # unified signature 31
        class ActorState_ModerateHR_ModerateHRV_ModerateRR_NormalSpO2_LVL3(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_Moderate_HR
                & ActorState_Moderate_HRV
                & ActorState_Moderate_RR 
                & ActorState_Normal_SpO2
                & ActorState_Drowsiness_Level_3 
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.awake_instance), 
                    onto.ActorStateHasAttention.value(onto.attentive_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.responsive_instance)
                ]
        
        # unified signature 32  
        class ActorState_VeryLowHR_LowHRV_HighRR_NormalSpO2_LVL3(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_Very_Low_HR
                & ActorState_Low_HRV
                & ActorState_High_RR 
                & ActorState_Normal_SpO2
                & ActorState_Drowsiness_Level_3 
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.drowsinesssuspected_instance), 
                    onto.ActorStateHasAttention.value(onto.attentive_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.undefined_atrisk_instance)
                ]
        # unified signature 33 
        class ActorState_VeryLowHR_LowHRV_LowRR_NormalSpO2_LVL3(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_Very_Low_HR
                & ActorState_Low_HRV
                & ActorState_Low_RR 
                & ActorState_Normal_SpO2
                & ActorState_Drowsiness_Level_3 
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.undefinedstate_instance), 
                    onto.ActorStateHasAttention.value(onto.attentive_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.undefined_atrisk_instance)
                ]

        # unified signature 34  
        class ActorState_VeryLowHR_LowHRV_VeryLowRR_LowSpO2_LVL3(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_Very_Low_HR
                & ActorState_Low_HRV
                & ActorState_Very_Low_RR 
                & ActorState_Normal_SpO2
                & ActorState_Drowsiness_Level_3 
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.drowsinesssuspected_instance), 
                    onto.ActorStateHasAttention.value(onto.attentive_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.undefined_atrisk_instance)
                ]

        # unified signature 35
        class ActorState_VeryLowHR_VeryLowHRV_HighRR_LowSpO2_LVL3(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_Very_Low_HR
                & ActorState_Very_Low_HRV
                & ActorState_High_RR 
                & ActorState_Low_SpO2
                & ActorState_Drowsiness_Level_3 
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.undefinedstate_instance), 
                    onto.ActorStateHasAttention.value(onto.undefined_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.imminent_instance)
                ]

        # unified signature 36 
        class ActorState_VeryLowHR_VeryLowHRV_HighRR_NormalSpO2_LVL3(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_Very_Low_HR
                & ActorState_Very_Low_HRV
                & ActorState_High_RR 
                & ActorState_Normal_SpO2
                & ActorState_Drowsiness_Level_3 
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.drowsinesssuspected_instance), 
                    onto.ActorStateHasAttention.value(onto.undefined_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.undefined_atrisk_instance)
                ]

        # unified signature 37 
        class ActorState_VeryLowHR_VeryLowHRV_LowRR_NormalSpO2_LVL3(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_Very_Low_HR
                & ActorState_Very_Low_HRV
                & ActorState_Low_RR 
                & ActorState_Normal_SpO2
                & ActorState_Drowsiness_Level_3 
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.undefinedstate_instance), 
                    onto.ActorStateHasAttention.value(onto.attentive_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.undefined_atrisk_instance)
                ]


        # unified signature 38 
        class ActorState_VeryLowHR_VeryLowHRV_VeryLowRR_CriticalSpO2_LVL3(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_Very_Low_HR
                & ActorState_Very_Low_HRV
                & ActorState_Very_Low_RR 
                & ActorState_Critical_SpO2
                & ActorState_Drowsiness_Level_3 
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.drowsinesssuspected_instance), 
                    onto.ActorStateHasAttention.value(onto.undefined_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.undefined_atrisk_instance)
                ]

        # unified signature 39
        class ActorState_VeryLowHR_VeryLowHRV_VeryLowRR_LowSpO2_LVL3(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_Very_Low_HR
                & ActorState_Very_Low_HRV
                & ActorState_Very_Low_RR 
                & ActorState_Low_SpO2
                & ActorState_Drowsiness_Level_3 
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.undefinedstate_instance), 
                    onto.ActorStateHasAttention.value(onto.undefined_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.imminent_instance)
                ]


        # unified signature 039
        class ActorState_VeryLowHR_ModerateHRV_ModerateRR_NormalSpO2_LVL7(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_Very_Low_HR
                & ActorState_Moderate_HRV
                & ActorState_Moderate_RR 
                & ActorState_Normal_SpO2
                & ActorState_Drowsiness_Level_7 
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.undefinedstate_instance), 
                    onto.ActorStateHasAttention.value(onto.undefined_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.imminent_instance)
                ]

        # unified signature 0039
        class ActorState_VeryLowHR_ModerateHRV_ModerateRR_LowSpO2_LVL7(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_Very_Low_HR
                & ActorState_Moderate_HRV
                & ActorState_Moderate_RR 
                & ActorState_Low_SpO2
                & ActorState_Drowsiness_Level_7 
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.undefinedstate_instance), 
                    onto.ActorStateHasAttention.value(onto.undefined_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.unresponsive_instance)
                ]
        # unified signature 00039    
        class ActorState_VeryLowHR_ModerateHRV_ModerateRR_NormalSpO2_LVL3(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_Very_Low_HR
                & ActorState_Moderate_HRV
                & ActorState_Moderate_RR 
                & ActorState_Normal_SpO2
                & ActorState_Drowsiness_Level_3 
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.undefinedstate_instance), 
                    onto.ActorStateHasAttention.value(onto.undefined_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.undefined_atrisk_instance)
                ]
            
        # unified signature 000039    
        class ActorState_VeryLowHR_ModerateHRV_ModerateRR_NormalSpO2_LVL5(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_Very_Low_HR
                & ActorState_Moderate_HRV
                & ActorState_Moderate_RR 
                & ActorState_Normal_SpO2
                & ActorState_Drowsiness_Level_5 
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.undefinedstate_instance), 
                    onto.ActorStateHasAttention.value(onto.undefined_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.undefined_atrisk_instance)
                ]

        # unified signature 40 
        class ActorState_VeryLowHR_VeryLowHRV_VeryLowRR_NormalSpO2_LVL3(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_Very_Low_HR
                & ActorState_Very_Low_HRV
                & ActorState_Very_Low_RR 
                & ActorState_Normal_SpO2
                & ActorState_Drowsiness_Level_3 
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.drowsinesssuspected_instance), 
                    onto.ActorStateHasAttention.value(onto.attentive_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.undefined_atrisk_instance)
                ]

        # unified signature 41
        class ActorState_HighHR_LowHRV_HighRR_LowSpO2_LVL5(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_High_HR
                & ActorState_Low_HRV
                & ActorState_High_RR 
                & ActorState_Low_SpO2
                & ActorState_Drowsiness_Level_5 
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.undefinedstate_instance), 
                    onto.ActorStateHasAttention.value(onto.inattentive_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.undefined_atrisk_instance)
                ]
        
        # unified signature 42  
        class ActorState_HighHR_LowHRV_VeryLowRR_LowSpO2_LVL5(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_High_HR
                & ActorState_Low_HRV
                & ActorState_Very_Low_RR 
                & ActorState_Low_SpO2
                & ActorState_Drowsiness_Level_5 
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.undefinedstate_instance), 
                    onto.ActorStateHasAttention.value(onto.inattentive_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.undefined_atrisk_instance)
                ]
        # unified signature 43 
        class ActorState_HighHR_VeryLowHRV_HighRR_LowSpO2_LVL5(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_High_HR
                & ActorState_Very_Low_HRV
                & ActorState_High_RR 
                & ActorState_Low_SpO2
                & ActorState_Drowsiness_Level_5 
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.undefinedstate_instance), 
                    onto.ActorStateHasAttention.value(onto.inattentive_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.imminent_instance)
                ]

        # unified signature 44  
        class ActorState_HighHR_VeryLowHRV_HighRR_NormalSpO2_LVL5(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_High_HR
                & ActorState_Very_Low_HRV
                & ActorState_High_RR 
                & ActorState_Normal_SpO2
                & ActorState_Drowsiness_Level_5 
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.undefinedstate_instance), 
                    onto.ActorStateHasAttention.value(onto.inattentive_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.undefined_atrisk_instance)
                ]

        # unified signature 45
        class ActorState_HighHR_VeryLowHRV_VeryLowRR_CriticalSpO2_LVL5(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_High_HR
                & ActorState_Very_Low_HRV
                & ActorState_Very_Low_RR 
                & ActorState_Critical_SpO2
                & ActorState_Drowsiness_Level_5 
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.undefinedstate_instance), 
                    onto.ActorStateHasAttention.value(onto.undefined_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.unresponsive_instance)
                ]

        # unified signature 46 
        class ActorState_HighHR_VeryLowHRV_VeryLowRR_LowSpO2_LVL5(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_High_HR
                & ActorState_Very_Low_HRV
                & ActorState_Very_Low_RR 
                & ActorState_Low_SpO2
                & ActorState_Drowsiness_Level_5 
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.undefinedstate_instance), 
                    onto.ActorStateHasAttention.value(onto.inattentive_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.imminent_instance)
                ]

        # unified signature 47 
        class ActorState_HighHR_VeryLowHRV_VeryLowRR_NormalSpO2_LVL5(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_High_HR
                & ActorState_Very_Low_HRV
                & ActorState_Very_Low_RR 
                & ActorState_Normal_SpO2
                & ActorState_Drowsiness_Level_5 
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.undefinedstate_instance), 
                    onto.ActorStateHasAttention.value(onto.inattentive_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.undefined_atrisk_instance)
                ]


        # unified signature 48 
        class ActorState_ModerateHR_HighHRV_ModerateRR_LowSpO2_LVL5(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_Moderate_HR
                & ActorState_High_HRV
                & ActorState_Moderate_RR 
                & ActorState_Low_SpO2
                & ActorState_Drowsiness_Level_5
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.drowsinesssuspected_instance), 
                    onto.ActorStateHasAttention.value(onto.inattentive_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.undefined_atrisk_instance)
                ]

        # unified signature 49
        class ActorState_ModerateHR_HighHRV_ModerateRR_NormalSpO2_LVL5(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_Moderate_HR
                & ActorState_High_HRV
                & ActorState_Moderate_RR 
                & ActorState_Normal_SpO2
                & ActorState_Drowsiness_Level_5 
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.awake_instance), 
                    onto.ActorStateHasAttention.value(onto.attentive_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.undefined_atrisk_instance)
                ]


        # unified signature 50 
        class ActorState_ModerateHR_LowHRV_ModerateRR_LowSpO2_LVL5(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_Moderate_HR
                & ActorState_Low_HRV
                & ActorState_Moderate_RR 
                & ActorState_Low_SpO2
                & ActorState_Drowsiness_Level_5 
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.drowsinesssuspected_instance), 
                    onto.ActorStateHasAttention.value(onto.undefined_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.undefined_atrisk_instance)
                ]
            

        # unified signature 51
        class ActorState_ModerateHR_ModerateHRV_ModerateRR_LowSpO2_LVL5(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_Moderate_HR
                & ActorState_Moderate_HRV
                & ActorState_Moderate_RR 
                & ActorState_Low_SpO2
                & ActorState_Drowsiness_Level_5 
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.drowsinesssuspected_instance), 
                    onto.ActorStateHasAttention.value(onto.inattentive_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.undefined_atrisk_instance)
                ]
        
        # unified signature 52  
        class ActorState_ModerateHR_ModerateHRV_ModerateRR_NormalSpO2_LVL5(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_Moderate_HR
                & ActorState_Moderate_HRV
                & ActorState_Moderate_RR 
                & ActorState_Normal_SpO2
                & ActorState_Drowsiness_Level_5 
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.awake_instance), 
                    onto.ActorStateHasAttention.value(onto.attentive_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.undefined_atrisk_instance)
                ]
            

        # ADDED EXTRA 1 
        class ActorState_ModerateHR_VeryLowHRV_ModerateRR_LowSpO2_LVL3(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_Moderate_HR
                & ActorState_Very_Low_HRV
                & ActorState_Moderate_RR 
                & ActorState_Low_SpO2
                & ActorState_Drowsiness_Level_3 
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.drowsinesssuspected_instance), 
                    onto.ActorStateHasAttention.value(onto.undefined_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.undefined_atrisk_instance)
                ]

            
        # unified signature 53 
        class ActorState_ModerateHR_VeryLowHRV_ModerateRR_LowSpO2_LVL5(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_Moderate_HR
                & ActorState_Very_Low_HRV
                & ActorState_Moderate_RR 
                & ActorState_Low_SpO2
                & ActorState_Drowsiness_Level_5 
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.drowsinesssuspected_instance), 
                    onto.ActorStateHasAttention.value(onto.undefined_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.undefined_atrisk_instance)
                ]

        # unified signature 54  
        class ActorState_VeryLowHR_LowHRV_HighRR_LowSpO2_LVL5(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_Very_Low_HR
                & ActorState_Low_HRV
                & ActorState_High_RR 
                & ActorState_Low_SpO2
                & ActorState_Drowsiness_Level_5 
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.undefinedstate_instance), 
                    onto.ActorStateHasAttention.value(onto.inattentive_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.undefined_atrisk_instance)
                ]

        # unified signature 55
        class ActorState_VeryLowHR_LowHRV_VeryLowRR_LowSpO2_LVL5(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_Very_Low_HR
                & ActorState_Low_HRV
                & ActorState_Very_Low_RR 
                & ActorState_Low_SpO2
                & ActorState_Drowsiness_Level_5 
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.undefinedstate_instance), 
                    onto.ActorStateHasAttention.value(onto.inattentive_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.undefined_atrisk_instance)
                ]

        # unified signature 56 
        class ActorState_VeryLowHR_VeryLowHRV_LowRR_LowSpO2_LVL5(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_Very_Low_HR
                & ActorState_Very_Low_HRV
                & ActorState_Low_RR 
                & ActorState_Low_SpO2
                & ActorState_Drowsiness_Level_5 
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.undefinedstate_instance), 
                    onto.ActorStateHasAttention.value(onto.inattentive_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.imminent_instance)
                ]

        # unified signature 57 
        class ActorState_VeryLowHR_VeryLowHRV_LowRR_NormalSpO2_LVL5(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_Very_Low_HR
                & ActorState_Very_Low_HRV
                & ActorState_Low_RR 
                & ActorState_Normal_SpO2
                & ActorState_Drowsiness_Level_5 
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.undefinedstate_instance), 
                    onto.ActorStateHasAttention.value(onto.inattentive_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.undefined_atrisk_instance)
                ]

        # unified signature 57-A
        class ActorState_ModerateHR_VeryLowHRV_ModerateRR_NormalSpO2_LVL5(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_Moderate_HR
                & ActorState_Very_Low_HRV
                & ActorState_Moderate_RR 
                & ActorState_Normal_SpO2
                & ActorState_Drowsiness_Level_5 
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.undefinedstate_instance), 
                    onto.ActorStateHasAttention.value(onto.inattentive_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.undefined_atrisk_instance)
                ]
        
        # unified signature 57-B
        class ActorState_ModerateHR_VeryLowHRV_ModerateRR_NormalSpO2_LVL3(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_Moderate_HR
                & ActorState_Very_Low_HRV
                & ActorState_Moderate_RR 
                & ActorState_Normal_SpO2
                & ActorState_Drowsiness_Level_3 
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.undefinedstate_instance), 
                    onto.ActorStateHasAttention.value(onto.inattentive_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.undefined_atrisk_instance)
                ]

        # unified signature 58 
        class ActorState_VeryLowHR_VeryLowHRV_VeryLowRR_CriticalSpO2_LVL5(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_Very_Low_HR
                & ActorState_Very_Low_HRV
                & ActorState_Very_Low_RR 
                & ActorState_Critical_SpO2
                & ActorState_Drowsiness_Level_5
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.undefinedstate_instance), 
                    onto.ActorStateHasAttention.value(onto.undefined_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.unresponsive_instance)
                ]

        # unified signature 59
        class ActorState_VeryLowHR_VeryLowHRV_VeryLowRR_LowSpO2_LVL5(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_Very_Low_HR
                & ActorState_Very_Low_HRV
                & ActorState_Very_Low_RR 
                & ActorState_Low_SpO2
                & ActorState_Drowsiness_Level_5 
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.undefinedstate_instance), 
                    onto.ActorStateHasAttention.value(onto.inattentive_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.imminent_instance)
                ]


        # unified signature 60 
        class ActorState_VeryLowHR_VeryLowHRV_VeryLowRR_NormalSpO2_LVL5(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_Very_Low_HR
                & ActorState_Very_Low_HRV
                & ActorState_Very_Low_RR 
                & ActorState_Normal_SpO2
                & ActorState_Drowsiness_Level_5 
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.undefinedstate_instance), 
                    onto.ActorStateHasAttention.value(onto.inattentive_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.undefined_atrisk_instance)
                ]
            

        # unified signature 61
        class ActorState_HighHR_LowHRV_HighRR_LowSpO2_LVL7(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_High_HR
                & ActorState_Low_HRV
                & ActorState_High_RR 
                & ActorState_Low_SpO2
                & ActorState_Drowsiness_Level_7 
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.undefinedstate_instance), 
                    onto.ActorStateHasAttention.value(onto.inattentive_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.undefined_atrisk_instance)
                ]
        
        # unified signature 62  
        class ActorState_HighHR_LowHRV_HighRR_NormalSpO2_LVL7(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_High_HR
                & ActorState_Low_HRV
                & ActorState_High_RR 
                & ActorState_Normal_SpO2
                & ActorState_Drowsiness_Level_7 
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.sleep_instance), 
                    onto.ActorStateHasAttention.value(onto.undefined_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.undefined_atrisk_instance)
                ]
            
        # unified signature 63 
        class ActorState_HighHR_LowHRV_VeryLowRR_LowSpO2_LVL7(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_High_HR
                & ActorState_Low_HRV
                & ActorState_Very_Low_RR 
                & ActorState_Low_SpO2
                & ActorState_Drowsiness_Level_7 
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.undefinedstate_instance), 
                    onto.ActorStateHasAttention.value(onto.inattentive_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.undefined_atrisk_instance)
                ]

        # unified signature 64  
        class ActorState_HighHR_LowHRV_VeryLowRR_NormalSpO2_LVL7(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_High_HR
                & ActorState_Low_HRV
                & ActorState_Very_Low_RR 
                & ActorState_Normal_SpO2
                & ActorState_Drowsiness_Level_7 
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.sleep_instance), 
                    onto.ActorStateHasAttention.value(onto.undefined_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.undefined_atrisk_instance)
                ]

        # unified signature 65
        class ActorState_HighHR_VeryLowHRV_HighRR_LowSpO2_LVL7(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_High_HR
                & ActorState_Very_Low_HRV
                & ActorState_High_RR 
                & ActorState_Low_SpO2
                & ActorState_Drowsiness_Level_7 
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.undefinedstate_instance), 
                    onto.ActorStateHasAttention.value(onto.inattentive_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.undefined_atrisk_instance)
                ]

        # unified signature 66 
        class ActorState_HighHR_VeryLowHRV_HighRR_NormalSpO2_LVL7(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_High_HR
                & ActorState_Very_Low_HRV
                & ActorState_High_RR 
                & ActorState_Normal_SpO2
                & ActorState_Drowsiness_Level_7 
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.sleep_instance), 
                    onto.ActorStateHasAttention.value(onto.undefined_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.undefined_atrisk_instance)
                ]

        # unified signature 67 
        class ActorState_HighHR_VeryLowHRV_VeryLowRR_CriticalSpO2_LVL7(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_High_HR
                & ActorState_Very_Low_HRV
                & ActorState_Very_Low_RR 
                & ActorState_Critical_SpO2
                & ActorState_Drowsiness_Level_7 
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.undefinedstate_instance), 
                    onto.ActorStateHasAttention.value(onto.undefined_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.unresponsive_instance)
                ]


        # unified signature 68 
        class ActorState_HighHR_VeryLowHRV_VeryLowRR_NormalSpO2_LVL7(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_High_HR
                & ActorState_Very_Low_HRV
                & ActorState_Very_Low_RR 
                & ActorState_Normal_SpO2
                & ActorState_Drowsiness_Level_7 
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.sleep_instance), 
                    onto.ActorStateHasAttention.value(onto.inattentive_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.undefined_atrisk_instance)
                ]

        # unified signature 69
        class ActorState_ModerateHR_HighHRV_ModerateRR_LowSpO2_LVL7(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_Moderate_HR
                & ActorState_High_HRV
                & ActorState_Moderate_RR 
                & ActorState_Low_SpO2
                & ActorState_Drowsiness_Level_7 
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.sleep_instance), 
                    onto.ActorStateHasAttention.value(onto.inattentive_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.undefined_atrisk_instance)
                ]


        # unified signature 70 
        class ActorState_ModerateHR_ModerateHRV_ModerateRR_LowSpO2_LVL7(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_Moderate_HR
                & ActorState_Moderate_HRV
                & ActorState_Moderate_RR 
                & ActorState_Low_SpO2
                & ActorState_Drowsiness_Level_7 
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.undefinedstate_instance), 
                    onto.ActorStateHasAttention.value(onto.inattentive_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.undefined_atrisk_instance)
                ]
            



        # unified signature 71
        class ActorState_ModerateHR_ModerateHRV_ModerateRR_NormalSpO2_LVL7(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_Moderate_HR
                & ActorState_Moderate_HRV
                & ActorState_Moderate_RR 
                & ActorState_Normal_SpO2
                & ActorState_Drowsiness_Level_7 
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.undefinedstate_instance), 
                    onto.ActorStateHasAttention.value(onto.inattentive_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.undefined_atrisk_instance)
                ]

        # unified signature 71-A
        class ActorState_ModerateHR_HighHRV_ModerateRR_NormalSpO2_LVL7(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_Moderate_HR
                & ActorState_High_HRV
                & ActorState_Moderate_RR 
                & ActorState_Normal_SpO2
                & ActorState_Drowsiness_Level_7 
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.awake_instance), 
                    onto.ActorStateHasAttention.value(onto.inattentive_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.undefined_atrisk_instance)
                ]

        
        # unified signature 72  
        class ActorState_ModerateHR_VeryLowHRV_ModerateRR_LowSpO2_LVL7(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_Moderate_HR
                & ActorState_Very_Low_HRV
                & ActorState_Moderate_RR 
                & ActorState_Low_SpO2
                & ActorState_Drowsiness_Level_7 
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.sleep_instance), 
                    onto.ActorStateHasAttention.value(onto.undefined_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.undefined_atrisk_instance)
                ]
            
        # unified signature 73 
        class ActorState_VeryLowHR_LowHRV_HighRR_LowSpO2_LVL7(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_Very_Low_HR
                & ActorState_Low_HRV
                & ActorState_High_RR 
                & ActorState_Low_SpO2
                & ActorState_Drowsiness_Level_7 
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.undefinedstate_instance), 
                    onto.ActorStateHasAttention.value(onto.inattentive_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.undefined_atrisk_instance)
                ]

        # unified signature 74  
        class ActorState_VeryLowHR_LowHRV_HighRR_NormalSpO2_LVL7(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_Very_Low_HR
                & ActorState_Low_HRV
                & ActorState_High_RR 
                & ActorState_Normal_SpO2
                & ActorState_Drowsiness_Level_7 
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.sleep_instance), 
                    onto.ActorStateHasAttention.value(onto.undefined_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.undefined_atrisk_instance)
                ]

        # unified signature 75
        class ActorState_VeryLowHR_LowHRV_VeryLowRR_LowSpO2_LVL7(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_Very_Low_HR
                & ActorState_Low_HRV
                & ActorState_Very_Low_RR 
                & ActorState_Low_SpO2
                & ActorState_Drowsiness_Level_7 
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.undefinedstate_instance), 
                    onto.ActorStateHasAttention.value(onto.inattentive_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.undefined_atrisk_instance)
                ]

        # unified signature 76 
        class ActorState_VeryLowHR_LowHRV_VeryLowRR_NormalSpO2_LVL7(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_Very_Low_HR
                & ActorState_Low_HRV
                & ActorState_Very_Low_RR 
                & ActorState_Normal_SpO2
                & ActorState_Drowsiness_Level_7 
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.sleep_instance), 
                    onto.ActorStateHasAttention.value(onto.undefined_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.undefined_atrisk_instance)
                ]

        # unified signature 77 
        class ActorState_VeryLowHR_VeryLowHRV_HighRR_LowSpO2_LVL7(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_Very_Low_HR
                & ActorState_Very_Low_HRV
                & ActorState_High_RR 
                & ActorState_Low_SpO2
                & ActorState_Drowsiness_Level_7 
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.undefinedstate_instance), 
                    onto.ActorStateHasAttention.value(onto.inattentive_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.undefined_atrisk_instance)
                ]

        # unified signature 78 
        class ActorState_VeryLowHR_VeryLowHRV_HighRR_NormalSpO2_LVL7(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_Very_Low_HR
                & ActorState_Very_Low_HRV
                & ActorState_High_RR 
                & ActorState_Normal_SpO2
                & ActorState_Drowsiness_Level_7 
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.sleep_instance), 
                    onto.ActorStateHasAttention.value(onto.undefined_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.undefined_atrisk_instance)
                ]

        # unified signature 79
        class ActorState_VeryLowHR_VeryLowHRV_VeryLowRR_CriticalSpO2_LVL7(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_Very_Low_HR
                & ActorState_Very_Low_HRV
                & ActorState_Very_Low_RR 
                & ActorState_Critical_SpO2
                & ActorState_Drowsiness_Level_7 
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.undefinedstate_instance), 
                    onto.ActorStateHasAttention.value(onto.undefined_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.unresponsive_instance)
                ]


        # unified signature 80 
        class ActorState_VeryLowHR_VeryLowHRV_VeryLowRR_LowSpO2_LVL7(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_Very_Low_HR
                & ActorState_Very_Low_HRV
                & ActorState_Very_Low_RR 
                & ActorState_Normal_SpO2
                & ActorState_Drowsiness_Level_7 
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.sleep_instance), 
                    onto.ActorStateHasAttention.value(onto.inattentive_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.undefined_atrisk_instance)
                ]
            
        # unified signature 80 
        class ActorState_LVL9(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_Drowsiness_Level_9
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.undefinedstate_instance), 
                    onto.ActorStateHasAttention.value(onto.undefined_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.unresponsive_instance)
                ]
            
        # unified signature 81 
        class ActorState_VeryLowHR_HighHRV_LowRR_NormalSpO2_LVL3(onto.ActorState): 
            equivalent_to = [(
                onto.ActorState 
                & ActorState_Very_Low_HR
                & ActorState_High_HRV
                & ActorState_Low_RR 
                & ActorState_Normal_SpO2
                & ActorState_Drowsiness_Level_3 
                )]

            is_a = [
                    onto.ActorStateHasFatigue.value(onto.drowsinesssuspected_instance), 
                    onto.ActorStateHasAttention.value(onto.undefined_instance), 
                    onto.ActorStateHasUnresponsiveness.value(onto.undefined_atrisk_instance)
                ]
            
        # unified signature 82
        # class ActorState_VeryLowHR_HighHRV_LowRR_LowSpO2_LVL7(onto.ActorState): 
        #     equivalent_to = [(
        #         onto.ActorState 
        #         & ActorState_Very_Low_HR
        #         & ActorState_High_HRV
        #         & ActorState_Low_RR 
        #         & ActorState_Normal_SpO2
        #         & ActorState_Drowsiness_Level_3 
        #         )]

        #     is_a = [
        #             onto.ActorStateHasFatigue.value(onto.drowsinesssuspected_instance), 
        #             onto.ActorStateHasAttention.value(onto.undefined_instance), 
        #             onto.ActorStateHasUnresponsiveness.value(onto.unresponsive_instance)
        #         ]
            
    logger.debug("All GCIs set correctly")    


def eye_mouth_state_rules(): 

    # Closed eyes mouth open
    Imp().set_as_rule(
       """
       ActorState(?act_st), 
       ActorStateHasFatigue(?act_st, sleep_instance), 
       ActorHasEyeState(?act_st, ?eye_st),
       ActorHasMouthState(?act_st, ?mouth_st)
       -> 
       EyeStateIs(?eye_st, closedstate_instance),
       MouthStateIs(?mouth_st, open_instance)
       """
    )

    # Closed eyes mouth open 
    Imp().set_as_rule(
        """
        ActorState(?act_st), 
        ActorStateHasUnresponsiveness(?act_st, unresponsive_instance), 
        ActorHasEyeState(?act_st, ?eye_st),
        ActorHasMouthState(?act_st, ?mouth_st)
        -> 
        EyeStateIs(?eye_st, closedstate_instance),
        MouthStateIs(?mouth_st, open_instance)
        """
    )
 
    # Open eyes mouth closed 
    Imp().set_as_rule(
       """
       ActorState(?act_st), 
       ActorStateHasFatigue(?act_st, awake_instance), 
       ActorStateHasAttention(?act_st, attentive_instance), 
       ActorStateHasUnresponsiveness(?act_st, responsive_instance),
       ActorHasEyeState(?act_st, ?eye_st), 
       ActorHasMouthState(?act_st, ?mouth_st)
       -> 
       EyeStateIs(?eye_st, openstate_instance), 
       MouthStateIs(?mouth_st, closed_instance) 
       """
    )


    Imp().set_as_rule(
        """
        ActorState(?act_st), 
        ActorStateHasFatigue(?act_st, drowsinesssuspected_instance), 
        ActorStateHasAttention(?act_st, attentive_instance), 
        ActorStateHasUnresponsiveness(?act_st, responsive_instance), 
        ActorHasEyeState(?act_st, ?eye_st), 
        ActorHasMouthState(?act_st, ?mouth_st)
        -> 
        EyeStateIs(?eye_st, openstate_instance), 
        MouthStateIs(?mouth_st, open_instance)
        """
    )

    Imp().set_as_rule(
       """
        ActorState(?act_st), 
        ActorStateHasFatigue(?act_st, drowsinesssuspected_instance), 
        ActorStateHasAttention(?act_st, inattentive_instance), 
        ActorStateHasUnresponsiveness(?act_st, responsive_instance), 
        ActorHasEyeState(?act_st, ?eye_st), 
        ActorHasMouthState(?act_st, ?mouth_st)
        -> 
        EyeStateIs(?eye_st, openstate_instance), 
        MouthStateIs(?mouth_st, open_instance)
       """

    )

    Imp().set_as_rule(
               """
                ActorState(?act_st),
                ActorStateHasFatigue(?act_st, drowsinesssuspected_instance),
                ActorStateHasAttention(?act_st, attentive_instance),
                ActorStateHasUnresponsiveness(?act_st, imminent_instance),  
                ActorHasEyeState(?act_st,?eye_inst),
                ActorHasMouthState(?act_st, ?mouth_st)
                ->
                EyeStateIs(?eye_inst, closed_instance), 
                MouthStateIs(?mouth_st, open_instance)
               """
            )

    Imp().set_as_rule(
       """
        ActorState(?act_st), 
        ActorStateHasFatigue(?act_st, awake_instance), 
        ActorStateHasAttention(?act_st, inattentive_instance), 
        ActorStateHasUnresponsiveness(?act_st, responsive_instance), 
        ActorHasEyeState(?act_st, ?eye_st), 
        ActorHasMouthState(?act_st, ?mouth_st)
        -> 
        EyeStateIs(?eye_st, openstate_instance), 
        MouthStateIs(?mouth_st, open_instance)
       """
    )

    Imp().set_as_rule(
       """
        ActorState(?act_st), 
        ActorStateHasFatigue(?act_st, drowsinesssuspected_instance), 
        ActorStateHasAttention(?act_st, attentive_instance), 
        ActorStateHasUnresponsiveness(?act_st, undefined_atrisk_instance), 
        ActorHasEyeState(?act_st, ?eye_st), 
        ActorHasMouthState(?act_st, ?mouth_st)
        -> 
        EyeStateIs(?eye_st, openstate_instance), 
        MouthStateIs(?mouth_st, closed_instance)
       """
    )

    Imp().set_as_rule(
       """
        ActorState(?act_st), 
        ActorStateHasFatigue(?act_st, awake_instance), 
        ActorStateHasAttention(?act_st, inattentive_instance), 
        ActorStateHasUnresponsiveness(?act_st, undefined_atrisk_instance), 
        ActorHasEyeState(?act_st, ?eye_st), 
        ActorHasMouthState(?act_st, ?mouth_st)
        -> 
        EyeStateIs(?eye_st, openstate_instance), 
        MouthStateIs(?mouth_st, closed_instance)
       """
    )

    Imp().set_as_rule(
       """
        ActorState(?act_st), 
        ActorStateHasFatigue(?act_st, awake_instance), 
        ActorStateHasAttention(?act_st, inattentive_instance), 
        ActorStateHasUnresponsiveness(?act_st, undefined_atrisk_instance), 
        ActorHasEyeState(?act_st, ?eye_st), 
        ActorHasMouthState(?act_st, ?mouth_st)
        -> 
        EyeStateIs(?eye_st, openstate_instance), 
        MouthStateIs(?mouth_st, closed_instance)
       """
    )


    Imp().set_as_rule(
       """
        ActorState(?act_st), 
        ActorStateHasFatigue(?act_st, awake_instance), 
        ActorStateHasAttention(?act_st, attentive_instance), 
        ActorStateHasUnresponsiveness(?act_st, undefined_atrisk_instance), 
        ActorHasEyeState(?act_st, ?eye_st), 
        ActorHasMouthState(?act_st, ?mouth_st)
        -> 
        EyeStateIs(?eye_st, openstate_instance), 
        MouthStateIs(?mouth_st, closed_instance)
       """
    )

    Imp().set_as_rule(
       """
        ActorState(?act_st), 
        ActorStateHasFatigue(?act_st, undefinedstate_instance), 
        ActorStateHasAttention(?act_st, attentive_instance), 
        ActorStateHasUnresponsiveness(?act_st, undefined_atrisk_instance), 
        ActorHasEyeState(?act_st, ?eye_st), 
        ActorHasMouthState(?act_st, ?mouth_st)
        -> 
        EyeStateIs(?eye_st, openstate_instance), 
        MouthStateIs(?mouth_st, closed_instance)
       """
    )

    Imp().set_as_rule(
       """
        ActorState(?act_st), 
        ActorStateHasFatigue(?act_st, undefinedstate_instance), 
        ActorStateHasAttention(?act_st,undefined_instance), 
        ActorStateHasUnresponsiveness(?act_st, undefined_atrisk_instance), 
        ActorHasEyeState(?act_st, ?eye_st), 
        ActorHasMouthState(?act_st, ?mouth_st)
        -> 
        EyeStateIs(?eye_st, closedstate_instance), 
        MouthStateIs(?mouth_st, open_instance)
       """
    )

    Imp().set_as_rule(
       """
        ActorState(?act_st), 
        ActorStateHasFatigue(?act_st, undefinedstate_instance), 
        ActorStateHasAttention(?act_st,undefined_instance), 
        ActorStateHasUnresponsiveness(?act_st, unresponsive_instance), 
        ActorHasEyeState(?act_st, ?eye_st), 
        ActorHasMouthState(?act_st, ?mouth_st)
        -> 
        EyeStateIs(?eye_st, closedstate_instance), 
        MouthStateIs(?mouth_st, open_instance)
       """
    )

    Imp().set_as_rule(
       """
        ActorState(?act_st), 
        ActorStateHasFatigue(?act_st, undefinedstate_instance), 
        ActorStateHasAttention(?act_st,undefined_instance), 
        ActorStateHasUnresponsiveness(?act_st, imminent_instance), 
        ActorHasEyeState(?act_st, ?eye_st), 
        ActorHasMouthState(?act_st, ?mouth_st)
        -> 
        EyeStateIs(?eye_st, closedstate_instance), 
        MouthStateIs(?mouth_st, open_instance)
       """
    )

    Imp().set_as_rule(
       """
        ActorState(?act_st), 
        ActorStateHasFatigue(?act_st, attentive_instance), 
        ActorStateHasAttention(?act_st,undefined_instance), 
        ActorStateHasUnresponsiveness(?act_st, responsive_instance), 
        ActorHasEyeState(?act_st, ?eye_st), 
        ActorHasMouthState(?act_st, ?mouth_st)
        -> 
        EyeStateIs(?eye_st, openstate_instance), 
        MouthStateIs(?mouth_st, closed_instance)
       """
    )

    Imp().set_as_rule(
       """
        ActorState(?act_st), 
        ActorStateHasFatigue(?act_st, drowsinesssuspected_instance), 
        ActorStateHasAttention(?act_st,undefined_instance), 
        ActorStateHasUnresponsiveness(?act_st, undefined_atrisk_instance), 
        ActorHasEyeState(?act_st, ?eye_st), 
        ActorHasMouthState(?act_st, ?mouth_st)
        -> 
        EyeStateIs(?eye_st, openstate_instance), 
        MouthStateIs(?mouth_st, closed_instance)
       """
    )

    Imp().set_as_rule(
    """
        ActorState(?act_st), 
        ActorStateHasFatigue(?act_st, drowsinesssuspected_instance), 
        ActorStateHasAttention(?act_st, inattentive_instance), 
        ActorStateHasUnresponsiveness(?act_st, undefined_atrisk_instance), 
        ActorHasEyeState(?act_st, ?eye_st), 
        ActorHasMouthState(?act_st, ?mouth_st)
        -> 
        EyeStateIs(?eye_st, openstate_instance), 
        MouthStateIs(?mouth_st, open_instance)

    """
    )

    Imp().set_as_rule(
    """
        ActorState(?act_st), 
        ActorStateHasFatigue(?act_st, undefinedstate_instance), 
        ActorStateHasAttention(?act_st, inattentive_instance), 
        ActorStateHasUnresponsiveness(?act_st, undefined_atrisk_instance), 
        ActorHasEyeState(?act_st, ?eye_st), 
        ActorHasMouthState(?act_st, ?mouth_st)
        -> 
        EyeStateIs(?eye_st, openstate_instance), 
        MouthStateIs(?mouth_st, open_instance)

    """
    )

    Imp().set_as_rule(
    """
        ActorState(?act_st), 
        ActorStateHasFatigue(?act_st, awake_instance), 
        ActorStateHasAttention(?act_st, undefined_instance), 
        ActorStateHasUnresponsiveness(?act_st, responsive_instance), 
        ActorHasEyeState(?act_st, ?eye_st), 
        ActorHasMouthState(?act_st, ?mouth_st)
        -> 
        EyeStateIs(?eye_st, openstate_instance), 
        MouthStateIs(?mouth_st, open_instance)

    """
    )

    logger.debug("[checked] EyeState rules have also been set correctly")


def set_up_HR_rules():
    """
    This function creates the rules to categorize the HR of the actor into
    threshold ranges: 
    * Low 
    * Slightly Low 
    * Moderate (Normal) 
    * High 

    These threshold ranges change based on the Age group of the actor.
    """
    Imp().set_as_rule(
        f""" 
        ActorState(?act_st), validAt(?act_st, ?t),
        StateHasThresholdProfile(?act_st, ?tp), 
        ActorStateHasPhysiologicalState(?act_st, ?hr_inst), HR(?hr_inst), 
        hasNumericalValue(?hr_inst, ?value), phyValidAt(?hr_inst, ?phy_t), 
        appliesHRLow(?tp, ?hr_low), hasThrValue(?hr_low, ?low), 
        greaterThanOrEqual(?value, 0), 
        lessThan(?value, ?low), 
        stringEqualIgnoreCase(?t, ?phy_t),
        Very_Low_HR(?vrl_hr)
        ->  HRis(?hr_inst, ?vrl_hr) 
        """
    )
    
    Imp().set_as_rule(
        f""" 
        ActorState(?act_st), validAt(?act_st, ?t), StateHasThresholdProfile(?act_st, ?tp), 
        ActorStateHasPhysiologicalState(?act_st, ?hr_inst), HR(?hr_inst), 
        hasNumericalValue(?hr_inst, ?value), phyValidAt(?hr_inst, ?phy_t), 
        appliesHRLow(?tp, ?hr_low), hasThrValue(?hr_low, ?low), 
        appliesHRModerate(?tp, ?hr_mod), hasThrValue(?hr_mod, ?mod), 
        greaterThanOrEqual(?value, ?low),
        lessThan(?value, ?mod), 
        stringEqualIgnoreCase(?t, ?phy_t),
        Low_HR(?l_hr)
        ->  HRis(?hr_inst, ?l_hr) 
        """
    )

    Imp().set_as_rule(
        f""" 
        ActorState(?act_st), validAt(?act_st,?t), StateHasThresholdProfile(?act_st, ?tp), 
        ActorStateHasPhysiologicalState(?act_st, ?hr_inst), HR(?hr_inst), 
        hasNumericalValue(?hr_inst, ?value), phyValidAt(?hr_inst, ?phy_t), 
        appliesHRModerate(?tp, ?hr_mod), hasThrValue(?hr_mod, ?mod), 
        appliesHRHigh(?tp, ?hr_high), hasThrValue(?hr_high, ?high), 
        greaterThanOrEqual(?value, ?mod),
        lessThan(?value, ?high), 
        stringEqualIgnoreCase(?t, ?phy_t),
        Moderate_HR(?mod_hr)
        -> HRis(?hr_inst, ?mod_hr) 
        """
    )

    Imp().set_as_rule(
        f""" 
        ActorState(?act_st),  validAt(?act_st, ?t), StateHasThresholdProfile(?act_st, ?tp), 
        ActorStateHasPhysiologicalState(?act_st, ?hr_inst), HR(?hr_inst), 
        hasNumericalValue(?hr_inst, ?value), phyValidAt(?hr_inst, ?phy_t), 
        appliesHRHigh(?tp, ?hr_high), hasThrValue(?hr_high, ?high), 
        greaterThanOrEqual(?value, ?high),
        lessThan(?value, 250), 
        stringEqualIgnoreCase(?t, ?phy_t),
        High_HR(?high_hr)
        -> HRis(?hr_inst, ?high_hr) 
        """
    )

    logger.debug("[checked] HR rules set correctly")


def set_up_HRV_rules():
    """
        This function creates the rules to categorize the HRV of the actor into
        threshold ranges: 
        * Very Low 
        * Low 
        * Moderate (Normal) 
        * High 

        These threshold ranges change based on the Age group of the actor.
    """
    Imp().set_as_rule(
        f"""
        ActorState(?act_st), validAt(?act_st, ?t), StateHasThresholdProfile(?act_st, ?tp), 
        ActorStateHasPhysiologicalState(?act_st, ?hrv_inst), HRV(?hrv_inst),
        hasNumericalValue(?hrv_inst, ?value), phyValidAt(?hrv_inst, ?phy_t), 
        appliesHRVLow(?tp, ?hrv_low), hasThrValue(?hrv_low, ?low), 
        greaterThanOrEqual(?value, 0), 
        lessThan(?value, ?low),
        stringEqualIgnoreCase(?t, ?phy_t),
        Very_Low_HRV(?vrl_hrv)
        -> HRVis(?hrv_inst, ?vrl_hrv)
        """
    )

    Imp().set_as_rule(
        f"""
        ActorState(?act_st),  validAt(?act_st, ?t), StateHasThresholdProfile(?act_st, ?tp), 
        ActorStateHasPhysiologicalState(?act_st,?hrv_inst), HRV(?hrv_inst), 
        hasNumericalValue(?hrv_inst, ?value), phyValidAt(?hrv_inst, ?phy_t), 
        appliesHRVLow(?tp, ?hrv_low), hasThrValue(?hrv_low, ?low), 
        appliesHRVModerate(?tp, ?hrv_mod), hasThrValue(?hrv_mod, ?mod), 
        greaterThanOrEqual(?value, ?low), 
        lessThan(?value, ?mod), 
        stringEqualIgnoreCase(?t, ?phy_t),
        Low_HRV(?l_hrv)
        -> HRVis(?hrv_inst, ?l_hrv)
        """
    )

    Imp().set_as_rule(
        f"""
        ActorState(?act_st),  validAt(?act_st, ?t), StateHasThresholdProfile(?act_st, ?tp), 
        ActorStateHasPhysiologicalState(?act_st, ?hrv_inst), HRV(?hrv_inst), 
        hasNumericalValue(?hrv_inst, ?value), phyValidAt(?hrv_inst, ?phy_t), 
        appliesHRVModerate(?tp, ?hrv_mod), hasThrValue(?hrv_mod, ?mod), 
        appliesHRVHigh(?tp, ?hrv_high), hasThrValue(?hrv_high, ?high), 
        greaterThanOrEqual(?value, ?mod), 
        lessThan(?value, ?high),
        stringEqualIgnoreCase(?t, ?phy_t),
        Moderate_HRV(?mod_hrv)
        -> HRVis(?hrv_inst, ?mod_hrv)
        """
    )

    Imp().set_as_rule(
        f"""
        ActorState(?act_st), validAt(?act_st, ?t), StateHasThresholdProfile(?act_st, ?tp), 
        ActorStateHasPhysiologicalState(?act_st, ?hrv_inst), HRV(?hrv_inst), 
        hasNumericalValue(?hrv_inst, ?value), phyValidAt(?hrv_inst, ?phy_t), 
        appliesHRVHigh(?tp, ?hrv_high), hasThrValue(?hrv_high, ?high), 
        greaterThanOrEqual(?value, ?high),
        lessThan(?value, 250), 
        stringEqualIgnoreCase(?t, ?phy_t),
        High_HRV(?high_hrv)
        -> HRVis(?hrv_inst, ?high_hrv)
        """
    )
    logger.debug("[checked] HRV rules set correctly")



def set_up_RR_rules(): 
    """
        This function creates the rules to categorize the RR of the actor into
        threshold ranges: 
        * Very Low 
        * Low 
        * Moderate (Normal) 
        * High 

        These threshold ranges change based on the Age group of the actor.
    """

    Imp().set_as_rule(
        f"""
        ActorState(?act_st), validAt(?act_st, ?t), StateHasThresholdProfile(?act_st, ?tp), 
        ActorStateHasPhysiologicalState(?act_st, ?rr_inst), RR(?rr_inst), 
        hasNumericalValue(?rr_inst, ?value), phyValidAt(?rr_inst, ?phy_t), 
        appliesRRLow(?tp, ?rr_low), hasThrValue(?rr_low, ?low), 
        greaterThanOrEqual(?value, 0), 
        lessThan(?value, ?low), 
        stringEqualIgnoreCase(?t, ?phy_t),
        Very_Low_RR(?vrl_rr)
        ->  RRis(?rr_inst, ?vrl_rr) 
        """
    )

    Imp().set_as_rule(
        f"""
        ActorState(?act_st), validAt(?act_st, ?t), StateHasThresholdProfile(?act_st, ?tp), 
        ActorStateHasPhysiologicalState(?act_st, ?rr_inst), RR(?rr_inst), 
        hasNumericalValue(?rr_inst, ?value), phyValidAt(?rr_inst, ?phy_t), 
        appliesRRLow(?tp, ?rr_low), hasThrValue(?rr_low, ?low), 
        appliesRRModerate(?tp, ?rr_mod), hasThrValue(?rr_mod, ?mod), 
        greaterThanOrEqual(?value, ?low),
        lessThan(?value, ?mod), 
        stringEqualIgnoreCase(?t, ?phy_t),
        Low_RR(?l_rr)
        ->  RRis(?rr_inst, ?l_rr)
        """
    )

    Imp().set_as_rule(
        f"""
        ActorState(?act_st), validAt(?act_st, ?t), StateHasThresholdProfile(?act_st, ?tp), 
        ActorStateHasPhysiologicalState(?act_st, ?rr_inst), RR(?rr_inst), 
        hasNumericalValue(?rr_inst, ?value), phyValidAt(?rr_inst, ?phy_t), 
        appliesRRModerate(?tp, ?rr_mod), hasThrValue(?rr_mod, ?mod), 
        appliesRRHigh(?tp, ?rr_high), hasThrValue(?rr_high, ?high), 
        greaterThanOrEqual(?value, ?mod),
        lessThan(?value, ?high), 
        stringEqualIgnoreCase(?t, ?phy_t),
        Moderate_RR(?mod_rr) 
        ->  RRis(?rr_inst, ?mod_rr)
        """
    )

    Imp().set_as_rule(
        f"""
        ActorState(?act_st), validAt(?act_st, ?t), StateHasThresholdProfile(?act_st, ?tp), 
        ActorStateHasPhysiologicalState(?act_st, ?rr_inst), RR(?rr_inst), 
        hasNumericalValue(?rr_inst, ?value), phyValidAt(?rr_inst, ?phy_t), 
        appliesRRHigh(?tp, ?rr_high), hasThrValue(?rr_high, ?high), 
        greaterThanOrEqual(?value, ?high),  
        lessThan(?value, 50), 
        stringEqualIgnoreCase(?t, ?phy_t),
        High_RR(?high_rr),
        ->  RRis(?rr_inst, ?high_rr)
        """
    )
    logger.debug("[checked] RR rules set correctly")


def set_up_SpO2_rules(): 
    """
    This function creates the rules to categorize the SPO2 of the actor into
    threshold ranges: 
    * Normal 
    * Slightly_Low
    * Critical

    These threshold ranges change based on the Age group of the actor.
    """
    Imp().set_as_rule(
        f"""
        ActorState(?act_st), validAt(?act_st, ?t), StateHasThresholdProfile(?act_st, ?tp), 
        ActorStateHasPhysiologicalState(?act_st, ?spo2_inst), SpO2(?spo2_inst), 
        hasNumericalValue(?spo2_inst, ?value), phyValidAt(?spo2_inst, ?phy_t), 
        appliesSpO2High(?tp, ?spo2_high), hasThrValue(?spo2_high, ?high), 
        greaterThanOrEqual(?value, ?high),
        lessThanOrEqual(?value, 100), 
        stringEqualIgnoreCase(?t, ?phy_t),
        Normal_SpO2(?n_spo2) 
        ->  SpO2is(?spo2_inst, ?n_spo2)
        """
    )

    Imp().set_as_rule(
        f"""
        ActorState(?act_st),validAt(?act_st, ?t), StateHasThresholdProfile(?act_st, ?tp), 
        ActorStateHasPhysiologicalState(?act_st, ?spo2_inst), SpO2(?spo2_inst), 
        hasNumericalValue(?spo2_inst, ?value), phyValidAt(?spo2_inst, ?phy_t), 
        appliesSpO2High(?tp, ?spo2_high), hasThrValue(?spo2_high, ?high), 
        appliesSpO2Moderate(?tp, ?spo2_mod), hasThrValue(?spo2_mod, ?mod), 
        greaterThanOrEqual(?value, ?mod),
        lessThan(?value, ?high), 
        stringEqualIgnoreCase(?t, ?phy_t),
        Low_SpO2(?l_spo2) 
        ->  SpO2is(?spo2_inst, ?l_spo2)
        """
    )

    Imp().set_as_rule(
        f"""
        ActorState(?act_st),validAt(?act_st, ?t), StateHasThresholdProfile(?act_st, ?tp), 
        ActorStateHasPhysiologicalState(?act_st, ?spo2_inst), SpO2(?spo2_inst), 
        hasNumericalValue(?spo2_inst, ?value), phyValidAt(?spo2_inst, ?phy_t), 
        appliesSpO2Moderate(?tp, ?spo2_mod), hasThrValue(?spo2_mod, ?mod),
        appliesSpO2Low(?tp, ?spo2_low), hasThrValue(?spo2_low, ?low),
        greaterThanOrEqual(?value, ?low),
        lessThan(?value, ?mod),  
        stringEqualIgnoreCase(?t, ?phy_t),
        Critical_SpO2(?c_spo2) 
        -> SpO2is(?spo2_inst, ?c_spo2)
        """
    )

    Imp().set_as_rule(
        f"""
        ActorState(?act_st),validAt(?act_st, ?t), StateHasThresholdProfile(?act_st, ?tp), 
        ActorStateHasPhysiologicalState(?act_st, ?spo2_inst), SpO2(?spo2_inst), 
        hasNumericalValue(?spo2_inst, ?value), phyValidAt(?spo2_inst, ?phy_t), 
        appliesSpO2Low(?tp, ?spo2_low), hasThrValue(?spo2_low, ?low),
        lessThan(?value, ?low),  
        stringEqualIgnoreCase(?t, ?phy_t),
        Critical_SpO2(?c_spo2) 
        -> SpO2is(?spo2_inst, ?c_spo2)
        """
    )
    logger.debug("[checked] SpO2 rules set correctly")



def set_up_Drowsiness_rules(): 
    """
        This function creates the rules to categorize the Drowsiness of the actor into
        threshold ranges based on Karolinska Sleep Scale (KSS)
        * Level_3 (actor is awake) 
        * Level_5 (actor is neither asleep or awake)
        * Level_7 (actor is asleep with no effor of waking up)
        * Level_9 (actor is asleep with effort of waking up)
    """
    Imp().set_as_rule(
        """
        ActorState(?act_state), validAt(?act_state, ?t),
        ActorStateHasPhysiologicalState(?act_state, ?dr_inst),Drowsiness(?dr_inst), 
        hasNumericalValue(?dr_inst, ?v), phyValidAt(?dr_inst, ?phy_t), 
        lessThanOrEqual(?v, 1),
        greaterThan(?v, 0), 
        stringEqualIgnoreCase(?t, ?phy_t)
        -> DrowsinessIs(?dr_inst, level_3_kss_instance) 
        """
    )
    
    Imp().set_as_rule(
        """
        ActorState(?act_state), validAt(?act_state, ?t),
        ActorStateHasPhysiologicalState(?act_state, ?dr_inst),Drowsiness(?dr_inst), 
        hasNumericalValue(?dr_inst, ?v), phyValidAt(?dr_inst, ?phy_t), 
        lessThanOrEqual(?v, 2), 
        greaterThan(?v, 1), 
        stringEqualIgnoreCase(?t, ?phy_t)
        ->  DrowsinessIs(?dr_inst, level_5_kss_instance) 
        """
    )
    
    Imp().set_as_rule(
        """
        ActorState(?act_state), validAt(?act_state, ?t),
        ActorStateHasPhysiologicalState(?act_state, ?dr_inst),Drowsiness(?dr_inst), 
        hasNumericalValue(?dr_inst, ?v), phyValidAt(?dr_inst, ?phy_t),
        lessThanOrEqual(?v, 3), 
        greaterThan(?v, 2), 
        stringEqualIgnoreCase(?t, ?phy_t)
        -> DrowsinessIs(?dr_inst, level_7_kss_instance) 
        """
    )

    Imp().set_as_rule(
        """
        ActorState(?act_state), validAt(?act_state, ?t),
        ActorStateHasPhysiologicalState(?act_state, ?dr_inst),Drowsiness(?dr_inst), 
        hasNumericalValue(?dr_inst, ?v), phyValidAt(?dr_inst, ?phy_t),
        lessThanOrEqual(?v, 4),
        greaterThan(?v, 3), 
        stringEqualIgnoreCase(?t, ?phy_t)
        ->  DrowsinessIs(?dr_inst, level_9_kss_instance) 
        """
    )
        
    logger.debug("[checked] Drowsiness rules set correctly")

    
