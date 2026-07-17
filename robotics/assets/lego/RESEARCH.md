# LEGO manipulation: real-world physics specification

Status: pre-build research dossier and falsifiable implementation plan
Target runtime: Isaac Sim 5.1 / Omni PhysX 107.3 on Windows
Initial scope: opaque, classic LEGO System bricks made from ABS
Last updated: 2026-07-10

This document deliberately precedes the scene builder. The first deliverable is
not a pretty workcell: it is a two-brick instrument that can be shown to agree
with physical bricks. A robot and a polished environment are allowed only after
that instrument passes convergence and force/pose validation.

## 0. Bottom line

1. A classic brick connection is primarily a **distributed frictional
   interference coupling**. It is not a binary pose state and it is not well
   represented by snapping a brick to a grid and adding a fixed joint.
2. The stud, outer walls, inner walls/bars, and coupling tubes create three- or
   four-point contacts around each engaged stud. Small elastic deflections create
   radial preload; Coulomb friction converts that preload into axial retention,
   lateral resistance, and torsional resistance.
3. Partial engagement, tilt, rocking, jamming, off-grid contact, seating impact,
   peel removal, wear, and creep are all real states. A faithful simulator must
   preserve them instead of collapsing them into `connected = true`.
4. The key geometric scale is not merely the 8 mm stud pitch. Published models
   use about 0.05 mm radial oversize, while LEGO reports moulding accuracy on the
   order of 0.004-0.005 mm. Collision error, contact offset, and solver drift must
   therefore be treated in tens of micrometres.
5. For the initial pairwise task, the best PhysX-native hypothesis is:
   high-detail local SDF/convex collision + force-based compliant contacts +
   measured static/dynamic friction + small timesteps + TGS. No weld, fixed
   joint, pose teleport, or grid snap is permitted.
6. Full-brick FEM is not the first runtime path. ABS is stiff (roughly GPa), its
   deformation is small and local, and the installed deformable implementation
   lacks static friction and deformable contact reports. Bulk bricks can be rigid
   while the measured interface compliance is represented at contact.
7. For larger assemblies, a reduced-order connector may eventually be necessary,
   but it must be a continuous, history-dependent 6-D wrench law calibrated from
   the physical-contact probe. It must not be a rigid on/off constraint.
8. Physics randomization will come from measured distributions across pieces,
   mould lots, colours/materials, dwell time, and wear cycles. Arbitrary broad
   randomization is not a substitute for identification.

## 1. What “faithful” means here

Visual resemblance is useful, but it is not the principal acceptance criterion.
The simulator is faithful only if an action applied in simulation produces the
same measurable consequences as the same action on physical parts, within a
declared uncertainty band.

The primary observables are:

- 6-D force/torque versus 6-D relative displacement during approach, insertion,
  seating, dwell, lateral loading, twist, pull-off, and peel;
- engagement depth, residual gap, tilt, and lateral offset under load;
- whether a commanded trajectory seats, partially seats, jams, damages, peels,
  or separates the pair;
- work of insertion and removal (integral of force over displacement), not only
  peak force;
- force relaxation during dwell and change over repeated cycles;
- impulse, rebound, and break location in assembly drop tests;
- robot wrist wrench, joint response, fingertip slip, and controller termination;
- runtime and numerical convergence, reported separately from physical accuracy.

A render, final pose, or symbolic connection graph cannot establish any of the
above by itself.

## 2. Scope boundaries

“LEGO” is not one contact model. The material and connector topology change by
part family.

### Initial in-scope family

- opaque classic System bricks;
- 2x2 first, followed by 1x2 and 2x4;
- brick-on-brick engagement in clean, dry indoor conditions;
- new and deliberately worn samples as separate populations;
- translational insertion, pull-off, shear, twist, and peel;
- later: a Franka Research 3 with physically modeled fingertips and impedance or
  force control.

### Explicitly deferred families

- baseplates: LEGO identifies classic baseplates as HIPS, not ABS;
- transparent elements: LEGO identifies a different transparent material;
- plates and 1-wide bricks: their underside and flexural topology differ;
- tiles: no top studs;
- Technic pins, axles, clips, hinges, gears, tyres, and flexible elements: these
  use different geometry, detents, and materials such as PA, PC, POM, TPU, or
  SEBS;
- DUPLO: twice the nominal scale and a materially different surface-pressure and
  handling regime;
- dirt, moisture, thermal expansion, plastic damage, and audible sound synthesis.

Each deferred connector becomes a separately calibrated connector family. We
must not reuse “ABS brick friction” as a universal LEGO constant.

## 3. Evidence hierarchy

The parameter ledger below labels every number by provenance:

- **MFR**: LEGO publication or LEGO-assigned patent.
- **PAT**: original or directly relevant building-brick patent.
- **MEAS**: published physical measurement on real bricks.
- **FEM**: a published FEM implementation or its source code.
- **SIM**: a simulator's chosen heuristic; not a real material property.
- **LOCAL**: verified in the installed Isaac Sim/PhysX build.
- **OPEN**: still requires our own measurement.

Simulator heuristics are useful for comparison, but may never silently become
ground truth.

## 4. What a classic brick connection physically is

### 4.1 Stud-and-tube principle

LEGO's history describes the 1958 addition of internal tubes specifically as the
source of the desired “clutch power.” The original patent describes each primary
projection (stud) as tangentially contacting surrounding surfaces at three points,
at least one of them on an internal secondary projection. The contact produces a
clamping effect.

This has several consequences:

- the contact is distributed around the stud, not concentrated at a single axial
  latch;
- walls and tubes are structural parts of the connector, not visual decoration;
- 1-wide, 1x1, edge, corner, and multi-row engagements can have different
  contact topologies;
