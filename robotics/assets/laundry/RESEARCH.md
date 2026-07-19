# Physics-first robotic laundry folding

Status: pre-build research dossier and falsifiable implementation plan, 16 July
2026. No laundry simulation, calibrated textile, successful fold, or sim-to-real
result is claimed here. This document decides what must be measured and what
must be true before a polished render or policy can be called physically
faithful.

Target scene/runtime: Isaac Sim 5.1 / Omni Physics 107.3.26 on Windows

Candidate textile runtime: NVIDIA Newton 1.4 / Warp, after isolated coupling and
constitutive-model probes. The repository environment currently contains Newton
1.3.0 and Warp 1.15.0; an upgrade is a proposed experiment, not an implicit
dependency change.

Long-term task: a robot removes an unknown household garment from a laundry
pile or basket, singulates it, identifies its state and category, unfolds it,
folds it into a category-appropriate configuration, and places it in a stable
stack. The first physical validation task is intentionally much smaller: one
measured rectangular woven-cotton towel, one calibrated table, and one physical
half-fold.

## 0. Executive decision

High-fidelity laundry folding is feasible within a declared material and motion
envelope. It is not feasible by treating every garment as an isotropic spring
net, increasing damping until it stops jittering, or judging success from a
pretty silhouette.

Laundry couples mechanisms that common robot cloth demos routinely collapse:

1. woven and knitted structures have nonlinear, direction-dependent tension,
   shear, bending, and hysteresis;
2. fabric is extremely thin, so reliable two-sided self-contact, edge--edge and
   face contact, compressed thickness, and layer ordering dominate a fold;
3. table, fabric--fabric, finger-pad, and trim friction depend on face,
   direction, load, sliding speed, surface finish, and environmental condition;
4. pressure and dwell time can change the persistent crease through internal
   yarn/fibre friction and plasticity, rather than merely changing the current
   elastic bend angle;
5. seams, hems, collars, cuffs, pockets, elastic, ribbing, buttons, and zippers
   are local structures, not a texture painted on a homogeneous sheet;
6. air drag and permeability matter during drops, shaking, and flinging because
   a garment has high area and low mass; and
7. a real grasp is distributed compliant contact whose equal-and-opposite force
   disturbs the robot. Pinning vertices to a moving gripper is not a grasp.

The installed PhysX surface-deformable system is useful as an engine baseline,
but it cannot be the entire fidelity solution. Its current public documentation
describes XPBD FEM with corotational linear elasticity, no cloth aerodynamics,
no independent surface stretch stiffness, and no separate simulation/collision
surface mesh. The broader surface-deformable documentation also leaves material
and attachment limitations that conflict with garment panels and calibrated
grasping. In particular, one isotropic Young's modulus and Poisson ratio cannot
represent independently measured warp, weft, bias shear, and knit response.

The recommended architecture is therefore modular and causal:

- **Isaac Sim owns** USD scene composition, RTX rendering, cameras and other
  sensors, robot assets, experiment UI, recording, and dashboard integration.
- **A textile dynamics module owns** panel-space nonlinear orthotropic membrane
  response, directional bending, thickness/contact, self-collision, seams,
  friction, damping, and all textile internal state.
- **A crease module owns** elastic rest angle, stick--slip internal friction,
  plastic rest-angle evolution, dwell/history, and recovery. It consumes actual
  contact pressure and time; there is no scripted "crease" event.
- **An aerodynamic module owns** wind-relative per-triangle forces and calibrated
  permeability for dynamic manipulation. It is inactive only when a scale
  analysis and held-out experiment show that it is negligible.
- **A coupled robot/contact module owns** the same contact pair on both sides:
  cloth impulses act on robot links and robot contact acts on cloth. The first
  candidates are a unified Newton VBD/AVBD solve and Newton 1.4's experimental
  symmetric coupled-solver path; neither is accepted until it passes explicit
  conservation and gripper tests.
- **An offline contact oracle owns no runtime task**. C-IPC or an equivalent
  intersection-free solve is used on small cases to expose contact failures and
  establish reference trajectories, not to make an interactive claim it cannot
  run.

The first physical-fidelity claim must still be a measured rectangular towel,
not a random T-shirt downloaded from the internet. The towel removes seam
topology and category uncertainty so gravity, anisotropy, bending, self-contact,
friction, compression, grasping, and folding can be identified separately. The
repository now builds a T-shirt and four other explicit constructions as
engineering-prior mechanism gates; this does not promote them to calibrated
canonical tasks. A named T-shirt claim still requires its own held-out coupon,
drape, dynamic, grasp, and fold evidence.

## 1. Evidence vocabulary

| Label | Meaning |
|---|---|
| **STANDARD** | A published ISO, ASTM, or AATCC test procedure or another normative requirement. Access restrictions and edition are recorded. |
| **MEASURED** | A physical experiment on an identified specimen with enough conditions to interpret it. |
| **PAPER** | A peer-reviewed or clearly identified preprint method/result; it is evidence for a method, not automatically for our garment. |
| **ENGINE** | Official engine documentation or a locally reproduced capability in the pinned runtime. |
| **CODE-AUDIT** | Behaviour established by reading the exact installed source/release, still requiring an executable probe. |
| **DERIVED** | A calculation from identified inputs; it is not an independent measurement. |
| **PRIOR** | A model form, parameter, tolerance, or acceptance band awaiting calibration. |
| **OPEN** | A required specimen, measurement, licence, parameter, or validation result that we do not yet possess. |

A coefficient copied from a paper about another fabric is a **PRIOR**, not a
measurement. A parameter recovered from one fold is a fit, not validation. A
solver that produces a convincing animation has not demonstrated correct force,
pressure, layer topology, or response on a held-out trajectory.

Every published chart, render, video, and PDF must distinguish:

- measured real data;
- simulator output from a named configuration;
- a literature value or starting prior;
- a derived quantity;
- and an uncalibrated visual-only demonstration.

## 2. What the environment must mean

### 2.1 Long-term episode

The complete environment eventually supports this causal sequence:

1. one or more dry garments occupy a measured basket or table in an unknown but
   reproducible state;
2. the robot perceives only configured sensors and its proprioception;
3. it contacts and singulates exactly one garment without hidden correspondence
   or attachment;
4. it infers or exposes semantic parts and material orientation;
5. it unfolds/canonicalises the garment;
6. it executes a category-specific sequence of grasps, placements, folds, and
   optional physical pressing;
7. it releases the garment and permits it to settle under physics; and
8. an evaluator uses geometry, material coordinates, topology, pressure/force
   history, and task events independently of the policy.

This is a family of tasks, not one universal final pose. A towel, T-shirt, pair
of trousers, sock, hoodie, and fitted sheet have different valid symmetries,
fold graphs, seams, layer order, and practical success criteria.

### 2.2 First canonical episode

The first reproducible episode is deliberately diagnostic:

- one identified, conditioned, dry, rectangular woven-cotton towel;
- dimensions, areal mass, thickness-versus-pressure, yarn directions, face/back,
  edge construction, and all fitted parameters stored with a specimen ID;
- a level rigid table with measured surface roughness/material and calibrated
  cloth--table friction;
- a bimanual robot with explicit compliant fingertip pads and measured actuator,
  controller, and force limits;
- towel initially flat within a declared geometric tolerance, with no initial
  interpenetration or stored elastic energy;
- robot grasps the two material-coordinate corners of one short edge, lifts,
  moves that edge to the opposite short edge, places it, releases it, and allows
  it to settle; and
- the task terminates after success, loss of the towel, unsafe force, invalid
  topology, robot failure, or timeout.

The flat initial state is a calibration task, not the final manipulation claim.
Later variants start from a registered crumpled state and require
canonicalisation before the same fold.

No numerical dimension or success tolerance is frozen until the real towel,
table, gripper, and metrology are selected. Defaults used to debug code are
visibly marked **PRIOR-ONLY / NOT PHYSICALLY CALIBRATED**.

### 2.3 Success predicate

A fold succeeds only after the robot has released the garment and a declared
settling window has elapsed. The predicate contains all of the following:

- the intended material edge maps to the intended target edge within a measured
  position/orientation tolerance;
- the fold curve lies near its target in material coordinates, not merely in a
  camera silhouette;
- the intended layer ordering is correct across sampled material regions;
- semantic corners/landmarks and the garment's canonical orientation are within
  their category-specific tolerances, modulo declared symmetries;
- stack height, projected footprint, coverage, and overhang lie inside declared
  bands;
- no disallowed self-intersection, table penetration, trim penetration, tear, or
  extreme strain occurred anywhere in the trace;
- no hidden attachment, fixed vertex, pose snap, or kinematic override was used;
- grasp forces, slip, contact pressure, robot effort, and crease pressure stayed
  inside declared safety/material envelopes; and
- the final state remains stable for the settling window without robot contact.

All thresholds are **OPEN** until linked to task utility, annotator agreement,
instrument uncertainty, and real-fold distributions. A scalar reward threshold
does not define success.

### 2.4 Fidelity claim we are willing to make

The first defensible claim is:

