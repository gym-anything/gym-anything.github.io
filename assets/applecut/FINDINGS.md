# AppleCut implementation findings

Status: P0 oracle plus dynamic whole-apple/Franka integration, 11 July 2026.
This is numerical verification with published starting priors. It is **not**
physical calibration. The embodied environment exists, but its current
prescribed fracture plane and aligned-blade coupling remain explicit limits.

## What now physically exists

- A structured two-half triangular FEM coupon with duplicate crack-face nodes.
- Standard two-point Gauss integration on zero-thickness cohesive line elements.
- A bilinear irreversible traction-separation law in which peak traction fixes
  initiation and the integrated envelope independently equals the prescribed
  fracture energy.
- Unilateral compression across the interface after tensile damage.
- An analytic circular-apex knife joined tangentially to its measured-angle
  wedge faces. The default 5 micrometre radius is never inflated to one cell.
- Penalty contact integrated along both crack faces, equal-and-opposite knife
  reaction, and optional maximum-dissipation regularized Coulomb blade friction.
- Explicit knife work, bulk/cohesive/contact storage, fracture dissipation,
  friction dissipation, and unexplained residual channels.
- A live Isaac viewer in which each carriage increment runs this solver and USD
  only visualizes the returned continuum state.

The current continuum is deliberately small-strain, homogeneous, two-
dimensional, quasi-static, and restricted to one prescribed straight crack
path. Those are reference-method boundaries, not hidden claims about an apple.

## Unit verification

`python -m unittest applecut.test_p0_model -v` passes 14 tests:

- cohesive peak strength and numerical envelope integral;
- complete-separation dissipation equals `G_c`;
- damage boundedness, monotonicity, and compression exclusion;
- rounded-apex/face positional continuity, distance signs, unit normals, and
  radius sensitivity;
- coincident-but-distinct crack nodes and interface-area accounting;
- stiffness symmetry and zero rigid-translation energy;
- exact affine triangular FEM strain;
- analytic two-branch Maxwell relaxation endpoints;
- zero-contact initial state;
- equal-and-opposite knife reaction;
- finite irreversible damage evolution; and
- frictional passivity plus increased push force.

## Why the cohesive integration changed

The first implementation placed cohesive/contact quadrature at interface
vertices. Its work could appear stable while the force changed abruptly as the
blade crossed each node. That was a discretization artifact. It was replaced by
zero-thickness line elements with two Gauss points, without changing material
parameters or acceptance gates.

At 2 mm knife travel with 1.0, 0.75, and 0.5 mm target cells:

| Increment | Peak-force change, two finest | Full-curve L1 change | Work change | Fracture-energy change | Finest energy residual | Verdict |
|---:|---:|---:|---:|---:|---:|---|
| 0.125 mm | 0.987% | 5.131% | 2.306% | 1.249% | 0.0175% | **FAIL**: curve gate is 5% |
| 0.0625 mm | 0.979% | 4.900% | 2.475% | 1.244% | 0.0444% | **PASS** for this partial-depth numerical gate |

The crack-front difference in the passing finest pair is about 0.00135 of the
coarser cell. All optimizer and damage-stagger solves converged. The failed run
is retained rather than overwritten.

This partial-depth pass demonstrates that temporal refinement materially
matters and that the predeclared gate can reject a visually plausible curve.

## Current full-depth reference trace

The 1.0 mm target-cell, 0.125 mm increment, frictionless 8 mm trace reports:

- peak upward knife reaction: 1.46560 N;
- imposed knife work: 8.97152 mJ;
- fracture dissipation: 6.62894 mJ;
- final relative energy residual: 0.02684%;
- fully separated interface area: 15.0 mm2;
- zero failed optimizer steps; and
- zero unconverged damage-stagger steps.

These are simulator outputs from prior material values, not measurements of a
real apple.

The complete 8 mm spatial matrix at a fixed 0.125 mm increment also passes. For
the two finest 0.75/0.5 mm profiles it gives:

