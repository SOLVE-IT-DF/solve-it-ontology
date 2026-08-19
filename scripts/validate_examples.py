#!/usr/bin/env python3
"""
Validate SOLVE-IT examples file against the ontology definitions.
Checks that all properties and classes used in examples are actually defined.
"""

from pathlib import Path
from rdflib import Graph, Namespace, RDF, RDFS, OWL, XSD, Literal, URIRef
from collections import defaultdict
import re

# Namespaces
SOLVEIT_CORE = Namespace("https://ontology.solveit-df.org/solveit/core/")
SOLVEIT_OBS = Namespace("https://ontology.solveit-df.org/solveit/observable/")
SOLVEIT_ANALYSIS = Namespace("https://ontology.solveit-df.org/solveit/analysis/")
SOLVEIT_DATA = Namespace("https://ontology.solveit-df.org/solveit/data/")  # External KB

def _local_name(iri):
    """Extract the local name from an IRI (after last / or #)."""
    for sep in ("#", "/"):
        idx = iri.rfind(sep)
        if idx >= 0:
            return iri[idx + 1:]
    return iri

def _short_label(graph, node):
    """Return rdfs:label if available, otherwise the IRI local name."""
    for label in graph.objects(node, RDFS.label):
        return str(label)
    return _local_name(str(node))

def load_ontology_definitions(project_root):
    """Load all ontology TTL files and extract defined classes and properties."""
    g = Graph()

    # Load all ontology files (not examples or shapes)
    ontology_files = sorted(project_root.glob("solve_it_*.ttl"))
    ontology_files = [f for f in ontology_files if "shapes" not in f.name]

    for ttl_file in ontology_files:
        if ttl_file.exists():
            print(f"Loading {ttl_file.name}...")
            g.parse(ttl_file, format="turtle")

    # Extract defined classes
    defined_classes = set()
    for s in g.subjects(RDF.type, OWL.Class):
        defined_classes.add(str(s))

    # Extract defined properties (both object and datatype properties)
    defined_properties = set()
    for s in g.subjects(RDF.type, OWL.ObjectProperty):
        defined_properties.add(str(s))
    for s in g.subjects(RDF.type, OWL.DatatypeProperty):
        defined_properties.add(str(s))

    # Extract domain and range constraints
    property_domains = {}
    property_ranges = {}
    for prop in defined_properties:
        prop_uri = URIRef(prop)
        # Get domain(s)
        domains = list(g.objects(prop_uri, RDFS.domain))
        expanded_domains = []
        for domain in domains:
            # Check if domain is a blank node (union)
            if isinstance(domain, URIRef):
                expanded_domains.append(str(domain))
            else:
                # It's a blank node - check for owl:unionOf
                union_list = list(g.objects(domain, OWL.unionOf))
                if union_list:
                    # Parse the RDF list
                    from rdflib.collection import Collection
                    for union_item in union_list:
                        col = Collection(g, union_item)
                        expanded_domains.extend([str(item) for item in col])
        if expanded_domains:
            property_domains[prop] = expanded_domains

        # Get range(s)
        ranges = list(g.objects(prop_uri, RDFS.range))
        if ranges:
            property_ranges[prop] = [str(r) for r in ranges]

    # The technique classes the examples type their actions with are defined in
    # the generated knowledge base, not in the ontology files: solve_it_core.ttl
    # defines the Technique metaclass, but each techniqueDFT-NNNN -- and the
    # rdfs:subClassOf that makes it a SolveitInvestigativeAction -- is emitted
    # by the KB generator. Without it the examples cannot be resolved against a
    # complete schema. Loaded after the extraction above so that
    # defined_classes/properties and the domain and range constraints still
    # describe the ontology alone; this graph is used only for subclass walks
    # and for reading the techniques' declared I/O classes.
    # Refreshed hourly on main by the generate-knowledge-base workflow. Its
    # absence is not fatal -- the same choice validate_example_io.py makes.
    kb_path = project_root / "docs" / "data" / "solve-it-kb.ttl"
    kb_graph = None
    if kb_path.exists():
        print(f"Loading {kb_path.relative_to(project_root)}...")
        kb_graph = Graph()
        kb_graph.parse(kb_path, format="turtle")
        g += kb_graph
    else:
        print(f"Warning: knowledge base not found at {kb_path}")
        print("Technique classes will be unresolved; run generate-knowledge-base.")

    return (defined_classes, defined_properties, property_domains,
            property_ranges, g, kb_graph)

