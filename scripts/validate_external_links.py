#!/usr/bin/env python3
"""
Validate that external links in generated HTML docs point to correct URLs.

Checks:
1. All external UCO/CASE links use proper CamelCase (not fallback capitalisation)
2. Optionally checks that linked URLs return HTTP 200 (--check-http flag)

Run after docs are generated:
    python scripts/validate_external_links.py docs
    python scripts/validate_external_links.py docs --check-http
"""

import re
import sys
from pathlib import Path

# The namespace base URLs we expect in external links
EXPECTED_BASES = [
    'https://ontology.unifiedcyberontology.org/uco/',
    'https://ontology.caseontology.org/case/',
]


def extract_external_links(docs_dir: str) -> list[tuple[str, str]]:
    """
    Extract all external UCO/CASE links from HTML docs.

    Returns list of (html_filename, url) tuples.
    """
    docs_path = Path(docs_dir)
    if not docs_path.exists():
        print(f"Error: {docs_dir} does not exist")
        sys.exit(1)

    links = []
    link_pattern = re.compile(r'href="(https://ontology\.[^"]+)"')

    for html_file in docs_path.glob("*.html"):
        content = html_file.read_text(encoding='utf-8')
        for match in link_pattern.finditer(content):
            url = match.group(1)
            for base in EXPECTED_BASES:
                if url.startswith(base):
                    links.append((html_file.name, url))
                    break

    return links


def check_camelcase(links: list[tuple[str, str]]) -> list[str]:
    """
    Check that the class/property name at the end of each URL uses proper
    CamelCase — i.e., not a single-capitalised word like 'Contextualcompilation'.

    Classes use PascalCase (ContextualCompilation) — multi-word names should
    have 2+ uppercase letters.

    Properties use camelCase (creationTime) — these start lowercase and are
    expected to have fewer uppercase letters, so we only flag properties
    that are very long with zero uppercase letters.
    """
    errors = []
    seen = set()

    for filename, url in links:
        # Extract the class/property name (last path segment)
        name = url.rstrip('/').split('/')[-1]
        if not name:
            continue

        key = (filename, url)
        if key in seen:
            continue
        seen.add(key)

        upper_count = sum(1 for c in name if c.isupper())
        is_property = name[0].islower()  # Properties start lowercase (camelCase)

        if is_property:
            # Properties: only flag if completely lowercase and long
            if len(name) >= 15 and upper_count == 0:
                errors.append(
                    f"  {filename}: {url}\n"
                    f"    '{name}' looks like broken camelCase "
                    f"(no uppercase in {len(name)} chars)"
                )
        else:
            # Classes: flag if long PascalCase name has only one uppercase
            if len(name) >= 12 and upper_count <= 1:
                errors.append(
                    f"  {filename}: {url}\n"
                    f"    '{name}' looks like broken PascalCase "
                    f"(only {upper_count} uppercase in {len(name)} chars)"
                )

    return errors


def check_http(links: list[tuple[str, str]]) -> list[str]:
    """Check that each URL returns HTTP 200."""
    import urllib.request
    import urllib.error

    errors = []
    checked = {}

    for filename, url in links:
        if url in checked:
            status = checked[url]
        else:
            try:
                req = urllib.request.Request(url, method='HEAD')
                req.add_header('User-Agent', 'SOLVE-IT-link-checker/1.0')
                resp = urllib.request.urlopen(req, timeout=10)
                status = resp.status
            except urllib.error.HTTPError as e:
                status = e.code
            except Exception as e:
                status = str(e)
            checked[url] = status

        if status != 200:
            errors.append(f"  {filename}: {url} -> HTTP {status}")

    return errors


def main():
    docs_dir = sys.argv[1] if len(sys.argv) > 1 else "docs"
    do_http = "--check-http" in sys.argv

    links = extract_external_links(docs_dir)
    print(f"Found {len(links)} external UCO/CASE links across docs")

    # Deduplicate URLs for summary
    unique_urls = set(url for _, url in links)
    print(f"  ({len(unique_urls)} unique URLs)")

    # Check CamelCase
    camelcase_errors = check_camelcase(links)
    if camelcase_errors:
        print(f"\nFAIL: {len(camelcase_errors)} link(s) with suspected broken CamelCase:")
        for err in camelcase_errors:
            print(err)
    else:
        print("\nCamelCase check: PASS")

    # Optional HTTP check
    http_errors = []
    if do_http:
        print("\nChecking HTTP status (this may take a moment)...")
        http_errors = check_http(links)
        if http_errors:
            print(f"\nFAIL: {len(http_errors)} link(s) returned non-200:")
            for err in http_errors:
                print(err)
        else:
            print("HTTP check: PASS")

    if camelcase_errors or http_errors:
        sys.exit(1)

    print("\nAll checks passed.")


if __name__ == "__main__":
    main()
