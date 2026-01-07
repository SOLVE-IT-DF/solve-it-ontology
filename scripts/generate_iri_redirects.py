#!/usr/bin/env python3
"""
Generate IRI redirect folders for all classes and properties in the SOLVE-IT ontology.
This script parses TTL files to extract classes and properties, then creates folder
structures with index.html redirects so that IRIs resolve properly.
"""

import os
import re
from pathlib import Path
from typing import Set, Tuple


def extract_local_name(uri: str) -> str:
    """Extract the local name from a URI."""
    if '#' in uri:
        return uri.split('#')[-1]
    elif '/' in uri:
        return uri.split('/')[-1]
    return uri


def normalize_filename(local_name: str) -> str:
    """
    Normalize a local name to match Ontospy's filename convention.
    Converts to lowercase and removes special characters.
    """
    # Convert to lowercase and remove special characters
    normalized = local_name.lower()
    # Remove any remaining special characters that aren't alphanumeric
    normalized = re.sub(r'[^a-z0-9]', '', normalized)
    return normalized


def parse_ttl_for_entities(ttl_file: Path, namespace: str) -> Tuple[Set[str], Set[str]]:
    """
    Parse a TTL file to extract classes and properties in the given namespace.
    Returns (classes, properties) as sets of local names.
    """
    classes = set()
    properties = set()

    with open(ttl_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find classes: lines like "solve-it:Technique rdf:type owl:Class"
    class_pattern = rf'(\S+)\s+rdf:type\s+owl:Class'
    for match in re.finditer(class_pattern, content):
        entity = match.group(1)
        # Check if it's in our namespace
        if entity.startswith('solve-it:') or entity.startswith(':'):
            local_name = entity.split(':')[-1]
            classes.add(local_name)

    # Find object properties: lines like "solve-it:hasWeakness rdf:type owl:ObjectProperty"
    obj_prop_pattern = rf'(\S+)\s+rdf:type\s+owl:ObjectProperty'
    for match in re.finditer(obj_prop_pattern, content):
        entity = match.group(1)
        if entity.startswith('solve-it:') or entity.startswith(':'):
            local_name = entity.split(':')[-1]
            properties.add(local_name)

    # Find datatype properties: lines like "solve-it:techniqueID rdf:type owl:DatatypeProperty"
    data_prop_pattern = rf'(\S+)\s+rdf:type\s+owl:DatatypeProperty'
    for match in re.finditer(data_prop_pattern, content):
        entity = match.group(1)
        if entity.startswith('solve-it:') or entity.startswith(':'):
            local_name = entity.split(':')[-1]
            properties.add(local_name)

    return classes, properties


def create_redirect_html(local_name: str, entity_type: str, base_domain: str) -> str:
    """
    Create an HTML redirect file content.

    Args:
        local_name: The local name of the entity (e.g., "Technique")
        entity_type: Either "class" or "property"
        base_domain: The base domain for canonical URLs
    """
    # Normalize the local name for the filename
    normalized = normalize_filename(local_name)

    # Determine the prefix based on entity type
    prefix = "class" if entity_type == "class" else "prop"

    # The target filename follows Ontospy's convention
    target_file = f"{prefix}-solve-it{normalized}.html"

    # Create the HTML content
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>SOLVE-IT {local_name} - Redirecting...</title>
    <link rel="canonical" href="{base_domain}/{target_file}">
    <meta http-equiv="refresh" content="0; url=../{target_file}">
    <script>window.location.href = "../{target_file}";</script>
</head>
<body>
    <p>Redirecting to <a href="../{target_file}">SOLVE-IT {local_name} documentation</a>...</p>
</body>
</html>
"""
    return html


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

    all_classes = set()
    all_properties = set()

    # Parse all TTL files
    print("Parsing TTL files...")
    for ttl_file in ttl_files:
        print(f"  Processing {ttl_file.name}...")
        classes, properties = parse_ttl_for_entities(ttl_file, "solve-it:")
        all_classes.update(classes)
        all_properties.update(properties)

    print(f"\nFound {len(all_classes)} classes and {len(all_properties)} properties")

    # Create redirect folders for classes
    print("\nCreating redirect folders for classes...")
    for class_name in sorted(all_classes):
        folder = docs_dir / class_name
        folder.mkdir(exist_ok=True)

        html_content = create_redirect_html(class_name, "class", base_domain)
        index_file = folder / "index.html"
        index_file.write_text(html_content, encoding='utf-8')
        print(f"  Created {class_name}/index.html")

    # Create redirect folders for properties
    print("\nCreating redirect folders for properties...")
    for prop_name in sorted(all_properties):
        folder = docs_dir / prop_name
        folder.mkdir(exist_ok=True)

        html_content = create_redirect_html(prop_name, "property", base_domain)
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
