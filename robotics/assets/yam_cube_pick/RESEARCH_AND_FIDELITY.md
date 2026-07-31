# YAM cube-pick research and fidelity contract

## Claim boundary

This environment demonstrates a contact-only rigid-body pickup in Isaac Sim.
It does **not** yet claim agreement with a named physical YAM installation.

The evidence is divided into four classes:

1. **Requested or source-exact.** The 50 mm cube edge, 200 mm square spawn
   region, station dimensions, arm mount poses, source meshes, source inertial
   properties, joint limits, and drive limits are either requested directly or
   read from the vendored YAM station asset.
2. **Runtime-audited simulation settings.** Gravity, mass, inertia, material
   coefficients, solver, friction model, CCD, contact offsets, iteration
   counts, GPU dynamics, and collision/material bindings are authored and read
   back from USD in every episode.
3. **Engineering priors.** Cube density, friction, restitution, and the
   unmeasured source robot/contact model are plausible initial values, not
   measurements of a named specimen.
4. **Simulation outcomes.** Lift, trajectory, speed, normal contact impulse,
   success, sensitivity, convergence, and repeatability are Isaac results.
   They are not physical validation data.

The title of every report and dashboard artifact must retain the label
**PRIOR-ONLY / NOT PHYSICALLY CALIBRATED** until the calibration protocol in
`calibration/` has been completed on frozen calibration and held-out splits.

## Physical model

For cube edge \(a\) and density \(\rho\),

\[
m=\rho a^3,\qquad
I_{xx}=I_{yy}=I_{zz}=\frac{ma^2}{6}.
\]

The reference values are \(a=0.05\ {\rm m}\),
\(\rho=1050\ {\rm kg\,m^{-3}}\), \(m=0.13125\ {\rm kg}\), and
\(I=5.46875\times10^{-5}\ {\rm kg\,m^2}\).

The free rigid body follows

\[
m\dot{\mathbf v}=m\mathbf g+\sum_i\mathbf f_i,\qquad
\mathbf I\dot{\boldsymbol\omega}+
\boldsymbol\omega\times(\mathbf I\boldsymbol\omega)
=\sum_i(\mathbf r_i-\mathbf x)\times\mathbf f_i .
\]

At a unilateral contact, the normal gap and normal impulse obey the
non-penetration/complementarity idealization

\[
g_n\ge0,\quad \lambda_n\ge0,\quad g_n\lambda_n=0,
\]

while Coulomb friction bounds the tangent impulse by

\[
\|\boldsymbol\lambda_t\|\le\mu\lambda_n.
\]

Isaac uses a finite-step rigid-contact solve rather than an exact continuous
solution. The canonical run uses TGS, patch friction, a 1/240 s physics step,
32 cube position iterations, four velocity iterations, CCD, and four physics
steps per 60 Hz control interval.

For two ideal opposed contacts with equal normal load \(N\), a conservative
gravity-support capacity condition is

\[
2\mu_d N\ge mg,\qquad
N_{\min}=\frac{mg}{2\mu_d}.
\]

With the reference dynamic coefficient \(\mu_d=0.75\),
\(N_{\min}=0.8581\ {\rm N}\) per finger. This is only a vertical
task-direction capacity bound. Two ideal point contacts do not establish full
six-dimensional force closure. The imported fingers create finite contact
patches, but torsional patch-friction impulse is not exposed by Isaac's
standard contact callback and is not claimed as a measurement.

The callback reports solved normal impulse vectors. Normal force is estimated
per physics step as

\[
F_{n,i}=\frac{1}{\Delta t}
\sum_{p\in i}|\mathbf J_p\cdot\hat{\mathbf n}_p|.
\]

The off-normal residual of every reported impulse vector is retained as an API
semantics audit. Internal patch-friction impulse is explicitly marked
unavailable.

## Robot and control model

The physical scene contains both six-axis YAM arms and both two-slide
grippers. The right arm remains dynamically present. The reference policy
sends exactly zero on all seven right-arm action channels, and success rejects
any right-arm/cube contact.

The public action is a 14-vector:

\[
[\mathbf v_L,\boldsymbol\omega_L,\dot w_L,
 \mathbf v_R,\boldsymbol\omega_R,\dot w_R].
\]

Each normalized channel is converted to a bounded Cartesian rate or aperture
rate. The operational-space controller maps Cartesian pose error through the
measured articulation Jacobian and commands the source force-limited joint
drives. The cube receives one pose write at reset and none afterward. No joint,
attachment, attractor, hidden force, or scripted cube transform participates
in a successful pickup.

The source MJCF applies gravity compensation to 22 named arm bodies. The
adapter preserves that set. Four massless TCP/camera coordinate-frame bodies
are folded into their physical parents for Isaac 5.1 compatibility without
changing initial world transforms.

## Task and reward

Success requires, continuously for 0.20 s:

- both left fingers in normal-force-bearing cube contact;
- at least 50 mm cube-center lift;
- no cube/table or moving-left-arm/table contact;
- no right-arm/cube contact;
- cube speed no greater than 0.15 m/s;
- one reset pose write and zero attachments.

A control-step cube displacement above 35 mm is a hard failure. The episode
limit is 15 s.

The dense potential is