> For named textile, seam, table, and gripper specimens, conditioned and tested
> in a declared temperature/humidity range, the simulator predicts held-out
> quasi-static and dynamic marker trajectories, force/pressure histories,
> drape, crease recovery, grasp slip, layer topology, and fold outcomes within
> stated experimental and numerical uncertainty over a declared motion range.

"Realistic laundry" without that envelope is not a scientific claim. Wet
laundry, electrostatics, lint, damage, unusual trims, and garments outside the
tested construction remain extrapolation until separately validated.

## 3. Causal chain and anti-cheat invariants

A successful end-to-end trace preserves this chain:

1. an unstrained panel-space pattern and seam graph instantiate the garment;
2. gravity, contact, and internal forces produce the observed initial state;
3. robot torques/commands move physical links subject to dynamics and limits;
4. finger pads approach without initial penetration;
5. distributed contact pressure, friction, and pad compliance form a grasp;
6. equal-and-opposite contact wrenches alter both cloth and robot;
7. membrane, shear, bend, damping, contact, and aerodynamic forces evolve each
   physics substep from current state and history;
8. self-contact preserves thickness and layer order as the garment folds;
9. local pressure and dwell can alter crease internal variables;
10. the gripper opens, contact disappears, and the cloth settles freely; and
11. the evaluator reads the recorded causal trace and settled state.

Hard failures include:

- teleporting, snapping, keyframing, or directly overwriting cloth vertices;
- welding/pinning vertices to the gripper and calling the result frictional
  grasping;
- driving a collision-only kinematic hand that never receives cloth reaction;
- disabling self-collision, collision pairs, or gravity during a difficult part;
- changing rest shape or material parameters after observing the desired fold;
- adding arbitrary global damping to hide instability or erase motion;
- using an image-space target force or a scripted fold curve;
- counting a fixed-point diagnostic mode as task success;
- creating visual wrinkles that affect scoring but not collision or mechanics;
- clipping one layer through another, then repairing the final mesh;
- fitting parameters on the exact evaluation motion or initial state;
- permitting nonphysical forces whose equal-and-opposite reaction is omitted;
- declaring success while the robot still holds or presses the garment; and
- editing the final video to hide a topology or stability failure.

Diagnostic constraints are permitted only in isolated tests, must be rendered
and logged as such, and cannot satisfy an end-to-end predicate. For example,
pinning two corners is useful in a drape coupon; it is not evidence of a grasp.

## 4. Physical state and governing mechanics

### 4.1 Material coordinates and state

Each garment begins as one or more two-dimensional material panels. For a panel
with material coordinate `X = (u, v)`, the simulated midsurface is
`x(X, t) in R^3`. Warp/course and weft/wale directions are stored in panel space
and transformed with the surface; they are not inferred from world axes.

The minimum state is:

- nodal positions `x`, velocities `v`, and areal masses;
- panel rest coordinates and triangle deformation gradients;
- seam/stitch connectivity and local construction labels;
- per-region membrane, shear, bending, damping, thickness, friction, and
  aerodynamic parameters;
- per-hinge or continuous crease internal variables;
- contact manifold, layer/side identity, normal/tangential traction, and slip
  history;
- robot generalized position/velocity and actuator/controller state; and
- air state, time, solver state, random seed, and provenance.

The semidiscrete dynamics have the form

`M x_ddot = f_mem + f_bend + f_seam + f_damp + f_contact + f_aero + M g`,

coupled to robot equations

`M_r(q) q_ddot + C(q,q_dot) + g_r(q) = tau + J_c(q)^T lambda_c`.

The same contact multiplier/traction `lambda_c` must appear with opposite sign
on the textile and robot. Numerical splitting may exchange equivalent impulses,
but a one-way moving obstacle is not the final model.

### 4.2 Nonlinear orthotropic membrane response

Fabric must not be identified by one Young's modulus. Let `a_w` and `a_f` be the
material warp/course and weft/wale directions, `F_s` the in-surface deformation
gradient, and define directional strains from `F_s a_w`, `F_s a_f`, plus a
shear-angle change `gamma`. A practical calibrated energy is

`W_mem = psi_w(e_w) + psi_f(e_f) + psi_s(gamma) + psi_c(e_w,e_f,gamma)`.

The one- and multi-dimensional response functions may be tabulated, spline-
based, piecewise polynomial, or derived by yarn-level homogenisation. They must
capture the observed nonlinear toe region, direction asymmetry, strain
stiffening, coupling, and cyclic hysteresis without producing negative tangent
stiffness outside a deliberately modelled regime.

For woven cloth, warp, weft, and bias shear are distinct. For knits, the loop
topology yields much larger, nonlinear extension and different course/wale
response; merely lowering a woven modulus is inadequate. The data-driven cloth
literature demonstrates that measured material-specific nonlinear stretch and
bend models visibly distinguish interlock, cotton, wool, and denim. Yarn-level
homogenisation is an offline option when construction data exists; coupon-fitted
shell response is the more practical runtime target.

Strain limiting is a numerical guard only when tied to measured ultimate or
operational strain. A universal 0% stretch constraint would make knits wrong;
an overly compliant penalty would make woven cotton rubbery.

### 4.3 Directional bending and damping

For adjacent triangles sharing edge `e`, let `theta_e` be dihedral angle and
`theta_e^r` its current elastic/plastic rest angle. A simple discrete energy is

`W_b,e = 0.5 k_b(e, direction, curvature) (theta_e - theta_e^r)^2`.

Real cloth may have nonlinear moment--curvature response, different warp/weft/
bias rigidity, face asymmetry, and bending hysteresis. Pure-bending coupon data
is therefore preferred over deriving bend stiffness from tensile modulus and
an arbitrarily chosen shell thickness. Mesh-discrete stiffness must be converted
so the same specimen does not become stiffer merely because it is remeshed.

Damping is also identified, not used as a visual knob. Candidate components are
material/cyclic damping, bending-rate damping, contact dissipation, aerodynamic
loss, and actuator/pad damping. Each must be separable in a calibration test.

### 4.4 Compression, thickness, and pressure

Cloth has small but nonzero thickness and becomes a multilayer stack. Its normal
response is pressure-dependent and hysteretic. Let measured compressed thickness
be `h = h(p, loading_direction, history, region)`, where `p` is contact pressure.
The contact model should reproduce loading/unloading thickness curves and stack
height, rather than assigning every vertex an oversized collision sphere.

Pressure means physical normal traction. For a contact patch `A_c`,

`F_n = integral_Ac p(x,t) dA`,

and a crease exposure can be summarized without losing the field as, for
example, `I_p(x) = integral p(x,t) dt`. Neither peak force divided by an unknown
area nor a keyboard command is a pressure model. The trace records patch area,
pressure distribution, total normal/tangential force, dwell, and uncertainty.

### 4.5 Friction is a family of responses

The relevant interfaces are at least:

- cloth face--table and cloth back--table;
- face--face, face--back, and back--back self-contact;
- cloth--finger pad and cloth--rigid gripper structure;
- seams/hems/trims against cloth and scene surfaces; and
- possibly garment--garment contact for piles and stacks.

A starting law may be load-dependent anisotropic dry friction,

`|t_i| <= mu_i(N, speed, direction, side, humidity) N`,

with a measured static-to-kinetic transition and, where supported by data, a
relation such as `F = k N^n`. The exact law is selected from ramp, pull, and
cyclic tests. A single isotropic Coulomb coefficient may remain as a documented
baseline, but it cannot silently become the fidelity model.

### 4.6 Persistent creases: elastic bend is not enough

A fold can recover immediately, relax slowly, or remain visibly creased after
pressure. Recent work attributes persistent wrinkles to interacting internal
yarn/fibre friction and plasticity, with stronger time dependence under longer
dwell. That paper provides a useful model structure but calls its own treatment
physics-inspired and accelerates time for animation; its numerical parameters
must not be copied as material truth.

Our candidate per-hinge state is:

- `theta_0`: manufactured elastic rest angle;
- `theta_a`: internal-friction anchor;
- `theta_p`: plastic rest-angle shift;
- `tau_s`: accumulated stick/dwell state;
- `tau_p`: accumulated plastic/hardening state; and
- optional recovery/aging state conditioned on humidity and temperature.

One candidate moment is

`M_e = k_b (theta - theta_0 - theta_p) + c_b theta_dot + M_f(theta-theta_a,tau_s)`.

The anchor sticks until a calibrated, dwell-dependent moment/strain threshold
is exceeded, then slips. Plastic rest-angle evolution begins only beyond a
measured yield criterion and can harden with dwell. Recovery evolves on measured
time scales after unloading. Pressure may alter these rates or thresholds only
if multi-pressure crease tests identify that dependence.

The model must reproduce, on held-out cases:

- fold angle during load;
- recovery angle as a function of time after release;
- dependence on warp/weft/bias fold direction;
- force/pressure and dwell dependence;
- repeated-cycle hysteresis and residual angle; and
- spatial crease width/sharpness at the simulation mesh's converged resolution.

ISO 2313-1 and AATCC TM66 provide controlled crease-recovery procedures. Their
angles are valuable observables, but ISO explicitly cautions that results from
very different fabric families are not directly comparable. We therefore store
the test method and specimen construction with every result.

### 4.7 Seams, hems, panels, and trims

