# LaundryFold executable findings

This file records retained and rejected results. Values describe the exact
software configuration and are not measurements of a real towel.

## 17 July 2026 -- P0 runtime and constitutive foundation

### Runtime audit

- Isaac Sim 5.1 bundles Warp 1.8.2.
- Newton 1.4.0 requires Warp 1.15.0 or newer.
- An isolated Python 3.12 environment was created at
  `.venv-laundry-newton14` with Newton 1.4.0 and Warp 1.15.0.
- CUDA executed on the local RTX 3090. The unrelated running Isaac 4.5 process
  was not stopped or modified.

### Stock runtime smoke tests

Newton's stock Style3D hanging-cloth test and full-surface VBD gripper test both
completed on CUDA. This established only that the installed features execute;
the repository-owned probe below tests the mechanisms and writes measurements.

### Solver-independent reference layer

Thirty-four tests pass. The retained gates include:

- rigid-rotation objectivity and zero membrane stress;
- analytic first-Piola stress versus central finite differences;
- distinct warp/weft response and independent shear coefficient;
- directional periodic bend response;
- monotone pressure--thickness response with an unloading branch;
- dissipative regularized sliding friction;
- pressure/dwell-dependent, bounded crease plasticity and real-time recovery;
- exact rectangular mesh area, lumped mass, winding, boundaries, and hinges;
- registered, ordered, non-duplicated folded initial conditions;
- released/settled/material-coordinate half-fold success gates; and
- monotonic, finite, hash-addressed evidence traces.

### Repository-owned Newton capability probe

Authoritative trace: `outputs/p0_newton_capabilities.json`.

1. **Style3D anisotropy passes.** Under the same 1 N strip load, swapping the
   panel-U stiffness from 8,000 N/m to 6,000 N/m increases extension from
   0.385940 mm to 0.512481 mm, a 1.327876 ratio. The fixed-edge error is exactly
   zero in both cases. These are numerical priors, not cotton measurements.
2. **Full-surface feature detection passes.** A two-triangle quad spans a box
   while all four vertices lie outside the contact margin. Vertex-only contact
   produces zero records; the enabled full-surface path produces three edge/
   face records and zero vertex records.
3. **Unified two-way motion passes in the conservative profile.** A 50 g cloth
   patch impacts a free 200 g rigid box. With full-surface contact, zero built-in
   contact damping, and the retained zero-gravity setup, the best measured total
   momentum residual is of order `1e-5` (the latest run measured `2.356e-5`)
   relative to the initial
   momentum. The box moves and its final velocity is nonzero; the result is not
   a kinematic obstacle response.
4. **The contact gap gate passes.** In the retained full-surface cases the
   minimum vertex gap remains within the declared two-prior-thickness bound.

### Rejected contact damping

The first probe paired contact stiffness with Newton's built-in soft-contact
damping. It failed conservation:

- `ke=1,000 N/m`, `kd=5 N s/m`, full surface: approximately 15.6% relative
  momentum residual;
- `ke=5,000 N/m`, `kd=25 N s/m`: approximately 34.2%; and
- `ke=20,000 N/m`, `kd=100 N s/m`: approximately 296% in the repeated matrix
  (an earlier single case was similarly catastrophic).

Repeating with `kd=0` reduces the residual by roughly four orders of magnitude.
This identifies the built-in damping path, rather than full-surface record count
alone, as the dominant failure in this probe. We will not use that damping to
hide vibration. A physical contact-loss model must be symmetric and separately
validated in force, energy, and momentum.

### Open at the P0 checkpoint

This list records what was still open when P0 was accepted. Later dated
sections below resolve the numerical fold, release/settling, modular API, and
Isaac-presentation items; physical specimen calibration remains open.

- Couple anisotropic Style3D response to a dynamic robot without losing
  equal-and-opposite reaction, or implement the same orthotropy in unified VBD.
- Validate self-contact, layer order, thickness, table friction, and stack
  compression under refinement.
- Integrate persistent-crease internal state into the GPU solver and reproduce
  independent recovery curves.
