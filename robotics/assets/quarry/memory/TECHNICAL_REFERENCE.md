# Technical Reference — Isaac Sim 5.1 / NuRec / PhysX (quarry)

Concrete, load-bearing facts. Consult before writing any new quarry script. Every item
here cost real debugging time.

---

## Environment
- **Isaac Sim 5.1.0 standalone:** `$env:ISAAC_SIM_ROOT`
  - Launch any script with the bundled python: `python.bat <script.py> [args]`
  - `pxr` is only importable AFTER `SimulationApp({...})` boots Kit. A pure
    `from pxr import Usd` without `SimulationApp` fails with `ModuleNotFoundError`.
- **GPU:** RTX 3090, 24 GB. ~3000 full-res scanned rocks (~193M tris) fit but render slow;
  ~600 (~39M tris) is comfortable.
- **Isaac Lab is NOT installed** (Isaac Sim is). No wheel-loader / haul-truck / excavator
  assets are bundled locally — only PhysX test-vehicle USDAs and small mobile robots
  (Carter, iw_hub). The task embodiment must be sourced + rigged.

## The scene (Vast Quarry splat)
- File: `Vast_Quarry_with_Machinery_nurec.usdz` (562 MB, ~5M gaussians, **visual only,
  no collision**).
- **CRITICAL — up-axis trap (REGRESSED ONCE — rule strengthened):** stage metadata says
  `upAxis = Z`, but the **geometry is Y-up** (bay floor normal ≈ +Y). Therefore:
  - **Down is −Y.** Always author a `UsdPhysics.Scene` with gravity `(0,-1,0)`, mag 9.81.
  - Never rely on `World`/PhysX **default gravity** — it is −Z = *horizontal* here.
  - **AND: authoring gravity in the FILE is NOT enough.** `World()`/PhysicsContext
    OVERRIDES the scene's gravity from the stage up-axis metadata (Z!) when it
    initializes. The 2026-06-11 regression: dynamic scripts trusted the file's authored
    (0,-1,0) and World silently flipped it to −Z; telltale = persistent ~100-150 kNm
    "gravity" torque on the VERTICAL swing axis (should be ~0). RULE: **re-assert
    gravity (0,-1,0) AFTER World creation AND after world.reset(), then VERIFY BY
    READBACK and print it.** Every World-using quarry script must do this.
- **NuRec rendering** (so the splat backdrop shows): `RaytracedLighting` +
  `/omni/rtx/nre/compositing/disableNuRecBackground=False` +
  `/omni/rtx/nre/compositing/disableNuRecPostProcessings=False`.

## Key scene constants (`quarry_task_params.json`)
- `floor_point.y = -1.392`  (bay floor height)
- `pocket_min = [-6.07, -1.59, -1.83]`, `pocket_max = [-0.64, 0.31, 2.52]`
- `pocket_center = [-3.40, -0.91, 0.29]`, footprint **5.43 × 4.35 m**, walls ~1.7 m
- `scale_m_per_unit = 1.0` (CALIBRATED; 1 unit = 1 real metre)
- Track / haul-unit location ≈ `(2.98, -0.30, 0.13)`

## Physics that works (muck)
- `World(stage_units_in_meters=1.0, physics_dt=1/120, rendering_dt=1/60)`.
- Per rock: `RigidBodyAPI` + `MassAPI(density=2550)` + `PhysxRigidBodyAPI(enableCCD=True,
  solverPositionIterationCount=32, solverVelocityIterationCount=4)`; collider =
  `MeshCollisionAPI` approximation **`convexHull`** on each child Mesh.
- Physics material: static friction 0.7, dynamic 0.6, restitution 0.15
  (`UsdPhysics.MaterialAPI`, bound with `materialPurpose="physics"`).
- **`convexHull` settles fast and quiesces.** **`convexDecomposition` was unstable here**
  (24 sliver hulls/rock → perpetual explosion during settle). Do not use it for the muck.
- No-overlap **rejection-sampled spawn** prevents tunneling; settle to **quiescence**
  (step until max per-rock move < ~1.5 cm / 200 steps), not a fixed step count.
