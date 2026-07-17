# The Triage Station: A Physically-Faithful Package-Triage Environment for Humanoid Robots in a Reconstructed Warehouse

**Status:** environment release · all reported numbers are measured from logged runs in this repository (`triage/*.log`, git history) — none are estimates.

---

## Abstract

We present a package-triage simulation environment modeled on a real industrial
workflow: a humanoid robot standing at a sortation cell must pick parcels from a
bin and place them **label-up** on a moving take-away conveyor, where an overhead
camera must optically decode each parcel's shipping barcode. The environment
combines (i) a photorealistic neural reconstruction (NuRec Gaussian splat) of a
real warehouse **with its scanned collision geometry**, so the robot walks on the
real building's uneven floor; (ii) a fully physical sortation cell — treadmill-driven
conveyors, a gravity transfer pan, a cleated return incline, and a drop-fed steel
bin — every mechanism validated by instrumented audits; (iii) a diverse parcel
population with real masses, dimensions and materials, including FEM-simulated
deformable poly bags; (iv) a free-standing Unitree G1 humanoid balanced by the
manufacturer's own pretrained locomotion policy — no world-weld, no stabilizing
constraints; and (v) a cheat-resistant optical verifier whose pass signal is a real
barcode decode from rendered pixels. We document the construction pipeline, the
governing equations and parameters, the verifier design, the measured validation
results, and the methodology ("measure before claiming; render before believing")
under which every subsystem was accepted. Task solving is deliberately left open:
this is an environment for policy builders.

---

## 1 Introduction

Contemporary humanoid demonstrations (e.g., Figure's *Helix* package-triage
livestream) show robots performing sustained logistics work: parcels of every
shape arrive continuously, and the robot's job is orientation-sensitive — a
package placed barcode-down is a failed sort, regardless of how gracefully it was
moved. Reproducing such a task in simulation is easy to do dishonestly: attach
parcels to grippers, weld the robot to the floor, read labels from metadata,
count successes with privileged state. Each shortcut produces an environment
whose solutions do not transfer.

This environment was built under a single governing rule: **the simulation bends
to reality, not the reverse.** Objects keep their real sizes, masses and surface
properties; the robot stands because a balance controller keeps it standing; the
verifier passes a parcel only if a real barcode decoder reads the label from the
tunnel camera's rendered image. Where an approximation was unavoidable it is
declared (§8) rather than hidden.

The second contribution is methodological. Every load-bearing claim in this
document traces to a logged, reproducible measurement, and the project history
(preserved in the repository) includes the *wrong* diagnoses and their
corrections. Several bugs reported here — a conveyor silently running at half
speed in interactive sessions, a collision-floor offset that exploded spawns,
a verifier gate that did not enforce its own documented criterion — were found
only because of this discipline, and each produced a rule that is now part of
the environment's regression suite.

---

## 2 Environment overview

### 2.1 Scene: a real warehouse, visually and physically

The scene shell is a neural reconstruction (NuRec Gaussian splat) of a real
warehouse interior, rendered photorealistically inside the simulator, paired
with the scan's triangle-mesh collider. Two properties follow:

- **Photorealism is genuine**: camera views used for the verifier and for
  policy observations show the real building — racks, signage, floor wear —
  not stylized CG. Correct compositing requires the renderer's NuRec settings
  (background and post-processing enabled) plus ray-traced lighting.
- **The floor is real**: a raycast survey (0.2 m grid) measured the collision
  floor at **6–14 cm above the nominal plane, varying across the room**. The
  robot therefore balances on the reconstruction's true uneven surface. This
  was discovered the honest way — a free-standing robot spawned at nominal
  height had its feet inside the floor mesh and was ejected by depenetration;
  the fix (spawn height from a local raycast) is part of the spawn doctrine.

The scene is Y-up with gravity $(0,-1,0)\cdot 9.81\,\mathrm{m/s^2}$, asserted
**and read back** at the start of every run.

### 2.2 The sortation cell

The cell reproduces the demo station's working triangle and is built
parametrically (`build_station.py` → `station_v1.usd` + `station_config.json`;
every load-bearing coordinate lives in the JSON):

