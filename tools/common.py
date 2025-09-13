import re
import uuid

from typing import Any
from owlready2 import Imp
from owlready2 import * 
from pandas import qcut
from datetime import datetime, timezone

def sync_reasoner(onto): 
    with onto: 
        sync_reasoner_pellet(infer_property_values=True)

def iso_format(datetime): 
    if isinstance(datetime, str):
        datetime = datetime.replace("-", " ")
        datetime = datetime.replace(":", " ") 
        datetime = datetime.split(" ")
        datetime = [int(value) for value in datetime]
        return datetime 
    return datetime.isoformat().replace("+00:00", "Z") 


def new_state(onto, actor, ts_iso): 

    if isinstance(ts_iso,list): 
        year = ts_iso[0]
        month = ts_iso[1] 
        day = ts_iso[2] 
        hour = ts_iso[3] 
        min = ts_iso[4] 
        sec = ts_iso[5] 
        ts_iso = datetime(
            year, month, day, hour, min, sec,
            tzinfo=timezone.utc
        ).isoformat() 
        ts_iso = ts_iso.replace("+00:00","")

    state_iri = f"DriverState_{uuid.uuid4().hex}"
    with onto: 
        state = onto.ActorState(state_iri) 
        state.StateOfActor = [actor] 
        state.validAt = [ts_iso] 

    return state 


def attach_values_to_observations(onto, obs_state, cols, row, idx):
    """
    Args: 
        - onto : the instance of the owlready2 ontology 
        - cols : the names of the data inside the dataset 
        - row : the information from the dataset 
        - idx : the index of the row inside the dataset 
    """

    #Pass health factors 
    obs_state.hasHR.append(row['HR'] if "HR" in cols and isinstance(row['HR'],int) else [-1])
    obs_state.hasHRV.append(row['HRV'] if "HRV" in cols and isinstance(row['HRV'],int) else [-1])
    obs_state.hasRR.append(row['RR'] if "RR" in cols and isinstance(row['RR'],int) else [-1])
    obs_state.hasSpO2.append(row["SPO2"] if "SPO2" in cols and isinstance(row['SPO2'],int) else [-1])
    obs_state.hasDrowsy.append(row['DROWSY'] if "DROWSY" in cols and isinstance(row['DROWSY'],int) else [-1])

    # Pass Actor's Characteristics
    obs_state.hasAccessories.append(row['Accessories'] if "Accessories" in cols and isinstance(row['Accessories'],str)  else [-1])
    obs_state.hasAge.append(row['Age'] if "Age" in cols and isinstance(row['Age'],int) else [-1])
    obs_state.hasSex.append(row['Sex'] if "Sex" in cols and isinstance(row['Sex'],str) else [-1])
    obs_state.hasFaceCharacteristics.append(row["Characteristics"] if "Characteristics" in cols and isinstance(row['Characteristics'],str) else [-1])
    obs_state.hasDemographic.append(row["Demographic"] if "Demographic" in cols and isinstance(row['Demographic'],str)  else [-1])

    return obs_state


def swrl_rules_in(onto): 
    return [r for r in Imp.instances() if r.namespace==onto] 


def has_rule_named(onto, name): 
    return onto.search_one(iri="*#" + name)  is not None 


def obs_to_PHY_instance(obs_state, instance:Any, property_name:Any): 
    inst_name = instance.name.split('_')[0] 
    instance_property = getattr(instance, property_name)

    if inst_name == "spo2": 
        instance_property.append(int(obs_state.hasSpO2.pop(0)))
    elif inst_name == "hr": 
        instance_property.append(int(obs_state.hasHR.pop(0)))
    elif inst_name == 'rr': 
        instance_property.append(int(obs_state.hasRR.pop(0)))
    elif inst_name == 'hrv': 
        instance_property.append(int(obs_state.hasHRV.pop(0))) 
    elif inst_name == 'sex': 
        instance_property.append(obs_state.hasSex.pop(0)) 
    elif inst_name == 'demographic' : 
        instance_property.append(obs_state.hasDemographic.pop(0))
    elif inst_name == 'accessories': 
        instance_property.append(obs_state.hasAccessories.pop(0)) 
    elif inst_name == 'facecharacteristics': 
        instance_property.append(obs_state.hasFaceCharacteristics.pop(0))
    elif inst_name == 'drowsiness': 
        instance_property.append(int(obs_state.hasDrowsy.pop(0))) 
    elif inst_name == 'age': 
        if hasattr(instance, 'hasAgeValue'):
            instance_property = getattr(instance, 'hasAgeValue')
            instance_property.append(int(obs_state.hasAge.pop(0))) 