- load sharing changes with overlap pattern and brick size;
- a 1x1 connection can retain rotational freedom that a multi-stud connection
  does not; a universal fixed transform would erase this behavior.

### 4.2 Interference, elastic preload, and friction

Published BrickFEM defaults use a radial oversize `delta_r = 0.05 mm`. Treat that
as a starting hypothesis, not an official production dimension. If local radial
interference is `delta`, a reduced normal model begins with

`F_n = k_n * delta + c_n * delta_dot`

and the local friction bound begins with

`|F_t| <= mu * F_n`.

The real walls/tubes couple the local deflections, so independent springs are an
approximation. Nevertheless, this captures the essential causality: elastic
interference creates normal preload; friction under that preload creates clutch
force. A fixed joint has neither causal chain.

The LEGO-assigned biopolymer patent explicitly says small LEGO bricks have higher
surface pressure than DUPLO and therefore demand wear resistance, scratch
resistance, and resistance to creep/stress relaxation. It also requires candidate
materials to withstand elastic deformation and specifies an elastic modulus of at
least 1.5 GPa, preferably at least 2 GPa.

### 4.3 Insertion is continuous, not an event trigger

During real insertion:

1. chamfers/edge radii first contact;
2. lateral and angular errors determine which studs and walls contact first;
3. walls/tubes deflect and the robot/fixture also deflects;
4. friction and geometry can self-align the pair or amplify a jam;
5. axial friction persists over the engaged height;
6. the top/bottom faces finally seat and create a support contact/impact;
7. after release, elastic recovery leaves a distributed preload.

A partially inserted brick can already resist pull-off. A tilted pair can be
retained on one edge. A brick may look nearly seated while one stud is hung up.
These are task-relevant states and must remain representable.

### 4.4 Removal mode matters

Straight pull-off loads many contacts simultaneously. Peeling or twisting unloads
the interface progressively and is much easier; real robot systems exploit this.
The 2024 lightweight LEGO manipulation study uses an insert-and-twist strategy,
and the CMU BrickPick system rotates a brick around its bottom edge before lifting.
Therefore the validation set must include:

- axial pull;
- edge peel about both brick axes;
- yaw twist;
- removal from solid and hollow supporting structures;
- cases in which a lower brick is unintentionally lifted.

### 4.5 History is part of state

The connection depends on:

- mould and part dimensions;
- colour/material formulation;
- surface finish;
- number and type of previous cycles;
- duration held assembled (stress relaxation/creep);
- temperature and humidity;
- dust, skin oils, scratches, and permanent damage.

The LEGO material patent evaluates repeated hand assembly/disassembly under
20-25 C and 20-65% relative humidity and discards the first two cycles before
scoring cycles 3-10. That protocol itself is evidence that cycle and environment
cannot be ignored.

## 5. Parameter ledger: known facts, priors, and gaps

| Quantity | Current value or range | Status | How it may be used |
|---|---:|---|---|
| System stud pitch | 8 mm | FEM/SIM, widely standardized | Nominal grid only; verify accumulated pitch on samples. |
| 2x4 nominal size | about 32 x 16 x 9.6 mm excluding studs | MFR patent | Coarse envelope, not collision geometry. |
| Stud diameter | about 4.8 mm | MFR patent | Initial CAD prior; measure actual pieces. |
| Stud height | 1.7 mm | FEM and real-robot paper | Initial CAD prior; measure logo/rim separately. |
| Brick body height | 9.6 mm | MFR/FEM | Strong nominal prior. |
| Nominal edge gap | 0.1 mm per outside edge in BrickFEM | FEM | CAD prior only. |
| Wall thickness | 1.6 mm in BrickFEM | FEM | CAD prior only; underside ribs require metrology. |
| Large tube outer radius | 3.3 mm | FEM | CAD prior only. |
| Large tube thickness | 0.9 mm | FEM | CAD prior only. |
| Radial oversize | 0.05 mm | FEM | Initial interference sweep center; not ground truth. |
| ABS Young's modulus | 2.2 GPa in BrickFEM | FEM | Prior. LEGO material patent prefers >=2 GPa for candidate materials. |
| Poisson ratio | 0.35 | FEM | Prior; low sensitivity expected in lumped contact, but verify. |
| Density | 1000 kg/m^3 in BrickFEM | FEM | Do not trust over measured mass/inertia. |
| ABS/ABS friction coefficient | 0.2 | FEM/SIM | Prior only; identify static and dynamic values separately. |
| Maximum friction load at a modeled contact point | 71.658 g x 9.8 m/s^2 = 0.702 N | MEAS | Useful structural prior; not a direct insertion curve. |
| 1x1 / 1x2 / 1x3 / 1x4 mass | 0.44 / 0.78 / 1.18 / 1.74 g | MEAS | Priors; reweigh our parts. |
| 1x6 / 1x8 mass | 2.23 / 3.08 g | MEAS | Priors; reweigh our parts. |
| 2x2 / 2x3 / 2x4 mass | 1.18 / 1.78 / 2.20 g | MEAS | Priors; reweigh our parts. |
| 2x6 / 2x8 mass | 3.28 / 4.40 g | MEAS | Priors; reweigh our parts. |
| Historical moulding accuracy | 1/200 mm = 0.005 mm | MFR | Scale warning, not a modern tolerance distribution. |
| 2016 quality measurement statement | tolerance measured to within 0.004 mm | MFR | Scale warning; wording does not prove every dimension is +/-0.004 mm. |
| Legal compatibility envelope | dimensions may vary at most 1% | MFR patent | Too broad for physics calibration; never use as randomization range. |
| BrickSim assembly press threshold | 1 N | SIM | A heuristic, not a measured clutch parameter. |
| BrickSim geometric gates | 1 mm vertical, 2 mm planar, 5 deg tilt/yaw | SIM | Audit baseline only; too coarse to define faithful engagement. |
| CMU vertical termination threshold | 30 N | MEAS robot setup | A safety/fit termination setting, not an insertion-force ground truth. |
| Franka pose repeatability | < +/-0.1 mm | MFR | Robot uncertainty prior and reason to model compliance/search. |
| Franka control rate | 1 kHz | MFR | Controller update target for robot phase. |
| Franka translational stiffness range | 10-3000 N/m | MFR | Use a declared real controller setting, not arbitrary USD gains. |
| Franka rotational stiffness range | 1-300 Nm/rad | MFR | Same. |
| Franka Hand continuous grasp force | adjustable 30-70 N | MFR | Cap the simulated gripper and identify fingertip material. |

