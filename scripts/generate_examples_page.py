#!/usr/bin/env python3
"""
Generate an HTML page documenting example instances from solve_it_examples.ttl
This page will be integrated into the ontology documentation.
"""

from pathlib import Path
from rdflib import Graph, Namespace, RDF, RDFS, Literal, BNode
from rdflib.collection import Collection
from collections import defaultdict
import html

# Namespaces
SOLVEIT_CORE = Namespace("https://ontology.solveit-df.org/solveit/core/")
SOLVEIT_OBS = Namespace("https://ontology.solveit-df.org/solveit/observable/")
SOLVEIT_ANALYSIS = Namespace("https://ontology.solveit-df.org/solveit/analysis/")
UCO_OBS = Namespace("https://ontology.unifiedcyberontology.org/uco/observable/")
XSD = Namespace("http://www.w3.org/2001/XMLSchema#")

def get_qname(uri, g):
    """Get a qualified name for a URI."""
    uri_str = str(uri)

    # Handle SOLVEIT namespaces
    if uri_str.startswith(str(SOLVEIT_CORE)):
        return f"solveit-core:{uri_str[len(str(SOLVEIT_CORE)):]}"
    elif uri_str.startswith(str(SOLVEIT_OBS)):
        return f"solveit-observable:{uri_str[len(str(SOLVEIT_OBS)):]}"
    elif uri_str.startswith(str(SOLVEIT_ANALYSIS)):
        return f"solveit-analysis:{uri_str[len(str(SOLVEIT_ANALYSIS)):]}"
    elif uri_str.startswith(str(UCO_OBS)):
        return f"uco-observable:{uri_str[len(str(UCO_OBS)):]}"
    elif uri_str.startswith("http://www.w3.org/2001/XMLSchema#"):
        return f"xsd:{uri_str[len('http://www.w3.org/2001/XMLSchema#'):]}"

    return uri_str

def get_class_link(class_uri):
    """Generate a link to the class documentation page."""
    class_str = str(class_uri)

    if class_str.startswith(str(SOLVEIT_CORE)):
        local_name = class_str[len(str(SOLVEIT_CORE)):]
        normalized = local_name.lower()
        return f"class-solveit-core{normalized}.html"
    elif class_str.startswith(str(SOLVEIT_OBS)):
        local_name = class_str[len(str(SOLVEIT_OBS)):]
        normalized = local_name.lower()
        return f"class-solveit-observable{normalized}.html"
    elif class_str.startswith(str(SOLVEIT_ANALYSIS)):
        local_name = class_str[len(str(SOLVEIT_ANALYSIS)):]
        normalized = local_name.lower()
        return f"class-solveit-analysis{normalized}.html"

    return None

def get_property_link(prop_uri):
    """Generate a link to the property documentation page."""
    prop_str = str(prop_uri)

    if prop_str.startswith(str(SOLVEIT_CORE)):
        local_name = prop_str[len(str(SOLVEIT_CORE)):]
        normalized = local_name.lower()
        return f"prop-solveit-core{normalized}.html"
    elif prop_str.startswith(str(SOLVEIT_OBS)):
        local_name = prop_str[len(str(SOLVEIT_OBS)):]
        normalized = local_name.lower()
        return f"prop-solveit-observable{normalized}.html"
    elif prop_str.startswith(str(SOLVEIT_ANALYSIS)):
        local_name = prop_str[len(str(SOLVEIT_ANALYSIS)):]
        normalized = local_name.lower()
        return f"prop-solveit-analysis{normalized}.html"

    return None

def is_rdf_list(node, g):
    """Check if a node is an RDF List."""
    if not isinstance(node, BNode):
        return False
    # Check if it has rdf:first (it's a list node) or is rdf:nil
    return (node, RDF.first, None) in g or node == RDF.nil

def format_rdf_list(list_node, g):
    """Format an RDF List for display."""
    try:
        # Use rdflib's Collection to parse the list
        collection = Collection(g, list_node)
        items = []
        for item in collection:
            items.append(format_value(item, g))
        return f"( {' '.join(items)} )"
    except:
        # Fallback if Collection doesn't work
        return str(list_node)

