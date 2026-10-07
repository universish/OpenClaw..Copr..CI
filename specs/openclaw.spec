%global debug_package %{nil}
%global __strip /bin/true
%global __brp_mangle_shebangs /bin/true
%global __provides_exclude_from ^/opt/%{name}/.*$
%global __requires_exclude_from ^/opt/%{name}/.*$
%global _build_id_links none

Name:           openclaw
Version:        %{_version}
Release:        %{?_release}%{!?_release:1}%{?dist}
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

%prep
%autosetup -n openclaw-%{version}-x86_64

%build

%install
rm -rf %{buildroot}

mkdir -p %{buildroot}/opt/%{name}
cp -a app/* %{buildroot}/opt/%{name}/

chmod -R a+rX %{buildroot}/opt/%{name}
find %{buildroot}/opt/%{name} -type f \( -name "AppRun*" -o -name "*openclaw*" -o -name "*OpenClaw*" \) -exec chmod +x {} + 2>/dev/null || true

mkdir -p %{buildroot}%{_bindir}

# 1. Masaüstü GUI Başlatıcısı (AppRun varsa Electron GUI, yoksa Web Dashboard açar)
cat << 'EOF' > %{buildroot}%{_bindir}/%{name}-desktop
#!/usr/bin/env bash
if [ -x /opt/openclaw/AppRun ]; then
    exec /opt/openclaw/AppRun "$@"
elif [ -x "$HOME/.openclaw/bin/openclaw" ]; then
    exec "$HOME/.openclaw/bin/openclaw" dashboard "$@"
elif [ -x /opt/openclaw/bin/openclaw ]; then
    exec /opt/openclaw/bin/openclaw dashboard "$@"
else
    xdg-open "http://127.0.0.1:18789/" 2>/dev/null || true
fi
EOF
chmod +x %{buildroot}%{_bindir}/%{name}-desktop

# 2. Terminal CLI Başlatıcısı
cat << 'EOF' > %{buildroot}%{_bindir}/%{name}
#!/usr/bin/env bash
if [ -x "$HOME/.openclaw/bin/openclaw" ]; then
    exec "$HOME/.openclaw/bin/openclaw" "$@"
elif [ -x /opt/openclaw/bin/openclaw ]; then
    exec /opt/openclaw/bin/openclaw "$@"
elif [ -x /opt/openclaw/AppRun ]; then
    exec /opt/openclaw/AppRun "$@"
fi
EOF
chmod +x %{buildroot}%{_bindir}/%{name}

# Masaüstü Kısayolu
mkdir -p %{buildroot}%{_datadir}/applications
cat << 'EOF' > %{buildroot}%{_datadir}/applications/%{name}.desktop
[Desktop Entry]
Name=OpenClaw
Comment=All your chats, one OpenClaw - AI Assistant and Gateway
GenericName=AI Assistant
Exec=/usr/bin/openclaw-desktop
Icon=openclaw
Type=Application
StartupNotify=true
StartupWMClass=OpenClaw
Terminal=false
Categories=Utility;Network;Chat;
EOF

# Uygulama simgesi
mkdir -p %{buildroot}%{_datadir}/icons/hicolor/512x512/apps
if [ -f %{buildroot}/opt/%{name}/openclaw.png ]; then
    install -m 0644 %{buildroot}/opt/%{name}/openclaw.png %{buildroot}%{_datadir}/icons/hicolor/512x512/apps/%{name}.png
fi

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/%{name}.desktop

%files
/opt/%{name}
%{_bindir}/%{name}
%{_bindir}/%{name}-desktop
%{_datadir}/applications/%{name}.desktop
%{_datadir}/icons/hicolor/512x512/apps/%{name}.png

%changelog
* Wed Oct 07 2026 Saffet Yavuz <universish@tutamail.com> - %{version}-%{release}
- Automated packaging with dynamic release counter.
