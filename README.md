# OpenClaw Copr Packaging CI (`OpenClaw..Copr..CI`)

Automated continuous integration pipeline to repackage upstream [OpenClaw](https://github.com/openclaw/openclaw) prebuilt `.deb` and `.AppImage` releases into native RPM packages for Fedora Linux, built and hosted on [Fedora Copr](https://copr.fedorainfracloud.org/coprs/universish/OpenClaw../).

## Packaging compliance

This package is distributed via COPR only. It rewraps the upstream prebuilt binary (`.deb` prioritized, `.AppImage` fallback), so it is **not eligible for the official Fedora repositories**: the Fedora Packaging Guidelines require all binaries to be built from source in the Fedora build system, and this repo intentionally ships the upstream prebuilt blob as-is (see `openclaw.spec`).

Everything else follows the guidelines:

- `ExclusiveArch: x86_64` — matches the tested upstream prebuilt Linux artifact.
- `%build` present (empty — nothing to compile) so rpm's build hooks run properly.
- `rpmlint` passes in CI with **0 errors, 0 warnings**: every flagged pattern is inherent to rewrapping the prebuilt Node/Electron blob (the `/opt` layout, required `$ORIGIN` runpaths, bare SONAMEs on private libraries, unstripped prebuilt binaries, GUI app without man page, docs not bundled by design) and is explicitly handled in `rpmlintrc`.
- Standard Fedora macros (`%{_bindir}`, `%{_datadir}`) are strictly used in `%files`.
- `%global debug_package %{nil}` with an explicit rationale: the prebuilt foreign binary cannot produce debuginfo, so debug packages are meaningless for a rewrap.
- The bundled libraries under `/opt/openclaw` carry bare SONAMEs. To prevent internal private libraries from leaking into the system package dependency graph, `%__provides_exclude_from` and `%__requires_exclude_from` strictly isolate `/opt/openclaw`.
- Minimal, documented transformations:
  - If a `.deb` package is provided upstream, payload contents are extracted directly from `data.tar.*` via `ar`.
  - If only `.AppImage` is published, squashfs layers are extracted directly without requiring runtime FUSE mounts.
  - The symlink `/usr/bin/openclaw -> /opt/openclaw/openclaw` is declared directly in `%install`, so RPM owns it natively without requiring unverified post-install scriptlets.
- Dependencies: explicitly lists runtime integration packages (`hicolor-icon-theme`, `xdg-utils`) that `rpmbuild`'s internal dependency generator cannot detect from prebuilt binary headers.

---

## Overview

[OpenClaw](https://openclaw.ai) is an all-in-one personal AI assistant and communication gateway. Upstream distributes its primary CLI via npm (which strictly enforces Node.js 24.16+/26.1+ LTS runtime gates and WAL-safe SQLite capabilities) and occasionally publishes pre-compiled Linux desktop artifacts as standalone `.deb` and `.AppImage` packages (`OpenClaw-<yyyy.mm.dd>-amd64`).

Building Node.js/Electron desktop applications directly from source inside isolated build environments like Fedora Mock or Copr is frequently hindered by offline network boundaries, Node.js version constraints, and complex pnpm workspace toolchains. This repository resolves that issue by implementing an automated **deb/AppImage-to-RPM repackaging pipeline**:

* Monitors upstream GitHub releases for prebuilt Linux distribution artifacts.
* **Smart Package Selection**: Prioritizes `.deb` packages when available due to cleaner filesystem payload extraction; seamlessly falls back to unpacking `.AppImage` bundles (without requiring FUSE).
* Bypasses source-only and npm-only tags to keep this repository strictly focused on binary repackaging rather than source compilation.
* Sanitizes and normalizes payloads into a standardized architecture-specific source tarball (`openclaw-<VERSION>-x86_64.tar.gz`).
* Generates a clean Source RPM (`.src.rpm`).
* Dispatches automated build tasks to the `universish/OpenClaw..` Copr repository across active Fedora chroots.

---

## Repository Structure

```text
.
├── .github/
│   └── workflows/
│       └── copr-ci.yml        # Automated release detector, extractor, and Copr trigger
├── openclaw.spec              # RPM packaging specification
├── latest-version.txt         # State tracker for the last processed upstream release
└── README.md

```

---

## Component Deep Dive

### 1. GitHub Actions Workflow (`.github/workflows/copr-ci.yml`)

The workflow runs on a scheduled cron trigger (every 6 hours) and supports manual triggering (`workflow_dispatch`) with an optional `force_version` input.

#### Operational Sequence:

1. **Upstream Release Resolution**: Queries the GitHub REST API for `openclaw/openclaw` releases, strips any leading `v` prefixes, and determines the latest release tag (e.g., `2026.9.5`).
2. **Prioritized Asset Detection**:
* **Primary Target (`.deb`)**: Searches for assets matching `OpenClaw-.*-amd64\.deb`. If found, selects this path as the preferred repackaging format.
* **Fallback Target (`.AppImage`)**: If no `.deb` is published, searches for `OpenClaw-.*-amd64\.AppImage`.
* **Source/NPM Bypass**: If neither prebuilt format exists, the workflow gracefully skips the run, ensuring no broken compilations are attempted.


3. **Payload Extraction & Normalization**:
* **For `.deb**`: Unpacks using `ar` and extracts the underlying `data.tar.*` archive directly.
* **For `.AppImage**`: Extracts the squashfs layer directly using `7z` / `unsquashfs`, eliminating runtime FUSE dependencies inside GitHub Actions runner containers.
* Identifies and standardizes application payloads into `/opt/openclaw`, alongside `.desktop` launcher shortcuts and high-resolution icons.


4. **Isolated SRPM Generation**: Compresses sanitized payloads into `openclaw-<VERSION>-x86_64.tar.gz` and runs `rpmbuild -bs` using `openclaw.spec` to output a clean, verifiable `.src.rpm`.
5. **Copr Dispatch (`copr-cli`)**: Injects credentials from the `COPR_CONFIG` secret into `~/.config/copr` and triggers non-blocking builds (`copr-cli build --nowait`) targeting the `universish/OpenClaw..` project chroots (e.g., `fedora-41-x86_64`, `fedora-42-x86_64`, `fedora-rawhide-x86_64`).

---

### 2. RPM Specification (`openclaw.spec`)

The RPM spec file handles binary payload placement, library conflict prevention, and desktop integration.

#### Key Architectural Highlights:

* **Binary Integrity Preservation**:
```spec
%global debug_package %{nil}
%global __strip /bin/true
%global _build_id_links none

```


Disables standard RPM build-root stripping and debuginfo extraction routines. Prebuilt Electron and Node ELF binaries contain internal symbols and bundled bindings that can fail or become corrupted if altered by standard stripping macros.
* **Dependency Isolation & Symbol Filtering**:
```spec
%global __provides_exclude_from ^/opt/%{name}/.*$
%global __requires_exclude_from ^/opt/%{name}/.*$

```


Prevents `rpmbuild`'s internal dependency generator from exposing internal bundled Node/Electron libraries as system-wide RPM provides or creating conflicting shared object requirements.
* **FHS Compliance & System Integration**:
* Installs the application payload into `/opt/openclaw/`.
* Creates a standard PATH symlink: `/usr/bin/openclaw -> /opt/openclaw/openclaw`.
* Installs and registers the desktop launcher under `/usr/share/applications/openclaw.desktop`.
* Places application icons into the standard hicolor icon theme directory (`/usr/share/icons/hicolor/512x512/apps/openclaw.png`).



---

## Configuration & Deployment

### 1. Copr Project Settings

Ensure the destination project exists on Fedora Copr:

* **Project URL**: [https://copr.fedorainfracloud.org/coprs/universish/OpenClaw../](https://copr.fedorainfracloud.org/coprs/universish/OpenClaw../)
* Navigate to **Settings -> Chroots** and enable the desired x86_64 targets (e.g., `fedora-41-x86_64`, `fedora-42-x86_64`, `fedora-rawhide-x86_64`).

---

## Installation Instructions (Client-Side)

To install OpenClaw on Fedora using the Copr repository:

```bash
# 1. Enable the Copr repository
sudo dnf copr enable universish/OpenClaw..

```
```bash
# 2. Install OpenClaw
sudo dnf install openclaw

```
```bash
# 3. Launch from terminal or application launcher
openclaw

```

> **Note**: Installing with superuser privileges (`sudo`) is at the user's discretion; no responsibility is accepted for local machine modifications.

---

## Feedback & Issues

This repository is an unofficial packaging pipeline intended to simplify installing and updating OpenClaw on Fedora.

* Please report any RPM packaging or Copr installation issues in our [Issue Tracker](https://www.google.com/search?q=https://github.com/universish/OpenClaw..Copr..CI/issues).
* For upstream application bugs, feature requests, or documentation, visit the official [OpenClaw Website](https://openclaw.ai) or the official [GitHub Repository](https://github.com/openclaw/openclaw).

---

## License

* Packaging scripts, GitHub Actions workflows, and spec files in this repository are licensed under the [MIT License](https://github.com/universish/OpenClaw..Copr..CI/blob/main/LICENSE).
* The underlying OpenClaw application and prebuilt binaries are governed by upstream OpenClaw licensing terms. OpenClaw repository are licensed under the [MIT LICENSE](https://github.com/openclaw/openclaw/blob/main/LICENSE)