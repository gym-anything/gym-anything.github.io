# Lock and key. Measured engine laws and probe results.

Every entry here was verified by a headless probe in this repo, with the
probe name given. This is the durable memory for the lock and key build. It
sits alongside RESEARCH.md, which holds the real world dimensions and forces.

## Engine laws (PhysX 5 / Isaac Sim 5.1, RTX 3090)

L1. A pin at true Kwikset scale seats stably. A free brass key pin (2.921 mm
diameter, 0.25 g) and a spring loaded driver in an octagonal chamber settle to
a rest that holds position to 0.4 um over a quarter second. The clearance used
was 0.10 mm radial and the contact offset 0.05 mm. Probe p1_pinstack.

L2. A large external force on a near weightless free body punches through in one
step. A 0.3 N spring force applied directly to a 0.26 g driver gave 1150 m per
second squared and the driver tunnelled through the key pin and floor in a
single 1/480 s step. The fix is to carry the spring on a prismatic joint drive,
which the solver integrates implicitly and cannot tunnel. It is also the
faithful model, because the driver never rotates in a real lock. Probe
p1_pinstack.

L3. PhysX reports resting contact velocity noise. A pin whose position holds to
sub micron over a window still reports an instantaneous speed of about 4 mm per
second. The physical test for "settled" is peak to peak position drift, not the
reported velocity. Probe p1_pinstack.

L4. A DYNAMIC signed distance field mesh does NOT generate contacts against a
convex or primitive shape. It DOES generate contacts against another signed
distance field mesh. Measured directly. A convex cylinder pin dropped into a
kinematic SDF plug is held, but the same pin dropped into a dynamic SDF plug
falls straight through, while an SDF meshed pin is held by the dynamic SDF plug.
Therefore, in this lock, the plug is a dynamic SDF body and every pin that must
touch it is also authored as an SDF mesh, not a UsdGeom primitive. This mirrors
NVIDIA Factory, where both the nut and the bolt are SDF. Probes _colltest and
_colltest2.

L5. A convex decomposition collider did not preserve the sub millimetre chamber.
A cylinder with a vertical bore, given the convexDecomposition approximation
with 64 hulls and half a million voxels, let a pin fall straight through. SDF is
the representation that keeps the chamber. Probe _colltest.

L6. The mesh boolean backend manifold3d and the 2D backend shapely are not in
the stock Isaac python and were installed with pip. trimesh 4.5 and scipy are
present. The plug, shell, and key blade are built by boolean subtraction and
2D profile extrusion with these.

L7. The correct-key turn needs a real shear tolerance; a rigid knife-edge shear
line binds the correct key. Measured cause: with SDF pins the key pin seats
about 0.06 to 0.10 mm above its ledge (an SDF contact-resting gap that shrinks
with the contact offset and the SDF margin), and the driver rests right on the
key pin, so any proudness binds. The faithful tolerance is the pin taper. Real
Kwikset pins are tapered on both ends, and the bevelled edge cams a near-shear
pin clear of the shear line. Chamfered pins plus a measured collision-skin tare
are being calibrated against the turn window (p2_sweep). Wrong keys already bind
hard at the operating torque, so the security behaviour is correct; only the
correct-key turn tolerance is open.

L8. The warding rejects a foreign blank geometrically (CPU, no physics). A
reconstructed KW1 keyway with two ward ridges, sized to the real 2.03 by 8.51 mm
blade envelope, gives zero overlap for the matching KW1 blade and 1.08 mm^2 of
overlap for a foreign profile, so the foreign blank is physically refused before
any pin is reached. Probe _wardtest. The exact KW1 ward profile is proprietary;
this is a disclosed reconstruction, and what is real is the refusal behaviour.