The following remain **OPEN** and block any claim of quantitative fidelity:

- actual stud diameters, tube/wall locations, chamfers, radii, taper/draft, rib
  geometry, and their distributions for the physical sample population;
- insertion/pull force-displacement curves by overlap pattern;
- 6-D wrench response versus lateral/angle error;
- static and kinetic ABS/ABS friction at relevant pressure and speed;
- contact damping and hysteresis;
- force relaxation with dwell time;
- wear law with cycles;
- coefficient of restitution/damping for brick-table and brick-brick impacts;
- gripper-pad friction and compliance;
- baseplate HIPS connector behavior.

## 6. What existing LEGO simulators establish—and what they do not

### 6.1 BrickSim (2026, Isaac Sim 5.1)

BrickSim is the strongest directly relevant comparison. It correctly states that
ordinary rigid-body simulation does not preserve LEGO-like assemblies and adds a
force-based structural model. It reports 100% static stability classification over
150 real structures and matching break locations in three drop demonstrations.

Its implementation is intentionally not an insertion-physics reference:

- bricks have cuboid collision proxies;
- studs and underside cavities are not collision geometry;
- an assembly monitor accepts a near-grid pose and compressive-force threshold;
- accepted bricks are snapped to the exact discrete transform;
- rigid constraints are inserted;
- collision inside a connected component is disabled;
- real 1x1 yaw freedom is explicitly not modeled;
- default gates are 1 mm vertical, 2 mm planar, 5 degrees tilt/yaw, and 1 N press.

This architecture is useful for fast structure planning, but cannot answer whether
a robot's particular approach trajectory would self-align, jam, partially seat,
or generate the correct wrench. We should use its static/drop experiments as later
comparisons, not copy its connection transition.

### 6.2 BrickFEM (2023)

BrickFEM explicitly models brick geometry and ABS deformation in Abaqus. Its public
defaults give the most coherent open set of geometric/material priors currently
available: 8 mm pitch, 0.1 mm edge gap, 1.6 mm walls, 1.7 mm studs, 0.05 mm radial
oversize, 2.2 GPa Young's modulus, 0.35 Poisson ratio, and friction 0.2.

BrickFEM creates the assembled preload using three artificial initialization stages
(widen, contact, free) and is intended for a few bricks because cost grows rapidly.
It is valuable as an offline/reference model, but it does not solve real-time robot
insertion for many parts and its default dimensions remain “typical,” not measured
production metrology.

### 6.3 Legolization (2015)

Legolization performed 70 physical lever/pull configurations, three trials each,
with 10 g load increments. A least-squares force/torque balance estimated the
maximum friction load `T` at a modeled contact point as approximately 0.702 N. It
also published brick masses.

This is genuine measurement and a useful structural prior, but it collapses local
elasticity and friction into a static capacity. It is not a force-displacement curve
and cannot calibrate insertion dynamics alone.

### 6.4 Real robotic LEGO work

Real systems consistently expose behaviors a pose-snap simulator omits:

- tight alignment and friction are named as the main sim-to-real gap;
- specialized end-effectors reduce in-hand pose uncertainty;
- twist/peel is used because straight pull can lift unintended lower bricks;
- force thresholds stop a failed insertion from driving into the baseplate;
- outcome classes include no contact, misaligned contact, incomplete contact, and
  complete contact;
- pull tests are used to verify that a connection actually holds.

These outcome classes become mandatory validation cases, not just policy ideas.

### 6.5 Factory and IndustReal

NVIDIA Factory demonstrates that GPU SDF contact can simulate M4 threads and other
millimetre-scale assembly geometry at real-time or faster rates. It also documents
why convex decomposition artifacts destabilize fine assembly and why SDF resolution,
uniform tessellation, contact reduction, and solver choice matter. Factory generally
uses clearances; LEGO is harder because it deliberately uses interference and needs
compliance.

IndustReal is a warning against trusting a simulator merely because a policy succeeds:
it explicitly detects excessive simulated interpenetration and suppresses policy
updates that exploit it. Our non-learning probes should likewise report maximum
penetration and reject physically impossible solutions.

## 7. Isaac Sim 5.1 / PhysX capability and limitation audit

### 7.1 Capabilities verified locally

The installed `omni.usd.schema.physx` 107.3 schema and demo sources expose:

- `PhysxSDFMeshCollisionAPI`, with resolution, sparse subgrid resolution, narrow
  band, margin, remeshing, precision, and triangle-reduction controls;
- `physxMaterial:compliantContactStiffness` and damping using implicit springs;
- force-based or acceleration-based compliant spring mode;
- static/dynamic friction and material combine modes;
- explicit `contactOffset` and `restOffset`;
- torsional patch radius and minimum torsional patch radius;
- rigid-body CCD/speculative CCD controls;
- contact reports, per-contact force/point/normal data, and force thresholds;
- TGS solver, GPU rigid-body dynamics, and GPU broadphase.

