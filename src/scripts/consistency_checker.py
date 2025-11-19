# Ontology consistency checker for Owlready2
from src.tools.common import get_assets_path

import sys, json
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Tuple, Optional, Any, Set

try:
    from owlready2 import get_ontology, Thing, default_world, onto_path
except Exception as e:

    print("Owlready2 is required. Install with `pip install owlready2`. Error:", e)
    raise

CHECK_VERSION = "1.0.0"


def _suffix_lookup(onto, name: str):
    """
    Find an entity in the ontology by suffix (local name).
    Returns the first matching entity or None.
    """
    if name is None:
        return None
    # Direct attribute if exists
    if hasattr(onto, name):
        return getattr(onto, name)
    # Fallback: search by IRI suffix among ontology entities

    lname = name.lower()
    for e in list(onto.classes()) + list(onto.object_properties()) + list(onto.data_properties()) + list(onto.individuals()):
        try:
            if e.name.lower() == lname:

                return e
        except Exception:
            pass
        try:
            iri = e.iri if hasattr(e, "iri") else str(e)
            if iri and iri.lower().endswith("#" + lname):
                return e
        except Exception:
            pass
    return None


def _get_first(obj_list):
    if not obj_list:
        return None
    return obj_list[0]


def _local_name(x) -> str:
    try:

        return x.name

    except Exception:
        s = str(x)
        if "#" in s:
            return s.rsplit("#", 1)[-1].strip(">/")
        return s


