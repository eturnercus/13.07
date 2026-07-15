#!/usr/bin/env bash
# Build Windows portable ZIP with CN8000A-KVM.exe (PyInstaller) + Java runtime.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CACHE_DIR="${ROOT_DIR}/.cache"
RUNTIME_DIR="${ROOT_DIR}/runtime-win"
DIST_DIR="${ROOT_DIR}/dist/CN8000A-KVM-Portable-Win64"
ZIP_OUT="${ROOT_DIR}/dist/CN8000A-KVM-Portable-Win64.zip"
PYI_DIST="${ROOT_DIR}/dist/CN8000A-KVM"

TEMURIN_API="https://api.adoptium.net/v3/binary/latest/8/ga"
ITW_URL="https://github.com/AdoptOpenJDK/IcedTea-Web/releases/download/icedtea-web-1.8.8/icedtea-web-1.8.8.win.bin.zip"

export WINEDEBUG="${WINEDEBUG:--all}"

mkdir -p "${ROOT_DIR}/dist"
"${ROOT_DIR}/scripts/ensure-runtime.sh" 2>/dev/null || true
if [[ ! -x "${ROOT_DIR}/runtime/icedtea-web/bin/javaws" && ! -x "${ROOT_DIR}/runtime/bin/javaws" ]]; then
  "${ROOT_DIR}/scripts/download-runtime.sh"
fi

download() {
  local url="$1"
  local out="$2"
  if [[ ! -f "${out}" ]]; then
    echo "Downloading ${url}"
    curl -fL --retry 3 -o "${out}" "${url}"
  fi
}

if [[ ! -x "${ROOT_DIR}/python-win/python.exe" ]]; then
  "${ROOT_DIR}/scripts/download-python-runtime.sh" windows
fi

if ! wine "${ROOT_DIR}/python-win/python.exe" -c "import PyInstaller" 2>/dev/null; then
  echo "Installing PyInstaller into Windows Python (Wine)..."
  wine "${ROOT_DIR}/python-win/python.exe" -m pip install pyinstaller
fi

JRE_ZIP="${CACHE_DIR}/temurin8-jre-windows.zip"
ITW_ZIP="${CACHE_DIR}/icedtea-web-win.zip"
download "${TEMURIN_API}/windows/x64/jre/hotspot/normal/eclipse?project=jdk" "${JRE_ZIP}"
download "${ITW_URL}" "${ITW_ZIP}"

rm -rf "${RUNTIME_DIR}" "${DIST_DIR}" "${PYI_DIST}"
mkdir -p "${RUNTIME_DIR}"

unzip -oq "${JRE_ZIP}" -d "${CACHE_DIR}/temurin-win"
JRE_SRC="$(find "${CACHE_DIR}/temurin-win" -maxdepth 2 -type d -name 'jdk8u*-jre' | head -n1)"
cp -a "${JRE_SRC}/." "${RUNTIME_DIR}/"

unzip -oq "${ITW_ZIP}" -d "${CACHE_DIR}/icedtea-win"
ITW_SRC="$(find "${CACHE_DIR}/icedtea-win" -maxdepth 2 -type d -name 'icedtea-web-*' | head -n1)"
mkdir -p "${RUNTIME_DIR}/icedtea-web"
cp -a "${ITW_SRC}/." "${RUNTIME_DIR}/icedtea-web/"

cat > "${RUNTIME_DIR}/bin/javaws.cmd" <<'EOF'
@echo off
setlocal
set "ROOT=%~dp0.."
set "JAVA_HOME=%ROOT%"
set "PATH=%ROOT%\bin;%PATH%"
"%ROOT%\icedtea-web\bin\javaws.exe" %*
EOF

echo "Building CN8000A-KVM.exe with PyInstaller..."
(
  cd "${ROOT_DIR}"
  wine python-win/python.exe -m PyInstaller --noconfirm --clean cn8000a.spec
)

mkdir -p "${DIST_DIR}"
cp -a "${PYI_DIST}/." "${DIST_DIR}/"
cp -a "${RUNTIME_DIR}" "${DIST_DIR}/runtime"

rm -f "${ZIP_OUT}"
(cd "${ROOT_DIR}/dist" && zip -qr "$(basename "${ZIP_OUT}")" "$(basename "${DIST_DIR}")")
echo "Built ${ZIP_OUT} (contains CN8000A-KVM.exe)"