The local demo `CompliantContactsDemo.py` confirms that compliant contact is a
supported material path, not an undocumented schema stub.

### 7.2 SDF is appropriate, but it is not magic

NVIDIA documents SDF as the supported high-detail collider for dynamic concave
mesh bodies and specifically cites assembly. Important constraints are:

- SDF is a GPU collision feature; CPU mode falls back to triangle-mesh behavior;
- SDF resolution is tied to the longest collider AABB extent;
- thin regions below roughly twice the grid spacing may disappear or distort;
- extremely high resolutions cost memory and collision time;
- SDF-SDF contact depends on mesh tessellation and can generate many contacts;
- NVIDIA recommends splitting a mesh when otherwise extreme resolution is needed;
- dynamic SDF colliders do not support per-triangle/multi-material collision in the
  simple path.

Therefore one visual brick must not automatically become one monolithic collider.
The collision representation should be split into local, watertight interface pieces
with bounded AABBs and uniform triangles. Outer structural faces and mating faces
must be separable so the mating interface alone receives compliant ABS/ABS material.

### 7.3 Contact compliance is the primary reduced elasticity model

PhysX compliant contact replaces rigid normal contact with an implicit spring-damper.
We will use **force-based**, not acceleration-based, springs: mass-independent sink
depth is convenient but not physical for this identification problem.

The fitted stiffness is an effective contact stiffness after geometry, mesh, SDF
resolution, contact count, timestep, and solver settings are frozen. It cannot be
copied directly from Young's modulus. A different tessellation may create a different
number of contact points and therefore change aggregate stiffness.

If a single scalar contact stiffness cannot match axial, lateral, and torsional tests
simultaneously, the next model is not a fixed joint. It is a discrete compliant-cell
model: rigid local wall/tube pads connected to the brick by a calibrated stiffness
matrix, with physical collision at the pad surfaces.

### 7.4 Contact offset is a physics parameter at this scale

PhysX begins generating contacts when shapes come within the sum of their contact
offsets. Automatic defaults may be large compared with a 50 micrometre interference.
We must set and sweep offsets explicitly.

The offset must be large enough that a feature cannot cross the contact envelope in
one timestep, yet small enough not to create visibly premature forces. A starting
sweep is 10, 25, 50, and 100 micrometres per interacting shape, tied to the commanded
insertion velocity and timestep.

### 7.5 GPU CCD caveat

Isaac 5.1 documentation states that conventional CCD requests are ignored when GPU
simulation is enabled. SDF requires the GPU path, so we cannot rely on swept CCD as
a rescue mechanism. Use:

- bounded insertion velocities;
- small fixed timesteps;
- explicit contact offsets;
- speculative CCD where supported;
- capped depenetration velocity;
- no direct pose jumps in contact.

### 7.6 Friction model

PhysX's default patch-friction model is Coulomb-like and uses up to two friction
anchors per contact patch. TGS treats the two tangential directions jointly and
applies friction throughout position/velocity iterations. This is preferable to PGS
for symmetry and persistent tight contacts, but it still needs validation.

Do not invent giant friction to make bricks stick. Friction coefficients, torsional
patch radius, and strong-friction behavior must be fitted or measured. If correct
geometry/compliance cannot reproduce retention at measured friction, that failure is
diagnostic—the answer is not a hidden weld.

### 7.7 FEM is a reference path, not the first runtime path

PhysX FEM soft bodies can represent Young's modulus and Poisson ratio, but the
installed generation has important limitations for this task:

- very stiff materials need more solver iterations;
- micrometre-scale wall deformation demands careful tetrahedral resolution;
- static friction for deformables is not supported;
- deformable contact reports are not supported;
- multi-material/contact control is restricted;
- runtime and determinism are worse than rigid contact.

One offline single-cell FEM probe may later estimate a local stiffness matrix, but
full deformable bricks are not the baseline robotic environment.

### 7.8 The robot controller must be physical

The real Franka Research 3 exposes a 1 kHz interface and configurable Cartesian
impedance. A USD articulation driven by arbitrarily stiff position targets is not the
same system. During robot validation we must specify:

- the exact control mode;
- update rate and latency;
- translational/rotational stiffness and damping;
- force/torque saturation and collision thresholds;
- rate/jerk limits;
- gripper force, speed, pad stiffness, and pad friction;
- wrist force/torque filtering and bias.

The initial brick probe intentionally excludes the robot so connector error and
controller error cannot compensate for one another.

## 8. Recommended simulation architecture

### Layer A: parametric physical brick asset

One brick asset contains separate representations:

1. **Render mesh**: bevels, draft, underside details, injection marks, stud logos,
   physically plausible ABS shading. No collision is inferred from render geometry.
2. **Mass model**: measured mass, center of mass, and inertia. Density-derived mass
   is only a cross-check.
3. **Outer collision**: efficient rigid/convex surfaces for table, gripper, and other
   non-mating contact.
4. **Mating collision**: high-detail local stud/chamfer and underside wall/tube
   colliders. These alone receive the calibrated compliant ABS/ABS material.
5. **Interface metadata**: stud/tube identities and nominal grid coordinates used
   only for logging and task definitions—not to move the bodies.

The geometry generator must expose every uncertain physical parameter and record it
in the stage metadata/calibration manifest.

### Layer B: high-fidelity pairwise contact mode

This is the highest-fidelity calibration/reference mode for a few active
connections. It becomes quantitatively credible only after holdout validation:

- both bricks remain independent rigid bodies;
- mating geometry collides continuously;
- compliant normal force and friction produce retention;
- all contact impulses are recorded;
- no connection is created in a topology graph;
- no collision is disabled after seating;
- no final pose is corrected;
- partial engagement and separation remain ordinary physical states.