- Build and verify a compliant gripper and bimanual robot action.
- Complete, release, settle, and independently score a towel fold.
- Bridge committed solver state into Isaac for sensors and photoreal rendering.
- Acquire and measure a named towel, table coupon, and finger-pad specimen.

## 17 July 2026 -- P1 gravity and ground contact

Authoritative trace: `outputs/p1_towel_drop.json`.

- The original fast profile at 240 Hz was rejected. Its second ground impact
  became unstable and the state diverged; the full trace is retained as
  `outputs/p1_towel_drop_rejected_dt240.json`.
- A stiffness sweep did not cure the coarse failure. Holding the mesh and
  material fixed while changing only the timestep showed 240 Hz unstable and
  480/960 Hz stable. The retained coarse profile is therefore 480 Hz.
- At 480 Hz (425 vertices) and 960 Hz (1,617 vertices), the 100 mm drop first
  contacts at 0.141667 s in both cases. The worst mid-surface heights are
  +0.142 mm and -0.114 mm, respectively, both inside the declared two-thickness
  bound.
- Final centre heights differ by 1.12 micrometres, and final maximum speeds are
  1.78 mm/s and 0.890 mm/s. Runtime state writes remain zero.
- The 960 Hz float32 free-fall velocity differs from the semi-implicit reference
  by 0.135 mm/s after 0.1 s (1.4e-4 relative). The gate records float32 reality
  and uses a 0.2 mm/s bound; it does not claim double precision.

This probe disables particle self-contact because a flat single layer cannot
self-contact. That mechanism is isolated below.

## 17 July 2026 -- P2 folded self-contact and thickness

Authoritative trace: `outputs/p2_folded_self_contact.json`.

- The folded initial condition is authored once before time starts while the
  elastic rest state remains flat. It is not a runtime action.
- Under the 2.942 Pa weight of the top half, the compression prior predicts
  0.797995 mm thickness. Retained fast/interactive median separations are
  0.799734 mm and 0.799915 mm, differing by only 0.181 micrometres.
- Across the retained 0.2 s cases, minimum measured stack separations are
  0.7905 mm and 0.7964 mm; layer order is preserved.
- The contact buffers peak at 8 records per vertex and 15 per edge, safely below
  the declared 64/128 per-primitive capacities.
- A causal closing-motion ablation collapses the median separation to
  0.000223 mm with self-contact disabled, but retains 0.798810 mm with
  self-contact enabled. Both cases have zero runtime pose writes.

Two numerical configurations were rejected during P2:

1. Contact buffers were initially (and incorrectly) scaled by total mesh size
   even though Newton sizes them per primitive. This caused near-quadratic
   allocation and a ten-minute watchdog failure. Fixed per-primitive capacities
   preserve the same contacts and reduce the fast four-step smoke test to about
   0.29 s.
2. The 48 x 32 mesh at 480 Hz developed localized motion near the tight material
   hinge, peaking near 1.02 m/s. Increasing topology-filter rings did not cure it.
   A timestep sweep retained 960 Hz (0.032 m/s peak in the sweep) and rejected
   480/720 Hz. The failed combined trace is retained as
   `outputs/p2_folded_self_contact_rejected_dt480.json`.

P2 validates low-load separation for the fixed-radius Newton contact model. It
does not yet validate high-pressure nonlinear compression, exact triangle
intersection count, or measured terry-loop thickness.

## 17 July 2026 -- P3 directional bending release

Authoritative trace: `outputs/p3_bending_release.json`.

- A gravity-free, contact-free curved towel is released from a manufactured-
  flat elastic rest state. Both retained fast and interactive meshes remain
  finite and release stored bending energy without runtime pose authoring.
- The fast and interactive release fractions are 0.315095 and 0.336748. Their
  0.021653 difference passes the declared refinement gate.
- Peak structural strain remains below 0.000006 in both cases, separating the
  intended bending response from membrane stretching.
