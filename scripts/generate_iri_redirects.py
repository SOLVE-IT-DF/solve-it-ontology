#!/usr/bin/env python3
"""
Generate IRI redirect folders for all classes and properties in the SOLVE-IT ontology.
This script reads the ontology TTL files, then creates folder structures with
index.html redirects so that IRIs resolve properly.

Two different names are involved, and they are not always the same string:

  * The redirect folder comes from the IRI itself, which has the form
    https://ontology.solveit-df.org/solveit/{module}/{name}. That is the path a
    reader dereferences, so it is what the folder has to match.
  * The redirect target comes from the prefix declared in the TTL file, because
    Ontospy names its pages after the prefix rather than the IRI.

For the weakness assessment module those differ: the namespace segment is
"weakness-assessment" while the declared prefix is "solveit-wa:", so the IRI
/solveit/weakness-assessment/hasEvaluation has to redirect to
prop-solveit-wahasevaluation.html. Deriving both from the source, rather than
reconstructing either by splitting a prefix string, is what keeps the two in
step as modules are added.
"""

import html
import re
import sys
from pathlib import Path
from typing import Dict, List, NamedTuple, Tuple

from rdflib import Graph, OWL, RDF

ONTOLOGY_BASE = "https://ontology.solveit-df.org/solveit/"


class Entity(NamedTuple):
    """One documented ontology term."""

    kind: str         # "class" or "property"
    module: str       # namespace segment from the IRI, e.g. "weakness-assessment"
    doc_prefix: str   # declared prefix without "solveit-", e.g. "wa"
    local_name: str   # e.g. "hasEvaluation"
    iri: str


def normalize_filename(local_name: str, doc_prefix: str = '') -> str:
    """
    Normalize a local name to match Ontospy's filename convention.
    Converts to lowercase and removes special characters.
    Includes the documentation prefix if provided.

    The prefix is used verbatim, because Ontospy keeps its hyphen:
    solveit-tool-profile:supportsTechnique becomes
    prop-solveit-tool-profilesupportstechnique.html.
    """
    normalized = re.sub(r'[^a-z0-9]', '', local_name.lower())

    if doc_prefix:
        return f"{doc_prefix}{normalized}"
    return normalized


def target_filename(entity: Entity) -> str:
    """Return the Ontospy page filename an entity's redirect should point at."""
    prefix = "class" if entity.kind == "class" else "prop"
    return f"{prefix}-solveit-{normalize_filename(entity.local_name, entity.doc_prefix)}.html"


def collect_entities(ttl_files: List[Path]) -> Tuple[List[Entity], List[str]]:
    """
    Read the ontology files and return every class and property in the SOLVE-IT
    namespace, together with any whose namespace has no declared solveit- prefix.

    Entities are keyed on (module, local name) rather than on the local name
    alone. Two modules may legitimately define the same local name, for example
    solveit-analysis:hasArtifact on a ForensicToolTagBasedReport and
    solveit-observable:hasArtifact on an ArtifactSet, and keying on the name
    alone silently discarded one of them.
    """
    graph = Graph()
    for ttl_file in ttl_files:
        print(f"  Processing {ttl_file.name}...")
        graph.parse(ttl_file, format="turtle")

    # Declared prefix for each SOLVE-IT namespace, e.g.
    # "https://ontology.solveit-df.org/solveit/weakness-assessment/" -> "wa"
    doc_prefixes: Dict[str, str] = {}
    for prefix, namespace in graph.namespaces():
        namespace = str(namespace)
        if namespace.startswith(ONTOLOGY_BASE) and prefix.startswith("solveit-"):
            doc_prefixes[namespace] = prefix[len("solveit-"):]

    entities: Dict[Tuple[str, str], Entity] = {}
    unprefixed: List[str] = []

    kinds = (
        ("class", OWL.Class),
        ("property", OWL.ObjectProperty),
        ("property", OWL.DatatypeProperty),
    )
    for kind, rdf_type in kinds:
        for subject in graph.subjects(RDF.type, rdf_type):
            iri = str(subject)
            if not iri.startswith(ONTOLOGY_BASE):
                continue

            remainder = iri[len(ONTOLOGY_BASE):]
            if remainder.count("/") != 1:
                continue
            module, local_name = remainder.split("/")
            if not module or not local_name:
                continue

            namespace = iri[:len(iri) - len(local_name)]
            doc_prefix = doc_prefixes.get(namespace)
            if doc_prefix is None:
                unprefixed.append(iri)
                continue

            entities[(module, local_name)] = Entity(
                kind=kind,
                module=module,
                doc_prefix=doc_prefix,
                local_name=local_name,
                iri=iri,
            )

    return sorted(entities.values()), sorted(set(unprefixed))


