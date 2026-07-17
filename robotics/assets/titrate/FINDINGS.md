# Titrate FINDINGS -- all measured (probe logs in titrate/)

## OPEN WORK (user will return to this -- do not lose)
T5c: pipetting and burette filling as PERFORMABLE steps. The flask aliquot
and burette charge are currently spawned by fiat. Burette filling is
pouring plus handling (proven physics, just choreography). Pipetting is
the hard half: real aspiration works by atmospheric pressure, which the
particle engine does not model -- needs a researched closure (candidate:
a contact-gated capped-force column model in the tip, like the sorthub
suction gripper) or the real poured-transfer alternative (graduated
cylinder). The user explicitly deferred this and explicitly said they
will come back to it.

## Fluid engine laws at lab scale (PCO = 1 mm PBD water)

1. **Volume calibration**: 1.32 uL/particle, stationary to 0.2% over 40 s
   (T0; fill-height creep decelerates). 50 mL ~ 40k particles.
2. **Rest jitter floor**: 9.5 mm/s mean speed, INVARIANT to solver iterations
   (16->32) and material damping (0->0.2). A property of PBD at this scale;
   its mixing effect = D_num, measured separately (T2b).
3. **Chemistry data path**: USD position readback 0.02 ms, per-particle
   displayColor write 0.01 ms (rendering visually confirmed), cKDTree 50k in
   40 ms -> 5-10 Hz chemistry trivially feasible. Tensor API has NO fluid
   particle view (cloth only) -- USD is the only path, and it suffices.
4. **Spawn-in-skin blast**: spawn margin to a collider must exceed
   restOffset_wall + restOffset_particle (~1.3 mm here); v6 spawned at
   1.2 mm and the t=0 depenetration storm ejected 5301 particles at exactly
   the max_depenetration_velocity cap. Splash-drops and free-fall onto
   sealed tips likewise hammer particles through geometry (T0 v1, T1 v3).
5. **Sub-particle gaps are pressure-relief valves**: PBD particles have no
   hard core; a pressurized column EXTRUDES through any standoff gap
   (0.2 mm gap passed 1.19 mm particles until the head dropped to ~25 mm,
   reproducibly across three versions). Seals must PLUG the channel
   (kinematic-static interpenetration is inert), not cap it at proximity.
6. **TALL-COLUMN GEYSER LAW**: a tall PBD column continuously converts its
   bottom density-constraint violation into velocity kicks. At high
   max_velocity the kicks fountain out of an open bore (v8 ballistics:
   escapees landed at 340 mm median -- impossible from the 0.5 m/s tip, so
   the exit was the TOP at 2-3 m/s; v9: lid + 0.3 m/s cap -> 0 escapes for
   2 s, restoring 3.0 -> 3186 out in 0.5 s). STABILITY REQUIRES a permanent
   max_velocity comparable to the system's real speeds: 1.0 m/s here
   (disclosed: drop impact speeds truncate at 1.0 vs real ~1.4 m/s; dispensed
   volumes and chemistry unaffected; Torricelli verifiable below ~50 mm head).
7. **Pulsed-crack dispensing works and is reproducible** (the honest analog
   of cracking a stopcock; the real 0.2 mm throttle crack is sub-resolution,
   disclosed): 30 ms -> ~57-84 uL, 60 ms -> ~105-115 uL, std 5-15% across
   FIVE independent runs with different (broken!) environments -- the
   dispensing mechanism itself is robust.

8. **Timestep vs seals**: the tall-column kicks defeat a seal by PER-STEP
   DISPLACEMENT, not force: at 240 Hz a 1 m/s kick crosses 4.2 mm/step --
   straight through a 2 mm plate; at 960 Hz (~1 mm/step) the same seal holds
   perfectly (T1 v11: 0 escapes at full head, cap 1.0). Gram-scale contact
   needed 1 kHz in pencap; mm-scale fluid seals need it too.
