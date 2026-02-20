#!/usr/bin/env bash
#
# Bump the SOLVE-IT ontology version across all TTL files.
#
# Usage:
#   ./scripts/bump_version.sh <new-version>
#
# Example:
#   ./scripts/bump_version.sh 0.0.2
#
# This updates:
#   - VERSION file (single source of truth)
#   - owl:versionIRI in all ontology and example TTL files
#   - owl:versionInfo in all ontology TTL files
#
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

if [ $# -ne 1 ]; then
    echo "Usage: $0 <new-version>"
    echo "  e.g. $0 0.0.2"
    exit 1
fi

NEW_VERSION="$1"

# Validate version format (semver-ish)
if ! [[ "$NEW_VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "ERROR: Version must be in X.Y.Z format (got: $NEW_VERSION)"
    exit 1
fi

OLD_VERSION="$(cat VERSION | tr -d '[:space:]')"

if [ "$OLD_VERSION" = "$NEW_VERSION" ]; then
    echo "Already at version $NEW_VERSION — nothing to do."
    exit 0
fi

echo "Bumping version: $OLD_VERSION → $NEW_VERSION"
echo ""

# 1. Update VERSION file
echo "$NEW_VERSION" > VERSION
echo "  Updated VERSION"

# 2. Update owl:versionInfo in main ontology TTL files
COUNT=0
for ttl in solve_it_*.ttl; do
    if grep -q "owl:versionInfo \"$OLD_VERSION\"" "$ttl"; then
        sed -i '' "s|owl:versionInfo \"$OLD_VERSION\"|owl:versionInfo \"$NEW_VERSION\"|g" "$ttl"
        COUNT=$((COUNT + 1))
    fi
done
echo "  Updated owl:versionInfo in $COUNT files"

# 3. Update owl:versionIRI in main ontology TTL files
COUNT=0
for ttl in solve_it_*.ttl; do
    if grep -q "/$OLD_VERSION>" "$ttl"; then
        sed -i '' "s|/$OLD_VERSION>|/$NEW_VERSION>|g" "$ttl"
        COUNT=$((COUNT + 1))
    fi
done
echo "  Updated owl:versionIRI in $COUNT files"

# 4. Update owl:versionIRI in example TTL files
COUNT=0
for ttl in solve_it_examples/*.ttl; do
    if grep -q "/$OLD_VERSION>" "$ttl"; then
        sed -i '' "s|/$OLD_VERSION>|/$NEW_VERSION>|g" "$ttl"
        COUNT=$((COUNT + 1))
    fi
done
echo "  Updated owl:versionIRI in $COUNT example files"

echo ""
echo "Done. Verify with:"
echo "  grep -r 'versionInfo\|versionIRI' solve_it_*.ttl solve_it_examples/*.ttl"