### Layer C: discrete compliant-cell fallback

If scalar compliant contact cannot reproduce all 6-D tests, model each contact region
as a local pad/flexure with a coupled stiffness and damping matrix identified from
experiment or an offline FEM cell. D6 constraints/springs may connect the pads to the
brick body, but the two bricks themselves still join through collision and friction.
Prefer explicit equal-and-opposite pad wrenches during identification: Omni PhysX
107.3 documents solver-specific D6-drive limitations under TGS, especially with
nonzero velocity iterations. Any D6 implementation therefore needs its own PGS/TGS
and iteration convergence test.

This adds direction-dependent wall/tube elasticity without a full deformable mesh.

### Layer D: scalable reduced-order connector

Only after Layer B/C is validated, fit a continuous per-stud connector law for larger
assemblies. State includes at least:

- 6-D relative displacement and velocity;
- engagement depth;
- contact topology and overlap;
- stick/slip state;
- peak previous displacement/cycle count;
- dwell/relaxation state;
- part-instance latent parameters.

The connector applies equal-and-opposite forces and torques into PhysX each step.
It must support partial engagement, progressive peel, and overload. It must not snap
poses or turn an assembly into one rigid body. A D6 spring may be an implementation
tool only if its complete wrench/displacement and break behavior matches the fitted
law.

### Layer E: robot and workcell

After connector validation:

- Franka Research 3 with declared impedance/force controller;
- force-limited gripper or a declared specialized LEGO tool;
- fixed metrology fixture for early tasks;
- then loose bricks, a storage area, build area, wrist/overhead cameras, and bins;
- a baseplate only after its HIPS interface is separately calibrated;
- visual realism added without changing collision truth.

## 9. Initial numerical hypothesis and mandatory sweep

These are experiment axes, not settled values.

| Parameter | Initial sweep |
|---|---|
| Physics timestep | 1/240, 1/480, 1/960, 1/1920 s |
| Solver | TGS |
| Position iterations | 8, 16, 32, 64 |
| Velocity iterations | 1, then 2 if damping/energy requires it |
| SDF background resolution | 128, 256, 512 per local collider |
| Sparse subgrid | 4, 6, 8; 16-bit samples initially |
| Interface contact offset | 10, 25, 50, 100 micrometres per shape |
| Rest offset | 0 initially; any change must be geometrically justified |
| Depenetration velocity | low bounded sweep, reported explicitly |
| Interference | measured distribution; before measurement 25-75 micrometres |
| Effective contact stiffness | log sweep, then system identification |
| Contact damping | fit from approach/release hysteresis; check critical-damping scale |
| Static/dynamic friction | measured; prior center 0.2 only |
| Insertion speed | 1, 5, 20 mm/s for calibration; broader robot speeds later |

For each configuration report:

- maximum penetration;
- contact count and GPU buffer warnings;
- peak force, pull-off force, insertion/removal work;
- final gap/tilt and drift over 10 s;
- energy change and rebound;
- simulated-time / wall-time ratio.

The chosen configuration must lie on a convergence plateau. A curve that matches
only because coarse SDF and large contact offset cancel one another is rejected.

## 10. Physical measurement campaign

No amount of web research can recover proprietary mould dimensions and the force
distribution of the exact parts we want to transfer to. A small hardware campaign is
therefore part of the simulator, not optional post-hoc validation.

### 10.1 Sample design

At minimum:

- 10 new opaque ABS 2x2 bricks from a recorded set/lot if possible;
- 10 additional 2x2 bricks for holdout validation;
- 1x2 and 2x4 sets only after the 2x2 model is frozen;
- at least two colours/lots to detect formulation or mould effects;
- a controlled worn population with recorded cycle count;
- separate HIPS baseplate samples later.

Never fit and validate on the same physical pair.

### 10.2 Metrology

Required or preferred instrumentation:

- a calibrated micrometer with about 1 micrometre readout for accessible dimensions;
- optical microscope, optical comparator, or CMM for inner walls/tubes, draft,
  radii, and chamfers;
- pin gauges where geometry permits;
- 1 mg-resolution balance for mass;
- repeated measurements at multiple studs and orientations;
- temperature and relative-humidity logging.

Ordinary callipers are adequate for nominal 8/9.6 mm envelopes but not for the
interference responsible for clutch force. Instrument resolution is not measurement
accuracy: record calibration, repeatability, probing force, and the complete
uncertainty budget.

### 10.3 Force-displacement fixture

Preferred fixture:

- rigid lower-brick mount whose compliance is measured separately;
- motorized linear stage with <=10 micrometre position resolution;
- 0-50 N axial load cell, ideally a 6-axis transducer;
- >=1 kHz synchronized force and displacement acquisition;
- interchangeable lateral-offset and tilt stages;
- no hand-applied load in the quantitative dataset.

Run approach, insertion, dwell, pull-off, shear, twist, and peel at controlled rates.
Record raw signals, unfiltered and filtered data, calibration certificates, fixture
compliance, part IDs, cycle IDs, and environmental conditions.

### 10.4 Experiment matrix

1. Perfectly aligned insertion/pull at 1, 5, and 20 mm/s.
2. Planar offset grid through the success/jam boundary.
3. Tilt around both horizontal axes through the success/jam boundary.
4. Yaw error and a 1x1 free-yaw test later.
5. Partial engagement holds at several depths, followed by pull tests.
6. Dwell for 1 s, 60 s, 1 h, and longer selected points; then pull.
7. Cycles 1, 2, 3-10, 100, and 1000 where practical.
8. Straight pull, edge peel, and twist removal.
9. Partial stud-overlap patterns for larger bricks.
10. Drop/rebound and connected-assembly drop tests after local fitting.