- peak-force change: 0.267%;
- full-curve L1 change: 1.396%;
- knife-work change: 0.327%;
- fracture-energy change: 0.103%;
- crack-front difference: 0.178 coarse cells; and
- finest relative energy residual: 0.0134%.

At the finest 0.5 mm mesh, halving the full-depth travel increment from 0.125
to 0.0625 mm changes peak force by 0.0011%, the full curve by 0.150%, work by
0.0085%, fracture energy by 0.000052%, and crack-front position by zero. The
finer run's relative energy residual is 0.0049%. All predeclared full-depth
spatial and temporal checks pass, with no failed equilibrium or damage solve.

## Rounded-edge isolation matrix

The no-fracture matrix disables damage completely and varies only analytic edge
geometry. At 0.5 mm imposed travel and a 20 degree included angle, reaction is
0.34433, 0.36130, and 0.37833 N for 1, 3, and 5 micrometre radii. A linear fit
has a slope of 0.008502 N/micrometre and `R2 = 0.9999986`. At a fixed 5
micrometre radius, 15, 20, and 30 degree wedges produce 0.25077, 0.37833, and
0.60400 N.

The predeclared monotonicity, radius-linearity, no-damage, energy-residual, and
solver gates all pass; the largest relative energy residual is 0.908%. This
shows that the sub-grid edge radius and wedge angle causally affect the model.
It does **not** validate the magnitudes or slopes against real blade/apple data.

The first matrix attempt exposed an audit bug: with fracture disabled, damage
remained exactly zero but the report still evaluated dissipated energy from
maximum opening. That produced 7.1 microjoules of nonexistent fracture work.
The fracture channel is now identically zero when the law is disabled, and a
regression test enforces it.

## Isaac viewer evidence

`p0_gui.py` passed a finite headless runtime test and a separate RGB capture.
At its captured 2 mm state it reported 0.9166 N reaction, maximum damage
0.96905, and a roughly -0.00003 mJ energy residual. The captured mesh came from
the live solver state. There is no PhysX apple collider, split-mesh swap, pose
write, or visibility-triggered fracture.

The first capture attempt exposed an Isaac 5.1 Replicator API issue: passing a
list containing a `HydraTexture` to `Annotator.detach` did not normalize it to a
render-product path and crashed synthetic-data shutdown. Passing the scalar
render product fixes the issue; both the runtime-only and capture paths now exit
without traceback or fatal shutdown.

## Dynamic 3-D solver bakeoff and selection

The accepted dynamic method is a CUDA total-Lagrangian tetrahedral FEM with
compressible neo-Hookean bulk response. The central plane has duplicated nodes
and zero-thickness triangular cohesive elements. Complete damage therefore
creates an actual displacement/velocity discontinuity; it is not a texture,
visibility event, or softened still-connected mesh.

The selected coupon passed all 14 oracle checks. Against the 1 mm P0 reference,
the retained run has 3.306% full-curve force error, 2.811% peak error, 0.261%
work error, 0.0835% fracture-work error, 2.397% opening error, one-layer
separated-area agreement, 0.0154% final energy residual, minimum `J=0.910`,
and no escaped nodes. The accepted 5 microsecond profile also passes a 2.5/5
microsecond comparison. Ten microseconds inverts the coupon and is retained as
failure.

The approximately 0.75 mm spatial refinement passes the declared force, peak,
work, fracture, opening, energy, Jacobian, and escape gates. A first 3.125
microsecond refined run failed only the 0.5% energy gate and is separately
retained; reducing it to 2.5 microseconds gives a 0.0060% residual.

Two MPM branches were not promoted. A single-field MLS-MPM baseline is stable
and fast enough for comparison but has no displacement discontinuity. Several
two-field/cohesive experiments either injected energy, inverted, under-damaged
through a fixed-interface approximation, or became prohibitively slow. Newton
1.3 implicit MPM was reproduced in an isolated environment and ran a roughly
42,000-particle 10 ms coupon at 8.59 frames/s, but its tested model had no
fracture/discontinuity. Those failures remain evidence rather than being hidden
behind a polished render.

