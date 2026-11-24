#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 || $# -gt 3 || ( $# -eq 3 && $3 != --apply ) ]]; then
  echo "Usage: bash scripts/deploy-site.sh REVISION EXISTING_WEB_ROOT [--apply]" >&2
  exit 2
fi

repo=$(git -C "$(dirname -- "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)
revision=$(git -C "$repo" rev-parse --verify --end-of-options "$1^{commit}")
destination=$(cd -- "$2" && pwd -P)
if [[ $destination == / || $destination == "$repo" || $destination == "$repo/"* || $repo == "$destination/"* ]]; then
  echo "Use a web root separate from the Git checkout." >&2
  exit 2
fi
if [[ ! -f "$destination/index.html" ]]; then
  echo "Expected an existing site with index.html in the web root." >&2
  exit 2
fi

stage=$(mktemp -d)
trap 'rm -rf -- "$stage"' EXIT
git -C "$repo" archive "$revision" site/ | tar -xf - -C "$stage"
test -f "$stage/site/index.html"
test -f "$stage/site/sitemap.xml"

options=(--recursive --checksum --itemize-changes --delay-updates --chmod=D755,F644)
if [[ ${3:-} != --apply ]]; then
  options+=(--dry-run)
fi
printf 'Revision %s → %s\n' "$revision" "$destination"
rsync "${options[@]}" -- "$stage/site/" "$destination/"
