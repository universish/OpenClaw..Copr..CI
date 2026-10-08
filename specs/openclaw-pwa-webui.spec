%global debug_package %{nil}

Name:           openclaw-pwa-webui
Version:        %{_version}
Release:        %{_release}%{?dist}
Summary:        OpenClaw WebUI (Smart PWA Launcher)
License:        Proprietary
URL:            https://openclaw.ai
BuildArch:      noarch

Requires:       openclaw-cli
Requires:       pciutils
Requires:       xdg-utils

%description
Smart PWA wrapper for OpenClaw. Eliminates the Electron dependency by intercepting the dashboard token and launching the interface as a borderless app window in the user's default Chromium or Firefox browser, complete with dynamic Wayland and GPU flag injection.

%prep

%build

%install
rm -rf %{buildroot}
mkdir -p %{buildroot}%{_bindir}
mkdir -p %{buildroot}%{_libexecdir}
mkdir -p %{buildroot}%{_datadir}/applications
mkdir -p %{buildroot}%{_datadir}/icons/hicolor/512x512/apps

# Akıllı Tarayıcı Sarmalayıcısı
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

# Ana Başlatıcı
cat << 'EOF' > %{buildroot}%{_bindir}/openclaw-webui
#!/usr/bin/env bash
export BROWSER="/usr/libexec/openclaw-browser-wrapper"
exec openclaw-cli dashboard "$@"
EOF
chmod +x %{buildroot}%{_bindir}/openclaw-webui

# Masaüstü Kısayolu (.desktop)
cat << 'EOF' > %{buildroot}%{_datadir}/applications/openclaw-webui.desktop
[Desktop Entry]
Name=OpenClaw PWA
Comment=OpenClaw AI Assistant (Lightweight WebUI)
GenericName=AI Assistant
Exec=/usr/bin/openclaw-webui
Icon=openclaw
Type=Application
StartupNotify=true
StartupWMClass=openclaw-webui
Terminal=false
Categories=Utility;Network;Chat;
EOF

# İkon
echo "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=" | base64 -d > %{buildroot}%{_datadir}/icons/hicolor/512x512/apps/openclaw.png

%files
%{_bindir}/openclaw-webui
%{_libexecdir}/openclaw-browser-wrapper
%{_datadir}/applications/openclaw-webui.desktop
%{_datadir}/icons/hicolor/512x512/apps/openclaw.png

%changelog
* Thu Oct 08 2026 Saffet Yavuz <universish@tutamail.com> - %{version}-%{release}
- Introduced standalone PWA webui launcher.