| Element | Key parameters (measured/final) |
|---|---|
| Take-away conveyor | surface $y=0.749$, belt speed $0.35\,\mathrm{m/s}$, 11-tile kinematic ring |
| Scan tunnel | camera at surface $+0.52\,\mathrm{m}$, $2048^2$ render, 60 k-intensity lamp |
| Corner transfer | gravity pan, painted steel, $\approx 18^\circ$ |
| Return incline | $19^\circ$, cleated tiles (6 cm cleats), 12-tile ring |
| Steel bin (tray) | $0.60\times1.00$ m floor, tilted $0.58\!\to\!0.46$ toward the robot, walls 0.86–1.02, drop-fed over the far wall |
| Deck | white work surface at the robot's front |
| Dressing | 2 e-stops (tray corner + tunnel post, matching the demo reference frames), translucent plexi guards (verified translucent by a through-shot), bolt heads, floor striping, conduit |

The loop is **recirculating**: parcels discharged off the take-away cross the
pan, ride the cleated incline, and are launched over the bin's far wall back to
the robot — providing continuous arrivals without teleportation.

### 2.3 Parcel population

Thirteen parcel classes from a real-parcel manifest; each instance carries its
true dimensions, mass, and a Code-128 shipping label:

| Class | Count | Examples (L×W×H cm, kg) | Body |
|---|---|---|---|
| Poly bags | 5 | 41.1×23.2×4.3, 0.74 | **FEM deformable** |
| Small boxes | 3 | 16.1×13.4×5.8, 1.14 | rigid convex hull |
| Medium boxes | 2 | 44.1×24.7×16.2, 4.49 | rigid convex hull |
| Bubble mailers | 2 | 34.2×22.5×4.2, 0.61 | rigid convex hull |
| Flats | 1 | 1.8 cm thick | rigid convex hull |

Masses span 0.17–4.49 kg. Rigid friction: cardboard $\mu_s{=}0.8$,
$\mu_d{=}0.7$, restitution 0. Deformable poly bags are FEM volumetric bodies
(hexahedral resolution 8) with Young's modulus $E=35$ kPa (20 kPa was measured
to interpenetrate rigid contacts and eject bodies on recovery), Poisson ratio
0.45, density 145 kg/m³, and honest LDPE surface friction $\mu\approx0.2$ —
notably, a deformable's own material friction governs its contacts outright,
so slick bags are genuinely slick.

**Labels are physically real.** Every label is rendered at the true 4×6″
(15 cm) physical size regardless of parcel size — small parcels do *not* get
proportionally shrunken (sub-spec) barcodes. Textures are generated on
aspect-correct canvases per face: square textures UV-stretched onto faces with
aspect ratio $<0.7$ were measured to squeeze bar widths below decodability.
Poly-bag textures carry procedurally generated crinkle shading (fold-line
polylines + blur) in the demo's color palette, with the label patch composited
at physical scale after shading.

### 2.4 The robot

A Unitree G1 humanoid (43 DoF including two 7-DoF Dex3 dexterous hands),
**free-standing**: the articulation root is unconstrained. Balance and
locomotion come from the manufacturer's own pretrained flat-terrain policy
(`unitree_rl_gym`, 12 leg DoF, recurrent LSTM actor, *blind* — proprioception
only, no external state), the same controller class Unitree deploys on physical
G1s, running with their published deployment gains:

$$k_p = [100,100,100,150,40,40]\times2,\quad k_d=[2,2,2,4,2,2]\times2$$

The upper body (waist, arms, hands) is position-controlled independently —
mirroring the real deployment architecture in which the legs policy balances
while a separate controller works the arms. Arm motion physically perturbs
balance and the legs visibly compensate; collisions with the station can trip
the robot. This is intended.

---

## 3 Construction pipeline

### 3.1 Conveyance: the treadmill doctrine

PhysX surface-velocity conveyors move rigid bodies but were **measured to move
FEM deformables at exactly 0.000 m/s**. Conveyance is therefore implemented as
*treadmills*: rings of kinematic tiles that physically translate, carrying
everything by real friction (measured: rigid 0.398 m/s, FEM bag 0.406 m/s at a
0.4 m/s command). The mechanism's hard-won rules:

