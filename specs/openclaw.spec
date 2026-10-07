%global debug_package %{nil}
%global __strip /bin/true
%global __brp_mangle_shebangs /bin/true
%global __provides_exclude_from ^/opt/%{name}/.*$
%global __requires_exclude_from ^/opt/%{name}/.*$
%global _build_id_links none

Name:           openclaw
Version:        %{_version}
Release:        1%{?dist}
Summary:        All your chats, one OpenClaw - AI Assistant and Gateway
License:        Proprietary
URL:            https://openclaw.ai
ExclusiveArch:  x86_64

Source0:        openclaw-%{version}-x86_64.tar.gz

BuildRequires:  desktop-file-utils

Requires:       hicolor-icon-theme
Requires:       xdg-utils

%description
OpenClaw is a personal AI assistant and communication gateway.
This package repackages the upstream prebuilt distribution into a native Fedora RPM.

%prep
%autosetup -n openclaw-%{version}-x86_64

%build
# Prebuilt binary / AppImage - derleme adımı gerekmez.

%install
rm -rf %{buildroot}

# Uygulama ana dizini (/opt/openclaw)
mkdir -p %{buildroot}/opt/%{name}
cp -a app/* %{buildroot}/opt/%{name}/

# Dosya izinleri
chmod -R a+rX %{buildroot}/opt/%{name}
find %{buildroot}/opt/%{name} -type f \( -name "AppRun*" -o -name "*openclaw*" -o -name "*OpenClaw*" \) -exec chmod +x {} + 2>/dev/null || true

# /usr/bin/openclaw başlatıcı betiği
mkdir -p %{buildroot}%{_bindir}
cat << 'EOF' > %{buildroot}%{_bindir}/%{name}
#!/usr/bin/env bash
set -e

APP_DIR="/opt/openclaw"

if [ -d "$APP_DIR/usr/lib" ]; then
    export LD_LIBRARY_PATH="$APP_DIR/usr/lib:$APP_DIR/usr/lib64:${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
fi
if [ -d "$APP_DIR/apprun-hooks" ]; then
    for hook in "$APP_DIR"/apprun-hooks/*; do
        [ -r "$hook" ] && . "$hook" 2>/dev/null || true
    done
fi

if [ -x "$APP_DIR/AppRun" ]; then
    exec "$APP_DIR/AppRun" "$@"
elif [ -x "$APP_DIR/AppRun.wrapped" ]; then
    exec "$APP_DIR/AppRun.wrapped" "$@"
elif [ -x "$APP_DIR/usr/bin/openclaw" ]; then
    exec "$APP_DIR/usr/bin/openclaw" "$@"
elif [ -x "$APP_DIR/usr/bin/OpenClaw" ]; then
    exec "$APP_DIR/usr/bin/OpenClaw" "$@"
elif [ -x "$APP_DIR/OpenClaw" ]; then
    exec "$APP_DIR/OpenClaw" "$@"
elif [ -x "$APP_DIR/openclaw" ]; then
    exec "$APP_DIR/openclaw" "$@"
else
    EXEC_BIN=$(find "$APP_DIR" -maxdepth 3 -type f -executable ! -name "*.so*" ! -name "*.sh" | head -n 1)
    if [ -n "$EXEC_BIN" ]; then
        exec "$EXEC_BIN" "$@"
    fi
    echo "Hata: /opt/openclaw altında çalıştırılabilir OpenClaw ikilisi bulunamadı." >&2
    exit 1
fi
EOF
chmod +x %{buildroot}%{_bindir}/%{name}

# Masaüstü dosyası kurulumu
mkdir -p %{buildroot}%{_datadir}/applications
cat << 'EOF' > %{buildroot}%{_datadir}/applications/%{name}.desktop
[Desktop Entry]
Name=OpenClaw
Comment=All your chats, one OpenClaw - AI Assistant and Gateway
GenericName=AI Assistant
Exec=/usr/bin/openclaw --ozone-platform-hint=auto --disable-features=Vulkan --enable-features=WaylandWindowDecorations %U
Icon=openclaw
Type=Application
StartupNotify=true
StartupWMClass=OpenClaw
Terminal=false
Categories=Utility;Network;Chat;
MimeType=x-scheme-handler/openclaw;
EOF

# Uygulama simgesi (Paket içinden ara, yoksa fallback oluştur)
mkdir -p %{buildroot}%{_datadir}/icons/hicolor/512x512/apps
ICON_SRC=$(find %{buildroot}/opt/%{name} -type f \( -iname "*openclaw*.png" -o -iname "*OpenClaw*.png" -o -iname "*icon*.png" \) 2>/dev/null | head -n 1)

if [ -n "$ICON_SRC" ]; then
    install -m 0644 "$ICON_SRC" %{buildroot}%{_datadir}/icons/hicolor/512x512/apps/%{name}.png
else
    # npm gibi saf CLI sürümlerinde %files hatasını önlemek için 1x1 şeffaf PNG üret
    echo "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=" | base64 -d > %{buildroot}%{_datadir}/icons/hicolor/512x512/apps/%{name}.png
fi

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/%{name}.desktop

%files
/opt/%{name}
%{_bindir}/%{name}
%{_datadir}/applications/%{name}.desktop
%{_datadir}/icons/hicolor/512x512/apps/%{name}.png

%changelog
* Mon Oct 05 2026 Saffet Yavuz <universish@tutamail.com> - %{version}-1
- Automatic packaging from upstream release.
