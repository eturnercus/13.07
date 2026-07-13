#!/usr/bin/env bash
# Post-build sanity checks for release artifacts.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FAIL=0

javaws_present() {
  local dir="$1"
  [[ -x "${dir}/icedtea-web/bin/javaws" \
    || -f "${dir}/icedtea-web/bin/javaws.exe" \
    || -x "${dir}/bin/javaws" \
    || -f "${dir}/bin/javaws.cmd" ]]
}

check_javaws_in_dir() {
  local dir="$1"
  local label="$2"
  if javaws_present "${dir}"; then
    echo "OK ${label}: javaws found"
  else
    echo "FAIL ${label}: javaws missing in ${dir}" >&2
    FAIL=1
  fi
}

APPIMAGE="${ROOT_DIR}/dist/CN8000A-KVM-x86_64.AppImage"
SQUASH="${ROOT_DIR}/dist/squashfs-root"
if [[ -f "${APPIMAGE}" ]]; then
  rm -rf "${SQUASH}"
  (cd "${ROOT_DIR}/dist" && ./CN8000A-KVM-x86_64.AppImage --appimage-extract >/dev/null 2>&1)
  if [[ -d "${SQUASH}/usr/lib/cn8000a/runtime" ]]; then
    check_javaws_in_dir "${SQUASH}/usr/lib/cn8000a/runtime" "AppImage runtime"
    [[ -f "${SQUASH}/usr/lib/cn8000a/kvm_transport.py" ]] \
      && echo "OK AppImage: kvm_transport.py" \
      || { echo "FAIL AppImage: kvm_transport.py missing" >&2; FAIL=1; }
    rm -rf "${SQUASH}"
  else
    echo "FAIL AppImage: could not extract payload" >&2
    FAIL=1
  fi
fi

WIN_APP="${ROOT_DIR}/dist/CN8000A-KVM-Portable-Win64/app"
if [[ -d "${WIN_APP}/runtime" ]]; then
  check_javaws_in_dir "${WIN_APP}/runtime" "Windows ZIP runtime"
  [[ -f "${WIN_APP}/kvm_transport.py" ]] \
    && echo "OK Windows: kvm_transport.py" \
    || { echo "FAIL Windows: kvm_transport.py missing" >&2; FAIL=1; }
fi

if [[ "${FAIL}" -ne 0 ]]; then
  exit 1
fi
echo "All package checks passed."