def get_instance_type(g, instance):
    """Get the rdf:type of an instance."""
    types = list(g.objects(URIRef(instance), RDF.type))
    return [str(t) for t in types]

def is_subclass_of(subclass_uri, superclass_uri, ontology_graph, visited=None):
    """Check if subclass_uri is a (transitive) subclass of superclass_uri."""
    if visited is None:
        visited = set()
    if subclass_uri in visited:
        return False
    visited.add(subclass_uri)
    for parent in ontology_graph.objects(subclass_uri, RDFS.subClassOf):
        if parent == superclass_uri:
            return True
        if is_subclass_of(parent, superclass_uri, ontology_graph, visited):
            return True
    return False


def is_instance_of_class_or_subclass(instance_types, target_class, ontology_graph):
    """Check if instance is of target class or a (transitive) subclass."""
    if not instance_types:
        return False
    target_uri = URIRef(target_class)
    for inst_type in instance_types:
        if inst_type == target_class:
            return True
        if is_subclass_of(URIRef(inst_type), target_uri, ontology_graph):
            return True
    return False

def validate_id_format(id_value, expected_prefixes):
    """Validate ID format (e.g., T1002, DFT-1002, W1004, DFW-1004, M1003, DFM-1003)."""
    for prefix in expected_prefixes:
        pattern = f"^{re.escape(prefix)}\\d+$"
        if re.match(pattern, id_value):
            return True
    return False

