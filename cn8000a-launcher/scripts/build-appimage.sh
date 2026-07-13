#!/usr/bin/env bash
# Build a portable Linux AppImage for CN8000A KVM Launcher.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="${ROOT_DIR}/build/appimage"
APPDIR="${BUILD_DIR}/CN8000A-KVM.AppDir"
APPIMAGE_TOOL="${ROOT_DIR}/.cache/appimagetool-x86_64.AppImage"
APP_PAYLOAD="${APPDIR}/usr/lib/cn8000a"

if [[ ! -d "${ROOT_DIR}/runtime/bin" ]]; then
  "${ROOT_DIR}/scripts/download-runtime.sh"
fi
if [[ ! -x "${ROOT_DIR}/python-linux/bin/python3" ]]; then
  "${ROOT_DIR}/scripts/download-python-runtime.sh" linux
fi

rm -rf "${APPDIR}"
mkdir -p "${APPDIR}/usr/bin" "${APP_PAYLOAD}"

cp -a "${ROOT_DIR}/launcher.py" "${ROOT_DIR}/cn8000_client.py" "${ROOT_DIR}/widgets.py" "${ROOT_DIR}/ui_theme.py" "${APP_PAYLOAD}/"
cp -a "${ROOT_DIR}/i18n" "${APP_PAYLOAD}/"
cp -a "${ROOT_DIR}/resources" "${APP_PAYLOAD}/"
cp -a "${ROOT_DIR}/runtime" "${APP_PAYLOAD}/runtime"
cp -a "${ROOT_DIR}/python-linux" "${APP_PAYLOAD}/python"

cat > "${APPDIR}/usr/bin/cn8000a-kvm" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../lib/cn8000a" && pwd)"
export PYTHONPATH="${APP_DIR}${PYTHONPATH:+:${PYTHONPATH}}"
cd "${APP_DIR}"
exec "${APP_DIR}/python/bin/python3" "${APP_DIR}/launcher.py" "$@"
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

ICON_SRC="${ROOT_DIR}/resources/icon-256.png"
if [[ ! -f "${ICON_SRC}" ]]; then
  ICON_SRC="${ROOT_DIR}/resources/icon.png"
fi
cp "${ICON_SRC}" "${APPDIR}/cn8000a-kvm.png"

if [[ ! -x "${APPIMAGE_TOOL}" ]]; then
  curl -fL -o "${APPIMAGE_TOOL}" \
    https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
  chmod +x "${APPIMAGE_TOOL}"
fi

mkdir -p "${ROOT_DIR}/dist"
ARCH=x86_64 VERSION=1.3.1 "${APPIMAGE_TOOL}" "${APPDIR}" "${ROOT_DIR}/dist/CN8000A-KVM-x86_64.AppImage"
echo "Built ${ROOT_DIR}/dist/CN8000A-KVM-x86_64.AppImage"