def format_value(value, g):
    """Format an RDF value for display."""
    if isinstance(value, Literal):
        # Handle typed literals
        if value.datatype:
            datatype_qname = get_qname(value.datatype, g)
            return f'"{html.escape(str(value))}"^^{datatype_qname}'
        # Handle language-tagged literals
        elif value.language:
            return f'"{html.escape(str(value))}"@{value.language}'
        else:
            return f'"{html.escape(str(value))}"'
    elif isinstance(value, BNode):
        # Check if it's an RDF List
        if is_rdf_list(value, g):
            return format_rdf_list(value, g)
        # Otherwise it's a blank node (shouldn't normally happen in our examples)
        return f"_:{value}"
    else:
        # It's a URI reference
        qname = get_qname(value, g)
        # Check if it's a local instance
        if str(value).startswith("https://ontology.solveit-df.org/solveit/examples/"):
            local_name = str(value).split("/")[-1]
            return f'<a href="#{local_name}">{html.escape(qname)}</a>'
        return html.escape(qname)

def get_instance_order(examples_file):
    """Parse the TTL file to get the order of instance declarations."""
    instance_order = []
    with open(examples_file, 'r', encoding='utf-8') as f:
        for line in f:
            # Look for instance declarations like ":instanceName rdf:type"
            if 'rdf:type' in line and not line.strip().startswith('#'):
                # Extract the instance identifier
                parts = line.strip().split()
                if len(parts) >= 3 and parts[0].startswith(':'):
                    instance_id = parts[0].rstrip(';')
                    instance_order.append(instance_id)
    return instance_order


def get_instance_order_from_files(example_files):
    """Parse multiple TTL files to get the order of instance declarations."""
    instance_order = []
    for examples_file in example_files:
        instance_order.extend(get_instance_order(examples_file))
    return instance_order

