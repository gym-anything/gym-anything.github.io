# Verified findings and experiment ledger

This file is the compact engineering record for the football environment. It
separates what the current simulator has demonstrated from what is still only a
physics prior. Detailed equations and sources live in [RESEARCH.md](RESEARCH.md).

## Claim in one sentence

Two floating-G1 command profiles causally score regulation-scale 11 m goals in
Isaac Sim without assigning an outgoing ball state, and the exercised numerical
closure, passivity, convergence, recovery, and visible/headless gates pass; no
named physical ball, surface, net, or G1 has yet calibrated the result.

## Retained architecture

1. Isaac/PhysX owns the floating articulated G1, rigid ball pose, rigid goal
   frame, gravity, and outer 500 Hz timeline.
2. A deterministic convex proxy built from the pinned visible right-shoe STL
   provides exact closest-triangle foot contact.
3. The live G1 mass matrix and link Jacobian plus hollow-ball inverse inertia
   define the contact-point response. No scalar fake striking mass is used in
   production.
4. A 20 kHz passive pressure-shell/stick-slip contact subsolver returns
   equal-and-opposite ball and robot impulses.
5. A separate 20 kHz grass/soil contact model owns normal compliance, traction,
   rolling, and spin resistance; the native ball-pitch pair is filtered.
6. Wind-relative drag, buoyancy, Magnus, spin decay, seam orientation, and a
   coherent wake apply forces and moments continuously after separation.
7. A continuous whole-ball crossing detector owns task truth. The net never
   decides whether a goal was scored.
8. A physical sloped cable back net is available; the roof and side net are
   currently visual only.
9. Reduced render deformation consumes the same contact compression
   coordinates but never changes the physical sphere collider.

## Current integrated results

| Quantity | Curl | Low spin |
|---|---:|---:|
| Whole-ball goal time | 7.036194 s | 6.147041 s |
| Separation speed | 7.4487 m/s | 7.8729 m/s |
| Separation spin magnitude | 10.9304 rad/s | 1.3592 rad/s |
| Transverse spin parameter | 0.16114 | 0.01896 |
| Launch elevation | 9.174 deg | 9.075 deg |
| Launch azimuth | 2.774 deg | -3.288 deg |
| Lateral residual vs constant heading | +0.5005 m | -0.0455 m |
| Maximum drag force | 0.6317 N | 0.7035 N |
| Maximum Magnus force | 0.2631 N | 0.2310 N |
| Maximum coherent-wake force | 0.0000013 N | 0.009205 N |
| Minimum recovery upright cosine | 0.9852 | 0.9795 |
| Maximum base excursion | 0.3455 m | 0.4165 m |

Interpretation: curl is a demonstrated contact-generated spin-and-bend profile.
Low spin is a demonstrated contact-generated low-spin goal with deterministic
wake state, but its roughly 9 mN wake force at roughly 8 m/s is not a dramatic
or physically calibrated knuckleball.

## Contact and robot evidence

- Convex asset hash:
  `232A588BEF5C4364DAA573C77F6F78874F17438F7A6F2CBF2EFBD6D1B46E80FD`.
- Pinned visible STL hash:
  `4B66222EA56653E627711B56D0A8949B4920DA5DF091DA0CEB343F54E884E3A5`.
- Convex geometry: 1,248 vertices, 2,492 triangles, 0.00051396 m3.
- The retired oriented box contacted the canonical reference 9.251 mm early.
- Canonical integrated contact: 12.754 ms, 461.99 N peak, 21.760 mm maximum
  modal compression, 3.217 N s resultant impulse.
- Live directional foot mass during integrated contact: 0.654-0.703 kg;
  combined foot/ball reduced mass: 0.259-0.267 kg.
- Equal-and-opposite impulse error is exactly zero; maximum origin-moment
  closure error is 2.3e-13 N m.
- Midpoint contact work and constitutive dissipation are both 2.06888 J;
  residual stored contact energy is zero and the accounting residual is
  8.9e-16 J.
- The G1 has no world anchor, makes no non-foot pitch contact, clips no joint
  target, and is not reset after episode initialization.

## Numerical gates retained

The convex-shoe coupon was repeated with the same 500 Hz outer step and 10, 20,
and 40 kHz contact substeps. The 10-to-40 kHz deltas are:

| Observable | Relative delta | Gate |
|---|---:|---:|
| Forward separation speed | 0.0790% | 0.10% |
| Vertical separation speed | 0.7042% | 1.00% |
| Spin magnitude | 0.1029% | 0.25% |
| Peak force | 0.0266% | 0.25% |
| Compression | 0.1634% | 0.25% |
| Normal impulse | 0.0790% | 0.10% |