The LEGO patent's 20-25 C, 20-65% RH, 10-cycle protocol is a useful baseline,
but our force test is quantitative rather than subjective.

### 10.5 Identification strategy

Use a hierarchical model rather than one magic coefficient:

- global nominal geometry/material values;
- mould-lot offsets;
- part-instance offsets;
- per-stud residuals where justified;
- cycle/wear state;
- measurement noise and fixture uncertainty.

Fit geometry to metrology first, normal compliance/damping to axial curves second,
friction to pull/shear/twist third, and controller/fingertip parameters last. Do not
allow robot gains to compensate for the wrong brick contact model.

## 11. Validation and acceptance gates

All numerical tolerances below are provisional engineering gates and should be
tightened or loosened according to physical sensor uncertainty.

### Gate 0: geometry and mass

- correct dimensions for the measured part population;
- collision surface error near mating regions <=10-20 micrometres or demonstrably
  negligible in force convergence;
- mass within 1% and center of mass/inertia within measurement/model uncertainty;
- no collision inferred from decorative logos or render-only bevel details unless
  they measurably affect contact.

### Gate 1: numerical convergence

- halving timestep changes peak force, work, and pull-off by <5%;
- doubling local SDF resolution changes them by <5%;
- doubling solver iterations changes them by <5%;
- maximum interpenetration stays within the identified compliant deformation band;
- no contact-buffer overflow, missed collision, explosive depenetration, or energy
  creation.

### Gate 2: aligned force curve

On holdout brick pairs:

- insertion-force curve shape and seating location match;
- peak insertion and pull-off forces within approximately 10-15%;
- insertion and removal work within approximately 10-15%;
- rate dependence across the tested velocities is reproduced;
- release produces the correct residual seating gap and rebound.

### Gate 3: 6-D perturbation boundary

- correct seated/partial/jammed classification over held-out planar and tilt grids;
- no false “connected” classification for a merely touching or teleported brick;
- correct lateral force and pitch/roll moments during one-edge-first contact;
- success boundary location within physical measurement uncertainty.

### Gate 4: retention modes

- axial pull, yaw twist, and edge peel match separately;
- progressive release occurs in the same order/location;
- a sub-threshold pull holds without hidden constraints;
- an overload separates without deleting collision or teleporting bodies.

### Gate 5: history

- correct direction and approximate magnitude of dwell relaxation;
- correct direction and distribution of wear over cycles;
- new and worn populations remain distinguishable;
- randomization samples measured correlated distributions.

### Gate 6: connected dynamics

- multi-brick static stability on holdout structures;
- drop survival/break decision and break location;
- connected assemblies do not drift apart at rest or become mathematically rigid;
- local compliance and oscillation remain plausible.

### Gate 7: robot interaction

- declared controller produces wrist wrench and stopping behavior matching reality;
- grasp does not rely on a weld or key attachment;
- insertion can yield no-contact, misaligned, incomplete, and complete outcomes;
- pull verification correctly detects seating;
- sim and real success maps agree across pose perturbations, not just one nominal
  trajectory.

### Gate 8: anti-cheat tests

The verifier must fail each of these:

- a brick teleported into the final pose without an insertion history;
- a brick within pose tolerance but not carrying retention load;
- a visually seated brick with one edge/stud incomplete;
- a brick held by the gripper at the target pose;
- a pose-snap/fixed-joint implementation with no measured force curve;
- a model that succeeds only through excessive interpenetration;
- a model tuned to the calibration parts but failing holdout pieces.

## 12. Task and environment progression

Physics capability, not visual ambition, sets the order.

### P0 — SDF/compliant-contact numerical cell

One fixed lower interface and one driven upper stud/cavity cell. No robot. Establish
SDF error, contact count, timestep/solver convergence, and stable interference.

### P1 — instrumented 2x2 pair

Full parametric 2x2 bricks and a virtual 6-axis test machine. Produce aligned
insertion/pull force curves and compare to hardware.

### P2 — error and removal atlas

Automated offset/tilt/yaw/velocity sweeps, partial seating, shear, twist, and peel.
This becomes the core connector dataset and verifier.

### P3 — history and population

Dwell, wear, part-instance distributions, and holdout validation. Freeze the first
calibrated `classic_abs_2x2` parameter set.

### P4 — generalization

1x2 and 2x4 bricks, overlap patterns, 1-wide topology, and plates. No parameter is
reused blindly; quantify what transfers and what changes.

### P5 — physical robot insertion

Franka with a 1 kHz impedance/force loop, realistic force limits, contact sensing,
and measured fingertips. Initially use a metrology fixture, not a loose cinematic
scene.

### P6 — pick, orient, assemble, and verify

Loose-brick picking, in-hand uncertainty, visual/tactile search, insertion, pull-test
verification, recovery from incomplete/jammed states, and safe release.

### P7 — multi-brick environment

Storage area, calibrated build fixture/baseplate, cameras, bins, distractors, and
assembly-order constraints. Add the scalable connector only after it reproduces P1-P4.

### P8 — structural and long-horizon tasks

Overhangs, bridges, subassemblies, disassembly, collapse, and damage-aware planning.
Compare against BrickSim/StableLEGO structural tests while retaining continuous local
mechanics for actively manipulated interfaces.

## 13. Recommended first build

Build **P0/P1**, not the robot scene:

1. parametric 2x2 ABS brick generator with separate render, outer-collision, and
   mating-collision meshes;
2. a fixed lower brick and a force-limited 6-D virtual test actuator;
3. GPU SDF + TGS + force-based compliant contact;
4. synchronized CSV/JSON trace of pose, velocity, contact points, normal/friction
   impulses, actuator wrench, energy, and penetration;
