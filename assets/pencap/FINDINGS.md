# Pencap findings (probe series P0/P1a-j) -- all measured, logs in pencap/

## MILESTONE (P1j): full snap-fit cycle achieved with honest physics
Force-controlled insertion (hand-mass model, no drives):
- ramp climb with rising interference (ovl +0.111 mm under 6.25 N)
- **SNAP at 7.3 N** past the crest, velocity spike to ~190 mm/s (hand-tamed;
  free-cap variant hit 1.1 m/s = unphysical)
- **CLICK = shoulder impact** at 189 mm/s; cap seats at rim 47.50 mm = the
  shoulder top EXACTLY; stays seated under 18.75 N of continued push
- retention: cap holds position at zero force (dwell)
- **PULL-OFF at 6.8 N** -- separates and flies (run-end detector mislabeled the
  free flight as explosion; benign)

## Engine laws measured (unit-tested, P0)
- `physxMaterial:compliantContactStiffness` = PER-CONTACT-POINT Hookean spring,
  exact to ~1% (sphere: mg/k; 4-corner box: mg/4k) on ALL pairings tested
  (sphere/SDF/convex vs trimesh/convex). The hoop stiffness of a snap-fit lives
  here legitimately -- with per-point normalization accounted.
- Contact REPORTS are BLIND for compliant contacts (zero events even under
  50 N of contact force). Use applied-force or drive-side witnesses.
- PhysX drops contacts beyond 32 friction patches per pair: a continuous
  annular ridge (~100 patches) JAMS UNRESOLVABLY. Discrete nubs (real caps use
  3-6 anyway) keep the pair at 4 patches. Ring design kept behind NUBS=0.
- VELOCITY drives (damping-only prismatic) DEADLOCK at the first speculative
  contact of the interference (frozen position + impossible constant velocity
  readback + zero contact events). Pure applied force passes the same
  geometry. Suspected TGS + joint-drive + speculative-contact interaction;
  workaround = force control (which is also the handbook measurement protocol).
- contactOffset is a PHYSICAL parameter at pen scale: it must sit below every
  running clearance (0.04 mm here) or the compliant band creates phantom
  cushions. Every clearance in the design must exceed it.
- Mesh WINDING: revolve profiles must run counter-clockwise in (r,y); an
  inside-out solid flips SDF inside/outside and builds phantom walls. The
  builder now enforces positive signed volume (auto-flip).
- CCD required: post-snap velocities tunnel through mm-scale features at 1 kHz.
- The HAND matters: real click dynamics = cap + ~0.3 kg hand momentum at low
  velocity. Free 5 g caps produce 1000 m/s^2 cartoon snaps.
- Compliant contacts transmit FLAT-surface friction exactly (p0f: box slips at
  0.53 N vs mu*m*g = 0.49 N, rigid/2%/30% damping all alike) BUT lose almost
  all TANGENTIAL friction in LINE contact (p0g: cylinder in compliant jaws
  escapes axially at 0.43 N -- 0.74 N even at 3x squeeze -- vs HELD >= 3 N by
  rigid jaws with the identical 8 N drive). Consistent with the compliant
  special-casing behind the blind-reports law. Consequence: gripper pads that
  must transmit axial force through a cylindrical grip MUST be rigid-contact.
- Convex decomposition BLOATS small revolve solids: the pen barrel read ~10.6 mm
  across (real 9.8) with slanted phantom hull faces bridging the center ring --
  fingers "gripped" the phantom and never touched the pen (wiggle test: zero
  response). Dynamic mm-scale task geometry needs SDF collision, not decomp.
- ARTICULATION SHAPE-FREEZE (drop-test-proven 7 ways, r2f): NO collider added
  at runtime to a loaded articulation becomes physically active -- not child
  prims of links (matrix-op OR plain-TRS xforms), not children of the parsed
  de-instanced geometry scope, not separate bodies jointed to a link by
  fixed/D6/prismatic joints (joints hold, shapes ghost; FixedJoints also merge
  the body into the link). The same prims parse fine as plain world bodies,
  and USD-level audits CANNOT catch this (APIs all present) -- only a physical
  probe (ball drop) can. Consequence: custom gripper fittings are impossible
  post-load; put task form-closure geometry on the OBJECTS (child shapes on
  plain rigid bodies parse -- the cap's nubs prove it) or edit the robot asset.
- Weeks-of-runs corollary, grasping 5-6 g objects: RIGID jaw squeezes store
  finger-splay strain (mJ) that launches the object on any micro-slip (force
  steps, ramps, and lifts all triggered it); COMPLIANT lossy pads absorb it --
  every clean capture+lift+hold in the series came from compliant pads at 8 N.
  Their missing axial line-contact friction must be replaced by form closure.

## Geometry (current, parametric)
Shaft r 5.0, bead crest 5.25 (lead 22 deg, return 45 deg, flat 0.3), nub
tangent 5.10 (interference 0.15), bore 5.40, 4 nubs r 0.45 at 1.5 mm above rim,
shoulder at snap+0.4 mm. K=3e4/nub, mu 0.25, dt 1/1000, SDF 768 (cap), barrel
exact trimesh.

## OPEN (calibration + fidelity)
1. **On/off asymmetry missing**: measured 6.8 N off vs 7.3 N on (predicted
   ~2.3x harder off from 45/22 deg ramps). Hypothesis: the 0.45 mm nub SPHERE
   curvature rounds off the short ramps (return run is only 0.25 mm) -- the
   effective contact angle is sphere-dominated. Fix candidates: smaller nub
   (0.25), longer/flatter ramps, or torus-segment nubs. MEASURE per-nub forces.
2. Force scale ~2x low vs hand calc (7.3 vs ~13 N at 4 engaged nubs): check
   engaged-nub count during climb (alignment/tolerance), calibrate K.
3. Plot x-window (post-flight dominates); end run at pull-off.
4. Analytic F(x) overlay on the measured curve (the validation gate).
5. Then: verifier (snap signature + pull test), tabletop free-pose scene,
   petal-lip architecture B for visible flex.
