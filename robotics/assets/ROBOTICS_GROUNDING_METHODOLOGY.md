# Grounding Gym-Anything for Robotics

Status: methodology foundation recorded 2026-07-19; source-expansion coverage
and the first national claim comparison updated 2026-07-21.

This document records the governing selection principle for Gym-Anything for
Robotics and translates the grounding methodology of *Gym-Anything: Turn any
Software into an Agent Environment* into the physical world.

Paper: <https://arxiv.org/abs/2604.06126>

## Governing principle

Gym-Anything grounds environments in **economic activity mediated through
software**. Gym-Anything for Robotics should ground environments in **real
human activity mediated through physical interaction**.

The benchmark must therefore not begin with a hand-authored list of interesting
robot demos, convenient simulator assets, or currently solvable manipulation
benchmarks. It must begin with what people actually do, determine which physical
actions those activities require, and only afterward consider simulation
feasibility.

The desired chain is:

```text
occupation and real-life activity
    -> native real-world task evidence
    -> physical portion of the task
    -> atomic physical action occurrences
    -> deduplicated, parameterized physical primitives
    -> tools, objects, materials, contacts, and scenes
    -> simulator environments
```

## What Gym-Anything grounds

The software benchmark constructs an open-vocabulary software universe rather
than starting from a fixed application taxonomy:

```text
occupation economic weight
    -> software categories used by the occupation
    -> products used within each category
    -> product economic weight
    -> reproducibility and access filters
    -> coverage-aware environment portfolio
```

Occupation weights are derived from O*NET occupations, BLS employment and wage
data, and BEA compensation/GDP totals. For an occupation, category, and product,
the approximate attribution is:

```text
occupation economic weight
    * computer-use fraction
    * category share within the occupation
    * product share within the category
```

The resulting product catalog is filtered only after the economically grounded
universe has been constructed. The final portfolio balances aggregate economic
importance with strategic, STEM, occupational, niche, and category coverage.

Tasks inside an application are occupation-conditioned and grounded through
application exploration and realistic professional data. They are not directly
extracted from O*NET task statements. This makes the paper's grounding strongest
at software selection and more indirect at exact workflow selection.

## Robotics translation

| Gym-Anything | Gym-Anything for Robotics |
| --- | --- |
| Occupation | Occupation and real-life activity |
| Software category | Physical-work domain |
| Software product | Tool, machine, object system, or workplace |
| Professional workflow | Real-world physical task |
| GUI action sequence | Physical action sequence |
| Application state | Physical world state |
| Task verifier | Measured physical state-transition verifier |

Scenes are necessary execution contexts, but scenes are not the fundamental
capability basis. The basis is the set of reusable physical actions needed to
compose real human tasks.

## Governing primitive-weight formula

For candidate atomic physical action `a`, aggregate its real-world importance
over occupations `o` and native tasks `t`:

\[
W(a) = \sum_{o,t}
W(o)
\cdot I(t \mid o)
\cdot F(t \mid o)
\cdot P_{\mathrm{physical}}(t)
\cdot R(a \mid t)
\]

where:

- `W(o)` is the occupation's labor or economic weight.
- `I(t | o)` is the normalized importance or prevalence of task `t` within
  occupation `o`.
- `F(t | o)` is its normalized frequency.
- `P_physical(t)` is the fraction of the task that requires physical-world
  interaction, not merely a binary physical/nonphysical label.
- `R(a | t)` is the normalized contribution of primitive `a` to the physical
  execution of task `t`.

`R(a | t)` must conserve task attribution across the primitive occurrences in a
task. Otherwise, decomposing one task into more steps would artificially create
more economic weight. The operational estimator and its normalization must be
specified and calibrated before ranking primitives.

The formula is a ranking and allocation model. Its inputs must retain their
provenance and uncertainty; model-derived estimates must never be presented as
native O*NET measurements.

### Paid work is not the whole activity universe

The occupation formula covers market work, but the intended benchmark also
includes household production, caregiving, personal activities, sport, exercise,
and recreation. These cannot be recovered from O*NET occupation records alone.