## Whole-apple timestep and knife geometry

The whole cage has 6,004 nodes, 27,480 tetrahedra, 620 cohesive triangles, and
0.2210 kg represented mass. It is clipped to the same five-lobe profile used by
the render surface. No apple nodes are fixed. A unilateral rigid-board plane
uses compliant penalty/dashpot contact and regularized friction; four flared,
unilateral compliant cradle faces provide lateral support without pinning the
crack plane. The cradle rises from a 30 mm half-width at 8 mm to 41 mm at 20 mm
and its sloped normals supply the corresponding upward component.

The analytic tool is finite along its 222 mm edge. Its curved tip profile,
46 mm heel blade height, 5 micrometre rounded apex, 20 degree included
micro-bevel, 1 mm bevel height, and 1.9 mm spine thickness match the authored
professional chef knife rather than an infinite wedge.

With that final edge, a 0.30 s deep-contact temporal gate gives only 0.0083%
damage difference, 0.063% opening difference, 0.063% work difference, and
0.101% damage-area difference between 5 and 10 microseconds. Geometry alone
would make them appear equivalent. Energy residual, however, is 0.0456% at 5
microseconds and 1.373% at 10 microseconds. The declared 0.5% gate therefore
promotes only 5 microseconds.

The depth-resolved full-cut audit is deliberately stricter than that earlier
deep-contact gate. It requires at least 99% separated interface area, at least
95% in every vertical band, a blade endpoint 0.30 mm above the board, no fixed
interface nodes, `J>0.20`, no escapes, and a true per-microstep node-speed peak
below 10 m/s. Current 5, 2.5, and 1.25 microsecond runs all reach 100% of the
interface and 100% of all 19 bands without inversion or escape. Corrected
energy residuals are 1.326%, 0.718%, and 0.903%; therefore topology and dynamic
stability pass, but none is promoted through the declared 0.5% whole-cut energy
gate. The non-monotone 1.25 microsecond result rejects a simplistic
"smaller timestep is sufficient" conclusion.

The original combined float32 atomic knife-work counter lost small contact
increments when interleaved with larger directional-cutting increments. The
physical kernels were not changed: diagnostics now sum independent directional
and compliant work channels in host float64 and retain the shared raw counter
and its precision loss. This reduced the reported 5 microsecond residual from
2.211% to 1.326%, but did not manufacture a pass.

## Physics-owned rendering

The apple skin is split into topologically independent left/right render
surfaces. Each surface point is embedded into same-side FEM nodes and receives
only interpolated solver displacement. Exposed flesh is generated only for
cohesive triangles whose irreversible damage exceeds the visible threshold.
Core, seed, and sub-millimetre peel classifications choose render materials but
do not alter mechanics. At rest, the bridge exposes exactly zero cut faces.

The first close camera was rejected: its 70 mm lens cropped inside the 82 mm
fruit and made a sound top surface read like a torn sheet. The retained edge
camera is wider and oblique. This was a camera failure, not a reason to alter
FEM displacement or exaggerate the crack opening.

## Continuous two-way Franka coupling

`apple_gui.py` has no solve key. Keyboard input changes only a Franka Cartesian
target. A 260 g rigid knife and approximately 160 g purpose-built holder form
one 420 g payload. The visible jaws, elastomer liners, clamp bridge, adapter,
flange, and bolts explain the load path to the wrist. Knife/holder geometry,
mass, inertia, and colliders are authored beneath `panda_hand` before physics
initialization so PhysX folds them into the reduced-coordinate articulation.
This removes the redundant maximal-coordinate fixed constraint that fought the
already-stiff Franka drives. The earlier invisible weak joint, stock finger
friction grasps, and external finite holder body were rejected: they hid the
attachment, slipped/expelled the knife, or introduced a second stiff constraint
and visible limit cycling. At each 8.335 ms partition boundary:

1. measured rigid-knife position and linear velocity are supplied to 1,667
   consecutive 5 microsecond FEM steps (angular velocity is zero until the FEM
   blade SDF supports time-varying rotation);
