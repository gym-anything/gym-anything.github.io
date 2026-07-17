# Environment Atlas

Environment Atlas is the repository's local visual catalog, evidence browser,
and allowlisted Isaac Sim launcher. It gives every environment the same path:

1. discover the task as an image-first card;
2. read exactly what the current evidence does and does not prove;
3. start a configured Isaac Sim entrypoint;
4. keep the keyboard control card beside the running scene; and
5. inspect reports, renders, motion frames, notes, and raw traces in one place.

The global **Artifacts** page opens on the report shelf: every available PDF is
shown first with a visual preview and opens directly in a browser tab. The same
library can then be filtered across renders, motion, evidence, data, and notes.
Curated policy-attempt videos appear as poster-backed Motion cards and play in
the portal lightbox; raw episode captures remain outside the dashboard bundle.

The visual and interaction model is informed by the useful information
architecture of the Prime Intellect Environments Hub—catalog, compact metadata,
versioned detail, actions, and artifacts—but is adapted for local visual physics
environments instead of installable training packages.

## Start the portal

From the repository root on Windows:

```powershell
.\portal\run.ps1
```

It opens `http://127.0.0.1:4173`. The launcher first checks
`ISAAC_SIM_PYTHON`, then `ISAAC_SIM_ROOT`, then known local Isaac Sim download
locations. An explicit path can be supplied when needed:

```powershell
.\portal\run.ps1 -IsaacPython "D:\path\to\isaac-sim\python.bat"
```

Use dry-run mode to exercise every launch button without opening Isaac Sim:

```powershell
.\portal\run.ps1 -DryRun
```

The server binds only to `127.0.0.1` by default. Launch requests can select
only environment/profile pairs declared in the manifest; arbitrary commands
and paths are never accepted from the browser. One Isaac Sim process is allowed
at a time because the scenes contend for the same GPU. Output is written under
the ignored `portal/runtime/` directory and can be opened from the live run bar.

## Architecture

- `environments.json` is the single source for cards, status boundaries,
  launch profiles, controls, scorecards, and curated artifacts.
- `server.py` serves the application and repository assets, discovers Isaac
  Sim, starts allowlisted scripts in their correct working directories, reports
  process status, and stops the complete child process tree.
- `static/app.js` implements hash-based catalog/detail navigation, filters,
  artifact viewers, runtime polling, launch/stop actions, and the image lightbox.
- `static/styles.css` provides the responsive dark interface without a build
  step or third-party web dependency.

## Publish the public atlas

GitHub Pages is static and cannot start a visitor's local Isaac Sim process. The
public atlas therefore preserves catalog navigation, search, reports, renders,
videos, traces, notes, and documented launch profiles while labeling launch
execution as local-only.

Export a self-contained Pages tree into an empty directory. The default public
URL is the Robotics project path, `https://gym-anything.github.io/robotics/`:

```powershell
python portal/export_pages.py --output D:\path\to\gym-anything.github.io
```

The exporter copies only files curated by `environments.json`, strips executable
profile paths and environment variables from the public manifest, validates that
every referenced artifact exists inside the repository, and writes
`site-manifest.json` with the source commit and SHA-256 digest of every published
asset. Use `--clean` only when refreshing a directory that already contains the
export marker.

The public `gym-anything/gym-anything.github.io` repository is a deployment
target, not a second source tree. Its root is the organization landing page and
the generated Atlas lives under `/robotics/`. The `Publish Environment Atlas`
workflow runs the exporter after every push to the private repository's `main`
branch, replaces only the marked Robotics export, and publishes through a
write-enabled deploy key scoped exclusively to the public repository. This keeps
the simulation source private without requiring paid GitHub seats or a
hand-maintained copy.

To stage the same layout against a local checkout of the public repository:

```powershell
python -m portal.stage_pages --pages-repository D:\path\to\gym-anything.github.io
```

## Add or update an environment

Edit the matching object in `environments.json`. A complete entry includes:

- a tracked hero render and concise task description;
- an honest evidence status (`green`, `amber`, or `gray`) with a claim boundary;
- measurements that can be located in the linked report or trace;
- one or more launch profiles with repository-relative script and working paths;
- the controls that are actually registered by that profile; and
- a curated artifact set spanning visual results and technical evidence.

Use repository-relative forward-slash paths. The server rejects asset and launch
paths that resolve outside the repository. Missing local visual artifacts degrade
to a branded placeholder rather than breaking the page.

## Quick verification

Start a dry-run server and then exercise its APIs:

```powershell
python portal/server.py --dry-run --port 4173
```

Check the catalog and a detail route in a browser, start a profile, confirm the
dry-run command toast, open an image and a JSON/text artifact, switch to the list
layout, and verify the responsive view at phone width.