- The directional ablation and continuum/discrete energy checks pass. The
  result exercises orthotropic moment--curvature conversion; it does not fit a
  real fabric cantilever or Kawabata bending curve.

## 17 July 2026 -- P4 static/kinetic table friction

Authoritative trace: `outputs/p4_table_friction.json`.

- A horizontal load of `0.45 m g` sticks below the declared static limit
  `mu_s m g = 0.50 m g`; a `0.55 m g` load breaks away on fast and interactive
  meshes. These ratios are fractions of weight, not fractions of the threshold.
- Sliding acceleration follows `a = F/m - mu_k g`; the 0.55-threshold cases
  measure 1.470989 and 1.470997 m/s^2 against 1.470998 m/s^2 expected.
- Added normal pressure increases deceleration according to the declared
  Coulomb law. The effective kinetic coefficient across fast, interactive,
  and validation profiles spans only 0.0000194 around the 0.4 prior.
- The zero-friction causal ablation, pressure dependence, dissipation, and
  refinement gates all pass. Applied particle loads are intentional laboratory
  forcing in this isolated coefficient probe and are not used in P6 or the
  modular task backend.

## 17 July 2026 -- P5 conservative two-way pinch grasp

Authoritative trace: `outputs/p5_two_way_grasp.json`.

- The symmetric projected pinch path applies equal-and-opposite impulses to
  cloth and finite-mass gripper bodies. It does not attach cloth particles or
  prescribe their motion.
- The retained interactive case lifts the gripper 150.001 mm and the cloth
  149.292 mm, leaving -0.709 mm tracking error. It retains at least 147 pinched
  particles after closure with 1.990 N maximum preload and 3.005% peak
  structural strain.
- The validation case lifts the cloth 149.555 mm for a 149.998 mm gripper
  motion, leaving -0.443 mm error with 1.655% peak strain.
- The zero-friction causal ablation and resolution-refinement gates pass. A raw
  Newton single-coefficient trace is retained separately as a rejected model;
  it is not relabelled as the accepted physical interface.

## 17 July 2026 -- P6 released and settled towel half-fold

Authoritative trace: `outputs/p6_released_half_fold.json`. Authoritative
keyframes: `traces/p6_released_half_fold_keyframes.npz`. Current content hash:
`sha256:4cd6555886da5d434fb4be469aecd3d8048543b41f347442a5340aec50392236`.

- A finite-mass, force-limited clamp acquires the overhanging edge, follows a
  smooth 162-degree folding arc, places the moving panel, releases it, and
  retracts. A separate passive-spin roller approaches from 450 mm, loads the
  observed crease from above, supports release, and then lifts clear.
- The independently evaluated final state passes: 16.396 mm edge RMS,
  17.755 mm edge maximum, 25.826 mm fold-line workspace translation, 0.042 mm
  intrinsic fold-line-shape RMS, 0.487765 footprint fraction, 1.0 layer-order
  fraction, 3.325% peak structural strain, and 2.668 mm/s settled maximum
  speed.
- The trajectory retains at least 34 pinched particles before support transfer.
  The roller reaches 17.074 N inferred normal load and 6.035 N inferred rolling
  load, both below its actuator limits, and its passive bearing reaches
  31.205 rad/s.
- There are zero nonlocal triangle intersections, zero cloth attachments, zero
  runtime cloth-pose writes, and zero direct external particle-force
  applications. Three topologically local crease contacts are reported
  separately instead of being mislabeled as distant surface crossings.
- Every declared P6 gate passes, including release, settling, fixture
  retraction, table clearance, dissipative contact corrections, bounded roller
  loads, passive roller motion, and one target write per fixture per substep.
- The explicit history-dependent crease-rest-angle coupling remains disabled.
  Its current form is an experimental/rejected ablation; the accepted fold uses
  verified elastic bending plus real contact and load dwell.

The P6 outcome is a causal numerical fold, not a calibrated real-towel claim.
The canonical fast profile is also not real-time: the accepted 19.6 s episode
took 478.1 s wall time in its recorded run.

