#!/bin/bash
# adm Soporte Remoto: arma el paquete .deb de Linux a partir del bundle de Flutter ya compilado.
#
# Equivale a build_flutter_deb() de build.py, con el nombre propio en todas las rutas: el programa busca su servicio,
# su .desktop y su proceso por el nombre interno en minúsculas (`adm-soporte-remoto`, src/platform/linux.rs), así que
# con las rutas de RustDesk el servicio no arrancaría (lo mismo que pasó en Windows con el ejecutable).
#
# Uso: adm/linux/empaquetar-deb.sh <versión> <arquitectura deb> <carpeta del bundle> <archivo .deb de salida>
set -euo pipefail

VERSION="$1"; ARQ="$2"; BUNDLE="$3"; SALIDA="$4"
APP=adm-soporte-remoto
RAIZ="$(cd "$(dirname "$0")/../.." && pwd)"
T="$(mktemp -d)"
trap 'rm -rf "$T"' EXIT

[ -x "$BUNDLE/$APP" ] || { echo "No está $BUNDLE/$APP: compile Flutter con BINARY_NAME $APP" >&2; exit 1; }

install -d "$T/usr/bin" "$T/usr/share/$APP/files/systemd" "$T/usr/share/applications" \
    "$T/usr/share/icons/hicolor/256x256/apps" "$T/usr/share/icons/hicolor/scalable/apps" "$T/DEBIAN"
cp -r "$BUNDLE"/. "$T/usr/share/$APP/"
# Mismo marcador que crea build.py (el programa lo usa para pedir permisos con polkit).
printf '#!/bin/sh\n' > "$T/usr/share/$APP/files/polkit"; chmod a+x "$T/usr/share/$APP/files/polkit"
cp "$RAIZ/res/128x128@2x.png" "$T/usr/share/icons/hicolor/256x256/apps/$APP.png"
cp "$RAIZ/res/scalable.svg" "$T/usr/share/icons/hicolor/scalable/apps/$APP.svg"

cat > "$T/usr/share/$APP/files/systemd/$APP.service" <<EOF
[Unit]
Description=adm Soporte Remoto
Requires=network.target
After=systemd-user-sessions.service

[Service]
Type=simple
ExecStart=/usr/bin/$APP --service
# detiene --tray y --server
ExecStop=pkill -f "$APP --"
PIDFile=/run/$APP.pid
KillMode=mixed
TimeoutStopSec=30
User=root
LimitNOFILE=100000
Environment="PULSE_LATENCY_MSEC=60" "PIPEWIRE_LATENCY=1024/48000"

[Install]
WantedBy=multi-user.target
EOF

cat > "$T/usr/share/applications/$APP.desktop" <<EOF
[Desktop Entry]
Name=adm Soporte Remoto
GenericName=Soporte remoto
Comment=Soporte remoto de Advising Technology
Exec=$APP %u
Icon=$APP
Terminal=false
Type=Application
StartupNotify=true
Categories=Network;RemoteAccess;GTK;
Keywords=remote-desktop;soporte;advising;
StartupWMClass=$APP
EOF

cat > "$T/usr/share/applications/$APP-link.desktop" <<EOF
[Desktop Entry]
Name=adm Soporte Remoto
NoDisplay=true
MimeType=x-scheme-handler/$APP;
TryExec=$APP
Exec=$APP %u
Icon=$APP
Terminal=false
Type=Application
StartupNotify=false
StartupWMClass=$APP
EOF

cat > "$T/DEBIAN/control" <<EOF
Package: $APP
Section: net
Priority: optional
Version: $VERSION
Architecture: $ARQ
Maintainer: ADVISING TECHNOLOGY S.A.S. <soporte@atasesorias.com>
Homepage: https://github.com/battusair1/adm-soporte-remoto
Depends: libgtk-3-0t64 | libgtk-3-0, libxcb-randr0, libxdo3 | libxdo4, libxfixes3, libxcb-shape0, libxcb-xfixes0, libasound2t64 | libasound2, libsystemd0, curl, libva2, libva-drm2, libva-x11-2, libgstreamer-plugins-base1.0-0, gstreamer1.0-pipewire
Recommends: libayatana-appindicator3-1
Description: adm Soporte Remoto (Advising Technology)
 Cliente de soporte remoto de Advising Technology basado en RustDesk 1.5.0 (AGPL-3.0).
EOF

cat > "$T/DEBIAN/preinst" <<EOF
#!/bin/bash
set -e
case \$1 in
    install|upgrade)
        if [ "\$(basename "\$(readlink /proc/1/exe)")" = systemd ]; then
            systemctl stop $APP >/dev/null 2>&1 || true
            sleep 1
        fi
        ;;
esac
exit 0
EOF

cat > "$T/DEBIAN/postinst" <<EOF
#!/bin/bash
set -e
if [ "\$1" = configure ]; then
    ln -f -s /usr/share/$APP/$APP /usr/bin/$APP
    if [ "\$(basename "\$(readlink /proc/1/exe)")" = systemd ]; then
        mkdir -p /usr/lib/systemd/system/
        cp /usr/share/$APP/files/systemd/$APP.service /usr/lib/systemd/system/$APP.service
        # systemd exige ruta absoluta en ExecStop (falla en Ubuntu 18.04 con «pkill» suelto)
        if [ -e /usr/bin/pkill ]; then
            sed -i "s|=pkill|=/usr/bin/pkill|" /usr/lib/systemd/system/$APP.service
        fi
        systemctl daemon-reload
        systemctl enable $APP
        systemctl start $APP
    fi
fi
EOF

cat > "$T/DEBIAN/prerm" <<EOF
#!/bin/bash
set -e
case \$1 in
    remove|upgrade)
        rm -f /usr/bin/$APP
        if [ "\$(basename "\$(readlink /proc/1/exe)")" = systemd ]; then
            systemctl stop $APP || true
            systemctl disable $APP || true
            rm -f /etc/systemd/system/$APP.service /usr/lib/systemd/system/$APP.service
        fi
        ;;
esac
exit 0
EOF

cat > "$T/DEBIAN/postrm" <<EOF
#!/bin/bash
set -e
case \$1 in
    purge)
        rm -rf /root/.config/$APP || true
        ;;
esac
exit 0
EOF
chmod 0755 "$T/DEBIAN/preinst" "$T/DEBIAN/postinst" "$T/DEBIAN/prerm" "$T/DEBIAN/postrm"

chmod 0755 "$T"; chmod -R u+rwX,go+rX,go-w "$T"
( cd "$T" && find usr -type f -exec md5sum {} + > DEBIAN/md5sums )
dpkg-deb --root-owner-group -b "$T" "$SALIDA"
dpkg-deb -I "$SALIDA"
