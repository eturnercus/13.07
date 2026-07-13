#!/usr/bin/env bash
# Ensure JRE 8 + IcedTea-Web (javaws) are present before packaging.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

javaws_ready() {
  [[ -x "${ROOT_DIR}/runtime/icedtea-web/bin/javaws" ]] \
    || [[ -x "${ROOT_DIR}/runtime/bin/javaws" ]]
}

if ! javaws_ready; then
  echo "Runtime incomplete — downloading JRE 8 + IcedTea-Web..."
  "${ROOT_DIR}/scripts/download-runtime.sh"
fi

if ! javaws_ready; then
  echo "ERROR: javaws not found in ${ROOT_DIR}/runtime after download." >&2
  exit 1
fi

echo "Runtime OK: $(readlink -f "${ROOT_DIR}/runtime/icedtea-web/bin/javaws" 2>/dev/null || readlink -f "${ROOT_DIR}/runtime/bin/javaws")"