def run_consistency_checks(
    onto_path_or_file: str,

    config: Optional[Dict[str, Any]] = None,
    verbose: bool = True,
) -> Dict[str, Any]:
    """
    Run a suite of structural + conceptual consistency checks on an in-cabin ontology.
    
    Parameters
    ----------

    onto_path_or_file : str
        Path to the .owl/.rdf ontology file.
    config : dict (optional)
        Mapping of ontology entity local names to use in checks. Provide at least the following keys (local names as strings):
          - "ActorState": class
          - "Actor": class
          - "stateOfActor": object property (ActorState -> Actor)
          - "validAt": data property (on ActorState and physio individuals)
          - "ActorStateHasPhysiologicalState": object property (ActorState -> physio individual)
          - "HR": class; "HRV": class; "RR": class; "SpO2": class

          - Level partitions (class names) per channel, e.g. "HR_levels": ["Very_Low_HR","Low_HR","Moderate_HR","High_HR"]

          - Alternatively, label properties: "HRis", "HRVis", "RRis", "SpO2is" (object properties to level individuals)
          - Fatigue/Attention/Unresponsiveness:
              "ActorStateHasFatigue", "Fatigue", "FatigueIs"
              "ActorStateHasAttention", "AttentionLevels", "AttentionIs"
              "ActorStateHasUnresponsiveness", "Unresponsiveness", "UnresponsivenessIs"
          - Accessories / temperature (optional): "ActorStateHasAccessories", "Accessories", "AccessoryBelongsToGroup",
              "denotesTemperature", "TemperatureGroup"
    verbose : bool
        If True, prints a human-readable report.
        
    Returns
    -------
    dict
        A dictionary with check results and details.
    """
    report: Dict[str, Any] = {"version": CHECK_VERSION, "checks": {}, "notes": []}

    # Load ontology
    onto_file = Path(onto_path_or_file)
    if not onto_file.exists():
        raise FileNotFoundError(f"Ontology file not found: {onto_file}")
    onto_dir = str(onto_file.parent.resolve())
    if onto_dir not in onto_path:
        onto_path.append(onto_dir)

    onto = get_ontology(onto_file.as_uri()).load()

    # Default config guesses (you can override via config param)
    cfg = {
        "ActorState": "ActorState",
        "Actor": "Actor",
        "stateOfActor": "stateOfActor",
        "validAt": "validAt",
        "ActorStateHasPhysiologicalState": "ActorStateHasPhysiologicalState",
        "HR": "HR",
        "HRV": "HRV",
        "RR": "RR",
        "SpO2": "SpO2",
        # partitions as classes (optional)
        "HR_levels": ["Very_Low_HR", "Low_HR", "Moderate_HR", "High_HR"],
        "HRV_levels": ["Very_Low_HRV", "Low_HRV", "Moderate_HRV", "High_HRV"],
        "RR_levels": ["Very_Low_RR", "Low_RR", "Moderate_RR", "High_RR"],
        "SpO2_levels": ["Critical_SpO2", "Low_SpO2", "Normal_SpO2"],
        # alternative: label properties (to individuals)
        "HRis": "HRis",
        "HRVis": "HRVis",
        "RRis": "RRis",
        "SpO2is": "SpO2is",
        # classifications
        "ActorStateHasFatigue": "ActorStateHasFatigue",
        "Fatigue": "Fatigue",
        "FatigueIs": "FatigueIs",
        "ActorStateHasAttention": "ActorStateHasAttention",
        "AttentionLevels": "AttentionLevels",
        "AttentionIs": "AttentionIs",
        "ActorStateHasUnresponsiveness": "ActorStateHasUnresponsiveness",
        "Unresponsiveness": "Unresponsiveness",
        "UnresponsivenessIs": "UnresponsivenessIs",
        # accessories (optional)
        "ActorStateHasAccessories": "ActorStateHasAccessories",
        "Accessories": "Accessories",
        "AccessoryBelongsToGroup": "AccessoryBelongsToGroup",
        "denotesTemperature": "DenotesTemperature",
        "TemperatureGroup": "TemperatureGroup",
    }
    if config:
        cfg.update(config)

    # Resolve entities by local name/suffix
    def ent(name):
        return _suffix_lookup(onto, name)

    ActorState = ent(cfg["ActorState"])
    Actor = ent(cfg["Actor"])
    stateOfActor = ent(cfg["stateOfActor"])
    validAt = ent(cfg["validAt"])
    hasPhysio = ent(cfg["ActorStateHasPhysiologicalState"])

    HR = ent(cfg["HR"]); HRV = ent(cfg["HRV"]); RR = ent(cfg["RR"]); SpO2 = ent(cfg["SpO2"])

    HRis = ent(cfg.get("HRis")); HRVis = ent(cfg.get("HRVis")); RRis = ent(cfg.get("RRis")); SpO2is = ent(cfg.get("SpO2is"))
    Fatigue = ent(cfg["Fatigue"]); FatigueIs = ent(cfg["FatigueIs"]); HasFatigue = ent(cfg["ActorStateHasFatigue"])
    AttentionLevels = ent(cfg["AttentionLevels"]); AttentionIs = ent(cfg["AttentionIs"]); HasAttention = ent(cfg["ActorStateHasAttention"])
    Unresp = ent(cfg["Unresponsiveness"]); UnrespIs = ent(cfg["UnresponsivenessIs"]); HasUnresp = ent(cfg["ActorStateHasUnresponsiveness"])


    # Level partitions (classes) if present
    partitions = {

        "HR": [ent(n) for n in cfg.get("HR_levels", [])],
        "HRV": [ent(n) for n in cfg.get("HRV_levels", [])],

        "RR": [ent(n) for n in cfg.get("RR_levels", [])],
        "SpO2": [ent(n) for n in cfg.get("SpO2_levels", [])],

    }

    # Helper: collect states
    actor_states = list(ActorState.instances()) if ActorState else []
    report["counts"] = {
        "ActorStates": len(actor_states),
        "Actors": len(Actor.instances()) if Actor else None,
        "HR": len(HR.instances()) if HR else None,
        "HRV": len(HRV.instances()) if HRV else None,
        "RR": len(RR.instances()) if RR else None,
        "SpO2": len(SpO2.instances()) if SpO2 else None,
    }

    # 1) Exactly one state per (Actor, validAt) and no duplicates
    dupe_keys: Counter = Counter()
    missing_actor = []
    missing_time = []

    for st in actor_states:

        actor = _get_first(stateOfActor[st]) if stateOfActor else None
        t = _get_first(validAt[st]) if validAt else None
        if actor is None:
            missing_actor.append(st)
        if t is None:
            missing_time.append(st)
        if actor is not None and t is not None:
            dupe_keys[(actor, t)] += 1
    duplicates = [(k, c) for k, c in dupe_keys.items() if c > 1]

    report["checks"]["state_identity"] = {

        "missing_actor_states": [_local_name(s) for s in missing_actor],
        "missing_time_states": [_local_name(s) for s in missing_time],

        "duplicate_keys_count": len(duplicates),
        "duplicates": [(_local_name(a), t, c) for (a, t), c in duplicates],
    }

    # 2) No orphan states
    orphans = [_local_name(s) for s in actor_states if not stateOfActor or not stateOfActor[s]]
    report["checks"]["orphans"] = {"count": len(orphans), "states": orphans}

    # 3) Time alignment inside a state
    time_mismatch: List[Tuple[str, str, Any, Any]] = []
    if hasPhysio and validAt:

        for st in actor_states:
            t_state = _get_first(validAt[st])
            for p in hasPhysio[st]:
                t_p = _get_first(validAt[p]) if validAt[p] else None
                if t_state is not None and t_p is not None and t_state != t_p:
                    time_mismatch.append((_local_name(st), _local_name(p), t_state, t_p))
    report["checks"]["time_alignment"] = {"mismatches": time_mismatch, "count": len(time_mismatch)}

    # 4) Exactly one HR / HRV / RR / SpO2 per state
    def _per_state_counts(st):

        cats = {"HR": 0, "HRV": 0, "RR": 0, "SpO2": 0}

        phys = list(hasPhysio[st]) if hasPhysio else []
        for p in phys:

            types = {cls for cls in p.is_a if hasattr(cls, "ancestors")}  # Owlready2 classes
            if HR and HR in types or any(HR and HR in c.ancestors() for c in types):
                cats["HR"] += 1
            if HRV and HRV in types or any(HRV and HRV in c.ancestors() for c in types):

                cats["HRV"] += 1
            if RR and RR in types or any(RR and RR in c.ancestors() for c in types):
                cats["RR"] += 1
            if SpO2 and SpO2 in types or any(SpO2 and SpO2 in c.ancestors() for c in types):

                cats["SpO2"] += 1
        return cats

    per_state_channel_issues = []
    for st in actor_states:
        c = _per_state_counts(st)
        bad = {k: v for k, v in c.items() if v != 1}
        if bad:
            per_state_channel_issues.append((_local_name(st), bad))
    report["checks"]["per_state_channels"] = {"count": len(per_state_channel_issues), "details": per_state_channel_issues}

    # 5) Categorization present (via classes or via *is properties)
    def _level_classified(ind, part_classes: List[Any]) -> bool:
        if not part_classes: return True  # skip if not provided
        types = set(ind.is_a)
        return any(pc in types or any(pc in a.ancestors() for a in types if hasattr(a, "ancestors")) for pc in part_classes)

    def _has_is_property(ind, prop):
        try:
            return bool(prop[ind])
        except Exception:
            return False

    uncategorized: Dict[str, List[str]] = {"HR": [], "HRV": [], "RR": [], "SpO2": []}
    for cls_name, cls in [("HR", HR), ("HRV", HRV), ("RR", RR), ("SpO2", SpO2)]:
        for ind in cls.instances() if cls else []:
            part = partitions.get(cls_name, [])

            ok_by_class = _level_classified(ind, part)
            # alternative via properties
            prop = {"HR": HRis, "HRV": HRVis, "RR": RRis, "SpO2": SpO2is}.get(cls_name)

            ok_by_prop = _has_is_property(ind, prop) if prop else True
            if not (ok_by_class or ok_by_prop):
                uncategorized[cls_name].append(_local_name(ind))
    report["checks"]["uncategorized_physio"] = uncategorized


    # 6) Disjointness sanity: no individual is in >1 level class per partition
    multi_membership: Dict[str, List[Tuple[str, List[str]]]] = {}
    for pname, part_list in partitions.items():
        collisions = []
        if part_list:
            # Gather membership
            members: Dict[Any, List[str]] = defaultdict(list)
            for pc in part_list:
                if pc is None: 
                    continue
                for ind in pc.instances():
                    members[ind].append(_local_name(pc))
            for ind, buckets in members.items():

                if len(buckets) > 1:
                    collisions.append((_local_name(ind), buckets))

        multi_membership[pname] = collisions

    report["checks"]["multi_membership"] = multi_membership

    # 7) Fatigue / Attention / Unresponsiveness single value per state and Is-functional-ish
    def _single_value_check(st_prop, cls_expected, is_prop_name):
        issues = []

        per_state_issues = []
        st_prop_ent = st_prop
        is_prop = is_prop_name
        cls_ent = cls_expected
        for st in actor_states:

            targets = list(st_prop_ent[st]) if st_prop_ent else []
            if len(targets) != 1:
                per_state_issues.append((_local_name(st), len(targets)))
            for t in targets:
                # Check single "Is" filler
                try:
                    vals = list(is_prop[t])
                    if len(vals) != 1:
                        issues.append((_local_name(t), len(vals)))
                except Exception:

                    # if no "Is" property, skip
                    pass
        return per_state_issues, issues


    fat_st_issues, fat_is_issues = _single_value_check(HasFatigue, Fatigue, FatigueIs)
    att_st_issues, att_is_issues = _single_value_check(HasAttention, AttentionLevels, AttentionIs)
    un_st_issues, un_is_issues = _single_value_check(HasUnresp, Unresp, UnrespIs)


    report["checks"]["fatigue_cardinality"] = {"per_state": fat_st_issues, "is_values": fat_is_issues}
    report["checks"]["attention_cardinality"] = {"per_state": att_st_issues, "is_values": att_is_issues}
    report["checks"]["unresp_cardinality"] = {"per_state": un_st_issues, "is_values": un_is_issues}

    # 8) Accessory mapping uniqueness (optional if props exist)
    acc_checks = {}
    ActorStateHasAccessories = ent(cfg.get("ActorStateHasAccessories"))
    Accessories = ent(cfg.get("Accessories"))
    AccessoryBelongsToGroup = ent(cfg.get("AccessoryBelongsToGroup"))
    denotesTemperature = ent(cfg.get("denotesTemperature"))
    TemperatureGroup = ent(cfg.get("TemperatureGroup"))

    if ActorStateHasAccessories and (AccessoryBelongsToGroup or denotesTemperature):
        # multiple temps per accessory group?
        group_to_temp: Dict[Any, Set[Any]] = defaultdict(set)
        multi_temps = []
        if AccessoryBelongsToGroup and denotesTemperature:
            for acc in Accessories.instances() if Accessories else []:
                try:
                    groups = AccessoryBelongsToGroup[acc]
                    for g in groups:
                        try:
                            temps = denotesTemperature[g]
                            for tg in temps:
                                group_to_temp[g].add(tg)

                        except Exception:
                            pass
                except Exception:
                    pass
            for g, temps in group_to_temp.items():
                if len(temps) > 1:
                    multi_temps.append((_local_name(g), [_local_name(t) for t in temps]))
        acc_checks["group_multiple_temperatures"] = multi_temps

        # Accessory instances typed and connected
        untyped_acc = []
        unlinked_temp = []
        for st in actor_states:
            for acc in ActorStateHasAccessories[st] if ActorStateHasAccessories else []:
                # typed?
                if Accessories and Accessories not in set(acc.is_a) and not any(Accessories in a.ancestors() for a in acc.is_a if hasattr(a, "ancestors")):
                    untyped_acc.append(_local_name(acc))
                # temp mapping exists?
                if AccessoryBelongsToGroup and denotesTemperature:
                    ok = False
                    for g in AccessoryBelongsToGroup[acc]:

                        if denotesTemperature[g]:
                            ok = True; break
                    if not ok:

                        unlinked_temp.append(_local_name(acc))

        acc_checks["untyped_accessories"] = untyped_acc
        acc_checks["unlinked_temp_for_accessory"] = unlinked_temp

    report["checks"]["accessories"] = acc_checks

    # 9) Cross-time mixing heuristic: physio individual linked to multiple states at different times
    physio_to_states: Dict[Any, Set[Any]] = defaultdict(set)
    if hasPhysio:
        for st in actor_states:
            for p in hasPhysio[st]:
                physio_to_states[p].add(st)
    reused_physio = [(_local_name(p), sorted({_local_name(s) for s in sts})) for p, sts in physio_to_states.items() if len(sts) > 1]
    report["checks"]["reused_physio_instances"] = reused_physio


    if verbose:
        print(f"\n=== Ontology Consistency Report v{CHECK_VERSION} ===")
        print(f"Ontology: {onto_file.name}")
        print(f"ActorStates: {report['counts']['ActorStates']} | HR: {report['counts']['HR']} | HRV: {report['counts']['HRV']} | RR: {report['counts']['RR']} | SpO2: {report['counts']['SpO2']}")
        print("\n[Identity] Duplicate (Actor, validAt) keys:", report["checks"]["state_identity"]["duplicate_keys_count"])
        if report["checks"]["state_identity"]["duplicates"]:
            for a,t,c in report["checks"]["state_identity"]["duplicates"]:
                print("  -", a, t, "count:", c)
        print("[Identity] Missing actor links:", len(report["checks"]["state_identity"]["missing_actor_states"]))
        print("[Identity] Missing timestamps:", len(report["checks"]["state_identity"]["missing_time_states"]))
        print("[Orphans] Orphan states:", report["checks"]["orphans"]["count"])
        print("[Time] Misaligned physio timestamps:", report["checks"]["time_alignment"]["count"])

        print("[Per-state channels] Issues:", report["checks"]["per_state_channels"]["count"])

        print("[Categorization] Unclassified HR:", len(report["checks"]["uncategorized_physio"]["HR"]),
              "| HRV:", len(report["checks"]["uncategorized_physio"]["HRV"]),

              "| RR:", len(report["checks"]["uncategorized_physio"]["RR"]),
              "| SpO2:", len(report["checks"]["uncategorized_physio"]["SpO2"]))
        for pname, collisions in report["checks"]["multi_membership"].items():
            print(f"[Partitions] Multi-membership in {pname}:", len(collisions))
        print("[Fatigue] per-state issues:", len(report["checks"]["fatigue_cardinality"]["per_state"]),
              "| Is-values issues:", len(report["checks"]["fatigue_cardinality"]["is_values"]))
        print("[Attention] per-state issues:", len(report["checks"]["attention_cardinality"]["per_state"]),
              "| Is-values issues:", len(report["checks"]["attention_cardinality"]["is_values"]))
        print("[Unresponsiveness] per-state issues:", len(report["checks"]["unresp_cardinality"]["per_state"]),
              "| Is-values issues:", len(report["checks"]["unresp_cardinality"]["is_values"]))

        if acc_checks:
            print("[Accessories] Group→Temp multiple mappings:", len(acc_checks.get("group_multiple_temperatures", [])))
            print("[Accessories] Untyped accessories:", len(acc_checks.get("untyped_accessories", [])))

            print("[Accessories] Accessories without temp link:", len(acc_checks.get("unlinked_temp_for_accessory", [])))
        print("[Reuse] Physio reused across states:", len(report["checks"]["reused_physio_instances"]))
        print("\nDone.\n")


    return report


# If executed as a script, run on a default path (user can edit this path)
if __name__ == "__main__":
    assets_dir = get_assets_path() 
    path = sys.argv[1] if len(sys.argv) > 1 else f"{assets_dir}/ontologies/snapshot_2.owl"
    res = run_consistency_checks(path, config=None, verbose=True)
    out = Path(f"{str(assets_dir)}/consistency_report.json")
    out.write_text(json.dumps(res, indent=2, default=str))
    print(f"Saved JSON report to {out}")

