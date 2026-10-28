#!/usr/bin/env python3
"""
Serialise the SOLVE-IT ontology modules (solve_it_*.ttl) as a single JSON-LD
file, published at ontology.solveit-df.org/solve-it-ontology.jsonld.

The ontology is otherwise published only as Turtle, which most languages have
no parser for. The output is expanded JSON-LD (full IRIs, no @context), so a
consumer can read labels, comments and parents with a plain JSON parser.

The output is deterministic, so an unchanged ontology produces a
byte-identical file and a changed one produces a diff of only what changed.
rdflib alone writes nodes in set-iteration order, which varies with Python's
per-run hash seed, and labels blank nodes randomly; either would rewrite most
of the file on every docs build.

Usage: python scripts/build_ontology_jsonld.py [output-path]
Default output: docs/solve-it-ontology.jsonld
"""

import json
import sys
from pathlib import Path
from rdflib import Graph
from rdflib.compare import to_canonical_graph

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO_ROOT / "docs" / "solve-it-ontology.jsonld"


def sort_key(value):
    # Property values are unordered sets in expanded JSON-LD, so they are
    # sorted. An @list's own items are left in place: list order is data.
    return json.dumps(value, sort_keys=True, ensure_ascii=False)


def main():
    # Root-level modules only, matching the ontospy build: solve_it_examples/
    # holds example data, not ontology.
    sources = sorted(REPO_ROOT.glob("solve_it_*.ttl"))
    if not sources:
        sys.exit(f"no solve_it_*.ttl files found in {REPO_ROOT}")
    g = Graph()
    for path in sources:
        g.parse(path, format="turtle")
    # Canonical blank node labels are derived from content, not generated.
    nodes = json.loads(to_canonical_graph(g).serialize(format="json-ld"))
    for node in nodes:
        for key, values in node.items():
            if isinstance(values, list):
                node[key] = sorted(values, key=sort_key)
    nodes.sort(key=lambda n: n["@id"])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(nodes, indent=1, sort_keys=True, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    print(f"wrote {len(g)} triples from {len(sources)} modules -> {OUT}")


if __name__ == "__main__":
    main()