L9. THE ROTATING PLUG WORKS AS AN EXPLICIT CONVEX DECOMPOSITION, not as an SDF
mesh. The SDF plug had three rotating-contact pathologies, each measured: it
binds rotating inside the static triangle-mesh shell bore (empty plug, no pins,
<1 deg with the shell, 45 deg without); a snap position-motor flings the SDF
pins off; and a proud key pin sweeps free without the shell catching it. The fix
is to build the plug from convex pieces -- two cylinder segments and two slabs
flanking the chamber, plus a ledge box (lock_mesh.make_plug_convex) -- attached
as convexHull child colliders of one plug body, with convexHull-cylinder pins.
Convex-vs-convex and convex-vs-static-mesh are PhysX's robust paths. Result,
reproducible bit-identical: the correct key TURNS (55.8 deg at a 30 deg/s hand
turn, 0.20 N m cap) while every wrong cut -- one increment or two, low or high --
BINDS under 2.1 deg, and no shell-collision filter is needed. Two more pieces of
the recipe: a velocity motor (a steady hand turn) instead of a snap position
drive keeps the pins engaged, and the pin taper cams a near-shear pin clear
against the FLAT convex chamber wall (it did not cam against the round SDF
chamber). Probe p2c_plug_bind. This is P2 PASS.

L10. THE FULL FIVE-PIN LOCK WORKS -- P4 PASS. The correct key 31542 OPENS (turns
51.7 deg) and every single-cut-wrong key LOCKS (under 2.1 deg), from contact
alone, no scripted decision. Two findings got it there. First, the key surface
tare should be near zero on the convex plug: unlike the SDF plug, the convex plug
has no contact-resting gap, so the key pin sits exactly at shear minus the tare,
and a tare of zero seats every correct pin right at the shear line so the drivers
do not have to be cammed. Second, and decisive, SOLVER QUALITY: with five pins,
ten free bodies, and many simultaneous camming contacts, the default 480 Hz and
32 position iterations hard-lock the correct key at about 8 deg regardless of
torque (a solver failure, not a real bind -- 2 N m could not break it). Raising
to 960 Hz and 64 position iterations resolves the contacts and the correct key
turns freely. Four pins already open at the lower quality; five need the boost.
Probe p4_full. This is the core task demonstrated.

L11. [SUPERSEDED by L13-L16 -- the sliding key is SOLVED, see L16.]
THE PHYSICAL SLIDING KEY (P3) is built but its full-insertion pin seating
is an OPEN refinement, disclosed honestly. What works: a keyway plug with the
chambers open to a channel (make_plug_keyway_convex, no ledges), a convex-slab
key blade whose milled top follows the real bitting (make_key_blade_convex,
verified: each cut sits at the correct key surface), the blade prismatic-jointed
to the plug so it slides to insert and turns with the plug, and partial insertion
correctly LOCKS the plug every time. What does not yet work reliably: seating all
five pins at the shear line on full insertion. The pins do not land in their cut
valleys deterministically -- dropping them onto a static inserted blade scatters
them by up to half a millimetre (the pin is wider than the cut flat and rests on
a ramp), and animating the blade slide-in flings them. Approaches tried: pointed
pin bottoms, a widened cut flat, a measured blade tare, finer slabs, longer
settling, the animated slide. This is the same sub-0.1 mm seating precision that
made P2/P4 hard, now on a moving discretized blade, and it is not yet solved.
DISCLOSED as a refinement, not hidden. The correct-key vs wrong-key
discrimination itself is fully physical and verified in P4; the key's cut surface
in the working assembly is the plug ledge, which rotates with the plug exactly as
the real key does when turned, so the lock is operated by a real key geometry --
the open item is specifically the physical slide-in insertion seating.

L12. P5 A156.5 QUANTIFICATION on the working P4 lock. Operating torque: the
correct key 31542 opens (51.7 deg) down to a 0.03 N m cap, well UNDER the
A156.5 Grade 1 maximum operating torque of 0.14 N m -- a correct key turns
easily, which is the realistic behaviour (0.14 is the ceiling, not the target).
Attack: a wrong key 41542 HOLDS at a 2.0 N m cap (turns only 1.74 deg), far under
the 45 deg failure limit; the wrong pin binds hard. So the lock is easy for the
right key and firm against the wrong one, both consistent with the standard.
Probe p4_full with MOTOR_CAP_NM.

