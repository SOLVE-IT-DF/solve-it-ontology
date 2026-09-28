#!/usr/bin/env python3
"""
Validate SOLVE-IT ontology files and SHACL shapes.
Checks syntax, and cross-references SHACL shapes against defined OWL classes/properties.
"""

from pathlib import Path
from rdflib import Graph, Namespace, RDF, OWL, URIRef
from rdflib.collection import Collection

# Namespaces
SH = Namespace("http://www.w3.org/ns/shacl#")

# External namespaces we skip validation for (can't resolve them)
EXTERNAL_PREFIXES = (
    "https://ontology.unifiedcyberontology.org/",
    "http://www.w3.org/",
    "http://purl.org/",
)


def is_external(uri):
    """Check if a URI belongs to an external namespace we can't validate."""
    uri_str = str(uri)
    return any(uri_str.startswith(prefix) for prefix in EXTERNAL_PREFIXES)


def load_ontology(project_root):
    """Load all solve_it_*.ttl files (excluding shapes) and extract classes/properties."""
    g = Graph()

    ontology_files = sorted(project_root.glob("solve_it_*.ttl"))
    ontology_files = [f for f in ontology_files if "shapes" not in f.name]

    for ttl_file in ontology_files:
        print(f"  Loading {ttl_file.name}...")
        g.parse(ttl_file, format="turtle")

    # Extract defined classes
    defined_classes = set()
    for s in g.subjects(RDF.type, OWL.Class):
        defined_classes.add(str(s))

    # Extract defined properties
    defined_properties = set()
    for s in g.subjects(RDF.type, OWL.ObjectProperty):
        defined_properties.add(str(s))
    for s in g.subjects(RDF.type, OWL.DatatypeProperty):
        defined_properties.add(str(s))

    return g, defined_classes, defined_properties


def load_shapes(project_root):
    """Load every SHACL shapes file into one graph.

    Globbed rather than named, so a new module's shapes are picked up by
    adding the file rather than by remembering to edit this list.
    """
    shape_files = sorted(project_root.glob("*_shapes.ttl"))
    if not shape_files:
        print(f"  No *_shapes.ttl files found in {project_root}")
        return None

    g = Graph()
    for shapes_file in shape_files:
        print(f"  Loading {shapes_file.name}...")
        g.parse(shapes_file, format="turtle")
    return g


def collect_sh_classes(shapes_graph):
    """Collect all sh:class values, including those nested in sh:or / sh:xone lists."""
    classes = set()

    # Direct sh:class on property constraints
    for obj in shapes_graph.objects(None, SH["class"]):
        classes.add(obj)

    return classes


def collect_sh_or_classes(shapes_graph):
    """Collect sh:class values from inside sh:or and sh:xone list items."""
    classes = set()

    for list_pred in [SH["or"], SH["xone"]]:
        for _, list_head in shapes_graph.subject_objects(list_pred):
            try:
                col = Collection(shapes_graph, list_head)
                for item in col:
                    for cls in shapes_graph.objects(item, SH["class"]):
                        classes.add(cls)
            except Exception:
                pass

    return classes


def validate(project_root):
    """Run all validation checks. Returns True if no errors found."""
    errors = []

    # --- Step 1: Syntax validation (parse all TTL files) ---
    print("\n[1/2] Syntax validation...")
    all_ttl = sorted(project_root.glob("solve_it_*.ttl"))
    for ttl_file in all_ttl:
        try:
            g = Graph()
            g.parse(ttl_file, format="turtle")
            print(f"  OK: {ttl_file.name}")
        except Exception as e:
            errors.append(f"Syntax error in {ttl_file.name}: {e}")
            print(f"  FAIL: {ttl_file.name}: {e}")

    # --- Step 2: SHACL cross-reference checks ---
    print("\n[2/2] SHACL cross-reference checks...")

    print("\nLoading ontology definitions...")
    ontology_graph, defined_classes, defined_properties = load_ontology(project_root)
    print(f"  Found {len(defined_classes)} classes, {len(defined_properties)} properties")

    print("\nLoading shapes...")
    shapes_graph = load_shapes(project_root)

    if shapes_graph is None:
        print("  Skipping SHACL checks (no shapes file)")
    else:
        # Check sh:targetClass
        print("\nChecking sh:targetClass references...")
        for shape, target_class in shapes_graph.subject_objects(SH.targetClass):
            if is_external(target_class):
                continue
            if str(target_class) not in defined_classes:
                shape_name = str(shape).split("/")[-1]
                errors.append(
                    f"sh:targetClass references undefined class: {target_class} "
                    f"(in shape {shape_name})"
                )
                print(f"  FAIL: {shape_name} -> {target_class}")
            else:
                print(f"  OK: {target_class}")

        # Check sh:class (direct + inside sh:or/sh:xone)
        print("\nChecking sh:class references...")
        all_sh_classes = collect_sh_classes(shapes_graph) | collect_sh_or_classes(shapes_graph)
        for cls in sorted(all_sh_classes, key=str):
            if is_external(cls):
                print(f"  SKIP (external): {cls}")
                continue
            if str(cls) not in defined_classes:
                errors.append(f"sh:class references undefined class: {cls}")
                print(f"  FAIL: {cls}")
            else:
                print(f"  OK: {cls}")

        # Check sh:path
        print("\nChecking sh:path references...")
        for _, path_val in shapes_graph.subject_objects(SH.path):
            if not isinstance(path_val, URIRef):
                continue
            if is_external(path_val):
                print(f"  SKIP (external): {path_val}")
                continue
            if str(path_val) not in defined_properties:
                errors.append(f"sh:path references undefined property: {path_val}")
                print(f"  FAIL: {path_val}")
            else:
                print(f"  OK: {path_val}")

    # --- Summary ---
    print("\n" + "=" * 70)
    if errors:
        print(f"VALIDATION FAILED — {len(errors)} error(s):\n")
        for err in errors:
            print(f"  - {err}")
        print()
        return False
    else:
        print("VALIDATION PASSED — all checks OK")
        return True


if __name__ == "__main__":
    project_root = Path(__file__).parent.parent

    print("SOLVE-IT Ontology Validator")
    print("=" * 70)

    success = validate(project_root)
    exit(0 if success else 1)