- Replay safety in the saved file: `maxDepenetrationVelocity=0.5`, linear/angular damping
  0.4, `sleepThreshold=0.005` (caps any residual nudge).

## The Fabric/Sdf save trap (and the fix)
- After `World.reset()`, PhysX writes poses to **Fabric/USDRT**, not the **Sdf** layer.
  `omni.usd.get_context().save_as_stage()` serializes Sdf → it saves the **pre-physics
  (authored) transforms**, i.e. the un-settled spawn scatter, even though in-session
  reads and renders (Fabric-backed) look settled.
- **Fix = two-phase, no physics in the saving process:**
  1. `settle_dump.py` — build, settle to quiescence, read settled WORLD poses via
     `ComputeLocalToWorldTransform` (Fabric-backed = settled), cull escapees (y < floor−2),
     `np.savez` → `muck_poses.npz`.
  2. `author_save.py` — **fresh process, NO `World`** — open splat, **define
     `/physicsScene` with gravity (0,-1,0)** (no World means nothing auto-creates it!),
     author each rock at its settled translate/orient/scale + colliders, render to verify,
     `save_as_stage`. With no Fabric active, the saved Sdf holds the real settled poses.

## Rendering (headless)
- `capture_viewport_to_file` writes **nothing** headless. Use Replicator:
  `rep.create.render_product` + `WriterRegistry.get("BasicWriter")` +
  `rep.orchestrator.step(rt_subframes=48)`, with `/omni/replicator/asyncRendering=False`
  and `/app/asyncRendering=False`. Last frame (most accumulated) is the one to inspect.
- Camera FOV: `focalLength = 36 / (2*tan(fov/2))`, `horizontalAperture=36`. Wide
  (~72–120°) for context; ~40–48° for close inspection. Too-narrow FOV on close texture
  reads misleadingly as "looking at a surface."

## Assets
- Scanned rocks: `rock_assets/<id>/<id>.usd` (converted from Poly Haven glTF via
  `omni.kit.asset_converter`). Subset used (grey/tan granite, native bbox size in units):
  namaqualand_boulder_02..06, namaqualand_boulders_01, namaqualand_rocks_01,
  namaqualand_stones_01, boulder_01, moon_rock_01, moon_rock_03. Mean **~64k tris/rock**.
- Floor material: `textures/Ground037` (OmniPBR, `project_uvw=True` triplanar).
- vMaterials 2.4 at `C:\Users\<user>\Documents\mdl\vMaterials_2` (measured materials).
- SAM3 env: `D:\research\uvenvs\sam3\Scripts\python.exe`; set `HF_HOME=D:\research\cache\hf`,
  `HF_HUB_OFFLINE=1`.

## Script map (quarry/)
- `settle_dump.py` — phase A: build + settle to quiescence → `muck_poses.npz`.
- `author_save.py` — phase B: author settled poses + **explicit −Y gravity** → save.
- `open_muck_gui.py` — open a saved muck USD in the interactive GUI (set `SCENE`).
- `diag_gravity.py` — reproduce GUI Play (timeline, no World) and report per-axis fall.
- `diagnose_play_v3.py` — steps physics via World; **note:** uses World's default gravity,
  so it does NOT faithfully reproduce GUI gravity — prefer `diag_gravity.py` for gravity.
- `count_rock_polys.py` — triangle/vertex census of the scanned rocks.
- Output: `quarry_scanned_muck_v3.usd` (final), `previews_scanned_muck*/` (renders).

## Articulations / robot control (the 23-iteration excavator saga)
- **Correct drive setup** (from `PolicyController.initialize`, `policy_controller.py`): after
  `world.reset()` + `art.initialize()` → `ctrl.set_effort_modes("force")` →
  `get_physx_simulation_interface().flush_changes()` → `ctrl.switch_control_mode("position")`
  → `ctrl.set_gains(kps,kds)` → `ctrl.set_max_efforts(...)` → `flush_changes()` →
  `art._articulation_view.set_max_joint_velocities(...)`. **The flushes and the
  control-mode switch are mandatory** — without them, gain/effort changes silently don't
  reach PhysX (every run comes out byte-identical regardless of what you set).
