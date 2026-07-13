#!/usr/bin/env bash
# Build a portable Linux AppImage for CN8000A KVM Launcher.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="${ROOT_DIR}/build/appimage"
APPDIR="${BUILD_DIR}/CN8000A-KVM.AppDir"
APPIMAGE_TOOL="${ROOT_DIR}/.cache/appimagetool-x86_64.AppImage"

if [[ ! -d "${ROOT_DIR}/runtime/bin" ]]; then
  "${ROOT_DIR}/scripts/download-runtime.sh"
fi

rm -rf "${APPDIR}"
mkdir -p "${APPDIR}/usr/bin" "${APPDIR}/usr/lib/cn8000a"

cp -a "${ROOT_DIR}/launcher.py" "${ROOT_DIR}/cn8000_client.py" "${APPDIR}/usr/lib/cn8000a/"
cp -a "${ROOT_DIR}/resources" "${APPDIR}/usr/lib/cn8000a/"
cp -a "${ROOT_DIR}/runtime" "${APPDIR}/usr/lib/cn8000a/runtime"

cat > "${APPDIR}/usr/bin/cn8000a-kvm" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../lib/cn8000a" && pwd)"
export PYTHONPATH="${APP_DIR}${PYTHONPATH:+:${PYTHONPATH}}"
cd "${APP_DIR}"
exec python3 "${APP_DIR}/launcher.py" "$@"
EOF
chmod +x "${APPDIR}/usr/bin/cn8000a-kvm"

cat > "${APPDIR}/AppRun" <<'EOF'
#!/usr/bin/env bash
HERE="$(dirname "$(readlink -f "$0")")"
exec "${HERE}/usr/bin/cn8000a-kvm" "$@"
EOF
chmod +x "${APPDIR}/AppRun"

cat > "${APPDIR}/cn8000a-kvm.desktop" <<'EOF'
[Desktop Entry]
Type=Application
Name=CN8000A KVM Launcher
Comment=Portable launcher for ATEN CN8000A Java KVM viewer
Exec=cn8000a-kvm
Icon=cn8000a-kvm
Categories=Network;RemoteAccess;
Terminal=false
EOF

# Simple placeholder icon (1x1 PNG) so appimagetool does not fail.
python3 - <<'PY' "${APPDIR}/cn8000a-kvm.png"
import base64, pathlib, sys
png = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO2T2WkAAAAASUVORK5CYII="
)
pathlib.Path(sys.argv[1]).write_bytes(png)
PY

if [[ ! -x "${APPIMAGE_TOOL}" ]]; then
  curl -fL -o "${APPIMAGE_TOOL}" \
    https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
  chmod +x "${APPIMAGE_TOOL}"
fi

mkdir -p "${ROOT_DIR}/dist"
ARCH=x86_64 VERSION=1.0.0 "${APPIMAGE_TOOL}" "${APPDIR}" "${ROOT_DIR}/dist/CN8000A-KVM-x86_64.AppImage"
echo "Built ${ROOT_DIR}/dist/CN8000A-KVM-x86_64.AppImage"
