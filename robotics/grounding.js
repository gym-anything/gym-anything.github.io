const PAGE_SIZES = [25, 50, 100, 250];
const DATASET_CACHE_LIMIT = 3;

const compactNumber = new Intl.NumberFormat("en-US", {
  notation: "compact",
  maximumFractionDigits: 2,
});
const integerNumber = new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 });

const FIELD_LABELS = Object.freeze({
  action: "Action",
  actions: "Draft actions",
  allocation_status: "Action-allocation status",
  axis: "Ranking measure",
  candidate_count: "Number of possible matches",
  candidate_kind: "Type of task proposal",
  candidates: "Possible action matches",
  catalog_status: "Action-grouping status",
  cleaned_actions: "Actions after automated checking",
  code: "Source-category code",
  confidence: "Model confidence",
  confidence_counts: "Counts by model-confidence level",
  contributors: "Contributing sources and actions",
  covered: "Represented",
  decision: "Automated action-pair decision",
  end_state: "Ending physical state",
  grouped_occurrences: "Grouped action instances",
  household_production_status: "Supplemental household-production estimate status",
  initial_state: "Initial physical state",
  instruction: "Task instruction",
  jurisdiction: "Country or source jurisdiction",
  jurisdictions: "Countries or source jurisdictions",
  label: "Source-category name",
  language: "Source language",
  link_status: "Link to action catalog",
  ranking_axis: "Ranking measure",
  reason: "Recorded reason",
  reset: "Reset plan",
  source_count: "Number of source records",
  start_state: "Starting physical state",
  status: "Implementation-plan status",
  support: "Supporting source text",
  terminal_state: "Required final state",
  tier: "Selection allocation",
  tool: "Tool or fixture",
  weights: "Separate work-value and time estimates",
  source_unit_uid: "Source record ID",
  source_unit_uids: "Source record IDs",
  source_kind: "Type of source activity",
  source_text: "Original source text",
  source_collection: "Public source collection",
  context_label: "Occupation or activity category",
  weight_axis: "Ranking measure",
  weight_value: "Source estimate",
  weight_unit: "Estimate unit",
  weight_status: "Estimate status",
  raw_classification: "First-pass label",
  classification: "Draft physicality label",
  classification_verdict: "Second-pass label decision",
  final_classification: "Label after automated checking",
  missing_action: "First pass missed an action",
  action_order: "Action order within source",
  action_validations: "Second-pass action decisions",
  validation_verdict: "Second-pass action decision",
  validation_issues: "Problems found by second pass",
  validation_reason: "Reason for second-pass decision",
  occurrence_id: "Action-instance ID",
  occurrence_ids: "Action-instance IDs",
  anchor_occurrence_id: "Action being compared",
  left_occurrence_id: "First action-instance ID",
  right_occurrence_id: "Second action-instance ID",
  action_occurrence_count: "Number of retained action instances",
  catalog_occurrence_count: "Number of catalog action instances",
  grouped_occurrence_count: "Number of grouped action instances",
  quarantined_occurrence_count: "Number of under-specified action instances",
  occurrence_count: "Number of action instances",
  state_change_family: "Type of physical state change",
  topology_change: "Cutting, tearing, or joining change",
  contact_modes: "Required physical contacts",
  mechanics_families: "Physical behavior categories",
  required_mechanics_families: "Required physical behavior categories",
  completion_condition: "Measurable success condition",
  terminal_relation: "Required final relation",
  interaction_mechanism: "How physical interaction occurs",
  material_regime: "Material behavior category",
  signature: "Normalized physical description",
  signature_equal: "Normalized descriptions match",
  candidate_judgments: "Model judgments about possible matches",
  directional_model_judgments: "Model judgments in both comparison directions",
  pair_id: "Compared-pair ID",
  block_id: "Compatibility-group ID",
  group_id: "Physical-action group ID",
  group_ids: "Physical-action group IDs",
  left_group_id: "First action's group ID",
  right_group_id: "Second action's group ID",
  group_label: "Physical-action group name",
  canonical_label: "Standard action name",
  group_method: "How the group was formed",
  quarantine_reason: "Why the action was left ungrouped",
  quarantined_action_mass: "Value or time assigned to under-specified actions",
  quarantined_occurrences: "Under-specified action instances",
  resolution_status: "Physical-detail status",
  resolution_reason: "Reason for physical-detail status",
  source_weight_point: "Stored source estimate",
  physical_share: "Estimated physical fraction",
  physical_share_lower: "Physical-fraction lower scenario",
  physical_share_point: "Physical-fraction point estimate",
  physical_share_upper: "Physical-fraction upper scenario",
  physical_share_confidence: "Confidence in physical-fraction judgment",
  physical_share_reason: "Reason for physical-fraction estimate",
  physical_share_status: "Physical-fraction estimate status",
  action_share: "Estimated fraction assigned to this action",
  action_share_lower: "Action-fraction lower scenario",
  action_share_point: "Action-fraction point estimate",
  action_share_upper: "Action-fraction upper scenario",
  action_share_reason: "Reason for action-fraction estimate",
  activity_buckets: "Source categories linked to this proposal",
  occurrence_weight_lower: "Action contribution, lower scenario",
  occurrence_weight_point: "Action contribution, point estimate",
  occurrence_weight_upper: "Action contribution, upper scenario",
  allocated_group_mass: "Value or time assigned to action groups",
  nonphysical_mass: "Value or time assigned to nonphysical content",
  unresolved_physicality_mass: "Value or time with unresolved physicality",
  excluded_mass: "Excluded value or time",
  conservation_difference: "Reconciliation difference",
  accounting_status: "Reconciliation status",
  market_work_economic_value_usd: "Allocated annual U.S. economic value",
  market_work_rank: "Economic-value rank",
  market_work_rank_status: "Economic-value rank status",
  marginal_axis_weight: "Prevalence assigned to this selection on its ranking measure",
  new_activity_buckets: "Source categories newly represented by this selection",
  new_physics_regimes: "Physics categories newly represented by this selection",
  everyday_life_annual_population_hours: "Estimated annual U.S. population-hours",
  everyday_life_rank: "Everyday-life rank",
  everyday_life_rank_status: "Everyday-life rank status",
  point_estimate: "Point estimate",
  standard_error: "Survey standard error",
  ci95_lower_nonnegative: "95% interval, lower bound",
  ci95_upper: "95% interval, upper bound",
  replicate_systems_used: "Survey methods used to estimate sampling error",
  replicate_input_complete: "All sampling-error inputs available",
  candidate_id: "Task-proposal ID",
  environment_id: "Existing environment ID",
  working_title: "Task-proposal title",
  action_label: "Physical action",
  object_or_person: "Object or person acted on",
  tool_or_fixture: "Tool or fixture",
  asset_requirements: "Required simulation assets",
  physics_regimes: "Required physics categories",
  required_physics_regimes: "Required physics categories",
  compute_class: "Compute requirement",
  development_flags: "Additional development required",
  fidelity_test: "Real-world comparison plan",
  verification: "Success-check plan",
  verification_condition: "Measurable success condition",
  feasibility: "Implementation-plan status",
  feasibility_status: "Implementation-plan status",
  selectable: "Included in automated selection screen",
  selection_order: "Selection order",
  selection_reason: "Reason selected",
  selection_target: "Selection goal",
  selected_environment_id: "Planned environment ID",
  uncovered_reason: "Reason it remained outside this release's portfolio",
  uncredited_reason: "Reason existing credit was unavailable",
  existing_environment_ids: "Matching existing environment IDs",
  grounding_occurrence: "Representative source action",
  credited_action_groups: "Represented physical-action groups",
  credited_environment_count: "Number of representing environments",
  credited_group_count: "Number of represented action groups",
  total_grouped_action_weight: "Total grouped value or time",
  covered_grouped_action_weight: "Value or time represented",
  covered_percent: "Share represented",
  positive_weight_action_groups: "Groups with a positive estimate",
  covered_positive_weight_action_groups: "Positive-estimate groups represented",
  bucket_id: "Source-category ID",
  bucket_type: "Source-category type",
  regime: "Physics category",
  action_group_id: "Action-group ID",
  action_group_index: "Action-group index",
  atomic_action_occurrence_id: "Action-occurrence ID",
  representative_action: "Representative action",
  group_origin: "Action-group origin",
  selection_status: "Eligibility status",
  selection_eligible: "Selection eligible",
  canonical_capability_id: "Capability ID",
  canonical_name: "Capability name",
  domain: "Capability domain",
  robot_capabilities: "Robot capabilities",
  physics_capabilities: "Physics capabilities",
  active_requirement_count: "Active requirements",
  missing_requirement_count: "Missing requirements",
  missing_requirements: "Missing requirements",
  portfolio_display_sequence: "Portfolio order",
  tier_id: "Selection tier",
  mode_id: "Capability mode",
  allocated_point_mass: "Allocated source value",
  allocation_share: "Allocation share",
  leaf_count: "Canonical leaves represented",
  action_count_sum: "Actions linked to cluster",
  created_in_round: "Created in clustering round",
});

const VALUE_LABELS = Object.freeze({
  k1_paid_work: "High paid-work prevalence",
  k2_everyday_life: "High everyday-life time",
  k3_activity_coverage: "Broader source-category representation",
  k4_action_coverage: "Broader physical-action representation",
  k5_physics_coverage: "Broader physics representation",
  market_work_economic_value_usd: "Economic value (allocated USD)",
  everyday_life_annual_population_hours: "Everyday-life population-hours",
  selected: "Selected in this mode",
  existing_coverage: "Represented by an existing simulation",
  uncovered: "Not selected in this release",
  ineligible: "Excluded by the fixed planning screen",
  ready: "Uses existing simulator capabilities",
  needs_development: "Requires additional development",
  physical: "Physical",
  nonphysical: "Nonphysical",
  unresolved: "Unresolved",
  keep: "Keep",
  repair: "Repair",
  reject: "Reject",
  uncertain: "Uncertain",
  grouped: "Assigned to an action group",
  quarantine: "Under-specified and kept outside grouping",
  sufficient: "Detailed enough to compare",
  k1_economic_core: "k1 · Economic core",
  k2_1_strategic_domains: "k2.1 · Strategic domains",
  k2_2_stem_research: "k2.2 · STEM and research",
  k3_soc_major_diversity: "k3 · SOC-major diversity",
  k4_niche_occupations: "k4 · Niche occupations",
  k5_capability_family_fill: "k5 · Capability-family fill",
  physics_only: "Physics only",
  physics_plus_robotics: "Physics + robotics",
  robotics_only: "Robotics only",
  robot_capabilities: "Robot",
  physics_capabilities: "Physics",
});