## 17 July 2026 -- modular environment boundary

- `LaundryPhysicsBackend` now separates task semantics from Newton, Isaac, or
  replay dynamics. `LaundryFoldEnv` exposes the same six normalized fixture-
  velocity channels and structured observation wire format to Gymnasium.
- `HalfFoldEpisodeTask` preserves grasp, release, peak strain, nonlocal
  intersection, pose-write, and particle-force history. Success requires the
  geometry gates, a real prior grasp/release sequence, settling, and fixture
  clearance; potential-difference shaping cannot reward a held static pose
  indefinitely.
- `NewtonLaundryBackend` reconstructs a fresh P6 model on reset, integrates
  velocity targets at the physics substep rate, and reads actual rigid-body and
  cloth state. Its exact oriented-box and capsule clearance queries are based
  on the simulated tool poses.
- A cached RTX 3090 smoke test reset the fast backend in 0.661 s and executed
  one fully audited 60 Hz frame in 0.473 s. It observed 425 particles, both
  tools, zero intersections, zero pose writes, and zero direct particle-force
  applications. Both fixture targets were written exactly eight times, once
  per 480 Hz physics substep.
- At this historical P6 checkpoint the suite contained 78 passing tests and
  non-rectangular garments still failed closed. The later P7--P12 track below
  supersedes that construction-status statement without changing the P6 result.

## 17 July 2026 -- isolated Isaac frontend and interactive control

- Isaac Sim 5.1 and Newton 1.4 cannot safely share an interpreter because their
  required Warp versions differ (1.8 and 1.15 respectively). The accepted
  architecture runs `newton_service.py` in the isolated Python 3.12
  environment and exchanges length-prefixed, finite JSON messages over a
  token-authenticated localhost socket.
- The Newton worker exclusively owns resets, actions, integration, task state,
  and observations. Isaac owns presentation, cameras, UI, and eventual sensor
  attachment. `laundry_visual_bridge.py` copies only committed worker state in
  one direction.
- The scene audit passes with 425 mechanical particles embedded into a closed
  7,154-vertex / 13,824-triangle render shell. All declared fixture links and
  six cameras exist, the calibration card is present, and the visual stage has
  zero `RigidBodyAPI` paths.
- Manual keyboard input and the complete P6 reference controller use the same
  six normalized public velocity channels. There are no private cloth-grab,
  warp, crease, or success controls. Reset reconstructs fresh worker physics;
  pause alone stops time, while a zero action still advances dynamics.
- The GUI submits the slow worker frame on a background future so Isaac can
  continue drawing and processing input. This improves interaction but does not
  make the accepted backend real-time; its measured latency remains explicitly
  visible in the UI and report.

## 17 July 2026 -- trace-linked RTX evidence and dossier

Authoritative render manifest: `renders/p6_render_manifest.json`. Source
mechanical trace: `traces/p6_released_half_fold_keyframes.npz`, SHA-256
`6b064e04c2a3f79e23fb3c9327d4bb7bde2b537cd4dccaaf593cfc955ecd801c`.

- Twelve 1440 x 960 captures cover the initial workcell, 25/50/75 percent fold,
  placement, roller loading, release, fixture retraction, and settled hero,
  overhead, and profile views. Every PNG is individually hash-addressed.
- Replicator capture is event-driven with capture-on-play disabled. Blank
  annotator buffers are retried at the same committed state and never accepted.
  A manifest with twelve captures and `pass: true` is the acceptance signal;
  Isaac's process exit code alone is insufficient because shutdown can mask a
  preceding Python exception.
- The presentation mesh is a barycentrically embedded, finite-thickness shell;
  its subdivision and material do not alter mechanics. The final rounded ridge
  is retained from the accepted NPZ: maximum height 24.280 mm, median 1.190 mm,
  95th percentile 8.016 mm, and 4.0 percent of particles above 10 mm. It is
  diagnosed against the 18.944 mm bending/gravity prior scale rather than
  cosmetically flattened.
