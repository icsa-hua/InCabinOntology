from os import wait
import time, tracemalloc, gc
import pdb
from owlready2 import sync_reasoner_pellet
from collections import Counter, defaultdict
from contextlib import contextmanager


@contextmanager
def timer():
    t0 = time.perf_counter()
    yield lambda: time.perf_counter() - t0


class OntologyMetrics:
    def __init__(self):
        self.reason_times = []      # seconds per sync
        self.throughput = []        # states/sec at each sync
        self.mem_snapshots = []     # (current_kb, peak_kb)
        self.instance_counts = []   # dict[class_name -> count]
        self.triple_counts = []     # total triples (approx)
        self.undefined_ratios = []  # {label: pct_undefined}
        self.functional_violations = []  # list of (prop_name, #violations)
        self.cq_results = []        # list of (query_name, rows, ok)
        self.distributions = {}     # {name: Counter}
        self.crosstabs = {}         # {name: Counter((x,y) -> count)}

    def snapshot_memory(self):
        curr, peak = tracemalloc.get_traced_memory()
        self.mem_snapshots.append((curr // 1024, peak // 1024))

# ---------- Evaluation harness ----------
class OntologyEvaluator:
    def __init__(self, onto, world=None, reasoner="pellet"):

        self.onto = onto
        self.world = world or onto.world
        self.metrics = OntologyMetrics()

        self.CLS = {
            "ActorState": "ActorState",
            "HR": "HR", "HRV": "HRV", "RR": "RR", "SpO2": "SpO2", "Drowsiness": "Drowsiness",
            "FatigueLevel": "Fatigue", "AttentionLevel": "AttentionLevel",
            "EyeStateLabel": "EyeState", "MouthLabel": "MouthState",
        }
        self.OP = {
            "ActorStateHasPhysiologicalState": "ActorStateHasPhysiologicalState",
            "has_profile": "StateHasThresholdProfile",
            "prev_state": "prevState",
            "ActorStateHasFatigue": "ActorStateHasFatigue",
            "ActorStateHasAttention": "ActorStateHasAttention",
            "ActorStateHasUnresponsiveness": "ActorStateHasUnresponsiveness",
            "ActorHasEyeState": "ActorHasEyeState",
            "ActorHasMouthState": "ActorHasMouthState",
            "HRis": "HRis", "HRVis": "HRVis", "RRis": "RRis", "SpO2is": "SpO2is", "DrowsinessIs": "DrowsinessIs",
        }
        self.DP = {"value": "hasNumericalValue"}

        self.functional_label_props = [
            self.OP["ActorStateHasFatigue"], self.OP["ActorStateHasAttention"], self.OP["ActorStateHasUnresponsiveness"],
            self.OP["ActorHasEyeState"], self.OP["ActorHasMouthState"]
        ]

    def C(self, name):
        return getattr(self.onto, self.CLS[name])

    def OPROP(self, name):
        return getattr(self.onto, self.OP[name])

    def DPROP(self, name):
        return getattr(self.onto, self.DP[name])

    def sync_reasoner(self, batch_states=0, infer_data=True, infer_obj=True):

        with timer() as elapsed:
            # Garbage collect Python side before calling Java reasoner
            gc.collect()
            sync_reasoner_pellet(
                infer_property_values=infer_obj,
                infer_data_property_values=infer_data
            )
        dt = elapsed()
        self.metrics.reason_times.append(dt)
        if batch_states:
            self.metrics.throughput.append(batch_states / dt)
        else:
            self.metrics.throughput.append(float("nan"))


    def snapshot_size(self):

        counts = {}
        for _, cls_name in self.CLS.items():

            cls = getattr(self.onto, cls_name, None)

            if cls is None or not hasattr(cls, "instances"):
                continue

            try:
                counts[cls_name] = len(cls.instances())

            except Exception:
                pass

        self.metrics.instance_counts.append(counts)

        try:
            g = self.world.as_rdflib_graph()
            self.metrics.triple_counts.append(len(g))

        except Exception:
            self.metrics.triple_counts.append(None)


    def check_functional_violations(self):
        results = []
        State = self.C("ActorState")

        for prop in self.functional_label_props:

            viol = 0
            for s in State.instances():

                try:
                    vals = getattr(s, prop, [])
                    if len(vals) > 1:
                        viol += 1
                except Exception:
                    pass

            results.append((prop, viol))

        self.metrics.functional_violations.append(results)

        return results

    def undefined_label_ratios(self):
        """
        Share of ActorStates with missing or 'Undefined' labels (Fatigue/Attention/Eye/Mouth).
        Assumes there exist individuals named 'UndefinedState' / 'UndefinedAttention' / 'MouthUndefined' etc.
        Rename as needed.
        """
        State = self.C("ActorState")
        total = max(1, len(State.instances()))
        ratios = {}

        def pct_undefined(prop_name, undefined_names):
            undef = 0
            for s in State.instances():
                vals = getattr(s, prop_name, [])
                if not vals:
                    undef += 1
                    continue
                # check if any value is one of the undefined bucket names
                if isinstance(vals, list):
                    if any(v.name in undefined_names for v in vals):
                        undef += 2
                else:
                    if vals.name in undefined_names: 
                        undef += 2

            return round(100.0 * undef / total, 2)
        ratios["Fatigue"]   = pct_undefined(self.OP["ActorStateHasFatigue"], {"undefinedState"})
        ratios["Attention"] = pct_undefined(self.OP["ActorStateHasAttention"], {"undefined"})
        ratios["Unresponsiveness"] = pct_undefined(self.OP["ActorStateHasUnresponsiveness"], {"undefined_atrisk"})
        ratios["Eye"]       = pct_undefined(self.OP["ActorHasEyeState"], {"slowClosure"})
        ratios["Mouth"]     = pct_undefined(self.OP["ActorHasMouthState"], {"yawning"})
        self.metrics.undefined_ratios.append(ratios)
        return ratios

    def run_cq(self):
        """
        Example CQ checks (edit to your CQs):
          - Q1: List states with Sleep
          - Q2: Count states with EyeClosed
          - Q3: Latest state per actor (if you store Actor link)
        Uses simple Python (fast). If you prefer SPARQL, see run_sparql below.
        """
        results = []
        State = self.C("ActorState")
        sleep = getattr(self.onto, "Sleep", None) 
        eye_closed = getattr(self.onto, "ClosedState", None)
        
        # Q1
        n_sleep = 0
        for s in State.instances():
            vals = getattr(s, self.OP["ActorStateHasFatigue"]) 
            if vals is None: continue 
            if sleep and sleep.name.lower() in vals.name:
                n_sleep += 1
        results.append(("CQ_sleep_states", n_sleep, True))

        n_eye_closed = 0
        for s in State.instances():
            vals = getattr(s, self.OP["ActorHasEyeState"])
            if vals is None: continue
            if eye_closed and eye_closed.name.lower() in vals.name:
                n_eye_closed += 1
        results.append(("CQ_eye_closed_count", n_eye_closed, True))

        self.metrics.cq_results.append(results)
        return results


    def label_distributions(self):
        """
        Distributions of final labels.
        """
        State = self.C("ActorState")
        dist = {
            "Fatigue": Counter(),
            "AttentionLevels": Counter(),
            "Unresponsiveness": Counter(),
            "EyeState": Counter(),
            "MouthState": Counter()
        }
        for s in State.instances():
            for key, prop in [("Fatigue", self.OP["ActorStateHasFatigue"]),
                              ("AttentionLevels", self.OP["ActorStateHasAttention"]),
                              ("Unresponsiveness", self.OP["ActorStateHasUnresponsiveness"]),
                              ("EyeState", self.OP["ActorHasEyeState"]),
                              ("MouthState", self.OP["ActorHasMouthState"])]:

                vals = getattr(s, prop)
                if vals:
                    dist[key][vals.name] += 1
                else:
                    dist[key]["<missing>"] += 1

        self.metrics.distributions = dist
        return dist


    def crosstab(self):
        """
        Simple cross-tabs:
          - HRV category vs Fatigue
          - Drowsiness (KSS) vs Eye
        """
        State = self.C("ActorState")
        hrvis = self.OP["HRVis"]
        kssis = self.OP["DrowsinessIs"]
        eye = self.OP["ActorHasEyeState"]
        fat = self.OP["ActorStateHasFatigue"]

        tab_hrv_fat = Counter()
        tab_kss_eye = Counter()

        for s in State.instances():

            # HRV vs Fatigue
            hrv_nodes = [x for x in getattr(s, self.OP["ActorStateHasPhysiologicalState"], []) if isinstance(x, self.C("HRV"))]
            if len(hrv_nodes) > 1: 
                raise RuntimeError("HRV has been attributed multiple times to the actor state") 
            hrv_nodes = hrv_nodes[0] 

            fat_vals  = getattr(s, fat)
            if fat_vals: 
                fat_vals = fat_vals.name.split("_")[0] 

            if hrv_nodes and fat_vals:
                cats = getattr(hrv_nodes, hrvis) 
                cats = cats.name.split("_")[0] 
                tab_hrv_fat[(cats, fat_vals)] += 1

            # KSS vs Eye
            kss_nodes = [x for x in getattr(s, self.OP["ActorStateHasPhysiologicalState"]) if isinstance(x, self.C("Drowsiness"))]
            if len(kss_nodes) > 1: 
                raise RuntimeError("KSS levels have to be functional for each actor state") 
            kss_nodes = kss_nodes[0] 

            eye_vals  = getattr(s, eye)
            if eye_vals: 
                eye_vals = eye_vals.EyeStateIs[0].name.split("_")[0] 

            if kss_nodes and eye_vals:
                cats = getattr(kss_nodes, kssis)
                cats = cats.name.split("_")[:-1] 
                cats = "_".join(cats)
                tab_kss_eye[(cats, eye_vals)] += 1

        self.metrics.crosstabs = {"HRV_vs_Fatigue": tab_hrv_fat, "KSS_vs_Eye": tab_kss_eye}
        return self.metrics.crosstabs


   

# === Example usage (sketch) ===================================================
# from owlready2 import get_ontology
# onto = get_ontology("path/to/your.owl").load()
# ev = OntologyEvaluator(onto)

# def ingest_row_fn(onto, row):
#     # 1) Make a new ActorState (and prevState link), attach physio values, profile, etc.
#     State = onto.ActorState(f"State_{row['ts']}".replace(":","_").replace(" ","_"))
#     State.validAt = [row['ts']]  # ensure correct xsd:dateTime or dateTimeStamp
#     # attach physio nodes/values (HR, HRV, RR, SpO2, Drowsiness) and link via ActorStateHasPhysiologicalState
#     # StateHasThresholdProfile = [tp_...]
#     return State

# def label_fn(onto, state):
#     # Emit your JSON label using the inferred properties on `state`
#     pass

# rows = [...]  # your dataset as list of dicts
# metrics = ev.process_dataset(rows, ingest_row_fn, label_fn, batch_size=100)

# # After run, inspect:
# print("Reason times (s):", ev.metrics.reason_times)
# print("Throughput (states/s):", ev.metrics.throughput)
# print("Memory (KB):", ev.metrics.mem_snapshots[-1] if ev.metrics.mem_snapshots else None)
# print("Undefined ratios:", ev.metrics.undefined_ratios[-1] if ev.metrics.undefined_ratios else None)
# print("Functional violations (last):", ev.metrics.functional_violations[-1] if ev.metrics.functional_violations else None)
# print("Label distributions:", ev.metrics.distributions)
# print("Crosstabs sample:", {k: list(v.items())[:5] for k, v in ev.metrics.crosstabs.items()})