9. **Stale-frame snapshot law**: with physics at 960 Hz and rendering_dt 1/60,
   a render only happens every 16 physics steps -- a step-based snapshot of
   fewer steps returns a STALE image (all 'blank drop' frames; the particles
   were IN the window, counted 111). Snapshots must call world.render()
   directly (also freezes fast events properly). USD audits, logs, AND frames
   can each lie in their own way; cross-check them.
10. **Droplet morphology at 1 mm resolution** (dropcam, verified frames): a
    60 ms crack's ~130 uL slug breaks up in flight into several coherent
    5-25 uL droplets (capillary breakup, cohesion-bound clusters) -- real
    dripping is 2-3 x 50 uL drops; same order, finer breakup, disclosed.
    Dispensed VOLUME (what the chemistry sees) is exactly calibrated.

11. **D_num measured (T2b PASS)**: the resting PBD fluid's intrinsic mixing
    diffusivity is 1.20e-7 m^2/s (MSD fit R2=0.999) == 1.25e-7 by the
    independent tracer-variance method (x1.04 agreement). ~13x molecular H+,
    ~90x Na+ -- the 'still' sim liquid mixes like a gently stirred real one;
    swirl advection dominates both. The chemistry's explicit exchange uses
    D_eff = 1.2e-7 to mirror particle self-diffusion (disclosed hosting).
12. **Handling blunders reproduce physically (T3 v4)**: swirling the flask
    at a 14 mm orbit -- exactly the neck's inner radius -- under a fixed
    burette tip put the falling drop line ON the moving neck wall, and the
    sim poured titrant down the OUTSIDE exactly as a real bench would (floor
    verified clean at start; spill arcs on the bench by pulse 10; permanent
    pink stains where spilled base met spilled analyte, since bench pairs
    never meet the acid bulk). The spill poisoned telemetry (end-of-mix pink
    pinned at 8%, strat dz dragged negative by z=0 particles) and locked the
    protocol drop-wise. Fix is the real chemist's technique, not a sim tweak:
    DISPENSE-THEN-SWIRL (flask spiraled to center on a smooth amplitude ramp,
    crack stationary, drops land, then mix), interior-masked telemetry, and a
    zero-spill verifier gate (a real spilled titration is discarded).
    Corollary: kinematic swirl on/off must RAMP amplitude -- a step jump
    teleports the wall 14 mm through the fluid in one step.
13. **KERNEL-FLOOR MIXING LAW (v5 vs v6, a controlled falsification)**: with
    a 2 mm exchange kernel, a titrant filament cannot homogenize faster than
    kernel^2/D_eff (33 s at the measured resting D_eff = 1.2e-7) NO MATTER
    HOW the flask is stirred: steady circular swirl (v5) and blinking-vortex
    chaotic swirl (v6) gave the SAME end-of-mix pink after identical coarse
    slugs (9.7% vs 9.3% after 9 s). Advection styles differ only below the
    kernel scale, which the exchange cannot see. A real bench clears in
    seconds because real turbulence stretches filaments to ~50 um where
    molecular diffusion finishes in ~0.3 s -- unrepresentable with 1 mm
    particles. Honest closure (v7): LES-style eddy diffusivity, D_eff rising
    from the measured resting 1.2e-7 to 3e-6 m^2/s while the flask swirls
    (amplitude-scaled; conservative vs real stirred-vessel 1e-5..1e-4;
    within the exchange stability clamp). At rest the measured value rules,
    preserving the real stratification physics v3 discovered.
14. **Landing-spray spill (v6 phase-split telemetry; falsified my own
    'swirl-phase fling' story)**: the residual ~6-particle-per-pulse bench
    spill happens entirely during the LAND phase (pulse 2: land 0.013 ->
    end-of-mix bench 0.013, zero growth across 9 s of swirl) -- in-flight
    breakup spray from a 35 mm fall above the mouth can clear the 14 mm rim.
    My energy argument ('cap 1.0 m/s cannot climb 100 mm') was right about
    the pool but blind to the falling stream. Fix is the real bench
    technique: the tip sits 3 mm above the flask mouth (v7) -- from there
    spray cannot geometrically reach the rim. LESSON RE-LEARNED: an
    energy argument about one path says nothing about the others; get
    phase-resolved telemetry BEFORE naming a mechanism.

