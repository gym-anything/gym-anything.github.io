# Physics-first humanoid football shooting

Status: pre-build research dossier and falsifiable implementation plan, 15 July
2026. No football simulation or real-world calibration result is claimed here.
The purpose of this document is to decide what must be true before a polished
scene, policy, or video can be called physically faithful.

Target runtime: Isaac Sim 5.1 / Omni PhysX 107.3 on Windows

Initial task: a free-floating humanoid kicks a stationary, regulation size-5
football into a full-size goal on a measured grass-like surface. The canonical
shot begins 11 m from the goal line. There is no goalkeeper in the first task.

## 0. Executive decision

This environment is feasible to a high and useful degree, but not by assigning
a rigid sphere one restitution value and adding a constant Magnus force.
Realistic shooting couples five systems whose characteristic scales differ by
orders of magnitude:

1. a torque-limited, free-floating humanoid transfers momentum while balancing
   on a compliant/frictional pitch;
2. a pressurised, layered shell deforms by centimetres over an approximately
   9 ms foot--ball impact and generates kilonewton reaction forces;
3. the ball's seams, grooves, spin, orientation, Reynolds number, wind-relative
   velocity, and wake history determine drag, curve, and knuckle motion;
4. grass/turf changes traction, rolling resistance, rebound, and oblique-bounce
   spin; and
5. the goal frame and net receive collision impulses while the Laws of the Game
   define scoring independently of the net animation.

The recommended architecture is therefore hybrid, but fully causal:

- **PhysX owns** the floating humanoid articulation, actuator/contact dynamics,
  rigid goal frame, ball six-degree-of-freedom state, rigid collisions, and scene
  timing.
- **A calibrated ball-contact module owns** pressure- and rate-dependent ball
  compression, distributed normal and tangential foot/ground contact, impact
  spin transfer, and equal-and-opposite reaction wrenches.
- **A calibrated flight module owns** air state, wind-relative drag, Magnus and
  reverse-Magnus regimes, buoyancy, aerodynamic spin decay, seam orientation,
  and a temporally coherent wake state for low-spin knuckle flight.
- **A calibrated pitch module owns** the macroscopic response that FIFA tests:
  vertical rebound, roll distance, shock absorption, deformation, traction, and
  rotational resistance. Grass blades remain visual unless a measured coupon
  proves they must be explicit.
- **A net module owns** cable/net deformation and ball--net contact. Net motion
  never decides whether a goal was scored.

Every custom force is applied each physics step (or resolved through a declared
impact microstep) and produces its equal-and-opposite reaction where one exists.
There is no velocity overwrite at kick-off, no scripted curve, no ball teleport,
no kinematic foot during contact, and no random lateral knuckle force drawn
independently each frame.

The first implementation should not begin with the humanoid. It should begin
with an instrumented ball flight/impact laboratory, because otherwise controller
error, contact error, and aerodynamic error cannot be identified separately.

## 1. Evidence vocabulary

| Label | Meaning |
|---|---|
| **STANDARD** | A current IFAB/FIFA requirement or test method. |
| **MEASURED** | A published physical experiment, retaining ball model, pressure, surface, speed, and conditions. |
| **ENGINE** | Official engine documentation or a locally reproduced capability in the installed build. |
| **DERIVED** | A calculation from identified inputs; it is not an independent measurement. |
| **PRIOR** | A model form, threshold, coefficient, or acceptance band to start investigation; it awaits calibration. |
| **OPEN** | A required specimen, measurement, parameter, or validation that we do not yet possess. |

A value fitted to one attractive trajectory remains a fit, not a material fact.
Training randomisation is not evidence. Agreement on a calibration trial is not
validation until held-out velocities, spins, orientations, and surfaces pass.

## 2. What the environment must mean

### 2.1 Canonical episode

- Regulation size-5 match ball, initially stationary on the pitch.
- Full-size goal: 7.32 m inside width and 2.44 m from ground to the lower edge of
  the crossbar.
- Ball centre initially 11 m from the goal line, matching the penalty-mark
  distance, with configurable lateral placement.
- A full floating-base humanoid begins behind or beside the ball.
- The robot approaches, plants, swings, contacts, and follows through under its
  actuator and balance constraints.
- The ball is allowed to fly, bounce, hit a post/crossbar, enter the net, or miss.
- The initial task ends after a goal, a settled miss, robot fall, timeout, or
  invalid contact sequence.

This is an atomic shooting task, not a full football match. Dribbling, a moving
ball, goalkeeper interaction, tackles, and multi-agent play are later tasks that
reuse the same physical modules.

### 2.2 Goal predicate

IFAB Law 10 says a goal is scored only when the whole ball passes over the goal
line, between the posts, and under the crossbar. For a spherical ball of radius
`r`, a robust continuous detector evaluates the swept ball state rather than a
single rendered frame:

- the trailing surface must have crossed the goal plane;
- the centre must have lateral clearance from both inside post faces by at least
  `r` at the crossing;
- the top of the ball must be below the lower crossbar face; and
- the lower surface of the ball must not be below the goal-opening ground plane;
  and
- no out-of-bounds or invalid event may have ended the episode first.

The detector must handle a fast ball crossing between ticks and a ball that
rebounds out after fully crossing. Touching the line, entering a loose axis-
aligned box, or moving the net is not a goal.

### 2.3 Fidelity claim we are willing to make

The first defensible claim is not "all football physics is solved." It is:

> For a named ball specimen, inflation pressure, atmospheric state, pitch
> specimen, robot model, and tested range of launch/contact conditions, the
> simulator reproduces declared held-out distributions of impact force,
> deformation, outgoing speed/spin, flight trajectory, bounce/roll, and robot
> reaction within stated uncertainty and numerical-convergence bounds.

Any condition outside that envelope is visibly marked extrapolation.

## 3. Causal chain and anti-cheat invariants

A successful shot must preserve this event chain:

1. The floating humanoid remains supported through explicit foot--pitch contact.
2. Joint torques pass through measured actuator limits, gearing/rotor dynamics,
   latency, and controller bandwidth.
3. The swing foot reaches the ball through robot dynamics, not a prescribed
   world-space pose during contact.
4. Foot geometry and ball shell first touch without initial penetration.
5. The ball compresses, shell tension/internal pressure rise, and a finite
   contact patch evolves over time.
6. Normal and tangential tractions change ball translation and spin while the
   equal-and-opposite wrench disturbs the foot and robot.
7. After separation, the integrated ball orientation advances its real seam
   pattern through the relative airflow.
8. Drag, lift/side force, buoyancy, wind, and aerodynamic torque act at every
   flight step from the current state.
9. Low-spin lateral motion emerges from a coherent seam/wake process, rather
   than a target-directed or framewise random force.
10. Ground, frame, and net interactions exchange impulses through collision and
    compliance.
11. The goal detector evaluates whole-ball plane crossing independently of the
    visual net.

Hard failures include:

- setting ball linear or angular velocity as a consequence of a kick command;
- disabling foot--ball collision and substituting a launch event;
- fixing the humanoid base or supporting it with an invisible constraint;
- changing the ball flight to steer toward the goal;
- selecting an aerodynamic phase after observing the desired target;
- applying ball contact force without the reaction on the robot;
- using CCD as a substitute for resolving impact compliance;
- snapping the ball into the net or scoring from centre-point crossing; and
- hiding poor pitch contact beneath visual grass.

## 4. Official geometry and test envelope

### 4.1 Ball and field

Current IFAB Law 2 requires a spherical ball of suitable material with:

| Quantity | Requirement | Evidence |
|---|---:|---|
| Circumference | 68--70 cm | **STANDARD** |
| Mass at match start | 410--450 g | **STANDARD** |
| Gauge pressure at sea level | 0.6--1.1 atmosphere | **STANDARD** |

