"""Save real PubMed results for the example searches so the demo is fast and never breaks on camera.

Run once with internet access:  python cache_demo.py
Then record with:               DEMO_MODE=1 python app.py
Edit EXAMPLES to change the queries shown on the home page.
"""
import json
from pathlib import Path

from app import search_pubmed

EXAMPLES = [
    "KRAS inhibitors in lung cancer",
    "CAR-T therapy for lupus",
    "GLP-1 agonists and cardiovascular outcomes",
]

cache = {}
for q in EXAMPLES:
    print(f"Fetching: {q}")
    cache[q] = search_pubmed(q)
    print(f"  saved {len(cache[q])} papers")

Path(__file__).with_name("demo_cache.json").write_text(json.dumps(cache, indent=2))
print("Wrote demo_cache.json")