A garment is assembled from sewing patterns. Abstractly welding a closed 3D
surface loses seam allowance, fold, thread constraint, local mass, and bending
stiffness. Research on cloth seams shows that seam and interlining construction
materially change drape; "True Seams" further models seam allowance folds and
stitches rather than treating a seam as an infinitesimal edge.

The asset representation requires:

- original 2D panels with grain/course orientation and unit scale;
- stitch pairs, stitch spacing/model, seam type, allowance, and construction
  order;
- local regions for hems, collars, cuffs, plackets, waistbands, pockets, ribbed
  knit, elastic, reinforcement, and interlining;
- explicit rigid/deformable trims when their mass/contact matters;
- semantic landmarks, boundaries, symmetry, inside/outside, and face/back; and
- a collision-valid physical mesh separate from a high-resolution render mesh.

Procedural pattern systems such as GarmentCode and structured public garment
datasets are useful asset sources. Their material labels and synthetic drape are
priors, not measurements of a physical item. Every asset needs a licence record,
topology audit, unit audit, non-manifold/intersection repair report, and an
identified material profile before it enters a validation set.

### 4.8 Air, porosity, and dynamic manipulation

For a triangle with area `A`, unit normal `n`, centroid velocity `v_t`, and
wind `v_air`, let `v_rel = v_air - v_t`. A starting normal drag model is

`f_D = 0.5 rho_air C_D(Re, porosity, angle) A |v_rel dot n| (v_rel dot n) n`,

with calibrated tangential drag/lift if required. Pressure leakage through a
porous textile reduces the effective normal loading; porosity/permeability must
therefore be measured or fit from dynamic data rather than hidden in frame
damping.

Air is likely secondary during a slow table fold and important during a corner
drop, shake, toss, or FlingBot-style dynamic flattening. That hypothesis is
tested by force-scale analysis and held-out marker trajectories. Full CFD is not
the default runtime. It becomes warranted only if the calibrated triangle model
fails the required motion envelope and the added cost is justified.

### 4.9 Mechanisms deliberately deferred

The initial environment is dry, clean laundry under controlled laboratory
conditions. The following are separate models, not randomization sliders:

- water uptake, wet mass distribution, capillarity, adhesion, and evaporation;
- electrostatic attraction;
- fibre shedding, lint, pilling, and wear;
- tearing, stitch failure, permanent tensile damage, and cutting;
- thermal ironing and coupled heat/moisture transport;
- detergent/softener residue and contamination; and
- human skin contact.

They remain visible scope limitations until a later task actually needs them.

## 5. Physical calibration programme

### 5.1 Specimen control and instrumentation

Material identification begins before simulation. Each physical item receives:

- immutable specimen and construction IDs;
- manufacturer/product/size/lot where known;
- fibre-content label and macro photographs of face, back, edges, and seams;
- measured panel geometry, grain/course direction, mass, and damaged/used state;
- conditioning temperature, relative humidity, conditioning time, and test time;
- test-machine, load-cell, camera/scanner, pressure-film/mat, and calibration IDs;
- raw observations, uncertainty, preprocessing, rejected-run reason, and operator;
- a train/validation/test assignment made before parameter fitting; and
- a content hash linking raw data, processed data, fitted profile, and code.

The real and virtual coordinate systems share fiducials. Registered optical or
motion-capture markers should be sufficiently light and sparse that a control
experiment can bound their influence. Dense 3D scans and silhouettes supplement
markers; they do not replace force, pressure, and material-coordinate data.

### 5.2 Coupon and whole-garment tests

| Test | Controlled variables | Primary observables | Parameters/mechanism identified | Evidence/method |
|---|---|---|---|---|
| Panel geometry and mass | conditioned specimen, scale | dimensions, panel mass, areal density | rest geometry, mass distribution | ASTM D3776-style mass per unit area; **STANDARD/MEASURED** |
| Thickness and compression | presser area, normal pressure, load/unload rate, face | `h(p)`, compression work, resilience, hysteresis | contact thickness/compliance | ASTM D1777 plus KES-FB3-style pressure cycle; **STANDARD/MEASURED** |
| Uniaxial cyclic tension | warp/course, weft/wale, bias; rate; cycle count | force--extension loops, residual strain | nonlinear membrane and damping/hysteresis | KES/FAST-style or instrumented coupon; **MEASURED** |
| In-plane shear | direction, normal tension, rate, cycles | shear force/torque versus angle, hysteresis | `psi_s`, coupling, shear damping | KES-FB1/FAST-style; **MEASURED** |
| Pure bending | axis/direction, face, curvature, rate, cycles | moment--curvature loop | directional nonlinear bend and hysteresis | KES-FB2-style; **MEASURED** |
| Cantilever/loop bending | specimen direction and overhang | bending length, flexural rigidity | independent low-cost bend check | ASTM D1388; **STANDARD/MEASURED** |
| Drape | support geometry, orientation, gravity | 3D surface, drape coefficient, lobe count/phase | held-out coupled membrane/bend/gravity response | scan plus classical drape protocol; **MEASURED** |
| Surface friction | interface, face, direction, normal load, speed, dwell, humidity | breakaway force, kinetic force, stick--slip | anisotropic/static/kinetic/load-rate law | sled/incline/ramp tests; **MEASURED** |
| Crease recovery | direction, prescribed fold, pressure/force, dwell, recovery times, cycles | angle-versus-time, crease width, residual angle | internal friction, plasticity, aging/recovery | ISO 2313-1:2021 and AATCC TM66 variants; **STANDARD/MEASURED** |
| Seam/hem bending | seam type, allowance, direction, face | moment--curvature, drape discontinuity | seam and multilayer construction | seam coupons and drape; **MEASURED/PAPER** |
| Corner drop | release height/orientation, still air | 3D marker trajectory, settling time | bend/damping/aerodynamics/contact | held-out dynamic test; **MEASURED** |
| Two-corner swing/shake/twist | trajectory, frequency, amplitude, air state | marker trajectories, phase, decay | dynamic response and air model | robot or motion stage; **MEASURED** |
| Fling/placement | release motion, height, table | trajectory, impact, coverage, topology | full dynamic/contact interaction | held-out robot test; **MEASURED** |
| Gripper squeeze/pull/lift | pad material, jaw geometry, normal force, approach, fabric side/layers | pressure map, tangential load, slip onset/rate, cloth and robot wrench | real grasp/contact law | force/torque sensor plus pressure sensing/vision; **MEASURED** |
| Full fold | initial registered state, robot action, release | 3D shape, force/pressure history, crease, topology, final stability | end-to-end validation only | held-out real episode; **MEASURED** |

Normative standards may be paywalled. The repository records edition and lawful
access/procedure metadata rather than paraphrasing an incomplete internet
summary into a false standard implementation.

### 5.3 Identification without leakage

Parameter fitting proceeds from isolated mechanisms to coupled motion:

1. fit geometry, areal density, and pressure-dependent thickness;
2. fit warp/weft/bias membrane and shear response from coupon curves;
3. fit directional bending from moment--curvature data;
4. fit cyclic/material damping from residual loops and free decay;
5. fit interface-specific friction from loads, speeds, faces, and directions;
6. fit crease internal variables from only the assigned pressure/dwell/recovery
   trials;
7. fit seam/local-zone profiles from seam coupons;
8. fit aerodynamic/permeability parameters from dynamic trials after structural
   mechanics is frozen; and
9. validate the fixed model on withheld coupons, drapes, motion trajectories,
   grasps, garments, and fold sequences.

The objective is multi-observable, for example

`J(theta) = sum_k w_k d_k(y_sim(theta), y_real) + R(theta)`,

where separate `d_k` terms cover force curves, marker/scan geometry, phase,
pressure, recovery angle, slip, and topology. Weights follow measurement noise
and task relevance, not whichever signal makes the plot look best. Parameter
uncertainty and covariance are retained; a broad posterior is not collapsed to
an overconfident decimal.

Identifiability is actively tested. If bend stiffness and numerical damping can
trade off on one drop test, another frequency or quasi-static moment test must
separate them. If table friction and cloth damping both shorten sliding distance,
they are measured independently. Solver settings cannot be fitted as surrogate
material properties.

### 5.4 Calibration and validation splits

At minimum, hold out:

- force/extension levels and loading rates within the interpolation range;
- at least one direction or combined loading path where scientifically useful;
- pressure and dwell combinations for crease recovery;
- a drape orientation and support size;
- a dynamic frequency/amplitude or release trajectory;
- initial crumple states and robot trajectories;
- physical specimens from the same product lot; and
- later, an entire garment construction/material family for transfer testing.

Extrapolation outside the fitted strain, curvature, contact pressure, speed,
temperature, or humidity range is reported explicitly and cannot be pooled with
validated results.

## 6. Garment and task taxonomy

### 6.1 Why one generic cloth material will fail