The FIFA Quality Programme adds laboratory tests for circumference, sphericity,
rebound, water absorption, mass, pressure loss, shape/size retention, and
balance. The current manual specifies controlled laboratory temperature and
humidity. For an outdoor size-5 FIFA Quality Pro ball, its current table narrows
circumference to 68.5--69.5 cm and mass to 420--445 g. The exact quality tier and
ball model must be stored in each trace; the broader IFAB range alone does not
identify a physical ball.

Current IFAB Law 1 supplies the canonical scene dimensions:

| Quantity | Value | Evidence |
|---|---:|---|
| Goal inside width | 7.32 m | **STANDARD** |
| Ground to lower crossbar edge | 2.44 m | **STANDARD** |
| Post/crossbar maximum width/depth | 0.12 m | **STANDARD** |
| Penalty mark from goal line | 11.0 m | **STANDARD** |
| International field length | 100--110 m | **STANDARD** |
| International field width | 64--75 m | **STANDARD** |

The rendered environment may crop distant geometry for performance, but its
metric coordinate system, goal, markings, and shot distance may not be scaled.

### 4.2 Pitch performance, not merely green material

FIFA natural-surface and football-turf programmes test the response seen by a
player and ball. Representative target bands in the cited manuals include:

| Test | Natural pitch, excellent rating | Football Turf, FIFA Quality Pro | Evidence |
|---|---:|---:|---|
| Vertical ball rebound | 0.60--1.00 m | 0.60--0.85 m | **STANDARD** |
| Ball roll | 4.0--10.0 m | 4.0--8.0 m | **STANDARD** |
| Shock/peak shock absorption | 55--70% | 60--70% | **STANDARD** |
| Vertical/peak deformation | 4--11 mm | <=15 mm | **STANDARD** |
| Rotational resistance/peak torque | 25--50 N m | 30--45 N m | **STANDARD** |

The natural-pitch ball used for validation is itself checked on concrete: a
2.00 m drop should rebound to 1.35 +/- 0.03 m. This matters because pitch and
ball parameters otherwise become confounded.

The initial environment should select one declared surface family. "Grass" is
not a coefficient: natural moisture, cut height, soil compaction, infill, pile
direction, wear, and temperature change performance.

## 5. Nominal size-5 physical scales

For a nominal circumference `C = 0.690 m` and mass `m = 0.430 kg`:

| Derived quantity | Value | Status |
|---|---:|---|
| Diameter `C/pi` | 0.21963 m | **DERIVED** |
| Radius | 0.10982 m | **DERIVED** |
| Projected area `pi r^2` | 0.03789 m^2 | **DERIVED** |
| Displaced volume `4 pi r^3 / 3` | 0.00555 m^3 | **DERIVED** |
| Weight at standard gravity | 4.217 N | **DERIVED** |
| Thin-shell inertia `2 m r^2 / 3` | about 0.00346 kg m^2 | **PRIOR/DERIVED** |

The thin-shell inertia is only a starting estimate. Panels, adhesive, bladder,
valve, and internal construction make the real inertia and balance specimen-
specific; a torsional pendulum or bifilar measurement belongs in calibration.

At sea-level density `rho = 1.225 kg/m^3`, buoyancy is approximately `0.0666 N`,
or 1.58% of nominal ball weight. It is small but not optional when the stated
goal is faithful trajectory transfer across atmospheric conditions. Density
also scales drag and lift, so altitude, pressure, temperature, and humidity
must be changed together rather than through unrelated random multipliers.

External atmospheric buoyancy and internal inflation pressure are different
physics. The former is the net force from displaced ambient air. Uniform
internal pressure produces no free-flight thrust; it tensions and stiffens the
shell, changes deformation/contact, and can slightly change volume and total
mass. Neither should be represented by an arbitrary upward force.

## 6. Governing state and equations

### 6.1 Ball state

The flight/contact state minimally contains:

- centre position `x` and velocity `v`;
- orientation quaternion `q` and angular velocity `omega`;
- measured mass and inertia tensor;
- internal deformation/contact modal state during impact;
- inflation pressure and thermal state at episode start;
- named seam/groove geometry expressed in the ball frame;
- wake state and its history;
- active contact patch state; and
- specimen identity and calibration version.

The free-flight rigid motion is

```text
m dv/dt = m g + F_b + F_D + F_M + F_K + F_other
I domega/dt + omega x (I omega) = tau_aero + tau_contact
dq/dt = 0.5 q tensor [0, omega]
```

`F_K` denotes the resolved unsteady side/lift component of the wake model, not
an arbitrary knuckle noise term. During impact, contact modes provide the ball's
large local deformation while the centre/orientation remain coupled to PhysX.

### 6.2 Air-relative quantities

Let

```text
u = v_ball - v_air(x, t)
Re = rho |u| D / mu
S  = |omega_perp| r / |u|
q_dyn = 0.5 rho |u|^2
```

where `S` is the spin parameter and `omega_perp` is the spin component normal to
the flight direction. Air state comes from pressure, temperature, relative
humidity, and altitude using a documented moist-air equation (CIPM-2007 is the
reference implementation), not a hand-selected density per episode.

External buoyancy is

```text
F_b = -rho_air V g_vector
```

with the ball's measured external volume. The mass of internal air is already
part of the ball's measured total mass; it must not be added twice.

### 6.3 Drag

```text
F_D = -q_dyn A C_D(Re, S, q, seam, wake) u_hat
```

Wind-tunnel experiments show a drag crisis: the coefficient falls sharply when
the boundary layer transitions, and the critical Reynolds number changes with
panel/groove design. Published football values place this transition in the same
speed range as a real shot. A single constant `C_D` is therefore unacceptable.

The runtime representation should be a smooth, uncertainty-bearing response
surface fitted to one named ball across Reynolds number, spin parameter, and
seam orientations. It must be checked against held-out wind-tunnel and free-
flight trajectories. Extrapolation beyond the measurement hull is logged.

### 6.4 Magnus, reverse Magnus, and full spin direction

A convenient vector form is

```text
F_M = q_dyn A C_M(Re, S, orientation, wake)
      normalize(omega x u)
```

but the fitted coefficient may change with Reynolds number and spin parameter.
Rotating-ball experiments report that drag depends on spin parameter and that a
slight reverse-Magnus regime can occur near the critical region. Clamping the
coefficient to a universal positive line in `S` would erase that behaviour.

The model uses the full angular-velocity vector. Side spin, topspin, backspin,
and mixed-axis spin should emerge from impact and affect all three trajectory
coordinates without separate scripted shot modes.

### 6.5 Knuckle flight is a wake-history problem

Low-spin shots expose changing seam/groove orientations slowly enough that
asymmetric separation and vortex switching create temporally varying side and
lift forces. Measurements report substantially larger transient vortex lift for
knuckle kicks than straight instep kicks and a characteristic force frequency
near 3.5 Hz in the tested condition.

That frequency and amplitude are not universal constants. A faithful reduced
model needs:

- ball-frame seam/groove orientation;
- current and recent `Re` and air-relative direction;
- a continuous, temporally correlated wake state;
- measured orientation-conditioned force spectra/cross-correlations;
- deterministic integration for fixed initial state and wind realisation; and
- an explicitly seeded, measured turbulence input if unresolved atmospheric
  turbulence is represented statistically.

Independent Gaussian force samples, a sine wave with arbitrary phase, or a
force aimed away from the goalkeeper are disallowed. The reduced wake model is
accepted only after reproducing held-out lateral/vertical force spectra and
trajectory distributions for physical launches.

### 6.6 Aerodynamic torque and spin decay

Spin is not constant in flight. Aerodynamic torque depends on speed, spin,
moment of inertia, surface construction, and flow regime. Published work finds
spin decay related to the product of initial spin and speed, with moment of
inertia dominant among ball construction variables.

The runtime uses a fitted vector torque law

