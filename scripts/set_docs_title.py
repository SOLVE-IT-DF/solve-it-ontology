#!/usr/bin/env python3
"""
Replace ontospy's auto-generated title with a version-aware SOLVE-IT title.

Usage:
    python scripts/set_docs_title.py docs
    python scripts/set_docs_title.py docs 0.0.2   # override version

Reads version from VERSION file if not supplied on command line.
"""

import re
import sys
from pathlib import Path


def get_version(repo_root: str, override: str | None = None) -> str:
    if override:
        return override
    version_file = Path(repo_root) / "VERSION"
    if version_file.exists():
        return version_file.read_text().strip()
    return "dev"


def set_title(docs_dir: str, version: str):
    docs_path = Path(docs_dir)
    if not docs_path.exists():
        print(f"Error: {docs_dir} does not exist")
        sys.exit(1)

    new_title = f"SOLVE-IT Ontology {version}"

    # Match ontospy's auto-generated title pattern
    title_pattern = re.compile(r'RDF knowledge graph \(\d+ ontolog(?:y|ies)\)')

    html_files = list(docs_path.glob("*.html"))
    modified = 0

    for html_file in html_files:
        content = html_file.read_text(encoding='utf-8')
        new_content = title_pattern.sub(new_title, content)
        if content != new_content:
            html_file.write_text(new_content, encoding='utf-8')
            modified += 1

    print(f"Set docs title to '{new_title}' in {modified} files")


def main():
    docs_dir = sys.argv[1] if len(sys.argv) > 1 else "docs"
    version_override = sys.argv[2] if len(sys.argv) > 2 else None

    repo_root = Path(__file__).resolve().parent.parent
    version = get_version(str(repo_root), version_override)

    set_title(docs_dir, version)


if __name__ == "__main__":
    main()
