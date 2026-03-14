#!/usr/bin/env bash
# PlanetHack version management
# Usage:
#   ./scripts/version.sh              # show current
#   ./scripts/version.sh bump patch   # 1.0.0 -> 1.0.1
#   ./scripts/version.sh bump minor   # 1.0.0 -> 1.1.0
#   ./scripts/version.sh bump major   # 1.0.0 -> 2.0.0
#   ./scripts/version.sh set 2.1.3    # set exact version
#   ./scripts/version.sh reset        # set 0.0.0-dev

set -e
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION_FILE="$ROOT/VERSION"

get() {
  [ -f "$VERSION_FILE" ] && cat "$VERSION_FILE" | tr -d '\n\r' || echo "1.0.0"
}

bump() {
  v="$1"; part="${2:-patch}"
  if [[ "$v" =~ ^([0-9]+)\.([0-9]+)\.([0-9]+) ]]; then
    maj="${BASH_REMATCH[1]}"; min="${BASH_REMATCH[2]}"; pat="${BASH_REMATCH[3]}"
  else
    echo "Invalid version: $v" >&2; exit 1
  fi
  case "$part" in
    major) echo "$((maj+1)).0.0" ;;
    minor) echo "$maj.$((min+1)).0" ;;
    patch) echo "$maj.$min.$((pat+1))" ;;
    *) echo "Unknown: $part" >&2; exit 1 ;;
  esac
}

sync_files() {
  v="$1"
  [ -f "$ROOT/config/config.yaml" ] && sed -i "s/version: *[\"'][^\"']*[\"']/version: \"$v\"/" "$ROOT/config/config.yaml"
  [ -f "$ROOT/frontend/package.json" ] && sed -i "s/\"version\": *\"[^\"]*\"/\"version\": \"$v\"/" "$ROOT/frontend/package.json"
}

case "${1:-}" in
  bump) cur=$(get); new=$(bump "$cur" "${2:-patch}")
    echo "$new" > "$VERSION_FILE"; sync_files "$new"
    echo "Bumped: $cur -> $new" ;;
  set) new="${2:?need X.Y.Z}"
    echo "$new" > "$VERSION_FILE"; sync_files "$new"
    echo "Set: $new" ;;
  reset) echo "0.0.0-dev" > "$VERSION_FILE"; sync_files "0.0.0-dev"
    echo "Reset to 0.0.0-dev" ;;
  "") get ;;
  *) echo "Usage: $0 [bump patch|minor|major | set X.Y.Z | reset]" >&2; exit 1 ;;
esac