```text
tau_aero = T(Re, S, orientation, omega, wake)
```

rather than exponential decay chosen for appearance. Calibration records both
translation and orientation at high speed so drag, lift, and torque are not
fitted from one projected curve.

## 7. Foot--ball impact physics

### 7.1 Measured event scale

High-speed studies of soccer instep kicks report approximately:

| Observable | Published result | Evidence |
|---|---:|---|
| Visual contact duration | 9.0 +/- 0.4 ms | **MEASURED** |
| Maximum ball deformation | 6.2 +/- 0.6 cm | **MEASURED** |
| Peak ball reaction force | 2926 +/- 509 N | **MEASURED** |
| Mean force | 1403 +/- 129 N | **MEASURED** |

The precise values belong to the tested players, ball, pressure, and kick, not
every future shot. They establish the scale: deformation is tens of millimetres,
contact is milliseconds, and peak reaction is kilonewtons.

For a nominal 0.430 kg ball accelerated from rest to 25 m/s, the translational
impulse is 10.75 N s. Spread uniformly over 9 ms it would imply about 1.19 kN;
the force history is not uniform, so a roughly 3 kN peak is plausible. This is a
**DERIVED consistency check**, not a fitted contact law.

Dividing the central peak-force scale by the central maximum-deformation scale
gives a secant stiffness near 47 kN/m. Treating that as a linear ball would give
a roughly 53 Hz natural frequency and a half-period near 9.5 ms--an interesting
agreement in scale with the observed event. It is not a constitutive fit: peak
force and peak compression need not be simultaneous, and the real pressurised
shell is nonlinear and hysteretic.

### 7.2 Why a rigid restitution sphere is insufficient

A single restitution/friction pair cannot jointly identify:

- pressure-dependent force--compression and hysteresis;
- finite contact area and changing pressure centre;
- shell/bladder modal vibration and rate dependence;
- panel/seam orientation effects;
- the speed/spin tradeoff from impact offset;
- local foot compliance and ankle motion;
- tangential stick, slip, and slip reversal;
- oblique ground bounce; and
- the time history of reaction transmitted into the robot.

High-speed curve-kick experiments show that impact offset controls outgoing
speed and spin, while ball deformation can transfer torque even when a simple
point-friction explanation is insufficient. Finite-element studies model a
hyperelastic bladder and orthotropic panel shell and report orientation changes
in restitution, contact duration, and deformation.

### 7.3 Recommended runtime contact representation

Use a stateful reduced-order pressurised-shell contact model, calibrated against
a higher-fidelity shell/FEM reference and physical impact coupons. It should
contain:

- radial/modal compression coordinates and rates;
- pressure-volume work and shell tension;
- rate-dependent dissipation/hysteresis;
- distributed contact samples over real foot/ground geometry;
- tangential compliance with stick/slip history;
- panel/seam orientation features at the patch;
- pressure, temperature, and specimen parameters; and
- a mapping from patch traction to net force and torque.

The model is not permitted to infer desired outgoing speed/spin. Its outputs are
tractions. Their integral updates the ball, and the opposite wrench is applied
at the same world-space patch on the robot or ground.

An offline explicit shell/FE model is the reference for deformation fields and
internal energetics. Running that full model every interactive frame is optional
only after the reduced model reproduces its held-out observables.

### 7.4 Numerical resolution

Samples within a 9 ms contact are:

| Physics rate | Samples/contact |
|---:|---:|
| 60 Hz | 0.54 |
| 120 Hz | 1.08 |
| 240 Hz | 2.16 |
| 480 Hz | 4.32 |
| 960 Hz | 8.64 |
| 1,000 Hz | 9.00 |
| 1,920 Hz | 17.28 |
| 2,000 Hz | 18.00 |

CCD can stop tunnelling but cannot create the missing force history. Candidate
runtime strategies must be benchmarked:

1. constant PhysX stepping at 960--1,920 Hz;
2. lower global stepping with a tightly coupled contact micro-integrator and
   conservative impulse/wrench exchange; and
3. an event-triggered high-rate rigid/contact window whose state transition is
   explicitly tested for energy and momentum error.

The chosen rate must pass 480/960/1920 Hz convergence for outgoing speed/spin,
peak force, impulse, robot joint response, and wall time. Render rate and policy
rate remain independent.

## 8. Pitch contact and robot traction

The pitch has two distinct consumers:

- the ball: vertical/oblique bounce, roll, spin change, and settling;
- the robot: normal compliance, shear traction, torsional resistance, foot slip,
  and energy absorption.

A single PhysX material pair cannot safely stand in for both across all speeds.
The pitch module should provide a measured compliant normal law, tangential
history, rolling resistance, and spatially varying surface state. It is fitted
to FIFA-style coupons plus robot-foot traction tests.

Natural grass blades need not each become a collider. The physically important
macroscopic response is represented explicitly; blade geometry is rendered and
may inform a measured directional/friction map. Local variation uses measured
pitch maps and a logged seed, not broad arbitrary domain randomisation.

Required pitch coupons:

- FIFA vertical rebound at multiple locations;
- FIFA ball roll along and across mowing/pile direction;
- oblique bounce over speed, angle, spin, and moisture;
- shock absorption and vertical deformation;
- rotational resistance;
- instrumented humanoid-foot shear/rotation under normal load; and
- spatial repeatability and temporal drift.

The FIFA natural-surface ball-roll method places the point approximately below
the ball centre at `1.000 +/- 0.005 m` above the surface on two smooth guide
bars, then measures from first surface contact to the resting centre projection.
The P3 dependency-free coupon therefore derives its initial speed from that
declared ramp potential energy (or accepts a measured exit-speed override); it
does not invent an arbitrary horizontal launch speed.  Wind, four directions,
three repeats per direction, ramp transfer loss, and the named test ball remain
part of the physical calibration protocol.

## 9. Goal frame, net, and render contract

### 9.1 Physical frame and net

The posts and crossbar use measured geometry, mass/inertia or rigid anchoring,
contact compliance, and surface friction. Ball--frame bounce is calibrated with
normal and oblique launcher impacts.

The net is a deformable cable network with measured:

- mesh topology and cord diameter;
- linear density;
- axial stiffness and damping;
- knot/junction response;
- boundary attachment layout and pretension;
- ball--cord friction/contact thickness; and
- energy dissipation under impact.

The installed PhysX surface-deformable or a purpose-built cable model can be a
runtime candidate. Neither is accepted by appearance alone. A pendulum/launcher
coupon must compare ball capture, peak deflection, rebound, settling frequency,
and attachment loads. Public FIFA documents establish dimensions and safety
testing but do not provide enough dynamic net material data; the initial net
parameter set is therefore **OPEN**.

### 9.2 Visual fidelity is coupled to physical state

The scene is intentionally simple, but it must look like a real training or
match pitch rather than a green plane with primitives:

- the ball uses a measured size, panel layout, groove depth/width, valve, and
  material construction; the rendered orientation is exactly the orientation
  used by the aerodynamic model;
- the reduced contact modes drive visible shell compression and recovery during
  the 9 ms impact--a rigid visual sphere is not acceptable for high-speed frames;
- near-camera grass uses geometry/instancing and measured sward height, while
  distance LODs retain correct colour/roughness and mowing direction;
- painted lines have real metric width, thickness/roughness variation, and no
  z-fighting; pitch wear, moisture, and local variation agree with the physical
  surface state rather than arbitrary grime decals;
- posts, crossbar, anchors, net supports, hooks, cord diameter, knots, and mesh
  spacing match the selected goal/net specimen;
- rendered net vertices are driven from the physical cable state. A separate
  canned net animation is forbidden;
- shoe/foot collision geometry and the visible robot foot align closely enough
  that the impact patch does not float or penetrate visibly;
- sun/sky, exposure, white balance, shadows, and motion blur are based on a
  declared capture condition; and
