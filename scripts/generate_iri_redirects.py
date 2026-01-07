#!/usr/bin/env python3
"""
Generate IRI redirect folders for all classes and properties in the SOLVE-IT ontology.
This script parses TTL files to extract classes and properties, then creates folder
structures with index.html redirects so that IRIs resolve properly.
"""

import html
import re
from pathlib import Path
from typing import Set, Tuple, Dict


def extract_local_name(uri: str) -> str:
    """Extract the local name from a URI."""
    if '#' in uri:
        return uri.split('#')[-1]
    elif '/' in uri:
        return uri.split('/')[-1]
    return uri


def extract_module_from_prefix(prefix: str) -> str:
    """
    Extract the module name from a namespace prefix.
    E.g., 'solveit-core:' -> 'core', 'solveit-analysis:' -> 'analysis'
    """
    if prefix.startswith('solveit-'):
        return prefix.split('-')[1].rstrip(':')
    return ''


def normalize_filename(local_name: str, module: str = '') -> str:
    """
    Normalize a local name to match Ontospy's filename convention.
    Converts to lowercase and removes special characters.
    Includes the module prefix if provided.
    """
    # Convert to lowercase and remove special characters
    normalized = local_name.lower()
    # Remove any remaining special characters that aren't alphanumeric
    normalized = re.sub(r'[^a-z0-9]', '', normalized)

    # Add module prefix if provided
    if module:
        return f"{module}{normalized}"
    return normalized


def parse_ttl_for_entities(ttl_file: Path) -> Tuple[Dict[str, str], Dict[str, str]]:
    """
    Parse a TTL file to extract classes and properties in the solveit namespace.
    Returns (classes, properties) as dictionaries mapping local names to module names.
    """
    classes = {}  # local_name -> module
    properties = {}  # local_name -> module

    with open(ttl_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find classes: lines like "solveit-core:Technique rdf:type owl:Class"
    class_pattern = rf'(\S+)\s+rdf:type\s+owl:Class'
    for match in re.finditer(class_pattern, content):
        entity = match.group(1)
        # Check if it's in our namespace (solveit-core:, solveit-analysis:, solveit-observable:, or :)
        if entity.startswith(('solveit-core:', 'solveit-analysis:', 'solveit-observable:')):
            prefix = entity.split(':')[0] + ':'
            local_name = entity.split(':')[-1]
            module = extract_module_from_prefix(prefix)
            classes[local_name] = module
        elif entity.startswith(':'):
            local_name = entity.split(':')[-1]
            # For default namespace, try to infer module from filename
            classes[local_name] = ''

    # Find object properties: lines like "solveit-core:hasWeakness rdf:type owl:ObjectProperty"
    obj_prop_pattern = rf'(\S+)\s+rdf:type\s+owl:ObjectProperty'
    for match in re.finditer(obj_prop_pattern, content):
        entity = match.group(1)
        if entity.startswith(('solveit-core:', 'solveit-analysis:', 'solveit-observable:')):
            prefix = entity.split(':')[0] + ':'
            local_name = entity.split(':')[-1]
            module = extract_module_from_prefix(prefix)
            properties[local_name] = module
        elif entity.startswith(':'):
            local_name = entity.split(':')[-1]
            properties[local_name] = ''

    # Find datatype properties: lines like "solveit-core:techniqueID rdf:type owl:DatatypeProperty"
    data_prop_pattern = rf'(\S+)\s+rdf:type\s+owl:DatatypeProperty'
    for match in re.finditer(data_prop_pattern, content):
        entity = match.group(1)
        if entity.startswith(('solveit-core:', 'solveit-analysis:', 'solveit-observable:')):
            prefix = entity.split(':')[0] + ':'
            local_name = entity.split(':')[-1]
            module = extract_module_from_prefix(prefix)
            properties[local_name] = module
        elif entity.startswith(':'):
            local_name = entity.split(':')[-1]
            properties[local_name] = ''

    return classes, properties


def create_redirect_html(local_name: str, entity_type: str, base_domain: str, module: str = '') -> str:
    """
    Create an HTML redirect file content.

    Args:
        local_name: The local name of the entity (e.g., "Technique")
        entity_type: Either "class" or "property"
        base_domain: The base domain for canonical URLs
        module: The module name (e.g., "core", "observable", "analysis")
    """
    # Normalize the local name for the filename with module prefix
    normalized = normalize_filename(local_name, module)

    # Determine the prefix based on entity type
    prefix = "class" if entity_type == "class" else "prop"

    # The target filename follows Ontospy's convention
    target_file = f"{prefix}-solveit-{normalized}.html"

    # Escape HTML
    escaped_name = html.escape(local_name)
    escaped_domain = html.escape(base_domain)
    escaped_file = html.escape(target_file)

    # Create the HTML content
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>SOLVE-IT {escaped_name} - Redirecting...</title>
    <link rel="canonical" href="{escaped_domain}/{escaped_file}">
    <meta http-equiv="refresh" content="0; url=../{escaped_file}">
    <script>window.location.href = "../{escaped_file}";</script>
</head>
<body>
    <p>Redirecting to <a href="../{escaped_file}">SOLVE-IT {escaped_name} documentation</a>...</p>
</body>
</html>
"""
    return html_content


def generate_redirects(docs_dir: Path, base_domain: str = "https://ontology.solveit-df.org"):
    """
    Generate redirect folders and index.html files for all ontology entities.

    Args:
        docs_dir: Path to the docs directory
        base_domain: Base domain for canonical URLs
    """
    # Find all TTL files in the project root (parent of scripts directory)
    project_root = Path(__file__).parent.parent
    ttl_files = list(project_root.glob("*.ttl"))

    if not ttl_files:
        print("No TTL files found in project root")
        return

    all_classes = {}  # local_name -> module
    all_properties = {}  # local_name -> module

    # Parse all TTL files
    print("Parsing TTL files...")
    for ttl_file in ttl_files:
        print(f"  Processing {ttl_file.name}...")
        classes, properties = parse_ttl_for_entities(ttl_file)
        all_classes.update(classes)
        all_properties.update(properties)

    print(f"\nFound {len(all_classes)} classes and {len(all_properties)} properties")

    # Create redirect folders for classes
    print("\nCreating redirect folders for classes...")
    for class_name in sorted(all_classes.keys()):
        folder = docs_dir / class_name
        folder.mkdir(exist_ok=True)

        module = all_classes[class_name]
        html_content = create_redirect_html(class_name, "class", base_domain, module)
        index_file = folder / "index.html"
        index_file.write_text(html_content, encoding='utf-8')
        print(f"  Created {class_name}/index.html")

    # Create redirect folders for properties
    print("\nCreating redirect folders for properties...")
    for prop_name in sorted(all_properties.keys()):
        folder = docs_dir / prop_name
        folder.mkdir(exist_ok=True)

        module = all_properties[prop_name]
        html_content = create_redirect_html(prop_name, "property", base_domain, module)
        index_file = folder / "index.html"
        index_file.write_text(html_content, encoding='utf-8')
        print(f"  Created {prop_name}/index.html")

    print(f"\n✓ Successfully created {len(all_classes) + len(all_properties)} redirect folders")


if __name__ == "__main__":
    # Determine the docs directory (in project root, parent of scripts directory)
    project_root = Path(__file__).parent.parent
    docs_dir = project_root / "docs"

    if not docs_dir.exists():
        print(f"Error: docs directory not found at {docs_dir}")
        exit(1)

    generate_redirects(docs_dir)