const HUMAN_VALUE_FIELDS = new Set([
  "allocation_status", "axis", "bucket_type", "candidate_kind", "catalog_status",
  "classification", "classification_verdict", "compute_class", "confidence",
  "contact_modes", "control_requirements", "decision", "feasibility",
  "feasibility_status", "final_classification", "group_method", "interaction_mechanism",
  "language", "link_status", "market_work_rank_status", "material_regime",
  "mechanics_families", "everyday_life_rank_status", "physical_share_confidence",
  "new_physics_regimes", "physical_share_status", "physics_regimes", "ranking_axis", "regime",
  "required_mechanics_families", "required_physics_regimes", "resolution_status",
  "source_kind", "source_kinds", "state_change_family", "status", "terminal_relation",
  "tier", "topology_change", "validation_verdict", "weight_axis", "weight_status",
]);

export function createGroundingUI(context) {
  const {
    app,
    lightbox,
    state,
    shell,
    escapeHTML,
    assetUrl,
    staticMode,
    portalConfig,
    openArtifact,
    toast,
  } = context;

  const cache = new Map();
  const loads = new Map();
  const facetCache = new Map();
  let leaderboardRows = null;
  let leaderboardLoad = null;
  let inputTimer = null;
  let visibleDatasetRows = [];
  let visibleLeaderboardRows = [];

  const datasetView = {
    id: null,
    query: "",
    facetField: "",
    facetValue: "",
    sort: "",
    direction: "asc",
    page: 1,
    pageSize: 50,
  };

  const leaderboardView = {
    view: "selected",
    mode: "robotics_only",
    query: "",
    tier: "All",
    status: "All",
    sort: "",
    direction: "asc",
    page: 1,
    pageSize: 50,
  };

  function manifest() {
    return state.groundingManifest;
  }

  function datasetById(id) {
    return manifest()?.datasets.find((item) => item.id === id);
  }

  function stageByNumber(number) {
    return manifest()?.stages.find((item) => item.number === Number(number));
  }

  function fileSize(bytes) {
    if (!Number.isFinite(Number(bytes))) return "—";
    const value = Number(bytes);
    if (value < 1024) return `${value} B`;
    if (value < 1024 ** 2) return `${(value / 1024).toFixed(1)} kB`;
    return `${(value / 1024 ** 2).toFixed(value > 10 * 1024 ** 2 ? 1 : 2)} MB`;
  }

  function formatLabel(format) {
    if (format === "csv") return "CSV";
    if (format === "json") return "JSON";
    if (format === "jsonl_gz") return "Compressed JSON Lines";
    return titleCase(format);
  }

  function fullNumber(value) {
    if (value === null || value === undefined || value === "") return "—";
    const numeric = Number(value);
    return Number.isFinite(numeric) ? integerNumber.format(numeric) : String(value);
  }

  function weight(value, axis) {
    if (value === null || value === undefined || value === "") return "—";
    const numeric = Number(value);
    if (!Number.isFinite(numeric)) return String(value);
    if (axis === "market") return `$${compactNumber.format(numeric)}`;
    return `${compactNumber.format(numeric)} h/yr`;
  }

  function titleCase(value = "") {
    return String(value)
      .replaceAll("_", " ")
      .replace(/\b\w/g, (letter) => letter.toUpperCase());
  }

  function fieldLabel(value = "") {
    if (FIELD_LABELS[value]) return FIELD_LABELS[value];
    return titleCase(value)
      .replace(/\bUid\b/g, "ID")
      .replace(/\bId\b/g, "ID")
      .replace(/\bIds\b/g, "IDs")
      .replace(/\bUsd\b/g, "USD")
      .replace(/\bAtus\b/g, "ATUS")
      .replace(/\bSoc\b/g, "SOC")
      .replace(/\bJson\b/g, "JSON");
  }

  function plainValue(value) {
    if (value === null || value === undefined) return "";
    if (typeof value === "object") return JSON.stringify(value);
    return String(value);
  }

  function displayScalar(value, field = "") {
    const text = String(value);
    if (VALUE_LABELS[text]) return VALUE_LABELS[text];
    if (HUMAN_VALUE_FIELDS.has(field)) return titleCase(text);
    return text;
  }

  function measuredValue(value, field = "", record = null) {
    const numeric = Number(value);
    if (!Number.isFinite(numeric)) return null;
    const recordAxis = String(record?.ranking_axis || record?.weight_axis || record?.axis || record?.weight_unit || "").toLowerCase();
    const dollarField = field.includes("_usd") || (field === "marginal_axis_weight" && recordAxis.includes("market"));
    const hourField = field.includes("population_hours") || ["point_estimate", "standard_error", "ci95_lower_nonnegative", "ci95_upper"].includes(field) || (field === "marginal_axis_weight" && recordAxis.includes("everyday"));
    const axisValue = ["weight_value", "source_weight_point", "occurrence_weight_lower", "occurrence_weight_point", "occurrence_weight_upper", "total_grouped_action_weight", "covered_grouped_action_weight"].includes(field);
    if (dollarField || (axisValue && (recordAxis.includes("market") || recordAxis.includes("usd")))) return `$${compactNumber.format(numeric)}`;
    if (hourField || (axisValue && (recordAxis.includes("everyday") || recordAxis.includes("hour")))) return `${compactNumber.format(numeric)} h/yr`;
    if (field === "covered_percent") return `${numeric.toFixed(1)}%`;
    return null;
  }

  function displayFieldScalar(value, field = "", record = null) {
    const measured = measuredValue(value, field, record);
    if (measured) return measured;
    if (field === "new_activity_buckets") {
      const match = record?.activity_buckets?.find((bucket) => bucket.bucket_id === String(value));
      if (match?.label) return match.label;
    }
    return displayScalar(value, field);
  }

  function briefValue(value, field = "", record = null) {
    if (value === null || value === undefined || value === "") return `<span class="g-null">Not recorded</span>`;
    if (typeof value === "boolean") return `<span class="g-boolean ${value ? "yes" : "no"}">${value ? "yes" : "no"}</span>`;
    if (Array.isArray(value)) {
      if (!value.length) return `<span class="g-null">None</span>`;
      const simple = value.every((item) => ["string", "number", "boolean"].includes(typeof item));
      if (simple) {
        return `<span class="g-array">${value.slice(0, 3).map((item) => `<span>${escapeHTML(displayFieldScalar(item, field, record))}</span>`).join("")}${value.length > 3 ? `<small>+${value.length - 3}</small>` : ""}</span>`;
      }
      return `<span class="g-complex">${value.length} nested ${value.length === 1 ? "item" : "items"}</span>`;
    }
    if (typeof value === "object") return `<span class="g-complex">${Object.keys(value).length} fields</span>`;
    const text = displayFieldScalar(value, field, record);
    const clipped = text.length > 135 ? `${text.slice(0, 132)}…` : text;
    return `<span title="${escapeHTML(text)}">${escapeHTML(clipped)}</span>`;
  }

  function stageRail(activeNumber = 0) {
    return `<nav class="g-stage-rail" aria-label="Activity-selection stages">
      ${manifest().stages.map((stage) => `
        <a href="#/grounding/stage/${stage.number}" class="g-stage-stop ${stage.number === activeNumber ? "active" : ""}" style="--stage:${stage.accent}">
          <span>${String(stage.number).padStart(2, "0")}</span>
          <strong>${escapeHTML(stage.shortTitle)}</strong>
        </a>`).join("")}
    </nav>`;
  }

  function metricCards(metrics, className = "") {
    return `<div class="g-metrics ${className}">${metrics.map((metric) => `
      <div class="g-metric">
        <strong>${escapeHTML(metric.value)}</strong>
        <span>${escapeHTML(metric.label)}</span>
      </div>`).join("")}</div>`;
  }

  function datasetCard(dataset, compact = false) {
    const stage = stageByNumber(dataset.stage);
    const substep = stage?.substeps.find((item) => item.id === dataset.substep);
    return `<a class="g-dataset-card ${compact ? "compact" : ""}" href="#/grounding/data/${encodeURIComponent(dataset.id)}">
      <div class="g-dataset-top">
        <span class="g-format">${escapeHTML(formatLabel(dataset.format))}</span>
        <span>${fullNumber(dataset.rowCount)} rows</span>
      </div>
      <h3>${escapeHTML(dataset.title)}</h3>
      ${compact ? "" : `<p>${escapeHTML(dataset.description)}</p>`}
      <div class="g-dataset-foot">
        <span>Stage ${dataset.stage}${substep ? ` · ${escapeHTML(substep.title)}` : ""}</span>
        <span>View <b>→</b></span>
      </div>
    </a>`;
  }

  function documentCard(document) {
    return `<button class="g-document-card" data-grounding-document="${escapeHTML(document.path)}">
      <span class="g-document-type">${document.type === "pdf" ? "PDF" : "DOC"}</span>
      <span><strong>${escapeHTML(document.label)}</strong><small>${escapeHTML(document.description)}</small></span>
      <b>↗</b>
    </button>`;
  }

  function glossary(items = []) {
    return `<dl class="g-glossary">${items.map((item) => `
      <div><dt>${escapeHTML(item.term)}</dt><dd>${escapeHTML(item.definition)}</dd></div>`).join("")}</dl>`;
  }

  function decisionMethod(method) {
    if (!method) return "";
    return `<section class="g-decision-method">
      <div class="g-decision-method-head">
        <div><span>How decisions were made</span><h4>${escapeHTML(method.heading)}</h4></div>
        <strong>${escapeHTML(method.kind)}</strong>
      </div>
      <ol class="g-decision-criteria">${method.criteria.map((criterion) => `
        <li><b>${escapeHTML(criterion.label)}</b><p>${escapeHTML(criterion.text)}</p></li>`).join("")}</ol>
      <div class="g-method-sources">
        <span>Method source${method.sources.length === 1 ? "" : "s"}</span>
        <div>${method.sources.map((source) => `<button type="button" data-grounding-method-source="${escapeHTML(source.path)}" data-grounding-method-label="${escapeHTML(source.label)}" data-grounding-method-type="${escapeHTML(source.type)}"><strong>${escapeHTML(source.label)}</strong><code>${escapeHTML(source.path)}</code></button>`).join("")}</div>
        ${method.promptHash ? `<p>Executed prompt SHA-256 <code>${escapeHTML(method.promptHash)}</code></p>` : ""}
      </div>
    </section>`;
  }

  function workedExample(example) {
    if (!example) return "";
    return `<section class="g-worked-example g-section">
      <div class="g-section-head"><div><span class="g-kicker">Worked example</span><h2>${escapeHTML(example.title)}</h2></div></div>
      <p class="g-section-intro">${escapeHTML(example.intro)}</p>
      <dl>${example.rows.map((row) => `<div><dt>${escapeHTML(row.label)}</dt><dd>${escapeHTML(row.value)}</dd></div>`).join("")}</dl>
    </section>`;
  }

  function stageContext(stage) {
    return `<section class="g-stage-context" aria-label="Stage ${stage.number} context">
      <div><span>Starts with</span><p>${escapeHTML(stage.startsWith)}</p></div>
      <div><span>What we did</span><p>${escapeHTML(stage.operation)}</p></div>
      <div><span>Produces</span><p>${escapeHTML(stage.produces)}</p></div>
      <div><span>Then</span><p>${escapeHTML(stage.nextStep)}</p></div>
    </section>`;
  }

  function percentage(value) {
    return Number.isFinite(Number(value)) ? `${Number(value).toFixed(1)}%` : "—";
  }

  function modeMeta(modeId) {
    return manifest().selection.modes.find((mode) => mode.id === modeId);
  }

  function latestModeResults() {
    const latest = manifest().selection.latestRound;
    return manifest().selection.roundResults.filter((row) => row.round === latest && row.status === "complete");
  }

  function renderClusteringFunnel() {
    const clustering = manifest().capabilityClustering;
    const maximum = clustering.rounds[0].nodes;
    return `<div class="g-cluster-funnel">
      ${clustering.rounds.map((round) => `
        <article class="g-cluster-step">
          <div class="g-cluster-label"><span>${round.round ? `Round ${round.round}` : "Input"}</span><strong>${fullNumber(round.nodes)}</strong><small>active nodes</small></div>
          <div class="g-cluster-track"><i style="width:${Math.max(18, 100 * round.nodes / maximum)}%"></i></div>
          <div class="g-cluster-split"><span><b>${fullNumber(round.robotNodes)}</b> robot</span><span><b>${fullNumber(round.physicsNodes)}</b> physics</span>${round.round ? `<span><b>−${fullNumber(round.reduction)}</b> this round</span>` : ""}</div>
        </article>`).join("")}
    </div>`;
  }

  function renderModeCards() {
    const results = new Map(latestModeResults().map((row) => [row.mode, row]));
    return `<div class="g-mode-grid">${manifest().selection.modes.map((mode) => {
      const row = results.get(mode.id);
      return `<article class="g-mode-card" style="--mode:${mode.accent}">
        <span>${escapeHTML(mode.label)}</span>
        <strong>${percentage(row?.economicPercent)}</strong>
        <small>economic coverage</small>
        <dl>
          <div><dt>Actions covered</dt><dd>${fullNumber(row?.coveredActions)} · ${percentage(row?.coveredActionPercent)}</dd></div>
          <div><dt>Personal time</dt><dd>${percentage(row?.personalPercent)}</dd></div>
          <div><dt>Strategic minimum</dt><dd>${percentage(row?.strategicMinimumPercent)}</dd></div>
          <div><dt>STEM minimum</dt><dd>${percentage(row?.stemMinimumPercent)}</dd></div>
          <div><dt>SOC minimum</dt><dd>${percentage(row?.socMinimumPercent)}</dd></div>
        </dl>
      </article>`;
    }).join("")}</div>`;
  }

  function renderRoundMatrix() {
    const results = new Map(manifest().selection.roundResults.map((row) => [`${row.round}:${row.mode}`, row]));
    return `<div class="g-round-table-wrap"><table class="g-round-table">
      <thead><tr><th>Capability graph</th>${manifest().selection.modes.map((mode) => `<th style="--mode:${mode.accent}">${escapeHTML(mode.short)}</th>`).join("")}</tr></thead>
      <tbody>${manifest().capabilityClustering.rounds.filter((row) => row.round).map((round) => `<tr>
        <th><span>Round ${round.round}</span><small>${fullNumber(round.nodes)} nodes</small></th>
        ${manifest().selection.modes.map((mode) => {
          const row = results.get(`${round.round}:${mode.id}`);
          return row?.status === "complete"
            ? `<td><strong>${percentage(row.economicPercent)}</strong><span>economy</span><small>${percentage(row.coveredActionPercent)} of actions</small></td>`
            : `<td class="not-run"><strong>—</strong><span>not run</span></td>`;
        }).join("")}
      </tr>`).join("")}</tbody>
    </table></div>`;
  }

  function renderClusteringSummary() {
    const clustering = manifest().capabilityClustering;
    return `<section class="g-section g-clustering-summary">
      <div class="g-section-head"><div><span class="g-kicker">Capability deduplication</span><h2>11,543 active labels → 2,490 capability families</h2></div><a href="#/grounding/data/cluster_round_4_nodes">Inspect round 4 →</a></div>
      <p class="g-section-intro">${escapeHTML(clustering.invariant)} ${escapeHTML(clustering.domainRule)}</p>
      ${renderClusteringFunnel()}
    </section>`;
  }

  function renderOverview() {
    const data = manifest();
    const totals = data.totals;
    const content = `
      <div class="content g-content">
        <header class="g-hero">
          <div class="g-kicker">Robot action-group selection</div>
          <h1>${escapeHTML(data.title)}</h1>
          <p>${escapeHTML(data.subtitle)}</p>
          <div class="g-hero-actions">
            <a class="button primary" href="#/grounding/stage/1">Read Stage 1 <span>→</span></a>
            <a class="button" href="#/grounding/leaderboard">Explore the three portfolios</a>
            <a class="button" href="#/grounding/data">Inspect the data files</a>
          </div>
        </header>

        <section class="g-overview-introduction">
          <div>
            <span class="g-kicker">Why this process exists</span>
            <h2>Start from real activities</h2>
            <p>${escapeHTML(data.goal)}</p>
          </div>
          <div>
            <span class="g-kicker">What is being selected</span>
            <h2>Action groups that supply reusable capabilities</h2>
            <p>${escapeHTML(data.environmentDefinition)}</p>
          </div>
        </section>

        ${stageRail()}

        <section class="g-section g-walkthrough-section">
          <div class="g-section-head">
            <div><span class="g-kicker">One example through all five stages</span><h2>${escapeHTML(data.walkthroughTitle)}</h2></div>
          </div>
          <p class="g-section-intro">${escapeHTML(data.walkthroughIntro)}</p>
          <ol class="g-walkthrough">
            ${data.walkthrough.map((item) => `<li style="--stage:${data.stages[item.stage - 1].accent}"><a href="#/grounding/stage/${item.stage}"><span>${String(item.stage).padStart(2, "0")}</span><div><strong>${escapeHTML(item.label)}</strong><p>${escapeHTML(item.detail)}</p></div><b>→</b></a></li>`).join("")}
          </ol>
        </section>

        <section class="g-section">
          <div class="g-section-head">
            <div><span class="g-kicker">The complete method</span><h2>What happens in each stage</h2></div>
          </div>
          <p class="g-section-intro">Each stage starts with the output of an earlier stage and produces the input for the next one. Open a stage to see every operation, its input and output, a concrete record, and the related data files.</p>
          <div class="g-stage-list">
            ${data.stages.map((stage) => `
              <a class="g-stage-row" href="#/grounding/stage/${stage.number}" style="--stage:${stage.accent}">
                <div class="g-stage-number">${String(stage.number).padStart(2, "0")}</div>
                <div class="g-stage-row-main"><div class="g-kicker">${escapeHTML(stage.title)}</div><h3>${escapeHTML(stage.question)}</h3><p>${escapeHTML(stage.description)}</p></div>
                <div class="g-stage-row-output"><span>Produces</span><p>${escapeHTML(stage.produces)}</p></div>
                <b class="g-stage-row-arrow">→</b>
              </a>`).join("")}
          </div>
        </section>

        <section class="g-section">
          <div class="g-section-head"><div><span class="g-kicker">Recorded pipeline</span><h2>From 52,512 descriptions to 9,363 selectable action groups</h2></div></div>
          <p class="g-section-intro">One source can yield several atomic action occurrences; equivalent occurrences then join one action group. Capability labels are deduplicated separately.</p>
          ${metricCards([
            { value: fullNumber(totals.sourceRows), label: "activity descriptions" },
            { value: fullNumber(totals.rawActions), label: "atomic action occurrences" },
            { value: fullNumber(totals.actionGroups), label: "final action groups" },
            { value: fullNumber(totals.canonicalCapabilities), label: "canonical capability labels" },
          ], "g-overview-metrics")}
        </section>

        <section class="g-section g-clustering-summary">
          <div class="g-section-head"><div><span class="g-kicker">Semantic capability clustering</span><h2>Four rounds, with leaf provenance retained</h2></div><a href="#/grounding/stage/4">Read Stage 4 →</a></div>
          <p class="g-section-intro">${escapeHTML(data.capabilityClustering.invariant)} ${escapeHTML(data.capabilityClustering.domainRule)}</p>
          ${renderClusteringFunnel()}
        </section>

        <section class="g-section g-optimization-overview">
          <div class="g-section-head"><div><span class="g-kicker">Constrained optimization</span><h2>The same 100-slot k1–k5 policy in three capability modes</h2></div><a href="#/grounding/stage/5">Read Stage 5 →</a></div>
          <div class="g-coverage-rule"><span>Coverage rule</span><p>${escapeHTML(data.selection.coverageRule)}</p><small>${escapeHTML(data.selection.supplyRule)}</small></div>
          ${renderModeCards()}
        </section>

        <section class="g-axis-explanation g-section">
          <div>
            <span class="g-kicker">Value model</span>
            <h2>Economic value and personal time remain separate</h2>
            <p>Work value is allocated from O*NET source tasks to their extracted action groups. Everyday-life time is allocated separately from ATUS. Portfolio coverage is then computed through capabilities, not by counting repeated action text.</p>
          </div>
          <div class="g-axis-pair">
            <a href="#/grounding/leaderboard" data-grounding-leaderboard-view="paid-work"><span class="g-axis-icon market">$</span><strong>Economic value</strong><small>allocated annual U.S. dollars</small></a>
            <span class="g-not-equal">≠</span>
            <a href="#/grounding/leaderboard" data-grounding-leaderboard-view="everyday-life"><span class="g-axis-icon life">h</span><strong>Everyday life</strong><small>annual U.S. population-hours</small></a>
          </div>
        </section>

        <section class="g-section">
          <div class="g-section-head"><div><span class="g-kicker">Reference</span><h2>Terms used on these pages</h2></div></div>
          <p class="g-section-intro">The pages define each term when it first appears. This list is a quick reference.</p>
          ${glossary(data.glossary)}
        </section>

        <section class="g-section">
          <div class="g-section-head"><div><span class="g-kicker">Documents</span><h2>Full method and data guides</h2></div></div>
          <p class="g-section-intro">These files describe the methodology, calculations, data releases, and selection results in full.</p>
          <div class="g-document-grid">${data.documents.map(documentCard).join("")}</div>
        </section>

        <section class="g-method-status g-section">
          <div class="g-section-head"><div><span class="g-kicker">Status of this work</span><h2>Scope of this release</h2></div></div>
          <div><span>Completed here</span><p>${escapeHTML(data.executionStatus)}</p></div>
          <div><span>Known modeling boundary</span><p>${escapeHTML(data.methodBoundary)}</p></div>
        </section>
      </div>`;
    app.innerHTML = shell(content, "grounding");
  }

  function renderStage(number) {
    const stage = stageByNumber(number);
    if (!stage) return renderNotFound("Stage not found", "#/grounding");
    const dataById = new Map(manifest().datasets.map((item) => [item.id, item]));
    const previous = stage.number > 1 ? stageByNumber(stage.number - 1) : null;
    const next = stage.number < 5 ? stageByNumber(stage.number + 1) : null;
    const clusteringExtra = stage.number === 4 ? renderClusteringSummary() : "";
    const selectionExtra = stage.number === 5 ? renderSelectionSummary() : "";
    const content = `
      <div class="content g-content" style="--stage:${stage.accent}">
        <a class="back-link" href="#/grounding">← Activity-selection overview</a>
        <header class="g-stage-hero">
          <div class="g-stage-big-number">${String(stage.number).padStart(2, "0")}</div>
          <div>
            <div class="g-kicker">${escapeHTML(stage.eyebrow)}</div>
            <h1>${escapeHTML(stage.title)}</h1>
            <strong class="g-stage-question">${escapeHTML(stage.question)}</strong>
            <p>${escapeHTML(stage.description)}</p>
          </div>
        </header>
        ${stageRail(stage.number)}
        ${stageContext(stage)}
        ${workedExample(stage.workedExample)}
        <section class="g-section">
          <div class="g-section-head"><div><span class="g-kicker">Step-by-step method</span><h2>What we did in Stage ${stage.number}</h2></div></div>
          <p class="g-section-intro">Every step identifies its input, operation, recorded decision method, output, related artifacts, and the ${escapeHTML(manifest().exampleLabel)} example.</p>
          <div class="g-substeps">
            ${stage.substeps.map((substep) => {
              const datasets = substep.datasets.map((id) => dataById.get(id)).filter(Boolean);
              return `<article class="g-substep">
                <div class="g-substep-index">${escapeHTML(substep.id)}</div>
                <div class="g-substep-body">
                  <h3>${escapeHTML(substep.title)}</h3>
                  <div class="g-step-operation"><span>What we did</span><p>${escapeHTML(substep.description)}</p></div>
                  ${decisionMethod(substep.decisionMethod)}
                  <dl class="g-step-io">
                    <div><dt>What came in</dt><dd>${escapeHTML(substep.input)}</dd></div>
                    <div><dt>What came out</dt><dd>${escapeHTML(substep.output)}</dd></div>
                  </dl>
                  <div class="g-step-example"><span>${escapeHTML(manifest().exampleLabel)} example</span><p>${escapeHTML(substep.example)}</p></div>
                  <details class="g-substep-data">
                    <summary>Inspect ${datasets.length} related data ${datasets.length === 1 ? "file" : "files"}<span>Row counts are shown for each file</span></summary>
                    <div class="g-substep-datasets">${datasets.map((dataset) => datasetCard(dataset, true)).join("")}</div>
                  </details>
                </div>
              </article>`;
            }).join("")}
          </div>
        </section>
        <section class="g-stage-result g-section">
          <div class="g-section-head"><div><span class="g-kicker">Result of Stage ${stage.number}</span><h2>${escapeHTML(stage.title)}</h2></div></div>
          <p>${escapeHTML(stage.result)}</p>
          ${metricCards(stage.metrics, "g-stage-metrics")}
        </section>
        ${clusteringExtra}
        ${selectionExtra}
        <section class="g-section">
          <div class="g-section-head"><div><span class="g-kicker">Reference</span><h2>Terms used in Stage ${stage.number}</h2></div></div>
          ${glossary(stage.terms)}
        </section>
        <section class="g-method-note">
          <span>How these decisions were made</span><p>${escapeHTML(stage.executionNote)}</p>
        </section>
        <nav class="g-stage-pagination" aria-label="Adjacent activity-selection stages">
          ${previous ? `<a href="#/grounding/stage/${previous.number}"><small>Previous stage</small><strong>← ${escapeHTML(previous.title)}</strong></a>` : `<a href="#/grounding"><small>Overview</small><strong>← Activity-selection method</strong></a>`}
          ${next ? `<a class="next" href="#/grounding/stage/${next.number}"><small>Next stage</small><strong>${escapeHTML(next.title)} →</strong></a>` : `<a class="next" href="#/grounding/leaderboard"><small>Selection results</small><strong>Action portfolios →</strong></a>`}
        </nav>
      </div>`;
    app.innerHTML = shell(content, "grounding");
  }

  function renderSelectionSummary() {
    const selection = manifest().selection;
    return `<section class="g-selection-summary g-section">
      <div class="g-section-head"><div><span class="g-kicker">Frozen optimization protocol</span><h2>100 slots across six ordered k1–k5 tiers</h2></div><a href="#/grounding/leaderboard">Explore action portfolios →</a></div>
      <p class="g-section-intro">Each mode uses the same candidates, values, tier budgets, and deterministic solver settings. Only the capability domain used to define coverage changes.</p>
      <div class="g-tier-bar">${selection.tierBudgets.map((tier) => `<span style="--tier:${tier.accent};--grow:${tier.count}" title="${escapeHTML(tier.label)}: ${tier.count}"><b>${tier.count}</b></span>`).join("")}</div>
      <div class="g-tier-legend">${selection.tierBudgets.map((tier) => `<span><i style="--tier:${tier.accent}"></i><b>${escapeHTML(tier.short)} · ${escapeHTML(tier.label)}</b> · ${tier.count}</span>`).join("")}</div>
      <div class="g-coverage-rule"><span>Exact coverage predicate</span><p>${escapeHTML(selection.coverageRule)}</p><small>${escapeHTML(selection.supplyRule)}</small></div>
      <div class="g-section-head g-inline-head"><div><span class="g-kicker">Latest complete graph</span><h2>Round-4 portfolio coverage</h2></div></div>
      ${renderModeCards()}
      <div class="g-section-head g-inline-head"><div><span class="g-kicker">Ablation history</span><h2>Coverage as capability labels merge</h2></div></div>
      ${renderRoundMatrix()}
      <p class="g-selection-axis-note">${escapeHTML(selection.axisWarning)}</p>
      <p class="g-selection-axis-note">${escapeHTML(selection.solver)}</p>
    </section>`;
  }

  function renderDataRegistry() {
    const datasets = manifest().datasets;
    const content = `
      <div class="content g-content">
        <header class="topline g-page-header">
          <div><div class="g-kicker">Pipeline data files</div><h1 class="page-title">Recorded inputs and outputs</h1><p class="page-subtitle">These ${datasets.length} registered artifacts expose the five-stage pipeline. Their row counts sum to ${fullNumber(manifest().totals.inspectableRows)} because the same source, action, or capability appears in multiple transformations.</p></div>
          <div class="header-actions"><a class="button" href="#/grounding">Method overview</a><a class="button primary" href="#/grounding/leaderboard">Action portfolios</a></div>
        </header>
        <div class="g-registry-toolbar">
          <label class="search-wrap"><span class="search-icon">⌕</span><input id="g-registry-search" class="search" type="search" placeholder="Search file names and descriptions…" autocomplete="off" /></label>
          <select id="g-registry-stage" class="select" aria-label="Filter files by stage"><option value="All">All five stages</option>${manifest().stages.map((stage) => `<option value="${stage.number}">Stage ${stage.number} · ${escapeHTML(stage.shortTitle)}</option>`).join("")}</select>
        </div>
        <div id="g-registry-results" class="g-registry-results">${renderRegistryResults(datasets)}</div>
      </div>`;
    app.innerHTML = shell(content, "grounding");
  }

  function renderRegistryResults(datasets) {
    const manifestOrder = new Map(manifest().datasets.map((item, index) => [item.id, index]));
    const ordered = [...datasets].sort((left, right) => left.stage - right.stage || left.substep.localeCompare(right.substep, undefined, { numeric: true }) || manifestOrder.get(left.id) - manifestOrder.get(right.id));
    return manifest().stages.map((stage) => {
      const items = ordered.filter((item) => item.stage === stage.number);
      if (!items.length) return "";
      const rows = items.reduce((sum, item) => sum + item.rowCount, 0);
      return `<section class="g-registry-stage" style="--stage:${stage.accent}">
        <div class="g-registry-stage-head">
          <div><span class="g-kicker">Stage ${stage.number}</span><h2>${escapeHTML(stage.title)}</h2><p>${escapeHTML(stage.produces)}</p></div>
          <span>${items.length} ${items.length === 1 ? "file" : "files"} · ${fullNumber(rows)} rows across files</span>
        </div>
        <div class="g-dataset-grid">${items.map((item) => datasetCard(item)).join("")}</div>
      </section>`;
    }).join("");
  }

  function filterRegistry() {
    const query = document.querySelector("#g-registry-search")?.value.trim().toLowerCase() || "";
    const stage = document.querySelector("#g-registry-stage")?.value || "All";
    const datasets = manifest().datasets.filter((item) => {
      const inStage = stage === "All" || String(item.stage) === stage;
      const text = [item.title, item.description, item.path, item.substep, ...item.columns, ...item.tags].join(" ").toLowerCase();
      return inStage && (!query || text.includes(query));
    });
    const region = document.querySelector("#g-registry-results");
    if (region) region.innerHTML = datasets.length ? renderRegistryResults(datasets) : `<div class="empty"><strong>No files match.</strong>Clear a filter or try a broader search.</div>`;
  }

  function touchCache(id, rows) {
    cache.delete(id);
    cache.set(id, rows);
    while (cache.size > DATASET_CACHE_LIMIT) cache.delete(cache.keys().next().value);
  }

  async function decodedText(response, compressed) {
    if (!compressed) return response.text();
    if (!("DecompressionStream" in globalThis)) throw new Error("This browser cannot decompress gzip data. Download the source file instead.");
    const bytes = await response.arrayBuffer();
    const signature = new Uint8Array(bytes, 0, Math.min(2, bytes.byteLength));
    // Some static hosts transparently decode .gz responses. Only decompress
    // when the body still carries the gzip magic bytes.
    if (signature[0] !== 0x1f || signature[1] !== 0x8b) {
      return new TextDecoder().decode(bytes);
    }
    const stream = new Blob([bytes]).stream().pipeThrough(new DecompressionStream("gzip"));
    return new Response(stream).text();
  }

  function parseCSV(text) {
    const table = [];
    let row = [];
    let field = "";
    let quoted = false;
    for (let index = 0; index < text.length; index += 1) {
      const char = text[index];
      if (quoted) {
        if (char === '"' && text[index + 1] === '"') { field += '"'; index += 1; }
        else if (char === '"') quoted = false;
        else field += char;
      } else if (char === '"') quoted = true;
      else if (char === ",") { row.push(field); field = ""; }
      else if (char === "\n") { row.push(field.replace(/\r$/, "")); table.push(row); row = []; field = ""; }
      else field += char;
    }
    if (field || row.length) { row.push(field.replace(/\r$/, "")); table.push(row); }
    const headers = table.shift() || [];
    return table.filter((values) => values.some((value) => value !== "")).map((values) => Object.fromEntries(headers.map((header, index) => [header.replace(/^\uFEFF/, ""), values[index] ?? ""])));
  }

  function atPath(value, path) {
    return path.reduce((current, key) => (current && typeof current === "object" ? current[key] : undefined), value);
  }

  async function loadDataset(spec) {
    if (cache.has(spec.id)) {
      const rows = cache.get(spec.id);
      touchCache(spec.id, rows);
      return rows;
    }
    if (loads.has(spec.id)) return loads.get(spec.id);
    const promise = (async () => {
      const response = await fetch(assetUrl(spec.path), { cache: "force-cache" });
      if (!response.ok) throw new Error(`Dataset download failed (${response.status})`);
      const text = await decodedText(response, spec.format === "jsonl_gz");
      let rows;
      if (spec.format === "csv") rows = parseCSV(text);
      else if (spec.format === "jsonl_gz") rows = text.split(/\r?\n/).filter(Boolean).map((line) => JSON.parse(line));
      else {
        const value = atPath(JSON.parse(text), spec.rootPath || []);
        rows = Array.isArray(value) ? value : value === undefined || value === null ? [] : [value];
      }
      touchCache(spec.id, rows);
      return rows;
    })().finally(() => loads.delete(spec.id));
    loads.set(spec.id, promise);
    return promise;
  }

  function prepareDatasetView(spec) {
    if (datasetView.id === spec.id) return;
    Object.assign(datasetView, {
      id: spec.id,
      query: "",
      facetField: "",
      facetValue: "",
      sort: spec.defaultSort || "",
      direction: spec.defaultDirection || "asc",
      page: 1,
      pageSize: 50,
    });
  }

  function renderDataset(id) {
    const spec = datasetById(id);
    if (!spec) return renderNotFound("Pipeline file not found", "#/grounding/data", "Return to the pipeline data");
    prepareDatasetView(spec);
    if (!cache.has(spec.id)) {
      const content = datasetHeader(spec, `<div class="g-data-loading"><div class="loading-mark"></div><strong>Loading ${fullNumber(spec.rowCount)} rows</strong><span>${fileSize(spec.bytes)} · ${escapeHTML(formatLabel(spec.format))}</span></div>`);
      app.innerHTML = shell(content, "grounding");
      loadDataset(spec)
        .then((rows) => {
          if (rows.length !== spec.rowCount) throw new Error(`Expected ${fullNumber(spec.rowCount)} rows but decoded ${fullNumber(rows.length)}`);
          if (location.hash === `#/grounding/data/${encodeURIComponent(spec.id)}` || location.hash === `#/grounding/data/${spec.id}`) renderDataset(spec.id);
        })
        .catch((error) => {
          if (!location.hash.includes(`/grounding/data/${spec.id}`)) return;
          app.innerHTML = shell(datasetHeader(spec, `<div class="empty"><strong>This pipeline file could not be loaded.</strong><a href="${assetUrl(spec.path)}" download>Download the file instead</a><details><summary>Technical details</summary><code>${escapeHTML(error.message)}</code></details></div>`), "grounding");
        });
      return;
    }
    const rows = cache.get(spec.id);
    const result = filterAndSortDataset(spec, rows);
    const totalPages = Math.max(1, Math.ceil(result.length / datasetView.pageSize));
    datasetView.page = Math.min(datasetView.page, totalPages);
    const start = (datasetView.page - 1) * datasetView.pageSize;
    visibleDatasetRows = result.slice(start, start + datasetView.pageSize);
    const table = renderDatasetTable(spec, visibleDatasetRows);
    const content = datasetHeader(spec, `
      <div class="g-data-toolbar">
          <label class="search-wrap"><span class="search-icon">⌕</span><input id="g-data-search" class="search" type="search" value="${escapeHTML(datasetView.query)}" placeholder="Search all fields in ${fullNumber(rows.length)} rows…" autocomplete="off" /></label>
        ${renderFacetControls(spec, rows)}
        <select id="g-data-page-size" class="select" aria-label="Rows per page">${PAGE_SIZES.map((size) => `<option value="${size}" ${datasetView.pageSize === size ? "selected" : ""}>${size} rows</option>`).join("")}</select>
      </div>
      <div class="g-table-status"><span><strong>${fullNumber(result.length)}</strong> matching rows</span><span>Showing ${result.length ? fullNumber(start + 1) : 0}–${fullNumber(Math.min(start + datasetView.pageSize, result.length))} · select a row to view all fields</span></div>
      ${table}
      ${pagination(datasetView.page, totalPages, "dataset")}
    `);
    app.innerHTML = shell(content, "grounding");
  }

  function datasetHeader(spec, body) {
    const stage = stageByNumber(spec.stage);
    const substep = stage?.substeps.find((item) => item.id === spec.substep);
    return `<div class="content g-content" style="--stage:${stage?.accent || "#d7f764"}">
      <div class="g-data-breadcrumbs"><a href="#/grounding/data">Pipeline data</a><span>/</span><a href="#/grounding/stage/${spec.stage}">Stage ${spec.stage}</a><span>/</span><b>${escapeHTML(spec.title)}</b></div>
      <header class="g-dataset-hero">
        <div><div class="g-kicker">Stage ${spec.stage}, step ${escapeHTML(spec.substep)}${substep ? ` · ${escapeHTML(substep.title)}` : ""}</div><h1>${escapeHTML(spec.title)}</h1><p>${escapeHTML(spec.description)}</p></div>
        <a class="button" href="${assetUrl(spec.path)}" download>Download this pipeline file <span>↓</span></a>
      </header>
      <section class="g-dataset-context">
        <div><span>What one row represents</span><p>${escapeHTML(spec.rowMeaning)}</p></div>
        <div><span>Why this file exists</span><p>${substep ? `This file contains records used or produced by Step ${escapeHTML(substep.id)}: ${escapeHTML(substep.title)}.` : `This file contains records from Stage ${spec.stage}.`}</p></div>
      </section>
      <details class="g-file-details">
        <summary>File details</summary>
        <div class="g-dataset-meta"><span><b>${fullNumber(spec.rowCount)}</b> rows</span><span><b>${fileSize(spec.bytes)}</b> file size</span><span><b>${escapeHTML(formatLabel(spec.format))}</b> format</span><span><b>${spec.columns.length}</b> displayed columns</span></div>
        <div class="g-path"><span>Repository file</span><code>${escapeHTML(spec.path)}</code></div>
      </details>
      ${body}
    </div>`;
  }

  function normalizedFacetValues(value) {
    if (Array.isArray(value)) return value.flatMap(normalizedFacetValues);
    if (value === null || value === undefined || value === "") return ["(empty)"];
    return [plainValue(value)];
  }

  function facetValues(spec, rows, field) {
    if (!field) return [];
    const key = `${spec.id}:${field}`;
    if (facetCache.has(key)) return facetCache.get(key);
    const counts = new Map();
    rows.forEach((row) => normalizedFacetValues(row[field]).forEach((value) => counts.set(value, (counts.get(value) || 0) + 1)));
    const values = [...counts].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0], undefined, { numeric: true })).slice(0, 500);
    facetCache.set(key, values);
    return values;
  }

  function renderFacetControls(spec, rows) {
    if (!spec.facets.length) return "";
    const values = facetValues(spec, rows, datasetView.facetField);
    return `<select id="g-data-facet-field" class="select" aria-label="Filter field"><option value="">Choose a filter field</option>${spec.facets.map((field) => `<option value="${escapeHTML(field)}" ${datasetView.facetField === field ? "selected" : ""}>${escapeHTML(fieldLabel(field))}</option>`).join("")}</select>
      ${datasetView.facetField ? `<select id="g-data-facet-value" class="select" aria-label="Filter value"><option value="">Choose a value</option>${values.map(([value, count]) => `<option value="${escapeHTML(value)}" ${datasetView.facetValue === value ? "selected" : ""}>${escapeHTML(displayScalar(value, datasetView.facetField))} (${fullNumber(count)})</option>`).join("")}</select>` : ""}`;
  }

  function compareValues(left, right) {
    if (left === right) return 0;
    if (left === null || left === undefined || left === "") return 1;
    if (right === null || right === undefined || right === "") return -1;
    const a = plainValue(left);
    const b = plainValue(right);
    const numericPattern = /^-?\d+(?:\.\d+)?$/;
    if (numericPattern.test(a) && numericPattern.test(b)) return Number(a) - Number(b);
    return a.localeCompare(b, undefined, { numeric: true, sensitivity: "base" });
  }

  function filterAndSortDataset(spec, rows) {
    const query = datasetView.query.trim().toLowerCase();
    const filtered = rows.filter((row) => {
      if (datasetView.facetField && datasetView.facetValue) {
        const values = normalizedFacetValues(row[datasetView.facetField]);
        if (!values.includes(datasetView.facetValue)) return false;
      }
      if (!query) return true;
      return JSON.stringify(row).toLowerCase().includes(query);
    });
    if (datasetView.sort) {
      const direction = datasetView.direction === "desc" ? -1 : 1;
      filtered.sort((a, b) => direction * compareValues(a[datasetView.sort], b[datasetView.sort]));
    }
    return filtered;
  }

  function renderDatasetTable(spec, rows) {
    const columns = spec.columns;
    if (!rows.length) {
      const filtered = Boolean(datasetView.query || datasetView.facetField || datasetView.facetValue);
      return filtered
        ? `<div class="empty"><strong>No rows match those filters.</strong>Clear the search or choose another filter value.</div>`
        : `<div class="empty"><strong>This pipeline file contains 0 rows.</strong>The automated screen produced zero records for this category.</div>`;
    }
    return `<div class="g-table-wrap"><table class="g-table"><thead><tr><th class="g-row-number">Row</th>${columns.map((column) => `<th><button data-g-dataset-sort="${escapeHTML(column)}" class="${datasetView.sort === column ? "active" : ""}">${escapeHTML(fieldLabel(column))}${datasetView.sort === column ? (datasetView.direction === "asc" ? " ↑" : " ↓") : ""}</button></th>`).join("")}</tr></thead><tbody>${rows.map((row, index) => `<tr tabindex="0" data-g-dataset-row="${index}"><td class="g-row-number">${fullNumber((datasetView.page - 1) * datasetView.pageSize + index + 1)}</td>${columns.map((column) => `<td>${briefValue(row[column], column, row)}</td>`).join("")}</tr>`).join("")}</tbody></table></div>`;
  }

  function pagination(page, totalPages, kind) {
    if (totalPages <= 1) return "";
    const start = Math.max(1, Math.min(page - 2, totalPages - 4));
    const pages = Array.from({ length: Math.min(5, totalPages) }, (_, index) => start + index);
    return `<nav class="g-pagination" aria-label="Table pagination"><button data-g-${kind}-page="${page - 1}" ${page === 1 ? "disabled" : ""}>← Previous</button><div>${pages.map((value) => `<button data-g-${kind}-page="${value}" class="${value === page ? "active" : ""}">${value}</button>`).join("")}</div><span>of ${fullNumber(totalPages)}</span><button data-g-${kind}-page="${page + 1}" ${page === totalPages ? "disabled" : ""}>Next →</button></nav>`;
  }

  async function loadLeaderboard() {
    if (leaderboardRows) return leaderboardRows;
    if (leaderboardLoad) return leaderboardLoad;
    leaderboardLoad = (async () => {
      const url = staticMode ? (portalConfig.groundingLeaderboardUrl || "./grounding-leaderboard.json.gz") : "/api/grounding/leaderboard";
      const response = await fetch(url, { cache: "force-cache" });
      if (!response.ok) throw new Error(`Leaderboard download failed (${response.status})`);
      const text = await decodedText(response, staticMode || url.endsWith(".gz"));
      const payload = JSON.parse(text);
      if (!Array.isArray(payload.rows) || payload.rows.length !== manifest().leaderboard.expectedRows) throw new Error("Action-group explorer integrity check failed");
      leaderboardRows = payload.rows;
      return leaderboardRows;
    })().finally(() => { leaderboardLoad = null; });
    return leaderboardLoad;
  }

  function tierShort(id) {
    return manifest().selection.tierBudgets.find((tier) => tier.id === id)?.label || "—";
  }

  function activeSelection(row) {
    return row.selection_by_mode?.[leaderboardView.mode] || {};
  }

  function activeCoverage(row) {
    return row.coverage_by_mode?.[leaderboardView.mode] || {};
  }

  function selectedDatasetId() {
    if (leaderboardView.mode === "physics_only") return "round_4_physics_selected";
    if (leaderboardView.mode === "physics_plus_robotics") return "round_4_combined_selected";
    return "round_4_robotics_selected";
  }

  function leaderboardFieldValue(row, field) {
    const selection = activeSelection(row);
    const coverage = activeCoverage(row);
    if (field === "selection_order") return selection.sequence;
    if (field === "portfolio_status") return selection.selected ? 1 : 0;
    if (field === "coverage_status") return coverage.covered ? 1 : 0;
    if (field === "missing_requirement_count") return coverage.missingRequirementCount;
    if (field === "tier") return selection.tier;
    return row[field];
  }

  function leaderboardDefaultSort() {
    if (leaderboardView.view === "selected") return ["selection_order", "asc"];
    if (leaderboardView.view === "paid-work") return ["market_work_rank", "asc"];
    if (leaderboardView.view === "everyday-life") return ["everyday_life_rank", "asc"];
    if (leaderboardView.view === "covered") return ["market_work_economic_value_usd", "desc"];
    if (leaderboardView.view === "uncovered") return ["market_work_economic_value_usd", "desc"];
    return ["action_group_index", "asc"];
  }

  function filterAndSortLeaderboard() {
    const query = leaderboardView.query.trim().toLowerCase();
    let rows = leaderboardRows.filter((row) => {
      const selection = activeSelection(row);
      const coverage = activeCoverage(row);
      if (leaderboardView.view === "selected" && !selection.selected) return false;
      if (leaderboardView.view === "covered" && !coverage.covered) return false;
      if (leaderboardView.view === "uncovered" && (selection.selected || coverage.covered)) return false;
      if (leaderboardView.view === "paid-work" && !row.market_work_rank) return false;
      if (leaderboardView.view === "everyday-life" && !row.everyday_life_rank) return false;
      if (leaderboardView.status === "selected" && !selection.selected) return false;
      if (leaderboardView.status === "covered" && !coverage.covered) return false;
      if (leaderboardView.status === "uncovered" && coverage.covered) return false;
      if (leaderboardView.status === "eligible" && !row.selection_eligible) return false;
      if (leaderboardView.status === "ineligible" && row.selection_eligible) return false;
      if (leaderboardView.tier !== "All" && selection.tier !== leaderboardView.tier) return false;
      if (!query) return true;
      return [
        row.action_group_id,
        row.representative_action,
        row.group_origin,
        row.eligibility_category,
        ...(row.robot_capabilities || []).flatMap((item) => [item.id, item.name]),
        ...(row.physics_capabilities || []).flatMap((item) => [item.id, item.name]),
        ...(coverage.missingRequirements || []).flatMap((item) => [item.id, item.name]),
      ].join(" ").toLowerCase().includes(query);
    });
    const [field, defaultDirection] = leaderboardView.sort
      ? [leaderboardView.sort, leaderboardView.direction]
      : leaderboardDefaultSort();
    const direction = defaultDirection === "desc" ? -1 : 1;
    rows = [...rows].sort((a, b) => direction * compareValues(
      leaderboardFieldValue(a, field),
      leaderboardFieldValue(b, field),
    ));
    return rows;
  }

  function requirementPreview(items) {
    if (!items?.length) return `<span class="g-null">None</span>`;
    return `<span class="g-capability-preview"><b>${items.length}</b><span>${items.slice(0, 2).map((item) => escapeHTML(item.name)).join(" · ")}</span>${items.length > 2 ? `<small>+${items.length - 2} more</small>` : ""}</span>`;
  }

  function renderLeaderboardTable(rows) {
    const firstField = leaderboardView.view === "selected"
      ? "selection_order"
      : leaderboardView.view === "paid-work"
        ? "market_work_rank"
        : leaderboardView.view === "everyday-life"
          ? "everyday_life_rank"
          : "action_group_index";
    const firstLabel = leaderboardView.view === "selected"
      ? "Portfolio order"
      : ["paid-work", "everyday-life"].includes(leaderboardView.view)
        ? "Rank"
        : "Group";
    const columns = [
      [firstField, firstLabel],
      ["representative_action", "Action group"],
      ["portfolio_status", "Portfolio"],
      ["coverage_status", "Capability coverage"],
      ["robot_capability_count", "Robot requirements"],
      ["physics_capability_count", "Physics requirements"],
      ["market_work_economic_value_usd", "Economic value"],
      ["everyday_life_annual_population_hours", "Personal time"],
    ];
    if (!rows.length) return `<div class="empty"><strong>No action groups match those filters.</strong>Clear a filter or choose another view.</div>`;
    return `<div class="g-table-wrap"><table class="g-table g-leaderboard-table"><thead><tr>${columns.map(([field, label]) => `<th><button data-g-leaderboard-sort="${field}" class="${leaderboardView.sort === field ? "active" : ""}">${escapeHTML(label)}${leaderboardView.sort === field ? (leaderboardView.direction === "asc" ? " ↑" : " ↓") : ""}</button></th>`).join("")}</tr></thead><tbody>${rows.map((row, index) => {
      const selection = activeSelection(row);
      const coverage = activeCoverage(row);
      const first = leaderboardView.view === "selected"
        ? `<strong class="g-order">${String(selection.sequence).padStart(3, "0")}</strong>`
        : leaderboardView.view === "paid-work"
          ? `#${fullNumber(row.market_work_rank)}`
          : leaderboardView.view === "everyday-life"
            ? `#${fullNumber(row.everyday_life_rank)}`
            : `<code>${fullNumber(row.action_group_index)}</code>`;
      return `<tr tabindex="0" data-g-leaderboard-row="${index}">
        <td>${first}</td>
        <td><strong>${escapeHTML(row.representative_action)}</strong><small>${fullNumber(row.action_occurrence_count)} occurrence${Number(row.action_occurrence_count) === 1 ? "" : "s"} · ${escapeHTML(row.action_group_id.split(":").pop().slice(0, 10))}</small></td>
        <td>${selection.selected ? `<span class="g-status selected">${escapeHTML(tierShort(selection.tier))}</span><small>order ${selection.sequence}</small>` : `<span class="g-status">Not selected</span>`}</td>
        <td>${coverage.covered ? `<span class="g-status covered">Covered</span><small>${fullNumber(coverage.activeRequirementCount)} active requirements</small>` : `<span class="g-status gap">Missing ${fullNumber(coverage.missingRequirementCount)}</span><small>${(coverage.missingRequirements || []).slice(0, 2).map((item) => escapeHTML(item.name)).join(" · ") || "No active-mode supplier"}</small>`}</td>
        <td>${requirementPreview(row.robot_capabilities)}</td>
        <td>${requirementPreview(row.physics_capabilities)}</td>
        <td><strong>${weight(row.market_work_economic_value_usd, "market")}</strong><small>${row.market_work_rank ? `rank #${fullNumber(row.market_work_rank)}` : "no positive estimate"}</small></td>
        <td><strong>${weight(row.everyday_life_annual_population_hours, "life")}</strong><small>${row.everyday_life_rank ? `rank #${fullNumber(row.everyday_life_rank)}` : "no positive estimate"}</small></td>
      </tr>`;
    }).join("")}</tbody></table></div>`;
  }

  function renderLeaderboard() {
    const expected = manifest().leaderboard.expectedRows;
    const selectedMode = modeMeta(leaderboardView.mode) || manifest().selection.modes[0];
    if (!leaderboardRows) {
      const content = `<div class="content g-content"><a class="back-link" href="#/grounding">← Selection overview</a><header class="g-leaderboard-hero"><div class="g-kicker">Output of Stage 5</div><h1>${fullNumber(expected)} action groups</h1><p>Loading selection and coverage results for all three capability modes.</p></header><div class="g-data-loading"><div class="loading-mark"></div><strong>Loading ${fullNumber(expected)} action groups</strong><span>Joining values, eligibility, requirements, selections, and missing-capability audits.</span></div></div>`;
      app.innerHTML = shell(content, "grounding");
      loadLeaderboard().then(() => {
        if (location.hash.startsWith("#/grounding/leaderboard")) renderLeaderboard();
      }).catch((error) => {
        if (location.hash.startsWith("#/grounding/leaderboard")) app.innerHTML = shell(`<div class="content g-content"><div class="empty"><strong>The action-group explorer could not be loaded.</strong><details><summary>Technical details</summary><code>${escapeHTML(error.message)}</code></details></div></div>`, "grounding");
      });
      return;
    }
    const result = filterAndSortLeaderboard();
    const totalPages = Math.max(1, Math.ceil(result.length / leaderboardView.pageSize));
    leaderboardView.page = Math.min(leaderboardView.page, totalPages);
    const start = (leaderboardView.page - 1) * leaderboardView.pageSize;
    visibleLeaderboardRows = result.slice(start, start + leaderboardView.pageSize);
    const tiers = manifest().selection.tierBudgets;
    const selectedCount = leaderboardRows.filter((row) => activeSelection(row).selected).length;
    const coveredCount = leaderboardRows.filter((row) => activeCoverage(row).covered).length;
    const content = `
      <div class="content g-content">
        <a class="back-link" href="#/grounding">← Selection overview</a>
        <header class="g-leaderboard-hero">
          <div><div class="g-kicker">Round ${manifest().selection.latestRound} · ${escapeHTML(selectedMode.label)}</div><h1>${fullNumber(expected)} action groups</h1><p>Inspect what the selected 100 supply, which target actions they cover, and the exact capability gaps for every uncovered action.</p></div>
          <a class="button" href="#/grounding/data/${selectedDatasetId()}">Inspect selected rows →</a>
        </header>
        <section class="g-mode-switcher">
          <div><span>Capability mode</span><strong>${escapeHTML(selectedMode.label)}</strong><p>${escapeHTML(selectedMode.description)}</p></div>
          <select id="g-leaderboard-mode" class="select" aria-label="Capability mode">${manifest().selection.modes.map((mode) => `<option value="${mode.id}" ${leaderboardView.mode === mode.id ? "selected" : ""}>${escapeHTML(mode.label)}</option>`).join("")}</select>
        </section>
        <section class="g-leaderboard-guide">
          <div><span>Portfolio</span><p><strong>${fullNumber(selectedCount)}</strong> action groups selected through k1–k5.</p></div>
          <div><span>Covered targets</span><p><strong>${fullNumber(coveredCount)}</strong> of ${fullNumber(expected)} satisfy every active-mode requirement.</p></div>
          <div><span>Coverage is not identity</span><p>One selected action may cover many other actions by supplying their required capabilities.</p></div>
          <div><span>Audit every gap</span><p>Each uncovered row lists the requirements not supplied at the required level.</p></div>
        </section>
        <div class="g-leaderboard-views" role="tablist">${manifest().leaderboard.views.map((view) => `<button role="tab" data-g-leaderboard-view="${view.id}" class="${leaderboardView.view === view.id ? "active" : ""}"><strong>${escapeHTML(view.label)}</strong><small>${escapeHTML(view.description)}</small></button>`).join("")}</div>
        <div class="g-data-toolbar g-leaderboard-toolbar">
          <label class="search-wrap"><span class="search-icon">⌕</span><input id="g-leaderboard-search" class="search" type="search" value="${escapeHTML(leaderboardView.query)}" placeholder="Search actions, capability labels, or IDs…" autocomplete="off" /></label>
          <select id="g-leaderboard-status" class="select" aria-label="Selection or coverage status"><option value="All">Any status</option><option value="selected" ${leaderboardView.status === "selected" ? "selected" : ""}>Selected</option><option value="covered" ${leaderboardView.status === "covered" ? "selected" : ""}>Covered</option><option value="uncovered" ${leaderboardView.status === "uncovered" ? "selected" : ""}>Uncovered</option><option value="eligible" ${leaderboardView.status === "eligible" ? "selected" : ""}>Selection eligible</option><option value="ineligible" ${leaderboardView.status === "ineligible" ? "selected" : ""}>Quarantined</option></select>
          <select id="g-leaderboard-tier" class="select" aria-label="Selection tier"><option value="All">All k1–k5 tiers</option>${tiers.map((tier) => `<option value="${tier.id}" ${leaderboardView.tier === tier.id ? "selected" : ""}>${escapeHTML(tier.short)} · ${escapeHTML(tier.label)}</option>`).join("")}</select>
          <select id="g-leaderboard-page-size" class="select" aria-label="Rows per page">${PAGE_SIZES.map((size) => `<option value="${size}" ${leaderboardView.pageSize === size ? "selected" : ""}>${size} rows</option>`).join("")}</select>
        </div>
        <div class="g-table-status"><span><strong>${fullNumber(result.length)}</strong> matching action groups</span><span>Showing ${result.length ? fullNumber(start + 1) : 0}–${fullNumber(Math.min(start + leaderboardView.pageSize, result.length))} · select a row for its complete capability audit</span></div>
        ${renderLeaderboardTable(visibleLeaderboardRows)}
        ${pagination(leaderboardView.page, totalPages, "leaderboard")}
      </div>`;
    app.innerHTML = shell(content, "grounding");
  }

  function renderNotFound(message, back, backLabel = "Return to the activity-selection overview") {
    app.innerHTML = shell(`<div class="content g-content"><div class="empty"><strong>${escapeHTML(message)}</strong><a href="${back}">${escapeHTML(backLabel)}</a></div></div>`, "grounding");
  }

  function openRecord(title, record, contextLines = []) {
    const entries = Object.entries(record);
    const isStructured = ([, value]) => value && typeof value === "object" && (!Array.isArray(value) || value.some((item) => item && typeof item === "object"));
    const ordinary = entries.filter((entry) => !isStructured(entry));
    const structured = entries.filter(isStructured);
    const fields = ordinary.map(([key, value]) => `<div class="g-record-field"><dt>${escapeHTML(fieldLabel(key))}</dt><dd>${renderRecordValue(value, key, record)}</dd></div>`).join("");
    const structuredFields = structured.map(([key, value]) => `<div class="g-record-field"><dt>${escapeHTML(fieldLabel(key))}</dt><dd>${renderRecordValue(value, key, record)}</dd></div>`).join("");
    lightbox.innerHTML = `<div class="lightbox-dialog g-record-dialog" role="dialog" aria-modal="true" aria-label="${escapeHTML(title)}"><div class="lightbox-head"><div><div class="lightbox-title">${escapeHTML(title)}</div><div class="lightbox-path">${contextLines.map(escapeHTML).join(" · ")}</div></div><button class="button icon" data-action="close-lightbox" aria-label="Close">×</button></div><div class="g-record-body"><dl>${fields}</dl>${structured.length ? `<details><summary>Structured fields from the source file (${structured.length})</summary><dl>${structuredFields}</dl></details>` : ""}<details><summary>Technical JSON</summary><pre>${escapeHTML(JSON.stringify(record, null, 2))}</pre></details></div></div>`;
    lightbox.hidden = false;
    lightbox.querySelector("[data-action=close-lightbox]")?.focus();
  }

  function portfolioStatus(record) {
    const selection = activeSelection(record);
    if (selection.selected) return `Selected at order ${selection.sequence}: ${tierShort(selection.tier)}`;
    return "Not selected in this mode";
  }

  function recordSection(title, description, entries) {
    const visible = entries.filter(Boolean);
    if (!visible.length) return "";
    return `<section class="g-record-section"><div class="g-record-section-head"><h2>${escapeHTML(title)}</h2>${description ? `<p>${escapeHTML(description)}</p>` : ""}</div><dl>${visible.map(([label, value]) => `<div class="g-record-field"><dt>${escapeHTML(label)}</dt><dd>${renderRecordValue(value)}</dd></div>`).join("")}</dl></section>`;
  }

  function openLeaderboardRecord(record) {
    const mode = modeMeta(leaderboardView.mode);
    const selection = activeSelection(record);
    const coverage = activeCoverage(record);
    const capabilityLines = (items) => (items || []).map((item) => `${item.name}${item.level ? ` · level ${item.level}` : ""}`);
    const missingLines = (coverage.missingRequirements || []).map((item) => `${item.name} · ${titleCase(item.domain)}${item.level ? ` · level ${item.level}` : ""}`);
    const technicalFields = Object.entries(record).map(([key, value]) => `<div class="g-record-field"><dt>${escapeHTML(fieldLabel(key))}</dt><dd>${renderRecordValue(value, key, record)}</dd></div>`).join("");
    const title = record.representative_action || "Action group";
    lightbox.innerHTML = `<div class="lightbox-dialog g-record-dialog" role="dialog" aria-modal="true" aria-label="${escapeHTML(title)}">
      <div class="lightbox-head"><div><div class="lightbox-title">${escapeHTML(title)}</div><div class="lightbox-path">${escapeHTML(record.action_group_id)} · ${escapeHTML(mode.label)} · ${escapeHTML(portfolioStatus(record))}</div></div><button class="button icon" data-action="close-lightbox" aria-label="Close">×</button></div>
      <div class="g-record-body g-proposal-record">
        ${recordSection("Action group", "The deduplicated physical operation used as the optimization unit.", [
          ["Representative action", record.representative_action],
          ["Action-group ID", record.action_group_id],
          ["Action occurrences", record.action_occurrence_count],
          ["Group origin", titleCase(record.group_origin)],
          ["Selection eligibility", record.selection_eligible ? "Eligible" : `Quarantined · ${titleCase(record.eligibility_category)}`],
        ])}
        ${recordSection("Selection", `The recorded round-${manifest().selection.latestRound} decision for ${mode.label}.`, [
          ["Portfolio status", portfolioStatus(record)],
          selection.tier ? ["Selection tier", tierShort(selection.tier)] : null,
          selection.sequence ? ["Portfolio order", selection.sequence] : null,
          selection.lostCoveredActions !== null && selection.lostCoveredActions !== undefined ? ["Covered actions lost without this selection", selection.lostCoveredActions] : null,
          selection.lostEconomicValueUsd !== null && selection.lostEconomicValueUsd !== undefined ? ["Economic coverage lost without this selection", weight(selection.lostEconomicValueUsd, "market")] : null,
          ["Economic value directly allocated to this action", weight(record.market_work_economic_value_usd, "market")],
          ["Personal time directly allocated to this action", weight(record.everyday_life_annual_population_hours, "life")],
        ])}
        ${recordSection("Capability coverage", manifest().selection.coverageRule, [
          ["Coverage result", coverage.covered ? "Covered" : "Uncovered"],
          ["Active-mode requirements", coverage.activeRequirementCount],
          ["Missing requirements", coverage.missingRequirementCount],
          missingLines.length ? ["Exact missing requirements", missingLines] : null,
          coverage.vacuouslyCovered ? ["Vacuous coverage", "Yes · this action has no active requirements in the selected mode"] : null,
        ])}
        ${recordSection("Round-4 requirements", "Robot and physics requirements remain separate even when the current coverage mode uses only one domain.", [
          ["Robot capabilities", capabilityLines(record.robot_capabilities)],
          ["Physics capabilities", capabilityLines(record.physics_capabilities)],
        ])}
        <details class="g-record-technical"><summary>All stored fields</summary><dl>${technicalFields}</dl><details><summary>Technical JSON</summary><pre>${escapeHTML(JSON.stringify(record, null, 2))}</pre></details></details>
      </div>
    </div>`;
    lightbox.hidden = false;
    lightbox.querySelector("[data-action=close-lightbox]")?.focus();
  }

  function renderRecordValue(value, field = "", record = null) {
    if (value === null || value === undefined || value === "") return `<span class="g-null">Not recorded</span>`;
    if (typeof value === "boolean") return `<span class="g-boolean ${value ? "yes" : "no"}">${value ? "Yes" : "No"}</span>`;
    if (Array.isArray(value)) {
      if (!value.length) return `<span class="g-null">None</span>`;
      if (value.every((item) => typeof item !== "object")) return `<div class="g-record-tags">${value.map((item) => `<span>${escapeHTML(displayFieldScalar(item, field, record))}</span>`).join("")}</div>`;
      return `<pre>${escapeHTML(JSON.stringify(value, null, 2))}</pre>`;
    }
    if (typeof value === "object") return `<pre>${escapeHTML(JSON.stringify(value, null, 2))}</pre>`;
    return `<span>${escapeHTML(displayFieldScalar(value, field, record))}</span>`;
  }

  function render(route) {
    if (!manifest()) {
      app.innerHTML = `<div class="loading"><div><div class="loading-mark"></div>Loading the activity-selection data…</div></div>`;
      return;
    }
    if (route.name === "grounding-stage") return renderStage(route.number);
    if (route.name === "grounding-data-detail") return renderDataset(route.id);
    if (route.name === "grounding-data") return renderDataRegistry();
    if (route.name === "grounding-leaderboard") return renderLeaderboard();
    return renderOverview();
  }

  function handleClick(event) {
    const methodSourceNode = event.target.closest("[data-grounding-method-source]");
    if (methodSourceNode) {
      openArtifact({
        label: methodSourceNode.dataset.groundingMethodLabel,
        path: methodSourceNode.dataset.groundingMethodSource,
        type: methodSourceNode.dataset.groundingMethodType || "text",
      });
      return true;
    }
    const documentPath = event.target.closest("[data-grounding-document]")?.dataset.groundingDocument;
    if (documentPath) {
      const document = manifest().documents.find((item) => item.path === documentPath);
      if (document) openArtifact({ label: document.label, path: document.path, type: document.type });
      return true;
    }
    const view = event.target.closest("[data-g-leaderboard-view], [data-grounding-leaderboard-view]")?.dataset.gLeaderboardView || event.target.closest("[data-grounding-leaderboard-view]")?.dataset.groundingLeaderboardView;
    if (view) {
      leaderboardView.view = view;
      leaderboardView.status = "All";
      leaderboardView.tier = "All";
      leaderboardView.page = 1;
      leaderboardView.sort = "";
      if (location.hash !== "#/grounding/leaderboard") location.hash = "#/grounding/leaderboard";
      else renderLeaderboard();
      return true;
    }
    const datasetSort = event.target.closest("[data-g-dataset-sort]")?.dataset.gDatasetSort;
    if (datasetSort) {
      if (datasetView.sort === datasetSort) datasetView.direction = datasetView.direction === "asc" ? "desc" : "asc";
      else { datasetView.sort = datasetSort; datasetView.direction = "asc"; }
      datasetView.page = 1; renderDataset(datasetView.id); return true;
    }
    const leaderboardSort = event.target.closest("[data-g-leaderboard-sort]")?.dataset.gLeaderboardSort;
    if (leaderboardSort) {
      if (leaderboardView.sort === leaderboardSort) leaderboardView.direction = leaderboardView.direction === "asc" ? "desc" : "asc";
      else { leaderboardView.sort = leaderboardSort; leaderboardView.direction = "asc"; }
      leaderboardView.page = 1; renderLeaderboard(); return true;
    }
    const datasetPage = event.target.closest("[data-g-dataset-page]")?.dataset.gDatasetPage;
    if (datasetPage) { datasetView.page = Number(datasetPage); renderDataset(datasetView.id); window.scrollTo({ top: 340, behavior: "smooth" }); return true; }
    const leaderboardPage = event.target.closest("[data-g-leaderboard-page]")?.dataset.gLeaderboardPage;
    if (leaderboardPage) { leaderboardView.page = Number(leaderboardPage); renderLeaderboard(); window.scrollTo({ top: 390, behavior: "smooth" }); return true; }
    const datasetRow = event.target.closest("[data-g-dataset-row]")?.dataset.gDatasetRow;
    if (datasetRow !== undefined) {
      const record = visibleDatasetRows[Number(datasetRow)];
      const spec = datasetById(datasetView.id);
      if (record && spec) {
        const rowNumber = (datasetView.page - 1) * datasetView.pageSize + Number(datasetRow) + 1;
        openRecord(`${spec.title}: row ${rowNumber}`, record, [spec.rowMeaning, spec.path]);
      }
      return true;
    }
    const leaderboardRow = event.target.closest("[data-g-leaderboard-row]")?.dataset.gLeaderboardRow;
    if (leaderboardRow !== undefined) {
      const record = visibleLeaderboardRows[Number(leaderboardRow)];
      if (record) openLeaderboardRecord(record);
      return true;
    }
    return false;
  }

  function handleInput(event) {
    if (event.target.id === "g-registry-search") { clearTimeout(inputTimer); inputTimer = setTimeout(filterRegistry, 120); return true; }
    if (event.target.id === "g-data-search") {
      datasetView.query = event.target.value; datasetView.page = 1; clearTimeout(inputTimer);
      inputTimer = setTimeout(() => renderPreservingInput("g-data-search", () => renderDataset(datasetView.id)), 180); return true;
    }
    if (event.target.id === "g-leaderboard-search") {
      leaderboardView.query = event.target.value; leaderboardView.page = 1; clearTimeout(inputTimer);
      inputTimer = setTimeout(() => renderPreservingInput("g-leaderboard-search", renderLeaderboard), 180); return true;
    }
    return false;
  }

  function renderPreservingInput(inputId, renderPage) {
    const input = document.getElementById(inputId);
    const wasFocused = document.activeElement === input;
    const selectionStart = input?.selectionStart ?? 0;
    const selectionEnd = input?.selectionEnd ?? selectionStart;
    const selectionDirection = input?.selectionDirection || "none";

    renderPage();
    if (!wasFocused) return;

    const replacement = document.getElementById(inputId);
    if (!replacement) return;
    const valueLength = replacement.value.length;
    replacement.focus({ preventScroll: true });
    replacement.setSelectionRange(
      Math.min(selectionStart, valueLength),
      Math.min(selectionEnd, valueLength),
      selectionDirection,
    );
  }

  function handleChange(event) {
    if (event.target.id === "g-registry-stage") { filterRegistry(); return true; }
    if (event.target.id === "g-data-facet-field") { datasetView.facetField = event.target.value; datasetView.facetValue = ""; datasetView.page = 1; renderDataset(datasetView.id); return true; }
    if (event.target.id === "g-data-facet-value") { datasetView.facetValue = event.target.value; datasetView.page = 1; renderDataset(datasetView.id); return true; }
    if (event.target.id === "g-data-page-size") { datasetView.pageSize = Number(event.target.value); datasetView.page = 1; renderDataset(datasetView.id); return true; }
    if (event.target.id === "g-leaderboard-status") {
      leaderboardView.status = event.target.value;
      leaderboardView.page = 1;
      renderLeaderboard();
      return true;
    }
    if (event.target.id === "g-leaderboard-tier") { leaderboardView.tier = event.target.value; leaderboardView.page = 1; renderLeaderboard(); return true; }
    if (event.target.id === "g-leaderboard-mode") {
      leaderboardView.mode = event.target.value;
      leaderboardView.tier = "All";
      leaderboardView.status = "All";
      leaderboardView.sort = "";
      leaderboardView.page = 1;
      renderLeaderboard();
      return true;
    }
    if (event.target.id === "g-leaderboard-page-size") { leaderboardView.pageSize = Number(event.target.value); leaderboardView.page = 1; renderLeaderboard(); return true; }
    return false;
  }

  function handleKeydown(event) {
    const datasetRow = event.target.closest?.("[data-g-dataset-row]");
    const leaderboardRow = event.target.closest?.("[data-g-leaderboard-row]");
    if ((event.key === "Enter" || event.key === " ") && (datasetRow || leaderboardRow)) {
      event.preventDefault();
      event.target.click();
      return true;
    }
    return false;
  }

  function setLeaderboardView(view) {
    if (manifest()?.leaderboard.views.some((item) => item.id === view)) {
      leaderboardView.view = view;
      leaderboardView.status = "All";
      leaderboardView.tier = "All";
    }
  }

  return { render, handleClick, handleInput, handleChange, handleKeydown, setLeaderboardView };
}
