%global debug_package %{nil}

Name:           openclaw
Version:        %{_version}
Release:        %{_release}%{?dist}
Summary:        All your chats, one OpenClaw - AI Assistant and Gateway
License:        Proprietary
URL:            https://openclaw.ai
BuildArch:      noarch

Requires:       openclaw-desktop
Requires:       openclaw-cli

%description
Meta-package that automatically installs both the OpenClaw Desktop GUI client and the background CLI/TUI Gateway.

%prep

%build

%install
mkdir -p %{buildroot}%{_datadir}/openclaw-meta
echo "OpenClaw Meta Package - universish" > %{buildroot}%{_datadir}/openclaw-meta/info.txt

%files
%{_datadir}/openclaw-meta/info.txt

%changelog
* Wed Oct 07 2026 Saffet Yavuz <universish@tutamail.com> - %{version}-%{release}
- Meta-package router for desktop and cli separation.
