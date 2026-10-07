%global debug_package %{nil}
%global __strip /bin/true
%global __brp_mangle_shebangs /bin/true
%global __provides_exclude_from ^/opt/openclaw-cli/.*$
%global __requires_exclude_from ^/opt/openclaw-cli/.*$
%global _build_id_links none

Name:           openclaw-cli
Version:        %{_version}
Release:        %{_release}%{?dist}
Summary:        OpenClaw CLI, TUI and Gateway Engine
License:        Proprietary
URL:            https://openclaw.ai
ExclusiveArch:  x86_64

Source0:        openclaw-cli-%{version}-x86_64.tar.gz

%description
OpenClaw command-line interface, terminal UI, and local gateway daemon.

%prep
%autosetup -n openclaw-cli-%{version}-x86_64

%build

%install
rm -rf %{buildroot}

mkdir -p %{buildroot}/opt/openclaw-cli
cp -a app/* %{buildroot}/opt/openclaw-cli/

chmod -R a+rX %{buildroot}/opt/openclaw-cli
find %{buildroot}/opt/openclaw-cli -type f \( -name "openclaw" -o -name "node" \) -exec chmod +x {} + 2>/dev/null || true

mkdir -p %{buildroot}%{_bindir}

# Saf Komut Satırı Motoru (/usr/bin/openclaw-cli)
cat << 'EOF' > %{buildroot}%{_bindir}/openclaw-cli
#!/usr/bin/env bash
if [ -x "$HOME/.openclaw/bin/openclaw" ]; then
    exec "$HOME/.openclaw/bin/openclaw" "$@"
elif [ -x /opt/openclaw-cli/bin/openclaw ]; then
    exec /opt/openclaw-cli/bin/openclaw "$@"
elif [ -x /opt/openclaw-cli/openclaw ] && [ ! -d /opt/openclaw-cli/openclaw ]; then
    exec /opt/openclaw-cli/openclaw "$@"
else
    echo "Hata: OpenClaw CLI ikilisi bulunamadı." >&2
    exit 1
fi
EOF
chmod +x %{buildroot}%{_bindir}/openclaw-cli

# Terminal Sohbet Arayüzü (/usr/bin/openclaw-tui)
cat << 'EOF' > %{buildroot}%{_bindir}/openclaw-tui
#!/usr/bin/env bash
exec /usr/bin/openclaw-cli tui "$@"
EOF
chmod +x %{buildroot}%{_bindir}/openclaw-tui

# Varsayılan Akıllı Başlatıcı (/usr/bin/openclaw)
cat << 'EOF' > %{buildroot}%{_bindir}/openclaw
#!/usr/bin/env bash
if [ $# -gt 0 ]; then
    exec /usr/bin/openclaw-cli "$@"
elif command -v openclaw-desktop >/dev/null 2>&1 && [ -x /opt/openclaw-desktop/AppRun -o -x /opt/openclaw-desktop/OpenClaw ]; then
    exec openclaw-desktop "$@"
else
    exec /usr/bin/openclaw-cli dashboard "$@"
fi
EOF
chmod +x %{buildroot}%{_bindir}/openclaw

%files
/opt/openclaw-cli
%{_bindir}/openclaw
%{_bindir}/openclaw-cli
%{_bindir}/openclaw-tui

%changelog
* Wed Oct 07 2026 Saffet Yavuz <universish@tutamail.com> - %{version}-%{release}
- Isolated CLI and TUI motor build for dynamic release tracking.