| Garment/material family | Dominant differences | Required additional validation |
|---|---|---|
| Plain woven cotton towel/napkin | low extension, shear locking, edge hems | base coupon/contact/crease programme |
| Cotton jersey T-shirt | course/wale nonlinear knit response, rolling edges, seams, ribbed collar, sleeves | knit cyclic tests, collar/seam profiles, sleeve topology |
| Denim trousers | high areal mass and bend rigidity, strong seams, pockets, waistband, zipper/button | seam/trim contact, thick multilayer compression, stronger persistent crease |
| Terry towel | pile loops, larger effective thickness, directional surface friction, air/water interaction | face-specific friction/compression and render microstructure |
| Fleece hoodie | loft/compression, hood, cuffs, drawstrings, zipper/pocket variants | loft hysteresis, local knit/trim assets, entanglement cases |
| Sock/elastane garment | extreme nonlinear extension, elastic recovery, small tubular topology | large-strain knit model and cyclic recovery |
| Fitted sheet | elastic boundary, large area, corner topology | boundary elastic profile and large-scale self-contact |

Dry household garments are already a broad benchmark. Wet towels, underwired
items, sequins, loose straps, and damaged clothing should be separate named
extensions rather than hidden inside domain randomisation.

### 6.2 Task ladder within the environment

The environment exposes atomic tasks with shared physics:

1. **Observe/drape:** predict or settle a garment with no robot action.
2. **Grasp:** acquire and hold one or more layers without a hidden attachment.
3. **Lift/place:** transport a selected material region and release it.
4. **Smooth/canonicalise:** increase usable coverage and align semantic parts.
5. **Fold:** execute one intended material-space fold with correct layer order.
6. **Multi-fold:** complete a category-specific fold graph.
7. **Singulate:** separate one item from a pile without moving all items as one.
8. **Stack:** place multiple released folded items in a stable ordered pile.
9. **Full laundry:** basket/pile to identified, folded, stable stack.

Each task can run with scripted *robot commands* for system identification, a
teleoperator, a classical controller, or a learned policy. None may script the
cloth state or bypass contact.

### 6.3 Asset sources and their role

- **GarmentCode** supplies a modular procedural sewing-pattern language and can
  generate valid, parameterised panels and stitch relations.
- **GarmentCodeData** offers a large structured synthetic garment collection and
  generation pipeline.
- **CLOTH3D** and **ClothesNet** provide category diversity, topology, and
  semantic annotations useful for perception and asset stress tests.
- **GarmentLab** supplies Isaac-oriented manipulation tasks/assets and API ideas.
- **RGBench** proposes a real-garment benchmark, measured dynamic attributes,
  geometry metrics, and high-fidelity simulator architecture.

These are complementary resources, not ground truth replacements. Public asset
availability also differs from paper claims: for example, the current RGBench
repository advertises its evaluation half and notes that the full solver/library
release is still forthcoming. We pin only actually available, licence-compatible
files and never claim a paper's entire dataset is bundled.

## 7. Contact, grasping, and topology

### 7.1 Required collision primitives

Thin-sheet folding needs continuous or conservatively detected contact for:

- vertex--face;
- edge--edge;
- edge/face crossings against rigid surfaces;
- cloth--cloth across the same and different garments;
- cloth--table and cloth--basket;
- cloth--finger pad and cloth--gripper structure; and
- seam/trim contacts.

Vertex-only rigid contact can miss a rigid edge passing through the interior of
a cloth triangle. Discrete collision after penetration can change layer order
before correction. Broad phase, continuous collision detection, barrier/contact
generation, friction, and untangling must be stress-tested separately.

The contact distance is derived from measured effective thickness and local
construction. A convenient default radius (for example, a few millimetres in a
sample) is a **PRIOR**, not permission to inflate a thin shirt until it behaves
like foam.

### 7.2 Intersection-free reference

Incremental Potential Contact and C-IPC provide a useful offline reference
because they target robust, intersection-free frictional contact with nonzero
thickness; C-IPC also addresses cloth-specific strain limiting and contact
challenges. Small deterministic scenarios are solved both by the runtime and by
the reference at tighter resolution. Disagreement localises failure but does
not automatically prove the offline material model is correct.

Reference cases include:

- two layers sliding and folding under known load;
- an edge approaching a face between time samples;
- a four-layer compressed stack;
- cloth pulled around a sharp but rounded table edge;
- two crossing folds with known intended layer order; and
- a finger closing on one versus two layers.

### 7.3 Physical gripper model

The gripper model includes true collision geometry, pad compliance, pad surface,
joint/actuator limits, force sensing, controller latency/bandwidth, and collision
filtering that never removes the captured cloth. Closing command is not grasp
success. Success requires a stable distributed contact patch and measured slip
criterion under a subsequent diagnostic pull/lift.

For every grasp the trace records:

- commanded and actual jaw pose/velocity/force;
- contact points/patches and cloth side/layer identity;
- normal and tangential traction/impulse per pad;
- robot-link equal-and-opposite wrench;
- material-point slip and any layer separation;
- maximum strain/curvature/pressure near the grasp; and
- whether a seam/trim or table was unintentionally captured.

Suction, adhesive, anthropomorphic hand, parallel jaw, and soft gripper are
separate modular end-effectors with different contact laws. A vertex attachment
can be a clearly labelled ablation, never the default abstraction for all of
them.

## 8. Rendering and visual validation

Textile appearance is multiscale. Task-scale folds must come from the physical
surface. Yarn weave/knit, fibres, fuzz, terry loops, seam thread, and submillimetre
roughness influence scattering and can be represented in a high-resolution
render mesh/material when they are below collision scale.

The rendering pipeline therefore separates:

- **physical mesh:** panel-space triangles, contact, seams, internal state;
- **render mesh:** smoothly embedded in the physical surface without changing
  the physical silhouette or contact geometry;
- **microgeometry/material:** anisotropic yarn-direction highlights, normal/
  displacement maps, fuzz/sheens, front/back differences, stains/labels; and
- **semantic overlay:** optional landmarks, material axes, contact pressure,
  layer ID, crease state, and validation residuals.

Measured cloth reflectance research shows that yarn/fibre geometry creates
directional highlights and colour behaviour that a generic diffuse material
misses. OmniPBR/MDL can provide a practical real-time approximation, but visual
parameters should be calibrated under known light/camera conditions with a
colour chart and close, medium, and wide reference photographs.

Visual rules:

- normals/displacement cannot invent a task-scale fold used by the evaluator;
- a render mesh may not pass through the table while the coarse physical mesh
  floats above it without this discrepancy being reported;
- contact shadows do not substitute for contact validation;
- every beauty render has a paired diagnostic render when making a physics
  claim; and
- videos show uncut real-time or declared slow-motion traces with simulation
  time, wall time, seed, and calibration status.

## 9. Installed engine and solver audit

### 9.1 Isaac Sim 5.1 / current Omni Physics surface deformables

The official migration guide says legacy particle cloth has been removed and
surface deformables now use XPBD FEM corotational linear elasticity rather than
the former PBD mass--spring model. It also documents that the surface simulation
mesh doubles as collision mesh and kinematic motion is currently unsupported.

| Requirement | Current documented state | Consequence |
|---|---|---|
| Surface continuum | XPBD FEM, corotational linear elasticity | useful stable baseline, but not a measured nonlinear orthotropic textile law |
| Independent stretch/shear | surface stretch stiffness currently unsupported; material uses thickness/Young's modulus/Poisson ratio | cannot directly fit independent warp, weft, and shear curves |
| Bending | explicit surface bend stiffness exists | useful baseline; still needs direction, nonlinearity, hysteresis, mesh conversion |
| Aerodynamics | legacy lift/drag/wind not supported on surface deformables | custom force path required for dynamic laundry |
| Collision mesh | simulation surface always doubles as collision surface | no independently refined collision surface |
| Self-collision/CCD | documented controls exist | must still pass thin-layer and topology probes |
| Kinematics | surface kinematic motion currently unsupported | no supported way to keyframe cloth, which is desirable for anti-cheat but limits some diagnostics |
| Material locality | current documented multi-material/support limitations require audit | garment seams/local regions cannot be assumed |
| Friction | deformable material exposes dynamic friction; required static/directional behaviour is not established | custom contact/friction or another solver likely required |
| Aerodynamic/pressure legacy fields | mapped to N/A | cannot recover old demo behaviour by schema migration |

Conclusion: PhysX is retained as a visible baseline and remains excellent for
scene/sensor/render integration. It is not selected as the sole fidelity solver
for heterogeneous woven/knit laundry.

### 9.2 Newton 1.3 installed audit

The installed Newton 1.3.0 source offers two especially relevant paths:

- `SolverVBD` combines vertex block descent for deformable particles with AVBD
  rigid/articulation integration. Its local source contains a unified mode that
  applies equal-and-opposite particle--rigid contact forces within the solve.
- `SolverStyle3D` uses projective dynamics and stores panel-space anisotropic
  triangle coefficients for weft, warp, and shear plus anisotropic bend data,
  sewing springs, self-contact routines, and rigid-particle contact.

There is a documentation/code caveat. Newton's FAQ still describes robot--cloth
examples as one-way coupled, and the bundled Franka/shirt example explicitly
chooses an external rigid solver mode that makes the demo one-way. The newer
unified source path is therefore a promising **CODE-AUDIT**, not a passed
experiment.

Neither inspected path is an off-the-shelf complete textile model:

- stock VBD material is not the required fitted nonlinear warp/weft/shear law;
- Style3D's coefficients and example contact radii still need physical units,
  calibration, convergence, and coupling validation;
