# Pen-cap closure: physics research + simulation architecture (phase 1)

Goal: simulate "close the pen's cap" with the REAL mechanism -- not a pose check.
Everything below is sourced (links at bottom) or verified in the local Isaac install.

## 1. How a pen cap actually holds: the annular snap-fit

A snap cap is an **annular snap-fit joint**: one part carries a circumferential
bead (ridge), the mate carries a groove; assembly requires the flexible member
(the cap lip) to expand elastically by the interference depth and ride a lead
ramp until the bead drops into the groove. Friction-only press-fit caps exist
(no click); clicking caps are snap-fits. Key mechanics (DuPont/MachineDesign
design equations):

- Radial force from hoop elasticity:  P = f * X * E_s / d
  f = interference (undercut) depth; d = mating diameter; E_s = secant modulus
  at working strain; X = geometry factor from diameters + Poisson ratio:
    flexible outer ring on rigid shaft:
    X = [(d_a^2 + d^2) + 2*nu*(d_a^2 - d^2)] / (d_a^2 - d^2)
  NOTE: normalization of P (total vs per-circumference) must be re-verified
  against the original design guide before quantitative use -- the web copy is
  ambiguous. Calibrate against the analytic curve during the probe.

- Insertion force through the ramp:
    F = P * (sin th + mu*cos th) / (cos th - mu*sin th)
  th = ramp angle at the contact. LEAD angle (going on) is shallow (< 30 deg);
  RETURN angle (coming off) sets removability: ~30 deg easy-off, ~45 deg
  typical reusable, 90 deg permanent. The ON/OFF force asymmetry of a real cap
  comes from this angle asymmetry.

- Strain check: hoop strain = f/d must stay under the material allowable
  (~50% of break strain; PP break ~ >8%, so ~2-3% working strain is healthy).

- Groove placement: a groove remote from the free end is ~3x stiffer than one
  near the end (the pen cap groove is near the lip -- compliant).

## 2. What the click IS (this matters for the verifier)

From fountain-pen cap mechanics analysis: during closure the force RISES along
the ramp (phase 1), then the bead flicks into the groove and resistance
COLLAPSES (phase 2). The human cannot back off force fast enough, so the cap
accelerates and IMPACTS the barrel shoulder -- **the click is the shoulder
impact**, tuned by making ramp travel slightly longer than groove engagement.
Consequence: a sim with the right force-displacement curve produces the click
KINEMATICALLY -- measurable as (force peak -> collapse -> velocity spike ->
shoulder impact impulse) with no audio hand-waving.

Also real: the cap/barrel annulus is a piston. Measured diametral gaps across
seven pens: 0.2-1.0 mm (avg 0.7). Fast removal pulls vacuum ("pop"), insertion
compresses air; real caps add vent holes (also anti-choking). Secondary effect;
declared approximation initially.

## 3. Pen-scale parameters (BIC-class, for the parametric builder)

- Cap: polypropylene, ID ~ 9.5-10.5 mm at the lip, wall ~ 1.0-1.2 mm.
- E(PP) ~ 1.3-1.8 GPa; secant at 2-3% strain ~ 0.8-1.2 GPa; mu(PP-PP) ~ 0.2-0.3.
- Interference f ~ 0.15-0.30 mm (hoop strain ~1.5-3% -- inside allowable).
- Lead angle ~ 20-25 deg; return angle ~ 40-50 deg.
- Real-world cap on/off force: order 5-30 N (to be validated analytically and,
  if possible, against any published measurement; else measured on hardware).

## 4. Simulation feasibility (verified locally + literature)

**Local Isaac 5.1 install verified to have:**
- `physxSDFMeshCollision:sdfResolution` (default 256) + `sdfSubgridResolution`:
  SDF voxel collision for exact nonconvex rigid contact (the Factory method).
- `physxMaterial:compliantContactStiffness` / `Damping` /
  `AccelerationSpring`: Hookean spring-damper CONTACT (force per unit
  penetration distance) replacing rigid contact when stiffness > 0.

**Literature:** NVIDIA Factory / IndustReal simulate mm and SUB-mm assembly
(peg-in-hole, gear mesh, NUT-AND-BOLT THREADING -- feature scale comparable to
a snap bead) with SDF contact, transferring to real robots at 83-99% success.
Tight-tolerance rigid contact at our feature scale is PROVEN territory.

