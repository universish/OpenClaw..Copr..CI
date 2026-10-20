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
Requires:       hicolor-icon-theme

%description
Smart PWA wrapper for OpenClaw. Eliminates the Electron dependency by intercepting the dashboard token and launching the interface as a standalone borderless PWA window in the user's browser, complete with dynamic Wayland and GPU flag injection.

%prep

%build

%install
rm -rf %{buildroot}
mkdir -p %{buildroot}%{_bindir}
mkdir -p %{buildroot}%{_libexecdir}
mkdir -p %{buildroot}%{_datadir}/applications
mkdir -p %{buildroot}%{_datadir}/icons/hicolor/512x512/apps
mkdir -p %{buildroot}%{_datadir}/pixmaps

# 1. AKILLI TARAYICI SARMALAYICISI (İzole PWA Modu Başlatıcısı)
cat << 'EOF' > %{buildroot}%{_libexecdir}/openclaw-browser-wrapper
#!/usr/bin/env bash
URL="$1"
[ -z "$URL" ] && URL="http://127.0.0.1:18789"

PWA_PROFILE_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/openclaw-pwa-profile"
mkdir -p "$PWA_PROFILE_DIR"

# GPU Tespiti ve İzole PWA Chromium Bayrakları
# --user-data-dir sayesinde açık olan normal tarayıcı penceresine sekme olarak eklenmez,
# her zaman bağımsız, çerçevesiz (borderless) bir PWA uygulaması olarak açılır.
CHROMIUM_FLAGS="--ozone-platform-hint=auto --user-data-dir=$PWA_PROFILE_DIR --class=OpenClawPWA --no-first-run --no-default-browser-check"

if lspci -k 2>/dev/null | grep -iA 2 "VGA" | grep -i "nvidia" > /dev/null; then
    CHROMIUM_FLAGS="$CHROMIUM_FLAGS --disable-features=Vulkan"
else
    CHROMIUM_FLAGS="$CHROMIUM_FLAGS --enable-features=Vulkan"
fi

export MOZ_ENABLE_WAYLAND=1

find_browser_bin() {
    for bin in "$@"; do
        if command -v "$bin" >/dev/null 2>&1; then
            echo "$bin"
            return 0
        fi
    done
    return 1
}

launch_firefox_pwa() {
    local ff_bin="$1"
    local ff_profile="$PWA_PROFILE_DIR/firefox-pwa"
    mkdir -p "$ff_profile/chrome"

    # Firefox/Zen/LibreWolf için adres çubuğu ve sekmeleri gizleyen PWA yapılandırması
    cat << 'USERJS' > "$ff_profile/user.js"
user_pref("toolkit.legacyUserProfileCustomizations.stylesheets", true);
user_pref("browser.tabs.warnOnClose", false);
user_pref("browser.shell.checkDefaultBrowser", false);
USERJS

    cat << 'CSS' > "$ff_profile/chrome/userChrome.css"
#TabsToolbar, #nav-bar, #PersonalToolbar, #sidebar-box, #sidebar-splitter {
    visibility: collapse !important;
}
CSS

    exec "$ff_bin" --profile "$ff_profile" --no-remote --class "OpenClawPWA" --new-window "$URL"
}

DEFAULT_BROWSER=$(xdg-settings get default-web-browser 2>/dev/null || xdg-mime query default x-scheme-handler/http 2>/dev/null)
DEFAULT_BROWSER=$(echo "$DEFAULT_BROWSER" | tr '[:upper:]' '[:lower:]')

# 1. Varsayılan tarayıcıya göre PWA başlat
if [[ "$DEFAULT_BROWSER" == *"helium"* ]] && BIN=$(find_browser_bin helium helium-browser); then
    exec "$BIN" --app="$URL" $CHROMIUM_FLAGS
elif [[ "$DEFAULT_BROWSER" == *"cromite"* ]] && BIN=$(find_browser_bin cromite cromite-browser); then
    exec "$BIN" --app="$URL" $CHROMIUM_FLAGS
elif [[ "$DEFAULT_BROWSER" == *"thorium"* ]] && BIN=$(find_browser_bin thorium-browser thorium); then
    exec "$BIN" --app="$URL" $CHROMIUM_FLAGS
elif [[ "$DEFAULT_BROWSER" == *"brave"* ]] && BIN=$(find_browser_bin brave-browser brave); then
    exec "$BIN" --app="$URL" $CHROMIUM_FLAGS
elif [[ "$DEFAULT_BROWSER" == *"chrome"* ]] && BIN=$(find_browser_bin google-chrome google-chrome-stable); then
    exec "$BIN" --app="$URL" $CHROMIUM_FLAGS
elif [[ "$DEFAULT_BROWSER" == *"chromium"* ]] && BIN=$(find_browser_bin chromium-browser chromium); then
    exec "$BIN" --app="$URL" $CHROMIUM_FLAGS
elif [[ "$DEFAULT_BROWSER" == *"edge"* ]] && BIN=$(find_browser_bin microsoft-edge microsoft-edge-stable); then
    exec "$BIN" --app="$URL" $CHROMIUM_FLAGS
elif [[ "$DEFAULT_BROWSER" == *"vivaldi"* ]] && BIN=$(find_browser_bin vivaldi vivaldi-stable); then
    exec "$BIN" --app="$URL" $CHROMIUM_FLAGS
fi

