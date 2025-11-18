import pdb
import os 
import re
import uuid

from typing import Any
from owlready2 import Imp
from owlready2 import * 
from datetime import datetime, timezone


def get_assets_path(parent_path=None): 
    parent_dir = parent_path if parent_path is not None else os.getcwd()
    assets_dir = os.path.join(parent_dir, "assets") 
    os.makedirs(assets_dir, exist_ok=True)
    return assets_dir


def iso_format(datetime): 
    if isinstance(datetime, str):
        datetime = datetime.replace("-", " ")
        datetime = datetime.replace(":", " ") 
        datetime = datetime.split(" ")
        datetime = [int(value) for value in datetime]
        return datetime 
    return datetime.isoformat().replace("+00:00", "Z") 


def get_ts_iso_value(ts_iso): 

    ts_iso = '_'.join(map(str, ts_iso))
    return ts_iso


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
        state.StateOfActor = actor 
        state.validAt = [ts_iso]
        state.StateHasThresholdProfile = None
        state.prevState = None

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


def create_Physiological_inds(onto, ts_iso): 

    hr_instance = onto.HR(f'hr_instance_{ts_iso}') 
    hr_instance.phyValidAt.append(ts_iso)
    hrv_instance = onto.HRV(f'hrv_instance_{ts_iso}') 
    hrv_instance.phyValidAt.append(ts_iso)
    rr_instance = onto.RR(f'rr_instance_{ts_iso}') 
    rr_instance.phyValidAt.append(ts_iso)
    spo2_instance = onto.SpO2(f'spo2_instance_{ts_iso}') 
    spo2_instance.phyValidAt.append(ts_iso)
    drowsiness_instance = onto.Drowsiness(f'drowsiness_instance_{ts_iso}')
    drowsiness_instance.phyValidAt.append(ts_iso)


    return {
            'hr': hr_instance, 
            'hrv': hrv_instance, 
            'rr': rr_instance, 
            'spo2': spo2_instance, 
            'drowsiness': drowsiness_instance, 

    }



def create_Actor_inds(onto, ts_iso): 
    accessories_instance = onto.Accessories(f'accessories_instance_{ts_iso}') 
    age_instance = onto.Age(f'age_instance_{ts_iso}') 
    demographic_instance = onto.Demographic(f'demographic_instance_{ts_iso}') 
    eye_state = onto.EyeState(f'eye_state_{ts_iso}') 
    facecharacteristics = onto.FaceCharacteristics(f'facecharacteristics_instance_{ts_iso}') 
    mouth_state = onto.MouthState(f'mouth_state_{ts_iso}')
    sex_instance = onto.Sex(f'sex_instance_{ts_iso}') 
    temp_instance = onto.WeatherCondition(f'temp_instance_{ts_iso}')

    return {
            "accessories": accessories_instance, 
            "age" : age_instance, 
            "demographic" : demographic_instance, 
            "eye_state" : eye_state, 
            "facecharacteristics": facecharacteristics, 
            "mouth_state": mouth_state, 
            "sex": sex_instance, 
            "temp": temp_instance
    }


def create_Label_ind(onto, ts_iso):
    return onto.Label(f'label_{ts_iso}')


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
                if spo2_low: onto.appliesSpO2Low[tp].append(spo2_low) 

            elif bw == "moderate" : 
                hr_mod = ind(f"{temp}_{bw}_hr_{age}_{sex}")
                if hr_mod: onto.appliesHRModerate[tp].append(hr_mod) 
                hrv_mod = ind(f"{temp}_{bw}_hrv_{age}_{sex}")
                if hrv_mod: onto.appliesHRVModerate[tp].append(hrv_mod) 
                rr_mod = ind(f"{temp}_{bw}_rr_{age}_{sex}")
                if rr_mod: onto.appliesRRModerate[tp].append(rr_mod) 
                spo2_mod = ind(f"{temp}_{bw}_spo2_{age}_{sex}")
                if spo2_mod: onto.appliesSpO2Moderate[tp].append(spo2_mod) 


            elif bw == "high" : 
                hr_high = ind(f"{temp}_{bw}_hr_{age}_{sex}")
                if hr_high: onto.appliesHRHigh[tp].append(hr_high) 
                hrv_high = ind(f"{temp}_{bw}_hrv_{age}_{sex}")
                if hrv_high: onto.appliesHRVHigh[tp].append(hrv_high) 
                rr_high = ind(f"{temp}_{bw}_rr_{age}_{sex}")
                if rr_high: onto.appliesRRHigh[tp].append(rr_high) 
                spo2_high = ind(f"{temp}_{bw}_spo2_{age}_{sex}")
                if spo2_high: onto.appliesSpO2High[tp].append(spo2_high) 


