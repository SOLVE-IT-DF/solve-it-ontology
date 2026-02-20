#!/usr/bin/env python3
"""
Post-process ontospy-generated HTML documentation to fix links to external ontologies.

External classes/properties (UCO, CASE) should link to their official documentation
rather than broken local links.

Class/property names are auto-discovered from the TTL source files so that the
mapping stays in sync as the ontology evolves.
"""

import os
import re
import sys
from pathlib import Path

# Mapping of namespace prefixes to their documentation base URLs
EXTERNAL_DOCS = {
    'uco-core': 'https://ontology.unifiedcyberontology.org/uco/core/',
    'uco-observable': 'https://ontology.unifiedcyberontology.org/uco/observable/',
    'uco-action': 'https://ontology.unifiedcyberontology.org/uco/action/',
    'uco-analysis': 'https://ontology.unifiedcyberontology.org/uco/analysis/',
    'uco-types': 'https://ontology.unifiedcyberontology.org/uco/types/',
    'uco-vocabulary': 'https://ontology.unifiedcyberontology.org/uco/vocabulary/',
    'case-investigation': 'https://ontology.caseontology.org/case/investigation/',
}

# Namespace IRIs that map to the same prefixes (for full-IRI references in TTL)
NAMESPACE_IRIS = {
    'https://ontology.unifiedcyberontology.org/uco/core/': 'uco-core',
    'https://ontology.unifiedcyberontology.org/uco/observable/': 'uco-observable',
    'https://ontology.unifiedcyberontology.org/uco/action/': 'uco-action',
    'https://ontology.unifiedcyberontology.org/uco/analysis/': 'uco-analysis',
    'https://ontology.unifiedcyberontology.org/uco/types/': 'uco-types',
    'https://ontology.unifiedcyberontology.org/uco/vocabulary/': 'uco-vocabulary',
    'https://ontology.caseontology.org/case/investigation/': 'case-investigation',
}


# Fallback names for UCO/CASE classes that may appear in ontospy's
# class hierarchy but aren't directly referenced in our TTL files.
# Auto-discovery from TTL takes priority over these.
_HIERARCHY_FALLBACKS = {
    'ucoobject': 'UcoObject',
    'ucothing': 'UcoThing',
    'item': 'Item',
    'annotation': 'Annotation',
    'assertion': 'Assertion',
    'attributedname': 'AttributedName',
    'bundle': 'Bundle',
    'compilation': 'Compilation',
    'confidence': 'Confidence',
    'confidencefacet': 'ConfidenceFacet',
    'contextualizableobject': 'ContextualizableObject',
    'contextualization': 'Contextualization',
    'controlledvocabulary': 'ControlledVocabulary',
    'enclosingcompilation': 'EnclosingCompilation',
    'externalreference': 'ExternalReference',
    'grouping': 'Grouping',
    'identity': 'Identity',
    'identityabstraction': 'IdentityAbstraction',
    'modusoperandi': 'ModusOperandi',
    'markingdefinition': 'MarkingDefinition',
    'markingdefinitionabstraction': 'MarkingDefinitionAbstraction',
    'contentdata': 'ContentData',
    'contentdatafacet': 'ContentDataFacet',
    'emailmessage': 'EmailMessage',
    'mobiledevice': 'MobileDevice',
    'smartphone': 'Smartphone',
    'tablet': 'Tablet',
    'laptop': 'Laptop',
    'computer': 'Computer',
    'networkconnection': 'NetworkConnection',
    'urlhistory': 'URLHistory',
    'windowsregistrykey': 'WindowsRegistryKey',
    'filefacet': 'FileFacet',
    'actionreference': 'ActionReference',
    'actionargumentfacet': 'ActionArgumentFacet',
    'actionestimationfacet': 'ActionEstimationFacet',
    'actionfrequencyfacet': 'ActionFrequencyFacet',
    'actionlifecycle': 'ActionLifecycle',
    'actionpattern': 'ActionPattern',
    'analyticresultfacet': 'AnalyticResultFacet',
    'artifactclassification': 'ArtifactClassification',
    'artifactclassificationresultfacet': 'ArtifactClassificationResultFacet',
    'provenancerecord': 'ProvenanceRecord',
    'authorization': 'Authorization',
    'subjectfacet': 'SubjectFacet',
}