The project must therefore maintain at least two native grounding streams:

- **Market work:** O*NET tasks weighted using BLS/BEA labor and economic data.
- **Everyday life:** population-weighted activity duration from the American
  Time Use Survey (ATUS), with BEA household-production valuations as an
  additional axis where applicable.

Separately versioned international releases may extend either stream, but they
do not inherit United States weights. ESCO adds multilingual occupation and
skill-relation content without prevalence. Canada 2022 diary microdata add a
Canadian population-day axis. India 2024 public time-use tables add a separate
India population-day aggregate axis without claiming registered microdata.
HETUS-2020 adds separate European country-table aggregates. Each retains its
own population, classification, unit, weight, missingness, and uncertainty
contract. Australia 2024 adds public aggregate workbooks but not respondent
rows; Argentina 2021 adds public ordered diary rows and replicate weights. A
17-question comparison records what each package supports but establishes no
cross-survey harmonization. An audited rule would still be required before
combining their categories or estimates.

The same decomposition and primitive deduplication machinery can operate over
both streams. Their weights must remain separate: dollars, population-hours, and
household-production value are not silently added into one meaningless scalar.
Environment selection should be multi-objective over these axes.

## Historical grounded layers

The repository's earlier grounding work, summarized in
`ISAAC_SIM_AGENT_BRIEF.md`, already contains:

- 22,023 native task-DWA weighted rows.
- 9,233 task-DWA rows classified as having nonzero physical requirements.
- 6,969 unique physical occupation-task units.
- 2,188 open-vocabulary raw scene strings.
- 1,627 conservative scene clusters.
- 1,149 practical scene families.

These are valuable historical priors. They do not constitute current labels or
a physical primitive catalog. In particular, a scene cluster answers *where*
work may happen; it does not answer *which reusable physical state transitions*
the work requires. The old task-dollar values also failed conservation checks
and are not used by the current weighting layer.

Exact copies of the legacy model outputs are retained under
`grounding/data/legacy/v0/` with hashes and an audit. They are used only to
stratify calibration samples.

## Current repository-native layers

The tracked `grounding/` package now contains:

- 51 byte-locked primary inputs from O*NET, BLS, BEA, and ATUS;
- 1,016 O*NET occupation titles, 18,796 unique occupation-task statements, and
  all native rating, DWA, work-context, and retained tool records;
- an exact code-based bridge onto all 830 published May 2025 OEWS occupation
  units, with no fuzzy title allocation;
- 465 ATUS activity codes and 2021–2025 population-time estimates using the
  published 160-replicate method;
- conserved occupation and task economic allocations with seven explicit
  sensitivity variants;
- 19,261 content-hashed native evidence packets containing 100,984 evidence
  records and no proposed physicality or action labels;
- a deterministic, manifest-bound activity inventory over all 19,261 source
  units, including the occupation/task and ATUS hierarchies, all seven market
  sensitivity variants, evidence packet joins, explicit structural
  missingness, and covariance-aware ATUS first-tier summaries without mixing
  dollars and population-hours;
- classification-only ISCO-08 and ICATUS 2016 bridge tables and a separately
  locked, unweighted national-content release over Canada NOC 2021 and Australia
  OSCA 2024. These expansion layers preserve native systems and provenance and
  make no statement-equivalence, physicality, prevalence, or primitive claim;
- a lossless ESCO 1.2.1 source-content release over 18,237 occupation, skill,
  and hierarchy records and 418,307 ordered relations. It preserves URI
  identity, multilingual maps, duplicate titles, and omissions while making no
  task, physicality, atomicity, procedure, equivalence, prevalence, or weight
  claim;
- an exact-copy Brazil CBO source release over 2,694 occupation codes and
  174,296 occupation-activity rows covering 2,669 occupations. The release
  preserves source anomalies and exact Portuguese source bytes, excludes the
  three linked books with conflicting embedded notices, and distributes no
  translated or otherwise transformed occupation or activity text. The rows
  remain unreviewed occupation content, not physical or atomic actions;
