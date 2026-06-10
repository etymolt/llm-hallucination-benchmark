#!/bin/bash
# zenodo_publish.sh — operator-runnable Zenodo deposit script for the
# LLM Brand-Name Hallucination Benchmark v0.5 raw scoring outputs.
#
# Usage:
#   export ZENODO_TOKEN=your_zenodo_personal_access_token
#   ./zenodo_publish.sh \
#       /absolute/path/to/cells.jsonl \
#       /absolute/path/to/analysis.json
#
# Optional:
#   ZENODO_BASE=https://sandbox.zenodo.org/api ./zenodo_publish.sh ...
#       (use sandbox for dry runs)
#   ZENODO_PUBLISH=1  ./zenodo_publish.sh ...
#       (skip the interactive confirm and auto-publish)
#
# Behavior:
#   1. Creates a new deposit
#   2. Uploads cells.jsonl + analysis.json + the five metadata/doc files
#      in this directory
#   3. Attaches metadata from ./metadata.json
#   4. Prints the bucket URL + draft DOI
#   5. Prompts before calling /actions/publish (override with ZENODO_PUBLISH=1)
#   6. Returns the final DOI

set -euo pipefail

TOKEN="${ZENODO_TOKEN:?need ZENODO_TOKEN env var (https://zenodo.org/account/settings/applications/)}"
BASE="${ZENODO_BASE:-https://zenodo.org/api}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

CELLS_PATH="${1:?usage: $0 /path/to/cells.jsonl /path/to/analysis.json}"
ANALYSIS_PATH="${2:?usage: $0 /path/to/cells.jsonl /path/to/analysis.json}"

for f in "$CELLS_PATH" "$ANALYSIS_PATH" "$HERE/metadata.json" "$HERE/README.md" \
         "$HERE/DATASET_SCHEMA.md" "$HERE/REPLICATION_QUICKSTART.md" "$HERE/MANIFEST.txt"; do
  [ -f "$f" ] || { echo "missing: $f" >&2; exit 1; }
done

command -v jq >/dev/null    || { echo "jq required"    >&2; exit 1; }
command -v curl >/dev/null  || { echo "curl required"  >&2; exit 1; }

echo ">> Base: $BASE"
echo ">> Creating deposit ..."
DEPOSIT="$(curl -fsS -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{}' \
  "$BASE/deposit/depositions")"

DEPOSIT_ID="$(echo "$DEPOSIT" | jq -r '.id')"
BUCKET_URL="$(echo "$DEPOSIT" | jq -r '.links.bucket')"
DRAFT_DOI="$(echo "$DEPOSIT" | jq -r '.metadata.prereserve_doi.doi // .doi_url // "unassigned"')"
PUBLISH_URL="$(echo "$DEPOSIT" | jq -r '.links.publish')"

echo ">> Deposit id:  $DEPOSIT_ID"
echo ">> Bucket URL:  $BUCKET_URL"
echo ">> Draft DOI:   $DRAFT_DOI"

upload() {
  local path="$1"
  local name="$(basename "$path")"
  echo ">> Uploading $name ($(du -h "$path" | awk '{print $1}')) ..."
  curl -fsS --progress-bar \
    -H "Authorization: Bearer $TOKEN" \
    -X PUT \
    -T "$path" \
    "$BUCKET_URL/$name" > /dev/null
}

# Upload data files (largest first so the progress bar is informative)
upload "$CELLS_PATH"
upload "$ANALYSIS_PATH"

# Upload documentation / metadata sidecars
upload "$HERE/README.md"
upload "$HERE/DATASET_SCHEMA.md"
upload "$HERE/REPLICATION_QUICKSTART.md"
upload "$HERE/MANIFEST.txt"

echo ">> Attaching metadata ..."
curl -fsS -X PUT \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  --data @"$HERE/metadata.json" \
  "$BASE/deposit/depositions/$DEPOSIT_ID" > /dev/null

echo
echo "============================================================"
echo "Draft deposit prepared."
echo "  ID:    $DEPOSIT_ID"
echo "  DOI:   $DRAFT_DOI   (reserved; activates on publish)"
echo "  URL:   ${BASE/api/}deposit/$DEPOSIT_ID"
echo "============================================================"
echo

if [ "${ZENODO_PUBLISH:-0}" != "1" ]; then
  read -p "Publish now? Type 'publish' to confirm, anything else to skip: " ANS
  if [ "$ANS" != "publish" ]; then
    echo ">> Skipping publish. Draft remains editable in the Zenodo UI."
    exit 0
  fi
fi

echo ">> Publishing ..."
PUBLISHED="$(curl -fsS -X POST \
  -H "Authorization: Bearer $TOKEN" \
  "$PUBLISH_URL")"

FINAL_DOI="$(echo "$PUBLISHED" | jq -r '.doi // .metadata.doi // empty')"
FINAL_URL="$(echo "$PUBLISHED" | jq -r '.links.html // .links.record_html // empty')"

echo
echo "============================================================"
echo "PUBLISHED."
echo "  DOI:   $FINAL_DOI"
echo "  URL:   $FINAL_URL"
echo "============================================================"