def validate_examples(project_root, defined_classes, defined_properties, property_domains, property_ranges, ontology_graph, kb_graph=None):
    """Validate all example files in the solve_it_examples directory against the ontology definitions."""
    examples_dir = project_root / "solve_it_examples"

    if not examples_dir.exists():
        print(f"Error: {examples_dir} not found")
        return False

    # Find all TTL files in the examples directory
    example_files = list(examples_dir.glob("*.ttl"))
    if not example_files:
        print(f"Error: No .ttl files found in {examples_dir}")
        return False

    print(f"\nFound {len(example_files)} example file(s):")
    for f in sorted(example_files):
        print(f"  - {f.name}")

    # Load all example files into a single graph
    g = Graph()
    for examples_file in sorted(example_files):
        print(f"\nLoading {examples_file.name}...")
        g.parse(examples_file, format="turtle")

    errors = []
    warnings = []

    # Track usage for reporting
    used_classes = defaultdict(list)
    used_properties = defaultdict(list)
    instances_by_class = defaultdict(list)

    # Required properties for each class
    required_properties = {
        str(SOLVEIT_CORE.Technique): [
            str(SOLVEIT_CORE.techniqueID),
            str(SOLVEIT_CORE.techniqueName)
        ],
        str(SOLVEIT_CORE.Weakness): [
            str(SOLVEIT_CORE.weaknessID),
            str(SOLVEIT_CORE.weaknessName)
        ],
        str(SOLVEIT_CORE.Mitigation): [
            str(SOLVEIT_CORE.mitigationID),
            str(SOLVEIT_CORE.mitigationName)
        ],
        str(SOLVEIT_CORE.Objective): [
            str(SOLVEIT_CORE.objectiveName),
            str(SOLVEIT_CORE.objectiveDescription)
        ]
    }

    # ID format validation patterns
    id_format_rules = {
        str(SOLVEIT_CORE.techniqueID): ['DFT-'],
        str(SOLVEIT_CORE.weaknessID): ['DFW-'],
        str(SOLVEIT_CORE.mitigationID): ['DFM-'],
    }

    # Collect all instances by type
    for s in g.subjects(RDF.type, None):
        for class_type in g.objects(s, RDF.type):
            class_str = str(class_type)
            if class_str.startswith(str(SOLVEIT_CORE)) or \
               class_str.startswith(str(SOLVEIT_OBS)) or \
               class_str.startswith(str(SOLVEIT_ANALYSIS)):
                instances_by_class[class_str].append(str(s))

    # Check all triples in examples
    for s, p, o in g:
        # Skip ontology metadata and standard RDF/RDFS/OWL predicates
        if str(p) in [str(RDF.type), str(RDFS.label), str(RDFS.comment)]:
            # Check if class is defined when used with rdf:type
            if str(p) == str(RDF.type):
                if str(o).startswith(str(SOLVEIT_CORE)) or \
                   str(o).startswith(str(SOLVEIT_OBS)) or \
                   str(o).startswith(str(SOLVEIT_ANALYSIS)):
                    if str(o) not in defined_classes:
                        errors.append(f"Undefined class used: {o}")
                    else:
                        used_classes[str(o)].append(str(s))
            continue

        # Skip standard namespace predicates
        if str(p).startswith("http://www.w3.org/") or \
           str(p).startswith("http://purl.org/"):
            continue

        # Check if property is defined in SOLVEIT namespaces
        if str(p).startswith(str(SOLVEIT_CORE)) or \
           str(p).startswith(str(SOLVEIT_OBS)) or \
           str(p).startswith(str(SOLVEIT_ANALYSIS)):
            prop_str = str(p)

            if prop_str not in defined_properties:
                errors.append(f"Undefined property used: {p} (in triple {s} -> {p} -> {o})")
                continue

            used_properties[prop_str].append(str(s))

            # Validation 1: Domain/Range Validation
            # Check domain constraint
            if prop_str in property_domains:
                subject_types = get_instance_type(g, str(s))
                domain_valid = False
                for domain in property_domains[prop_str]:
                    if is_instance_of_class_or_subclass(subject_types, domain, ontology_graph):
                        domain_valid = True
                        break

                if not domain_valid and subject_types:
                    domain_names = [d.split('/')[-1] for d in property_domains[prop_str]]
                    errors.append(f"Domain violation: {prop_str} used on {s} (type: {subject_types[0].split('/')[-1]}) but domain expects one of: {', '.join(domain_names)}")

            # Check range constraint for object properties
            if prop_str in property_ranges:
                range_constraint = property_ranges[prop_str][0]

                # Validation 2: Datatype Validation
                if str(range_constraint).startswith(str(XSD)):
                    # It's a datatype property - validate literal type
                    if isinstance(o, Literal):
                        if range_constraint == str(XSD.boolean):
                            if str(o).lower() not in ['true', 'false']:
                                errors.append(f"Datatype violation: {prop_str} on {s} has value '{o}' (expected boolean true/false)")
                        elif range_constraint == str(XSD.anyURI):
                            # Basic URI validation
                            if not (str(o).startswith('http://') or str(o).startswith('https://')):
                                warnings.append(f"URI format: {prop_str} on {s} has value '{o}' (expected URI)")
                    else:
                        # It's a URI but should be a literal
                        errors.append(f"Datatype violation: {prop_str} on {s} should be a literal value, got URI {o}")

                # Validation 5: Reference Integrity (for object properties)
                elif str(range_constraint).startswith(str(SOLVEIT_CORE)) or \
                     str(range_constraint).startswith(str(SOLVEIT_OBS)) or \
                     str(range_constraint).startswith(str(SOLVEIT_ANALYSIS)):
                    # It's an object property - check if referenced instance exists
                    if isinstance(o, URIRef):
                        # Skip validation for external KB references (solveit-data namespace)
                        if str(o).startswith(str(SOLVEIT_DATA)):
                            continue
                        object_types = get_instance_type(g, str(o))
                        if not object_types:
                            errors.append(f"Reference integrity: {prop_str} on {s} references {o} which is not defined in examples")
                        elif not is_instance_of_class_or_subclass(object_types, range_constraint, ontology_graph):
                            errors.append(f"Range violation: {prop_str} on {s} points to {o} (type: {object_types[0]}) but range is {range_constraint}")

            # Validation 4: ID Format Validation
            if prop_str in id_format_rules:
                if isinstance(o, Literal):
                    id_value = str(o)
                    expected_prefixes = id_format_rules[prop_str]
                    if not validate_id_format(id_value, expected_prefixes):
                        fmt_examples = " or ".join(f"{p}####" for p in expected_prefixes)
                        errors.append(f"ID format violation: {prop_str} on {s} has value '{id_value}' (expected format: {fmt_examples})")

    # Validation 3: Required Properties Check
    for class_uri, required_props in required_properties.items():
        if class_uri in instances_by_class:
            for instance in instances_by_class[class_uri]:
                instance_uri = URIRef(instance)
                for required_prop in required_props:
                    prop_uri = URIRef(required_prop)
                    if not list(g.objects(instance_uri, prop_uri)):
                        prop_name = required_prop.split('/')[-1]
                        class_name = class_uri.split('/')[-1]
                        errors.append(f"Missing required property: {instance} (type {class_name}) is missing {prop_name}")

    # Validation 6: Input/Output Type Compatibility
    # For SolveitInvestigativeAction instances, warn when the types of
    # uco-action:object (inputs) or uco-action:result (outputs) don't
    # match the hasCASEInputClass / hasCASEOutputClass declared on the
    # linked technique.  This is a warning, not an error — many techniques
    # don't have I/O classes mapped yet, and there may be valid variations.
    UCO_ACTION = Namespace("https://ontology.unifiedcyberontology.org/uco/action/")
    combined_graph = g + ontology_graph  # query across both

    # Under the UCO 1.5.0 Technique metaclass model, a performed action states
    # the technique it implements by rdf:type against the technique class,
    # rather than through a usedTechnique property. A technique class is any
    # node typed solveit-core:Technique in the examples or in the ontology.
    technique_classes = set(combined_graph.subjects(RDF.type, SOLVEIT_CORE.Technique))

    for action in set(g.subjects(RDF.type, None)):
        for technique_ref in [t for t in g.objects(action, RDF.type) if t in technique_classes]:
            # Collect expected I/O classes from the technique definition
            expected_inputs = set()
            expected_outputs = set()
            for cls_literal in combined_graph.objects(technique_ref, SOLVEIT_CORE.hasCASEInputClass):
                expected_inputs.add(str(cls_literal))
            for cls_literal in combined_graph.objects(technique_ref, SOLVEIT_CORE.hasCASEOutputClass):
                expected_outputs.add(str(cls_literal))

            # Skip if technique has no I/O classes defined (nothing to check)
            if not expected_inputs and not expected_outputs:
                continue

            # Collect actual types of uco-action:object (inputs)
            if expected_inputs:
                actual_input_types = set()
                for obj in g.objects(action, UCO_ACTION.object):
                    for t in g.objects(obj, RDF.type):
                        actual_input_types.add(str(t))
                if actual_input_types:
                    if not actual_input_types & expected_inputs:
                        tech_label = _short_label(combined_graph, technique_ref)
                        action_label = _short_label(g, action)
                        expected_names = ", ".join(sorted(_local_name(c) for c in expected_inputs))
                        actual_names = ", ".join(sorted(_local_name(t) for t in actual_input_types))
                        warnings.append(
                            f"Input type mismatch: {action_label} provides "
                            f"object types [{actual_names}] but technique "
                            f"{tech_label} expects [{expected_names}]"
                        )

            # Collect actual types of uco-action:result (outputs)
            if expected_outputs:
                actual_output_types = set()
                for res in g.objects(action, UCO_ACTION.result):
                    for t in g.objects(res, RDF.type):
                        actual_output_types.add(str(t))
                if actual_output_types:
                    if not actual_output_types & expected_outputs:
                        tech_label = _short_label(combined_graph, technique_ref)
                        action_label = _short_label(g, action)
                        expected_names = ", ".join(sorted(_local_name(c) for c in expected_outputs))
                        actual_names = ", ".join(sorted(_local_name(t) for t in actual_output_types))
                        warnings.append(
                            f"Output type mismatch: {action_label} produces "
                            f"result types [{actual_names}] but technique "
                            f"{tech_label} expects [{expected_names}]"
                        )

    # Report results
    print("\n" + "=" * 70)
    print("VALIDATION RESULTS")
    print("=" * 70)

    if errors:
        print(f"\n❌ ERRORS FOUND: {len(errors)}")
        for error in sorted(set(errors)):
            print(f"  - {error}")
    else:
        print("\n✅ No errors found!")

    if warnings:
        print(f"\n⚠️  WARNINGS: {len(warnings)}")
        for warning in sorted(set(warnings)):
            print(f"  - {warning}")

    print(f"\n📊 STATISTICS:")
    print(f"  - Defined classes: {len(defined_classes)}")
    print(f"  - Defined properties: {len(defined_properties)}")
    print(f"  - Classes used in examples: {len(used_classes)}")
    print(f"  - Properties used in examples: {len(used_properties)}")

    return len(errors) == 0

if __name__ == "__main__":
    project_root = Path(__file__).parent.parent

    print("SOLVE-IT Examples Validator")
    print("=" * 70)

    # Load ontology definitions
    (defined_classes, defined_properties, property_domains,
     property_ranges, ontology_graph, kb_graph) = load_ontology_definitions(project_root)

    # Validate examples
    is_valid = validate_examples(project_root, defined_classes, defined_properties, property_domains, property_ranges, ontology_graph, kb_graph)

    exit(0 if is_valid else 1)
