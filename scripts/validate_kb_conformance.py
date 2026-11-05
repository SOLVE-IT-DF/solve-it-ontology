#!/usr/bin/env python3
"""
Check the generated knowledge base against the ontology it claims to use.

The knowledge base is built by reporting_scripts/generate_rdf_from_kb.py in the
solve-it repository, which mints terms through rdflib Namespace objects. A
Namespace is a string with attribute access, so SOLVEIT_CORE.anything returns an
IRI whether or not the ontology defines that term, and the generator never reads
the ontology. Nothing else in this repository checks the knowledge base itself:
validate_ontology.py does not load it, and validate_examples.py and
validate_example_io.py load it only as the reference to check the examples
against.

That combination let six terms be published in the ontology's own namespace
without ever being defined in it - solveit-core:Citation, citationID,
citationPlaintext, citationBibtex, objectiveID and sortOrder - and let
hasReference be used 241 times with an IRI object while it was declared a
datatype property. This script closes that gap.

Two checks:

  1. Every SOLVE-IT ontology term the knowledge base uses is defined in the
     ontology. The solveit-data namespace is excluded, because that is where
     knowledge base entries live rather than ontology terms.
  2. No property is used against its declared kind: an owl:DatatypeProperty
     with an IRI object, or an owl:ObjectProperty with a literal object. Both
     are invalid in OWL DL and neither shows up without a reasoner.
"""

import sys
from collections import Counter
from pathlib import Path

from rdflib import Graph, Literal, OWL, RDF, RDFS, URIRef

ONTOLOGY_BASE = "https://ontology.solveit-df.org/solveit/"
# Knowledge base entries, not ontology terms.
DATA_NAMESPACE = ONTOLOGY_BASE + "data/"


def load_ontology(project_root):
    """Load the ontology files and return the graph and every term it defines."""
    graph = Graph()
    ttl_files = sorted(project_root.glob("solve_it_*.ttl"))
    if not ttl_files:
        print("No ontology TTL files found in project root")
        return None, set()

    for ttl_file in ttl_files:
        print(f"Loading {ttl_file.name}...")
        graph.parse(ttl_file, format="turtle")

    defined = set()
    for rdf_type in (OWL.Class, OWL.ObjectProperty, OWL.DatatypeProperty,
                     OWL.AnnotationProperty, OWL.NamedIndividual, RDF.Property):
        for subject in graph.subjects(RDF.type, rdf_type):
            defined.add(str(subject))
    return graph, defined


def is_ontology_term(iri):
    """True for a SOLVE-IT ontology IRI, false for a knowledge base entry."""
    return iri.startswith(ONTOLOGY_BASE) and not iri.startswith(DATA_NAMESPACE)


def check_terms_defined(kb, defined, errors):
    """Report SOLVE-IT ontology terms the knowledge base uses but never defines."""
    used = Counter()
    for subject, predicate, obj in kb:
        for node in (predicate, obj):
            if isinstance(node, URIRef) and is_ontology_term(str(node)):
                used[str(node)] += 1

    undefined = {iri: n for iri, n in used.items() if iri not in defined}
    for iri, count in sorted(undefined.items(), key=lambda item: (-item[1], item[0])):
        errors.append(
            f"Undefined ontology term: <{iri}> is used {count} time"
            f"{'' if count == 1 else 's'} by the knowledge base but is not "
            f"defined in any ontology file"
        )
    return len(used)


def check_property_kinds(kb, ontology, errors):
    """Report properties used against the kind the ontology declares for them."""
    datatype_properties = {str(s) for s in ontology.subjects(RDF.type, OWL.DatatypeProperty)}
    object_properties = {str(s) for s in ontology.subjects(RDF.type, OWL.ObjectProperty)}

    misuse = Counter()
    for subject, predicate, obj in kb:
        name = str(predicate)
        if name in datatype_properties and isinstance(obj, URIRef):
            misuse[(name, "datatype property", "an IRI")] += 1
        elif name in object_properties and isinstance(obj, Literal):
            misuse[(name, "object property", "a literal")] += 1

    for (name, declared, found), count in sorted(misuse.items(), key=lambda item: -item[1]):
        ranges = [str(r) for r in ontology.objects(URIRef(name), RDFS.range)]
        range_note = f", declared range <{ranges[0]}>" if ranges else ""
        errors.append(
            f"Property used against its declared kind: <{name}> is an "
            f"owl:{'DatatypeProperty' if declared.startswith('datatype') else 'ObjectProperty'}"
            f"{range_note}, but the knowledge base gives it {found} on "
            f"{count} statement{'' if count == 1 else 's'}"
        )


def main():
    project_root = Path(__file__).parent.parent

    ontology, defined = load_ontology(project_root)
    if ontology is None:
        return 1

    kb_path = project_root / "docs" / "data" / "solve-it-kb.ttl"
    if not kb_path.exists():
        print(f"\nNo knowledge base at {kb_path.relative_to(project_root)}, nothing to check.")
        print("It is built by a separate workflow, so this is not a failure.")
        return 0

    print(f"Loading {kb_path.relative_to(project_root)}...")
    kb = Graph()
    kb.parse(kb_path, format="turtle")

    errors = []
    term_count = check_terms_defined(kb, defined, errors)
    check_property_kinds(kb, ontology, errors)

    print("\n" + "=" * 70)
    print("KNOWLEDGE BASE CONFORMANCE")
    print("=" * 70)
    print(f"Ontology terms defined            : {len(defined)}")
    print(f"Ontology term uses in the KB      : {term_count}")

    if errors:
        print(f"\nERRORS FOUND: {len(errors)}")
        for error in errors:
            print(f"  - {error}")
        print("\nThe knowledge base generator mints terms without consulting the")
        print("ontology, so a term it invents is published unless it is caught here.")
        print("Either define the term in the ontology or correct the generator in")
        print("the solve-it repository.")
        return 1

    print("\nCONFORMANCE PASSED - the knowledge base uses only defined terms")
    return 0


if __name__ == "__main__":
    sys.exit(main())