- The original `paper/laundryfold_physics_report.pdf` checkpoint was a visually
  audited 22-page P0--P6 dossier. Dossier v1.2 supersedes it with a 28-page PDF
  (cover plus 27 numbered pages), P7--P12 construction/contact/topology evidence,
  matched garment failures, 16 numbered figures, and 48 linked sources while
  preserving every P6 result and its calibration boundary.
- The cover, every page header, dashboard-facing copy, and render scene state
  that all material and contact values are prior-only and not physically
  calibrated. Passing the artifact gates does not turn a numerical fold into a
  prediction for a named towel.

## 17 July 2026 -- P7--P9 sewn-garment construction and Style3D ingestion

Authoritative catalogue trace: `outputs/p9_garment_catalog_style3d.json`.
Authoritative exact states: `artifacts/frames/p9_garment_catalog_style3d.npz`.

- The garment path now keeps a cut-panel material atlas separate from its sewn
  physical quotient. Named seam samples weld physical vertices while distinct
  material vertices preserve panel identity, grain axes, openings, and task
  semantics. Lumped mass is integrated from each panel's exact area and areal-
  density profile.
- Five explicit constructions enter Newton Style3D: a 5-panel/13-seam jersey
  T-shirt (651 particles, 1,250 triangles, 126.387 g), 11-panel/25-seam button-
  down (1,039 / 2,025 / 150.248 g), 19-panel/44-seam jeans (887 / 1,780 /
  357.301 g), 1-panel terry towel (272 / 482 / 141.750 g), and 8-panel/17-seam
  asymmetric top (941 / 1,737 / 150.220 g).
- A physical winding audit fails closed unless every shared edge is traversed
  in opposite directions by its two incident triangles. It exposed 87 shirt,
  184 jeans, and 52 asymmetric-top same-direction edges. The patterns were
  corrected; all five retained cases now have zero mismatches and zero
  nonmanifold edges.
- P9 accepts 5/5 cases with all particles/triangles retained, model mass within
  20 nanograms of authored mass, bounded one-step principal stretch, finite
  state, and no degenerate triangles. The nonrectangular assembly optimizers do
  report their 1,200-iteration cap rather than falsely claiming optimizer
  convergence; acceptance is based on explicit final geometry/runtime gates.
- P7 separately exposes both low-convergence translational leakage and high-
  convergence free-rigid-frame rotational leakage, then verifies the retained
  gauge-fixed zero-force state. P8 verifies a sewn T-shirt gravity/table drop;
  P12 below supersedes its residual table projection for topology release.

These are construction and engine-ingestion results. They do not show that a
robot can fold any of the five garments, and no seam/material profile is fitted
to a named specimen.

## 17 July 2026 -- P10 one-way tools and P11 semantic garment tasks

- P10 uses Newton Style3D kinematic colliders on the terry-towel construction,
  not cloth attachments or cloth pose writes. Two finite pads acquire two common particles; a requested 50 mm
  tool lift produces a 49.994 mm mean lift of that patch and 15.052 mm whole-
  garment centre-of-mass lift with principal stretch 0.9991--1.0018.
- The coupling is deliberately reported as one-way: prescribed pads influence
  the cloth but cloth reaction cannot move a finite-mass robot. P10 is a contact
  plumbing gate, not evidence of robot dynamics, conservative two-way momentum,
  or robust grasp policy behavior.
- P11 registers one topology-bound benchmark objective per construction:
  T-shirt sleeve tuck, shirt sleeve fold, jeans leg alignment, towel half-fold,
  and asymmetric-tie untangling. The four folding evaluators reject their
  unchanged states; the untangling evaluator correctly accepts its registered
  initially extended ties. All 5/5 remain invariant to rigid frame changes and
  pass their declared witness/anti-cheat gates.
- P11 validates semantic indexing, predicates, history/integrity boundaries,
  and false-positive resistance. It does not run a controller or dynamics
  policy, and its thresholds remain engineering priors.