- **Required per joint:** both `UsdPhysics.DriveAPI(joint,"angular")` AND
  `PhysxSchema.JointStateAPI(joint,"angular")` (drive_rules.py:34-35). Fixed-base =
  `ArticulationRootAPI` on the BASE link + a `FixedJoint` (body0 empty, body1=base).
- **UNRESOLVED standalone bug:** in a standalone `World` loop, `apply_action(joint_positions=...)`
  applied only the FIRST target then ignored subsequent ones — on BOTH a hand-authored
  articulation AND a URDF-imported one. So it's the standalone control loop, not the robot.
  Verified not caused by: gains/efforts/targets (all read back correct), masses/inertias
  (correct), JointStateAPI, control mode, flush, world.scene.add vs manual init.
- **WHAT WORKS for control:** kinematic `art.set_joint_positions(q)` each step tracks the
  full trajectory exactly; the moving colliders still push dynamic rocks. Using that for the
  task. Force-controlled drives (for RL) are PARKED — revisit (likely a step/flush detail or
  Isaac version quirk; try the `omni.physx` tensor API or an interactive-GUI loop next).
- URDF import: author `.urdf` (box links + computed inertias) → `omni.kit.commands.execute(
  "URDFCreateImportConfig")` set `fix_base`, `import_inertia_tensor` → `execute(
  "URDFParseAndImportFile", urdf_path, import_config, dest_path)`. Imports Z-up at
  `/World/<robotname>` with a `root_joint` fixed base.

## CAT excavator asset (the real agent)
- `excavator_assets/cat/excavator_cat.usd` — converted from sarvesh12's "Excavator (CAT)"
  (Sketchfab, **CC-BY-4.0, must credit**, see gltf/license.txt). Photoreal full-PBR
  (BaseColor/Metallic/Roughness/Normal per region), tracked 320-class, ~9 m long at
  scale 0.772, **author-structured articulation chain**:
  `whole_body1 → turning_body (swing) → whole_arm (boom) → arm1 (stick) → plough (bucket)`.
- **UNITS TRAP (cost a full debug cycle):** the FBX→USD conversion puts a **0.01 scale on
  the root**, so prim-local space is in **CENTIMETERS**. Any local-space xform op
  (e.g. rotate-about-pivot translate values) must be authored ×100 vs world meters.
  Symptom when wrong: pivots behave as if at origin and changing them does nothing.
- **Hinge pivots (local cm frame), verified by isolated-rotation renders:**
  swing (-85,0,-177) axis Y (slew-ring disc pCylinder16); boom (-120,145,55) axis X
  (pins pCylinder13/114); stick (-120,235,455) axis X (boom-nose/stick-knuckle overlap);
  bucket (-120,-78,518) axis X (stick-tip/link-plate overlap). Rig = per-group op triplet
  translate(pivot) * rotate(angle) * translate(-pivot). Zero pose = folded transport pose.
- Known polish item: hydraulic cylinder rods are rigid with their groups (no length
  animation) — can visually under/over-extend at extreme angles.
- **HINGE-SENSE TRAP (cost 3 verification cycles):** the joint rotation SENSE flips
  between the raw stage and the quarry placement (reference + wrapper rotY(-90)·rotX(-90)
  composing with the FBX-internal orient). In the quarry scene, VERIFIED by telemetry:
  **boom + = down, stick − = extend, bucket + = curl.** Never assume the neutral-stage
  sense carries over — verify with a bucket-world-position printout after posing.
- **Dig interaction VERIFIED (verify_dig.py):** kinematic-RB bucket (trimesh) genuinely
  engages the muck — plunge below grade into the pile, 78 rocks displaced >30 cm
  (settle baseline 10), 1 rock captured+carried through the lift. Capture/pass is low
  with this coarse rock distribution; deeper center passes improve it. Caveats: arm is
  kinematic (infinite force, can kick rocks; slow motions are gentle), stick/boom have
  static-only colliders, no cylinder-length animation.
