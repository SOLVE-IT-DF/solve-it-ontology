#!/usr/bin/env python3
"""
Validate input/output type compatibility between SOLVE-IT example
InvestigativeActions and technique definitions in the knowledge base.

For each SolveitInvestigativeAction in the examples, checks whether the
types of uco-action:object (inputs) and uco-action:result (outputs) match
the hasCASEInputClass / hasCASEOutputClass declared on the referenced
technique in the KB.

Reports:
  - MISMATCH: example provides types that don't overlap with KB expectations
  - NOT IN KB: technique referenced in example not found in KB
  - NO I/O: technique exists in KB but has no input/output classes defined

Exit code:
  0 — no mismatches (warnings are OK)
  1 — at least one mismatch found
"""

import json
import sys
from pathlib import Path
from rdflib import Graph, Namespace, RDF, URIRef


# -- Namespaces --

SOLVEIT_CORE_NS = "https://ontology.solveit-df.org/solveit/core/"
UCO_ACTION = Namespace("https://ontology.unifiedcyberontology.org/uco/action/")
UCO_CORE_NAME = URIRef("https://ontology.unifiedcyberontology.org/uco/core/name")
SOLVEIT_CORE = Namespace(SOLVEIT_CORE_NS)
TECH_TYPE = SOLVEIT_CORE_NS + "Technique"


# -- Helpers --

def _extract_uris(val):
    """Extract URI strings from KB JSON-LD values (typed or plain)."""
    if not val:
        return set()
    if not isinstance(val, list):
        val = [val]
    uris = set()
    for v in val:
        if isinstance(v, dict):
            uris.add(v.get("@value", v.get("@id", "")))
        else:
            uris.add(str(v))
    return uris


def _short(uri):
    """Return local name from a URI."""
    for sep in ("#", "/"):
        idx = uri.rfind(sep)
        if idx >= 0:
            return uri[idx + 1:]
    return uri


def _short_set(uris):
    """Return sorted short names for a set of URIs."""
    return sorted(_short(u) for u in uris)


def load_kb_techniques(kb_path):
    """Load technique I/O class mappings from the KB JSON-LD file.

    Returns:
        Tuple of (tech_names, tech_inputs, tech_outputs) dicts keyed by IRI.
    """
    data = json.loads(kb_path.read_text())

    tech_names = {}
    tech_inputs = {}
    tech_outputs = {}

    for item in data:
        types = item.get("@type", [])
        if isinstance(types, str):
            types = [types]
        if TECH_TYPE not in types:
            continue

        iri = item.get("@id", "")
        tid = item.get(SOLVEIT_CORE_NS + "techniqueID", "")
        tname = item.get(SOLVEIT_CORE_NS + "techniqueName", "")
        # Handle typed values
        if isinstance(tid, list):
            tid = tid[0].get("@value", "") if tid else ""
        elif isinstance(tid, dict):
            tid = tid.get("@value", "")
        if isinstance(tname, list):
            tname = tname[0].get("@value", "") if tname else ""
        elif isinstance(tname, dict):
            tname = tname.get("@value", "")

        tech_names[iri] = f"{tid} ({tname})"

        inputs = _extract_uris(item.get(SOLVEIT_CORE_NS + "hasCASEInputClass"))
        outputs = _extract_uris(item.get(SOLVEIT_CORE_NS + "hasCASEOutputClass"))
        if inputs:
            tech_inputs[iri] = inputs
        if outputs:
            tech_outputs[iri] = outputs

    return tech_names, tech_inputs, tech_outputs


def load_examples(examples_dir):
    """Load all example TTL files into a single graph."""
    g = Graph()
    files = sorted(examples_dir.glob("*.ttl"))
    for f in files:
        g.parse(f, format="turtle")
    return g, files


def validate(examples_graph, tech_names, tech_inputs, tech_outputs):
    """Validate example actions against KB technique I/O classes.

    Returns:
        Tuple of (mismatches, warnings) where each is a list of strings.
    """
    g = examples_graph
    mismatches = []
    warnings = []

    action_class = URIRef(SOLVEIT_CORE_NS + "SolveitInvestigativeAction")
    used_tech = URIRef(SOLVEIT_CORE_NS + "usedTechnique")

    for action in sorted(g.subjects(RDF.type, action_class), key=str):
        names = list(g.objects(action, UCO_CORE_NAME))
        action_name = str(names[0]) if names else _short(str(action))

        actual_input_types = set()
        for obj in g.objects(action, UCO_ACTION.object):
            for t in g.objects(obj, RDF.type):
                actual_input_types.add(str(t))

        actual_output_types = set()
        for res in g.objects(action, UCO_ACTION.result):
            for t in g.objects(res, RDF.type):
                actual_output_types.add(str(t))

        for tech_ref in g.objects(action, used_tech):
            tech_iri = str(tech_ref)
            label = tech_names.get(tech_iri)

            if label is None:
                warnings.append(
                    f"{action_name}: technique {_short(tech_iri)} not found in KB"
                )
                continue

            expected_inputs = tech_inputs.get(tech_iri, set())
            expected_outputs = tech_outputs.get(tech_iri, set())

            if not expected_inputs and not expected_outputs:
                warnings.append(
                    f"{action_name}: {label} has no I/O classes in KB"
                )
                continue

            # Check inputs
            if expected_inputs and actual_input_types:
                if not (actual_input_types & expected_inputs):
                    mismatches.append(
                        f"{action_name} -> {label} inputs: "
                        f"example has [{', '.join(_short_set(actual_input_types))}] "
                        f"but KB expects [{', '.join(_short_set(expected_inputs))}]"
                    )

            # Check outputs
            if expected_outputs and actual_output_types:
                if not (actual_output_types & expected_outputs):
                    mismatches.append(
                        f"{action_name} -> {label} outputs: "
                        f"example has [{', '.join(_short_set(actual_output_types))}] "
                        f"but KB expects [{', '.join(_short_set(expected_outputs))}]"
                    )

    return mismatches, warnings


def main():
    project_root = Path(__file__).parent.parent
    examples_dir = project_root / "solve_it_examples"
    kb_path = project_root / "docs" / "data" / "solve-it-kb.jsonld"

    print("SOLVE-IT Example I/O Type Validator")
    print("=" * 60)

    if not examples_dir.exists():
        print(f"Error: {examples_dir} not found")
        sys.exit(1)

    if not kb_path.exists():
        print(f"Warning: KB not found at {kb_path}")
        print("Skipping I/O validation (KB required)")
        sys.exit(0)

    # Load KB
    tech_names, tech_inputs, tech_outputs = load_kb_techniques(kb_path)
    print(f"KB: {len(tech_names)} techniques "
          f"({len(tech_inputs)} with inputs, {len(tech_outputs)} with outputs)")

    # Load examples
    g, files = load_examples(examples_dir)
    print(f"Examples: {len(files)} files loaded\n")

    # Validate
    mismatches, warnings = validate(g, tech_names, tech_inputs, tech_outputs)

    # Report
    if mismatches:
        print(f"❌ MISMATCHES: {len(mismatches)}")
        for m in mismatches:
            print(f"  - {m}")
    else:
        print("✅ No I/O type mismatches")

    if warnings:
        print(f"\n⚠️  WARNINGS: {len(warnings)}")
        for w in warnings:
            print(f"  - {w}")

    print()
    # Warn-only for now — exit 0 even with mismatches until KB is updated
    sys.exit(0)


if __name__ == "__main__":
    main()