- no complete time/pressure-dependent crease model was identified;
- the relevant friction path is not the full measured anisotropic interface
  family; and
- aerodynamic fields/helpers do not establish that the selected Style3D solve
  applies the required per-triangle forces, so a custom Warp force kernel is
  likely.

### 9.3 Newton 1.4 candidate

Newton 1.4 was published on 16 July 2026, the date of this audit. Its release and
documentation add an experimental coupled-solver framework, including proxy and
ADMM-style coupling, symmetric equal-and-opposite exchange, body--particle
attachments/contact, and full-surface rigid--soft contact intended to catch
triangle edge/face crossings that vertex-only contact misses.

This is highly relevant but deliberately not treated as solved:

- the coupling documentation labels the framework experimental;
- symmetric coupling introduces penalty/consensus parameters and iteration
  choices that can affect stiffness, energy, and stability;
- robot articulation, cloth, contact, and controller clocks must be tested
  together;
- full-surface contact coverage differs by coupling path; and
- today's release has not yet passed this repository's deterministic probes.

The upgrade belongs in a pinned isolated environment with a rollback path and
recorded commit/package hashes. We compare it against the simpler unified
VBD/AVBD route before choosing an architecture.

### 9.4 C-IPC and other offline solvers

C-IPC/IPC is the preferred small-case contact oracle because of its explicit
intersection-free/frictional-contact goals. ARCSim is valuable for adaptive
anisotropic remeshing, strain limiting, and bending plasticity; its adaptive
fold work is especially relevant to sharp creases. SOFA, MuJoCo, Bullet, Flex,
and published garment simulators provide benchmarks and ablations, not automatic
fidelity.

An offline solver can be slower than real time. The interactive runtime cannot
quietly replay its cached trajectory, and an oracle result is not experimental
ground truth unless its constitutive law was separately calibrated.

### 9.5 Architecture decision matrix

| Path | Main advantage | Main risk | Decision gate |
|---|---|---|---|
| Stock PhysX surface deformable | tight Isaac/USD/runtime integration | insufficient independent anisotropy/aero/crease/contact detail | baseline only unless all physical gates unexpectedly pass |
| Custom unified Newton VBD/AVBD | one solve, direct two-way contact and conservation path | substantial custom orthotropic/crease/contact implementation | conservation, articulation, anisotropy, contact and performance probes |
| Newton 1.4 coupled robot solver + custom VBD/Style3D textile | modular solvers, new symmetric/full-surface mechanisms | experimental tuning, split-solver stability and drift | proxy/ADMM convergence, energy/momentum and grasp probes |
| PhysX robot + external Warp textile handshake | preserves mature PhysX robot stack | highest coupling/API/synchronisation burden | equal/opposite impulse and stable force-control probe |
| C-IPC primary runtime | strongest contact reference | likely incompatible with interactive/control throughput at garment scale | reference-only unless benchmark disproves cost assumption |

The provisional preference is the simplest Newton route that passes two-way
coupling and contact tests, hosted by Isaac for rendering and sensors. We do not
choose between unified VBD/AVBD and Newton 1.4 coupling on documentation alone.

## 10. Proposed modular runtime

### 10.1 Component boundaries

```text
Episode specification + specimen/material profile + seed
                         |
                         v
        Robot/controller/actuator state and commands
                         |
                         v
    +---------------- coupled physics step ----------------+
    | robot articulation <-> contact manifold <-> textile |
    |                               |                      |
    |      membrane/bend/seam/crease/thickness/friction   |
    |                               |                      |
    |                         aerodynamics                 |
    +------------------------------------------------------+
                         |
           immutable state/event/force trace
            /                  |                \
       evaluator          Isaac/USD bridge       calibration residuals
                              |
                    RTX render + sensors + UI
```

The proposed interfaces are intentionally narrower than solver APIs:

- `GarmentAsset`: material-space panels, topology, seam/local-zone graph,
  semantic features, physical/render meshes, and licence/provenance;
- `TextileProfile`: versioned constitutive functions, thickness, friction,
  crease, aero, uncertainty, valid envelope, and calibration links;
- `RobotPort`: articulation state, commanded effort/position/velocity, link
  geometry/material, sensor state, and returned contact wrench;
- `ContactBatch`: pair IDs, time of impact, feature type, normal, area/weights,
  thickness, traction/impulse, side/layer identity, and persistent contact ID;
- `PhysicsStep`: fixed state-in/command-in and state-out/event-out contract;
- `SensorBridge`: one-way observation generation from committed physical state;
- `Evaluator`: read-only task and diagnostic metrics; and
- `Trace`: append-only inputs, states, contacts, forces, energies, solver stats,
  events, hashes, and evidence labels.

The textile solver can be swapped without changing task success or robot policy
APIs. A solver-specific field can appear in diagnostics, never in the universal
task contract unless it expresses a physical observable.

### 10.2 Clocks and ordering

Use a fixed physics substep selected by convergence testing, not render FPS.
Within each control interval:

1. latch the controller command and exogenous air/environment state;
2. perform the declared number of coupled physics substeps;
3. generate and solve contact at every required iteration/substep;
4. update crease/history variables from the converged physical step only;
5. commit state and append the trace;
6. run sensors at their own timestamped rates with declared latency/exposure;
7. evaluate termination/safety from committed state; and
8. interpolate or decimate committed states for rendering only.

No force is multiplied by frame rate. No visual frame advances the physics. A
slow wall-clock run has the same simulated trajectory as an otherwise identical
fast run within deterministic/numerical tolerance.

Candidate multirate operation is allowed only after comparison with a uniformly
fine reference. Stiff seam, contact, or pad behaviour may require smaller local
steps or an implicit solve; slowing the render rate is not a physics fix.

### 10.3 Two-way coupling decision probes

Before building the room or garment catalogue, implement four minimal scenes in
both candidate Newton architectures:

1. **Momentum exchange:** a hanging cloth pulls a free rigid block. Check equal
   and opposite contact/attachment impulse and system momentum change from known
   external forces.
2. **Compliant finger:** cloth drapes and slides over a force-controlled robot
   finger. Compare cloth traction, link wrench, work, and held-out real motion.
3. **Squeeze/lift:** two dynamic jaws close on one/two layers, then lift and pull.
   Check pressure map, slip threshold, no hidden attachment, and stable control.
4. **Full-surface crossing:** a rounded rigid edge/face moves between cloth
   vertices and time samples. Check that layer topology is preserved without an
   inflated contact radius.

For each probe sweep time step, mesh resolution, nonlinear/contact iterations,
coupling iterations, and penalty/ADMM parameters. Report:

- momentum residual after known external impulse;
- energy/work balance and artificial numerical dissipation;
- maximum penetration/intersection and topology errors;
- position/force convergence against the finest feasible reference;
- deterministic repeat residual;
- GPU memory, simulated-seconds/second, and worst-step latency; and
- failure boundary as stiffness, mass ratio, speed, and layer count increase.

The architecture with fewer tunable interfaces wins if both meet physical gates.
Novelty is not a selection criterion.

### 10.4 Coordinate, unit, and provenance contract

- SI units internally: metres, kilograms, seconds, newtons, pascals, radians.
- USD stage units and imported assets are checked and converted exactly once.
- Material axes live in panel coordinates and survive remeshing/skinning.
- Time is simulation time; wall time and rendered time are separate trace fields.
- All model, asset, package, calibration-data, and configuration versions are
  hashed.
- Randomness uses named streams and stored seeds; initial crumples are assets or
  reproducible physical generation procedures, not opaque final meshes.
- A report can reconstruct every plot/video frame from a trace or states why the
  required artefact is unavailable.

## 11. Validation and falsification gates

### G0: units, topology, and zero-load sanity

- mass from mesh/profile equals the measured panel/garment mass;
- rest panels have the correct dimensions, orientation, face, seams, and no
  non-manifold or self-intersecting geometry;
- a rigid transform creates no elastic energy or internal force;
- a free garment accelerates at measured gravity independent of mesh; and
- a flat, unloaded cloth does not acquire a crease or spontaneous velocity.

### G1: constitutive unit tests

- single-triangle/strip tests reproduce fitted warp, weft, and bias curves;
- pure bending reproduces directional loading/unloading moment curves;
- compression reproduces thickness/pressure hysteresis;
- friction reproduces breakaway and kinetic curves across held-out loads/speeds;
- crease state reproduces held-out dwell/recovery trials; and
- finite-difference/autodiff force checks agree with energy gradients where the
  formulation is energy-based.

### G2: numerical convergence

- refine mesh, time step, solver tolerance/iterations, and contact sampling
  independently;
- compare force, geometry, pressure, fold curve, crease width, and topology;
- declare a production setting only inside a stable convergence region; and
- keep solver-error bands separate from experimental-error bands.

A result that changes category success under one reasonable refinement fails,
even if its coarse render looks better.

### G3: contact and coupling

- no initial penetration or hidden collision filters;
- required vertex/edge/face contact cases preserve nonintersection/layer order;
- equal-and-opposite impulses close within numerical tolerance;
- robot effort and cloth motion both change under contact;
- gripper slip/pressure match held-out measurements; and
- sleeping, stabilization, or depenetration settings do not create energy or
  freeze a slowly recovering crease.

### G4: isolated real-material validation