1. **Exact rings.** Tile ring span must equal $n\cdot\ell_{tile}$ (here
   $\ell=0.3$ m); anything else opens support holes at the wrap seam.
2. **Edge-wrap discharge.** Tiles carry parcels to the discharge edge (a real
   end-roller tip-off), then dip 0.45–0.5 m over ≈8 cm of travel past the
   edge, return underground, and teleport back while deep.
3. **The wrap teleport is a gun.** A kinematic pose jump of $L=3.05$ m in one
   $\Delta t = 1/120$ s step implies a swept velocity
   $$v_{\text{implied}} = L/\Delta t \approx 366\,\mathrm{m/s},$$
   and speculative/CCD contact generation will fire parcels across the room
   even with a 5 cm clearance (caught by high-speed trace). Tiles therefore
   collide **only at full height** ($\Delta y > -1$ mm) and every collision
   toggle is followed by a physics flush — on the GPU pipeline, unflushed
   toggles may silently not apply.
4. **Never place furniture across a discharge.** A full-height guide fin at
   the belt end face-planted every arriving parcel — found only by rendering
   the corner, not by telemetry.

### 3.2 Friction pairing and gravity transfers

PhysX combines pair friction by **averaging** by default, which silently
manufactures grip: cardboard (0.8) on steel (0.12) averaged to 0.46, and a 14°
pan held every parcel. Steel surfaces therefore declare
`frictionCombineMode = min`:

$$\mu_{\text{pair}} = \min(\mu_{\text{steel}},\ \mu_{\text{parcel}}),$$

and a parcel slides when $\tan\theta_{\text{pan}} > \mu_{\text{pair}}$. With
honest pairing, the corner pan runs at ≈18° and the cleated 19° incline carries
slick LDPE bags on its cleats rather than by fictional friction.

### 3.3 Bin filling: exact packing + staged release

Naive grid spawns interpenetrate (a 0.20 m grid vs 32–44 cm boxes ejected
parcels 6.5 m through depenetration). The pile spawner is a first-fit-decreasing
shelf packer using **exact yaw-rotated footprints**: a parcel of footprint
half-extents $(h_x,h_z)$ at yaw $\theta$ occupies the AABB

$$h_x' = |\cos\theta|\,h_x + |\sin\theta|\,h_z,\qquad
  h_z' = |\sin\theta|\,h_x + |\cos\theta|\,h_z,$$

packed with per-material clearances (+5 cm for FEM bulge), deformable bags on
the bin floor (an unheld bag packed high toboggans off box tops at
$\mu=0.2$), rigid layers above, each layer based on the *real* maximum height
of the layer below. Because real bins fill parcel-by-parcel, upper rigid layers
spawn kinematically held and release one layer at a time onto a settled pile
(belts frozen during fill; the treadmill phase state is incremental, so
freezing is wrap-safe). A dry-run checker proves zero pairwise overlap before
any simulation.

### 3.4 Locomotion integration

The balance policy consumes a 47-dimensional observation, assembled entirely
in the **pelvis frame** (making it world-up-axis agnostic; this environment is
Y-up while the policy was trained Z-up):

$$o_t = \big[\ \omega_b\cdot0.25;\ \ \hat g_b;\ \ c\cdot(2,2,0.25);\ \
(q-\bar q);\ \ \dot q\cdot0.05;\ \ a_{t-1};\ \ \sin 2\pi\phi;\ \cos 2\pi\phi\ \big]$$

where $\omega_b$ is body angular velocity, $\hat g_b = R^\top\hat g_w$ the
projected gravity, $c=(v_x,v_y,\dot\psi)$ the velocity command, $q,\dot q$ the
12 leg positions/velocities against the deployment stance $\bar q$, and
$\phi=(t \bmod T)/T$ a gait clock with $T=0.8$ s. Actions map to leg PD targets
$q^* = \bar q + 0.25\,a_t$ at 50 Hz (validated additionally at 60 Hz).