def create_Physiological_inds(onto): 

    hr_instance = onto.HR('hr_instance') 
    hrv_instance = onto.HRV('hrv_instance') 
    rr_instance = onto.RR('rr_instance') 
    spo2_instance = onto.SpO2('spo2_instance') 
    drowsiness_instance = onto.Drowsiness('drowsiness_instance')
    fatigue_instance = onto.Fatigue('fatigue_instance') 
    attention_instance = onto.AttentionLevels('attention_instance')
    unresponsiveness = onto.Unresponsiveness('unresponsiveness') 
    return {
            'hr': hr_instance, 
            'hrv': hrv_instance, 
            'rr': rr_instance, 
            'spo2': spo2_instance, 
            'drowsiness': drowsiness_instance, 
            'fatigue': fatigue_instance, 
            'attention': attention_instance, 
            'unresponsiveness':unresponsiveness 
    }



def create_Actor_inds(onto): 
    accessories_instance = onto.Accessories('accessories_instance') 
    age_instance = onto.Age('age_instance') 
    demographic_instance = onto.Demographic('demographic_instance') 
    eye_state = onto.EyeState('eye_state') 
    facecharacteristics = onto.FaceCharacteristics('facecharacteristics_instance') 
    mouth_state = onto.MouthState('mouth_state')
    sex_instance = onto.Sex('sex_instance') 

    return {
            "accessories": accessories_instance, 
            "age" : age_instance, 
            "demographic" : demographic_instance, 
            "eye_state" : eye_state, 
            "facecharacteristics": facecharacteristics, 
            "mouth_state": mouth_state, 
            "sex": sex_instance 
    }


def attach_obs_to_phy_state(obs_state, phy_vocab): 
    if phy_vocab['hr'] not in obs_state.ObsIsDividedIntoPhS:
        obs_state.ObsIsDividedIntoPhS.append(phy_vocab['hr'])

    if phy_vocab['hrv'] not in obs_state.ObsIsDividedIntoPhS:
        obs_state.ObsIsDividedIntoPhS.append(phy_vocab['hrv'])

    if phy_vocab['rr'] not in obs_state.ObsIsDividedIntoPhS:
        obs_state.ObsIsDividedIntoPhS.append(phy_vocab['rr'])

    if phy_vocab['spo2'] not in obs_state.ObsIsDividedIntoPhS:
            obs_state.ObsIsDividedIntoPhS.append(phy_vocab['spo2'])

    if phy_vocab['drowsiness'] not in obs_state.ObsIsDividedIntoPhS:
            obs_state.ObsIsDividedIntoPhS.append(phy_vocab['drowsiness'])
            
    # if phy_vocab['fatigue'] not in obs_state.ObsIsDividedIntoPhS:
    #     obs_state.ObsIsDividedIntoPhS.append(phy_vocab['fatigue'])
    #
    # if phy_vocab['attention'] not in obs_state.ObsIsDividedIntoPhS:
    #         obs_state.ObsIsDividedIntoPhS.append(phy_vocab['attention'])
    #
    # if phy_vocab['unresponsiveness'] not in obs_state.ObsIsDividedIntoPhS:
    #         obs_state.ObsIsDividedIntoPhS.append(phy_vocab['unresponsiveness'])
    #
    return obs_state


def attach_obs_to_actor_state(obs_state, actor_vocab): 

    if actor_vocab['accessories'] not in obs_state.ObsIsDividedIntoActor: 
        obs_state.ObsIsDividedIntoActor.append(actor_vocab['accessories']) 
    if actor_vocab['age'] not in obs_state.ObsIsDividedIntoActor: 
        obs_state.ObsIsDividedIntoActor.append(actor_vocab['age']) 
    if actor_vocab['demographic'] not in obs_state.ObsIsDividedIntoActor: 
        obs_state.ObsIsDividedIntoActor.append(actor_vocab['demographic']) 
    if actor_vocab['facecharacteristics'] not in obs_state.ObsIsDividedIntoActor: 
        obs_state.ObsIsDividedIntoActor.append(actor_vocab['facecharacteristics']) 
    if actor_vocab['sex'] not in obs_state.ObsIsDividedIntoActor: 
        obs_state.ObsIsDividedIntoActor.append(actor_vocab['sex']) 

    return obs_state 


