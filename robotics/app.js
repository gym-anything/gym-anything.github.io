const app = document.querySelector("#app");
const lightbox = document.querySelector("#lightbox");
const toastRegion = document.querySelector("#toast-region");
const portalConfig = Object.freeze({ ...(globalThis.ATLAS_CONFIG || {}) });
const staticMode = portalConfig.mode === "static";
const publicRuntime = Object.freeze({
  publicSite: true,
  running: false,
  isaacAvailable: false,
  message: "Simulation launch requires an authorized local checkout and Isaac Sim GPU runtime.",
});

const state = {
  manifest: null,
  runtime: staticMode ? publicRuntime : null,
  query: "",
  category: "All",
  catalogTab: "explore",
  view: localStorage.getItem("atlas-view") || "grid",
  sort: "featured",
  detailTab: "overview",
  artifactFilter: "All",
  libraryFilter: "Reports",
  libraryQuery: "",
  profiles: {},
};

const escapeHTML = (value = "") =>
  String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");

const encodedAssetPath = (path) => String(path).split("/").map(encodeURIComponent).join("/");
const assetUrl = (path) => {
  const encoded = encodedAssetPath(path);
  if (!staticMode) return `/asset/${encoded}`;
  const base = new URL(portalConfig.assetBase || "./assets/", document.baseURI);
  return new URL(encoded, base).href;
};
const environmentById = (id) => state.manifest?.environments.find((item) => item.id === id);
const route = () => {
  if (location.hash.startsWith("#/artifacts")) return { name: "artifacts" };
  const match = location.hash.match(/^#\/environment\/([^/?]+)(?:\?(.+))?/);
  if (!match) return { name: "catalog" };
  const tab = new URLSearchParams(match[2] || "").get("tab");
  return { name: "detail", id: decodeURIComponent(match[1]), tab };
};

function formatElapsed(seconds) {
  const total = Math.max(0, Math.floor(seconds || 0));
  const minutes = Math.floor(total / 60);
  const secs = total % 60;
  return `${String(minutes).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
}

function toast(message, tone = "") {
  const node = document.createElement("div");
  node.className = `toast ${tone}`.trim();
  node.textContent = message;
  toastRegion.append(node);
  setTimeout(() => node.remove(), 4600);
}

function runtimeLabel() {
  if (staticMode) return ["Public atlas", "Artifacts and evidence are online", "available"];
  if (!state.runtime) return ["Checking runtime", "Looking for Isaac Sim Python", ""];
  if (state.runtime.running) {
    const env = environmentById(state.runtime.environmentId);
    return ["Simulation live", `${env?.title || state.runtime.environmentId} · ${formatElapsed(state.runtime.elapsedSeconds)}`, "running"];
  }
  if (state.runtime.isaacAvailable) {
    return [state.runtime.dryRun ? "Dry-run ready" : "Isaac Sim ready", state.runtime.dryRun ? "Launches are validated only" : "One GPU scene at a time", "available"];
  }
  return ["Isaac Sim not found", "Set ISAAC_SIM_PYTHON to enable launch", ""];
}

function shell(content, active = "catalog") {
  const [runtimeTitle, runtimeCopy, runtimeTone] = runtimeLabel();
  return `
    <div class="shell">
      <aside class="sidebar">
        <a class="brand" href="#/" aria-label="Gym Anything environment catalog">
          <span class="brand-mark">G</span>
          <span class="brand-copy"><span class="brand-title">Gym Anything</span><span class="brand-sub">Environment atlas</span></span>
        </a>
        <nav aria-label="Primary navigation">
          <div class="nav-label">Workspace</div>
          <button class="nav-item ${active === "catalog" ? "active" : ""}" data-action="catalog"><span class="nav-icon">⌗</span><span>Environments</span></button>
          <button class="nav-item ${active === "artifacts" ? "active" : ""}" data-action="artifacts"><span class="nav-icon">▧</span><span>Artifacts</span></button>
          <div class="nav-label">Repository</div>
          <button class="nav-item" data-action="guide"><span class="nav-icon">≡</span><span>Portal guide</span></button>
          ${staticMode
            ? `<a class="nav-item" href="${escapeHTML(portalConfig.organizationUrl || "https://github.com/gym-anything")}" target="_blank" rel="noreferrer"><span class="nav-icon">↗</span><span>GitHub org</span></a>`
            : `<button class="nav-item" data-action="copy-root"><span class="nav-icon">⌘</span><span>Copy repo path</span></button>`}
        </nav>
        <div class="sidebar-bottom">
          <div class="runtime-card">
            <div class="runtime-row"><span class="runtime-dot ${runtimeTone}"></span><span>${escapeHTML(runtimeTitle)}</span></div>
            <div class="runtime-copy">${escapeHTML(runtimeCopy)}</div>
          </div>
        </div>
      </aside>
      <main id="main" class="main">${content}</main>
      ${renderRunbar()}
    </div>`;
}

function renderRunbar() {
  if (!state.runtime?.running) return `<div class="runbar" hidden></div>`;
  const environment = environmentById(state.runtime.environmentId);
  const log = state.runtime.log ? assetUrl(state.runtime.log) : "";
  return `
    <div class="runbar">
      <span class="runtime-dot running"></span>
      <div class="runbar-main">
        <div class="runbar-title">${escapeHTML(environment?.title || state.runtime.environmentId)} is running</div>
        <div class="runbar-copy">${escapeHTML(state.runtime.message || "Isaac Sim process is live")}${log ? ` · <a href="${log}" target="_blank" rel="noreferrer">open log</a>` : ""}</div>
      </div>
      <span class="runbar-time">${formatElapsed(state.runtime.elapsedSeconds)}</span>
      <button class="button danger" data-action="stop">Stop</button>
    </div>`;
}

function filteredEnvironments() {
  let environments = [...state.manifest.environments];
  if (state.catalogTab === "featured") environments = environments.filter((item) => item.featured);
  if (state.catalogTab === "verified") environments = environments.filter((item) => item.status.tone === "green");
  if (state.category !== "All") environments = environments.filter((item) => item.category === state.category);
  const needle = state.query.trim().toLowerCase();
  if (needle) {
    environments = environments.filter((item) =>
      [item.title, item.eyebrow, item.summary, item.category, item.status.label, ...item.tags]
        .join(" ")
        .toLowerCase()
        .includes(needle),
    );
  }
  if (state.sort === "name") environments.sort((a, b) => a.title.localeCompare(b.title));
  if (state.sort === "updated") environments.sort((a, b) => b.updated.localeCompare(a.updated));
  if (state.sort === "evidence") environments.sort((a, b) => b.artifacts.length - a.artifacts.length);
  if (state.sort === "featured") environments.sort((a, b) => Number(b.featured) - Number(a.featured) || b.updated.localeCompare(a.updated));
  return environments;
}

function renderCatalog() {
  const environments = filteredEnvironments();
  const subtitle = staticMode
    ? "Explore each scene, inspect what it proves, and move from render to report to raw trace in one public evidence catalog."
    : "Launch a scene, inspect what it proves, and move from render to report to raw trace without hunting through the repository.";
  const totals = state.manifest.environments.reduce(
    (acc, item) => ({ environments: acc.environments + 1, artifacts: acc.artifacts + item.artifacts.length }),
    { environments: 0, artifacts: 0 },
  );
  const cards = environments.length
    ? environments.map(renderCard).join("")
    : `<div class="empty" style="grid-column:1/-1"><strong>No environment matches that view.</strong>Clear the search or choose a different physics category.</div>`;
  const content = `
    <div class="content">
      <header class="topline">
        <div>
          <div class="eyebrow">Physics-first embodied systems</div>
          <h1 class="page-title">Environment Atlas</h1>
          <p class="page-subtitle">${escapeHTML(subtitle)}</p>
        </div>
        <div class="header-actions">
          <button class="button" data-action="guide">Read guide</button>
          <button class="button primary" data-action="first-featured">Explore featured <span>↗</span></button>
        </div>
      </header>
      <div class="catalog-tabs" role="tablist" aria-label="Catalog view">
        <button class="catalog-tab ${state.catalogTab === "explore" ? "active" : ""}" data-catalog-tab="explore">Explore</button>
        <button class="catalog-tab ${state.catalogTab === "featured" ? "active" : ""}" data-catalog-tab="featured">Featured</button>
        <button class="catalog-tab ${state.catalogTab === "verified" ? "active" : ""}" data-catalog-tab="verified">Verified gates</button>
      </div>
      <div class="toolbar">
        <label class="search-wrap">
          <span class="search-icon">⌕</span>
          <input id="catalog-search" class="search" type="search" value="${escapeHTML(state.query)}" placeholder="Search tasks, physics, robots, or evidence…" autocomplete="off" />
        </label>
        <select class="select" data-action="sort" aria-label="Sort environments">
          <option value="featured" ${state.sort === "featured" ? "selected" : ""}>Featured first</option>
          <option value="updated" ${state.sort === "updated" ? "selected" : ""}>Recently updated</option>
          <option value="name" ${state.sort === "name" ? "selected" : ""}>Name</option>
          <option value="evidence" ${state.sort === "evidence" ? "selected" : ""}>Most evidence</option>
        </select>
        <div class="view-toggle" aria-label="Card layout">
          <button data-view="grid" class="${state.view === "grid" ? "active" : ""}" aria-label="Grid view">▦</button>
          <button data-view="list" class="${state.view === "list" ? "active" : ""}" aria-label="List view">☷</button>
        </div>
      </div>
      <div class="chips" aria-label="Physics categories">
        ${state.manifest.categories.map((category) => `<button class="chip ${state.category === category ? "active" : ""}" data-category="${escapeHTML(category)}">${escapeHTML(category)}</button>`).join("")}
      </div>
      <div class="results-head">
        <h2 class="section-title">${state.catalogTab === "featured" ? "Featured environments" : state.catalogTab === "verified" ? "Passed evidence gates" : "All environments"}</h2>
        <span class="result-count">${environments.length} shown · ${totals.environments} total · ${totals.artifacts} curated artifacts</span>
      </div>
      <div class="env-grid ${state.view}">${cards}</div>
    </div>`;
  app.innerHTML = shell(content, "catalog");
  bindImageFallbacks();
  const search = document.querySelector("#catalog-search");
  search?.addEventListener("input", (event) => {
    state.query = event.target.value;
    renderCatalog();
    const next = document.querySelector("#catalog-search");
    next?.focus();
    next?.setSelectionRange(state.query.length, state.query.length);
  });
}

function renderArtifactLibrary() {
  const records = state.manifest.environments.flatMap((environment) =>
    environment.artifacts.map((artifact) => ({ environment, artifact })),
  );
  const groups = ["All", "Reports", "Renders", "Motion", "Evidence", "Data", "Notes"];
  const needle = state.libraryQuery.trim().toLowerCase();
  const visible = records.filter(({ environment, artifact }) => {
    const inGroup = state.libraryFilter === "All" || artifact.group === state.libraryFilter;
    const searchable = [environment.title, artifact.label, artifact.caption, artifact.group, artifact.type, artifact.path]
      .join(" ")
      .toLowerCase();
    return inGroup && (!needle || searchable.includes(needle));
  });
  const reportCount = records.filter(({ artifact }) => artifact.type === "pdf").length;
  const content = `
    <div class="content">
      <header class="topline">
        <div>
          <div class="eyebrow">Repository evidence</div>
          <h1 class="page-title">Artifact Library</h1>
          <p class="page-subtitle">Open the report first, then follow its claims into renders, motion frames, traces, and retained research notes.</p>
        </div>
        <div class="header-actions">
          <a class="button primary" href="#/">Browse environments <span>↗</span></a>
        </div>
      </header>
      <section class="report-callout">
        <div class="report-callout-mark">PDF</div>
        <div><div class="report-callout-title">${reportCount} complete simulation reports</div><div class="report-callout-copy">The default view is reports. Every PDF opens directly in a new browser tab.</div></div>
        <span class="result-count">${records.length} total artifacts</span>
      </section>
      <div class="toolbar library-toolbar">
        <label class="search-wrap">
          <span class="search-icon">⌕</span>
          <input id="artifact-search" class="search" type="search" value="${escapeHTML(state.libraryQuery)}" placeholder="Search reports, environments, traces, or renders…" autocomplete="off" />
        </label>
      </div>
      <div class="artifact-filters library-filters">
        ${groups.map((group) => {
          const count = group === "All" ? records.length : records.filter(({ artifact }) => artifact.group === group).length;
          return `<button class="artifact-filter ${state.libraryFilter === group ? "active" : ""}" data-library-filter="${escapeHTML(group)}">${escapeHTML(group)} <span>${count}</span></button>`;
        }).join("")}
      </div>
      <div class="results-head library-results-head">
        <h2 class="section-title">${escapeHTML(state.libraryFilter === "All" ? "All artifacts" : state.libraryFilter)}</h2>
        <span class="result-count">${visible.length} shown</span>
      </div>
      <div class="artifact-grid library-grid">
        ${visible.length
          ? visible.map(({ environment, artifact }, index) => renderArtifact(artifact, index, environment.id, true)).join("")
          : `<div class="empty" style="grid-column:1/-1"><strong>No artifact matches that search.</strong>Try another file type or environment name.</div>`}
      </div>
    </div>`;
  app.innerHTML = shell(content, "artifacts");
  bindImageFallbacks();
  const search = document.querySelector("#artifact-search");
  search?.addEventListener("input", (event) => {
    state.libraryQuery = event.target.value;
    renderArtifactLibrary();
    const next = document.querySelector("#artifact-search");
    next?.focus();
    next?.setSelectionRange(state.libraryQuery.length, state.libraryQuery.length);
  });
}

function renderCard(environment) {
  const running = state.runtime?.running && state.runtime.environmentId === environment.id;
  return `
    <article class="env-card" tabindex="0" data-environment="${escapeHTML(environment.id)}" style="--accent:${escapeHTML(environment.accent)}">
      <div class="card-media">
        <div class="card-fallback" style="color:${escapeHTML(environment.accent)}33">${escapeHTML(environment.title.slice(0, 2).toUpperCase())}</div>
        <img src="${assetUrl(environment.hero)}" alt="${escapeHTML(environment.title)} environment render" loading="lazy" />
        <span class="card-category">${escapeHTML(environment.category)}</span>
        ${staticMode ? "" : `<button class="quick-launch" data-quick-launch="${escapeHTML(environment.id)}" aria-label="Launch ${escapeHTML(environment.title)}" title="Launch default profile">${running ? "■" : "▶"}</button>`}
      </div>
      <div class="card-body">
        <div class="card-top"><span>${escapeHTML(environment.eyebrow)}</span><span>v${escapeHTML(environment.version)}</span></div>
        <h3 class="card-title">${escapeHTML(environment.title)}</h3>
        <p class="card-summary">${escapeHTML(environment.summary)}</p>
        <div class="card-meta">
          <span class="status-pill ${escapeHTML(environment.status.tone)}">${escapeHTML(running ? "Running now" : environment.status.label)}</span>
          <span class="artifact-count">${environment.artifacts.length} artifacts · ${environment.profiles.length} ${staticMode ? "local " : ""}${environment.profiles.length === 1 ? "launch" : "launches"}</span>
        </div>
      </div>
    </article>`;
}

function renderDetail(environment) {
  state.profiles[environment.id] ||= environment.profiles[0]?.id;
  const selectedProfile = environment.profiles.find((profile) => profile.id === state.profiles[environment.id]) || environment.profiles[0];
  const isRunning = state.runtime?.running && state.runtime.environmentId === environment.id;
  const report = environment.artifacts.find((artifact) => artifact.type === "pdf");
  const active = state.detailTab === "artifacts" ? "artifacts" : "catalog";
  const launchPanel = staticMode
    ? `<div class="launch-stack public-launch">
        <select class="select" data-action="profile" aria-label="Local launch profile">
          ${environment.profiles.map((profile) => `<option value="${escapeHTML(profile.id)}" ${profile.id === selectedProfile.id ? "selected" : ""}>${escapeHTML(profile.label)}</option>`).join("")}
        </select>
        <button class="button large" type="button" disabled>Local Isaac only</button>
        <div class="launch-help">${escapeHTML(selectedProfile.description)} GitHub Pages cannot access a visitor's GPU; launch this profile from an authorized local checkout.</div>
      </div>`
    : `<div class="launch-stack">
        <select class="select" data-action="profile" aria-label="Launch profile">
          ${environment.profiles.map((profile) => `<option value="${escapeHTML(profile.id)}" ${profile.id === selectedProfile.id ? "selected" : ""}>${escapeHTML(profile.label)}</option>`).join("")}
        </select>
        ${isRunning
          ? `<button class="button danger large" data-action="stop">Stop sim</button>`
          : `<button class="button primary large" data-launch="${escapeHTML(environment.id)}">Start sim <span>▶</span></button>`}
        <div class="launch-help">${escapeHTML(selectedProfile.description)} One GPU simulation can run at a time.</div>
      </div>`;
  const content = `
    <div class="content" style="--accent:${escapeHTML(environment.accent)}">
      <a class="back-link" href="#/">← All environments</a>
      <section class="detail-hero">
        <div class="detail-image"><div class="card-fallback" style="color:${escapeHTML(environment.accent)}33">${escapeHTML(environment.title.slice(0, 2).toUpperCase())}</div><img src="${assetUrl(environment.hero)}" alt="${escapeHTML(environment.title)} environment" /></div>
        <div class="detail-side">
          <div class="eyebrow">${escapeHTML(environment.eyebrow)}</div>
          <h1 class="detail-title">${escapeHTML(environment.title)}</h1>
          <p class="detail-summary">${escapeHTML(environment.summary)}</p>
          <div class="detail-badges">${environment.tags.map((tag) => `<span class="tag">${escapeHTML(tag)}</span>`).join("")}</div>
          ${report ? `<a class="report-link" href="${assetUrl(report.path)}" target="_blank" rel="noreferrer"><span class="report-link-icon">PDF</span><span><strong>Read the full report</strong><small>${escapeHTML(report.label)} · opens in a new tab</small></span><span class="report-link-arrow">↗</span></a>` : ""}
          ${launchPanel}
        </div>
      </section>
      <div class="evidence-banner">
        <div class="evidence-mark ${escapeHTML(environment.status.tone)}">${environment.status.tone === "green" ? "✓" : environment.status.tone === "amber" ? "!" : "·"}</div>
        <div><div class="evidence-title">${escapeHTML(environment.status.label)}</div><div class="evidence-copy">${escapeHTML(environment.status.detail)}</div></div>
        <div class="version">v${escapeHTML(environment.version)} · ${escapeHTML(environment.updated)}</div>
      </div>
      <div class="detail-layout">
        <section>
          <div class="detail-tabs" role="tablist" aria-label="Environment details">
            ${["overview", "artifacts", "controls", "evidence"].map((tab) => `<button class="detail-tab ${state.detailTab === tab ? "active" : ""}" data-detail-tab="${tab}">${tab[0].toUpperCase() + tab.slice(1)}${tab === "artifacts" ? ` <span style="color:var(--faint)">${environment.artifacts.length}</span>` : ""}</button>`).join("")}
          </div>
          ${renderDetailPanel(environment)}
        </section>
        <aside class="detail-aside">
          <div class="aside-card">
            <div class="aside-head">About this environment</div>
            <div class="aside-body">
              <div class="about-row"><span>Category</span><strong>${escapeHTML(environment.category)}</strong></div>
              <div class="about-row"><span>Interaction</span><strong>${escapeHTML(environment.mode)}</strong></div>
              <div class="about-row"><span>Version</span><strong>${escapeHTML(environment.version)}</strong></div>
              <div class="about-row"><span>Updated</span><strong>${escapeHTML(environment.updated)}</strong></div>
              <div class="about-row"><span>Evidence</span><strong>${environment.artifacts.length} artifacts</strong></div>
            </div>
          </div>
          <div class="aside-card">
            <div class="aside-head">Control card</div>
            <div class="aside-body">${environment.controls.slice(0, 7).map((control) => `<div class="control-row"><kbd>${escapeHTML(control.keys)}</kbd><span class="control-action">${escapeHTML(control.action)}</span></div>`).join("")}</div>
          </div>
        </aside>
      </div>
    </div>`;
  app.innerHTML = shell(content, active);
  bindImageFallbacks();
}

function renderDetailPanel(environment) {
  if (state.detailTab === "artifacts") return renderArtifacts(environment);
  if (state.detailTab === "controls") {
    const controlsIntro = staticMode
      ? "These controls apply when the profile is running in a local Isaac Sim checkout. The public atlas documents them but cannot forward browser input to a visitor's simulator."
      : "Controls are delivered to the Isaac Sim window, so click that window before using them. Camera orbit and the Isaac toolbar remain available in every profile.";
    return `<div class="tab-panel copy-section"><h2>Keyboard and runtime controls</h2><p>${escapeHTML(controlsIntro)}</p><div style="margin-top:18px" class="evidence-list">${environment.controls.map((control, index) => `<div class="evidence-row"><div class="evidence-index">${String(index + 1).padStart(2, "0")}</div><div><h3><kbd>${escapeHTML(control.keys)}</kbd></h3><p>${escapeHTML(control.action)}</p></div></div>`).join("")}</div></div>`;
  }
  if (state.detailTab === "evidence") {
    const evidence = [
      ["Claim boundary", environment.status.detail],
      ["Measured scorecard", environment.metrics.map((metric) => `${metric.label}: ${metric.value}`).join(" · ")],
      ["Inspectable record", `${environment.artifacts.length} curated artifacts connect renders to reports, raw traces, and retained findings.`],
      ["Reproducible entrypoint", `${environment.profiles.length} allowlisted launch ${environment.profiles.length === 1 ? "profile is" : "profiles are"} ${staticMode ? "documented here and available from an authorized local checkout" : "available from this page"}.`],
    ];
    return `<div class="tab-panel copy-section"><h2>What the current environment proves</h2><p>This summary keeps presentation quality separate from physics acceptance. Open the report and traces for the exact gates.</p><div style="margin-top:18px" class="evidence-list">${evidence.map((item, index) => `<div class="evidence-row"><div class="evidence-index">${String(index + 1).padStart(2, "0")}</div><div><h3>${escapeHTML(item[0])}</h3><p>${escapeHTML(item[1])}</p></div></div>`).join("")}</div></div>`;
  }
  return `<div class="tab-panel copy-section">
    <h2>Environment intent</h2>
    <p>${escapeHTML(environment.description)}</p>
    <div class="metric-grid">${environment.metrics.map((metric) => `<div class="metric"><div class="metric-value ${escapeHTML(metric.tone || "")}">${escapeHTML(metric.value)}</div><div class="metric-label">${escapeHTML(metric.label)}</div></div>`).join("")}</div>
    <h2>From scene to evidence</h2>
    <div class="mechanism-strip">
      <div class="mechanism-item"><div class="mechanism-number">01</div><div class="mechanism-title">${staticMode ? "Choose a profile" : "Run the world"}</div><div class="mechanism-copy">${staticMode ? "Inspect the exact local Isaac entrypoint represented by each evidence bundle." : "Start an allowlisted Isaac entrypoint with its correct working directory."}</div></div>
      <div class="mechanism-item"><div class="mechanism-number">02</div><div class="mechanism-title">Interact and inspect</div><div class="mechanism-copy">Use the control card and cameras without hiding the underlying physics state.</div></div>
      <div class="mechanism-item"><div class="mechanism-number">03</div><div class="mechanism-title">Audit the claim</div><div class="mechanism-copy">Open the exact render, motion frame, report, source note, or numerical trace.</div></div>
    </div>
  </div>`;
}

function renderArtifacts(environment) {
  const groups = ["All", ...new Set(environment.artifacts.map((artifact) => artifact.group))];
  if (!groups.includes(state.artifactFilter)) state.artifactFilter = "All";
  const artifacts = state.artifactFilter === "All" ? environment.artifacts : environment.artifacts.filter((artifact) => artifact.group === state.artifactFilter);
  return `<div class="tab-panel">
    <div class="artifact-toolbar">
      <div class="artifact-filters">${groups.map((group) => `<button class="artifact-filter ${state.artifactFilter === group ? "active" : ""}" data-artifact-filter="${escapeHTML(group)}">${escapeHTML(group)}</button>`).join("")}</div>
      <span class="result-count">${artifacts.length} files</span>
    </div>
    <div class="artifact-grid">${artifacts.map((artifact, index) => renderArtifact(artifact, index, environment.id, false)).join("")}</div>
  </div>`;
}

function renderArtifact(artifact, index, environmentId, includeEnvironment = false) {
  const environment = environmentById(environmentId);
  const visual = artifact.type === "image"
    ? `<img src="${assetUrl(artifact.path)}" alt="${escapeHTML(artifact.label)}" loading="lazy" />`
    : artifact.type === "video"
      ? `<video src="${assetUrl(artifact.path)}"${artifact.preview ? ` poster="${assetUrl(artifact.preview)}"` : ""} muted playsinline preload="metadata"></video><span class="artifact-play" aria-hidden="true">▶</span>`
      : artifact.type === "pdf" && artifact.preview
        ? `<img src="${assetUrl(artifact.preview)}" alt="Preview of ${escapeHTML(artifact.label)}" loading="lazy" />`
        : `<span class="artifact-symbol">${artifact.type === "pdf" ? "PDF" : artifact.type === "json" ? "{ }" : "Aa"}</span>`;
  return `<article class="artifact ${artifact.type === "pdf" ? "pdf-artifact" : artifact.type === "video" ? "video-artifact" : ""}" tabindex="0" data-artifact-index="${index}" data-artifact-environment="${escapeHTML(environmentId)}" data-artifact-path="${escapeHTML(artifact.path)}">
    <div class="artifact-media">${visual}<span class="artifact-type">${escapeHTML(artifact.group)} · ${escapeHTML(artifact.type)}</span></div>
    <div class="artifact-copy">${includeEnvironment ? `<div class="artifact-environment">${escapeHTML(environment?.title || environmentId)}</div>` : ""}<div class="artifact-title">${escapeHTML(artifact.label)}</div><div class="artifact-caption">${escapeHTML(artifact.caption)}</div><div class="artifact-path">${escapeHTML(artifact.path)}</div></div>
  </article>`;
}

function renderApp() {
  if (!state.manifest) {
    app.innerHTML = `<div class="loading"><div><div class="loading-mark"></div>Loading environment atlas…</div></div>`;
    return;
  }
  const current = route();
  if (current.name === "detail") {
    const environment = environmentById(current.id);
    if (!environment) {
      app.innerHTML = shell(`<div class="content"><div class="empty"><strong>Environment not found.</strong><a href="#/">Return to the catalog</a></div></div>`);
      return;
    }
    renderDetail(environment);
  } else if (current.name === "artifacts") {
    renderArtifactLibrary();
  } else {
    renderCatalog();
  }
}

function bindImageFallbacks() {
  document.querySelectorAll("img").forEach((image) => {
    image.addEventListener("error", () => image.classList.add("broken"), { once: true });
  });
}

async function updateRuntime({ rerender = true } = {}) {
  if (staticMode) return;
  try {
    const response = await fetch("/api/status", { cache: "no-store" });
    if (!response.ok) return;
    const previous = JSON.stringify(state.runtime);
    state.runtime = await response.json();
    if (rerender && JSON.stringify(state.runtime) !== previous) renderApp();
  } catch {
    // A transient poll failure should not replace the catalog.
  }
}

async function launch(environmentId, profileId = null) {
  const environment = environmentById(environmentId);
  if (!environment) return;
  if (staticMode) {
    toast("Simulation launch requires an authorized local checkout and Isaac Sim GPU runtime.");
    return;
  }
  const selected = profileId || state.profiles[environmentId] || environment.profiles[0]?.id;
  try {
    const response = await fetch("/api/launch", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ environmentId, profileId: selected }),
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error || "Launch failed");
    state.runtime = payload;
    if (payload.dryRun) toast(`Dry run validated ${environment.title}: ${payload.command.join(" ")}`, "success");
    else toast(`${environment.title} is launching. The Isaac Sim window can take a little while to appear.`, "success");
    renderApp();
  } catch (error) {
    toast(error.message, "error");
  }
}

async function stopSimulation() {
  if (staticMode) return;
  try {
    const response = await fetch("/api/stop", { method: "POST" });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error || "Stop failed");
    state.runtime = payload;
    toast(payload.message || "Simulation stopped");
    renderApp();
  } catch (error) {
    toast(error.message, "error");
  }
}

async function copyRepositoryPath() {
  if (staticMode) return;
  try {
    const response = await fetch("/api/health", { cache: "no-store" });
    if (!response.ok) throw new Error("Repository path is unavailable");
    const payload = await response.json();
    await navigator.clipboard.writeText(payload.repository);
    toast("Repository path copied.");
  } catch (error) {
    toast(error.message, "error");
  }
}

async function openArtifact(artifact) {
  if (!artifact) return;
  const url = assetUrl(artifact.path);
  if (artifact.type === "pdf") {
    window.open(url, "_blank", "noopener,noreferrer");
    return;
  }
  const header = `<div class="lightbox-head"><div class="lightbox-title">${escapeHTML(artifact.label)}</div><div class="lightbox-path">${escapeHTML(artifact.path)}</div><a class="button" href="${url}" target="_blank" rel="noreferrer">Open file</a><button class="button icon" data-action="close-lightbox" aria-label="Close">×</button></div>`;
  if (artifact.type === "image" || artifact.type === "video") {
    const media = artifact.type === "image" ? `<img src="${url}" alt="${escapeHTML(artifact.label)}" />` : `<video src="${url}" controls autoplay></video>`;
    lightbox.innerHTML = `<div class="lightbox-dialog" role="dialog" aria-modal="true" aria-label="${escapeHTML(artifact.label)}">${header}<div class="lightbox-body">${media}</div></div>`;
    lightbox.hidden = false;
    lightbox.querySelector("[data-action=close-lightbox]")?.focus();
    return;
  }
  lightbox.innerHTML = `<div class="lightbox-dialog" role="dialog" aria-modal="true" aria-label="${escapeHTML(artifact.label)}">${header}<div class="lightbox-body"><div class="loading"><div><div class="loading-mark"></div>Loading file…</div></div></div></div>`;
  lightbox.hidden = false;
  try {
    const response = await fetch(url);
    if (!response.ok) throw new Error("Artifact is not available in this checkout");
    let text = await response.text();
    if (artifact.type === "json") {
      try { text = JSON.stringify(JSON.parse(text), null, 2); } catch { /* keep original */ }
    }
    const clipped = text.length > 180000 ? `${text.slice(0, 180000)}\n\n… preview clipped at 180 kB; use Open file for the complete artifact.` : text;
    const pre = document.createElement("pre");
    pre.textContent = clipped;
    lightbox.querySelector(".lightbox-body").replaceChildren(pre);
  } catch (error) {
    const pre = document.createElement("pre");
    pre.textContent = error.message;
    lightbox.querySelector(".lightbox-body").replaceChildren(pre);
  }
}

document.addEventListener("click", (event) => {
  const action = event.target.closest("[data-action]")?.dataset.action;
  if (action === "catalog") location.hash = "#/";
  if (action === "artifacts") location.hash = "#/artifacts";
  if (action === "guide") openArtifact({ label: "Environment portal guide", path: "portal/README.md", type: "text" });
  if (action === "copy-root") copyRepositoryPath();
  if (action === "first-featured") {
    const featured = state.manifest.environments.find((item) => item.featured);
    if (featured) location.hash = `#/environment/${encodeURIComponent(featured.id)}`;
  }
  if (action === "stop") stopSimulation();
  if (action === "close-lightbox") lightbox.hidden = true;

  const catalogTab = event.target.closest("[data-catalog-tab]")?.dataset.catalogTab;
  if (catalogTab) { state.catalogTab = catalogTab; renderCatalog(); }
  const category = event.target.closest("[data-category]")?.dataset.category;
  if (category) { state.category = category; renderCatalog(); }
  const view = event.target.closest("[data-view]")?.dataset.view;
  if (view) { state.view = view; localStorage.setItem("atlas-view", view); renderCatalog(); }
  const detailTab = event.target.closest("[data-detail-tab]")?.dataset.detailTab;
  if (detailTab) {
    const current = route();
    state.detailTab = detailTab;
    state.artifactFilter = "All";
    location.hash = `#/environment/${encodeURIComponent(current.id)}?tab=${detailTab}`;
  }
  const artifactFilter = event.target.closest("[data-artifact-filter]")?.dataset.artifactFilter;
  if (artifactFilter) { state.artifactFilter = artifactFilter; renderApp(); }
  const libraryFilter = event.target.closest("[data-library-filter]")?.dataset.libraryFilter;
  if (libraryFilter) { state.libraryFilter = libraryFilter; renderArtifactLibrary(); }

  const quick = event.target.closest("[data-quick-launch]")?.dataset.quickLaunch;
  if (quick) {
    event.stopPropagation();
    if (state.runtime?.running && state.runtime.environmentId === quick) stopSimulation();
    else launch(quick);
    return;
  }
  const launchId = event.target.closest("[data-launch]")?.dataset.launch;
  if (launchId) launch(launchId);

  const artifactNode = event.target.closest("[data-artifact-index]");
  if (artifactNode) {
    const environment = environmentById(artifactNode.dataset.artifactEnvironment);
    const artifact = environment?.artifacts.find((item) => item.path === artifactNode.dataset.artifactPath);
    openArtifact(artifact);
    return;
  }
  const card = event.target.closest("[data-environment]");
  if (card) location.hash = `#/environment/${encodeURIComponent(card.dataset.environment)}`;
});

