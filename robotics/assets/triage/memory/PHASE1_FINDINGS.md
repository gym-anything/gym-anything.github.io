# TRIAGE (Figure-style package station) — Phase 1 feasibility findings
All numbers MEASURED on this machine (Isaac Sim 5.1, RTX 3090), logs in triage/p*.log.
Scripts: p1_api_probe, p1_fem_bag, p2_decode_probe, p3_render_matrix, p4a-p4h, p5, p5b.

## P1 — Deformable poly bags: FEASIBLE (FEM, "old" deprecated API)
- This build has BOTH the deprecated PhysxDeformableBodyAPI path
  (`deformableUtils.add_physx_deformable_body`, needs GPU dynamics + GPU broadphase) and
  the new beta UsdPhysics.DeformableBodyAPI (`/persistent/physics/enableDeformableBeta`).
  The OLD path is what we validated (works headless, first try).
- Stuffed-mailer pillow (30x9x22 cm ellipsoid mesh, hex res 8, YM 20 kPa, Poisson 0.45,
  density 145, self_collision off, 16 pos iters):
  - 1 bag:  2.1 ms/step avg -> ~3.9x realtime @120 Hz. Stable, settles, no NaN.
  - 16-bag pile in a walled bin: 4.3 ms/step avg (8.8 ms during active settling,
    2.3 ms at rest) -> ~1.9-4x realtime. Pile stable over 2400 steps, no explosion,
    no fall-through, bags rest at plausible heights (0.02..0.28 m).
- Cooking is cheap (1-2 s for 16 bags at res 8).

## P2 — Barcode decode geometry (zxing-cpp on RTX renders, 2048^2, scan lamp 60k):
- RIGID box label (p03 texture): decodes at camera height 0.40/0.50/0.60 m above the
  label; FAILS at 0.30 (label out of frame) and 0.80 (px/module too low).
- FEM bag with label planar-projected on its curved settled top (p01): decodes at ALL
  heights 0.30-0.80 m (bigger label; curvature mild after settle).
- DESIGN: scan-tunnel camera at ~0.50 m above the belt. Deformation does not break
  decoding per se; frame coverage and px/module are the real constraints.

## P3 — Render+physics in ONE process: NO CRASH (old two-process doctrine disproven here)
Cumulative matrix, 360 steps each with live RTX rendering + camera annotator:
  A rigid scene ......................... 14.1 ms/step OK
  B + G1 articulation under control ..... 23.9 ms/step OK
  C + NuRec photoreal hub ............... 100 ms/step OK
  D + FEM deformable (GPU dynamics) ..... 118 ms/step OK
  E + zxing decode in-loop .............. 117 ms/step OK  (decode itself needs P2 geometry)
The historical v11 crash was NOT reproducible with this stack; in-loop scanning is
feasible (with NuRec the frame budget is ~8 Hz — fine for a scan camera).

## P4 — TWO-HAND CONTACT MANIPULATION: WORKS (the make-or-break result)
p4h_box_grip.py run 4 (p4h4.log): 0.8 kg 16x15x18 cm box on a plate in front of the G1.
GATES (all measured, contact forces from RigidPrim.get_contact_force_matrix):
  squeeze  PASS  fL=11.5 fR=9.3 N (force-gated fine roll ramp)
  lift     PASS  +0.150 m, zero contact gaps (grip maintenance re-tightens on decay)
  hold     PASS  240 steps, slip 0.000 m, forces ~32-35 N
  carry    PASS  waist-yaw turn swings box 0.207 m horizontally, height constant
  release  PASS  slow roll-out ramp -> box set down at 0.00 peak velocity
  (pre-pose gate flags a 7 cm box nudge during hand descent -- open polish item; the
   squeeze re-centers on the measured box pose so downstream still succeeds)
NO attachments, NO kinematic holds, collisions ON everywhere, PD position targets only.