- `control.py` now exposes a 14-channel backend-neutral bimanual target-rate
  schema: XYZ translation, XYZ rotation, and symmetric jaw aperture for each
  hand. The older six-channel clamp/roller schema remains the exact P6 API.

## 17--18 July 2026 -- P12 topology-safe T-shirt reset and release

Authoritative trace: `outputs/p12_topology_safe_flat_lay.json`. Authoritative
accepted/rejected motion frames:
`artifacts/frames/p12_topology_safe_flat_lay.npz`.

- The reset respects the closed body and tubular sleeves. Front/back body
  layers receive a declared 8 mm reset-only separation; each sleeve is flattened
  as a developable folded tube and filled by graph-harmonic extension from exact
  cuff/cap landmarks. A deterministic metric/edge preconditioner operates only
  at reset and is absent from runtime dynamics.
- IPC Toolkit supplies an operator-split proximity barrier, collision-free
  linear-trajectory step size, and exact post-step surface verification around
  Newton Style3D. This is not a monolithic incremental-potential solve, and IPC
  minimum separation is zero at welded seams; Newton proximity contact remains
  the finite-thickness provider.
- The accepted run advances all 180 steps (0.75 simulated seconds) with zero
  confirmed triangle crossings, zero IPC trajectory clips, nonzero causal
  barrier forces, and no checkpoint table penetration. Principal stretch spans
  0.6990--1.2307 over all checkpoints and finishes at 0.8923--1.1084; final
  maximum speed is 0.05243 m/s in the retained regeneration.
- Cleaning a nearly coincident sleeve fold-axis sample removed a 51.9-aspect-
  ratio sliver. The formerly retained gravity-release penalty ablation then
  stopped crossing, so it was rejected as causal evidence rather than silently
  preserved. The healthy canonical mesh has maximum panel aspect ratio 8.75.
- The replacement causal comparison is a declared 40-step, reset-only topology
  stress on the same healthy mesh. Both sleeve layers receive a 2.0 m/s relative
  closing velocity with 1.21e-10 kg m/s residual linear momentum; gravity,
  table, and air are disabled. Positions, velocities, time step, iterations,
  damping, textile, and finite penalty contact match exactly; only
  `ipc_self_contact` differs.
- The penalty-only stress develops three exact topology-local crossings at
  steps 32--37. The IPC branch remains exact-intersection-free for 40/40 steps,
  with a 0.525 N maximum reported barrier-force norm and zero CCD clips. This
  proves a topology-preservation distinction under the declared synthetic
  challenge, not nonlocal whole-garment tunnelling or a real handling load.
- Newton candidate pairs are independently confirmed by IPC predicates, and a
  whole-surface IPC query fails closed if a candidate was omitted.
- A globally scaled table CCD branch was rejected: the earliest resting vertex
  throttled every unrelated vertex and effectively froze the garment. The
  retained table guard snapshots the true pre-step origin, solves a local swept-
  sphere/top-plane time of impact, removes inward normal velocity with zero
  restitution, and corrects only impacted particles. Newton retains tangential
  Coulomb response.
- The local table guard records contact on 180/180 steps because many vertices
  rest on the plane, but it never scales the global cloth step. Recorded minimum
  accepted checkpoint clearance is approximately 1 micrometre and the normal
  response removes, rather than adds, kinetic energy.
- The retained result depends on the explicit topology-aware seed, conditioned
  mesh, exact audit, matched stress, barrier, and local table response. Rejected
  global-freeze and sliver-driven branches remain recorded rather than being
  promoted into evidence.

P12 proves one topology-safe reset/release mechanism. It does not prove that a
robot performed the flat lay or folded the T-shirt, and it does not establish
pressure-dependent thickness or real-garment calibration.

## 19 July 2026 -- P13 complete garment flat-lay catalogue and Isaac inspection

Authoritative catalogue trace:
`outputs/p13_garment_flat_lay_catalog.json`. Authoritative exact states:
`artifacts/frames/p13_garment_flat_lay_catalog.npz`, SHA-256
`0649585cbb4314b8aa298c9f4f02289bba15b247abd9133bde16ac2fea361e2c`.
Authoritative visual manifest: `renders/garment_catalog/manifest.json`, SHA-256
`0f5c9f7b5e73a824c1dcb28553dc00d2cdd9507b56d9d099737e9aefb01c14e6`.