- held-out tension/shear/bend/compression/friction/crease curves;
- 3D drape geometry and lobe structure;
- corner-drop and swing marker position, phase, amplitude, and decay;
- table sliding/settling and multilayer stack height; and
- seam-coupon and local-zone response.

No single scalar pass hides a phase error or topology failure. Plots include raw
trials, uncertainty, simulation, residual, and condition metadata.

### G5: whole-garment and robot validation

- registered held-out garment drop/shake/fling trajectories;
- bimanual grasp, transport, placement, and release with measured link wrenches;
- flat-to-half-fold towel episode from multiple orientations and speeds;
- crumpled-to-flat-to-fold towel episodes generated independently of fitting;
- T-shirt drape and fold after seam/local-material introduction; and
- garment-to-garment transfer reported separately from in-family performance.

### G6: evidence package

Every promoted environment version includes:

- specimen/material cards and calibration provenance;
- source and licence manifest;
- solver/coupling/convergence reports;
- real-versus-sim plots and registered motion frames;
- success/failure videos including diagnostic overlays;
- task/reward definitions and anti-cheat audit;
- known failure envelope and unimplemented mechanisms;
- reproducible commands/configs/seeds; and
- a PDF generated from repository sources, not a manually diverged document.

## 12. Metrics, objectives, and rewards

### 12.1 Geometry and material correspondence

Use multiple metrics because each can hide a different failure:

- bidirectional Chamfer-L1/L2 between registered simulated and real surface
  samples;
- one-sided and symmetric Hausdorff distances for worst local deviation;
- tracked material-point/semantic-keypoint position and velocity error;
- silhouette IoU and projected coverage in calibrated views;
- fold-curve distance and orientation in material coordinates;
- target-edge alignment modulo garment symmetry;
- normal/curvature-field discrepancy at task-relevant spatial scales; and
- stack footprint, height, overhang, and centre-of-mass support margin.

Coverage is useful for smoothing but cannot prove a correct fold: a wrong layer
can produce the same silhouette. Chamfer can also pair the wrong material region
to a nearby surface. Registered material and topology metrics are mandatory.

### 12.2 Topology and physical validity

- self-intersection count/area/depth and rigid penetration;
- intended versus observed layer-order relation by material region;
- sleeve, pocket, hood, cuff, or leg entanglement;
- inside/out and face/back correctness;
- captured layer count at each grasp;
- maximum/percentile membrane strain, shear, curvature, seam load, and trim load;
- mass, momentum, energy/work residuals; and
- unsupported contact, fixed vertex, or invalid state-write event count (must be
  zero for a valid episode).

### 12.3 Pressure, crease, and grasp metrics

- pressure-map error, peak and percentile pressure, patch area, impulse, and
  pressure--time integral;
- crease centreline, width, curvature/sharpness, residual angle, and recovery
  curve after release;
- jaw normal/tangential force and robot-link wrench error;
- material-point slip onset, distance, rate, and grasp retention;
- unintended table/trim/layer capture; and
- damage/safety-envelope violations.

### 12.4 Robot and task metrics

- released-settled success rate with confidence interval;
- time, control cycles, number of regrasps/actions, and path length;
- actuator electrical/mechanical proxy energy and peak/continuous effort;
- perception-only versus privileged-state performance;
- robustness over registered initial states and calibrated parameter uncertainty;
- simulated-seconds/second, step latency distribution, GPU memory, and numerical
  failure rate; and
- real-to-sim and sim-to-real gaps reported per garment family and task stage.

### 12.5 Reward design

The evaluator owns success; the policy receives a reward designed for progress.
A candidate form is

`r_t = w_p [Phi(s_{t+1}) - Phi(s_t)] - c_action - c_force - c_damage - c_invalid`,

where `Phi` combines only causal task observables such as canonical coverage,
semantic/material alignment, intended fold-curve progress, correct layer order,
and released compactness. Penalties cover excessive force/strain, slip when
undesired, collision, penetration, topology violations, and unnecessary action.

Rules:

- no camera-only term may reward a physically invalid hidden layer;
- no privileged target force may act on the cloth;
- potential shaping cannot pay indefinitely for oscillation;
- large terminal reward requires the independent settled success predicate;
- separate reward components and raw metrics are logged every step;
- reward weights are subjected to adversarial policy tests; and
- domain randomisation samples the calibrated uncertainty distribution plus
  clearly labelled extrapolation tests, not arbitrary ranges used to excuse a
  wrong nominal model.

## 13. Research-to-build ladder

This is the long-horizon fidelity roadmap written before implementation. Its
`P0`--`P10` labels are programme stages and are distinct from the repository's
executable mechanism probes `p0_newton_capabilities` through
`p12_topology_safe_flat_lay`. Current accepted/rejected results, including the
completed numerical half-fold, sewn construction track, topology-safe release,
Isaac bridge, renders, and dossier, are recorded chronologically in
[FINDINGS.md](FINDINGS.md).

### R0 -- capability and evidence dossier (this document)

Deliverable: source-backed scope, physical model, engine audit, calibration
matrix, anti-cheat rules, metrics, and falsifiable build plan. Exit requires
internal review of claims and links; it does not claim a working environment.

### P0 -- textile calibration kit and data schema

Acquire the first towel/table/pad specimens; implement specimen registry, raw
data schema, conditioning log, units, uncertainty, and fitting notebooks/tools.
Run mass, thickness/compression, tension/shear, bending, friction, drape, crease,
and simple dynamic tests. Exit: immutable raw data and held-out split.

### P1 -- rectangular textile laboratory

Create a standalone deterministic panel-space cloth scene with gravity,
orthotropic membrane, directional bending, calibrated damping, table/self-
contact, and diagnostic views. No robot and no crease plasticity yet. Exit: G0--
G4 elastic/contact/dynamic tests and convergence report.

### P2 -- coupling bake-off

Pin Newton 1.4 in an isolated environment and implement the four probes for
unified VBD/AVBD, proxy, and ADMM candidates. Exit: select one architecture from
measured conservation, contact, control stability, throughput, and complexity.

### P3 -- physical gripper and robot

Import one bimanual robot, calibrate pad/jaw/contact/actuator behaviour, and run
squeeze/pull/lift/place trials with two-way force feedback. Exit: held-out grasp
slip, pressure, and wrench validation; no attachment used in task mode.

### P4 -- flat towel half-fold

Execute a prescribed robot-space/control trajectory through the normal action
interface. The trajectory may be engineered, but it cannot write cloth state.
Validate release, layer order, final stability, force, and real motion. Exit:
multiple held-out orientations/speeds pass the declared predicate.

### P5 -- pressure/history-dependent crease

Implement and identify the friction/plastic/recovery internal-variable model.
Add pressure and dwell telemetry. Exit: held-out ISO/AATCC-style recovery curves,
repeated cycles, and full-fold crease results without time acceleration.

### P6 -- crumpled towel and dynamic actions

Add reproducible real/virtual crumple generation, dynamic corner motion, airflow,
permeability, smoothing, and bimanual canonicalisation. Exit: held-out drop,
shake, fling, placement, and crumpled-to-folded episodes.

### P7 -- T-shirt with true construction

Add 2D panels, sleeves, collar/rib region, hems, and calibrated seams. Exit:
coupon, drape, contact, grasp, and fold validation on at least one named physical
T-shirt; report all failures separately from towel results.

### P8 -- material and garment breadth

Add trousers/denim, terry towel, hoodie/fleece, and sock/elastic knit one family
at a time. Every family gets a material card and held-out physical validation.
Only then add piles, singulation, garment identification, and stable stacking.

### P9 -- policies, teleoperation, and cold-start data

Expose the existing modular control/teleoperation ports to task actions and
observations. Collect provenance-rich demonstrations, train baselines, and test
reward exploits and sim-to-real transfer. Policy development does not alter the
frozen validation evaluator.

### P10 -- publication-grade evidence and dashboard

Generate the report/PDF, equations, source tables, calibration plots, real/sim
motion-frame plates, pressure/crease overlays, success and honest failure videos,
artifacts, one-click launch entries, and reproducibility manifest. A beauty
render is last evidence, not first implementation.

### Implementation checkpoint -- sewn garments and topology protection

The executable repository has advanced beyond the original rectangular-only
software checkpoint while preserving the calibration order above:

| Executable probe | What it now establishes | What it does not establish |
|---|---|---|
| P7 | sewn T-shirt quotient topology, mass, zero-force/gauge behavior, and explicit rejected convergence branches | calibrated T-shirt or task success |
| P8 | gravity/table contact on the sewn T-shirt | general self-contact or folding |
| P9 | 5/5 exact constructions enter Newton Style3D with mass/manifold/orientation/runtime gates | valid seam coefficients, photorealism, or robot folds |
| P10 | official one-way kinematic pad contact acquires and lifts a terry-towel patch without cloth state writes | finite-mass robot reaction or robust grasp policy |
| P11 | topology-bound tasks pass rigid-frame, task-appropriate baseline, witness, and anti-cheat gates for all five constructions | controller/dynamics success |
| P12 | topology-aware T-shirt reset/release stays intersection-free for 180 verified steps; in a separate matched 40-step sleeve-layer stress, penalty contact crosses at step 32 while IPC stays clean | robot-performed flat lay, calibrated handling load, nonlocal tunnelling claim, monolithic IPC, or sim-to-real fidelity |
| P13 | 5/5 construction-specific flat lays retain every physical particle/triangle with finite state, zero degenerates, zero exact crossing pairs, garment-specific footprint/height/stretch gates, and hash-bound front/back/construction views | calibrated drape equilibrium, robot folding success, or visual appearance as physical validation |

