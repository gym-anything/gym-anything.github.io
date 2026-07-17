# OPEN ISSUES — things parked, that I (the agent) must proactively remind the user about

> It is my responsibility to raise these again at the right moment, not wait to be asked.

---

## ISSUE #1 — RESOLVED (2026-06-11): force control works; root cause was Replicator
**The "first-target-only / uncontrollable articulation" bug was NOT a drive problem.**
`rep.orchestrator.step()` (the render-snapshot call) stops/plays the timeline, which
INVALIDATES the articulation's physics handles — exactly as the `SingleArticulation.
initialize` docstring warns ("call after each Stop+Play"). Every failing script
rendered between phases; every clean one didn't. FIX: `rep.orchestrator.step(...,
pause_timeline=False)` (fallback: re-`initialize()` after each snapshot). With that,
position-drive tracking is ≤0.5° across arbitrary successive targets.
The excavator is now a TRUE force-controlled dynamic articulation (per-joint effort
caps, 1 rad/s velocity limits) — the kinematic workaround and the hardcoded workspace
clamp are RETIRED. See TECHNICAL_REFERENCE for the full recipe.

## ISSUE #2 — RESOLVED (2026-06-11): CAPTURE ACHIEVED — user dug and carried rocks
## interactively with the TRUE-MESH bucket. ROOT CAUSE of all pass-through/capture
## failures: (1) bucket collision was hand-authored proxy boxes, never actually
## aligned with the visual scoop (bbox "verification" cannot detect mis-mounting) —
## fixed by convexDecomposition collision ON the photoreal bucket mesh itself;
## (2) rocks' maxDepenetrationVelocity=0.5 (a settle-era stabilizer) let any contact
## faster than 0.5 m/s sink THROUGH walls — raised to 6.0 with velocity/impulse caps;
## (3) muck regraded to real fines->boulders (1797 rocks, median 0.2 m) — flows and
## fills like real material. The scripted autonomous dig cycle still needs the
## mouth-close timing polished (operator-level skill; FK harness in proof_dig.py),
## but the PHYSICS is fully proven. Historical analysis below.
## (the section below predates the resolution — kept for the record)
VERIFIED WORKING: FK-planned bites reach the bay floor (teeth -1.2); 160+ rocks
displaced per cycle; ridge-building (windrow double-pass: bucket presses into 0.3 m
of accumulated material); attitude-held exit chain (bowl world-attitude theta =
boom+stick+bucket kept ~60 deg through lift+swing — fixes the carry spill); the scoop
IS a working container (a teleported REAL rock rests in the bowl and stays at rest).
THE GAP: the 1.71x/5x muck rescale left a SPARSE COARSE BED (median rock 0.29 m,
2-3 layers, large voids). Rocks escape laterally around the 0.9 m scoop instead of
pressurizing into the mouth — real granular behavior for thin coarse beds; what fills
real buckets is the FINES fraction, which the rescale removed. 4 rocks were within
0.7 m of the bowl at curl-end (wall-trap pass) but none nested inside through lift.
PATHS (in realism order):
 (a) RESTORE FINES: +1500-2500 small rocks (0.08-0.2 m) = true muck gradation
     (fines->boulders); fines pour over the lip and fill the bowl. Headless verify
     first; GUI rock count may need tuning for FPS.
 (b) Scoop plate friction: colliders have NO physics material (binding cannot reach
     instance-proxy colliders; requires editing configuration/*_physics.usd
     prototypes directly). Steel-on-rock ~0.5 would help retention.
 (c) Interactive operator finesse in the GUI (machine is fully driveable now).
ALSO LEARNED: session-spawned spheres do NOT collide with the articulation (test
artifact — real file-resident rocks do); test container behavior with real rocks.
LATE-SESSION DISCOVERIES (critical for the next capture attempt):
- **THE BOWL CRADLES AT NEGATIVE BUCKET ANGLES** (empirical flip test: a real rock
  RESTS on the bucket at -60, sheds at +100). The "+ = curl" convention from the
  kinematic era describes TEETH ENGAGEMENT, not bowl attitude. Cradle/carry attitude:
  theta_total = boom+stick+bucket ~ -100. ALL prior capture cycles closed an INVERTED
  dome over the material and lifted an upside-down cup.
- Scoop plates thickened 0.07 -> 0.22 m (centers shifted outward; cavity EXACTLY
  preserved) to prevent force-extrusion through thin walls.
- User-observed "rocks passing through the holder": combination of inverted-bowl
  deflection + (pre-thickening) thin-plate tunneling at speed.
- Remaining gap: ROTATE-AND-SINK coordination — rotating the bucket toward cradle
  (-95) lifts the mouth out of the material (cavity rides ~0.0 while rocks top at
  -0.35); the boom must press down DURING the rotation to keep the mouth submerged
  (cav target <= -0.5). 275 rocks moved per cycle, throws to 1.5 m — engagement is
  vigorous; envelopment is the unsolved inch. Fines restoration remains the
  forgiveness fix.

## ISSUE #3 — Known terrain-mesh artifacts (NEW, 2026-06-11)
(a) Bench triangles face DOWN → downward raycasts pass through (backface culling);
    do NOT trust raycast heights on this mesh — collision contact is two-sided and fine.
(b) The bench is debris-strewn scan junk; a deliberate full-force bucket grind into it
    can WEDGE the bucket irreversibly (rigid mesh doesn't yield like real ground).
    Mitigated: graded machine pad under the tracks (real-practice leveled pad);
    operators shouldn't grind the junk pile. The dynamic MUCK yields correctly.
(c) One pinch-ejection event seen (rock shot 26 m when pinched by scoop) — watch.

## ISSUE #1-OLD (historical text below, kept for the record)
## Excavator force-controlled drives don't work in the standalone loop (PARKED)
**Status:** parked on purpose (2026-06-09). Using **kinematic** control to build the task instead.
**Owner reminder:** I must bring this up again **before/at the point we need a learning or
torque-controlled agent** (i.e. when we wire up RL / an agent that commands joint efforts or
position targets through physics), because kinematic actuation won't suffice there. Also raise
it if the kinematic excavator ever looks unphysical when scooping (e.g. plowing through rocks
with no give).

**What works now:** `art.set_joint_positions(q)` each physics step — the arm tracks the full
dig cycle exactly, and the moving colliders physically push the dynamic rocks. Good enough to
build and demonstrate the loading task.

**The bug:** in a standalone `isaacsim.core.api.World` loop,
`art.apply_action(ArticulationAction(joint_positions=...))` applies only the **first** target,
then every subsequent target is ignored (arm freezes at the first commanded pose). Reproduced
on BOTH a hand-authored articulation AND a URDF-imported one → it's the standalone control
loop, not the robot.

**Ruled out (all verified):** gains (read back = set), max_efforts (read back = 5e6), applied
target (read back = commanded), masses/inertias (correct), `JointStateAPI`, `switch_control_mode
("position")`, `flush_changes()`, `world.scene.add` vs manual `initialize()`, drive type
force/acceleration, velocity cap, self-collision.

**What to try next (research-first, per the #1 rule):** read a *complete* Isaac standalone
example that drives an articulation across multiple targets over time (not a one-shot pose);
the `omni.physx` tensor API directly; or run the control loop inside the interactive GUI app
loop instead of headless `world.step`. Confirm with a stock robot (Franka) in the identical
loop to isolate the loop vs the setup.

**Cost so far:** ~23 build-render-guess iterations. (See PRINCIPLES.md #0 — this is exactly the
kind of thing to research fully before the next attempt.)

## ISSUE #4 — RESOLVED (2026-06-12): truck DELIVERY proven; spotting geometry was the blocker
## The verifier counted LOADED: 1 rock into the parked ADT bed (load_cycle_proof.py).
## Three real-geometry blockers, all named by contact instrumentation + asset probes:
## (1) bed long axis radial + FK minimum dump radial ~6.1 m => only the HEADBOARD was
##     reachable -> re-spotted the truck rear-of-bed-at-radius, cab beyond max reach;
## (2) haul road has a real ~12% grade -> truck parked at surveyed height + rotX -6.9;
## (3) the asset has a raised TAILGATE (top ~3.0 world, 1.3 m above rail median) ->
##     dump pose raised to bucketJ (6.56, 4.61) so opening teeth (dip 3.16) clear it.
## STILL OPEN: scripted bite gathers ~0 rocks (user digs fine interactively);
##             multi-cycle 100 kg success needs real bites or the GUI operator.

## ISSUE #5 — Rock leak through carved bay edges (OPEN, low priority)
## ~50 rocks per long episode end below y=-3 (fell through gaps at the carved bay
## boundary), flagged as lost_offmap by the verifier. Doesn't affect loading proofs;
## fix candidates: skirt colliders at the carve seam, or re-carve with overlap.
