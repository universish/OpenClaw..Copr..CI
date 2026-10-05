%install
rm -rf %{buildroot}

# Uygulama ana dizini (/opt/openclaw)
mkdir -p %{buildroot}/opt/%{name}
cp -a app/* %{buildroot}/opt/%{name}/

# Çalıştırılabilir dosyaların izinlerini güvenceye al
chmod -R a+rX %{buildroot}/opt/%{name}
find %{buildroot}/opt/%{name} -type f \( -name "AppRun*" -o -name "*openclaw*" -o -name "*OpenClaw*" \) -exec chmod +x {} + 2>/dev/null || true

# /usr/bin/openclaw için kararlı başlatıcı betik
mkdir -p %{buildroot}%{_bindir}
cat << 'EOF' > %{buildroot}%{_bindir}/%{name}
#!/usr/bin/env bash
set -e

APP_DIR="/opt/openclaw"

# Gömülü AppImage kütüphanelerini tanıt
if [ -d "$APP_DIR/usr/lib" ]; then
    export LD_LIBRARY_PATH="$APP_DIR/usr/lib:$APP_DIR/usr/lib64:${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
fi
if [ -d "$APP_DIR/apprun-hooks" ]; then
    for hook in "$APP_DIR"/apprun-hooks/*; do
        [ -r "$hook" ] && . "$hook" 2>/dev/null || true
    done
fi

# Çalıştırıcı ikiliyi sırasıyla dene
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
    # Son çare: /opt/openclaw altındaki ilk çalıştırılabilir ana ikiliyi bul
    EXEC_BIN=$(find "$APP_DIR" -maxdepth 3 -type f -executable ! -name "*.so*" ! -name "*.sh" | head -n 1)
    if [ -n "$EXEC_BIN" ]; then
        exec "$EXEC_BIN" "$@"
    fi
    echo "Hata: /opt/openclaw altında çalıştırılabilir OpenClaw ikilisi bulunamadı." >&2
    exit 1
fi
EOF
chmod +x %{buildroot}%{_bindir}/%{name}

# Masaüstü kısayolu
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

# Uygulama simgesi
mkdir -p %{buildroot}%{_datadir}/icons/hicolor/512x512/apps
if [ -f %{buildroot}/opt/%{name}/openclaw.png ]; then
    install -m 0644 %{buildroot}/opt/%{name}/openclaw.png %{buildroot}%{_datadir}/icons/hicolor/512x512/apps/%{name}.png
elif [ -f %{buildroot}/opt/%{name}/OpenClaw.png ]; then
    install -m 0644 %{buildroot}/opt/%{name}/OpenClaw.png %{buildroot}%{_datadir}/icons/hicolor/512x512/apps/%{name}.png
elif [ -f %{buildroot}/opt/%{name}/openclaw-desktop.png ]; then
    install -m 0644 %{buildroot}/opt/%{name}/openclaw-desktop.png %{buildroot}%{_datadir}/icons/hicolor/512x512/apps/%{name}.png
fi

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/%{name}.desktop

%files
/opt/%{name}
%{_bindir}/%{name}
%{_datadir}/applications/%{name}.desktop
%{_datadir}/icons/hicolor/512x512/apps/%{name}.png
