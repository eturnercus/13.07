#!/usr/bin/env bash
# Download portable Python runtime (with tkinter) for release packaging.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CACHE_DIR="${ROOT_DIR}/.cache"
PY_RELEASE="20260623"
PY_VERSION="3.12.13"

usage() {
  echo "Usage: $0 <linux|windows>" >&2
  exit 1
}

TARGET="${1:-}"
[[ -n "${TARGET}" ]] || usage

mkdir -p "${CACHE_DIR}"

download() {
  local url="$1"
  local out="$2"
  if [[ -f "${out}" ]]; then
    echo "Using cached $(basename "${out}")"
    return 0
  fi
  echo "Downloading ${url}"
  curl -fL --retry 3 --retry-delay 2 -o "${out}" "${url}"
}

case "${TARGET}" in
  linux)
    OUT_DIR="${ROOT_DIR}/python-linux"
    ARCHIVE="${CACHE_DIR}/python-linux-${PY_VERSION}.tar.gz"
    URL="https://github.com/astral-sh/python-build-standalone/releases/download/${PY_RELEASE}/cpython-${PY_VERSION}%2B${PY_RELEASE}-x86_64-unknown-linux-gnu-install_only_stripped.tar.gz"
    ;;
  windows)
    OUT_DIR="${ROOT_DIR}/python-win"
    ARCHIVE="${CACHE_DIR}/python-win-${PY_VERSION}.tar.gz"
    URL="https://github.com/astral-sh/python-build-standalone/releases/download/${PY_RELEASE}/cpython-${PY_VERSION}%2B${PY_RELEASE}-x86_64-pc-windows-msvc-install_only_stripped.tar.gz"
    ;;
  *)
    usage
    ;;
esac

download "${URL}" "${ARCHIVE}"
rm -rf "${OUT_DIR}"
mkdir -p "${OUT_DIR}"
tar -xzf "${ARCHIVE}" -C "${OUT_DIR}" --strip-components=1
echo "Python runtime installed to ${OUT_DIR}"