- scientific cameras include a high-shutter, high-frame-rate contact view,
  orthogonal trajectory views, and force/axis overlays that can be disabled.

The hero render, training observations, motion-frame figures, and validation
plots must all come from the same USD and episode trace. Presentation may change
camera and render quality, but never the underlying physical rollout.

### 9.3 Fixed-step rendering contract

An initial visible P5 capture falsified our first stepping implementation. In
Isaac Sim 5.1, `World.step(render=True)` delegates to the Kit update loop when
both physics and rendering timesteps are nonzero. With a 2 ms physics timestep
and 20 ms rendering timestep, that update can advance multiple physics ticks.
The outer Python loop therefore missed controller, aerodynamic, and custom
contact updates on hidden ticks: the ball and robot diverged on the very first
sample, the humanoid fell, and the shot failed. Those images and that trace are
not evidence.

The integrated runner now owns one and only one `World.step(render=False)` for
every 2 ms interval. When a viewport update is due it subsequently calls the
render-only path, which disables simulation advancement around the Kit update.
The report independently records the expected physics clock, its maximum error,
the count of render-only updates, and the maximum physics-clock advance caused
by any render. Camera changes receive two render-only warm-up updates to avoid a
one-frame-old view.

The current capture run requested 5,000 fixed physics steps and 524 render-only
updates. Its maximum accumulated physics-clock error is below `5e-7 s`; maximum
render-induced physics-clock advance is exactly `0.0 s`. All 500 recorded ball,
spin, pelvis, foot, contact, and control samples match the canonical headless
trace exactly. This establishes rendering neutrality for this deterministic
episode, not physical validity of the priors.

## 10. Humanoid dynamics and control

### 10.1 Full-body kicking problem

A dynamic kick is not a leg animation. The robot must manage:

- approach momentum;
- support-foot placement and traction;
- centre of mass and angular momentum;
- wind-up and hip rotation;
- knee extension and distal-link speed;
- foot orientation/impact offset for speed and spin;
- the impact disturbance; and
- follow-through or recovery without an invisible support.

Recent humanoid research describes a six-phase kicking motion (approach, plant,
wind-up, cocking, swing, follow-through) and combines trajectory optimisation
with reference-tracking reinforcement learning. It demonstrates useful
simulation methodology, not validation of our ball model or Unitree hardware.

### 10.2 Robot model requirements

- Floating base, gravity enabled, no hidden stabilising joint.
- Collision geometry for soles, swing foot, shank, and body that matches the
  selected hardware revision.
- Named actuator torque/speed envelopes, reflected inertia, damping, delay,
  control rate, and thermal limits.
- Joint position/velocity/effort limits from a traceable URDF or manufacturer
  record, verified against the physical robot where possible.
- Foot sole compliance and traction measured on the selected pitch.
- IMU/joint sensing noise and latency added from measurements, not arbitrary
  percentages.
- Controller actions at joint torque or physically identified motor-command
  level. Position targets are acceptable only through a documented actuator
  model that produces bounded torques.

### 10.3 Local Unitree G1 asset warning

The repository contains G1-related assets, including fixed-base USD variants,
and an ignored local floating-base 29-DoF URDF. The local URDF lists joint
effort/speed limits that do not cleanly match the current public Unitree G1 page
for every joint (notably the knee across G1/G1 EDU variants). Consequently:

- fixed-base assets are disallowed for the task;
- the exact G1/G1 EDU revision and serialised hardware configuration are
  **OPEN**;
- asset provenance and inertial/collision fidelity must be audited before a
  hardware-transfer claim; and
- the imported articulation must be checked link by link against its source.

The scene can be developed with a declared simulation robot while this remains
open, but the dashboard and paper must say so.

## 11. Installed Isaac Sim / PhysX capability audit

Local installation:

```text
$env:ISAAC_SIM_ROOT
Isaac Sim 5.1.0
Omni PhysX 107.3.26 / PhysX 107.3.3 family
GPU: RTX 3090, 24 GiB
```

| Capability | Local/official result | Consequence |
|---|---|---|
| Rigid body and articulation dynamics | Available | PhysX owns robot, ball rigid state, frame, and ordinary collision. |
| Apply force/torque at a world position | Available | Custom aero/contact can inject causal wrenches. |
| Pre-physics callback | Available | State-dependent forces can be evaluated before each step. |
| Sweep and speculative CCD | Available | Use for fast ball/foot/frame/net candidates; profile GPU cost. |
| Surface deformable (XPBD FEM) | Available/beta family | Candidate for net coupons, not assumed correct. |
| Deprecated particle cloth pressure/inflatable path | Locally present | Not the canonical ball: deprecated and still not a validated football shell. |
| Surface-deformable stretch/shear and inflatable parity | Limited in 107.3 migration docs | New surface deformable cannot simply become a pressurised anisotropic football. |
| Direct GPU API with CCD | Documented limitations | Do not select a backend before the collision path is proven. |

Native PhysX is essential, but the installed engine does not expose a ready-made
seam-aware aerodynamic model or a validated pressurised soccer-ball constitutive
law. Implementing those force laws beside PhysX is not a physics shortcut when
they are state-based, calibrated, conservative where appropriate, and coupled
both ways. A velocity launch or trajectory script would be a shortcut.

## 12. Modular software architecture

The physics should be reusable for launch rigs, different humanoids, robot arms,
and teleoperation. Suggested boundaries:

```text
FootballEnvironment
|- WorldClock / deterministic trace recorder
|- AtmosphereModel
|  |- moist-air state
|  `- wind field / turbulence realisation
|- BallSpecimen
|  |- geometry, mass, inertia, seam mesh
|  |- pressure/thermal state
|  |- ContactShellModel
|  `- AerodynamicModel + WakeState
|- PitchModel
|- GoalFrameModel
|- GoalNetModel
|- RobotAdapter
|  |- articulation and collision mapping
|  |- actuator/sensor model
|  `- controller or policy interface
|- ContinuousGoalDetector
`- Metrics / reward / falsification monitors
```

### 12.1 Interfaces

`AtmosphereModel.sample(x, t)` returns pressure, temperature, humidity, density,
viscosity, wind velocity, and uncertainty.

`AerodynamicModel.evaluate(ball_state, atmosphere, dt)` returns force, torque,
updated wake state, coefficient provenance, and extrapolation flags.

`ContactShellModel.resolve(patches, ball_state, dt_sub)` returns patch tractions,
deformation state, work/energy terms, and uncertainty. The environment applies
opposite patch wrenches to the contacting bodies.

`PitchModel.resolve_ball(...)` and `resolve_foot(...)` share one measured surface
state but use validated contact regimes.

`RobotAdapter` exposes link poses/velocities, collision shapes, actuator state,
sensor packets, and bounded commands without embedding football logic.
For impulsive contact it also exposes the live contact-point inverse-mass tensor
derived from the generalized mass matrix and shifted body Jacobian. A selected
support constraint is always accompanied by free-floating and translation-only
brackets; none is called a hardware measurement.

`GoalDetector.update(previous_ball, current_ball)` returns a swept crossing event
with the exact time and clearance.

Each model stores a semantic version and calibration bundle hash in the episode
trace. This makes it possible to replace the G1, ball, atmosphere, or net without
rewriting the environment.

## 13. Physics and control clocks

The clocks are distinct and logged:

| Clock | Initial candidate | Status |
|---|---:|---|
| Render | 60 Hz | **PRIOR** |
| Policy/high-level control | 50--100 Hz | **PRIOR** |
| Motor/low-level control | 500--1,000 Hz if hardware supports it | **OPEN/PRIOR** |
| Rigid physics | 500 Hz current integrated profile | Numerically exercised; **PRIOR** |
| Foot/ball and pitch microstep | 20 kHz current profile | 10/20/40 kHz sweep passes |
| Cable-net microstep | 24 kHz current profile | P3 convergence coupon passes |
| Aerodynamic update | every rigid step | Required |

