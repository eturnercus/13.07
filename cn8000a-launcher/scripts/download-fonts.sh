#!/usr/bin/env bash
# Bundle DejaVu Sans for consistent Cyrillic rendering on Linux AppImage.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FONTS_DIR="${ROOT_DIR}/resources/fonts"
BASE_URL="https://github.com/prawnpdf/prawn/raw/master/data/fonts"

mkdir -p "${FONTS_DIR}"

download() {
  local name="$1"
  local out="${FONTS_DIR}/${name}"
  if [[ ! -f "${out}" ]]; then
    echo "Downloading ${name}"
    curl -fL --retry 3 -o "${out}" "${BASE_URL}/${name}"
  fi
}

download "DejaVuSans.ttf"
download "DejaVuSans-Bold.ttf"

echo "Fonts ready in ${FONTS_DIR}"