Hard-won mechanics (each cost runs):
1. `g1_robot_fixed_flat.usd` is Z-UP: G1Hold needs translate + rotY(180) + rotX(-90)
   (build_sorthub_scene.py:142). Without rotX the robot lies on its side and every
   measurement is garbage (waist-yaw "lifting" wrists was the tell).
2. Zero pose (upright, facing -x): wrists (-0.20, 0.88, +-0.15); palm link 4.2 cm beyond
   wrist; palms naturally face each other; LEFT hand works +z side, RIGHT -z.
3. Dex3 THUMB protrudes ~6.5 cm INBOARD of the palm plane in every wrist/thumb config —
   palm-to-palm face contact is geometrically blocked; the thumb tips are the first jaw.
   Thumb tips at spawn sit at (-0.26, 0.88, +-0.087): parcels must spawn >8 cm clear of
   x=-0.26 or depenetration ejects them (two runs lost to this).
4. Finger curl limits are MIRRORED: left index/middle close NEGATIVE [-1.57,0], right
   POSITIVE [0,+1.57] (thumb_1/2 also mirrored). Left pre-curl of +0.4 silently no-ops.
5. Joint-direction table (p4b2.log) is the ground truth for servo Jacobians; re-measure
   at the working pose (stale J sent the servo the wrong way). Waist pitch is the
   descent axis (-0.21 m/rad y both palms) — front-low reaches NEED it (9-dof
   coordinated solve: 4 joints/arm + shared waist).
6. CONTACT FORCE READBACK: get_contact_force_matrix(dt=PHYSICS_DT)! Default dt=1.0
   returns raw per-step IMPULSE (N*s): our "2 N plateau" was really ~240 N of crush.
   Calibrate against a known resting weight; note kinematic/static filter rows read 0
   (only dynamic-vs-articulation pairs reported reliably here).
7. Force control by position targets: fine ramps (0.002 rad ~ 0.3 mm) force-gated per
   hand; contact stiffness ~100 N/cm. Coarse ramps or ungated servos crush, eject, or
   wind up (blocked-error integration through the shared waist contorts the body).
8. Grip maintenance during transport: if either hand's force decays below ~6 N,
   re-tighten both rolls. Release must be a slow ramp or stored press energy flings.
9. Hand gains: kp150/kd8/eff5 N*m (≈ real Dex3 torque). Arm kp600/kd120/eff150.

## P5 — Conveyor for deformables: SURFACE VELOCITY DOES NOT MOVE FEM BODIES
- PhysxSurfaceVelocityAPI (kinematic rigid): rigid box conveys at exactly 0.400 m/s;
  FEM bag does NOT move at all (0.000). The mechanism only feeds rigid contacts.
- TREADMILL belt (kinematic tiles physically translating +x, leapfrog back past the end,
  out of contact): box 0.398 m/s AND bag 0.406 m/s — both convey by real friction.
  8 tiles x 1 m @ 0.4 m/s, teleport at span edge behind the flow. THIS is the belt
  mechanism for the triage station (more faithful than surface velocity anyway: the
  surface genuinely moves).
- surfaceVelocityLocalSpace defaults TRUE and multiplies by prim scale — use world space
  or unscaled prims (old repo lesson, still true).

## Design consequences for Phase 2 (station build)
- Belt = treadmill tiles (rigid+deformable capable), NuRec hub as the shell, scan tunnel
  camera 0.50 m above belt, 2048^2, scan lamp.
- Hopper/pile: FEM bags at hex res 8 ~ 1 ms/step each while settling; budget ~15-20 FEM
  bodies live + rigid boxes/envelopes. Parked/inactive parcels cost ~0.
- In-loop scanning is allowed (P3): single process, but keep frame rate expectations
  ~8 Hz with NuRec on.
- Robot manipulation baseline = p4h primitive (pre-pose flank -> force-gated squeeze ->
  joint-space lift -> waist-yaw carry -> slow release). Open items: descent-brush fix,
  deformable-bag scoop variant (P4 was rigid box), robustness matrix across sizes/masses.