No rate is accepted because it sounds standard. The convergence and real-time
probes select it. Physics may run faster or slower than wall time during
calibration; training throughput and physical accuracy are reported separately.

## 14. Calibration programme

### Gate A: metrology and specimen registry

For each ball:

- mass before/after inflation;
- circumference along multiple great circles;
- sphericity and panel/seam scan;
- valve position;
- gauge pressure, temperature, humidity, and equilibration time;
- centre-of-mass offset and inertia tensor;
- construction/model/lot and usage history.

For the pitch, net, frame, robot foot, and robot, store equally explicit specimen
identities. This prevents one set of fitted numbers becoming "the football."

### Gate B: quasistatic/dynamic ball compression

- platen compression over orientations, pressures, rates, and dwell;
- force--displacement hysteresis and relaxation;
- local indentation over panel, seam, and valve neighbourhood;
- repeatability and thermal dependence.

Exit: reduced and high-fidelity shell models reproduce held-out curves, work,
and orientation trends.

### Gate C: normal impact rig

- launcher into instrumented rigid plate over 5--35 m/s;
- force plate at >=10 kHz plus high-speed imaging;
- contact duration, deformation, peak/mean force, impulse, rebound, and modal
  ringing;
- pressures, temperatures, and seam orientations held out from fitting.

Exit: momentum balance closes and all primary observables converge numerically.

### Gate D: oblique foot and surface impact

- instrumented surrogate foot with real geometry/compliance;
- impact speed, foot velocity direction, offset, orientation, friction, and
  incoming ball spin varied systematically;
- measure 6-D wrench, outgoing velocity/spin, patch motion, and work.

Exit: the model predicts speed--spin tradeoffs and tangential-force reversal on
held-out combinations without retuning.

### Gate E: wind-tunnel coefficient map

- named ball at multiple seam orientations;
- `Re` spanning subcritical, critical, and supercritical flow;
- spin parameter and spin-axis sweep;
- six-axis mean force/torque and unsteady spectra;
- repeated low-spin trials with controlled upstream turbulence.

Exit: smooth coefficient/wake model predicts held-out forces, spectra, drag-
crisis location, and any observed reverse-Magnus region with uncertainty.

### Gate F: free-flight launcher

- stereo high-speed/long-baseline tracking of position and orientation;
- straight, curve, topspin/backspin, and low-spin launches;
- 5--35 m/s, multiple axes, seam orientations, wind/air states;
- calibration trials separated from blind holdouts.

Exit: flight model predicts complete 3-D trajectories and spin histories, not
only landing points.

### Gate G: pitch

Run official-style rebound, roll, shock/deformation, rotational-resistance, and
traction coupons. Add oblique ball and robot-foot trials.

Exit: held-out locations/directions/moisture states reproduce distributions and
the robot cannot exploit a numerical traction regime absent from the specimen.

### Gate H: frame and net

Launcher trials across post/crossbar incidence and net impact locations, speeds,
and spins. Measure frame rebound, ball capture/rebound, net peak deflection,
attachment force, frequency, and settling.

Exit: continuous collision catches all tested impacts and dynamic observables
match within declared uncertainty.

### Gate I: robot

- joint/link inertial audit;
- motor torque--speed/current response and delay;
- free-swing and loaded tracking;
- foot/ground traction and compliance;
- balance pushes and impact-like disturbance response.

Exit: the floating robot matches hardware observables before learning to kick.

### Gate J: integrated blind kicks

Physical robot or instrumented kicking rig trials supply contact, launch, flight,
and robot reaction in one trace. Initial conditions are reconstructed in sim;
no coefficient is changed after holdout trajectories are revealed.

## 15. Numerical thinking probes

`probes/flight_scale_probe.py` is a standard-library-only scale calculation. It
is deliberately not the future flight solver and labels all illustrative
coefficient curves as priors.

### 15.1 Reynolds and force scale

For the nominal ball and sea-level air:

| Speed | Reynolds number | `q_dyn A` |
|---:|---:|---:|
| 5 m/s | 74,324 | 0.580 N |
| 10 m/s | 148,647 | 2.321 N |
| 15 m/s | 222,971 | 5.221 N |
| 20 m/s | 297,294 | 9.282 N |
| 25 m/s | 371,618 | 14.504 N |
| 30 m/s | 445,942 | 20.885 N |
| 35 m/s | 520,265 | 28.427 N |

At 25 m/s, `C_D=0.2` implies 2.90 N drag while `C_D=0.5` implies 7.25 N.
This difference is of the same order as the ball's weight and cannot be hidden
inside a cosmetic trajectory tweak.

### 15.2 Spin parameter scale

At 25 m/s:

| Spin | `S = omega r / v` |
|---:|---:|
| 1 rev/s | 0.028 |
| 3 rev/s | 0.083 |
| 5 rev/s | 0.138 |
| 8 rev/s | 0.221 |
| 10 rev/s | 0.276 |

Published rotating-ball data place interesting coefficient changes in this
range. Spin cannot be reduced to a binary "curve shot" flag.

### 15.3 Illustrative 11 m trajectory scale

The probe uses a 22 m/s, 10-degree launch and deliberately uncalibrated smooth
coefficient priors. It exists only to test orders of magnitude:

- gravity plus sea-level buoyancy reaches the 11 m plane in roughly 0.51 s;
- adding plausible drag delays and lowers the ball materially;
- an illustrative 6 rev/s side-spin coefficient can move it roughly 0.8 m
  laterally by the goal plane; and
- a 2 N, 3.5 Hz illustrative low-spin force changes lateral/vertical crossing
  by centimetres depending on wake phase.

Those are **PRIOR scale results**, not validation. Their lesson is that flight
physics can easily decide whether a shot crosses a post/crossbar boundary, so
calibration matters.

### 15.4 Humanoid launch feasibility scale

The same uncalibrated flight prior was swept over launch speed and elevation to
ask a narrow question: does the centre cross the 11 m plane between one ball
radius above ground and one radius below the 2.44 m crossbar?

| Launch speed | Ball kinetic energy | Tested elevations reaching opening |
|---:|---:|---|
| 10 m/s | 21.5 J | none |
| 11 m/s | 26.0 J | none |
| 12 m/s | 31.0 J | 35, 40 degrees |
| 13 m/s | 36.3 J | 30, 35, 40 degrees |
| 15 m/s | 48.4 J | 20, 25, 30 degrees |
| 18 m/s | 69.7 J | 20 degrees |

This coarse angle grid ignores bounce and uses aerodynamic **PRIORS**, so it is
not an actuator requirement. It does show why a published humanoid result of
"over 11 m/s" does not establish that our robot can score from 11 m. P4 must
measure the selected robot's attainable foot speed, effective striking mass,
support traction, torque/speed saturation, outgoing ball state, and recovery.

### 15.5 Configuration-dependent impact response probe

The first G1 contact implementation used a transparent but uncalibrated 2 kg
scalar foot-mass prior. That is inadequate for two reasons. First, articulated
impact response changes with configuration and direction. Second, a scalar
cannot represent cross-axis response or the way tangential impulse produces
both ball translation and spin.

For a body-origin spatial Jacobian with linear-first convention, the contact
point Jacobian is

```text
J_p = J_v - [r]x J_w .
```

The free articulated point inverse-mass response is

```text
W_free = J_p M^-1 J_p^T .
```

For an explicitly declared ideal support constraint `C qdot = 0`, the selected
planted-foot bracket is

```text
P_C = M^-1 - M^-1 C^T (C M^-1 C^T)^+ C M^-1
W_foot = J_p P_C J_p^T .
```

The free hollow ball's response at contact arm `r_b` is

```text
W_ball = I_3 / m_b - [r_b]x I_b^-1 [r_b]x .
```