- Diagnostic that cracked it: print rot-op values + bucket WORLD center per phase —
  exposed both the cm-units pivot bug and the inverted senses in one shot, after
  renders alone had been misread for 3 runs.

## Terrain collision (splat is visual-only!)
- The NuRec splat has NO collision; rocks always rested on AUTHORED invisible boxes
  (BayFloor/BayWall_*). Anywhere else (apron, walls) was collision-less — the arm
  swept through the world until `terrain_collider.usd` was added.
- `terrain_collider.usd` = converted `Vast Quarry Industrial Machinery.mesh.ply`
  (same reconstruction, identity frame — splat USDZ carries NO transform). 360k faces,
  static trimesh (approximation "none"), invisible. Mesh has HOLES (e.g. the bay
  interior — occluded in capture); the authored bay boxes cover those.
- **Drop-test verified** (verify_terrain_collision.py): probes rest on apron/track/edges.
- **SLEEPING-TELEPORT TRAP (caused 2 false-positive test runs):** a rigid body
  teleported via set_world_pose with ZERO velocity stays/falls ASLEEP mid-air (the
  saved muck authors sleepThreshold=0.005 per rock) — it hangs frozen and a lazy
  "didn't fall below floor" check reads as success. Wake it with a non-zero
  set_linear_velocity. Also: fresh session-authored test bodies failed to simulate in
  the re-opened muck scene (cause unconfirmed); use existing file-resident bodies as
  probes instead.

## Force-controlled CAT (the marathon, resolved 2026-06-11)
- **Root cause of the historic 'first-target-only' bug: `rep.orchestrator.step()`
  stops/plays the timeline → articulation physics handles go STALE (documented in
  SingleArticulation.initialize). Fix: `pause_timeline=False` (or re-initialize after
  each snapshot).** Verified: ≤0.5° tracking across successive targets WITH renders.
- Working control recipe (standalone): FSD off (`/app/useFabricSceneDelegate=false`,
  belt-and-braces) → World → SingleArticulation(root_joint) → scene.add → reset →
  set_effort_modes("force") → flush_changes → switch_control_mode("position") →
  set_gains(kp~2-4e7, kd~2-4e4 — kd/kp ≈ 1e-3; BIG kd caps velocity at cap/kd and
  reads as fake 'stalls') → set_max_efforts(real caps: swing 1.5e5, boom 3.5e5,
  stick 2.2e5, bucket 1.2e5 N·m) → flush → set_max_joint_velocities(1.0 rad/s) →
  apply_action(targets) every step.
- Robot asset: `excavator_cat_robot.usd` = URDF import (dest_path! NEVER import into a
  scene file — the importer SAVES configuration sublayers next to / into the open
  stage; it corrupted the muck scene once) + photoreal part grafts under each link
  (X_k = M_cu · W_base · inv(W_k), numeric). URDF needs <visual> on every link or the
  importer mis-structures (collision import verified via INSTANCE-PROXY traversal —
  colliders are instanceable references; default Traverse() is BLIND to them, which
  faked 'zero colliders' three times).
- Contact-pair debugging: PhysxContactReportAPI on links + get_contact_report(),
  decode ids with PhysicsSchemaTools.intToSdfPath IN THE SAME SESSION. This named the
  house-grinding-terrain and bucket-on-debris contacts that telemetry couldn't.
- Scene composition for the dig: terrain trimesh (visual-only splat needs it) +
  graded machine pad under tracks (bench is rigid scan junk) + containment walls at
  the REAL rim height 0.31 (the muck-era +0.6 margin was an invisible fence the arm
  ground against) + reach-over-the-rim dig profile.
- Verified dig dynamics: plunge stalls at boom cap ON the rocks; oversized bite forces
  the bucket open (cap 120 kNm); 67 rocks displaced. Capture needs shallower bites.
  (NOTE: that dig ran with the stale-extent oversized colliders, see below — REVERIFY.)