5. automated timestep/SDF/solver/contact-offset sweep;
6. plots of force versus displacement and convergence;
7. an explicit “prior-only / not yet physically calibrated” banner until hardware
   curves are supplied.

Only when this test has a stable convergence plateau should we add the Franka. This
ordering prevents a visually convincing robot demo from concealing a fake connector.

## 14. Installed-engine findings and resulting design

The implementation campaign changed several recommendations from the initial
paper design. These are observations from the installed Isaac Sim 5.1 / Omni
PhysX 107.3 engine, not claims about all PhysX configurations.

### 14.1 Scale every scene parameter, not only the mesh

A nominal 2x2 brick is 15.8 mm wide and 11.3 mm high including studs. Several
default collision/friction distances in a metre-scale rigid-body scene are of
the same order as, or larger than, the whole part. In particular, the documented
PhysX scene defaults for `frictionOffsetThreshold` and
`frictionCorrelationDistance` are 40 mm and 25 mm. Leaving those values implicit
allows one friction patch to correlate anchors across multiple moulded features.

The profiles therefore author both values explicitly. The friction offset is
0.20 mm for the render-only fast profile, 0.10 mm for interactive work, and
0.04 mm for calibration; correlation is 0.50 mm in all three. Contact/rest
offset, SDF resolution, solver frequency, depenetration speed, sleep thresholds,
mass, and actuator bandwidth are likewise declared rather than inherited.

This is a general robotics-simulation lesson: scaling geometry without scaling
the solver's spatial memory produces a visually small scene with mechanically
large contacts.

### 14.2 Strong friction is not guaranteed across changing SDF patches

PhysX patch friction can preserve tangential anchors through the strong-friction
mechanism, but the rigid-body documentation notes that compliant contact behaves
best with stable contact points. SDF contact generation on detailed moving
interfaces can replace or reorganize points as penetration and topology change.
The observed LEGO result matches that risk: reducing the friction correlation
scale and raising static friction changed post-press rebound only slightly.

This does not show that Coulomb friction is irrelevant. It shows that a scalar
coefficient cannot repair contact-anchor turnover. Calibration must record the
contact population and patch lifetime along with force and displacement, and a
model that fits one aligned pull peak must be challenged by offset, tilt, twist,
and peel.

### 14.3 Split resolved and unresolved compliance

Stud/tube/wall interference is spatially resolved by the chosen SDF and must
remain a compliant contact problem. Broad top/rim support is different: the real
ABS compression at roughly 20 N is smaller than the collision discretization,
while an explicit spring stiff enough to represent it has a natural period far
below the 480 Hz interactive step for a 1.18 g body.

Installed-engine tests confirmed the distinction. A soft broad face produced
nonphysical sink; a 5 MN/m explicit broad support spring stored and released
enough unresolved energy to launch the free brick; the implicit rigid
nonpenetration constraint remained stable. The accepted representation is
therefore compliant local interfaces plus rigid broad support. A future FEM or
modal model may restore sub-resolution support compliance, but an under-resolved
spring is less faithful than declaring that deformation unresolved.

### 14.4 Use an evidence ladder for connector fidelity

One representation cannot currently satisfy metrology, interactive control, and
long-horizon stability equally well. The environment uses an explicit ladder:

1. **P0 geometry truth:** independent bodies, joint-free SDF contact, constrained
   test carriage, and complete force/displacement/energy traces.
2. **Free-brick press truth:** gravity, physical guide, finite-impedance ram, and
   no connector constraint during insertion.
3. **Episode clutch:** a force-limited D6 constraint created only after physical
   seating evidence. It holds lateral/rotational state at the measured activation
   frame while leaving axial motion to an implicit force drive.
4. **Task verifier:** history-sensitive success requires grasp, lift, alignment,
   insertion, seat, unload, and upward retention; a correct final pose alone
   cannot pass.

The D6 layer is not hidden. Its path, activation pose, axial stiffness, damping,
force cap, collision state, and `pose_write: false` evidence are written to the
trace. The calibration path never uses it. This separation prevents the common
mistake of fitting a constraint and then reporting its behavior as geometric
contact validation.

### 14.5 Activation is a proof obligation

Reduced-order activation requires all of the following at runtime:

- a continuous physical insertion history;
- `seated == true` from relative pose and engagement geometry;
- upper-bottom seat error no greater than +0.05 mm;
- at least 5 N of measured contact against the fixed lower brick;
- no pose write, kinematic switch, collision disable, or reset after episode
  start.

The D6 world anchor is authored at the current upper-body pose, so it begins
without a correction impulse. X/Y and three rotations are locked; translation Z
is free and receives an 18 kN/m, 0.15 N s/m implicit force drive capped at
2.67 N. A scalar breakable fixed joint was tested and rejected because its break
force necessarily couples the lateral preload capacity to axial pull-off.

### 14.6 What the present evidence supports

The installed engine has demonstrated finite joint-free insertion/pull traces,
physical Franka reach and grasp/lift, a tapered force-limited guide die, and a
clean combined autonomous episode. In v32, the press verified a +0.025 mm seat
with 19.329 N contact before D6 activation; after unload and physical regrasp,
the upward verification ended at +0.068 mm seat error and task phase `success`.
The trace records collision enabled and no pose write. This is one deterministic
simulation pass, not real LEGO calibration. Hardware data, randomized episodes,
and holdout structures remain the authority.

## 15. Sources

### Manufacturer and patents

- LEGO, “The stud and tube principle”:
  https://www.lego.com/en-us/history/articles/d-the-stud-and-tube-principle
