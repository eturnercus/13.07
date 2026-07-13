#!/usr/bin/env bash
# Build Windows portable ZIP from Linux (for CI / release packaging).
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CACHE_DIR="${ROOT_DIR}/.cache"
RUNTIME_DIR="${ROOT_DIR}/runtime-win"
DIST_DIR="${ROOT_DIR}/dist/CN8000A-KVM-Portable-Win64"
ZIP_OUT="${ROOT_DIR}/dist/CN8000A-KVM-Portable-Win64.zip"

TEMURIN_API="https://api.adoptium.net/v3/binary/latest/8/ga"
ITW_URL="https://github.com/AdoptOpenJDK/IcedTea-Web/releases/download/icedtea-web-1.8.8/icedtea-web-1.8.8.win.bin.zip"

mkdir -p "${CACHE_DIR}" "${ROOT_DIR}/dist"

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

JRE_ZIP="${CACHE_DIR}/temurin8-jre-windows.zip"
ITW_ZIP="${CACHE_DIR}/icedtea-web-win.zip"
download "${TEMURIN_API}/windows/x64/jre/hotspot/normal/eclipse?project=jdk" "${JRE_ZIP}"
download "${ITW_URL}" "${ITW_ZIP}"

rm -rf "${RUNTIME_DIR}" "${DIST_DIR}"
mkdir -p "${RUNTIME_DIR}" "${DIST_DIR}/app"

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

cp "${ROOT_DIR}/launcher.py" "${ROOT_DIR}/cn8000_client.py" "${ROOT_DIR}/widgets.py" "${ROOT_DIR}/ui_theme.py" "${ROOT_DIR}/kvm_transport.py" "${DIST_DIR}/app/"
cp -a "${ROOT_DIR}/i18n" "${DIST_DIR}/app/"
cp -a "${ROOT_DIR}/resources" "${DIST_DIR}/app/"
cp -a "${RUNTIME_DIR}" "${DIST_DIR}/app/runtime"
cp -a "${ROOT_DIR}/python-win" "${DIST_DIR}/app/python"

cat > "${DIST_DIR}/CN8000A-KVM.bat" <<'EOF'
@echo off
setlocal
set "APP_DIR=%~dp0app"
set "PYTHONPATH=%APP_DIR%"
cd /d "%APP_DIR%"
start "" "%APP_DIR%\python\pythonw.exe" "%APP_DIR%\launcher.py"
EOF

rm -f "${ZIP_OUT}"
(cd "${ROOT_DIR}/dist" && zip -qr "$(basename "${ZIP_OUT}")" "$(basename "${DIST_DIR}")")
echo "Built ${ZIP_OUT}"