## The stale-extent night (2026-06-11) — root cause of ALL "phantom contact" bugs
- **THE TRAP: the URDF importer authors collision Cubes as size=1 + xformOp:scale=dim
  but leaves a stale authored `extent` of +-dim/2. BOTH PhysX cooking AND BBoxCache
  read the authored extent -> every collider was effectively dim x dim (a 4.66 m track
  box cooked ~21.7 m; the house an invisible 17.5 m slab REACHING THE GROUND).**
  Symptoms: swing pinned at cap (house slab ground-grinding = ring brake, height- and
  position-independent), early "terrain stops", phantom house<->terrain contact 60/60.
  FIX in build_robot_usd.py: after import, for every collision Cube set size=1.0 AND
  re-author extent=[(-.5,..),(+.5,..)]; assert world-bbox spans match authored dims.
  CONTACT POSITIONS (get_contact_report data .position) were the decisive instrument:
  contact at y=0.2-0.6 where the authored box bottom was 1.71 = impossible -> the
  cooked shape != the authored shape. When telemetry and geometry contradict, dump
  contact POSITIONS, not just pairs.
- **PhysX jointFriction is a COEFFICIENT scaled by the joint's CONSTRAINT impulse**
  (NOT a torque in N*m). A slew bearing's constraint carries the whole upper works ->
  even 0.1 locks the swing. Don't model bearing friction this way (negligible vs
  150 kNm drives anyway). 5e3 "N*m" locked everything solid.
- **Hydraulic-lock control recipe (tested green)**: MOVE gains kp full (2-4e7),
  kd 1-2e5; LOCK gains kp/10 + kd {9e5,1.2e6,5e5,2.5e5}. Full-kp lock saturates the
  cap at 0.4 deg error = bang-bang relay = sustained ~0.4 rad/s limit cycle ("never
  stops wobbling"). kp/10 widens the linear band to ~4 deg (gravity droop ~1.4 deg,
  invisible) and kd overdamps it: <0.01 rad/s within 2 s. ALSO: on key-release SNAP
  the target to current q (valve-centering) — a ramped-ahead target stores spring
  energy and rings.
- **Kit viewport hotkey collisions (GUI)**: W/E/R = gizmo tools, F = frame-selected,
  SPACE = play/pause, H = hide-prim. Use arrows + I/K/O/L + B; POLL RMB state per
  frame (event latches stick ON when the release lands off-viewport -> all arm keys
  die while C still works).
- **TEST THE INPUT PATH ITSELF**: test_gui_controls.py builds the exact GUI control
  stack headless, injects key-held states, and asserts the joints PHYSICALLY move and
  settle. Never hand over an interactive build the test hasn't driven end-to-end.
- **FLOATING BASE (the final realism fix, all-green 2026-06-11)**: a FIXED root joint
  = infinite anchor -> the arm can press with unbounded ground force and TUNNEL the
  bucket through thin colliders, past a box's top face where contact normals flip and
  trap it ("locks right after a collision" — user-reported, reproduced, fixed). Import
  with fix_base=False; ArticulationRootAPI lands on base_link (find root by API, not
  by FixedJoint name); place via holder xform only (+2 cm drop); disable articulation
  sleep (sleepThreshold/stabilizationThreshold = 0 — hydraulic-lock stillness is BELOW
  the sleep threshold and sleeping articulations ignore drive targets). Track grip:
  high-friction pad material (1.2/1.0) with frictionCombineMode=MAX (track colliders
  are instance proxies = unbindable; MAX makes the pad govern the pair). Verified real
  behaviors: full-force press LIFTS the front (force relief = no tunneling possible);
  hard swing shuffles the base ~0.4 m (true tracked-machine creep); machine can pogo
  forward off an undersized pad when slamming (pad is now 7.0 x 4.4 m, real work-pad
  size). Wake-after-contact-rest: PASS (29 deg recovery).