L13. PHYSX CONVEX COOKING CORRUPTS ANY HULL THINNER THAN ~1 MM. Measured with
_hullprobe.py (a cube pressed against a thin wall, reading where it stops): a
0.51 mm wall's collision face sits +0.345 mm OUTSIDE its authored position; a
0.30 mm wall is unstable (face read 0.14 mm inside); 1.0 mm and 2.0 mm walls
are exact to a micron. PhysxConvexHullCollisionAPI minThickness does NOT cure
it. The corruption is not confined to the thin axis -- a piece with ANY sub-mm
dimension bleeds on other faces too (widened-but-thin-in-x between-chamber
bands poked 0.16 mm into the keyway slot at their ledge corner). RULE: every
convex collider must be >= 1 mm in EVERY dimension; faces are then exact.
This single law explains the phantom-contact jams on boolean-verified-clean
scenes (228-290 reported contacts at rest) AND retroactively explains P4's
0.22 mm tare (was misattributed to contact skin). Consequences implemented:
the key blade is 16 large convex prisms with exact sloped tops
(make_key_blade_prisms -- thin slabs cook badly, 1 mm slabs staircase the
ramps into unclimbable risers); the plug's 0.69 mm between-chamber walls and
slot caps are visual-only; their turn-phase role (the surface a lifted driver
rides) is played by corner bands that follow the REAL round chamber wall at
|y|>=1.2 mm where the between-chamber material is 1.81 mm wide (all dims
>=1 mm). Slot walls widen OUTWARD (overlapping same-body pieces is harmless)
so their functional faces stay exact.

L14. THE PHYSICS DEMANDED THE REAL MANUFACTURED GEOMETRY. Every sliding-key
failure traced to a place where the model was LESS real than the metal:
- Flat-bottomed pins catch cut crests on their cylindrical flank (horizontal
  normal, nothing cams; measured 19.6 N grinding at exactly such a contact).
  Real Kwikset bottom pins are bullet-nosed; tip_bot=1.2 mm ended it.
- A sharp-cornered rectangular blade cannot enter the bore: its bottom corners
  are at 6.45 mm radius vs the 6.40 mm shell bore. Real keys remove those
  corners with warding grooves; _blade_slab's corner bevel is that relief.
- A flat-topped pin at the shear PLANE pokes past the plug CYLINDER at its rim
  (sqrt(PIN_R^2+PLUG_R^2)=6.52 > bore 6.40) and wedges plug-to-shell at
  exactly 0.00 deg. Breaks must seat ~0.2 mm BELOW the plane (root_tare on
  the cuts, standing in for real domed pin ends). Tare the CUTS, never the
  spine (a spine tare sinks the blade bottom into the shell floor).
- The widened 2.9 mm cut flat (an old workaround) self-intersects at MACS-4
  adjacent cuts: the deep cut's cutter shaves the shallow neighbour's seat
  0.24 mm low and the turn binds. The REAL 2.13 mm flat has no such
  intersection; restoring it fixed the turn AND the partial-insertion stall.
- Drivers must spawn ABOVE their key pin's spawn top: a driver spawned at
  shear interpenetrates a long pin by up to 3.2 mm and the deep-penetration
  resolve wedges the stack.
- The key insertion must be a FORCE-CAPPED dynamic hand (world-anchored
  prismatic drive at the A156.5 gate), never a kinematic pose: kinematic
  contacts carry unbounded force, grind the plug through its rotational-play
  limit, and penetrate the static shell silently. The honest dynamic blade is
  what EXPOSED the geometry errors above.
- Key pins ride vertical prismatic joints to the PLUG (anti-cock, and they
  rotate with the plug); drivers ride world-anchored joints (they must stay
  with the shell to bind). The key's support of a pin is UNILATERAL: after
  insertion the pin's joint LOWER LIMIT becomes the key-set height (a floor),
  never a rigid bilateral lock (which welds a grazing pin and wedges at 0.00).

L15. INSTRUMENT LAWS. (a) The PhysX contact report only includes pairs whose
BODY carries PhysxContactReportAPI -- a plug-only report made pin contacts
invisible and manufactured a false 'floating pin' mystery; flag every body.
(b) GPU rigid-body dynamics is nondeterministic run-to-run and occasionally
produced states classifiable only as engine misbehaviour (pin-driver
interpenetration by mm with no reported contact); CPU (CPU=1) is deterministic
but grinds differently. The final config runs GPU with all geometry
cooking-safe, where results reproduce bit-for-bit. (c) Sleep must be disabled
on the pins (sleepThreshold 0): a pin riding a constant-height blade section
sleeps and then ignores gravity AND its driver spring.