15. **STOPCOCK FLOW CURVE MEASURED (t4c ladder, 960 Hz seal physics)**: plug
    slide <= 7.7 mm passes 0.000 mL/s (collision skins eat the geometric
    crescent); 8.1 mm = 0.003 mL/s (true dropwise, one drop/~25 s); 8.6 mm =
    2.34 mL/s (stream); 11 mm = 2.62 mL/s (full bore). The drip->stream
    transition spans ~0.4 mm -- sharper than a real tapered stopcock because
    1.2 mm particles quantize the aperture (disclosed). The interactive
    knob is therefore GEARED like a needle valve: 0-30 deg dead zone,
    30-80 deg stretched over the measured live band, 80-90 wide open.
16. **Rigid-body corollaries of the spawn-blast law (t4b settle audits,
    5 runs, 20->14 objects all within 10.7 mm)**: (a) DEFAULT rigid contact
    offsets (~2 cm) swallow any mm-scale spawn clearance -- objects spawn
    inside neighbors' skins and get depenetration-popped (one random bottle
    launched per run until explicit contactOffset 2 mm / restOffset 0);
    (b) PhysX cooks cylinders as faceted prisms -- facet-edge landings rock
    tall bottles over unless the mass model is honest (a FILLED bottle's low
    center of mass is what keeps real bottles standing; +grippy zero-
    restitution glass-on-epoxy contact material); (c) a LOOSE cap dropped
    on a bottle mouth rolls away in sim exactly as in reality -- real caps
    are SCREWED ON, so cap+bottle are modeled as the one rigid body they
    physically are.

## Chemistry layer (pure numpy, T2a: 9/9 units PASS)

- Reaction conservation exact; diffusion conserves to 1e-20 and matches the
  two-particle analytic decay to every digit; indicator == Henderson
  equilibrium; 0-D endpoint walk crosses at 25.05 mL (one drop past 25.00,
  as chemistry demands); full chem step on 40k particles = 137 ms (~7 Hz).
- Two T2a first-run failures were WRONG TEST EXPECTATIONS (a physically
  absurd relaxation-time demand; a 2x slip in my hand analytic) -- the code
  was right. Tests must respect the physics they test.

## T5a RESULT: the PHYSICAL bench PASSED (8 runs of forensics, all gates)

Contact is now the only thing that moves the valve: pinch-pads (robot-finger
stand-ins) turned the jointed stopcock lever to 75 deg -> 3.51 mL/s flow
(x3 reproducible); released at 40 deg it HELD (drift 0.0 deg); pushed back
to 6 deg the flow stopped (0.000). Magnetic stirrer + stir bar replace the
ghost-swirl (slug pink 2.9% -> 0.0% in 10 s). Graduated scale read against
the glass agrees with the particle count to 0.04-0.12 mL. New laws:

17. **MECHANISM LAWS**: (a) a lever with its center of mass off the hinge
    axis is an INVERTED PENDULUM -- gravity slams it to a joint limit in
    ~0.1 s whenever ungripped, and kinematic caging MASKS the instability
    (five runs chased 'release kicks' that were really the pendulum; the
    preload-discharge theory was falsified by the two-stage release test).
    Real stopcock keys are symmetric about their axis -- model them so.
    (b) physxJoint:jointFriction is INERT on a plain revolute joint here;
    a damping-only angular drive (stiffness 0) is the brake that works.
18. **Calibrate-to-deliver (like real volumetric ware)**: PBD wall exclusion
    in the 11 mm bore makes liquid stand 11.53 mm/mL vs the geometric
    10.52 -- print the scale at the MEASURED pitch. Also: spawn density is
    ~half settled density (a single spawn pass through the tube caps at
    ~20 mL), so fill by VOLUME; the honest protocol fix for the smaller
    charge is a 10.00 mL aliquot + dilution water (textbook practice --
    dilution changes concentration, not moles; V_eq invariant).