def discover_external_names(ttl_dir: str) -> dict[str, str]:
    """
    Scan TTL files for references to external UCO/CASE classes and properties.
    Merges with hierarchy fallbacks (auto-discovered names take priority).

    Returns a dict mapping lowercase slug -> proper CamelCase name.
    e.g. {'contextualcompilation': 'ContextualCompilation', ...}
    """
    # Start with fallbacks, then overlay auto-discovered names
    names = dict(_HIERARCHY_FALLBACKS)
    ttl_path = Path(ttl_dir)

    # Prefixes we care about (the short prefix names used in TTL)
    prefix_names = set(EXTERNAL_DOCS.keys())

    # Pattern for prefixed names: uco-core:ClassName, case-investigation:InvestigativeAction
    prefixed_pattern = re.compile(
        r'\b(' + '|'.join(re.escape(p) for p in prefix_names) + r'):([A-Za-z]\w*)'
    )

    # Pattern for full IRI references: <https://ontology.../uco/core/ClassName>
    iri_pattern = re.compile(
        r'<(' + '|'.join(re.escape(ns) for ns in NAMESPACE_IRIS.keys()) + r')([A-Za-z]\w*)>'
    )

    for ttl_file in ttl_path.glob("**/*.ttl"):
        content = ttl_file.read_text(encoding='utf-8', errors='replace')

        # Find prefixed references
        for match in prefixed_pattern.finditer(content):
            proper_name = match.group(2)
            slug = proper_name.lower()
            names[slug] = proper_name

        # Find full IRI references
        for match in iri_pattern.finditer(content):
            proper_name = match.group(2)
            slug = proper_name.lower()
            names[slug] = proper_name

    return names


def get_proper_name(slug: str, known: dict[str, str]) -> tuple[str, bool]:
    """
    Convert a lowercase slug back to proper CamelCase.

    Returns (name, was_found) — was_found is False if we had to guess.
    """
    if slug in known:
        return known[slug], True
    # Fallback: capitalize first letter (likely wrong for multi-word names)
    return slug.capitalize(), False


def fix_links_in_html(html_content: str, known: dict[str, str]) -> tuple[str, list[str]]:
    """
    Fix links to external classes/properties in HTML content.

    Returns (modified_content, list_of_unknown_slugs).
    """
    unknown_slugs = []

    def fix_uco_case_links(content: str) -> str:
        # Pattern for UCO/CASE class and property links
        patterns = [
            (r'href="class-uco-core([a-z]+)\.html"', 'uco-core'),
            (r'href="class-uco-observable([a-z]+)\.html"', 'uco-observable'),
            (r'href="class-uco-action([a-z]+)\.html"', 'uco-action'),
            (r'href="class-uco-analysis([a-z]+)\.html"', 'uco-analysis'),
            (r'href="class-case-investigation([a-z]+)\.html"', 'case-investigation'),
            (r'href="prop-uco-core([a-z]+)\.html"', 'uco-core'),
            (r'href="prop-uco-observable([a-z]+)\.html"', 'uco-observable'),
            (r'href="prop-uco-action([a-z]+)\.html"', 'uco-action'),
            (r'href="prop-uco-analysis([a-z]+)\.html"', 'uco-analysis'),
        ]

        for pattern, prefix in patterns:
            def make_replacer(pfx):
                def replacer(m):
                    slug = m.group(1)
                    proper_name, found = get_proper_name(slug, known)
                    if not found:
                        unknown_slugs.append(f"{pfx}:{slug}")
                    url = f"{EXTERNAL_DOCS[pfx]}{proper_name}"
                    return f'href="{url}" target="_blank"'
                return replacer

            content = re.sub(pattern, make_replacer(prefix), content)

        return content

    return fix_uco_case_links(html_content), unknown_slugs


def process_docs_directory(docs_dir: str, ttl_dir: str = "."):
    """Process all HTML files in the docs directory."""
    docs_path = Path(docs_dir)

    if not docs_path.exists():
        print(f"Error: {docs_dir} does not exist")
        return False

    # Auto-discover class/property names from TTL source files
    discovered = discover_external_names(ttl_dir)
    print(f"Auto-discovered {len(discovered)} external class/property names from TTL files")

    html_files = list(docs_path.glob("*.html"))
    print(f"Processing {len(html_files)} HTML files...")

    modified_count = 0
    all_unknown = []

    for html_file in html_files:
        original_content = html_file.read_text(encoding='utf-8')
        modified_content, unknown = fix_links_in_html(original_content, discovered)

        if unknown:
            for slug in unknown:
                all_unknown.append(f"  {html_file.name}: {slug}")

        if original_content != modified_content:
            html_file.write_text(modified_content, encoding='utf-8')
            modified_count += 1
            print(f"  Fixed links in: {html_file.name}")

    print(f"Modified {modified_count} files")

    if all_unknown:
        # Deduplicate
        unique_unknown = sorted(set(all_unknown))
        print(f"\nWARNING: {len(unique_unknown)} link(s) used fallback capitalisation "
              f"(CamelCase not found in TTL sources):")
        for entry in unique_unknown:
            print(entry)
        print("\nThese links are likely broken. Add the referenced class/property "
              "to the TTL files, or check for typos in the ontology.")
        return False

    return True


if __name__ == "__main__":
    docs_dir = sys.argv[1] if len(sys.argv) > 1 else "docs"
    ttl_dir = sys.argv[2] if len(sys.argv) > 2 else "."
    success = process_docs_directory(docs_dir, ttl_dir)
    if not success:
        sys.exit(1)