Thus only the normal damping law needs a scalar projection,

```text
m_red(n) = 1 / (n^T (W_foot + W_ball) n),
```

while the complete internal relative-velocity update remains tensor-valued:

```text
Delta v_rel = -(W_foot + W_ball) impulse_ball .
```

This follows operational-space inertia rather than inventing a stronger foot.
The support-rigid, support-translation, and free-floating G1 results differed by
less than 0.1% for the observed normal, but all three remain in each contact
sample because another posture or direction need not be insensitive.

The initial live G1 audit falsified the 2 kg scalar prior. In the promoted
integrated curl kick, the live directional foot mass varies from
0.654--0.703 kg and the combined foot/ball reduced mass varies from
0.259--0.267 kg. These are **ASSET-DERIVED MODEL VALUES**, not Unitree hardware
measurements. The local generalized mass matrix does not establish the exact
G1 revision, rotor reflected inertia, transmission stiffness/backlash, or
closed-loop impact impedance. Published robot-impact work likewise warns that
the appropriate inverse inertia depends on actuator stiffness and impact time
scale; physical impact identification remains mandatory.

The contact surface was also promoted from an oriented-box approximation to a
deterministic convex proxy built from the pinned visible right-shoe STL. The
asset contains 1,248 vertices and 2,492 triangles, is queried by exact closest-
triangle distance, and records both the source-mesh and generated-asset SHA-256
hashes. The former box is retained only as a falsification coupon: at the
canonical recorded contact pose it reports contact 9.251 mm too early. The
convex hull is still an outer approximation that fills true concavities; it is
more faithful than the box, not an exact concave shoe surface.

The 500 Hz Isaac coupon was swept at 10, 20, and 40 kHz internal contact rates:

| Observable | 10 kHz | 20 kHz | 40 kHz | 10-to-40 kHz delta |
|---|---:|---:|---:|---:|
| Forward separation speed | 7.6265 m/s | 7.6304 m/s | 7.6325 m/s | 0.0790% |
| Vertical separation speed | 1.2858 m/s | 1.2806 m/s | 1.2768 m/s | 0.7042% |
| Separation spin magnitude | 10.2399 rad/s | 10.2315 rad/s | 10.2294 rad/s | 0.1029% |
| Peak force | 481.02 N | 481.10 N | 481.15 N | 0.0266% |
| Peak compression | 22.283 mm | 22.307 mm | 22.319 mm | 0.1634% |
| Normal impulse | 3.2794 N s | 3.2811 N s | 3.2820 N s | 0.0790% |

The machine-readable gate is
`outputs/p4_foot_contact_tensor_rate_sweep.json`. Convergence only shows that the
chosen numerical rate is adequate for this prior; it does not validate the
constitutive law.

Each tensor substep also audits midpoint work. With constant `W` over that
microstep,

```text
work_extracted = dt F^T (v_old + v_new) / 2
               = T_rel,old - T_rel,new .
```

Gas, shell, and tangential-spring energy are tracked separately. The promoted
integrated curl kick extracts and ultimately dissipates 2.06888 J, closes its
constitutive ledger to `8.9e-16 J`, leaves zero residual contact energy, and
records no negative incremental energy creation. The gate separately requires
positive total dissipation, passive increments, and `1e-10 J` global work
closure.

### 15.6 Integrated P5 evidence, shot profiles, and falsifying failures

Replacing the scalar foot mass and box geometry did not preserve old success by
design. Early convex-shoe trajectories stopped short, moved the base too far,
or failed recovery. This is important evidence that the task result is not
scripted: changing the physical contact changes whether the shot scores.

The promoted bounded G1 controller uses an unclipped leg swing, a 0.4 rad arm
counter-swing, braking, guard hand-back to the balance policy, and recovery. A
named profile is allowed to select only robot spawn/support pose and actuator
command targets. Its contract explicitly forbids prescribing the ball's
outgoing pose, velocity, spin, flight, or task result.

The default `curl` trace in `outputs/isaac_p5_integrated_shot.json` records:

| Observable | Canonical result |
|---|---:|
| Pass / whole-ball goal | true / true |
| Ball velocity at foot separation | `(7.3448, 0.3559, 1.1876)` m/s |
| Ball angular velocity at separation | `(-1.8762, 0.4418, 10.7591)` rad/s |
| Separation spin parameter | 0.16114 |
| Goal event time | 7.036194 s |
| Goal-event centre | `(0.1098, 1.0376, 0.1092)` m |
| Lateral residual versus constant heading | +0.5005 m |
| Peak foot--ball force / compression | 461.99 N / 21.760 mm |
| Foot-contact work / dissipation | 2.06888 J / 2.06888 J |
| Constitutive energy residual | `8.9e-16 J` |
| Pitch max compression / shadow disagreement | 5.932 mm / 2.342 mm |
| Worst / recovered / final upright cosine | 0.907 / 0.985 / 1.000 |
| Minimum pelvis height / base excursion | 0.708 m / 0.346 m |
| Non-foot pitch contact / target clipping / state writes | 0 N / 0 / 0 |
| Visible/headless sampled-state difference | exactly zero over 500 samples |
| Maximum render-induced physics-clock advance | `0.0 s` over 524 render updates |

The curl separation speed is 7.449 m/s. Its maximum post-separation drag and
Magnus forces are 0.632 N and 0.263 N respectively. The stated 0.5005 m lateral
residual includes every post-separation force and ground contact and is not
mislabelled as Magnus-only displacement.

The second named `low_spin` profile also scores and recovers without any runtime
parameter override. Its contact generates a 7.873 m/s separation speed,
1.359 rad/s spin magnitude, and spin parameter 0.01896. The deterministic
coherent wake becomes active, but its maximum force is only 9.20 mN and the
lateral residual is 0.0455 m. This is a useful **knuckle-ready low-spin prior**,
not evidence of a visually dramatic or physically calibrated high-speed
knuckleball. The cross-profile evidence is machine-gated in
`outputs/p5_shot_profiles_summary.json`.

Both balls stop before the sloped physical back net, so net deflection is
correctly zero. A whole-ball goal is the task truth predicate; requiring
back-net contact would reject a physically valid slow ground shot and contradict
Section 16.2. The physical back net remains active and has a separate passing P3
impact coupon. Roof and side cords remain visual-only and explicitly **OPEN**.

The visual ball is deformed from the same resolved foot and pitch compression
coordinates. In the curl trace its determinant stays above 0.912, maximum
translation stays below 7.1 mm, and the collider radius remains exactly
0.109817 m before and after. This reduced render mode makes deformation visible
without pretending that the collision sphere is a calibrated shell FE model.

These P5 results are causal, numerically audited **PRIOR simulation results**.
They do not close Gates A--J: blind physical ball, pitch, net, and G1 trials are
still required before claiming real-world fidelity.

The six ray-traced motion frames under `renders/p5_*.png` derive from the same
passing state history. Their machine-readable timing/camera provenance is in
`outputs/isaac_p5_integrated_shot_frames_evidence.json`; the independent
`probes/p5_evidence_probe.py` requires exact visible/headless sample equality.

## 16. Metrics, reward, and termination

### 16.1 Truth metrics

Every episode records:

- robot base/link/joint/actuator state and contact wrenches;
- ball position, orientation, velocity, spin, pressure/deformation state;
- foot--ball patch force/torque, impulse, work, duration, maximum compression;
- aerodynamic `Re`, `S`, coefficients, forces, torque, wake state, wind state;
- pitch/frame/net contacts and energy terms;
- minimum post/crossbar clearance and exact goal-plane crossing;
- linear/angular momentum and energy residuals;
- solver iterations, dt, CCD events, real-time factor, and extrapolation flags;
- calibration bundle hashes and random seeds.

### 16.2 Sparse objective