def generate_html(example_files, output_file):
    """Generate the examples HTML page from multiple example files."""

    # Load all examples into a single graph
    g = Graph()
    for examples_file in example_files:
        print(f"  Loading {examples_file.name}...")
        g.parse(examples_file, format="turtle")

    # Get the order of instances from all TTL files
    instance_order_ids = get_instance_order_from_files(example_files)

    # Group instances by class, preserving order
    instances_by_class = defaultdict(list)
    instance_to_class = {}

    # Find all instances
    for s in g.subjects(RDF.type, None):
        # Skip blank nodes and ontology definitions
        if isinstance(s, Literal) or str(s).endswith("/examples"):
            continue

        # Get the class(es)
        for class_uri in g.objects(s, RDF.type):
            # Only process SOLVEIT and UCO classes
            class_str = str(class_uri)
            if class_str.startswith(str(SOLVEIT_CORE)) or \
               class_str.startswith(str(SOLVEIT_OBS)) or \
               class_str.startswith(str(SOLVEIT_ANALYSIS)) or \
               class_str.startswith(str(UCO_OBS)):
                instances_by_class[class_uri].append(s)
                instance_to_class[s] = class_uri

    # Start building HTML
    html_parts = []

    # HTML header
    html_parts.append("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SOLVE-IT Ontology Examples</title>
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css">
    <style>
        body { padding-top: 20px; }
        .page-header { border-bottom: 2px solid #eee; padding-bottom: 10px; margin-bottom: 30px; }
        .example-instance {
            background: #f9f9f9;
            border-left: 4px solid #337ab7;
            padding: 15px;
            margin-bottom: 25px;
            border-radius: 3px;
        }
        .instance-header {
            font-size: 1.3em;
            font-weight: bold;
            color: #337ab7;
            margin-bottom: 10px;
        }
        .instance-type {
            color: #666;
            font-size: 0.9em;
            margin-bottom: 15px;
        }
        .property-table {
            background: white;
            margin-top: 10px;
        }
        .property-name {
            font-family: monospace;
            color: #d14;
            font-weight: 500;
        }
        .property-value {
            font-family: monospace;
            color: #099;
        }
        .class-section {
            margin-bottom: 40px;
        }
        .class-title {
            font-size: 1.8em;
            color: #333;
            margin-top: 30px;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 1px solid #ddd;
        }
        .breadcrumb {
            background-color: #f5f5f5;
            margin-bottom: 20px;
        }
        code {
            background-color: #f5f5f5;
            padding: 2px 6px;
            border-radius: 3px;
        }
    </style>
</head>
<body>
    <div class="container">
        <ol class="breadcrumb">
            <li><a href="index.html">SOLVE-IT Ontology</a></li>
            <li class="active">Examples</li>
        </ol>

        <div class="page-header">
            <h1>SOLVE-IT Ontology Examples</h1>
            <p class="lead">Example instances demonstrating the use of SOLVE-IT classes and properties.</p>
        </div>
""")

    # Create ordered list of instances based on TTL file order
    ordered_instances = []
    for instance_id in instance_order_ids:
        # Find the full URI for this instance
        for instance_uri in instance_to_class.keys():
            if str(instance_uri).endswith('/' + instance_id.lstrip(':')):
                ordered_instances.append(instance_uri)
                break

    # Generate content, preserving TTL file order
    current_class = None
    for instance_uri in ordered_instances:
        if instance_uri not in instance_to_class:
            continue

        class_uri = instance_to_class[instance_uri]

        # If we're starting a new class section, add the header
        if class_uri != current_class:
            if current_class is not None:
                html_parts.append('        </div>\n')  # Close previous class section

            class_qname = get_qname(class_uri, g)
            class_link = get_class_link(class_uri)

            html_parts.append(f'        <div class="class-section">\n')

            if class_link:
                html_parts.append(f'            <h2 class="class-title">Examples of <a href="{class_link}">{html.escape(class_qname)}</a></h2>\n')
            else:
                html_parts.append(f'            <h2 class="class-title">Examples of {html.escape(class_qname)}</h2>\n')

            current_class = class_uri

        # Process this instance
        instance_id = str(instance_uri).split("/")[-1]

        # Get label
        label = None
        for lbl in g.objects(instance_uri, RDFS.label):
            label = str(lbl)
            break

        html_parts.append(f'            <div class="example-instance" id="{instance_id}">\n')

        if label:
            html_parts.append(f'                <div class="instance-header">{html.escape(label)}</div>\n')
        else:
            html_parts.append(f'                <div class="instance-header">{html.escape(instance_id)}</div>\n')

        html_parts.append(f'                <div class="instance-type">Instance URI: <code>{html.escape(str(instance_uri))}</code></div>\n')

        # Build property table
        html_parts.append('                <table class="table table-bordered table-condensed property-table">\n')
        html_parts.append('                    <thead><tr><th width="35%">Property</th><th>Value</th></tr></thead>\n')
        html_parts.append('                    <tbody>\n')

        # Get all properties
        properties = []
        for p, o in g.predicate_objects(instance_uri):
            # Skip rdf:type (already shown) and rdfs:label (already shown in header)
            if p != RDF.type and p != RDFS.label:
                properties.append((p, o))

        # Sort properties
        properties.sort(key=lambda x: str(x[0]))

        for prop, value in properties:
            prop_qname = get_qname(prop, g)
            prop_link = get_property_link(prop)

            formatted_value = format_value(value, g)

            html_parts.append('                        <tr>\n')

            if prop_link:
                html_parts.append(f'                            <td class="property-name"><a href="{prop_link}">{html.escape(prop_qname)}</a></td>\n')
            else:
                html_parts.append(f'                            <td class="property-name">{html.escape(prop_qname)}</td>\n')

            html_parts.append(f'                            <td class="property-value">{formatted_value}</td>\n')
            html_parts.append('                        </tr>\n')

        html_parts.append('                    </tbody>\n')
        html_parts.append('                </table>\n')
        html_parts.append('            </div>\n')

    # Close the last class section
    if current_class is not None:
        html_parts.append('        </div>\n')

    # HTML footer
    file_list = ', '.join(f'<code>{f.name}</code>' for f in example_files)
    html_parts.append(f"""
        <hr>
        <footer>
            <p class="text-muted">Generated from {file_list}</p>
        </footer>
    </div>
</body>
</html>
""")

    # Write output
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(''.join(html_parts))

    print(f"✓ Generated examples page: {output_file}")
    print(f"  - {len(instances_by_class)} classes with examples")
    total_instances = sum(len(instances) for instances in instances_by_class.values())
    print(f"  - {total_instances} example instances")

if __name__ == "__main__":
    project_root = Path(__file__).parent.parent
    examples_dir = project_root / "solve_it_examples"
    output_file = project_root / "docs" / "examples.html"

    if not examples_dir.exists():
        print(f"Error: {examples_dir} not found")
        exit(1)

    # Find all TTL files in the examples directory
    example_files = sorted(examples_dir.glob("*.ttl"))
    if not example_files:
        print(f"Error: No .ttl files found in {examples_dir}")
        exit(1)

    print(f"Found {len(example_files)} example file(s):")
    for f in example_files:
        print(f"  - {f.name}")

    if not output_file.parent.exists():
        output_file.parent.mkdir(parents=True, exist_ok=True)

    generate_html(example_files, output_file)