19. **READ-AFTER-WAITING LAW**: a fast drain leaves the upper column
    transiently decompacted (fifths measured 102/99/67/36/0% full); it
    recompacts within ~20 s to a sharp surface, after which the scale delta
    matches the dispensed count (+3.38 vs 3.30 mL). The sim thus enforces
    the real analytical rule: wait ~30 s for drainage before reading a
    burette. Read immediately and the instrument honestly misleads you.

20. **COLUMN CRYSTALLIZATION (t5d V6 diagnosed by MEASURING then LOOKING —
    the user forced the looking, and it changed the answer)**: after rapid
    draining, the burette's upper column does not subside — it LOCKS into a
    loose ORDERED SQUARE LATTICE (seen at full resolution: neat rows with
    visible gaps; the packed bottom shows irregular close-packing). Density
    measured 54% of settled, over ~6 cm, relaxing at only ~0.2 mL/min —
    stable on any chemist timescale because a lattice jammed against the
    glass in a ~9-particle-wide bore has no thermal agitation to melt it.
    Real water cannot do this (its particles are thermal molecules); this
    is a DISCRETENESS ARTIFACT of 1.2 mm particles in an 11 mm bore — the
    liquid fails toward granular behavior, and granular media in narrow
    tubes genuinely do crystallize. Consequence: the graduation scale is
    exact on a settled column (0.04–0.12 mL) and reads LOW after fast
    drains (t5d: delta 5.21 vs 10.41 true — the famous exact-half, which
    is the lattice's density ratio showing up in the level arithmetic).
    Prior wrong theories, both killed by evidence: wall-film stragglers
    (falsified by the density read), 'froth' (falsified by the lattice
    image — froth is disordered; this is a crystal). Possible honest
    mitigation, unbuilt: a physical TAP on the glass (real chemists' move,
    melts exactly this jam). Until then: intermediate scale readings after
    fast dispensing are disclosed as biased; settled readings are exact.

21. **Kinematic-vs-static A/B on the column lattice**: with a STATIC tube
    the post-drain lattice reproduces bit-identically (3/3 runs: same
    ...,74,55,54,54,53,12 profile, delta +8.70); with the tube flagged
    KINEMATIC (same shape, never moved) the column packs correctly
    (98-102%, delta agrees with count to 0.19 mL, 1/1). The particle
    contact path against kinematic bodies evidently provides the micro-
    agitation the static path lacks. A solver-path accommodation, not a
    physics change — candidate remedy alongside the researched cohesion
    calibration (in progress: Tate's-law pendant-drop anchor ~80 uL for
    the 3 mm tip; zero-yield-stress requirement; preset cohesion 0.01 was
    never verified against drop physics — a gap in the original research).

22. **COHESION RESPONSE IS FLAT — the tensile deficiency is STRUCTURAL
    (t5g calibration ladder, 4 points across 2 orders of magnitude)**:
    Tate-anchor drop test (real water from our 3 mm tip: ~80 uL pendant
    drops, one every ~3 s at the measured feed) at cohesion 0.01 / 0.05 /
    0.2 / 1.0 gave continuous dribble at EVERY value (3.42-3.89 mL seeped
    in 120 s with at most one momentary break; 100x baseline seeped MORE
    than baseline). No cohesion value produces pendant-drop formation at
    1.2 mm particle scale: drops need a neck sustained under tension, and
    the PBD density constraint is one-sided (resists compression, ignores
    stretching). CONSEQUENCE, proven not presumed: the water cannot be
    made 'more watery' on the tensile axis by parameter choice — the
    engine internals are closed (GPU particle kernels binary-only), so
    calibration was the only formal route, and it returned a negative.
    The mitigations are therefore conclusions, not conveniences:
    (a) kinematic-collider tube prevents the drained-column lattice (law
    21, A/B 3/3 vs 1/1); (b) the modeled tap (t5f) melts residual jams;
    (c) scale readings trusted on settled columns only (law 19). Kept
    real: dispensed VOLUMES stay exactly calibrated (T0/T1) — what is
    unreal is drop MORPHOLOGY at the tip and column tensile behavior,
    both now documented with measurements.

## T5d RESULT: the FULL ONE-PIECE titration on the physical bench

Pads gripped the stopcock lever ONCE (hand-on-stopcock technique) and the
V_eq-blind chemist protocol ran the whole experiment through the physical
chain: pads -> lever joint -> plug -> flow -> stirred flask. 12 additions,
coarse ~1 mL splashes repeatable to +-0.05, pH ON the analytic curve
throughout (measured 10.77 at 10.10 mL vs analytic 10.8), first flash at
5.86 mL, knee caught at 9.76 mL (downshift), whole-flask permanent pink at
10.41 mL. Verifier: conservation OK, flashes OK, overshoot permanence OK,
zero spill OK (0.044 mL one-time first-crack spray, frozen across the run).
TWO HONEST FAILURES, both informative:
- V1 endpoint 10.41 vs 10.00 (+0.41, gate 0.35): the OPERATOR's smallest
  splash is ~0.3 mL (the controller sweeps past the drip band) -- a clumsy
  chemist SHOULD overshoot, and the sim correctly measured it. The world
  supports finer technique (0.003 mL/s dropwise at a held angle, T5a). Not
  reran to green: that would be grinding the task, not building the sim.
- V6 scale delta +5.21 vs count 10.41: after ~12 open/close cycles the
  upper column holds a PERSISTENT partial-density froth/arch zone that the
  meniscus read mistakes for liquid (single-drain reads agreed to 0.08 mL;
  law 19's 30 s wait no longer suffices). OPEN SIM QUESTION: profile the
  post-titration column, find the real relaxation time or a read that
  rejects the froth band (real chemists also tap the glass).

## T3 RESULT: the full emergent titration PASSED (v7, all 5 gates)

- 20.00 mL of 0.100 M HCl + phenolphthalein, titrated by a V_eq-blind
  three-speed chemist protocol from a real-geometry burette. ENDPOINT at
  20.060 mL vs analytic 20.00 -- ONE 70 uL drop past equivalence, which is
  exactly where chemistry puts a phenolphthalein endpoint (indicator turns
  at pH 8.2, reached one drop after V_eq). Class-A glassware gives +-0.05 mL;
  we read +0.06.
- The one-drop equivalence slam, measured: at 20.014 mL (14 uL past V_eq)
  bulk pH jumped 3.21 -> 9.07; the next 70 uL drop -> 10.20 and 94% pink;
  30 s swirl hold -> 100% pink (V4 overshoot permanence 100%).
- The whole pre-equivalence shelf tracked the analytic curve (e.g. measured
  pH 3.21 at 19.755 mL vs analytic 3.21). Protocol downshifts fired off real
  signals only: MEDIUM at 19.52 mL (extensions maxed with 3.1% residue),
  DROP-WISE at 20.014 (50% residue). Zero spill in 27 landings (V5); exact
  conservation (V2, dNa 4e-19). Curve figure: t3_curve.png; log preserved
  t3_v7_PASS.log.
- HONEST GAP: the endpoint FRAME does not show the pink -- the flask mesh
  renders opaque (displayColor opacity is ignored by the RTX path). The
  color proof is per-particle telemetry + the curve; a real glass material
  (UsdPreviewSurface) is the T4 fix. The bench IS visibly clean (V5 by eye).

## Process laws (reaffirmed)

- The forensic ladder works: every T1 failure was diagnosed by MEASUREMENT
  (escape counts, radii percentiles, landing ballistics), not by guessing.
- Frames must be looked at: the v4 "seal failure" was visibly a ground
  covered in sprayed droplets -- a different failure than the log suggested.
- Watchdogs on every background run (CLAUDE.md rule 11, proven necessary).
