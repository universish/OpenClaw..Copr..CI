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
Source1:        com.openclaw.openclaw.metainfo.xml
Source2:        openclaw.desktop

BuildRequires:  desktop-file-utils
BuildRequires:  libappstream-glib

# npm demeti sistem Node.js çalışma ortamını kullanır
Requires:       nodejs >= 1:24.16.0
Requires:       hicolor-icon-theme
Requires:       xdg-utils

%description
OpenClaw is a personal AI assistant and communication gateway.
This package repackages the upstream distribution (deb, AppImage, or npm bundle)
into a native Fedora RPM.

%prep
%autosetup -n openclaw-%{version}-x86_64

%build
# Önceden paketlenmiş demet (Prebuilt / npm bundle) - derleme adımı gerekmez.

%install
rm -rf %{buildroot}

# Uygulama ana dizini (/opt/openclaw)
mkdir -p %{buildroot}/opt/%{name}
cp -a app/* %{buildroot}/opt/%{name}/

# Çalıştırılabilir ikili dosya ve symlink yapılandırması
mkdir -p %{buildroot}%{_bindir}
if [ -f %{buildroot}/opt/%{name}/bin/%{name} ]; then
    chmod +x %{buildroot}/opt/%{name}/bin/%{name}
    ln -sf /opt/%{name}/bin/%{name} %{buildroot}%{_bindir}/%{name}
else
    chmod +x %{buildroot}/opt/%{name}/%{name} 2>/dev/null || true
    ln -sf /opt/%{name}/%{name} %{buildroot}%{_bindir}/%{name}
fi

# Desktop dosyası kurulumu
desktop-file-install \
    --dir=%{buildroot}%{_datadir}/applications \
    %{SOURCE2}

# AppStream Metainfo kurulumu
mkdir -p %{buildroot}%{_metainfodir}
install -m 0644 %{SOURCE1} %{buildroot}%{_metainfodir}/com.openclaw.openclaw.metainfo.xml

# Uygulama simgesi (Icon) 
mkdir -p %{buildroot}%{_datadir}/icons/hicolor/512x512/apps
if [ -f app/%{name}.png ]; then
    install -m 0644 app/%{name}.png %{buildroot}%{_datadir}/icons/hicolor/512x512/apps/%{name}.png
fi

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/%{name}.desktop
appstream-util validate-relax --nonet %{buildroot}%{_metainfodir}/com.openclaw.openclaw.metainfo.xml

%files
/opt/%{name}
%{_bindir}/%{name}
%{_datadir}/applications/%{name}.desktop
%{_metainfodir}/com.openclaw.openclaw.metainfo.xml
%{_datadir}/icons/hicolor/512x512/apps/%{name}.png

%changelog
* Sun Oct 04 2026 Saffet Yavuz <universish> - %{version}-1
- Automatic packaging from upstream deb, AppImage, or npm bundle.
