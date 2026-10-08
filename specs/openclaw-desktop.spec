%global debug_package %{nil}
%global __strip /bin/true
%global __brp_mangle_shebangs /bin/true
%global __provides_exclude_from ^/opt/openclaw-desktop/.*$
%global __requires_exclude_from ^/opt/openclaw-desktop/.*$
%global _build_id_links none

Name:           openclaw-desktop
Version:        %{_version}
Release:        %{_release}%{?dist}
Summary:        OpenClaw Desktop GUI Client
License:        Proprietary
URL:            https://openclaw.ai
ExclusiveArch:  x86_64

Source0:        openclaw-desktop-%{version}-x86_64.tar.gz

BuildRequires:  desktop-file-utils
Requires:       hicolor-icon-theme
Requires:       xdg-utils

%description
OpenClaw Desktop GUI Client powered by Electron. This package provides the graphical interface separated from the core CLI gateway.

%prep
%autosetup -n openclaw-desktop-%{version}-x86_64

%build

%install
%install
rm -rf %{buildroot}

mkdir -p %{buildroot}/opt/openclaw-desktop
cp -a app/* %{buildroot}/opt/openclaw-desktop/

chmod -R a+rX %{buildroot}/opt/openclaw-desktop
find %{buildroot}/opt/openclaw-desktop -type f \( -name "AppRun*" -o -name "*openclaw*" -o -name "*OpenClaw*" \) -exec chmod +x {} + 2>/dev/null || true

mkdir -p %{buildroot}%{_bindir}

# Masaüstü/WebUI Arayüzü Başlatıcısı (/usr/bin/openclaw-desktop)
cat << 'EOF' > %{buildroot}%{_bindir}/openclaw-desktop
#!/usr/bin/env bash

# Electron Wayland odaklanma ve native GPU uyumluluk bayrakları
ELECTRON_OPTS="--ozone-platform-hint=auto --enable-features=WaylandWindowDecorations"

if [ -x /opt/openclaw-desktop/AppRun ]; then
    exec /opt/openclaw-desktop/AppRun $ELECTRON_OPTS "$@"
elif [ -x /opt/openclaw-desktop/OpenClaw ] && [ ! -d /opt/openclaw-desktop/OpenClaw ]; then
    exec /opt/openclaw-desktop/OpenClaw $ELECTRON_OPTS "$@"
else
    if command -v openclaw-cli >/dev/null 2>&1; then
        exec openclaw-cli dashboard "$@"
    else
        echo "Hata: OpenClaw Masaüstü ikilisi bulunamadı." >&2
        exit 1
    fi
fi
EOF
chmod +x %{buildroot}%{_bindir}/openclaw-desktop

# Masaüstü Kısayolu (.desktop)
mkdir -p %{buildroot}%{_datadir}/applications
cat << 'EOF' > %{buildroot}%{_datadir}/applications/openclaw.desktop
[Desktop Entry]
Name=OpenClaw
Comment=All your chats, one OpenClaw - AI Assistant and Gateway
GenericName=AI Assistant
Exec=/usr/bin/openclaw-desktop
Icon=openclaw
Type=Application
StartupNotify=true
# Dock üzerindeki yeni pencerelerin tek ikonda gruplanması için xprop WM_CLASS eşleşmesi
StartupWMClass=openclaw-desktop
Terminal=false
Categories=Utility;Network;Chat;
EOF

# Yüksek Çözünürlüklü İkon Kurulumu
mkdir -p %{buildroot}%{_datadir}/icons/hicolor/512x512/apps
mkdir -p %{buildroot}%{_datadir}/pixmaps

ICON_SRC=$(find %{buildroot}/opt/openclaw-desktop -maxdepth 2 -type f \( -iname "*openclaw*.png" -o -iname "*OpenClaw*.png" -o -iname "*icon*.png" \) 2>/dev/null | head -n 1)

if [ -n "$ICON_SRC" ]; then
    install -m 0644 "$ICON_SRC" %{buildroot}%{_datadir}/icons/hicolor/512x512/apps/openclaw.png
    install -m 0644 "$ICON_SRC" %{buildroot}%{_datadir}/pixmaps/openclaw.png
else
    echo "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=" | base64 -d > %{buildroot}%{_datadir}/icons/hicolor/512x512/apps/openclaw.png
    install -m 0644 %{buildroot}%{_datadir}/icons/hicolor/512x512/apps/openclaw.png %{buildroot}%{_datadir}/pixmaps/openclaw.png
fi

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/openclaw.desktop

%files
/opt/openclaw-desktop
%{_bindir}/openclaw-desktop
%{_datadir}/applications/openclaw.desktop
%{_datadir}/icons/hicolor/512x512/apps/openclaw.png
%{_datadir}/pixmaps/openclaw.png

%changelog
* Wed Oct 07 2026 Saffet Yavuz <universish@tutamail.com> - %{version}-%{release}
- Isolated desktop GUI build for independent updates.
