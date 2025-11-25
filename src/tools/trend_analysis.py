import pdb

def detect_T1_starting_drowsy(last_labels) -> bool:
    # last_labels: list of 3 dicts, oldest → newestact_st
    return all(
        last_labels[lab]["fatigue"] == "awake" and
        last_labels[lab]["attention"] == "inattentive"
        for lab in last_labels
    )


def detect_T2_drowsy_to_inattentive(last_labels) -> bool:
    # last_labels: list of 3 dicts, oldest → newest

    return all(
        last_labels[lab]["fatigue"] == "drowsinesssuspected" and
        last_labels[lab]["attention"] == "undefined"
        for lab in last_labels
    )


def detect_T3_sleep_unresp_inat(last_labels) -> bool:
    # last_labels: list of 3 dicts, oldest → newest
    return all(
        last_labels[lab]["fatigue"] == "sleep" 
        for lab in last_labels
    )


def detect_T4_sleep_unresp_inat(last_labels) -> bool:
    # last_labels: list of 3 dicts, oldest → newest
    return all(
        last_labels[lab]["fatigue"] == "drowsinesssuspected" and
        last_labels[lab]["attention"] == "attentive"
        for lab in last_labels
    )


def detect_T5_drowsy_inatt_to_imminent(last_labels) -> bool: 
    return all(
         last_labels[lab]["fatigue"] == "drowsinesssuspected" and
         last_labels[lab]["attention"] == "inattentive" and 
         last_labels[lab]["unresponsiveness"] == "responsive"
        for lab in last_labels
    )


def detect_T6_stable_safe(last_labels) -> bool: 
    return all(
         last_labels[lab]["fatigue"] == "awake" and
         last_labels[lab]["attention"] == "attentive" and 
         last_labels[lab]["unresponsiveness"] == "responsive"
        for lab in last_labels
    )


def detect_T7_persistent_imminent_to_unresponsive(last_labels) -> bool: 
    return all(
         last_labels[lab]["attention"] == "inattentive" and 
         last_labels[lab]["unresponsiveness"] == "imminent"
        for lab in last_labels
    )


def detect_T8_undefined_risky(last_labels) -> bool: 
    return all(
         last_labels[lab]["fatigue"] == "undefinedstate" and
         last_labels[lab]["attention"] == "inattentive"  
        for lab in last_labels
    )


def trends(): 
    return {
        "T1": detect_T1_starting_drowsy, 
        "T2": detect_T2_drowsy_to_inattentive, 
        "T3": detect_T3_sleep_unresp_inat, 
        "T4": detect_T4_sleep_unresp_inat, 
        "T5": detect_T5_drowsy_inatt_to_imminent, 
        "T6": detect_T6_stable_safe, 
        "T7": detect_T7_persistent_imminent_to_unresponsive, 
        "T8": detect_T8_undefined_risky
    }


def analysis(trends:dict, data:dict): 

    for ind, trend in enumerate(trends): 

        flag = trends[trend](data)
        if not flag: 
            continue 
        act_state = data.get(-1) 

        if act_state is None: continue

        if ind == 0 : 
            act_state.hasFatigueTrend = "fatigue_starting_drowsy"
        elif ind == 1: 
            act_state.hasAttentionTrend = "attention_drowsy_to_inattentive"
        elif ind == 4: 
            act_state.hasUnresponsivenessTrend = "unresp_escalate_imminent"
        elif ind == 5: 
            act_state.hasUnresponsivenessTrend = "unresp_stable_safe"
        elif ind == 6: 
            act_state.hasUnresponsivenessTrend = "unresp_persistent_imminent"
        elif ind == 7: 
            act_state.hasUnresponsivenessTrend = "unresp_undefined_risky"
            


def gci_trends(onto): 
    class StartingDrowsyFatigueTrend(onto.ActorState): 
        equivalent_to = [(onto.ActorState & onto.hasFatigueTrend.value("fatigue_starting_drowsy"))]
        is_a = [(onto.ActorStateHasFatigue.value(onto.drowsinesssuspected_instance))]

    # class DrowsyToInattentive(onto.ActorState): 
    #     equivalent_to = [(
    #         onto.ActorState 
    #         & onto.hasAttentionTrend.value('attention_drowsy_to_inattentive')
    #     )]
    #
    #     is_a = [(
    #         onto.ActorStateHasAttention.value(onto.inattentive_instance) 
    #     )]
    #
    # class SleepUnresponsiveInattentive(onto.ActorState): 
    #     equivalent_to = [(
    #         onto.ActorState 
    #         & onto.ActorStateHasFatigue.value(onto.sleep_instance)
    #     )]
    #     is_a = [
    #         onto.ActorStateHasAttention.value(onto.inattentive_instance), 
    #         onto.ActorStateHasUnresponsiveness.value(onto.unresponsive_instance)
    #     ]
    #
    # class DrowsyAtRisk(onto.ActorState): 
    #     equivalent_to = [(
    #         onto.ActorState
    #         & onto.ActorStateHasFatigue.value(onto.drowsinesssuspected_instance)
    #         & onto.ActorStateHasAttention.value(onto.attentive_instance)
    #     )]
    #
    #     is_a = [(
    #         onto.ActorStateHasUnresponsiveness.value(onto.undefined_atrisk_instance) 
    #     )]
    #
    # class DrowsyToImminent(onto.ActorState): 
    #     equivalent_to = [(
    #         onto.ActorState
    #         & onto.hasUnresponsivenessTrend.value("unresp_escalate_imminent")
    #     )]
    #
    #     is_a = [(
    #         onto.ActorStateHasUnresponsiveness.value(onto.imminent_instance) 
    #     )]
    #
    # class StableSafe(onto.ActorState): 
    #     equivalent_to = [(
    #         onto.ActorState
    #         & onto.hasUnresponsivenessTrend.value("unresp_stable_ref")
    #     )]
    #
    #     is_a = [(
    #         onto.ActorStateHasUnresponsiveness.value(onto.responsive_instance) 
    #     )]
    #
    # class PersistentImminentUnresponsive(onto.ActorState): 
    #     equivalent_to = [(
    #         onto.ActorState
    #         & onto.hasUnresponsivenessTrend.value("unresp_persistent_imminent")
    #     )]
    #
    #     is_a = [(
    #         onto.ActorStateHasUnresponsiveness.value(onto.unresponsive_instance) 
    #     )]
    #
    # class UndefinedRisky(onto.ActorState): 
    #     equivalent_to = [(
    #         onto.ActorState
    #         & onto.hasUnresponsivenessTrend.value("unresp_undefined_risky")
    #     )]
    #
    #     is_a = [(
    #         onto.ActorStateHasUnresponsiveness.value(onto.undefined_atrisk_instance) 
    #     )]