The compiler treats each pattern panel as its own material domain and forms a
physical quotient only at declared stitch samples. This separation preserves
grain/material coordinates and named paths for mechanics and tasks while giving
Style3D a welded surface. Oriented shared edges are audited fail-closed; a
winding defect is physics-invalid even if a two-sided render hides it.

P12 uses IPC Toolkit's barrier derivatives, collision-free step-size query, and
exact surface predicates around a Newton Style3D step. This is explicitly an
operator split, not the monolithic variational IPC algorithm. Newton remains the
finite-thickness proximity-contact provider; IPC minimum distance is zero at
welded seams. Newton broad-phase triangle pairs are conservative candidates,
not intersection evidence, and IPC independently confirms the complete surface.

The causal IPC comparison is not the ordinary gravity release. A mesh cleanup
removed a fold-axis sliver and correctly eliminated the old penalty-release
crossing, so that failure was not retained. P12 now authors a separate synthetic,
reset-only, mass-balanced 2.0 m/s relative sleeve-layer closing velocity on the
healthy mesh. Gravity, table, and air are off; every numerical and material
setting matches except `ipc_self_contact`. Penalty contact produces three exact
topology-local crossings at steps 32--37, whereas IPC remains clean for all 40
steps. This isolates a topology mechanism but is not a robot action, a measured
load case, or evidence of nonlocal garment tunnelling.

The table guard is also local and operator-split. A rejected conservative-
advancement branch scaled the entire garment to the earliest table impact and
allowed one resting vertex to freeze airborne cloth. The retained method solves
particle-sphere/top-plane time of impact, applies a zero-restitution normal
impulse and endpoint correction only to affected vertices, and leaves
tangential Coulomb response to Newton. This is a numerical integrity mechanism,
not a calibrated pressure/contact law.

P13 generalizes topology-aware reset construction without applying one planar
recipe to every garment. The T-shirt uses a flattened sewn shell; the shirt
selectively preconditions sleeves and collar pieces while holding its body;
the towel is exactly isometric; the asymmetric top uses separate curved
front/back neck facings and selectively preconditions only its unequal sleeves;
and the jeans use a two-stage zero-gravity Style3D/IPC continuation followed by
explicit terminal-speed gates. A panel-restricted pass moves a welded physical
particle only when every material source belongs to a selected panel, so a
sleeve pass cannot silently deform the body through its shared armhole seam.
These preconditioners define accepted reset states and are absent from task
dynamics; their garment-specific stretch caps are numerical reset gates, not
measured textile failure strains.

The P13 Isaac showcase is downstream of the exact NPZ. All 45 cut panels are
retained as barycentrically embedded thick shells, while thread, buttons,
buttonholes, rivets, zipper teeth, and dobby bands are audited render-only
annotations. Fifteen hash-addressed captures provide front-owned, back-owned,
and all-panel construction views. Layer isolation never creates an alternate
pose, and temporal RTX history is flushed after visibility changes so hidden
details do not contaminate evidence. The render audit establishes identity and
inspectability, not material calibration.

The exact implementation boundary is therefore intentionally uneven: sewn
construction, semantic goals, one topology-safe release, and five accepted
construction-specific reset/inspection states exist; a complete finite-mass
bimanual robot garment fold does not. The next accepted sewn-garment
task must combine a named robot, conservative two-way reaction, P11 history and
integrity gates, topology protection, convergence, and held-out physical data.

## 14. Original first-turn experiment slate (historical)

This list preserves the initial due-diligence-to-build handoff. It is not the
current task list; several items were completed, rejected, or superseded by the
evidence in `FINDINGS.md`, while physical specimen acquisition remains open.

1. create a pinned `laundry` package/config skeleton and trace schema;
2. install Newton 1.4 in a new isolated environment without changing the known
   working Isaac/runtime environment;
3. reproduce and record a stock PhysX surface-deformable rectangular sheet as a
   labelled baseline;
4. reproduce Newton Style3D anisotropic extension in warp/weft/shear directions;
5. run the unified VBD/AVBD momentum-exchange probe;
6. run Newton 1.4 proxy/ADMM and full-surface contact probes;
7. implement a deterministic anisotropic coupon test harness shared by all
   solvers;
8. select/acquire the canonical real towel, table coupon, and gripper pad before
   tuning a visually plausible garment; and
9. publish probe results, including failures, before room/robot art production.

## 15. Open risks and questions

| Risk/question | Why it matters | Earliest decisive test |
|---|---|---|
| Can Newton's unified or coupled path stably solve a stiff cloth against a force-controlled articulation? | one-way or unstable contact invalidates robot folding | P2 compliant-finger and squeeze/lift probes |
| Can the runtime preserve thin multilayer topology at useful resolution/speed? | a visually small crossing can reverse the fold | edge/face and compressed-stack probes versus C-IPC |
| What constitutive representation is expressive but identifiable? | too simple is wrong; too flexible overfits | coupon train/held-out curves and parameter covariance |
| How much local mesh resolution/adaptivity is required for measured crease width? | coarse hinges diffuse or quantize creases | mesh-converged crease coupon; compare adaptive reference |
| Is pressure-dependent crease formation observable at robot folding pressures/times? | avoids an elaborate model outside task scale | multi-pressure/dwell physical trials |
| Is a triangle aerodynamic model enough for fling? | full CFD is costly; frame damping is unphysical | held-out drop/shake/fling trajectories |
| How should soft pad compliance be represented and measured? | it sets pressure patch and grasp slip | instrumented pad compression and pull tests |
| Can high-resolution render skinning preserve contact appearance? | coarse physical/render mismatch damages visual credibility | close-up table/gripper contact renders plus geometry overlay |
| Which public garment assets have usable licences and topology? | prevents unshippable or invalid dataset dependency | automated manifest/topology audit |
| What task tolerances match human judgement and downstream stacking utility? | arbitrary thresholds can over/understate success | real-fold distributions, annotator study, stack stability |

## 16. Research sources

Accessed 16 July 2026 unless otherwise noted. A source supports the adjacent
method or limitation; it does not supply calibrated parameters for our specimen.

### 16.1 Textile mechanics, constitutive models, and solvers