document.addEventListener("change", (event) => {
  if (event.target.matches('[data-action="sort"]')) { state.sort = event.target.value; renderCatalog(); }
  if (event.target.matches('[data-action="profile"]')) {
    const current = route();
    state.profiles[current.id] = event.target.value;
    renderApp();
  }
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && !lightbox.hidden) lightbox.hidden = true;
  if ((event.key === "Enter" || event.key === " ") && event.target.matches(".env-card, .artifact")) event.target.click();
});

lightbox.addEventListener("click", (event) => {
  if (event.target === lightbox) lightbox.hidden = true;
});

window.addEventListener("hashchange", () => {
  const current = route();
  state.detailTab = ["overview", "artifacts", "controls", "evidence"].includes(current.tab) ? current.tab : "overview";
  state.artifactFilter = "All";
  window.scrollTo({ top: 0, behavior: "instant" });
  renderApp();
});

async function init() {
  renderApp();
  try {
    const manifestUrl = staticMode ? (portalConfig.manifestUrl || "./environments.json") : "/api/environments";
    const runtimeRequest = staticMode ? Promise.resolve(null) : fetch("/api/status", { cache: "no-store" });
    const [manifestResponse, runtimeResponse] = await Promise.all([
      fetch(manifestUrl, { cache: "no-store" }),
      runtimeRequest,
    ]);
    if (!manifestResponse.ok) throw new Error("Environment manifest could not be loaded");
    state.manifest = await manifestResponse.json();
    if (runtimeResponse?.ok) state.runtime = await runtimeResponse.json();
    const initialRoute = route();
    if (["overview", "artifacts", "controls", "evidence"].includes(initialRoute.tab)) {
      state.detailTab = initialRoute.tab;
    }
    renderApp();
    if (!staticMode) setInterval(() => updateRuntime(), 2000);
  } catch (error) {
    app.innerHTML = `<div class="loading"><div><strong>Portal could not start.</strong><div style="margin-top:8px;color:var(--red)">${escapeHTML(error.message)}</div></div></div>`;
  }
}

init();