def pick_appropriate_profile_state(onto, actor_state, age_group, sex_group, temp_group): 

    tp_name = f"tp_{age_group}_{sex_group}_{temp_group}"
    tp = getattr(onto, tp_name,None)
    if tp is None: raise ValueError("Invalid ThresholdProfile instance name")

    actor_state.StateHasThresholdProfile = [tp]


def new_actor_state(onto, actor, ts_iso:str, last_state:Any): 
    actor_state = new_state(
            onto=onto, 
            actor=actor, 
            ts_iso=ts_iso) 

    if last_state is not None: 
        actor_state.prevState = [last_state.get(actor.hasUniqueIdentifier[0])]

    actor.ActorhasState.append(actor_state)

    return actor_state


def check_spo2(onto): 
    for st in onto.ActorState.instances():
        spo2s = [p for p in onto.ActorStateHasPhysiologicalState[st] if isinstance(p, onto.SpO2)]
        if len(spo2s) != 1: 
            continue
        spo2 = spo2s[0]
        # classified via SpO2is?
        if not onto.SpO2is[spo2]:
            print("UNCLASSIFIED:", st.name, "| SpO2:", spo2.name)
            # dump bindings used by the rule
            print("  state time:", list(onto.validAt[st]))
            print("  spo2 time:", list(getattr(onto, "phyValidAt")[spo2] if hasattr(onto, "phyValidAt") else onto.validAt[spo2]))
            print("  spo2 numeric:", list(getattr(onto, "hasNumericalValue")[spo2] or getattr(onto, "hasNumericValue")[spo2]))
            tp = next(iter(onto.StateHasThresholdProfile[st]))
            print("  tp:", tp.name)
            lows = list(onto.appliesSpO2Low[tp])
            mods = list(onto.appliesSpO2Moderate[tp])
            highs = list(onto.appliesSpO2High[tp])
            print("  low thr:", [(x.name, list(onto.hasThrValue[x])) for x in lows])
            print("  mod thr:", [(x.name, list(onto.hasThrValue[x])) for x in mods])
            print("  high thr:", [(x.name, list(onto.hasThrValue[x])) for x in highs])
            


def check_elderly_state(onto): 
    # Helper to resolve by local name
    def ent(name):
        return getattr(onto, name, None)

# 1) Locate the tp and its threshold links
    tp = ent("tp_elderly_male_cold")
    print("TP exists:", bool(tp), tp)

    applies_low  = getattr(onto, "appliesSpO2Low",  None)
    applies_mod  = getattr(onto, "appliesSpO2Moderate",  None)
    applies_high = getattr(onto, "appliesSpO2High",  None)
    has_thr      = getattr(onto, "hasThrValue", None)

    print("Props present:", bool(applies_low), bool(applies_mod), bool(applies_high), bool(has_thr))

    def safe_vals(thr_ind):
        if not thr_ind or not has_thr: return []
        try:
            return list(has_thr[thr_ind])
        except Exception:
            return []

    lows = list(applies_low[tp]) if applies_low and tp else []
    mods = list(applies_mod[tp]) if applies_mod and tp else []
    highs= list(applies_high[tp]) if applies_high and tp else []

    print("Low thresholds:", [(x.name, safe_vals(x)) for x in lows])
    print("Mod thresholds:", [(x.name, safe_vals(x)) for x in mods])
    print("High thresholds:", [(x.name, safe_vals(x)) for x in highs])

# 2) Dump SWRL rules that mention SpO2 and 'High' to check head/body correctness

    rules = list(onto.rules()) 
    print("\nTotal rules:", len(rules))
    spo2_rules = []
    for r in rules:
        txt = r.get_name()
        if not txt: 
            continue
        stxt = str(txt)
        if ("SpO2" in stxt or "spo2" in stxt) and ("Normal" in stxt or "normal" in stxt):
            
            spo2_rules.append((r.name, stxt))

    print("SpO2 'normal' rules found:", len(spo2_rules))
    for name, txt in spo2_rules:
        print("\n==", name, "==")
        print(txt)

# 3) Verify High_SpO2 class vs individual existence
    High_SpO2 = ent("Normal_SpO2")
    print("\nHigh_SpO2 entity:", High_SpO2, "is class:", getattr(High_SpO2, "is_a", None) is not None and hasattr(High_SpO2, "instances"))





















