<div align="center">
  <table>
    <tr>
      <td align="center" valign="middle">
        <img width="256" height="256" alt="256" src="https://github.com/user-attachments/assets/f3c9cefb-50a0-4b5b-bcde-1d86338f8098" />
      </td>
      <td align="center" valign="middle">
        <img width="256" height="256" src="https://upload.wikimedia.org/wikipedia/commons/4/41/Fedora_icon_%282021%29.svg" alt="Fedora Logo" width="110"/>
      </td>
    </tr>
  </table>

  <h1>OpenClaw Copr Packaging CI</h1>
  <p>
    <a href="https://copr.fedorainfracloud.org/coprs/universish/OpenClaw../"><img src="https://img.shields.io/badge/Copr-universish%2FOpenClaw..-blue?logo=fedora&style=for-the-badge" alt="Copr Build"></a>
    <img src="https://img.shields.io/badge/Platform-Fedora_Linux-51A2DA?logo=fedora&style=for-the-badge" alt="Platform">
    <img src="https://img.shields.io/badge/Arch-x86__64-brightgreen?style=for-the-badge" alt="Arch">
    <a href="https://github.com/universish/OpenClaw..Copr..CI/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge" alt="License"></a>
  </p>
  <p><em>Automated enterprise-grade continuous integration pipeline for native RPM packaging.</em></p>
</div>

<hr>

## 🚀 Overview

