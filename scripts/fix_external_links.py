#!/usr/bin/env python3
"""
Post-process ontospy-generated HTML documentation to fix links to external ontologies.

External classes/properties (UCO, CASE) should link to their official documentation
rather than broken local links.
"""

import os
import re
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

# Known UCO/CASE class names (lowercase slug -> proper CamelCase)
# This maps the lowercased ontospy slug back to the correct name
KNOWN_CLASSES = {
    # uco-core
    'ucoobject': 'UcoObject',
    'ucothing': 'UcoThing',
    'facet': 'Facet',
    'item': 'Item',
    'relationship': 'Relationship',
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

    # uco-observable
    'observableobject': 'ObservableObject',
    'file': 'File',
    'archivefile': 'ArchiveFile',
    'disk': 'Disk',
    'laptop': 'Laptop',
    'computer': 'Computer',
    'mobiledevice': 'MobileDevice',
    'smartphone': 'Smartphone',
    'tablet': 'Tablet',
    'device': 'Device',
    'account': 'Account',
    'application': 'Application',
    'contentdata': 'ContentData',
    'contentdatafacet': 'ContentDataFacet',
    'emailmessage': 'EmailMessage',
    'image': 'Image',
    'message': 'Message',
    'networkconnection': 'NetworkConnection',
    'process': 'Process',
    'url': 'URL',
    'urlhistory': 'URLHistory',
    'volume': 'Volume',
    'windowsregistrykey': 'WindowsRegistryKey',
    'filefacet': 'FileFacet',
    'hash': 'Hash',

    # uco-action
    'action': 'Action',
    'actionreference': 'ActionReference',
    'actionargumentfacet': 'ActionArgumentFacet',
    'actionestimationfacet': 'ActionEstimationFacet',
    'actionfrequencyfacet': 'ActionFrequencyFacet',
    'actionlifecycle': 'ActionLifecycle',
    'actionpattern': 'ActionPattern',

    # uco-analysis
    'analyticresult': 'AnalyticResult',
    'analysis': 'Analysis',
    'analyticresultfacet': 'AnalyticResultFacet',
    'artifactclassification': 'ArtifactClassification',
    'artifactclassificationresultfacet': 'ArtifactClassificationResultFacet',

    # case-investigation
    'investigativeaction': 'InvestigativeAction',
    'investigation': 'Investigation',
    'provenancerecord': 'ProvenanceRecord',
    'authorization': 'Authorization',
    'subject': 'Subject',
    'subjectfacet': 'SubjectFacet',
}

def get_proper_name(slug: str) -> str:
    """Convert a lowercase slug back to proper CamelCase."""
    if slug in KNOWN_CLASSES:
        return KNOWN_CLASSES[slug]
    # Fallback: just capitalize first letter (may not be correct)
    return slug.capitalize()

def fix_links_in_html(html_content: str) -> str:
    """Fix links to external classes/properties in HTML content."""

    def fix_uco_case_links(content: str) -> str:
        # Pattern for UCO/CASE class links
        patterns = [
            # uco-core classes
            (r'href="class-uco-core([a-z]+)\.html"', 'uco-core'),
            # uco-observable classes
            (r'href="class-uco-observable([a-z]+)\.html"', 'uco-observable'),
            # uco-action classes
            (r'href="class-uco-action([a-z]+)\.html"', 'uco-action'),
            # uco-analysis classes
            (r'href="class-uco-analysis([a-z]+)\.html"', 'uco-analysis'),
            # case-investigation classes
            (r'href="class-case-investigation([a-z]+)\.html"', 'case-investigation'),
            # uco-core properties
            (r'href="prop-uco-core([a-z]+)\.html"', 'uco-core'),
            # uco-observable properties
            (r'href="prop-uco-observable([a-z]+)\.html"', 'uco-observable'),
            # uco-action properties
            (r'href="prop-uco-action([a-z]+)\.html"', 'uco-action'),
            # uco-analysis properties
            (r'href="prop-uco-analysis([a-z]+)\.html"', 'uco-analysis'),
        ]

        for pattern, prefix in patterns:
            def make_replacer(pfx):
                def replacer(m):
                    slug = m.group(1)
                    proper_name = get_proper_name(slug)
                    url = f"{EXTERNAL_DOCS[pfx]}{proper_name}"
                    return f'href="{url}" target="_blank"'
                return replacer

            content = re.sub(pattern, make_replacer(prefix), content)

        return content

    return fix_uco_case_links(html_content)

def process_docs_directory(docs_dir: str):
    """Process all HTML files in the docs directory."""
    docs_path = Path(docs_dir)

    if not docs_path.exists():
        print(f"Error: {docs_dir} does not exist")
        return

    html_files = list(docs_path.glob("*.html"))
    print(f"Processing {len(html_files)} HTML files...")

    modified_count = 0
    for html_file in html_files:
        original_content = html_file.read_text(encoding='utf-8')
        modified_content = fix_links_in_html(original_content)

        if original_content != modified_content:
            html_file.write_text(modified_content, encoding='utf-8')
            modified_count += 1
            print(f"  Fixed links in: {html_file.name}")

    print(f"Modified {modified_count} files")

if __name__ == "__main__":
    import sys

    docs_dir = sys.argv[1] if len(sys.argv) > 1 else "docs"
    process_docs_directory(docs_dir)
