#!/usr/bin/env bash
# Download portable Java 8 + IcedTea-Web runtime for CN8000A launcher builds.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNTIME_DIR="${ROOT_DIR}/runtime"
CACHE_DIR="${ROOT_DIR}/.cache"
mkdir -p "${CACHE_DIR}"

OS="$(uname -s)"
ARCH="$(uname -m)"

ITW_VERSION="1.8.8"
ITW_BASE="https://github.com/AdoptOpenJDK/IcedTea-Web/releases/download/icedtea-web-${ITW_VERSION}"

# Temurin 8 is used because it still ships javaws-compatible JRE and accepts security overrides.
TEMURIN_API="https://api.adoptium.net/v3/binary/latest/8/ga"

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

install_linux() {
  local jre_tgz="${CACHE_DIR}/temurin8-jre-linux.tar.gz"
  local itw_zip="${CACHE_DIR}/icedtea-web-portable.zip"

  download "${TEMURIN_API}/linux/x64/jre/hotspot/normal/eclipse?project=jdk" "${jre_tgz}"
  download "${ITW_BASE}/icedtea-web-${ITW_VERSION}.linux.bin.zip" "${itw_zip}"

  rm -rf "${RUNTIME_DIR}"
  mkdir -p "${RUNTIME_DIR}"
  tar -xzf "${jre_tgz}" -C "${RUNTIME_DIR}" --strip-components=1

  unzip -oq "${itw_zip}" -d "${CACHE_DIR}/icedtea-web"
  ITW_SRC="$(find "${CACHE_DIR}/icedtea-web" -maxdepth 2 -type d -name 'icedtea-web-*' | head -n1)"
  mkdir -p "${RUNTIME_DIR}/icedtea-web"
  cp -a "${ITW_SRC}/." "${RUNTIME_DIR}/icedtea-web/"

  cat > "${RUNTIME_DIR}/bin/javaws" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export JAVA_HOME="${ROOT}"
export PATH="${ROOT}/bin:${PATH}"
exec "${ROOT}/icedtea-web/bin/javaws" "$@"
EOF
  chmod +x "${RUNTIME_DIR}/bin/javaws"
}

install_windows() {
  local jre_zip="${CACHE_DIR}/temurin8-jre-windows.zip"
  local itw_zip="${CACHE_DIR}/icedtea-web-win.zip"

  download "${TEMURIN_API}/windows/x64/jre/hotspot/normal/eclipse?project=jdk" "${jre_zip}"
  download "${ITW_BASE}/icedtea-web-${ITW_VERSION}.win.bin.zip" "${itw_zip}"

  rm -rf "${RUNTIME_DIR}"
  mkdir -p "${RUNTIME_DIR}"
  unzip -oq "${jre_zip}" -d "${CACHE_DIR}/temurin-win"
  JRE_SRC="$(find "${CACHE_DIR}/temurin-win" -maxdepth 2 -type d -name 'jdk8u*-jre' | head -n1)"
  cp -a "${JRE_SRC}/." "${RUNTIME_DIR}/"

  unzip -oq "${itw_zip}" -d "${CACHE_DIR}/icedtea-win"
  ITW_SRC="$(find "${CACHE_DIR}/icedtea-win" -maxdepth 2 -type d -name 'icedtea-web-*' | head -n1)"
  cp -a "${ITW_SRC}/." "${RUNTIME_DIR}/icedtea-web/"

  cat > "${RUNTIME_DIR}/bin/javaws.cmd" <<'EOF'
@echo off
setlocal
set "ROOT=%~dp0.."
set "JAVA_HOME=%ROOT%"
set "PATH=%ROOT%\bin;%PATH%"
"%ROOT%\icedtea-web\bin\javaws.exe" %*
EOF
}

case "${OS}" in
  Linux)
    install_linux
  ;;
  MINGW*|MSYS*|CYGWIN*)
    install_windows
  ;;
  *)
    echo "Unsupported build host OS: ${OS}" >&2
    exit 1
  ;;
esac

echo "Runtime installed to ${RUNTIME_DIR}"
