

import os 
from rdflib import Graph 
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4

def save_sparql_results_to_pdf(output_path, results_dict):
    """
    Saves SPARQL query results to a PDF file.
    
    Params:
        output_path (str): Path to save the PDF.
        results_dict (dict): 
            {
              "Q1. Missing physiological": [(state1,), (state2, ...)],
              "Q2. Multiple HR": [...]
            }
    """
    styles = getSampleStyleSheet()
    story = []

    doc = SimpleDocTemplate(output_path, pagesize=A4)

    # Title
    story.append(Paragraph("Consistency Questionnaire Results", styles["Title"]))
    story.append(Spacer(1, 12))

    # Body
    for name, rows in results_dict.items():
        story.append(Paragraph(f"<b>{name}</b>", styles["Heading3"]))

        if not rows:
            story.append(Paragraph("✔ No inconsistencies found.", styles["BodyText"]))
        else:
            story.append(Paragraph(
                f"❌ {len(rows)} inconsistencies found.", styles["BodyText"]
            ))
            for row in rows[:10]:   # show first 10
                story.append(Paragraph(str(row), styles["Code"]))
        
        story.append(Spacer(1, 12))

    doc.build(story)


# Load the ontology
g = Graph() 
parent_path = os.getcwd() 
ontology_path = os.path.join(parent_path, "assets/ontologies/snapshot_2.owl")
g.parse(ontology_path)


#Load the .ttl CQ 
def load_queries_from_ttl(path):

    """
    NOTE: RULE FORMAT 
    # ------------------------
    # Q3. Multiple HRV per ActorState
    # ------------------------
    # SELECT DISTINCT ?state WHERE {
    #   ?state rdf:type :ActorState ;
    #          :ActorStateHasPhysiologicalState ?h1, ?h2 .
    #   ?h1 rdf:type :HRV . ?h2 rdf:type :HRV .
    #   FILTER (?h1 != ?h2)
    # }

    """

    queries = []
    current_name = None
    current_lines = []

    with open(path, "r") as f:
        for raw_line in f:
            line = raw_line.rstrip("\n")

            # Header line with question name
            if line.startswith("# Q") and not "----" in line:
                # flush previous
                if current_name and current_lines:
                    queries.append((current_name, "\n".join(current_lines)))
                    current_lines = []
                current_name = line[2:].strip()  # e.g. "Q3. Multiple HRV per ActorState"

            # Separator lines: "# ------------------------"
            elif line.startswith("# ---"):
                # if we already collected query lines, separator means end of this block
                if current_name and current_lines:
                    queries.append((current_name, "\n".join(current_lines)))
                    current_name = None
                    current_lines = []

            # Query lines: commented SPARQL
            elif line.startswith("# ") and current_name:
                # ignore pure headers already handled; keep everything else as query
                stripped = line[2:]
                if stripped.strip():       # skip empty "# "
                    current_lines.append(stripped)

            # Blank line: finish current query if any
            elif not line.strip():
                if current_name and current_lines:
                    queries.append((current_name, "\n".join(current_lines)))
                    current_name = None
                    current_lines = []

        # flush last one if file doesn't end with blank line
        if current_name and current_lines:
            queries.append((current_name, "\n".join(current_lines)))

    return queries


# Execute Queries
ttl_file = os.path.join(parent_path, "assets/consistency_questionnaire.ttl")
queries = load_queries_from_ttl(ttl_file)
messages = {} 


for name, q in queries:
    messages[name] = "" 
    messages[name] += f"Running {name}..."
    print(f"Running {name}...")
    res = g.query(q)
    rows = list(res)
    if rows:
        messages[name] += f"❌ Inconsistencies found ({len(rows)} rows)"
        print(f"❌ Inconsistencies found ({len(rows)} rows)")
        for r in rows[:5]:  # show first few
            messages[name] += f"{r}"
            print("  ", r)
    else:
        messages[name] += "✅ No issues"
        print("✅ No issues")
    print()

save_sparql_results_to_pdf(
    os.path.join(parent_path, "assets/CQ_report.pdf"), 
    messages
)


