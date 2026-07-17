# TITRATION — research dossier (pass 1+2: literature + engine archaeology)

Goal: a physically faithful acid–base titration in Isaac Sim. The HACK to refuse:
"if the liquids are close / in the same container, apply the titration result."
The faithful version: the endpoint EMERGES from per-particle chemistry + real
fluid mixing, and every observable (drop, flash, permanent pink, endpoint
volume) is a measurable physical signature — the pen-cap doctrine applied to
liquids.

## 1. What REALLY happens in a titration (ground truth)

Apparatus (verified specs):
- 50 mL Class A burette: tolerance ±0.05 mL, 0.1 mL graduations, ~77 cm tall,
  PTFE straight-bore stopcock (ASTM E287 / DIN ISO 385). One DROP ~0.05 mL —
  the standard endpoint increment ("add drop by drop near the endpoint").
- Erlenmeyer flask (125–250 mL) with ~25.00 mL analyte, swirled by hand.

Chemistry (the canonical strong–strong case):
- 25.00 mL of 0.100 M HCl + phenolphthalein, titrated with 0.100 M NaOH.
- Equivalence: V_eq = C_a·V_a/C_b = 25.00 mL exactly.
- H+ + OH- -> H2O rate constant k = 1.3x10^11 M^-1 s^-1 (Eigen; the fastest
  known aqueous reaction, diffusion-controlled). At 0.1 M the reaction
  half-life is ~1e-10 s << any timestep ==> the reaction is INSTANTANEOUS at
  any resolvable scale; MIXING is always the rate-limiting physics. This is
  the scientific licence for "instantaneous local neutralization" and the
  core argument for a simulation that RESOLVES MIXING SPATIALLY.
- Phenolphthalein: colorless below pH 8.2, pink 8.2–10.0 (pKa ~9.4).
  Textbook endpoint criterion: "faint pink persists ~30 s".
- The one-drop discrimination is REAL and resolvable: at 24.95 mL NaOH the
  flask is pH ~4.0; at 25.05 mL it is pH ~10.0 (excess 1e-4 M either side).
  One drop crosses the entire indicator range. A faithful sim can and must
  reproduce endpoint detection to ±1 drop (±0.05 mL).
- The famous TRANSIENT PINK FLASH: before the endpoint, where a drop lands,
  the LOCAL fluid is momentarily basic -> pink streak that vanishes on
  swirling. This is a spatial phenomenon that no bulk-pH model can produce —
  it is our "click": the observable that only emerges if the physics is real.
- Neutralization enthalpy −57.1 kJ/mol -> ~+0.34 K bulk temperature rise for
  this titration (optional extra verification channel).
- Molecular diffusivities: D(H+) ~9.3e-9, D(OH-) ~5.3e-9, D(Na+) ~1.3e-9
  m^2/s. Across a 1.2 mm particle spacing, pure molecular diffusion needs
  ~minutes ==> ADVECTION (swirling) dominates mixing, physically and in-sim.

## 2. Prior art map (who did what, what they faked)

- **Chemistry3D** (arXiv 2406.08160; Isaac Sim): THE closest prior work — and
  the sophisticated version of the hack. Liquids are PhysX particle visuals;
  reactions TRIGGER on center-of-mass contact + a 65-reaction DATABASE; pH,
  color (UV/Vis->RGB), temperature are COMPUTED PROPERTIES applied to the
  whole liquid; kinetics is a fitted exponential. No spatial chemistry, no
  local flash, endpoint would be a lookup. Valuable as engineering reference
  (they colored Isaac particle fluids and poured them); not fidelity.
- **VR chemistry labs** (Labster, MEL, PraxiLabs...): scripted/bulk models;
  titration trainers explicitly use plain water + animated color.