- an audit-only Japan job tag snapshot locking all four current data files
  (6,804,183 bytes) and the publisher-hosted full terms PDF (223,764 bytes),
  together with 556 Japanese occupation descriptions and 7,501 populated task
  positions across 433 individual occupations. It preserves 11 CP932-CSV/XLSX
  representation differences, 38 description-only records, four title changes,
  and task missingness without repair. Deterministic extraction checks the
  locked terms document's Article 9 permission and attribution text. The
  candidate is `locked_source_native` but not admitted. A separate source-
  faithful review frame preserves all 7,501 task occurrences, keeps all 141
  exact-repeat groups contextual, and creates two blank 200-row human
  calibration templates in different orders. It uses no machine translation
  and now has executable independent-import, bilingual-review, specialist,
  adjudication, English-clarity, revision, and calibration-acceptance gates.
  Acceptance reconstructs the frame from the locked source, rebuilds the
  derived review and adjudication waves, and separately binds every accepted
  source hash to that frame. Imported human assessment files remain custody
  roots; their hashes do not prove authorship.
  Only synthetic temporary test records have traversed those gates, so it still
  contains zero real or accepted translations; its tasks have no physicality,
  atomicity, completeness, procedure, prevalence, or weight decision;
- separate everyday-life evidence outside the United States: the Canada 2022
  Time Use Survey release preserves 12,336 person diaries, 168,078 episodes,
  and 500 bootstrap weights as one Canadian population-day axis; the India 2024
  release preserves 31,050 published estimates over all 230 ICATUS nodes and
  10,206 major-division RSE cells as a separate public aggregate axis; and the
  HETUS-2020 release preserves 407,160 source-native aggregate cells for ten
  European countries. None is merged into ATUS or treated as an action catalog;
- a separately verified wave-2 selection frame built from three locked United
  Nations sources. It preserves 317 survey records for 108 countries and ranks
  22 current candidates across nine uncovered geographic groups. Its four-point
  Australia-over-Argentina lead is below the registered eight-point margin, and
  no national package is byte-locked within the release, so it admits no new
  diary, estimate, population weight, physicality label, procedure, or action;
- a separately verified access-only continuation for the Kenya and Mongolia
  conditional runners named by that frozen frame. It preserves seven visual
  captures plus a machine-readable observation log, records both login
  boundaries without using them, and mechanically re-ranks all 22 unchanged
  parent candidates. It acquires no national package and does not alter the
  failed automatic gate;
- a second access-only continuation for Georgia. It freezes all 63 predecessor
  files, preserves four full-page captures plus one observation log, and records
  the visible findings, questionnaire, database, and description routes without
  activating a substantive link. Georgia reaches 66 and rank four, all three
  conditional runners are now observed, no national package is acquired, and
  the failed automatic gate remains unchanged;
- separately verified national evidence for both leaders following the explicit
  decision to inspect them despite the failed automatic gate. Australia 2024
  contributes six locked public sources, 73 native categories, and 549
  normalized aggregate rows with uncertainty, while its respondent rows remain
  DataLab-only. Argentina 2021 contributes ten tracked official sources,
  14,350 selected people, 41,025 member rows, three source activity slots, 52
  native codes, `WPER`, `WHOG`, and a checksum-pinned 300-person plus
  300-household replicate system. Its separate loss-aware derived release
  mechanically orders all 2,066,400 ten-minute rows by `ID` and `N_FILA` while
  retaining source row and slot position. It preserves 2,489 ordered tuples,
  21,008 consecutive tuple types, and the sole repeated-code interval, and
  keeps full-unique, full-slot, and equal-split durations as separate meanings
  rather than harmonized or physical-action measures;
- a deterministic two-package by 17-claim comparison. Its 34 rows bind every
  answer to exact source hashes and locations and preserve `proven`,
  `proven_with_limits`, `documented_but_data_unacquired`, `not_available`, and
  `unknown` as evidence states rather than scores. It creates no winner,
  category merge, crosswalk, physical-step observation, or action label;