**FEM at GPa:** PhysX FEM soft bodies remain "a bit soft" regardless of E
(developer guidance + forum reports of steel-stiff bodies acting soft) --
a GPa cap lip would under-report retention force. Not the primary path.

## 5. Candidate architectures (fidelity x feasibility)

- **A. Rigid SDF + compliant contact (RECOMMENDED FIRST).** Cap and barrel are
  rigid meshes with exact bead/groove/ramp/shoulder geometry (SDF collision).
  The hoop elasticity is lumped into the contact spring: set
  compliantContactStiffness k = P/f (the real hoop stiffness), damping from
  material loss. The bead physically rides the ramp by compressing the contact
  spring by up to f; insertion force F(x) emerges from geometry + friction;
  the snap collapse and shoulder-impact click emerge kinematically.
  DECLARED approximations: elasticity lumped at the contact (cap does not
  visibly flare); spring is contact-normal rather than hoop-directional.
- **B. Petal-discretized elastic lip (FIDELITY TARGET).** Split the cap lip
  into N rigid petals on torsion joints; derive joint stiffness by matching
  ring-expansion strain energy; SDF/convex collision per petal. The lip
  visibly flares, compliance is direction-correct, snap fully emergent.
  More build + tuning; do after A validates the measurement harness.
- **C. FEM cap at real E.** One probe to DOCUMENT the softness gap honestly,
  not a primary path.
- **D. Pure rigid, no compliance.** Geometrically impossible for an
  interference fit (bead cannot pass) -- this is why the naive approach is
  fake. Rejected.

## 6. Validation & verifier design (the anti-pose-check)

Instrumented probe: barrel fixed; cap driven axially by a measured
force/velocity profile; log contact force vs displacement.

1. **Force-curve match:** in-sim F(x) vs the analytic ramp curve (Sec. 1) --
   peak magnitude, peak location, post-snap collapse.
2. **Click signature (kinematic):** force collapse -> cap velocity spike ->
   shoulder impact impulse within the final ~0.5 mm. Log all three.
3. **Retention asymmetry:** pull-off force / push-on force ratio consistent
   with return/lead angle prediction; pull below threshold does NOT separate.
4. **CLOSED :=** bead axial position inside the groove band
   AND closure history contains the snap signature (2)
   AND an applied axial pull at F_test < F_retention does not separate the
   parts. A teleported/pose-faked cap has no snap signature and fails the
   pull test if not geometrically seated.
5. Air piston: postponed, declared (real pens vent); candidate later model =
   gap-flow axial force term.

## 7. Next steps

1. Parametric revolved-profile builder: barrel + cap meshes with (d, f, lead,
   return, groove width, shoulder gap) as parameters; export with SDF collision.
2. Probe P1: SDF contact sanity at 0.2 mm features (resolution/dt sweep;
   does the bead ride the ramp without tunneling or explosion?).
3. Probe P2: compliant-contact stiffness sweep; measure F(x); compare analytic.
4. Probe P3: full closure with a velocity-controlled push -> click signature?
5. Probe P4: pull-off asymmetry; verifier end-to-end incl. spoof tests.
6. Then architecture B (petal lip) against the same harness.

## Sources

- MachineDesign, "Fundamentals of annular snap-fit joints" (DuPont design
  equations): https://www.machinedesign.com/fastening-joining/article/21834620/fundamentals-of-annular-snap-fit-joints
- Fountain Pen Design, "Cap mechanics and physics" (click = shoulder impact;
  pumping/gap data): https://fountainpendesign.wordpress.com/fountain-pen-cap-history-overview/fountain-pen-cap-mechanics-physics/
- Factory: Fast Contact for Robotic Assembly (SDF assembly sim):
  https://www.researchgate.net/publication/361717052_Factory_Fast_Contact_for_Robotic_Assembly
- IndustReal / NVIDIA sim-to-real assembly blog:
  https://developer.nvidia.com/blog/bridging-the-sim-to-real-gap-for-industrial-robotic-assembly-applications-using-nvidia-isaac-lab/
- Isaac deformable stiffness limits (forum + docs):
  https://forums.developer.nvidia.com/t/small-stiff-deformable-body/267129
- Snap-fit overviews: https://www.plasticstoday.com/injection-molding/injection-molding-design-fundamentals-snap-fits-for-plastic-parts ,
  https://www.eycpu.com/blog/snap-fit-joints-design-guideline/
- Local verification: `omni.usd.schema.physx` schema.usda in this install
  (SDF + compliant-contact attributes present).