- Christiansen, *Toy Building Brick*, US 3,005,282 (original three-point clamping
  geometry):
  https://patents.google.com/patent/US3005282A/en
- LEGO Group, *Responsibility Report 2016*, p. 28 (clutch-power quality checks and
  0.004 mm statement):
  https://www.lego.com/cdn/cs/aboutus/assets/blt19f572ab26a9af07/Responsibility-Report-2016.pdf
- LEGO, “The LEGO moulding philosophy” (ABS and historical 0.005 mm accuracy):
  https://www.lego.com/en-us/history/articles/e-the-lego-moulding-philosophy
- LEGO, “Materials in LEGO bricks and elements” (classic brick ABS, baseplate HIPS,
  other families/materials):
  https://www.lego.com/en-sk/sustainability/product-safety/materials
- LEGO A/S, *Toy building bricks made of biopolymeric material*, WO2019106129A1
  (dimensions, material stiffness requirement, wear/creep, assembly and drop tests):
  https://patents.google.com/patent/WO2019106129A1/en

### Measured mechanics and simulation literature

- Luo et al., *Legolization: Optimizing LEGO Designs* (70 physical configurations,
  contact-force capacity and measured masses):
  https://www.cs.columbia.edu/~yonghao/siga15/luo-Legolization.pdf
- Pletz and Drvoderic, *BrickFEM* paper and implementation (explicit geometry,
  interference, ABS, friction, and FEM initialization):
  https://engrxiv.org/preprint/download/2898/5376/4213
  https://github.com/mpletz/BrickFEM
- Wen et al., *BrickSim: A Physics-Based Simulator for Manipulating Interlocking
  Brick Assemblies* (Isaac architecture, structural model, tests, and limitations):
  https://arxiv.org/html/2603.16853
  https://github.com/intelligent-control-lab/BrickSim
- Liu, Sun, and Liu, *A Lightweight and Transferable Design for Robust LEGO
  Manipulation* (alignment, friction gap, insert/twist/peel, robot results):
  https://arxiv.org/abs/2309.02354
- Holtz, *Improving Robotic Lego Assembly with Vibro-Tactile Feedback* (force-based
  termination and no/misaligned/incomplete/complete outcome classes):
  https://www.ri.cmu.edu/app/uploads/2024/08/MSR_Thesis.pdf
- Ma et al., *WorkBenchMark* (tiered long-horizon LEGO/DUPLO tasks; useful task
  structure but not a contact-physics reference):
  https://arxiv.org/abs/2606.19358
- Narang et al., *Factory: Fast Contact for Robotic Assembly* (SDF contact,
  millimetre-scale geometry, contact reduction, solver studies):
  https://arxiv.org/abs/2205.03532
- Tang et al., *IndustReal* (sim-to-real assembly and interpenetration-aware policy
  updates):
  https://arxiv.org/abs/2305.17110

### Official PhysX / Isaac documentation

- SDF and collider tuning:
  https://docs.omniverse.nvidia.com/kit/docs/omni_physics/latest/dev_guide/rigid_bodies_articulations/collision.html
- Compliant contacts and material combination:
  https://docs.omniverse.nvidia.com/kit/docs/omni_physics/latest/dev_guide/rigid_bodies_articulations/rigid_bodies.html
- Collision behavior guide (SDF contact buffers, tessellation, resolution):
  https://docs.omniverse.nvidia.com/kit/docs/omni_physics/107.3/dev_guide/guides/collision_guide.html
- PhysX GPU/SDF limitations:
  https://nvidia-omniverse.github.io/PhysX/physx/5.4.1/docs/GPURigidBodies.html
- PhysX patch-friction model:
  https://nvidia-omniverse.github.io/PhysX/physx/5.4.0/_api_build/struct_px_friction_type.html
- PhysX rigid-body dynamics (strong friction, compliant contacts, and contact
  stability):
  https://nvidia-omniverse.github.io/PhysX/physx/5.4.0/docs/RigidBodyDynamics.html
- `PxSceneDesc` API (friction offset and correlation-distance defaults):
  https://physics-playground.github.io/PhysX5/physx/5.3.1/_api_build/class_px_scene_desc.html
- PhysX material flags (strong-friction disable flag):
  https://nvidia-omniverse.github.io/PhysX/physx/5.4.0/_api_build/struct_px_material_flag.html
- PhysX FEM soft bodies and stiff-material cost:
  https://nvidia-omniverse.github.io/PhysX/physx/5.4.1/docs/SoftBodies.html
- Omni PhysX 107.3 known limitations (deformable static friction/contact reports and
  D6/TGS caveats):
  https://docs.omniverse.nvidia.com/kit/docs/omni_physics/107.3/dev_guide/guides/current_limitations.html
- Isaac 5.1 contact sensor/reporting:
  https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_physics_contact.html

### Robot hardware

- Franka Research 3 datasheet (1 kHz interface, repeatability, stiffness, limits):
  https://franka.de/hubfs/Datasheet%20Franka%20Research%203_R02212_2.2_EN.pdf
- Franka Hand manual/specification (force, width, speed):
  https://download.franka.de/documents/220010_Product%20Manual_Franka%20Hand_1.2_EN.pdf
- Franka Cartesian impedance API:
  https://frankarobotics.github.io/libfranka/latest/classfranka_1_1Robot.html

### Local installed evidence

- `${ISAAC_SIM_ROOT}/extscache/omni.usd.schema.physx-107.3.26+107.3.3.wx64.r.cp311.u353/plugins/PhysxSchema/resources/generatedSchema.usda`
- `${ISAAC_SIM_ROOT}/extscache/omni.physx.demos-107.3.26+107.3.3.cp311.u353/omni/physxdemos/scenes/CompliantContactsDemo.py`