- **FluidLab** (ICLR'23) / **SoftGym**: real fluid manipulation benchmarks
  (Taichi MPM / NVIDIA Flex) — fluids without chemistry. Confirm fluids-for-
  manipulation is established; no reaction layer.
- **Genesis** (2024, open source): unified MPM/SPH/PBD engine, very fast —
  the strongest ALTERNATIVE ENGINE if PhysX PBD fails us; cost = abandoning
  our validated Isaac robot/apparatus stack. Keep as fallback.
- **Ren et al. 2014, ACM TOG, "Multiple-Fluid SPH Using a Mixture Model"**:
  the METHOD PRECEDENT — per-particle volume fractions, inter-particle
  diffusion, demonstrated MIXING and CHEMICAL REACTION inside a particle
  fluid. Establishes that per-particle species + neighbor exchange is
  standard simulation methodology, not a hack. (Full PDF paywalled; abstract
  + project page confirm scope. Our formulation: conservative antisymmetric
  Fickian exchange, unit-tested from first principles regardless.)
- **ChemGymRL**: RL bench chemistry with abstract vessels — no spatial fluid.

**The gap we fill**: nobody couples a real-time particle fluid to spatially
resolved reaction+indicator chemistry with measured verification. That is
the titration equivalent of the pen-cap snap-fit.

## 3. Engine archaeology (verified LOCALLY in Isaac Sim 5.1, this machine)

- `omni.physx .../scripts/particleUtils.py` — full PBD fluid stack:
  - `add_physx_particle_system(...)`: contact_offset, rest_offset,
    particle_contact_offset (PCO), solid/fluid rest offsets, CCD, solver
    iterations, max_velocity, max_neighborhood (default 96), wind.
  - `add_pbd_particle_material(...)`: friction, viscosity, surface_tension,
    cohesion, adhesion, drag, lift, vorticity_confinement. WATER PRESET in
    the file: cohesion 0.01, surface_tension 0.0074 (SI-scaled by mpu^3),
    viscosity 0.0000017/mpu^3.
  - `add_physx_particleset_points(...)`: particle sets as **UsdGeom.Points**
    with per-particle positions/velocities/widths; fluid flag; particle
    group; mass/density. Points = our chemistry state carrier.
  - anisotropy / smoothing / **isosurface** helpers (render-only).
- Offset architecture (Omniverse docs, verified against local API): PCO
  drives everything — fluidRestOffset = 0.99*0.6*PCO; neighbors within
  2*PCO; defaults assume ~5 cm scale ==> mm-scale lab fluids are OFF-DEFAULT
  territory (probe!).
- **Tensor-API gap (verified)**: `omni.physics.tensors` ParticleSystemView
  exposes only system params; per-particle positions/velocities exist ONLY
  for particle CLOTH. ==> fluid particle state must go through USD.
- **`/physics/updateParticlesToUsd`** setting exists (verified in
  `_physx.pyi`; also updateVelocitiesToUsd) ==> per-step particle positions
  (and velocities) are written into the Points prim; numpy reads them.
- **Warp 1.8.2** ships as `omni.warp.core` extension (GPU kernels available
  in-process if numpy neighbor search is too slow).
- Particles are GPU-only (no CPU fallback); different particle SYSTEMS do
  not collide ==> ALL liquids (analyte + titrant) must live in ONE particle
  system (and thus one PBD material — same viscosity/ST for both: fine and
  honest for dilute aqueous solutions).
- Isosurface extracts ONE mesh per system with ONE material ==> per-particle
  COLOR (the whole point) is lost under isosurface. Default rendering =
  Points/instancer with per-particle displayColor; isosurface only for
  beauty shots. Disclosed trade.

## 4. Architecture (chosen)

**Mechanics**: PhysX PBD particle fluid (one system). Glass apparatus as
revolve-profile SDF colliders (our proven builder): burette (with real
stopcock: a revolve plug with a cross-bore, revolute-jointed — flow gated by
real geometry), Erlenmeyer flask, stand. Swirling: kinematic flask motion
first (pencap hand-guide pattern), robot later.

**Chemistry (the new layer, operator-split at 5–20 Hz)**:
per particle i (fixed volume V_p): moles n_H, n_OH, n_Na, n_Cl, n_Ind.
1. ADVECTION: free — particles move with the PBD flow.
2. DIFFUSION: for neighbor pairs (i,j) within h: antisymmetric Fickian
   exchange dn = D_eff * (c_i - c_j) * w(r_ij) * dt (conservative by
   construction). Molecular D is negligible at particle scale; D_eff is the
   HONEST HOSTING of sub-particle mixing (like pencap's per-nub K) —
   calibrated, small, disclosed.
3. REACTION: dn = min(n_H, n_OH); n_H -= dn; n_OH -= dn (justified: k =
   1.3e11 ==> instantaneous at any resolvable scale). Track heat optionally.
4. pH per particle from net excess (H or OH, via Kw); indicator pink
   fraction f = 1/(1+10^(pKa - pH)), pKa 9.4; per-particle displayColor =
   lerp(solution color, pink, f * has_indicator).
Neighbors: scipy cKDTree at low cadence -> Warp hash grid if needed.

**Instrumentation**: dispensed volume = particles-passed-the-valve x V_p
(ground truth) AND burette column height reading (the "meniscus" instrument,
with its real ±0.05 mL class-A error) — comparing the two MODELS the
instrument error honestly.

## 5. Feasibility arithmetic (first principles, to be probe-verified)

- PCO 1.0 mm -> fluidRestOffset 0.594 mm -> rest spacing ~1.2 mm ->
  ~0.9–1.7 uL/particle -> 50 mL total liquid = ~30k–60k particles. PhysX PBD
  routinely runs 100k+ on a 3090 ==> comfortable.
- One drop 0.05 mL = ~30–60 particles — enough for a coherent pendant drop.
- Chemistry cadence 10 Hz on 50k particles: cKDTree build ~50–100 ms (numpy)
  == borderline -> chemistry every 0.1–0.2 s sim-time is fine (mixing
  timescale is seconds); Warp upgrade path if not.
- USD readback (50k Vec3f) + displayColor writeback per chemistry step:
  ms-scale, fine.
- Moles per particle at 0.1 M: ~1e-7 mol — float64 arrays, no precision issue.

## 6. The VERIFIER (what "titrated" means, physically)

1. **Endpoint emergence**: dispense drop-wise with swirling; endpoint =
   whole-flask pink persisting >30 s (the textbook criterion, applied to the
   sim's own color state). PASS iff |V_endpoint - V_eq| <= 0.05 mL (1 drop).
2. **Conservation invariants** (machine-checked every chemistry step):
   total Na+ and Cl- constant; H+ consumed == OH- consumed; charge balance.
3. **The flash falsification test**: before endpoint, a drop WITHOUT
   swirling must produce a LOCAL pink patch that persists (stratified);
   swirling must clear it. A bulk-pH model cannot pass this.
4. **Overshoot permanence**: +1 drop past endpoint -> pink everywhere,
   permanently.
5. **Flow physics**: valve-open efflux vs head must follow Torricelli
   scaling; drop volume ~0.05 mL at the real tip geometry (tolerance
   disclosed after T1).
6. **Titration curve**: log bulk pH vs dispensed volume; overlay the
   analytic strong-strong curve — shape match through the equivalence jump.

## 7. Probe ladder (pencap-style; each gated by numbers + looked-at frames)

- T0a fluid calibration: block in a box at PCO 1.0 mm — uL/particle, rest
  density, settle stability, SDF-glass leak test (hours-long soak).
- T0b throughput: 50k particles — readback rate, color write rate, kdtree ms.
- T0c pour/containment: fill flask, tip it kinematically: no leaks, volume
  conserved, splash plausibility.
- T1 THE DROP: burette tip + stopcock geometry; measure drop volume/rate vs
  cohesion/surface-tension; Torricelli check at full open; valve-clog map
  (orifice must be >= ~3 particle diameters).
- T2 chemistry units: two-particle diffusion (analytic decay), reaction
  conservation, indicator color-vs-pH curve overlay.
- T3 static titration end-to-end (kinematic dispensing + swirl): verifier
  items 1,2,4,6 + the flash test 3.
- T4 interactive scene: user drives valve + swirl (falsifiability keys).
- T5 robots (pencap R-lessons apply: stock Franka, no runtime jaw fittings —
  articulation shape-freeze law! — object-side geometry only): turn the
  stopcock, swirl the flask, read the endpoint by camera.

## 8. Risks / open questions (all probeable, none blocking)

1. PBD cohesion/surface-tension is approximate — pendant-drop pinch-off
   fidelity unknown (T1). Fallback: drop size set by real tip geometry is
   still emergent; deviation measured and disclosed.
2. mm-scale PCO stability/perf: PhysX particle defaults assume ~5 cm scale;
   nobody documents 1 mm lab scale (T0a). Fallback: PCO 1.5–2 mm costs
   volume resolution (still ~15k–25k particles, 1 drop ~8–15 particles).
3. Valve clogging at small orifices (T1); design orifice >= 3 particle Ø.
4. Single-system constraint: titrant/analyte share a PBD material — fine
   for dilute aqueous; disclosed.
5. Per-particle color only in points rendering (isosurface loses it) —
   points default; look-dev later.
6. USD readback is the only fluid-state path (tensor API gap verified) —
   throughput probe T0b; Warp fallback.
7. Glass rendering (refraction) vs seeing the particles — thin-shell glass
   material, camera through the wall; probe visually.
8. Chemistry cadence vs fast advection: operator splitting at 5–20 Hz is
   standard; the mixing timescale (~1 s) is far slower.

## 9. Sources

- Chemistry3D: arxiv.org/abs/2406.08160 (+ GitHub huangyan28/Chemistry3D)
- Omniverse particles: docs.omniverse.nvidia.com/kit/docs/omni_physics/latest/dev_guide/particles/particles.html
- PhysX 5 ParticleSystem: nvidia-omniverse.github.io/PhysX/physx/5.4.1/docs/ParticleSystem.html
- Ren et al. 2014 TOG multiple-fluid SPH: dl.acm.org/doi/10.1145/2645703
- FluidLab: arxiv.org/abs/2303.02346 ; Genesis: github (Genesis-Embodied-AI)
- H+/OH- rate constant: ScienceDirect neutralization overview (1.3e11 M^-1 s^-1, Eigen)
- Phenolphthalein range 8.2–10, faint-pink-30s criterion: chemistry education refs
- Class A burette ±0.05 mL, 0.1 mL grads (ASTM E287/ISO 385): Eisco/CalPac specs
- LOCAL (verified this machine): particleUtils.py APIs + water preset;
  omni.physics.tensors api.py (no fluid-particle view); _physx.pyi
  (updateParticlesToUsd); omni.warp.core 1.8.2 present.
