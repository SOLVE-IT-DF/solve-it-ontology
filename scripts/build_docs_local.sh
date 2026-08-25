#!/usr/bin/env bash
#
# Local equivalent of the build-ontology-docs GitHub Action.
# Builds into a temp directory by default so docs/ isn't modified.
#
# Usage:
#   ./scripts/build_docs_local.sh                  # full rebuild in temp dir
#   ./scripts/build_docs_local.sh --skip-ontospy   # skip ontospy, validate only
#   ./scripts/build_docs_local.sh --in-place        # build into docs/ (like CI does)
#
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

SKIP_ONTOSPY=false
IN_PLACE=false
for arg in "$@"; do
    case "$arg" in
        --skip-ontospy) SKIP_ONTOSPY=true ;;
        --in-place) IN_PLACE=true ;;
        *) echo "Unknown option: $arg"; exit 1 ;;
    esac
done

# Check dependencies
if ! command -v ontospy &> /dev/null && [ "$SKIP_ONTOSPY" = false ]; then
    echo "ERROR: ontospy not installed. Run: pip install ontospy"
    exit 1
fi

# Determine output directory
if [ "$IN_PLACE" = true ]; then
    DOCS_DIR="docs"
    CLEANUP=""
    echo "=== Local docs build (in-place — will modify docs/) ==="
else
    DOCS_DIR="$(mktemp -d)"
    CLEANUP="$DOCS_DIR"
    trap 'rm -rf "$CLEANUP"' EXIT
    echo "=== Local docs build (temp dir: $DOCS_DIR) ==="
fi
echo ""

# Step 1: Build with ontospy (unless skipped)
if [ "$SKIP_ONTOSPY" = false ]; then
    echo "--- Building docs with ontospy ---"

    if [ "$IN_PLACE" = true ] && [ -d docs/data ]; then
        mv docs/data /tmp/docs-data-backup-local
    fi

    rm -rf "$DOCS_DIR"
    mkdir -p "$DOCS_DIR"

    # Ontology TTL files only. ontospy recurses, so pointing it at the
    # repository root also swept up solve_it_examples/, whose technique
    # declarations ("a owl:Class , solveit-core:Technique") were then rendered
    # as ontology classes. Technique entries are knowledge base data.
    # Keep this in step with .github/workflows/validate-and-build-docs.yml.
    ONTOLOGY_SRC="$(mktemp -d)"
    # Extends the existing EXIT trap so the staging directory is removed even
    # if ontospy fails, which set -e would otherwise skip. CLEANUP is empty in
    # in-place mode, and rm -rf tolerates that.
    trap 'rm -rf "$CLEANUP" "$ONTOLOGY_SRC"' EXIT
    cp solve_it_*.ttl "$ONTOLOGY_SRC"/
    ontospy gendocs "$ONTOLOGY_SRC" -o "$DOCS_DIR" --type 2

    if [ "$IN_PLACE" = true ] && [ -d /tmp/docs-data-backup-local ]; then
        mv /tmp/docs-data-backup-local docs/data
    fi

    echo "ontology.solveit-df.org" > "$DOCS_DIR/CNAME"
    echo ""
else
    echo "--- Skipping ontospy (--skip-ontospy) ---"
    # If not in-place and skipping ontospy, copy existing docs to temp dir
    if [ "$IN_PLACE" = false ]; then
        echo "    Copying existing docs/ to temp dir for validation..."
        cp -r docs/* "$DOCS_DIR/" 2>/dev/null || true
    fi
    echo ""
fi

# Step 2: Set docs title
echo "--- Setting docs title ---"
python3 scripts/set_docs_title.py "$DOCS_DIR"
echo ""

# Step 3: Fix external links
echo "--- Fixing external ontology links ---"
python3 scripts/fix_external_links.py "$DOCS_DIR" .
echo ""

# Step 4: Validate external links
echo "--- Validating external links ---"
python3 scripts/validate_external_links.py "$DOCS_DIR"
echo ""

# Step 5: Generate IRI redirects (only if in-place — these write to docs/)
if [ "$IN_PLACE" = true ]; then
    echo "--- Generating IRI redirects ---"
    python3 scripts/generate_iri_redirects.py
    echo ""

    echo "--- Generating examples page ---"
    python3 scripts/generate_examples_page.py
    echo ""
fi

echo "=== All steps passed ==="
if [ "$IN_PLACE" = false ]; then
    echo ""
    echo "No files were modified in docs/."
    echo "Use --in-place if you want to rebuild docs/ for real."
fi
