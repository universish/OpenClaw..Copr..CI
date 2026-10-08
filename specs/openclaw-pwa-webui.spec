%install
rm -rf %{buildroot}
mkdir -p %{buildroot}%{_bindir}
mkdir -p %{buildroot}%{_libexecdir}
mkdir -p %{buildroot}%{_datadir}/applications

# --- 1. AKILLI TARAYICI SARMALAYICISI ---
cat << 'EOF' > %{buildroot}%{_libexecdir}/openclaw-browser-wrapper
#!/usr/bin/env bash
URL="$1"

# GPU Tespiti ve Wayland Chromium Bayrakları
CHROMIUM_FLAGS="--ozone-platform-hint=auto"
if lspci -k 2>/dev/null | grep -iA 2 "VGA" | grep -i "nvidia" > /dev/null; then
    CHROMIUM_FLAGS="$CHROMIUM_FLAGS --disable-features=Vulkan"
else
    CHROMIUM_FLAGS="$CHROMIUM_FLAGS --enable-features=Vulkan"
fi

export MOZ_ENABLE_WAYLAND=1

DEFAULT_BROWSER=$(xdg-settings get default-web-browser 2>/dev/null || xdg-mime query default x-scheme-handler/http)
DEFAULT_BROWSER=$(echo "$DEFAULT_BROWSER" | tr '[:upper:]' '[:lower:]')

if [[ "$DEFAULT_BROWSER" == *"firefox"* ]] || [[ "$DEFAULT_BROWSER" == *"zen"* ]] || [[ "$DEFAULT_BROWSER" == *"librewolf"* ]]; then
    exec xdg-open "$URL"
elif [[ "$DEFAULT_BROWSER" == *"helium"* ]]; then
    exec helium --app="$URL" $CHROMIUM_FLAGS
elif [[ "$DEFAULT_BROWSER" == *"cromite"* ]]; then
    exec cromite --app="$URL" $CHROMIUM_FLAGS
elif [[ "$DEFAULT_BROWSER" == *"thorium"* ]]; then
    exec thorium-browser --app="$URL" $CHROMIUM_FLAGS
elif [[ "$DEFAULT_BROWSER" == *"brave"* ]]; then
    exec brave-browser --app="$URL" $CHROMIUM_FLAGS
elif [[ "$DEFAULT_BROWSER" == *"chrome"* ]]; then
    exec google-chrome --app="$URL" $CHROMIUM_FLAGS
elif [[ "$DEFAULT_BROWSER" == *"chromium"* ]]; then
    exec chromium-browser --app="$URL" $CHROMIUM_FLAGS
elif [[ "$DEFAULT_BROWSER" == *"edge"* ]]; then
    exec microsoft-edge --app="$URL" $CHROMIUM_FLAGS
else
    exec xdg-open "$URL"
fi
EOF
chmod +x %{buildroot}%{_libexecdir}/openclaw-browser-wrapper

# --- 2. ANA BAŞLATICI (GATEWAY TETİKLEYİCİ EKLENDİ) ---
cat << 'EOF' > %{buildroot}%{_bindir}/openclaw-webui
#!/usr/bin/env bash

# Gateway kapalıysa systemd üzerinden uyandır ve hazır olması için bekle
if ! systemctl --user is-active --quiet openclaw-gateway.service; then
    systemctl --user start openclaw-gateway.service
    sleep 2
fi

export BROWSER="/usr/libexec/openclaw-browser-wrapper"
exec openclaw-cli dashboard "$@"
EOF
chmod +x %{buildroot}%{_bindir}/openclaw-webui

# --- 3. MASAÜSTÜ KISAYOLU (.desktop) ---
cat << 'EOF' > %{buildroot}%{_datadir}/applications/openclaw-webui.desktop
[Desktop Entry]
Name=OpenClaw WebUI
Comment=OpenClaw AI Assistant (PWA Mode)
GenericName=AI Assistant
Exec=/usr/bin/openclaw-webui
# Şeffaf ikon yerine sistemin yerleşik web veya sohbet ikonunu kullanıyoruz
Icon=applications-internet
Type=Application
StartupNotify=true
StartupWMClass=openclaw-webui
Terminal=false
Categories=Utility;Network;Chat;
EOF

%files
%{_bindir}/openclaw-webui
%{_libexecdir}/openclaw-browser-wrapper
%{_datadir}/applications/openclaw-webui.desktop

%changelog
* Thu Oct 08 2026 Saffet Yavuz <universish@tutamail.com> - %{version}-%{release}
- Added Helium browser support to PWA wrapper.
- Added auto-start trigger for systemd gateway daemon.
- Fixed invisible desktop icon bug by utilizing native system icons.