def create_redirect_html(entity: Entity, base_domain: str) -> str:
    """
    Create an HTML redirect file content.

    Args:
        entity: The ontology term the redirect is for
        base_domain: The base domain for canonical URLs
    """
    target_file = target_filename(entity)

    # Redirects are at docs/solveit/{module}/{name}/index.html and the target is
    # at docs/{prefix}-solveit-{normalized}.html, so go up three levels.
    relative_path = f"../../../{target_file}"

    escaped_name = html.escape(entity.local_name)
    escaped_domain = html.escape(base_domain)
    escaped_file = html.escape(target_file)
    escaped_relative = html.escape(relative_path)

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>SOLVE-IT {escaped_name} - Redirecting...</title>
    <link rel="canonical" href="{escaped_domain}/{escaped_file}">
    <meta http-equiv="refresh" content="0; url={escaped_relative}">
    <script>window.location.href = "{escaped_relative}";</script>
</head>
<body>
    <p>Redirecting to <a href="{escaped_relative}">SOLVE-IT {escaped_name} documentation</a>...</p>
</body>
</html>
"""
    return html_content


def generate_redirects(docs_dir: Path, base_domain: str = "https://ontology.solveit-df.org") -> bool:
    """
    Generate redirect folders and index.html files for all ontology entities.

    Returns True on success. Nothing is written if any redirect would point at a
    page that does not exist, because a redirect to a missing page is a 404 that
    only shows up when someone dereferences the IRI.

    Args:
        docs_dir: Path to the docs directory
        base_domain: Base domain for canonical URLs
    """
    # The ontology files in the project root (parent of the scripts directory).
    # This is the same set that the documentation is built from, so that every
    # redirect has a page to point at.
    project_root = Path(__file__).parent.parent
    ttl_files = sorted(project_root.glob("solve_it_*.ttl"))

    if not ttl_files:
        print("No ontology TTL files found in project root")
        return False

    print("Parsing TTL files...")
    entities, unprefixed = collect_entities(ttl_files)

    if unprefixed:
        print(f"\nERROR: {len(unprefixed)} entities are in the SOLVE-IT namespace "
              f"but their namespace has no declared solveit- prefix, so the "
              f"documentation filename cannot be determined:")
        for iri in unprefixed:
            print(f"  {iri}")
        return False

    classes = [e for e in entities if e.kind == "class"]
    properties = [e for e in entities if e.kind == "property"]
    modules = sorted({e.module for e in entities})
    print(f"\nFound {len(classes)} classes and {len(properties)} properties "
          f"across {len(modules)} modules: {', '.join(modules)}")

    missing = [(e, target_filename(e)) for e in entities
               if not (docs_dir / target_filename(e)).exists()]
    if missing:
        print(f"\nERROR: {len(missing)} redirects would point at a page that "
              f"does not exist. No redirects written.")
        for entity, target in missing:
            print(f"  {entity.iri} -> {target}")
        return False

    print("\nCreating redirect folders...")
    for entity in entities:
        folder = docs_dir / "solveit" / entity.module / entity.local_name
        folder.mkdir(parents=True, exist_ok=True)

        index_file = folder / "index.html"
        index_file.write_text(create_redirect_html(entity, base_domain), encoding='utf-8')
        print(f"  Created solveit/{entity.module}/{entity.local_name}/index.html")

    print(f"\n✓ Successfully created {len(entities)} redirect folders")
    return True


if __name__ == "__main__":
    # Determine the docs directory (in project root, parent of scripts directory)
    project_root = Path(__file__).parent.parent
    docs_dir = project_root / "docs"

    if not docs_dir.exists():
        print(f"Error: docs directory not found at {docs_dir}")
        sys.exit(1)

    if not generate_redirects(docs_dir):
        sys.exit(1)