L16. P3 SOLVED -- THE FULL PHYSICAL SLIDING KEY WORKS, ALL VERDICTS FROM
CONTACT. Config: prism blade (real 2.13 mm flats, root_tare 0.2 mm, corner
bevel, 45-deg tip lead-in to a 1 mm nose), ledge keyway plug with corner
bands, bullet-nosed jointed pins, spawn-separated drivers, 26 N hand
(HAND_FORCE_N, the A156.5 worn gate; 13 N stalls on ramp-climb friction),
0.5 s insertion (INSERT_S; the real speed -- slow quasistatic crawls grind),
0.3 N m turn cap. VERIFIED (p3_slidekey.py): correct key 31542 inserts fully
(shoulder stops on the plug face), seats ALL FIVE breaks at -0.200 mm, opens
60.04 deg -- BIT-FOR-BIT REPRODUCIBLE x3 (identical heights to 0.001 mm,
identical angle). Wrong keys hold at the ~1 deg rotational play: 12345 at
1.0, 54321 at 0.9, 31541 (a SINGLE increment on a SINGLE cut, 0.58 mm) at
1.5. Partial insertion (60%) reaches its commanded depth and holds at 0.95.

## Resume plan (when the GPU is free)

The GPU is periodically held by the user's game (FC26); Isaac boot-crashes under
its exclusive hold, so GPU probes pause and a watcher waits for the game to
close. When the GPU is free, run in this order.

1. `bash p2_sweep.sh` then read `p2_sweep.log`. Find the (chamfer, tare) combo
   where CORRECT turns past 30 deg and WRONG_low stays under 5 deg. Analysis
   predicts chamfer 0.4 mm, tare 0.10 mm. If NO combo turns the correct key,
   the pin-taper camming does not resolve in SDF; fall back to modelling the
   real plug-shell clearance as radial float on the plug (a D6 joint: free rotX
   with the motor, transY and transZ limited to the clearance, the rest locked).
2. `PIN_CHAMFER_MM=<c> SURF_TARE_MM=<t> bash p4_run.sh` then read `p4.log`. The
   correct key 31542 must OPEN; every single-cut-wrong key must stay LOCKED.
   That is the core task demonstrated.
3. P3: build the 3D warded keyway (extrude the verified 2D ward cross-section
   along X, subtract into the plug) and a real KW1 blade that slides in and
   lifts the pins; a foreign blank is refused. The 2D warding already passes
   (_wardtest). Replace the ledge stand-in with the sliding blade.
4. P5: the ANSI/BHMA A156.5 verifier battery + spring/friction calibration
   anchored to the 13 N insertion gate.
5. Assembly, a viewable scene with real materials, an embodied agent that
   inserts and turns the key, and the paper.

Always kill stray kit.exe before a launch and stagger launches; a crashed-but-
not-exited kit holds the GPU (seen here) and blocks the next run.

## Probe ladder status

- P1 PASS. One real pin stack seats stably at true scale. Verified.
- P2 PASS. One stack in a rotating CONVEX plug: the correct key turns 55.8 deg,
  every wrong cut binds under 2.1 deg, reproducible, from contact alone. The
  canonical probe is p2c_plug_bind (the SDF p2_plug_bind is superseded).
- P4 PASS. The full five-pin lock: correct key 31542 OPENS (51.7 deg), every
  single-cut-wrong key LOCKS (<2.1 deg), from contact. Settings: 960 Hz, 64 pos
  iters, tare 0. Probe p4_full.
- P3 PASS (L16). The physical sliding key: a 26 N hand inserts the real-profile
  blade in 0.5 s, the shoulder stops on the plug face, all five breaks seat at
  -0.200 mm, the correct key opens 60.04 deg bit-for-bit reproducibly x3;
  wrong keys (12345, 54321, single-increment 31541) and a 60% partial
  insertion all hold at ~1 deg. Probe p3_slidekey.
