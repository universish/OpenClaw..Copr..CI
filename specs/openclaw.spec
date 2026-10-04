%global debug_package %{nil}
%global __strip /bin/true
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
Source1:        com.openclaw.openclaw.metainfo.xml

Requires:       hicolor-icon-theme
Requires:       xdg-utils

%description
OpenClaw is a personal AI assistant and communication gateway.
This package repackages the upstream prebuilt Linux distribution for Fedora.

%prep
%autosetup -n openclaw-%{version}-x86_64

%build
# Prebuilt binary - derleme adımı gerekmez.

%install
rm -rf %{buildroot}
mkdir -p %{buildroot}%{_metainfodir}
install -m 0644 %{SOURCE1} %{buildroot}%{_metainfodir}/com.openclaw.openclaw.metainfo.xml

%check
appstream-util validate-relax --nonet %{buildroot}%{_metainfodir}/com.openclaw.openclaw.metainfo.xml

# Uygulama ana dizini (/opt/openclaw)
mkdir -p %{buildroot}/opt/%{name}
cp -a app/* %{buildroot}/opt/%{name}/
chmod +x %{buildroot}/opt/%{name}/openclaw 2>/dev/null || true

# /usr/bin sembolik bağlayıcı
mkdir -p %{buildroot}%{_bindir}
ln -sf /opt/%{name}/openclaw %{buildroot}%{_bindir}/%{name}

# Desktop dosyası
mkdir -p %{buildroot}%{_datadir}/applications
if [ -f app/%{name}.desktop ]; then
    install -m 0644 app/%{name}.desktop %{buildroot}%{_datadir}/applications/%{name}.desktop
elif [ -f app/OpenClaw.desktop ]; then
    install -m 0644 app/OpenClaw.desktop %{buildroot}%{_datadir}/applications/%{name}.desktop
else
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
elif [ -f app/OpenClaw.png ]; then
    install -m 0644 app/OpenClaw.png %{buildroot}%{_datadir}/icons/hicolor/512x512/apps/%{name}.png
fi

%files
/opt/%{name}
%{_bindir}/%{name}
%{_datadir}/applications/%{name}.desktop
%{_datadir}/icons/hicolor/512x512/apps/%{name}.png
%{_metainfodir}/com.openclaw.openclaw.metainfo.xml

%changelog
* Sun Oct 04 2026 Saffet Yavuz <universish> - %{version}-1
- Automatic rewrap from upstream prebuilt binary.