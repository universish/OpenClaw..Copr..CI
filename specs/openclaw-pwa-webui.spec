%global debug_package %{nil}

Name:           openclaw-pwa-webui
Version:        %{_version}
Release:        %{_release}%{?dist}
Summary:        OpenClaw WebUI (Smart PWA Launcher)
License:        Proprietary
URL:            https://openclaw.ai
BuildArch:      noarch

Source0:        openclaw.png

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
mkdir -p %{buildroot}%{_datadir}/pixmaps

# 1. AKILLI TARAYICI SARMALAYICISI (Browser Wrapper)
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

# Varsayılan tarayıcı kimliğini al
DEFAULT_BROWSER=$(xdg-settings get default-web-browser 2>/dev/null || xdg-mime query default x-scheme-handler/http 2>/dev/null)
DEFAULT_BROWSER=$(echo "$DEFAULT_BROWSER" | tr '[:upper:]' '[:lower:]')

# Tarayıcıyı tespit et ve PWA/App modunda çalıştır
if [[ "$DEFAULT_BROWSER" == *"helium"* ]]; then
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
elif [[ "$DEFAULT_BROWSER" == *"firefox"* ]] || [[ "$DEFAULT_BROWSER" == *"zen"* ]] || [[ "$DEFAULT_BROWSER" == *"librewolf"* ]]; then
    exec firefox --new-window "$URL"
else
    # Bilinmeyen tarayıcılar için genel çağrı
    exec xdg-open "$URL"
fi
EOF
chmod +x %{buildroot}%{_libexecdir}/openclaw-browser-wrapper

# 2. ANA BAŞLATICI (Aktif Port Kontrolü ile Yarış Durumunu Önler)
cat << 'EOF' > %{buildroot}%{_bindir}/openclaw-webui
#!/usr/bin/env bash

# Servis kapalıysa arka planda başlat
if ! systemctl --user is-active --quiet openclaw-gateway.service; then
    systemctl --user start openclaw-gateway.service
fi

# Port 18789 dinlemeye geçene kadar bekle (Maksimum 25 saniye, her 0.5 saniyede bir kontrol)
PORT_READY=false
for i in {1..50}; do
    if (exec 3<>/dev/tcp/127.0.0.1/18789) 2>/dev/null; then
        exec 3>&-
        PORT_READY=true
        break
    fi
    sleep 0.5
done

if [ "$PORT_READY" = false ]; then
    echo "Hata: OpenClaw Gateway servisi zaman aşımına uğradı." >&2
    exit 1
fi

export BROWSER="/usr/libexec/openclaw-browser-wrapper"
exec openclaw-cli dashboard "$@"
EOF
chmod +x %{buildroot}%{_bindir}/openclaw-webui

# 3. MASAÜSTÜ KISAYOLU (.desktop)
cat << 'EOF' > %{buildroot}%{_datadir}/applications/openclaw-webui.desktop
[Desktop Entry]
Name=OpenClaw WebUI
Comment=OpenClaw AI Assistant (PWA Mode)
GenericName=AI Assistant
Exec=/usr/bin/openclaw-webui
Icon=openclaw
Type=Application
StartupNotify=true
StartupWMClass=openclaw-webui
Terminal=false
Categories=Utility;Network;Chat;
EOF

# 4. RESMİ LOGO KURULUMU
install -m 0644 %{SOURCE0} %{buildroot}%{_datadir}/icons/hicolor/512x512/apps/openclaw.png
install -m 0644 %{SOURCE0} %{buildroot}%{_datadir}/pixmaps/openclaw.png

Source0:        openclaw.png

# ... (prep, build ve install bölümleri aynen kalıyor) ...

# Kurulum bittiğinde GNOME ikon önbelleğini anında tazele
%post
/bin/touch --no-create %{_datadir}/icons/hicolor &>/dev/null || :
if [ -x %{_bindir}/gtk-update-icon-cache ]; then
    %{_bindir}/gtk-update-icon-cache %{_datadir}/icons/hicolor &>/dev/null || :
fi
/usr/bin/update-desktop-database &>/dev/null || :

%postun
/bin/touch --no-create %{_datadir}/icons/hicolor &>/dev/null || :
if [ -x %{_bindir}/gtk-update-icon-cache ]; then
    %{_bindir}/gtk-update-icon-cache %{_datadir}/icons/hicolor &>/dev/null || :
fi
/usr/bin/update-desktop-database &>/dev/null || :

%files
%{_bindir}/openclaw-webui
%{_libexecdir}/openclaw-browser-wrapper
%{_datadir}/applications/openclaw-webui.desktop
%{_datadir}/icons/hicolor/512x512/apps/openclaw.png
%{_datadir}/pixmaps/openclaw.png

%changelog
* Thu Oct 08 2026 Saffet Yavuz <universish@tutamail.com> - %{version}-%{release}
- Replaced static sleep with dynamic socket probing on port 18789 to fix cold-start failure.
- Bundled official OpenClaw icon into RPM to fix browser icon caching.
- Enhanced browser wrapper for seamless PWA frame execution across Helium, Cromite, and Firefox.