# 2. Varsayılan tarayıcı Chromium tabanlı değilse bile sistemde yüklü bir Chromium tabanlı tarayıcı varsa yerel --app modu için onu tercih et
if BIN=$(find_browser_bin helium helium-browser cromite thorium-browser thorium brave-browser brave chromium-browser chromium google-chrome google-chrome-stable microsoft-edge vivaldi); then
    exec "$BIN" --app="$URL" $CHROMIUM_FLAGS
fi

# 3. Yalnızca Firefox / Zen / LibreWolf yüklüyse özel userChrome.css PWA profiliyle başlat
if BIN=$(find_browser_bin zen zen-browser librewolf firefox); then
    launch_firefox_pwa "$BIN"
fi

exec xdg-open "$URL"
EOF
chmod +x %{buildroot}%{_libexecdir}/openclaw-browser-wrapper

# 2. ANA BAŞLATICI (Gateway Tetikleyici ve Doğrudan Token/URL Yakalayıcı)
cat << 'EOF' > %{buildroot}%{_bindir}/openclaw-webui
#!/usr/bin/env bash

if systemctl --user list-unit-files openclaw-gateway.service &>/dev/null; then
    if ! systemctl --user is-active --quiet openclaw-gateway.service; then
        systemctl --user start openclaw-gateway.service 2>/dev/null || true
    fi
fi

PORT_READY=false
for i in {1..15}; do
    if (exec 3<>/dev/tcp/127.0.0.1/18789) 2>/dev/null; then
        exec 3>&-
        PORT_READY=true
        break
    fi
    sleep 0.3
done

if [ "$PORT_READY" = false ]; then
    nohup openclaw-cli gateway start >/dev/null 2>&1 &
    for i in {1..35}; do
        if (exec 3<>/dev/tcp/127.0.0.1/18789) 2>/dev/null; then
            exec 3>&-
            PORT_READY=true
            break
        fi
        sleep 0.5
    done
fi

if [ "$PORT_READY" = false ]; then
    echo "Hata: OpenClaw Gateway servisi zaman aşımına uğradı." >&2
    exit 1
fi

# openclaw-cli dashboard komutunun xdg-open çağrısını devre dışı bırakıp URL'yi doğrudan yakala
URL_FILE=$(mktemp /tmp/openclaw-pwa-url.XXXXXX)
CAPTURE_SCRIPT=$(mktemp /tmp/openclaw-pwa-cap.XXXXXX)

cat << CAPEOF > "$CAPTURE_SCRIPT"
#!/usr/bin/env bash
for arg in "\$@"; do
    if [[ "\$arg" =~ ^https?:// ]]; then
        echo "\$arg" > "$URL_FILE"
        exit 0
    fi
done
CAPEOF
chmod +x "$CAPTURE_SCRIPT"

CLI_OUT=$(BROWSER="$CAPTURE_SCRIPT" openclaw-cli dashboard --no-open "$@" 2>&1 || BROWSER="$CAPTURE_SCRIPT" openclaw-cli dashboard "$@" 2>&1 || true)

TARGET_URL=$(cat "$URL_FILE" 2>/dev/null | head -n 1)
if [ -z "$TARGET_URL" ]; then
    TARGET_URL=$(echo "$CLI_OUT" | grep -Eo 'https?://(127\.0\.0\.1|localhost):[0-9]+[^[:space:]"'"'"']*' | head -n 1)
fi
rm -f "$URL_FILE" "$CAPTURE_SCRIPT"

if [ -z "$TARGET_URL" ]; then
    TARGET_URL="http://127.0.0.1:18789"
fi

exec %{_libexecdir}/openclaw-browser-wrapper "$TARGET_URL"
EOF
chmod +x %{buildroot}%{_bindir}/openclaw-webui

# 3. MASAÜSTÜ KISAYOLU (.desktop)
# Not: İkon adı çakışmayı önlemek için openclaw-webui olarak ayrılmıştır.
cat << 'EOF' > %{buildroot}%{_datadir}/applications/openclaw-webui.desktop
[Desktop Entry]
Name=OpenClaw WebUI
Comment=OpenClaw AI Assistant (PWA Mode)
GenericName=AI Assistant
Exec=/usr/bin/openclaw-webui
Icon=openclaw-webui
Type=Application
StartupNotify=true
StartupWMClass=OpenClawPWA
Terminal=false
Categories=Utility;Network;Chat;
EOF

# 4. İKON DOSYALARI (openclaw-desktop ile çakışmaması için openclaw-webui.png adıyla kurulur)
install -m 0644 %{SOURCE0} %{buildroot}%{_datadir}/icons/hicolor/512x512/apps/openclaw-webui.png
install -m 0644 %{SOURCE0} %{buildroot}%{_datadir}/pixmaps/openclaw-webui.png

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
%dir %{_datadir}/icons/hicolor
%dir %{_datadir}/icons/hicolor/512x512
%dir %{_datadir}/icons/hicolor/512x512/apps
%{_datadir}/icons/hicolor/512x512/apps/openclaw-webui.png
%{_datadir}/pixmaps/openclaw-webui.png

%changelog
* Tue Oct 20 2026 Saffet Yavuz <universish@tutamail.com> - %{version}-%{release}
- Resolved icon file collision with openclaw-desktop by renaming PWA icon to openclaw-webui.png.
- Added isolated user-data-dir and URL interception so clicking the shortcut always opens a standalone PWA window.