- **HYDRAULIC PRESSURE RAMP (the chassis-hop fix)**: real masses + real torque CAPS
  are not enough — instant +-cap application snatches the 3.3 t arm at ~6 g, whose
  reaction (~200 kN ~ machine weight) HOPS the 21 t chassis (76 cm measured!). Real
  valves ramp PRESSURE: while a joint is commanded, ramp its effort cap 20->100% over
  0.5 s (per-frame set_max_efforts; held joints keep full cap for gravity/load).
  Plus command-rate valve ramp (5->30 deg/s over 0.4 s) and engagement kp/10. Result:
  hop 76.6 cm -> 3.3 cm, all motion/wake/settle tests stay green. Three-layer recipe:
  REAL CAPS (force limits) + PRESSURE RISE TIME (force rate limits) + FLOW RAMP
  (velocity rate limits) = machine that is strong, planted, and feels like hydraulics.

## The pass-through endgame (RESOLVED 2026-06-11 — user captured rocks)
- **Bucket collision = convexDecomposition ON the grafted photoreal mesh** (in
  build_robot_usd.py); the hand-authored URDF scoop boxes are DEACTIVATED on the
  bucket link. Collision now aligned with the visual BY CONSTRUCTION. Proven: a real
  rock rode the bucket through a full swing+carry; the user then dug and carried
  rocks interactively. Box proxies remain only on bulk links (base/house/boom/stick).
- **rocks' physxRigidBody:maxDepenetrationVelocity was 0.5** (muck-settle stabilizer)
  -> solver could not expel penetrations faster than 0.5 m/s -> anything quicker SANK
  THROUGH walls (contacts reported, never resolved). Now 6.0 + maxLinearVelocity 10 +
  maxContactImpulse 2e5 (no railguns), baked into settle_dump/author_save so piles
  settle natively under final params.
- **Muck regraded**: SZMULT 1.15, N 1800 (median ~0.2 m, real fines->boulders power
  law, volume parity with the old 1.71x/600 fill). Fines flow and fill buckets.
- Carry side of the TRUE bucket follows the VISUAL: positive curl (O) = bowl up.
- Stale metrics trap: cavity-center/capture counters tuned to the old box geometry
  reported 0 while a rock was riding — recalibrate metrics after geometry changes.

## Cheap diagnostics that paid off
- **Per-axis displacement** after stepping (mean dx/dy/dz) — instantly reveals wrong
  gravity direction. Far more honest than a Y-only `below_floor` count.
- **Read back authored transforms** from the saved file (no physics) — exposes save bugs
  that in-session reads hide.
- **Triangle census** (`count_rock_polys.py`) — grounds compute claims in measured numbers
  instead of guessed poly counts.

## Performance doctrine (benchmarked 2026-06-12, 1800-rock scene)
- **MEASURE before optimizing**: the pause-test (GUI FPS paused vs running) splits
  physics-bound from render-bound in 10 s. Then A/B each lever headless with a
  standard working sequence + a REALISM GATE inside every variant.
- **USD pose write-back dominates many-body scenes**: 124 ms/step baseline -> 16 ms
  with omni.physx.fabric (7.8x). Solver iterations (32->4), CCD-off, and 60 Hz each
  moved the needle <12% — the solve was never the cost; copying 1800 transforms to
  USD每 step was ~87% of it.
- **Fabric pairing rule**: omni.physx.fabric (physics writes to Fabric) MUST pair
  with /app/useFabricSceneDelegate=true (renderer reads Fabric) in rendered apps,
  or the viewport watches a frozen USD stage. Under Fabric, USD-based pose reads
  (Xformable/ComputeLocalToWorldTransform/BBoxCache) are STALE — use tensor views
  (RigidPrim/Articulation get_world_poses). Never save the stage while Fabric owns
  transforms (the old Fabric/Sdf trap).
- Scenegraph instancing helps RENDER only; physics ignores it entirely.

## USD reference-placement trap (cost a truck-scale debugging loop, 2026-06-12)
Authoring xformOps on the PRIM THAT HOLDS A REFERENCE clobbers the referenced
defaultPrim's own xformOpOrder (they are the same prim after composition; the
attribute has one strongest opinion). An asset whose root carries baked scale/yaw/
ground ops will silently compose at NATIVE size/orientation in any scene that does
holder.AddTranslateOp(). RULE: placement ops go on a PARENT Xform; the reference
lives on a bare child prim. And verify asset transforms by COLD-REOPENING the file,
never by in-session reads (in-session edits mask what was actually saved).
