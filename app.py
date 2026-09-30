"""TrialScout: a small research-paper finder built on PubMed's public E-utilities API.

Run:        python app.py
Demo mode:  DEMO_MODE=1 python app.py   (serves only cached queries, no network)
"""
import json
import os
import re
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import requests
from flask import Flask, jsonify, render_template, request

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
CACHE_FILE = Path(__file__).parent / "demo_cache.json"
LIVE_TTL_SECONDS = 3600
MAX_RESULTS = 10
DEMO_MODE = os.getenv("DEMO_MODE") == "1"

app = Flask(__name__)

# Queries saved by cache_demo.py. These make the demo fast and repeatable.
_saved = json.loads(CACHE_FILE.read_text()) if CACHE_FILE.exists() else {}
demo_titles = list(_saved)  # original capitalisation, shown as example chips
demo_cache = {k.lower(): v for k, v in _saved.items()}
live_cache = {}  # query -> (timestamp, results)


def _params(extra):
    params = {"tool": "trialscout", **extra}
    if os.getenv("NCBI_EMAIL"):
        params["email"] = os.environ["NCBI_EMAIL"]
    if os.getenv("NCBI_API_KEY"):
        params["api_key"] = os.environ["NCBI_API_KEY"]
    return params


def _text(node):
    """All text inside an XML node, including nested tags like <i> and <sub>."""
    return "".join(node.itertext()).strip() if node is not None else ""


def _sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+(?=[A-Z])", text) if s.strip()]


def summarize(sections):
    """Plain summary without an LLM: the labelled conclusion if there is one,
    otherwise the first two sentences of the abstract."""
    for label, body in sections:
        if label.upper().startswith("CONCLUSION") and body:
            text = " ".join(_sentences(body)[:2])
            break
    else:
        full = " ".join(body for _, body in sections)
        text = " ".join(_sentences(full)[:2])
    return text if len(text) <= 260 else text[:257].rsplit(" ", 1)[0] + "..."


def parse_articles(xml_text):
    root = ET.fromstring(xml_text)
    results = []
    for art in root.findall(".//PubmedArticle"):
        pmid = _text(art.find(".//MedlineCitation/PMID"))
        title = _text(art.find(".//Article/ArticleTitle"))
        journal = _text(art.find(".//Article/Journal/Title"))

        year = _text(art.find(".//Article/Journal/JournalIssue/PubDate/Year"))
        month = _text(art.find(".//Article/Journal/JournalIssue/PubDate/Month"))
        if not year:  # some records use MedlineDate, e.g. "2024 Jan-Feb"
            m = re.search(r"\d{4}", _text(art.find(".//Article/Journal/JournalIssue/PubDate/MedlineDate")))
            year = m.group(0) if m else ""
        date = f"{month} {year}".strip()

        sections = [
            (n.get("Label") or "", _text(n))
            for n in art.findall(".//Article/Abstract/AbstractText")
        ]
        names = []
        for a in art.findall(".//Article/AuthorList/Author"):
            last, initials = _text(a.find("LastName")), _text(a.find("Initials"))
            if last:
                names.append(f"{last} {initials}".strip())
        authors = ", ".join(names[:3]) + (" et al." if len(names) > 3 else "")

        results.append({
            "pmid": pmid,
            "title": title,
            "journal": journal,
            "date": date,
            "authors": authors,
            "summary": summarize(sections) if sections else "No abstract available for this paper.",
            "abstract": [{"label": l, "text": t} for l, t in sections],
            "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
        })
    return results


def search_pubmed(query, limit=MAX_RESULTS):
    r = requests.get(
        f"{EUTILS}/esearch.fcgi",
        params=_params({"db": "pubmed", "term": query, "retmax": limit, "retmode": "json", "sort": "relevance"}),
        timeout=15,
    )
    r.raise_for_status()
    ids = r.json()["esearchresult"]["idlist"]
    if not ids:
        return []
    r = requests.get(
        f"{EUTILS}/efetch.fcgi",
        params=_params({"db": "pubmed", "id": ",".join(ids), "retmode": "xml"}),
        timeout=20,
    )
    r.raise_for_status()
    by_id = {a["pmid"]: a for a in parse_articles(r.text)}
    return [by_id[i] for i in ids if i in by_id]  # keep PubMed's relevance order


def get_results(query):
    key = query.strip().lower()
    if key in demo_cache:
        return demo_cache[key]
    if DEMO_MODE:
        raise LookupError("Demo mode only serves the saved example searches. Pick one of the examples.")
    hit = live_cache.get(key)
    if hit and time.time() - hit[0] < LIVE_TTL_SECONDS:
        return hit[1]
    results = search_pubmed(query)
    live_cache[key] = (time.time(), results)
    return results


@app.get("/")
def index():
    examples = demo_titles or [
        "KRAS inhibitors in lung cancer",
        "CAR-T therapy for lupus",
        "GLP-1 agonists and cardiovascular outcomes",
    ]
    return render_template("index.html", examples=examples)


@app.get("/api/search")
def api_search():
    q = request.args.get("q", "").strip()
    if len(q) < 3:
        return jsonify(error="Type at least 3 characters to search."), 400
    try:
        return jsonify(query=q, results=get_results(q))
    except LookupError as e:
        return jsonify(error=str(e)), 404
    except requests.RequestException:
        return jsonify(error="PubMed could not be reached. Check your connection and search again."), 502


if __name__ == "__main__":
    app.run(debug=not DEMO_MODE, port=int(os.getenv("PORT", 5000)))
