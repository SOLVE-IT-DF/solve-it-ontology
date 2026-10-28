#!/usr/bin/env python3
"""
Serialise the SOLVE-IT ontology modules (solve_it_*.ttl) as a single JSON-LD
file, published at ontology.solveit-df.org/solve-it-ontology.jsonld.

The ontology is otherwise published only as Turtle, which most languages have
no parser for. The output is expanded JSON-LD (full IRIs, no @context), so a
consumer can read labels, comments and parents with a plain JSON parser.

Usage: python scripts/build_ontology_jsonld.py [output-path]
Default output: docs/solve-it-ontology.jsonld
"""

import sys
from pathlib import Path
from rdflib import Graph

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO_ROOT / "docs" / "solve-it-ontology.jsonld"


def main():
    # Root-level modules only, matching the ontospy build: solve_it_examples/
    # holds example data, not ontology.
    sources = sorted(REPO_ROOT.glob("solve_it_*.ttl"))
    if not sources:
        sys.exit(f"no solve_it_*.ttl files found in {REPO_ROOT}")
    g = Graph()
    for path in sources:
        g.parse(path, format="turtle")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(g.serialize(format="json-ld", indent=1), encoding="utf-8")
    print(f"wrote {len(g)} triples from {len(sources)} modules -> {OUT}")


if __name__ == "__main__":
    main()