2. FEM contact accumulates the equal-and-opposite linear and angular impulse;
3. the mean wrench is applied to `panda_hand` at the knife edge origin; and
4. PhysX advances the merged tool and Franka under that load.

An anisotropic outer measured-edge loop (12/s blade-normal, 6/s lateral, 3/s
feed) acts through RMPflow/joint drives and never writes the knife pose. The
merged payload settles within 0.313 mm. A 240-frame no-contact audit measures
0.0388 mm peak-to-peak motion and 5.237 mm/s maximum instantaneous speed.

The retained full embodied proof commands the same 15 mm/s unloaded reference
as the GUI and terminates at the physical task endpoint after 678 frames. The
edge reaches 0.247 mm above the board, 100% of the cohesive area and every one
of 19 vertical bands is separated, and no ligament remains. Peak reaction is
26.684 N; final and worst ramp tracking errors are 0.237 and 5.873 mm; lateral
tool excursion is 0.274 mm; angular excursion is 0.269 degrees; terminal
`J=0.99114`; zero nodes escape; terminal and historical peak node speeds are
0.345 and 4.788 m/s. Apple centre-of-mass drift is 0.237 mm blade-normal. This
is a passing coupled-execution/topology proof. Its 5.833% energy residual keeps
the separate `physics_acceptance_pass` false.

The first live keyboard implementation was rejected despite passing the
autonomous probe. It added 1 mm on every OS key-repeat event; because a coupled
frame is much slower than wall-clock key repeat, holding `N` queued a large
target discontinuity, produced 1.116 m/s node speed, and correctly triggered
an upward safety retract. The retained controller stores only press/release
state and integrates a 15 mm/s target once per physics frame. A 0.15 mm
payload-correction deadband prevents the outer loop from integrating tiny idle
errors. `15 mm/s` is an unloaded Cartesian trajectory reference: Franka drive
torques track it and FEM force is emergent. A soft limiter holds full speed
below 22 N and reaches zero reference speed at 40 N. It is not a pose write or
a fracture clock.

Interactive travel now reaches the whole apple and stops at a 0.30 mm target
clearance above the board. Complete separation at that endpoint is an explicit
terminal event; the held-down command is cleared and the robot retracts instead
of dwelling against the board indefinitely. Non-finite state, escaped nodes,
`J<0.90`, node speed above 10 m/s (or above 2.5 m/s for three coupling frames),
force above 40 N, or torque above 2 N m causes a zero-wrench safety retract.
The invalid FEM state is frozen during that retract and reset only when the
robot is unloaded, preventing a failed numerical state from continuing to
inject motion or crashing reset.

Both reset paths are now sequenced. `R` retracts until the tool is unloaded
before resetting the FEM. A toolbar Stop/Reset rebuilds tensor handles,
reinitializes the merged hand/tool articulation, aligns the robot, and resets
RMPflow and FEM state without recommissioning an external constraint.

An 8/s outer-servo experiment reduced final lag to 1.74 mm but excited the
partitioned contact and raised energy residual to 40.3%. It is retained as
`gpu_fem_robot_coupling_probe_servo8_FAIL.json`; the slower 3/s controller is
the accepted profile.

## Still open

1. Measure a specific apple cultivar and knife with the calibration contract;
   all present material and anatomy values remain priors.
2. Add viscoelastic/poroelastic rate dependence to the dynamic solver and
   validate relaxation, not only the P0 analytic Maxwell curve.
3. Resolve peel, core/carpel, seed cavities, anisotropy, and heterogeneous
   fracture mechanically rather than only in rendering.
4. Replace the prescribed centre plane with a topology-general, energy-audited
   free crack method.
5. Add crack-face self-contact and reversal verification.
6. Converge and calibrate the board/cradle contact and close the remaining
   whole-cut and partitioned-coupling energy residuals.
7. Generalize the robot coupling from an aligned blade to arbitrary 6-DoF tool
   rotation and validate partition stability under torque.
