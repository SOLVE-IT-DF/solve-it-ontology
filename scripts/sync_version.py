#!/usr/bin/env python3
"""
Sync the version from the VERSION file into all ontology TTL files.
Updates owl:versionInfo and owl:versionIRI in every solve_it_*.ttl file.

Usage:
    python sync_version.py              # Sync VERSION to TTL files
    python sync_version.py --bump-patch # Increment patch, update VERSION, sync to TTL files
"""

import argparse
import re
from pathlib import Path


def bump_patch(version):
    """Increment the patch component of a semver string."""
    major, minor, patch = version.split(".")
    return f"{major}.{minor}.{int(patch) + 1}"


def sync_version(project_root, bump=False):
    version_file = project_root / "VERSION"
    version = version_file.read_text().strip()

    if bump:
        old_version = version
        version = bump_patch(version)
        version_file.write_text(version + "\n")
        print(f"Bumped patch version: {old_version} -> {version}")
    else:
        print(f"Version from VERSION file: {version}")

    ttl_files = sorted(project_root.glob("solve_it_*.ttl"))
    updated = 0

    for ttl_file in ttl_files:
        content = ttl_file.read_text()
        original = content

        # Update owl:versionInfo "x.y.z"
        content = re.sub(
            r'(owl:versionInfo\s+")[^"]+(")',
            rf"\g<1>{version}\2",
            content,
        )

        # Update owl:versionIRI <.../x.y.z>
        content = re.sub(
            r"(owl:versionIRI\s+<[^>]+/)\d+\.\d+\.\d+(>)",
            rf"\g<1>{version}\2",
            content,
        )

        if content != original:
            ttl_file.write_text(content)
            print(f"  Updated {ttl_file.name}")
            updated += 1
        else:
            print(f"  No change: {ttl_file.name}")

    print(f"\n{updated} file(s) updated to version {version}")
    return updated


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sync VERSION to ontology TTL files")
    parser.add_argument(
        "--bump-patch",
        action="store_true",
        help="Increment patch version before syncing",
    )
    args = parser.parse_args()

    project_root = Path(__file__).parent.parent
    sync_version(project_root, bump=args.bump_patch)