\[
\Phi=0.35e^{-d/0.10}
+0.30\frac{c_A+c_B}{2}
+0.35\,{\rm clip}\left(\frac{h}{h_*},0,1\right),
\]

and the step reward is \(\Phi_{t+1}-\Phi_t\), plus 10 on success or minus 10
on integrity/contact failure. Reward never moves the robot or cube.

## Numerical evidence contract

Every numerical comparison must use the same seed, sampled initial state,
controller, 60 Hz control boundary, GPU, source hash, and success definition.
The comparison record lists every changed spec field. Conclusions are rejected
if another changed field, different starting state, different simulated time,
or different execution source could explain the observation.

The frozen campaign includes:

- three independent-process repeats of the canonical cell;
- 120, 240, and 480 Hz temporal cells;
- 16, 32, and 64 position-iteration cells;
- two, four, and eight velocity-iteration cells;
- contact-offset, density, friction, restitution, solver, and CCD sensitivity;
- zero-friction and high-mass physical falsification cells; and
- a 200 mm lift-threshold verifier falsification cell.

The campaign reports raw outcomes and deltas. It does not reinterpret a failed
probe as an architectural limit.

## Physical calibration and validation

The machine-readable protocol is in `calibration/schema.json`; synchronized
columns are in `calibration/measurement_template.csv`. Required experiments
cover cube metrology, surveyed station geometry, tilt and sled friction,
restitution, gripper normal force, aperture, pose tracking, joint tracking,
and a pre-registered held-out task panel.

No value from a renderer, simulator, or hand-tuned successful episode may be
entered as physical calibration data.

## Primary and official sources

| Topic | Source | Use here |
| --- | --- | --- |
| YAM hardware/model | [I2RT YAM documentation](https://doc.i2rt.com/products/yam) | Robot architecture, control modes, official model availability |
| Bimanual station | [I2RT YAM Cell documentation](https://doc.i2rt.com/products/yam-cell) | Two-arm tabletop arrangement |
| YAM policy stack | [Raiden documentation](https://tri-ml.github.io/raiden/) | Reproducible YAM scene initialization and IK context |
| Isaac articulation control | [Isaac Sim 5.1 articulation controller](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_simulation/articulation_controller.html) | Joint control semantics |
| Physics stepping | [Isaac Sim simulation fundamentals](https://docs.isaacsim.omniverse.nvidia.com/latest/physics/simulation_fundamentals.html) | Physics/render timestep separation |
| TGS and friction patches | [PhysX simulation documentation](https://nvidia-omniverse.github.io/PhysX/physx/5.8.0/docs/Simulation.html) | Solver and iteration semantics |
| Contact/rest offsets and CCD | [PhysX 5.1 advanced collision detection](https://nvidia-omniverse.github.io/PhysX/physx/5.1.2/docs/AdvancedCollisionDetection.html) | Collision generation and tunneling controls |
| Patch friction enum | [PhysX friction type API](https://nvidia-omniverse.github.io/PhysX/physx/5.4.0/_api_build/struct_px_friction_type.html) | Friction model identity |
| Contact callback | [Omniverse contact reports](https://docs.omniverse.nvidia.com/kit/docs/omni_physics/latest/extensions/runtime/source/omni.physx/docs/dev_guide/contact_reports.html) | Positions, normals, separations, normal impulses |
| PhysX source | [NVIDIA Omniverse PhysX](https://github.com/NVIDIA-Omniverse/PhysX) | Engine provenance |
| Force closure | [Modern Robotics, force closure](https://modernrobotics.northwestern.edu/nu-gm-book-resource/12-2-3-force-closure/) | Wrench-cone definition and limits of point contacts |
| Grasp closure | [Bicchi 1995, DOI 10.1177/027836499501400402](https://doi.org/10.1177/027836499501400402) | Force/form closure theory |
| Grasp quality | [Ferrari and Canny 1992, DOI 10.1109/ROBOT.1992.219918](https://doi.org/10.1109/ROBOT.1992.219918) | Disturbance-based grasp quality |
| Rigid-contact time stepping | [Stewart and Trinkle 1996](https://doi.org/10.1002/(SICI)1097-0207(19960815)39:15%3C2673::AID-NME972%3E3.0.CO;2-I) | Nonsmooth time-stepping foundation |
| Complementarity contact | [Anitescu and Potra 1997](https://doi.org/10.1023/A:1008292328909) | Rigid-body contact formulation |
| Robotic hand testing | [NIST SP 1227](https://www.nist.gov/publications/performance-metrics-and-test-methods-robotic-hands-draft) | Replicable hand metrics |
| Grasp benchmarking | [NIST grasping performance](https://www.nist.gov/publications/grasping-performance-facilitating-replicable-performance-measures-benchmarking-and) | Benchmark design |
| Robot performance | [ISO 9283](https://www.iso.org/standard/22244.html) | Accuracy and repeatability framework |
| Robot metrology | [ISO/TR 13309](https://www.iso.org/standard/21679.html) | Measurement guidance |
| Plastic density | [ASTM D792](https://store.astm.org/d0792-20.html) | Density-method reference |
| Friction testing | [ASTM D1894 research report](https://store.astm.org/rr-d20-1131.html) | Static/kinetic friction terminology |