- P13 registers an explicit topology-aware flat-lay strategy for every
  canonical construction and accepts 5/5. Every state retains its complete
  physical topology, is finite, has zero degenerate triangles, and has zero
  exact IPC-confirmed crossing pairs.
- Accepted exact states are: T-shirt 650 particles / 1,248 triangles / stretch
  0.6948--1.1695; shirt 1,104 / 2,114 / 0.6969--1.2324; jeans 991 / 1,912 /
  0.7378--1.2507; towel 273 / 484 / exactly isometric; asymmetric top 976 /
  1,788 / 0.7198--1.4776. The asymmetric 1.50 cap is an explicit reset gate,
  not a calibrated failure strain.
- The former asymmetric rectangular neck-facing strip was rejected: its closed
  curved attachment forced a minimum principal stretch near 0.096. It was
  replaced from first principles by separate curved front/back cut facings
  whose free edges are correctly longer than their attachment curves and whose
  22 mm shoulder joins close exactly. Internal shoulder-roll references remove
  the remaining exact triangle crossings.
- Protecting every source-curve control on both sides of eased seams was also
  rejected because it created 20--229 aspect-ratio slivers and a shirt seam
  fixed-point oscillation. Source fractions are now protected only when both
  complete seam references trace the same authored polyline in the same
  correspondence direction. All canonical panel meshes return below the
  aspect-10 and relative-area-error gates.
- Static preconditioning is panel-selective: the shirt moves only sleeves and
  collar pieces; the asymmetric top moves only its unequal sleeves. A physical
  particle shared with any unselected host is a hard Dirichlet boundary. The
  unit test proves sleeve-only relaxation changes selected interiors while
  leaving every welded body/armhole host vertex bit-exact.
- Denim requires a reported two-stage zero-gravity Style3D/IPC continuation.
  The retained run brakes at high-solver step 120, settles through step 100,
  finishes with 4.440 mm/s maximum and 1.500 mm/s RMS speed, preserves a
  0.395 x 1.026 x 0.143 m recognizable footprint, and remains exact-crossing-
  free. Stage-boundary velocity clearing is numerical reset plumbing, not a
  claim of calibrated denim equilibrium.
- The Isaac inspector uses the P13 NPZ directly. It retains all 45 actual cut
  panels and 175 construction-detail primitives through a one-way
  barycentric/thick-shell bridge, and its stage contains zero rigid-body
  dynamics. `1`--`5` select garments; `V` cycles front-owned, back-owned, and
  all-panel construction views.
- Fifteen 1,500 x 980 RTX captures are individually hash-addressed. Direct
  review exposed temporal front-detail ghosting in the first back-view pass;
  the renderer now discards three complete RTX histories after every visibility
  change. The regenerated shirt and asymmetric back views contain no hidden
  front layers, and the final render manifest passes all source, panel,
  ownership, pixel, and scene gates.
- Targeted construction/meshing/flat-lay tests pass 20/20; the new selective-
  relaxation, exact IPC-pair semantics, P13 artifact, and render-manifest tests
  pass within the 30-test targeted artifact suite. The authoritative pinned
  Newton 1.4 / Warp 1.15 environment passes the complete suite: 170 tests plus
  74 subtests in 155.48 s.
- Dossier v1.3 compiles to 30 pages (cover plus 29 numbered pages), 17 numbered
  figures, 48 linked sources, and 16.39 MiB. The full contact sheet and the new
  catalogue, table, garment-render, cover, claims, commands, conclusion, and
  sources pages were directly reviewed with no clipping or overlap.

P13 proves distinct garment construction, accepted topology-safe reset states,
and honest inspection. It does not prove calibrated drape, a robot-performed
flat lay, or a successful fold of any sewn-garment task.