Two integration rules were paid for in falls and are now doctrine:

- **Spawn from the measured floor**: pelvis height = (local raycast hit)
  $+\,0.76$ m — and the ray must be cast with the robot parked elsewhere,
  or it measures the robot's own head.
- **The loop time base must match the stepper**: an interactive
  `step(render=True)` advances one *render* frame (1/60 s = two physics
  substeps), not one physics step. Running the gait clock on the wrong base
  halves its speed and the policy falls within half a second. (The same bug
  had the interactive conveyor running at half speed — invisible with a welded
  robot, fatal with a balancing one.)

At zero command the blind policy marches in place and drifts (~0.3 m/s); a
station-keeping loop converts parking drift into small body-frame corrections,
$c_{xy} = \mathrm{clip}\big(1.2\,R^\top e_{xz},\ \pm0.15\big)$, as real
velocity-command deployments do.

---

## 4 Task and verifier

### 4.1 Task definition

Parcels arrive continuously in the bin via the recirculating loop. For each
parcel the operator must **pick it from the pile and place it label-up on the
moving take-away**, where the scan tunnel reads it. The environment defines the
task; solving it (scripted or learned) is intentionally out of scope for this
release.

### 4.2 Verifier (`verifier_tri.py`)

The verifier uses only sensors a real sortation line has:

- **Photo-eye (throughput).** A beam segment across the belt at the scan line,
  mounted at surface $+1.2$ cm — geometric intersection against rigid OBBs and
  FEM surface points. (At a +6 cm mount, 4.2 cm mailers and 1.8 cm flats passed
  underneath uncounted; the low mount is a measured fix.) A rising edge counts
  one processed parcel.
- **Optical scan (correctness).** While the beam is blocked, the tunnel
  camera's rendered image is decoded by a real barcode reader (zxing-cpp)
  every 15 steps; a decode is attributed to the parcel nearest the tunnel.
  There is **no metadata path**: an unreadable, occluded, or face-down label
  simply does not decode.
- **Label-up state signal** for rigids: $\hat n_{\text{top}}\cdot\hat y$
  (diagnostic; the camera remains the truth).
- **Honesty monitors.** Per-step jump/teleport detection on every parcel;
  any violation fails the episode outright.

$$\textbf{PASS} \iff \frac{N_{\text{decoded}}}{N_{\text{processed}}} \ge 0.80
\ \wedge\ \text{zero honesty violations}.$$

The 0.80 gate mirrors realistic single-read rates measured in-environment
(12–13/13 manifest decode at tunnel optics; the marginal read is a real
small-label effect, and belt-pass scanning gives multiple frames per parcel).

### 4.3 Verifier validation

The verifier itself was tested like a subsystem, not trusted:
self-tests (geometry, attribution, edge cases) all pass; a live validation run
with a deliberately label-down mailer counted 3/3 parcels, decoded 2, correctly
refused the face-down label, and bound the gate (0.67 < 0.80 → FAIL); an
**injected teleport cheat** (parcel warped across the scan line) was caught by
the jump monitor and failed the episode. One real defect was found and fixed
during environment audits: the PASS expression omitted its documented no-jam
term (a run printed PASS with a parcel on the floor); the gate now enforces
every documented criterion.

---

## 5 Validation results (measured)

