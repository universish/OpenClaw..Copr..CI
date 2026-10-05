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

# Yalnızca tek kaynak (tarball) yeterlidir; desktop içeriği aşağıda üretilir
Source0:        openclaw-%{version}-x86_64.tar.gz

BuildRequires:  desktop-file-utils

Requires:       nodejs >= 1:24.16.0
Requires:       hicolor-icon-theme
Requires:       xdg-utils

%description
OpenClaw is a personal AI assistant and communication gateway.
This package repackages the upstream prebuilt distribution into a native Fedora RPM.

%prep
%autosetup -n openclaw-%{version}-x86_64

%build
# Prebuilt binary / npm bundle - derleme adımı gerekmez.

%install
rm -rf %{buildroot}

# Uygulama ana dizini (/opt/openclaw)
mkdir -p %{buildroot}/opt/%{name}
cp -a app/* %{buildroot}/opt/%{name}/

# Çalıştırılabilir ikili dosya ve sembolik bağ
mkdir -p %{buildroot}%{_bindir}
if [ -f %{buildroot}/opt/%{name}/bin/%{name} ]; then
    chmod +x %{buildroot}/opt/%{name}/bin/%{name}
    ln -sf /opt/%{name}/bin/%{name} %{buildroot}%{_bindir}/%{name}
else
    chmod +x %{buildroot}/opt/%{name}/%{name} 2>/dev/null || true
    ln -sf /opt/%{name}/%{name} %{buildroot}%{_bindir}/%{name}
fi

# Desktop dosyası kurulumu
mkdir -p %{buildroot}%{_datadir}/applications

DESKTOP_SRC=""
if [ -f app/%{name}.desktop ]; then
    DESKTOP_SRC="app/%{name}.desktop"
elif [ -f app/OpenClaw.desktop ]; then
    DESKTOP_SRC="app/OpenClaw.desktop"
fi

if [ -n "$DESKTOP_SRC" ]; then
    # Upstream dosyasını kur ve Exec satırına Wayland/NVIDIA bayraklarını yerleştir
    install -m 0644 "$DESKTOP_SRC" %{buildroot}%{_datadir}/applications/%{name}.desktop
    sed -i 's|^Exec=.*|Exec=/usr/bin/openclaw --ozone-platform-hint=auto --disable-features=Vulkan --enable-features=WaylandWindowDecorations %U|' \
        %{buildroot}%{_datadir}/applications/%{name}.desktop
else
    # Dosya yoksa (örneğin npm paketinde) sıfırdan oluştur
    cat << 'EOF' > %{buildroot}%{_datadir}/applications/%{name}.desktop
[Desktop Entry]
Name=OpenClaw
Comment=All your chats, one OpenClaw - AI Assistant and Gateway
GenericName=AI Assistant
Exec=/usr/bin/openclaw --ozone-platform-hint=auto --disable-features=Vulkan --enable-features=WaylandWindowDecorations %U
Icon=openclaw
Type=Application
StartupNotify=true
StartupWMClass=openclaw
Terminal=false
Categories=Utility;Network;Chat;
MimeType=x-scheme-handler/openclaw;
EOF
fi

# Uygulama simgesi (Icon)
mkdir -p %{buildroot}%{_datadir}/icons/hicolor/512x512/apps
if [ -f app/%{name}.png ]; then
    install -m 0644 app/%{name}.png %{buildroot}%{_datadir}/icons/hicolor/512x512/apps/%{name}.png
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