def capture_thr_values_from_individuals(onto, thr_prop_name='hasThrValue'): 

    RANGE = {"low":"low", "high":"high", "moderate":"moderate"}
    TEMP = {"cold":"cold", "hot":"hot", "moderate":"moderate"} 
    BIO_SEX = {"female":"female", "male":"male"}
    AGE = {"young":"young", "middle_aged":"middle-aged", "elderly":"elderly"}
    PHY = {"hr":"hr", "hrv":"hrv", "rr":"rr", "spo2":"spo2"}

    TAG = re.compile(r"^(?P<temp>[^_]+)_(?P<range>[^_]+)_(?P<phy>[^_]+)_(?P<age>[^_]+)_(?P<bsex>[^_]+)$")

    thr_values = {}

    def norm(token, table): 
        t = token.lower().strip() 
        return table.get(t, t) 

    def safe_first(lst): 
        return lst[0] if lst else None 

    exclude = "ThresholdProfile" 
    for cls in onto.Thresholds.subclasses(): 
        if cls.name == exclude: continue 
        for indi in cls.instances(): 
            name = indi.name 
            m = TAG.match(name) 
            if not m: continue 

            temp = norm(m.group("temp"), TEMP) 
            age = norm(m.group("age"), AGE) 
            bsex = norm(m.group("bsex"), BIO_SEX) 
            rng = norm(m.group("range"), RANGE) 
            phy = norm(m.group("phy"), PHY) 

            thr_property = getattr(onto, thr_prop_name, None) 

            val = safe_first(getattr(indi, thr_prop_name, [])) if thr_property else None
            if val is None : continue 

            try: 
                val = int(val) 
            except (TypeError,ValueError): 
                continue 

            key = (age, bsex, temp) 
            bucket = thr_values.setdefault(key,{})

            bucket_phy =  bucket.setdefault(phy, {}) 
            bucket_phy[rng] = val

    return thr_values


def parse_thr_profiles(onto,thr_values): 

    for (age, sex, temp),metric in thr_values.items(): 
        # If you find the attribute (instance) use it, if not create it. 
        tp = getattr(onto, f"tp_{age}_{sex}_{temp}", None) or onto.ThresholdProfile(f"tp_{age}_{sex}_{temp}") 

        def ind(name): 
            return getattr(onto, name, None)
        
        for bw in ("low","moderate","high"): 

            if bw == "low":
                hr_low = ind(f"{temp}_{bw}_hr_{age}_{sex}")
                if hr_low: onto.appliesHRLow[tp].append(hr_low) 
                hrv_low = ind(f"{temp}_{bw}_hrv_{age}_{sex}")
                if hrv_low: onto.appliesHRVLow[tp].append(hrv_low) 
                rr_low = ind(f"{temp}_{bw}_rr_{age}_{sex}")
                if rr_low: onto.appliesRRLow[tp].append(rr_low) 
                spo2_low = ind(f"{temp}_{bw}_spo2_{age}_{sex}")
                if spo2_low: onto.appliesSPO2Low[tp].append(spo2_low) 

            elif bw == "moderate" : 
                hr_mod = ind(f"{temp}_{bw}_hr_{age}_{sex}")
                if hr_mod: onto.appliesHRModerate[tp].append(hr_mod) 
                hrv_mod = ind(f"{temp}_{bw}_hrv_{age}_{sex}")
                if hrv_mod: onto.appliesHRVModerate[tp].append(hrv_mod) 
                rr_mod = ind(f"{temp}_{bw}_rr_{age}_{sex}")
                if rr_mod: onto.appliesRRModerate[tp].append(rr_mod) 
                spo2_mod = ind(f"{temp}_{bw}_spo2_{age}_{sex}")
                if spo2_mod: onto.appliesSPO2Moderate[tp].append(spo2_mod) 


            elif bw == "high" : 
                hr_high = ind(f"{temp}_{bw}_hr_{age}_{sex}")
                if hr_high: onto.appliesHRHigh[tp].append(hr_high) 
                hrv_high = ind(f"{temp}_{bw}_hrv_{age}_{sex}")
                if hrv_high: onto.appliesHRVHigh[tp].append(hrv_high) 
                rr_high = ind(f"{temp}_{bw}_rr_{age}_{sex}")
                if rr_high: onto.appliesRRHigh[tp].append(rr_high) 
                spo2_high = ind(f"{temp}_{bw}_spo2_{age}_{sex}")
                if spo2_high: onto.appliesSPO2High[tp].append(spo2_high) 





   


def pick_appropriate_profile_state(onto, actor_state, age_group, sex_group, temp_group): 

    tp_name = f"tp_{age_group}_{sex_group}_{temp_group}"
    tp = getattr(onto, tp_name,None)
    if tp is None: raise ValueError("Invalid ThresholdProfile instance name")

    actor_state.StateHasThresholdProfile = [tp]