| Subsystem | Result |
|---|---|
| Gravity | $(0,-1,0)\cdot9.81$ read back every run |
| Settle | pile parcels rest on spawn surfaces, residual velocity 0.000–0.006 m/s |
| Conveyance | rigid 0.398 m/s, FEM bag 0.406 m/s at 0.4 command; in-station 0.30–0.35 m/s |
| Flow audit (standard, 9 parcels) | **PASS** repeatedly: 0 teleports, 0 leaks, 0 NaN, 0 speed violations, 6/6 circulators delivered, pile settled |
| Flow audit (density, 14-in-cell) | **PASS ×4 reproducible** under the strict gate (incl. no-jam term) |
| Bin capacity | measured: 17–18 parcels in-cell sheds 1–2 gently per run (heap at rim); 14 is the shed-free robot-less operating point — higher density requires an operator draining the bin, as in the demo |
| Label optics | 12–13/13 manifest decode at tunnel camera; square-texture stretch and sub-physical label sizes are decode-killers (fixed) |
| Verifier | self-test pass; live 5/5 checks; injected cheat caught |
| Locomotion (flat) | 20 s upright, walk 3.29 m at 0.5 m/s command, turn on command; PASS at 200 Hz/50 Hz and 120 Hz/60 Hz |
| Locomotion (in station) | upright on the reconstructed floor; 120 s interactive session with driving: **0 falls**; station-keeping parks at ±3 cm |
| Collision world survey | raycast map: real floor +6–14 cm, belt 0.75, guard 0.78, tray floor 0.49, plexi trim 1.20 — map self-consistent with built geometry |
| Performance | ~30 ms/step headless (RTX 3090) full station with FEM + robot; interactive sessions render photoreal NuRec live |

Every failure encountered en route is preserved in the repository logs with its
diagnosis — including three initially *wrong* diagnoses (a medbox "cleat
escape" that was actually pile rollout; a "splat-blob" render occlusion that
was a nondeterministic frame-grab flake; a chirality inference from a
degenerate top-down camera) — each retracted and corrected by direct
measurement. We consider this failure record part of the environment's
documentation: it states precisely which pitfalls the current design guards
against.

---

## 6 Realism methodology

Three rules governed acceptance of every subsystem:

1. **Measure before claiming.** No property is asserted from intention; the
   audit harness (teleport/leak/NaN/speed detectors, segment events, jam
   detection, settle checks) must pass, and its gate must enforce every
   documented criterion.
2. **Render before believing.** Multiple defects (the discharge fin, the
   fallen spawn, panel translucency) were invisible in telemetry and caught
   only by generating and *looking at* frames. No interactive session is
   handed to a user without a rendered frame of the same scene state.
3. **Reality sets parameters; the sim does not negotiate.** Real masses, real
   dimensions, real label sizes, honest friction pairs, a real balance
   controller, a real decoder — and where the demo's physicality mattered
   (tote proportions, e-stop placement, bag palette), the reference footage
   was measured against renders side-by-side.

---

## 7 Declared approximations

1. **Poly bags are FEM volumetric pillows**, not thin film around discrete
   contents. Mass, size, friction and compliance are honest; bag construction
   is not literal. (Largest single fidelity gap for grasp learning.)
2. **Rigid parcels have uniform-density inertia**; real contents shift.
3. **Arm/hand PD gains are plausible but not system-identified** to hardware
   (leg control *is* the manufacturer's deployment configuration; hand torque
   caps ≈ real Dex3 limits).
4. **The interactive policy rate is 60 Hz vs the native 50 Hz** — validated
   stable at both; command-to-speed gain runs ≈1.5× at 60 Hz.
5. **The conveyor return run is abstracted** (tiles wrap underground,
   collision-gated); the working surface is fully physical, as a real belt's
   return side never touches a parcel.
6. **Balance-during-manipulation is unexplored territory**: all manipulation
   reach data in the repository predates the free-standing robot and must be
   re-established on the balancing base by whoever builds policies.

---

## 8 Intended use

The environment targets: (a) training and evaluating pick-and-orient policies
under a sensor-realistic, cheat-resistant success signal; (b) teleoperated
demonstration collection (a keyboard interface drives locomotion commands,
waist, arms and fingers, with a robot-head camera view); (c) studying
loco-manipulation interference — the balance policy visibly fights arm swings
and station contacts, which is precisely the coupling fixed-base rigs hide.

The verifier's scan-rate gate doubles as a sparse task reward; the photo-eye
provides throughput; the honesty monitors disqualify degenerate policies by
construction.

---

## Provenance

All quantitative claims trace to logged runs in `triage/` (audit series
`audit*.log`, locomotion series `p6_loco*.log`, optics `labels_check`,
verifier `vlive*.log`, floor survey `p6_scan_floor.log`) and to the git
history, which additionally preserves every retracted diagnosis alongside its
correction.
