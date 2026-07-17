# LEGO simulation findings

Status: active implementation and falsification log. Every force, coefficient,
and tolerance below is a simulation prior unless explicitly identified as a
physical measurement. No real LEGO force curve has yet been supplied.

## Accepted architecture

The repository now uses two deliberately separate representations.

### Geometry truth

The P0/P1 calibration path keeps the bricks as independent rigid bodies. There
is no pose snap, brick attachment, collision deletion, connected-state flag, or
inter-brick constraint. Local watertight GPU SDF meshes represent studs and
tubes; convex components represent walls and the broad support surfaces.

Stud/tube/wall interfaces use a force-based compliant material. Broad support
uses the implicit rigid PhysX constraint because a real ABS top plate's elastic
compression under the target load is below the resolved collision scale. The
2x2 mass prior is 1.18 g. Only the P0 virtual test-carriage experiment raises
the driven equivalent mass by 0.30 kg; exported brick assets keep 1.18 g.

### Long-horizon episode model

Native SDF contact physically performs the insertion. Only after all three
conditions below are measured may the runtime create the force-limited D6
connector:

- the assembly metric is seated;
- seat error is no greater than +0.05 mm;
- the lower-brick contact history contains at least 5 N.

The joint anchor is the brick's current measured pose, so activation begins
with zero constraint error. X/Y and all rotations are held; Z remains free and
is acted on by an implicit 18 kN/m, 0.15 N s/m drive capped at 2.67 N. Collision
remains enabled. No body pose is written. This is a transparent reduced-order
clutch for episode dynamics, not the geometry-calibration truth model.

## Direct-contact numerical identification

With a 3 kN/m force-based spring per generated interface contact point and
0.1 N s/m damping, the aligned 2x2 probe at 5 mm/s produced:

| Profile | dt | SDF | TGS position iterations | Peak insertion | Peak pull | Minimum upper-bottom z |
|---|---:|---:|---:|---:|---:|---:|
| interactive | 1/480 s | 256 | 32 | 19.88 N | 2.68 N | 9.377 mm |
| calibration | 1/960 s | 512 | 64 | 20.78 N | 2.67 N | 9.575 mm |

Peak insertion and pull differ by about 4.3% and 0.4%. That is not full
convergence: insertion work differs by about 35.9%, removal work by about 7.1%,
and the minimum-Z seat location by 0.199 mm. The 240 Hz/SDF 128 profile tunnels
and is unsuitable for connector mechanics. `traces/p0_convergence.json`
therefore correctly reports `overall_converged: false`.

The raw negative PhysX contact `separation` is preserved in traces but is not
treated as material deformation. Convex margins and SDF contact construction
can make it much larger than the measured support sink.

## Calibration perturbation matrix

The calibration profile used SDF 512, 960 Hz, 64 TGS position iterations, a
25 N fixture limit, and 5 mm/s motion in every case:

| Case | Peak insertion | Peak pull | Insertion work | Removal work | Minimum z |
|---|---:|---:|---:|---:|---:|
| aligned | 20.775 N | 2.669 N | 11.102 mJ | 2.289 mJ | 9.575 mm |
| +0.25 mm X offset | 20.308 N | 1.483 N | 11.514 mJ | 0.185 mJ | 9.577 mm |
| +1 degree X tilt | 21.116 N | 2.729 N | 6.494 mJ | 1.527 mJ | 9.575 mm |

All runs were finite and reached the fixture's axial seat band. Removal work is
far more sensitive than peak insertion force, which is why validation cannot be
reduced to one force maximum.

## LEGO-scale PhysX findings

PhysX defaults are not neutral at this scale. The default 40 mm friction offset
and 25 mm correlation distance are larger than a 15.8 mm 2x2 brick. The profiles
now use explicit friction offset thresholds of 0.20/0.10/0.04 mm for
fast/interactive/calibration and a 0.50 mm correlation distance. This prevents a
single metre-scale friction patch from silently spanning the part.

That correction improved native post-press rebound only from roughly 0.371 mm
to 0.354 mm. A native ABS static-friction sweep from 0.20 to 0.30 was nearly
flat. Together with the changing SDF contact population, this indicates that
the residual retention error is contact-patch turnover/static-friction loss,
not simply a low Coulomb coefficient.

Compliant contact is useful for resolved stud/wall interference, but a stiff
explicit spring on a broad face is the wrong numerical representation for a
1.18 g free part at 480 Hz. Rigid support plus compliant local interfaces is the
stable resolved-scale split.

## Guided press and connector backend evidence

The workcell press is a 0.30 kg rigid ram with X/Y and rotation locked, Z driven
by finite impedance, and a 28 N ceiling. Four closed convex guide walls taper
over 12 mm from 1.60 mm total capture clearance to a 0.12 mm throat, constraining
translation and yaw without making the upper brick kinematic.

The current strict activation trace
`traces/press_cycle_interactive_strictgate_v2.json` passes:

- peak measured lower contact: 17.559 N;
- D6 activation seat error: +0.039 mm;
- final seat error after unload: +0.057 mm;
- final engagement: 1.643 mm;
- collision enabled and `pose_write: false`;
- finite state throughout.