- a separately locked OaSIS 2025 release over 900 Canadian seven-digit
  occupation profiles. It preserves bilingual ratings and occupation content,
  including 4,991 English main-duty screening rows, while recording O*NET's
  role in the source method and making no independence, novelty, physicality,
  atomicity, completeness, prevalence, or weight claim;
- a separately locked zero-data contract release for the Skills England
  Occupational Maps public API. Six public documents reconstruct all 17
  operations, 35 schemas, and 203 fields while preserving access, privacy,
  licence, attribution, and contract differences. No key was requested, no data
  endpoint was called, and no occupation, duty, knowledge, skill, or behaviour
  row was admitted;
- separate unweighted procedural-evidence releases for all 54 current Canadian
  Red Seal trades and all 15,162 Australian competency units observed current.
  The Australian release emits structured text only for 14,047 licensable,
  non-confidential units; both releases expose unreviewed screening candidates,
  not physicality labels, atomic actions, equivalence decisions, or weights;
- blinded physicality-calibration samples for 440 market-work tasks and 170
  everyday-life activity units, plus immutable reviewer forms and holdout
  protection;
- a label-independent, exhaustive decomposition-supply reserve over the 18,356
  remaining work tasks and 289 remaining substantive everyday-life codes, with
  explicit prohibition on evaluation or prevalence use; and
- explicit coverage, decomposition, fidelity-envelope, pair-relation, and
  conservative-clustering contracts with executable tests.

Independent human physicality judgments have not yet been collected. The
legacy classifier and this model's proposals must not be described as those
labels.

## Non-negotiable design constraints

1. **Source first.** Preserve native occupation, task, rating, activity, and
   work-context records, as well as native time-use activity records, with
   versioned provenance.
2. **Open vocabulary first.** Do not author the primitive taxonomy in advance.
   Extract candidates from source-grounded tasks, then deduplicate and organize
   them.
3. **One canonical task unit.** Decompose unique occupation-task units rather
   than duplicated task-DWA rows.
4. **Evidence for every inference.** Every physicality estimate, decomposition,
   primitive occurrence, and merge must point back to supporting evidence.
5. **Separate data layers.** Source-native, deterministic-derived,
   model-derived, experimentally measured, and manually adjudicated fields must
   remain distinguishable.
6. **Weight conservation.** Neither DWA multiplicity nor decomposition length
   may duplicate the economic weight of a task.
7. **Feasibility comes later.** Isaac Sim support, available assets, and current
   robot capability are annotations or downstream filters, not the source
   taxonomy.
8. **Audit high-impact decisions.** Human review should be concentrated on
   high-weight, low-confidence, disputed, and cluster-boundary cases.
9. **Measure basis coverage.** Environment selection must report both weighted
   real-world coverage and marginal primitive coverage.
10. **Retain uncertainty.** Rankings should expose uncertainty and sensitivity,
    not only a single opaque score.

## Immediate missing layer

The next systematic stage is:

> Collect and adjudicate the blinded human physicality calibration labels;
> freeze and evaluate the physicality rubric once on its sealed holdout; use the
> separately preregistered reserve only for observed candidate-supply
> shortfalls; select the human-confirmed decomposition calibration set; then build a
> balanced 200-source-unit end-to-end pilot from versioned procedural evidence
> through scenarios, action graphs, occurrence relations, conservative
> primitives, and conserved weights.

The repository now contains the complete machine path for the middle of that
sentence: fixed external resources and locators, independently reviewed claims,
enriched packet construction, two-person packet sufficiency review, separately
authored decomposition packages, and third-party pair comparison. These tools
do not change the first missing fact: the human physicality development labels
are still uncollected, so no selected calibration task or primitive is claimed
as complete.

The identity of a primitive is not an English verb. It is a class of role-bound
physical state-transition occurrences that one simulator template can reproduce
inside one declared and calibrated fidelity envelope. Critical missing evidence
prevents a merge.

Only after that stage should the project decide which new simulator environments
form the best initial physical capability basis.

The concrete collection and audit design is specified in
[`ATOMIC_PRIMITIVE_COLLECTION_PLAN.md`](ATOMIC_PRIMITIVE_COLLECTION_PLAN.md).
