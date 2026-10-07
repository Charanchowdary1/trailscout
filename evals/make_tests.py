"""Build tests.yaml from TrialScout's demo_cache.json (real PubMed abstracts).

Usage:  python make_tests.py path/to/trialscout/demo_cache.json
Needs:  pip install pyyaml
"""
import json
import sys

import yaml

PER_QUERY = 3  # papers taken from each saved search

cache = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "demo_cache.json"))
tests = []

for query, papers in cache.items():
    usable = [p for p in papers if p["abstract"]]
    # Mix of structured (several labelled sections) and single-paragraph abstracts.
    structured = [p for p in usable if len(p["abstract"]) > 1][:2]
    plain = [p for p in usable if len(p["abstract"]) == 1][:PER_QUERY - len(structured)]
    for p in structured + plain:
        abstract = "\n".join(
            f'{s["label"]}: {s["text"]}' if s["label"] else s["text"] for s in p["abstract"]
        )
        tests.append({
            "description": f'{query} | PMID {p["pmid"]}',
            "vars": {"title": p["title"], "abstract": abstract},
        })

# Hand-written edge case: what TrialScout shows when PubMed has no abstract.
tests.append({
    "description": "Edge case | no abstract available",
    "vars": {
        "title": "A paper without an abstract",
        "abstract": "No abstract available for this paper.",
    },
    "assert": [{
        "type": "llm-rubric",
        "value": "The response says that no abstract is available. It does not invent any study findings.",
    }],
})

yaml.safe_dump(tests, open("tests.yaml", "w"), sort_keys=False, allow_unicode=True, width=100)
print(f"Wrote tests.yaml with {len(tests)} test cases")