Primary task success is the continuous whole-ball goal predicate. It is not
defined by net contact, forward ball velocity, or distance to a target point.

Secondary evaluation reports:

- shot speed and spin at separation;
- placement/clearance at the goal plane;
- time to goal;
- robot fall/slip/joint-limit/torque-limit events;
- energy consumed and recovery quality; and
- robustness across the measured parameter distribution.

### 16.3 Training reward prior

Reward shaping may include causal progress:

- stable approach and support placement;
- foot pre-impact velocity/orientation relative to a task command;
- physically produced ball velocity toward a requested goal-plane target;
- whole-ball goal bonus;
- balance/recovery and bounded energy/impact penalties.

Any term that directly moves the ball, rewards a hidden scripted shot class, or
lets the policy exploit model extrapolation is forbidden. Reward weights are
**PRIOR** until learning diagnostics show they do not replace task truth.

## 17. Validation and falsification matrix

Suggested first acceptance bands below are **PRIOR engineering targets**, not
published universal tolerances. They must be tightened or relaxed from physical
repeatability and sensor uncertainty.

| Observable | Initial target on blind holdouts | Failure interpretation |
|---|---:|---|
| Impact impulse | <=5% relative or within measurement CI | contact momentum wrong |
| Contact duration | <=10% | stiffness/rate or timestep wrong |
| Peak force | <=10% | force history/contact model wrong |
| Maximum deformation | <=10% | shell/pressure model wrong |
| Outgoing speed | <=5% | normal impulse/energy wrong |
| Outgoing spin vector | <=5% magnitude and <=3 deg axis | patch/tangential model wrong |
| Force/torque coefficient map | within experimental CI | aerodynamic response surface wrong |
| Flight path to 11 m | <=50 mm 3-D RMSE | aero/initial state wrong |
| Flight path to 20 m | <=100 mm 3-D RMSE | accumulated aero error |
| Spin history | <=5% over validated flight | aero torque/inertia wrong |
| FIFA rebound/roll | inside target distribution | pitch/ball contact wrong |
| Robot joint/base response | within identified uncertainty | coupling/actuator model wrong |
| Momentum residual | <1% of event impulse | implementation leak |
| Energy residual | explained by stored/dissipated/work terms | nonphysical source/sink |

Required adversarial tests:

1. Disable aerodynamics: trajectory must reduce to gravity plus buoyancy and
   collision, not retain learned/scripted curl.
2. Reverse spin: lateral curve must reverse when the measured regime predicts
   it, while any documented reverse-Magnus region is retained.
3. Rotate the same low-spin ball: seam-conditioned force history must change
   consistently with calibration.
4. Zero wind versus matched moving air: only relative airflow may matter.
5. Change altitude through a consistent atmosphere: density, viscosity,
   buoyancy, drag, and lift must change together.
6. Double physics resolution: impact and flight observables must converge.
7. Remove robot reaction wrench: the conservation monitor must fail loudly.
8. Fix the robot base in a test branch: task result is marked invalid, never a
   better policy score.
9. Make net invisible/remove it: the goal predicate must remain identical.
10. Shoot exactly at post/crossbar boundaries: continuous clearance logic must
    resolve whole-ball crossing correctly.
11. Swap ball specimen without its calibration: runtime must flag unsupported
    extrapolation, not silently reuse coefficients.
12. Resume/replay: deterministic inputs must reproduce within the declared
    engine determinism envelope.

## 18. Build ladder and gates

### P0 -- research and reproducible scale probes

- This dossier and source ledger.
- Geometry/air/contact scale probe.
- Local Isaac capability/timing probe.

Exit: architecture and open measurements are explicit; no realism claim.

### P1 -- instrumented flight laboratory

- Regulation visual/metric ball with integrated orientation/seam state.
- Atmosphere, wind-relative drag, buoyancy, Magnus, torque, wake interface.
- Launcher that sets a declared measured initial state for calibration only.
- 3-D traces, coefficient diagnostics, and convergence tests.

Exit: published-data reproduction plus our planned physical holdout protocol.
The launcher is a scientific instrument, not the final task mechanism.

### P2 -- pressurised impact laboratory

- Shell/reference coupon and reduced-order contact model.
- Plate and surrogate-foot impact rigs.
- Two-way force application and energy/momentum audit.

Exit: normal/oblique held-outs and timestep convergence pass.

### P3 -- pitch, frame, and net laboratory

- FIFA-style pitch coupons.
- Frame impact rig and deformable net bakeoff.
- Continuous whole-ball goal detector.

Exit: surface/frame/net tests pass independently.

### P4 -- floating humanoid kick laboratory

- Audited robot asset and actuator model.
- No ball initially: balance, support traction, free swing, disturbances.
- Then low-speed instrumented contact and recovery.

Exit: hardware/identified-reference observables pass and no hidden support exists.
Current status: the floating-asset, live operational-response, two-way wrench,
rate, energy, recovery, no-anchor, no-clipping, and no-state-write numerical
gates pass. Hardware/identified-reference observables remain **OPEN**.

### P5 -- integrated 11 m shooting task

- Full causal contact-to-flight-to-goal episode.
- Reference trajectory optimisation and/or learning controller.
- Robustness across measured specimen/atmosphere/pitch distributions.

Exit: blind integrated trials pass; success videos are accompanied by traces.
Current status: two named numerical-prior command profiles pass the sparse goal,
recovery, causality, and physics-invariant gates under the same physical model.
A physics-neutral six-frame curl sequence matches the headless trace exactly.
Blind physical trials, calibrated parameter distributions, robustness, and
high-speed named-ball knuckle validation remain **OPEN**.

### P6 -- presentation and compatibility

- Interactive Isaac controls and teleoperation adapter.
- Best-attempt videos, motion frames, plots, tables, screenshots, PDF paper.
- Dashboard card, one-click launch, artifacts, and reproducibility commands.
- Regression tests matching repository environment conventions.

Exit: visual quality is high, but all presentation derives from the same
validated scene and logs.

## 19. Open measurements and decisions

Do not bury these behind implementation progress:

1. **Ball specimen:** choose an accessible current match ball and obtain seam
   geometry plus impact/aerodynamic measurements. Different World Cup balls are
   demonstrably not interchangeable.
2. **Pressure convention:** store gauge and absolute pressure, local atmospheric
   pressure, temperature, and equilibration procedure.
3. **Wind-tunnel access:** required for a strong seam/wake claim; published maps
   can bootstrap but not fully identify our specimen.
4. **High-speed impact instrumentation:** force plate >=10 kHz and high-speed
   cameras are needed to calibrate the 9 ms event.
5. **Pitch family:** natural or a named artificial-turf specimen for v1.
6. **Net specimen:** public dynamic material data are insufficient.
7. **Robot revision:** G1 versus G1 EDU and exact asset/actuator provenance.
8. **Runtime target:** interactive human viewing versus training throughput;
   both must report real-time factor and fidelity separately.
9. **Wake model order:** selected by held-out spectra/trajectory error, not by
   the most impressive wobble.
10. **Physical robot availability:** determines whether initial integrated
    validation is a surrogate kicking rig or actual G1.

## 20. Source catalogue

### Official laws and FIFA test programmes

