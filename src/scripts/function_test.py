# Re-run the same analysis (the previous environment reset).

import re, json, textwrap
from pathlib import Path
from collections import Counter, defaultdict

path = Path("src/designs/rule_creator.py")
print("Exists:", path.exists(), path)

code = path.read_text(encoding="utf-8", errors="ignore")


func_pattern = re.compile(r"def\s+__determine_fatigue\s*\(.*?\):\s*(?P<body>(?:.|\n)*?)(?=\n\s*def\s+|\Z)", re.M)
m = func_pattern.search(code)
if not m:
    print("Could not find __determine_fatigue function.")

    print(code[:800])
else:
    body = m.group("body")
    print("Function length (chars):", len(body))
    entries = []
    for block in re.finditer(r"rule_name\s*=\s*['\"]([^'\"]+)['\"][\s\S]*?Imp\s*\(\s*rule_name\s*\)\.set_as_rule\(\s*['\"]{3}([\s\S]*?)['\"]{3}\s*\)\s*", body):
        name = block.group(1)
        rule_text = block.group(2)
        entries.append((name, rule_text))
    print("Rules found:", len(entries))
    names = [n for n,_ in entries]
    cnt = Counter(names)
    dups = [n for n,c in cnt.items() if c>1]
    print("Duplicate rule names:", dups)

    def norm(s):

        s2 = re.sub(r"#.*", "", s)
        s2 = re.sub(r"\s+", " ", s2).strip()
        return s2
    body_map = defaultdict(list)
    for i,(n,t) in enumerate(entries):
        body_map[norm(t)].append(n)

    dup_bodies = [names for names in body_map.values() if len(names)>1]
    print("Duplicate rule bodies (normalized):", json.dumps(dup_bodies, indent=2))

    # Common typos/grammatical issues
    typos = {
        "drowsiness_instance":0,
        "HRV(?hr)": 0,
        "RR(?hr)": 0,
        "SpO2(?hr)": 0,
        "HR(?rr)": 0, 
        "fatigue_instance":0, 
        "SPO2":0, 
        "HR(?hrv)":0, 
        "isntance":0,
    }

    var_inconsistencies = []
    for n,t in entries:
        for k in list(typos.keys()):
            if k in t:
                typos[k]+=1

        if re.search(r"drowsiness_instance", t):
            var_inconsistencies.append((n,"drowsiness_instance found instead of ?dr or dr_inst"))

        if re.search(r"\bHRV\(\?hr\)", t):
            var_inconsistencies.append((n,"HRV uses ?hr instead of ?hrv"))

        if re.search(r"\bRR\(\?hr\)", t):
            var_inconsistencies.append((n,"RR uses ?hr instead of ?rr"))

        if re.search(r"\bSpO2\(\?hr\)", t):
            var_inconsistencies.append((n,"SpO2 uses ?hr instead of ?spo2"))

        if re.search(r"HRV\(\?hr\)\s*,\s*HRVis\(\?hrv", t):
            var_inconsistencies.append((n,"HRV head uses ?hr but HRVis uses ?hrv"))

        if re.search(r"HR\(\?rr\)", t):
            var_inconsistencies.append((n,"HR head uses ?rr but should be ?hr"))

        if re.search(r"SPO2", t):
            var_inconsistencies.append((n,"SPO2 is found instead of SpO2"))

        if re.search(r"fatigue_instance", t):
            var_inconsistencies.append((n,"fatigue_instance is used instead of fatigue_inst"))

        if re.search(r"HR\(\?hrv\)", t):
            var_inconsistencies.append((n,"HR head uses ?hrv but should be ?hr"))

        if re.search(r"isntance", t):
            var_inconsistencies.append((n,"HR head uses ?hrv but should be ?hr"))


        if t.count("(") != t.count(")"):

            var_inconsistencies.append((n,"Unbalanced parentheses"))

    print("\nPotential typos counts:")
    for k,v in typos.items():
        print(f"  {k}: {v}")
    print("\nVariable / structural inconsistencies:")
    if len(var_inconsistencies) != 0: 
        for item in var_inconsistencies:
            print(" ", item)
    else: 
        print("No inconsistencies found")

    print("\nAll rule names:")
    for n in names:
        print(" ", n)