[OpenClaw](https://openclaw.ai) is an all-in-one personal AI assistant and communication gateway. Upstream distributes its primary CLI via npm (which strictly enforces Node.js 24.16+/26.1+ LTS runtime gates and WAL-safe SQLite capabilities) and occasionally publishes pre-compiled Linux desktop artifacts as standalone `.deb` and `.AppImage` packages (`OpenClaw-<<year>.XX.YY>-amd64`).

Building Node.js/Electron desktop applications directly from source inside isolated build environments like Fedora Mock or Copr is frequently hindered by offline network boundaries, Node.js version constraints, and complex `pnpm` workspace toolchains. 

This repository resolves that issue by implementing an automated **Deb/AppImage/NPM-to-RPM repackaging pipeline** that monitors upstream GitHub releases, bypasses source-only tags, prioritizes the correct binary artifacts, and dispatches automated build tasks to the `universish/OpenClaw..` Copr repository across active Fedora chroots.

---

<img width="1892" height="564" alt="openclaw-dashboard-icon" src="https://github.com/user-attachments/assets/68084df1-5f61-483e-a1be-76f51e079fe3" />


<div align="center">
  <table>
    <tr>
      <td align="left" valign="middle">
<pre style="color: #FF8C00; font-weight: bold; background: transparent; border: none; font-family: monospace; line-height: 1.2;">
 •●●:.        .:●●•
:●●●●:        :●●●●:
.●●●●:.:•●●•:.:●●●●.
 .●●●: •●●●●• :●●●. 
 ..:••●●●●●●●●••:.. 
.::••••●●●●●●••••::.
 . .:  •●●●●•  :. .
    .  :●●●●:  .
      .●●●●●●.
       :••••:
</pre>
      </td>
      <td align="right" valign="middle">
        <img width="214" height="214" alt="openclaw" src="https://github.com/user-attachments/assets/5568213e-a1b2-416f-99e7-ea6a2266871b" />
      </td>
    </tr>
  </table>
</div>

---

## 🏗️ Decoupled Architecture

OpenClaw operates with a split client-server model: a background Node.js gateway/CLI and an Electron-based desktop GUI. Because upstream publishes these components at different cadences, this repository implements a **Multi-Package Architecture** to prevent RPM file conflicts and ensure granular updates:

*   📦 **`openclaw-desktop`**: Contains only the Electron GUI. Tracks upstream `.AppImage` or `.deb` releases. Installed isolated into `/opt/openclaw-desktop`.
*   📦 **`openclaw-cli`**: Contains the core gateway daemon, TUI, and CLI commands. Tracks upstream `npm` or `tarball` releases. Installed isolated into `/opt/openclaw-cli`.
*   📦 **`openclaw`**: A structural meta-package that requires both of the above, providing a seamless "install everything" experience.

Intelligent bash wrappers (`/usr/bin/openclaw`, `/usr/bin/openclaw-desktop`, `/usr/bin/openclaw-cli`) handle routing, ensuring users are dropped into the desktop app if available, or the TUI/CLI fallback if operating in a headless environment.

---

## 🛡️ Packaging Compliance

This package is distributed via COPR only. It rewraps the upstream prebuilt binaries, so it is **not eligible for the official Fedora repositories**: the Fedora Packaging Guidelines require all binaries to be built from source in the Fedora build system, and this repo intentionally ships the upstream prebuilt blob as-is.

Everything else follows the guidelines stringently:

*   **`ExclusiveArch: x86_64`** — Matches the tested upstream prebuilt Linux artifact.
*   **Zero-Warning Policy** — `rpmlint` passes in CI with **0 errors, 0 warnings**. Every flagged pattern inherent to rewrapping a prebuilt Node/Electron blob (the `/opt` layout, required `$ORIGIN` runpaths, bare SONAMEs on private libraries, unstripped binaries, missing man pages) is explicitly handled in `rpmlintrc.txt`.
*   **Debuginfo Suppression** — `%global debug_package %{nil}` is defined with an explicit rationale: the prebuilt foreign binary cannot produce debuginfo, and attempting to strip it corrupts Electron/Node bindings.
*   **Dependency Isolation** — The bundled libraries under `/opt/openclaw-*` carry bare SONAMEs. To prevent these from leaking into the system package dependency graph, `%__provides_exclude_from` and `%__requires_exclude_from` strictly isolate these directories.
*   **Minimal, Documented Transformations**:
    *   If a `.deb` package is provided upstream, payload contents are extracted directly from `data.tar.*` via `ar`.
    *   If an `.AppImage` is targeted, the squashfs layer is extracted via `--appimage-extract`, eliminating runtime FUSE mount dependencies during CI builds.
*   **Native Integration** — Symlinks (`/usr/bin/openclaw`) and desktop integrations (hicolor icons, `.desktop` files) are declared directly in `%install`, so RPM owns them natively without requiring unverified post-install scriptlets.
*   **System Dependencies** — Explicitly lists runtime integration packages (`hicolor-icon-theme`, `xdg-utils`) that `rpmbuild`'s internal dependency generator cannot detect from prebuilt binary headers.

---

## 📂 Repository Structure

```text
.
├── .github/
│   └── workflows/
│       └── copr_ci.yml                        # Release detector and Copr build trigger
├── sources/
│   └── com.openclaw.openclaw.metainfo.xml
├── specs/
│   ├── openclaw-cli.spec                      # RPM spec for the TUI, CLI, and Gateway daemon
│   ├── openclaw-desktop.spec                  # RPM spec for the Electron GUI client
│   ├── openclaw-pwa-webui.spec                # RPM spec for the PWA WebUI client
│   ├── openclaw.spec                         # RPM meta-package router
│   └── rpmlintrc                              # Audit suppression for prebuilt blob constraints
├── icon/
│   └── 32.png, 48.png, 64.png, 96.png, 128.png, 180.png, 256.png from PWA's "Icons" file
└── README.md

```

---

## ⚙️ Configuration & Deployment

Ensure the destination project exists on Fedora Copr:

* **Project URL**: [https://copr.fedorainfracloud.org/coprs/universish/OpenClaw../](https://copr.fedorainfracloud.org/coprs/universish/OpenClaw../)
* Navigate to **Settings -> Chroots** and enable the desired x86_64 targets (e.g., `fedora-41-x86_64`, `fedora-42-x86_64`, `fedora-rawhide-x86_64`).

---

## 🧩 The Quad-Package Architecture (Modular Design)

To accommodate different hardware capabilities and user preferences without forcing unnecessary dependencies, this repository splits the upstream OpenClaw monolithic experience into a highly modular **4-Package Architecture**. 

You can mix and match these components based on your environment:

*   📦 **`openclaw-desktop`** (`openclaw-desktop.spec`): The thick, standard Electron GUI client. It packages the upstream `.deb` or `.AppImage` releases into a native RPM. Best for users who want the traditional, isolated application experience.
*   📦 **`openclaw-cli`** (`openclaw-cli.spec`): The core backbone. It provides the headless background Gateway daemon, the interactive Terminal UI (TUI), and command-line management tools. It is completely decoupled from any graphical dependencies.
*   📦 **`openclaw-pwa-webui`** (`openclaw-pwa-webui.spec`): A custom, zero-overhead Smart PWA Launcher. It acts as a lightweight alternative to the thick Electron client (details below).
*   📦 **`openclaw`** (`openclaw.spec`): The meta-package. Running `sudo dnf install openclaw` will automatically pull in the upstream-standard combination (`openclaw-desktop` + `openclaw-cli`) for a complete, out-of-the-box experience.

---

## ⚡ The Smart PWA Launcher (`openclaw-pwa-webui`)

Electron-based desktop applications bundle their own entire Chromium rendering engine, which can lead to high memory consumption, redundant resource usage, and specific hardware acceleration bugs (such as Skia font rendering crashes on Linux or NVIDIA/Wayland lockups). 

To solve this, we engineered the **`openclaw-pwa-webui`** package.

### Why We Created It & User Benefits
Instead of shipping a heavy Electron wrapper, this package relies on the browser you already have installed (e.g., Firefox, Chromium, Thorium, Cromite). 
*   **Zero RAM Overhead:** It uses your existing browser's memory pool and cache.
*   **Dynamic GPU Flag Injection:** Every time you launch it, a bash wrapper (`openclaw-browser-wrapper`) queries your system's PCI bus (`lspci`). If it detects an NVIDIA GPU, it automatically disables Vulkan to prevent Wayland white-screen crashes. If it detects AMD or Intel, it enables full Vulkan hardware acceleration.
*   **Seamless Interception:** It intercepts the `openclaw dashboard` command, generates the secure authentication token from the background daemon, and opens the WebUI in "App Mode" (`--app=URL`). 
*   **Native Feel:** The interface opens in a dedicated, borderless window without an address bar or browser tabs, feeling exactly like a native desktop app.

---

## 📦 Installation & Setup

**1. Enable the Copr Repository**
Register the official Copr repository with your DNF package manager:

```bash
sudo dnf copr enable universish/OpenClaw..

```

**2. Choose Your Installation Method**
Thanks to the modular architecture, you can install the complete suite or strictly the components you need for your environment.

* **Full Installation (Desktop GUI + CLI/TUI & Gateway Engine):**
```bash
sudo dnf install openclaw

```

* **CLI / TUI Only (Headless, Terminal, or Server usage):**
```bash
sudo dnf install openclaw-cli

```

* **Desktop GUI Only (Connects to an existing local or remote gateway):**
```bash
sudo dnf install openclaw-desktop

```
*(Note: The `openclaw-desktop` package depends on the `openclaw-cli` package.)*

* **🛠️ Managing the PWA Experience and Installation:**
If you want to ditch the Electron app and use the lightweight PWA launcher instead, install the WebUI and the CLI daemon:
```bash
sudo dnf install openclaw-pwa-webui openclaw-cli

```

*(Note: If you previously installed `openclaw-desktop`, you can safely remove it with `sudo dnf remove openclaw-desktop` before running this).*

---

## ⚙️ Background Service Management (Gateway)

The OpenClaw CLI operates a background gateway daemon to coordinate AI and chat functions. You can manage this background service directly via the CLI:

+ Start the background gateway daemon:
```
openclaw gateway start

```

+ Stop the running daemon:
```
openclaw gateway stop

```

+ Restart the daemon:
```
openclaw gateway restart

```

+ Check the real-time status and port health:
```
openclaw gateway status

```

---

## 🔄 Updates & Maintenance

### **Refresh Repository Cache and Upgrade All System Packages:**

```
sudo dnf upgrade --refresh

```

### **Upgrade Only OpenClaw Packages:**

```
sudo dnf upgrade openclaw openclaw-cli openclaw-desktop

```

### **Install or Downgrade to a Specific Version:**
Because the CLI and Desktop update independently, you can mix and match versions by appending the target release version to the package name:

```
sudo dnf install openclaw-desktop-2026.9.5
sudo dnf install openclaw-cli-2026.10.1

```

---

## 🗑️ Removal & Teardown

+ **Uninstall Packages:**
Remove all OpenClaw components from the system:

```
sudo dnf remove openclaw openclaw-cli openclaw-desktop openclaw-pwa-webui

```

+ If you wish to uninstall the PWA wrapper and revert to terminal-only usage or the thick Electron client:

```
sudo dnf remove openclaw-pwa-webui

```

+ **Uninstall only `openclaw-desktop` package:**

**The `openclaw-desktop` package depends on the `openclaw-cli` package. If you remove the `openclaw-desktop` package, the `openclaw-cli` package will also be removed.**

There are two ways to prevent DNF from mistaking the `openclaw-cli` package for an “unused dependency” and removing it:

**Method 1: Use a One-Time Flag (The Fastest)**
You can add the `--noautoremove` parameter to the removal command to disable the automatic removal process:

```bash
sudo dnf remove openclaw openclaw-desktop --noautoremove

```

**Method 2: Mark the Package as a “User-Installed” Package (The Safest)**
If you tell DNF that the `openclaw-cli` package is not a dependency but a main package you installed yourself, it will never attempt to remove it on its own again. To do this, first mark it, then perform the removal as usual:

```bash
sudo dnf mark install openclaw-cli
sudo dnf remove openclaw openclaw-desktop

```

Answers to Questions about Dependencies and Packages:

1. Why do we also remove openclaw when uninstalling openclaw-desktop?
Fedora’s package manager (DNF) strictly tracks dependencies. When you try to remove just openclaw-desktop, DNF says in the background, “But the meta-package named openclaw requires this to function; if I remove it, that package will break.” That’s why we remove that empty meta-package as well to break the “required dependency” chain.

2. Does the openclaw-cli package work without openclaw?
It definitely does. The actual background engine (Gateway), database, TUI, and commands are already directly included in the openclaw-cli package. The meta-package was merely a tool to facilitate its installation.

3. The openclaw-pwa-webui package works without OpenClaw. Its own “Requires” rule lists only openclaw-cli. It has no structural connection to the meta-package named openclaw.

---

### **Easy path** (CLI still installed):

The command attempts independent requested cleanup scopes and returns a nonzero status if any scope fails or is blocked. Service teardown remains the safety gate for state and workspace deletion; if that gate fails, those data scopes are preserved while app cleanup is still attempted. Partial cleanup is reported explicitly and is never followed by an unconditional completion result.

* **OpenClaw Uninstall:**
```
openclaw uninstall

```

The interactive prompt preselects only the Gateway service. For complete local removal, also select state, workspace, and app in the prompt, or run `openclaw uninstall --all`. State removal preserves configured workspace directories unless you also select `--workspace`.
```
openclaw uninstall --all

```

```
openclaw uninstall --workspace

```

* **Preview what will be removed (safe):**
```
openclaw uninstall --dry-run --all

```

* **Non-interactive (automation / npx):**
Use with caution and only after confirming scopes:
```
openclaw uninstall --all --yes --non-interactive
npx -y openclaw uninstall --all --yes --non-interactive

```

Flags: `--service`, `--state`, `--workspace`, `--app` select individual scopes; `--all` selects all four.

```
openclaw uninstall --state

```

Unlike `openclaw uninstall --state`, manual state deletion does not preserve workspaces. Stop and uninstall the service successfully before deleting files. Before manual state or prefix deletion, move any configuration you want to keep outside that directory.

1. Stop the gateway service:
```
openclaw gateway stop

```

2. Uninstall the gateway service (launchd/systemd/schtasks):
```
openclaw gateway uninstall

```

3. Decide whether to preserve the workspace.
Move every configured workspace you want to keep, including `~/.openclaw/workspace`, outside the state directory before manual deletion. Workspaces inside that directory will otherwise be deleted with it; they need no separate deletion.

4. Delete state + config:
```
rm -rf "${OPENCLAW_STATE_DIR:-$HOME/.openclaw}"

```

If you set `OPENCLAW_CONFIG_PATH` to a custom location outside the state dir, delete that file too. Restore preserved workspaces after recreating their parent, or configure their new paths on reinstall.

5. Delete an external workspace only if you want to remove its agent files too:
```
rm -rf /path/to/external/workspace

```

6. [Remove the CLI](https://docs.openclaw.ai/install/uninstall#remove-the-cli) using the installation owner below.


### **Manual service removal** (CLI not installed):

Use this if the gateway service keeps running but `openclaw` is missing.

Default unit name is `openclaw-gateway.service` (or `openclaw-gateway-<profile>.service`). A pre-rename `clawdbot-gateway.service` unit may still exist on machines upgraded from very old installs; `openclaw uninstall` / `openclaw gateway uninstall` detects and removes it automatically.

```
systemctl --user disable --now openclaw-gateway.service
rm -f ~/.config/systemd/user/openclaw-gateway.service{,.bak}
systemctl --user daemon-reload

```

See All Remove Commands [Uninstall DOCS](https://docs.openclaw.ai/install/uninstall)

---

### **Disable the Copr Repository:**
Deactivate the repository to stop receiving updates:

```bash
sudo dnf copr disable universish/OpenClaw..

```

### **Updating Packages To bypass local metadata caching and immediately pull new builds or packaging revisions** (e.g., <version>-1 to <version>-2):

* **Flush the cache:**
```
sudo dnf clean all && sudo dnf makecache

```

* **upgrade --refresh:**
```
sudo dnf upgrade --refresh openclaw "openclaw*" "openclaw-*" "openclaw-desktop*" openclaw-desktop "openclaw-cli*" openclaw-cli

```
### **If that doesn't work, follow these steps:**

* **Flush the cache:**
```
sudo dnf clean all && sudo dnf makecache

```

* **Install the thorium (it now comes directly from COPR):**
```
sudo dnf install openclaw

```

> ⚠️ **Note**: System modifications using `sudo dnf` are performed at the user's discretion. No liability is assumed for local environment alterations.

---

### Run / Usage

* **desktop gui:**
```
openclaw-desktop

```
____

* **Terminal CLI:**
```
openclaw-cli

```

or **Onboarding (CLI):**

```
openclaw onboard

```

See [CLI DOCS](https://docs.openclaw.ai/cli)
See [Onboarding DOCS](https://docs.openclaw.ai/start/wizard)

____

* **TUI:**
```
openclaw-tui

```
or

```
openclaw tui

```
See [TUI DOCS](https://docs.openclaw.ai/cli/tui/) for Other TUI commands

____

* **Dashboard CLI:**
```
openclaw dashboard

```
See [Dashboard DOCS](https://docs.openclaw.ai/cli/dashboard)

____

* **PWA (Progressive Web Application) / WebUI App Usage:**
You do not need to use the terminal to start the app.

* Simply open your GNOME/KDE application grid and click the **OpenClaw PWA** icon.
* The script will silently ensure the background Gateway daemon is running, generate your secure token, and open the UI in your default browser.
* Alternatively, you can launch it from the terminal via:
```
openclaw-webui

```

____

* **main command:**
```
openclaw

```

See [OpenClaw DOCS](https://docs.openclaw.ai/)

---

### Quickstart:

See [Quickstart](https://docs.openclaw.ai/start/getting-started)

---

## 💬 Feedback & Issues

This repository is a community-driven packaging pipeline designed to simplify the deployment of OpenClaw on Fedora Linux.

* Report RPM packaging anomalies, repository synchronization failures, or CI/CD issues in this repository's [Issue Tracker](https://www.google.com/search?q=https://github.com/universish/OpenClaw..Copr..CI/issues).
* For core application bugs, feature requests, and upstream documentation, visit the official [OpenClaw Website](https://openclaw.ai) or the [OpenClaw GitHub Repository](https://github.com/openclaw/openclaw).

---

## **White Screen / Application Hang on Launch**
If OpenClaw launches into an unresponsive white screen on Fedora, it is likely caused by an upstream Chromium/Skia bug crashing when reading certain `COLRv1` color fonts. You can resolve this by removing conflicting font packages:
```
sudo dnf remove google-noto-color-emoji-fonts hfg-gmuend-openmoji-color-fonts

```
Then refresh your font cache using `fc-cache -fv`.

---

## 📜 License

* Packaging scripts, CI/CD workflows, and `.spec` files provided in this repository are licensed under the [MIT License](https://github.com/universish/OpenClaw..Copr..CI/blob/main/LICENSE).
* The underlying OpenClaw application and its prebuilt binaries are governed by upstream licensing terms. The core OpenClaw repository is licensed under the [MIT License](https://github.com/openclaw/openclaw/blob/main/LICENSE).

---

> **Note**: Installing with superuser privileges (`sudo`) is at the user's discretion; no responsibility is accepted for local machine modifications.
