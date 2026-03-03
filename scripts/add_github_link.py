#!/usr/bin/env python3
"""
Add a GitHub repository link to the navbar in generated ontospy docs.

Usage:
    python scripts/add_github_link.py docs
"""

import sys
from pathlib import Path

GITHUB_URL = "https://github.com/SOLVE-IT-DF/solve-it-ontology"

GITHUB_LINK = f"""\
      <ul class="nav navbar-nav navbar-right">
        <li><a href="{GITHUB_URL}" target="_blank">GitHub</a></li>
      </ul>"""


def add_github_link(docs_dir):
    docs_path = Path(docs_dir)
    if not docs_path.exists():
        print(f"Error: {docs_dir} does not exist")
        sys.exit(1)

    html_files = list(docs_path.glob("*.html"))
    modified = 0

    for html_file in html_files:
        content = html_file.read_text(encoding="utf-8")

        # Skip if already patched
        if "navbar-right" in content:
            continue

        # Insert before the closing </div><!--/.nav-collapse -->
        marker = '    </div><!--/.nav-collapse -->'
        if marker in content:
            content = content.replace(
                marker,
                GITHUB_LINK + "\n" + marker,
            )
            html_file.write_text(content, encoding="utf-8")
            modified += 1

    print(f"Added GitHub link to {modified} HTML files")


if __name__ == "__main__":
    docs_dir = sys.argv[1] if len(sys.argv) > 1 else "docs"
    add_github_link(docs_dir)