1. Wang et al., [Data-Driven Elastic Models for Cloth](https://graphics.berkeley.edu/papers/Wang-DDE-2011-08/), SIGGRAPH 2011 -- measured nonlinear, anisotropic stretch and bend models across ten materials.
2. Miguel et al., [Data-Driven Estimation of Cloth Simulation Models](https://research-explorer.ista.ac.at/record/2106), Computer Graphics Forum 2012 -- parameter estimation from complex 3D deformation and independent motions.
3. Sperl et al., [Homogenized Yarn-Level Cloth](https://research-explorer.ista.ac.at/record/8385), SIGGRAPH 2020 -- shell energies derived from woven/knitted yarn simulations.
4. Sperl et al., [Estimation of Yarn-Level Simulation Models for Production Fabrics](https://arxiv.org/abs/2401.15169), 2024 -- nonlinear anisotropic membrane/bending estimation from yarn structure and simple measurements.
5. Baraff and Witkin, [Large Steps in Cloth Simulation](https://publications.ri.cmu.edu/large-steps-in-cloth-simulation/), SIGGRAPH 1998 -- implicit integration foundation.
6. Narain et al., [ARCSim](https://graphics.berkeley.edu/resources/ARCSim/) -- adaptive anisotropic remeshing, strain limiting, contact, and plasticity research code.
7. Narain et al., [Folding and Crumpling Adaptive Sheets](https://graphics.berkeley.edu/papers/Narain-FCA-2013-07/), SIGGRAPH 2013 -- adaptive crease-aligned mesh and explicit plastic embedding space.
8. Chen et al., [Vertex Block Descent](https://doi.org/10.1145/3658179), SIGGRAPH 2024 -- parallel implicit variational solver used by Newton VBD.
9. Li et al., [Incremental Potential Contact](https://ipc-sim.github.io/), SIGGRAPH 2020 -- intersection-free contact framework.
10. Li et al., [Codimensional Incremental Potential Contact](https://ipc-sim.github.io/C-IPC/), SIGGRAPH 2021 -- robust frictional contact and strain limiting for codimensional materials including cloth.
11. Liang et al., [DiffCloth](https://arxiv.org/abs/2106.05306), 2021 -- differentiable projective cloth with dry frictional contact, identification, and manipulation examples.

### 16.2 Creasing, hysteresis, seams, and friction

12. Chen et al., [Cloth Animation with Time-dependent Persistent Wrinkles](https://arxiv.org/html/2502.13491), 2025 -- physics-inspired internal-friction/plasticity/dwell model; explicitly not a calibrated physical law for our textiles.
13. Miguel et al., [Plasticity and Aging of Folded Elastic Sheets](https://arxiv.org/abs/2004.11825), 2020 -- crease rest-angle plasticity/aging evidence and modelling.
14. Volino et al., [Persistent Wrinkles and Folds in Cloth](https://ijvr.eu/article/view/2803) -- hysteresis and evolving rest-shape approaches.
15. Umetani et al., [Seams and Bending in Cloth Simulation](https://diglib.eg.org/items/1e040067-1e01-478c-9cab-77943f5b7935), SCA 2011 -- measured seam/interlining bending influence.
16. Cirio et al., [True Seams for Fabricated Garments](https://filedn.eu/l8vDXhPLwQPyaW6XewVeXCk/publications/trueseams/paper.pdf), SCA 2017 -- explicit seam allowance and stitch construction.
17. Tanno et al., [Anisotropy in Frictional Properties of Plain Woven Fabrics](https://cir.nii.ac.jp/crid/1390001205259634048) -- direction/load dependence including a power-law load relation.
18. Pabst et al., [Anisotropic Friction for Deformable Surfaces and Solids](https://diglib.eg.org/items/109ae695-fca3-4192-9347-c9530f9e4534) -- anisotropic friction simulation model.

### 16.3 Physical test methods

19. ISO, [ISO 2313-1:2021: crease recovery by measurement of the recovery angle](https://www.iso.org/standard/77945.html).
20. AATCC, [TM66: Wrinkle Recovery of Woven Fabrics, Recovery Angle](https://members.aatcc.org/store/tm66/496/).
21. ASTM, [D1777: Standard Test Method for Thickness of Textile Materials](https://store.astm.org/standards/d1777).
22. ASTM, [D1388: Standard Test Method for Stiffness of Fabrics](https://store.astm.org/standards/d1388).
23. ASTM, [D3776/D3776M: Mass Per Unit Area (Weight) of Fabric](https://www.astm.org/d3776_d3776m-20.html).
24. CSIRO, [SiroFAST fabric assurance system publication record](https://publications.csiro.au/publications/publication/PIprocite%3A52208e8c-3915-4096-89be-3ee4a828d30b).
25. ICAR-CIRCOT, [Kawabata Evaluation System tensile and shear tester](https://circot.icar.gov.in/kawabata-evaluation-system-kes-fb1-tensile-and-shear-tester) -- overview of KES fabric-hand measurements.
26. IEEE 3D Body Processing working group, [Measurement of Fabric Properties for Virtual Simulation: A Critical Review](https://standards.ieee.org/wp-content/uploads/import/governance/iccom/3DBP-Measurement_Fabric_Properties-Virtual_Simulation.pdf).

### 16.4 Aerodynamics and appearance

27. Zhang and Jeon, [An Inextensible Model for Robotic Garment Manipulation](https://arxiv.org/abs/2103.09586), 2021 -- calibrated simplified aerodynamic correction and reported marker-error experiments.
28. Chen et al., [Modeling Friction and Air Effects between Cloth and Deformable Bodies](https://wanghmin.github.io/publication/chen-2013-mfa/Chen-2013-MFA.pdf), SIGGRAPH 2013 -- friction, permeability, and pressure effects.
29. [A practical aerodynamic model for cloth](https://www.sciencedirect.com/science/article/abs/pii/S0094114X25000825), 2025 -- experimentally evaluated dynamic-cloth aerodynamic model.
30. Sadeghi et al., [A Practical Microcylinder Appearance Model for Cloth Rendering](https://escholarship.org/uc/item/6v11p5b0), SIGGRAPH 2013 -- yarn/fibre-scale anisotropic appearance.
31. Montazeri et al., [A Multiscale Yarn Model for Cloth Rendering](https://arxiv.org/abs/2401.12724), 2024.
32. Zhu et al., [A Practical Ply-Based Appearance Model of Woven Fabrics](https://projects.shuangz.com/practical_cloth-sa20/), SIGGRAPH Asia 2020.
33. NVIDIA, [OmniPBR material template](https://docs-prod.omniverse.nvidia.com/materials-and-rendering/latest/templates/OmniPBR.html).

### 16.5 Engines and coupling

34. NVIDIA, [Omni Physics deformable migration guide](https://docs.omniverse.nvidia.com/kit/docs/omni_physics/latest/dev_guide/deformables/deformable_migration.html) -- current surface-deformable model and removed/unsupported legacy cloth features.
35. NVIDIA, [Omni Physics deformable bodies guide](https://docs.omniverse.nvidia.com/kit/docs/omni_physics/109.0/dev_guide/deformables/deformable_bodies.html).
36. NVIDIA, [Newton overview](https://newton-physics.github.io/newton/stable/guide/overview.html).
37. NVIDIA, [Newton Style3D solver API](https://newton-physics.github.io/newton/stable/api/newton_solvers_style3d.html).
38. NVIDIA, [Newton solver coupling](https://newton-physics.github.io/newton/stable/concepts/coupling.html) -- experimental proxy/ADMM composition and limitations.
39. NVIDIA, [Newton v1.4.0 release](https://github.com/newton-physics/newton/releases/tag/v1.4.0) -- coupled composition and opt-in full-surface rigid--soft contact.
40. NVIDIA, [Warp documentation](https://nvidia.github.io/warp/) -- GPU kernel/differentiable simulation foundation used by Newton.

### 16.6 Garment assets, benchmarks, and robotic manipulation

41. Korosteleva and Lee, [GarmentCode](https://github.com/maria-korosteleva/GarmentCode) and [paper](https://arxiv.org/abs/2306.03642) -- modular procedural sewing-pattern construction.
42. Korosteleva et al., [GarmentCodeData](https://arxiv.org/abs/2405.17609), 2024 -- large structured synthetic sewing-pattern dataset/pipeline.
43. Bertiche et al., [CLOTH3D](https://arxiv.org/abs/1912.02792), 2019 -- synthetic clothed-human dataset with garment topology/material variation.
44. Zhou et al., [ClothesNet](https://openaccess.thecvf.com/content/ICCV2023/html/Zhou_ClothesNet_An_Information-Rich_3D_Garment_Model_Repository_with_Simulated_Clothes_ICCV_2023_paper.html), ICCV 2023 -- annotated 3D garment repository.
45. [GarmentLab](https://github.com/GarmentLab/GarmentLab) -- Isaac Sim garment-manipulation benchmark/assets; task inspiration, not physical ground truth.
46. Huang et al., [RGBench](https://rgbench.github.io/) and [public code/data status](https://github.com/hwk0809/RGBench), AAAI 2026 -- measured real-garment attributes, simulator/benchmark metrics, and current release caveats.
47. Ha and Song, [FlingBot](https://flingbot.cs.columbia.edu/), CoRL 2021 -- dynamic bimanual cloth spreading.
48. Ha et al., [Cloth Funnels](https://clothfunnels.cs.columbia.edu/), ICRA 2023 -- canonicalisation and action primitives for cloth manipulation.
49. Weng et al., [SpeedFolding](https://pantor.github.io/speedfolding/), IROS 2022 -- fast bimanual smoothing/folding on real garments.
50. [Flat'n'Fold](https://arxiv.org/abs/2409.18297), 2024 -- human and robot garment-folding demonstrations across garment categories.
51. Blanco-Mulero et al., [Benchmarking the Sim-to-Real Gap in Cloth Manipulation](https://arxiv.org/abs/2310.09543), 2023 -- dynamic/quasi-static real tests, geometry/stability/runtime metrics, and simulator comparison.
52. Borràs et al., [Household Cloth Object Set](https://www.iri.upc.edu/files/scidoc/2574-Household-cloth-object-set%3A-Fostering-benchmarking-in-deformable-object-manipulation.pdf), 2020 -- repeatable household cloth-object benchmark proposal.
53. [Laundry folding rubric in a household manipulation benchmark](https://www.roboticsproceedings.org/rss21/p010.pdf), RSS 2025 -- bin removal, table placement, flattening, folding, and stacking task stages.
54. IPC Toolkit, [getting started](https://ipctk.xyz/tutorials/getting_started.html) -- executable collision mesh, constraints, barrier potential, and derivative interface.
55. IPC Toolkit, [Python API](https://ipctk.xyz/v1.0.0/python-api/main.html) -- collision-free step-size query for linear trajectories used by the operator-split guard.
56. Newton, [solver overview](https://newton-physics.github.io/newton/stable/guide/overview.html) -- official modular solver and coupling boundary.
57. Newton, [compatibility policy](https://newton-physics.github.io/newton/stable/guide/compatibility.html) -- public/private API guarantees relevant to the triangle-candidate audit adapter.

## 17. Bottom line

The environment should be ambitious about fidelity and modest about claims.
Isaac Sim gives us an excellent robot/sensor/render host, but today's stock
surface-deformable model is not an adequate universal laundry material. Newton
1.4 makes a genuinely promising two-way modular path newly available, while
C-IPC gives us a contact reference. The decisive work is still physical:
measure one towel, reproduce its independent behaviours, prove conservation and
contact, and make one real released fold match. The five implemented garment
constructions are valuable mechanism substrates, but they must not be promoted
to fidelity claims before named-specimen calibration, two-way robot coupling,
and held-out folds. Piles, policies, and cinematic art remain downstream of that
evidence.