All pass. This establishes rate convergence for this trajectory and prior only.

The visible curl run performs 524 render-only updates, advances the physics
clock by exactly 0.0 s during those updates, and matches all 500 sampled states
in the headless trace exactly.

## Verified viewport videos

Fresh simulation-time viewport captures were retained for both named profiles.
They are direct renderer outputs, not telemetry animations:

| Profile | Source frames | H.264 frames | Clip | Render-only updates | Goal |
|---|---:|---:|---:|---:|---:|
| Curl | 170 | 200 | 6.667 s | 1,095 | 7.036 s |
| Low-spin | 136 | 166 | 5.533 s | 890 | 6.147 s |

Both use 20 simulation-time fps, 30 fps delivery, 1.5x playback, and a declared
one-second terminal hold. The curl capture covers 1.50-9.95 s. Low-spin
naturally reaches `settled_after_goal` at 8.274 s, so its last physical source
frame is 8.25 s; no post-termination frames were fabricated.

The video gate fully decodes both files and requires exact equality—not a
tolerance—between each visible capture trace and its fresh headless canonical
trace for sampled state, foot/pitch/net contact streams, goal event, separation
state, reaction ledgers, and recovery. Both maximum render-clock advances are
0.0 s and both runs record zero outgoing ball-state assignments.

Two preliminary low-spin captures reached the same natural termination with an
older plan that incorrectly expected frames through 9.95 s. They produced no
accepted trace or video. The retained generic rule now truncates only capture
requests strictly after a non-time-limit natural termination; any missing frame
before the terminal boundary remains a hard failure.

## Rejected or superseded branches

### Scripted launch

Rejected for the task. Initial-state launchers remain only in isolated P1
flight coupons. The integrated environment records zero outgoing ball state
assignments.

### Kinematic foot or anchored robot

Rejected. It would remove the load path and make arbitrary impulse possible.
Production uses the floating articulation and applies the reaction impulse.

### Scalar 2 kg foot mass

Superseded after the live operational-response audit measured a substantially
smaller, posture-dependent directional response. Production uses the full 3-D
point inverse-mass tensor.

### Oriented-box shoe contact

Superseded. It was transparent and fast but geometrically biased and contacted
the canonical ball 9.251 mm too early. It remains only as a falsification coupon.

### First convex-shoe trajectory

Failed to score. Replacing the contact geometry and live inertia did not
preserve the old task result automatically; several early trajectories stopped
before the line or destabilized recovery. This is positive evidence that goal
success is not hard-coded.

### Aggressive follow-through without braking/recovery

Rejected. It could kick harder but produced unacceptable base motion or poor
recovery. The retained profiles use explicit leg braking, arm counter-swing,
and post-kick balance commands.

### Random lateral knuckle force

Rejected. Production maintains a deterministic, temporally coherent wake state
conditioned on relative flow, spin, and orientation. Random per-step wobble
would be visually convenient and physically incoherent.

### Net-contact success condition

Rejected. IFAB task truth is whole-ball passage across the goal plane. A valid
slow ground shot may stop before the back net.

### Deforming the collision sphere

Rejected for this reduced model. The visible shell responds to measured contact
compression while the physical collider remains unchanged. A calibrated shell
FE model is the future reference for true geometry-changing contact.

## What would falsify the current implementation

- changing render rate changes any sampled physics state;
- reversing measured spin fails to reverse lateral response in a calibrated
  Magnus regime;
- removing aerodynamic forces leaves the same curved trajectory;
- deleting the robot reaction impulse does not trip momentum closure;
- changing contact microstep rate materially changes impulse or outgoing state;
- a named-ball impact trial lies outside declared uncertainty in duration,
  force, deformation, speed, or spin;
- the same low-spin trajectory appears after changing ball orientation when a
  calibrated seam model predicts otherwise;
- a score is reported when any part of the ball has not crossed the line or the
  centre is outside the legal opening clearance;
- a blind physical G1 trial requires actuator behavior absent from the asset,
  such as unmodeled reflected inertia or torque-speed capability.

## Open calibration work

The strongest missing evidence is physical, not another prettier successful
run: one named ball and inflation protocol; high-rate normal and oblique impact
data; wind-tunnel/free-flight coefficient and wake maps; a named pitch and net;
and exact G1 actuator/impact identification. Until those are held out and
passed, every integrated result remains `PRIOR-ONLY / NOT PHYSICALLY CALIBRATED`.