1. IFAB, [Law 2: The Ball](https://www.theifab.com/laws/latest/the-ball/).
   Current circumference, mass, pressure, and certification requirements.
2. IFAB, [Law 1: The Field of
   Play](https://www.theifab.com/laws/latest/the-field-of-play/). Goal, penalty
   mark, post, and international-field dimensions.
3. IFAB, [Law 10: Determining the Outcome of a
   Match](https://www.theifab.com/laws/latest/determining-the-outcome-of-a-match/).
   Whole-ball goal rule.
4. FIFA, [Quality Programme for
   Footballs](https://football-technology.fifa.com/innovation/standards/footballs)
   and [2026 testing
   manual](https://digitalhub.fifa.com/m/5d88f22cfef8c799/original/FIFA-Quality-Programme-for-Football-Testing-Manual.pdf).
5. FIFA, [Natural Playing
   Surfaces](https://football-technology.fifa.com/innovation/standards/natural-playing-surfaces),
   [test
   manual](https://digitalhub.fifa.com/m/4901b0f4f30f534f/original/FIFA-Quality-Programme-for-natural-playing-surfaces-October-2021-Edition-V-1.pdf),
   and [natural pitch rating
   system](https://digitalhub.fifa.com/m/58aa765dd3e85f26/original/FIFA-natural-pitch-rating-system_EN.pdf).
6. FIFA, [Football
   Turf](https://football-technology.fifa.com/innovation/standards/football-turf)
   and [current test
   requirements](https://digitalhub.fifa.com/asset/f13cc722-c116-47c8-b5a9-2e65e469a301/FIFA-quality-programme-for-football-turf-Test-Manual-II-Test-requirements.pdf).
7. FIFA, [Football goal testing
   process](https://inside.fifa.com/innovation/standards/football-goals/football-goal-testing-process).

### Ball aerodynamics

8. Carré, Goodwill, and Haake (2005), [Understanding the effect of seams on the
   aerodynamics of an association football](https://doi.org/10.1243/095440605X31463).
   Drag crisis, seam transition, and Magnus regimes.
9. Hong et al. (2016), [Aerodynamic characteristics of a soccer ball in a
   rotating state](https://doi.org/10.1016/j.proeng.2016.06.189). Drag/side
   coefficient versus spin parameter and a measured slight negative-Magnus
   region.
10. Hong and Asai (2010), [Unsteady aerodynamic force on a knuckle ball in
    soccer](https://doi.org/10.5432/jjpehss.09053). Knuckle wake and unsteady
    force observations.
11. Goff et al. (2016), [Wind-tunnel experiments and trajectory analyses for
    five nonspinning soccer
    balls](https://doi.org/10.1016/j.proeng.2016.06.185). Orientation-dependent
    lateral/lift force and trajectory consequences.
12. Asai et al. (2007), [Fundamental aerodynamics of the soccer
    ball](https://doi.org/10.1007/BF02844207). Critical Reynolds-number
    measurements and flow visualisation.
13. Sakamoto et al. (2021), [Effect of soccer ball panels on aerodynamic
    characteristics and flow
    structures](https://doi.org/10.3390/app11010296). Groove geometry, flow
    separation, and drag crisis.
14. Passmore et al. (2012), [The aerodynamic performance of a range of FIFA-
    approved footballs](https://doi.org/10.1177/1754337111415768).
15. Goff and Carré (2009), [Trajectory analysis of a soccer
    ball](https://doi.org/10.1119/1.3197187).
16. James and Haake (2008), [The spin decay of sports balls in
    flight](https://doi.org/10.1007/978-2-287-09413-2_20). Spin decay and ball
    construction/inertia effects.
17. Bush (2013), [The aerodynamics of the beautiful
    game](https://thales.mit.edu/bush/wp-content/uploads/2013/11/Beautiful-Game-2013.pdf).
    Synthesis of drag crisis and changing Magnus regimes.

### Ball impact, deformation, and bounce

18. Shinkai et al. (2009), [Ball impact dynamics of instep kicking in
    soccer](https://pubmed.ncbi.nlm.nih.gov/19276844/). 5,000 Hz contact,
    deformation, force, and phase measurements.
19. Asai et al. (2002), [The curve kick of a football I: impact with the
    foot](https://doi.org/10.1046/j.1460-2687.2002.00108.x). Impact offset,
    deformation, speed, spin, and force.
20. Price, Jones, and Harland (2006), [Soccer ball anisotropy
    modelling](https://doi.org/10.1016/j.msea.2006.01.079).
    Layered shell/bladder FEM and orientation effects.
21. Price, Jones, and Harland (2007), [Advanced finite-element modelling of a
    32-panel soccer ball](https://doi.org/10.1243/09544062JMES711).
22. Rezaei et al. (2011), [Finite element modelling and experimental study of
    oblique soccer ball bounce](https://doi.org/10.1080/02640414.2011.587443).
    Oblique bounce, tangential force, and validation observables.
23. Cross (2016), [Effects of air pressure on the coefficient of restitution of
    a pressurised ball](https://doi.org/10.1139/cjp-2015-0378). Mechanistic
    pressure/COR relation.
24. Iga et al. (2013), [Basic mechanical analysis of soccer ball
    impact](https://ojs.ub.uni-konstanz.de/cpa/article/view/5637/5130). 10 kHz
    force-platform and 5,000 Hz imaging methodology.

### Atmosphere and humanoid

25. Picard et al., NIST, [CIPM-2007 equation for the density of moist
    air](https://www.nist.gov/system/files/documents/calibrations/CIPM-2007.pdf).
26. NASA, [U.S. Standard Atmosphere
    1976](https://ntrs.nasa.gov/citations/19930090991).
27. NASA Glenn, [Air density and viscosity
    relations](https://www.grc.nasa.gov/www/BGH/airprop.html).
28. Wang et al. (2024), [A biomechanics-inspired approach to soccer kicking for
    humanoid robots](https://arxiv.org/abs/2407.14612). Dynamic full-body phase
    structure, trajectory optimisation, and imitation learning.
29. Unitree, [G1 humanoid](https://www.unitree.com/g1/). Public geometry, mass,
    DoF, and actuator headline specifications; exact revision remains required.
30. Khatib (1987), [A unified approach for motion and force control of robot
    manipulators: the operational space
    formulation](https://doi.org/10.1109/JRA.1987.1087068). Operational-space
    inertia from generalized mass and task Jacobians.
31. Wang, Dehio, and Kheddar (2022), [On inverse inertia matrix and
    contact-force model for robotic manipulators at normal
    impacts](https://doi.org/10.1109/LRA.2022.3145967). Configuration-dependent
    inverse inertia, viscoelastic force histories, energy consistency, and the
    warning that high-stiffness impact response must be selected empirically.
32. Wensing et al. (2017), [Proprioceptive actuator design in the MIT Cheetah:
    impact mitigation and high-bandwidth physical interaction for dynamic
    legged robots](https://doi.org/10.1109/TRO.2016.2640183). Operational-space
    impact inertia and the material role of reflected rotor/transmission inertia.

### Installed engine

33. NVIDIA, [Isaac Sim 5.1 rigid prim API](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.core.prims/docs/index.html).
    Per-step force/torque and force-at-position interfaces.
34. NVIDIA, [Isaac Sim 5.1 simulation context
    API](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.core.api/docs/index.html).
    Physics callbacks and timestep control.
35. NVIDIA, [PhysX 107.3 rigid bodies and
    CCD](https://docs.omniverse.nvidia.com/kit/docs/omni_physics/107.3/dev_guide/rigid_bodies_articulations/rigid_bodies.html).
36. NVIDIA, [PhysX 107.3 deformable
    migration](https://docs.omniverse.nvidia.com/kit/docs/omni_physics/107.3/dev_guide/deformables_beta/deformable_migration.html).
    XPBD surface-deformable capabilities and missing cloth/inflatable parity.

## 21. Research conclusion

The apparently impossible part is not that the governing physics is unknown.
The difficult part is identification: a football's panel construction and wake,
a 9 ms nonlinear impact, the surface, and the robot must each be calibrated
without allowing one module to compensate for another.

The project becomes tractable by separating those systems, instrumenting every
exchange, validating coupons before integration, and retaining exact ball
orientation/wake history. The resulting runtime can still be interactive: a
reduced contact and aerodynamic model is legitimate when it reproduces the
high-fidelity/physical reference and applies real forces continuously. What we
must reject is any mechanism that chooses the desired shot and then manufactures
its trajectory.