- P5 PASS on the P4 lock (L12). Sliding-key-side recalibration (insertion
  force curve, spring preload spread) still open.
- OPEN: physical 3D warding (2D proof only), the live interactive scene, and
  the padlock presentation pass.

## L17-L22: the UNLOCK-THE-BOX scene (unlock_box.py, 2026-07-08 session)

The task scene the padlock belongs in: a room, a table, a chest whose lid is
held by a real hasp chain (staple ring through a slotted hasp plate, pinned by
the shackle leg), two keys in cradles (31542 correct, 12345 wrong), and a
Franka that picks the correct key, carries it, seats it, and turns the plug.
Every law below was found by a measured failure of that run and fixed at cause.

- L17 CONTACT-SKIN SPAWN LAW RECONFIRMED. Scene colliders built by helper
  functions carried the PhysX default (~cm) contact offset; every mm-scale
  clearance (key cradles, staple ring, shackle) spawned inside a skin and got
  depenetration-blasted (a key flew 1.06 m). Every add_box now authors a
  0.3 mm contact offset and clearances sit above it.
- L18 UNRACK ALONG THE FREE AXIS. A horizontal blade lifted vertically through
  snug cradle forks scrapes, spikes the contact, and flings the welded arm
  (measured err 88 -> 559 mm). Sliding the key forward along the open slot
  direction leaves nothing to fight (err 23 mm). Racks must be departed the
  way they were entered.
- L19 RMPFLOW DIVERGES ON THE LATERAL CARRY; LULA WAYPOINTS DO NOT. With or
  without registered obstacles, RMPflow blew up (334-624 mm) moving the welded
  key laterally at this bench. Lula analytical IK + joint-space interpolation
  + closed-loop nudges (the sorthub place recipe) tracks every leg at 3-4 mm.
- L20 SERVO ON THE OBJECT WITH GAIN. The arm carries a stable ~4 mm tracking
  deficit at tilted-wrist poses; unit-gain closed-loop rounds re-absorb their
  own correction forever. One round commanding 2.2x the measured error snaps
  the key from -4.3 mm to -0.06 mm. All alignment loops now run gain 2.2 after
  two unit rounds, clipped to 8 mm.
- L21 THE GRASP COCKS THE KEY ~11 DEG; LEVEL IT CLOSED-LOOP, THEN ENTER. A
  compliant grip engaged in free air lets the blade-heavy key nose-dive
  (measured z -7.5 mm at the mouth). Order that works: rigid weld through the
  free-air approach, measure the key quaternion, rotate the hand by its
  inverse (11.28 -> 0.14 deg), re-align, and only go compliant when the slot
  itself can support the blade.
- L22 THE KEY'S SHOULDER IS LOAD-BEARING GEOMETRY. The embodied_open key's
  neck overlapped the blade's last 8 mm, so full seat required driving the
  neck through the shell face -- an impossible geometry that read as a force
  stall (the measured stall x matched the neck-face contact to 1 mm). The
  neck now sits fully behind the blade rear and kisses the shell face at
  seat depth, exactly the real shoulder stop. With it, the arm seats the
  correct key (breaks within 0.33 mm of shear) and the wrong key jams 6 mm
  short under the same capped force with breaks up to 3.4 mm off shear.

RESULT (correct key, full chain, selftest): grasp weld -> carry -> level ->
seat (five breaks within 0.33 mm of shear) -> wrist turn -> plug 74.39 deg
OPENS -> shackle pops 10.27 mm. Wrong key: INSERT INCOMPLETE at 6 mm short,
no turn attempted (and a fully-seated wrong key binds at ~1 deg per P3).
DISCLOSED MODEL: the shackle release is a real spring on the rail whose
retarget is gated on the MEASURED plug angle; the contact dog-and-cam latch
is TODO (padlock_bench shipped a visual-only shackle; this is one step up).
DISCLOSED: the lock mechanism stays world-anchored at its hanging pose (as in
every verified probe); the hasp chain around it is real contact geometry
(lid pull test: held at 30 N locked; control with the ring deleted opens).