An earlier D6 run reached a +0.002 mm activation seat and finished at +0.024 mm;
another loose-gate trace activated at +0.097 mm and finished at +0.118 mm. The
latter is useful historical evidence but would now be rejected by the +0.05 mm
activation gate.

A diagnostic breakable fixed joint could hold when its scalar break force was
raised to 1000 N, proving that deferred creation at the current pose was stable.
It was rejected as the episode model because a fixed joint couples radial and
axial capacity: one scalar break threshold cannot represent a laterally stiff
but 2.67 N axial clutch.

## Robot evidence

The staged Franka probe uses RMPflow for the arm, physical prismatic finger
drives, measured contact impulses, and no transport attachment.

- Open-finger reach passes with about 0.94 mm target error in the recorded D6
  run.
- Grasp/lift passes: contact occurs during closure, actual opening is 15.603 mm,
  lift is 34.839 mm, and tracking error is 0.218 mm.
- The guided press has physically seated the part in earlier autonomous runs,
  but native contact rebounds by about 0.36 mm during unload.
- `robot_assemble_interactive_v27_d6.json` reached and passed reach/grasp but
  rejected activation under an obsolete seat gate.
- The follow-up v28 run was interrupted during fine alignment by a 30-minute
  infrastructure timeout while an unrelated Kit process was consuming CPU. It
  did not produce evidence of a connector failure, but it also did not produce
  an end-to-end success trace.

Runs v29-v31 exposed and localized a real straight-guide failure. The robot
release left about 0.85 degrees yaw. The loose straight skirt centered XY but
lower studs then contacted the upper inner-wall colliders. A low-force preload
did not fix it; additional stroke triggered the 5-degree alignment safety stop.
The same XY/yaw state reproduced the jam and non-finite unload in the focused
rig. Replacing the skirt with a tapered physical die made that exact reproduction
pass at +0.046 mm seat, 1.654 mm engagement, and 20.97 N peak contact.

`traces/robot_assemble_interactive_v32_tapered_die.json` is the first clean
combined pass:

- reach error 0.94 mm and physical 34.84 mm grasp/lift;
- pre-insert planar error 0.137 mm;
- contact-loaded press seat +0.025 mm at 19.329 N;
- deferred D6 activation with collision enabled and `pose_write: false`;
- seat after unload +0.043 mm, engagement 1.657 mm;
- physical regrasp contact and upward pull attempt;
- final pull seat +0.068 mm, engagement 1.632 mm;
- task phase `success`, finite state, and no pose jump.

This establishes one deterministic end-to-end episode. It does not replace the
required randomized, population, solver, and hardware holdouts.

## Falsification ledger

1. **100 kN/m explicit fixture servo at 240 Hz:** saturated and oscillated,
   producing 2.37 mm penetration. Rejected.
2. **One compliant material for every ABS face:** broad support sank about
   0.62 mm through the lower top. Rejected.
3. **Full-thickness stiff seating rim:** its inner vertical face contacted studs
   and created an artificial hard stop. Rejected.
4. **70 kN/m on every generated SDF point:** multiplied stiffness by roughly
   70-80 numerical points and jammed above 25 N at SDF 512. Rejected.
5. **5 MN/m force spring for broad support:** its unresolved high-frequency
   energy launched the 1.18 g free brick on unload. Replaced by rigid support.
6. **Full six-axis external `ContinuousStudConnector` wrench:** torsional and
   centering action ejected the shallowly engaged brick. Not installed.
7. **Axial-only external wrench during lead-in:** applied retention before a
   robust contact state and ejected the part. Not installed.
8. **Passive regularized explicit axial force:** analytically passive in the
   unit law but still discretely unstable on a 1.18 g body at 480 Hz. Not the
   episode backend.
9. **Native compliant connector pads:** introduced 21.6 mm upward displacement
   in the recorded experiment. Disabled by default and retained only as an
   optional falsification artifact.
10. **Higher native Coulomb friction alone:** 0.20 to 0.30 did not recover
    retention. Rejected as a sufficient fix.
11. **Breakable fixed connector:** stable only as a diagnostic and unable to
    separate axial clutch from lateral stiffness. Replaced by force-limited D6.

## Software and artifact checks

- All 24 pure-Python tests pass: manifold geometry, mass override, task-history
  anti-cheat behavior, connector equal/opposite and passive laws, calibration
  parsing, and Gym API validation.
- `LegoAssembly-v0` registers through `lego.lego_env` with a seven-component
  normalized action and 30-component observation.
- GUI runtime self-test is finite and holds the press at 1.400000 m after 240
  physics steps.
- The authored scene records solver/contact scales, brick collider counts,
  press mechanism, and connector activation policy in `scene_audit.json`.

## What has not been established

None of these numerical results validates real clutch power. Required evidence
still includes real part dimensions and distributions; aligned/offset/tilt/yaw
force-displacement curves; insertion and removal energy; shear/twist/peel;
dwell, temperature, humidity, wear, and cycle history; physical Franka grasp
and press response; and holdout multi-brick structures.
