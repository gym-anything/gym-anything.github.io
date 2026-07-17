# Lock and key. Research notes.

Task. Simulate a real pin tumbler lock and its key in Isaac Sim with full physical fidelity. The lock must open only with the right key, fully inserted. Wrong keys, partial insertion, wear, friction, and forces must all behave as they do in the real object.

This file is the durable research record. Every number carries a source label. The labels mean the following. READ means I read the primary document first hand in this session. WEB means a web page or search summary reported it and I have not seen the primary document. BLOG means a single informal web source with no corroboration yet.

Iterations 1 and 2 were completed on 2026-07-05. Iteration 2 closed the blade thickness and deadbolt gaps and proved that two other gaps are unpublished proprietary data that must close by probe. Remaining gaps and the probe ladder are listed at the end.

## The reference platform

The build targets a Kwikset style 5 pin residential cylinder on the KW1 keyway. Kwikset has the coarsest geometry of the common platforms. Its cut increment is 0.023 inches which is 0.584 mm. Schlage is the second reference with a 0.015 inch increment and 6 pins, and both spec sheets are captured below so the sim can later switch platforms.

## Anatomy and operation

A pin tumbler cylinder has a rotating plug inside a fixed shell. Pin chambers are drilled through both. Each chamber holds a spring, a driver pin, and a key pin, from top to bottom. The gap between plug and shell is the shear line. With no key the springs push the driver pins down across the shear line, locking the plug to the shell. The correct key lifts every key pin so that each key pin to driver pin joint sits exactly at the shear line, and only then can the plug rotate. The plug drives a cam or tailpiece at its rear which throws the bolt. Sources are lockwiki.com and art-of-lockpicking.com and scienceabc.com. Label WEB.

Wrong key failure needs no scripting. A wrong bitting lifts at least one pin stack to the wrong height, so either a driver pin still crosses the shear line or a key pin is pushed up across it, and the pin binds between plug and shell under torque. Partial insertion fails the same way because each cut sits under the wrong chamber. This is geometry, not logic, and the sim must produce it from contact alone.

## Dimensions, cross verified

The two tables below come from two independent sources that agree on every entry. Source one is the factory style spec sheet from lsamichigan.org which I read first hand as a PDF. Source two is the community pinning reference sheet version 3.0 from naswek.com which I also read first hand. Label READ for both tables.

### Kwikset classic, KW1

| Property | Value |
|---|---|
| Pins | 5 |
| Pin diameter | 0.115 in = 2.921 mm |
| Plug diameter | 0.500 in = 12.70 mm (lockwiki gives measured 0.498 in) |
| MACS | 4 |
| Cut increment | 0.023 in = 0.584 mm |
| Progression | single step |
| Blade width (key height) | 0.335 in = 8.51 mm |
| Depth tolerance | +/- 0.003 in = +/- 76 um |
| Spacing tolerance | +/- 0.004 in = +/- 102 um |
| First cut from shoulder | 0.247 in |
| Cut to cut spacing | 0.150 in = 3.81 mm |
| Cut angle | 90 deg |
| Cut root flat | 0.084 in (factory sheet drawing) |
| Root depths 1..7 | 0.329 / 0.306 / 0.283 / 0.260 / 0.237 / 0.214 / 0.191 in |
| Key pin lengths 1..6 | 0.172 / 0.195 / 0.218 / 0.241 / 0.264 / 0.287 in |
| Driver pin length | 0.180 in regular, 0.160 in construction |
| Key pin tips | slightly tapered on both ends (lockwiki, label WEB) |

### Schlage classic, SC1

| Property | Value |
|---|---|
| Pins | 6 standard cuts |
| Pin diameter | 0.115 in |
| Plug diameter | 0.500 in |
| MACS | 7 |
| Cut increment | 0.015 in = 0.381 mm |
| Progression | two step |
| Blade width | 0.343 in |
| Depth tolerance | +0.002 / -0 in |
| Spacing tolerance | +/- 0.001 in |
| First cut from shoulder | 0.231 in |
| Cut positions from shoulder | 0.231 / 0.3872 / 0.5434 / 0.6996 / 0.8558 / 1.012 in |
| Cut angle | 100 deg |
| Cut root flat | 0.031 in |
| Root depths 0..9 | 0.335 down to 0.200 in step 0.015 |
| Bottom pin lengths 0..9 | 0.165 up to 0.300 in step 0.015 |
| Top pins, compensated | 0.235 in for plug totals 0 to 3, 0.200 in for 4 to 6, 0.165 in for 7 to 9 |
| Bottom pin tip | drawn pointed conical in the factory sheet |
| Driver pin shape | drawn as flat ended cylinder in the factory sheet |

### Key blade thickness and the keyway width

The blade thickness is the dimension the keyway width must match, and it is measured rather than published as a factory spec. A locksport source measured KW1 blades at 0.079 to 0.081 in, which is 2.01 to 2.06 mm, and SC1 blades at 0.085 to 0.090 in. A separate source gives a factory calibrated cut key blade thickness of 0.098 in. Label WEB, iteration 2. The build will use 2.03 mm for the KW1 blade and cut the keyway slot to that plus the working clearance. The keyway is not a plain slot. It carries warding grooves that a foreign blank cannot pass, which is the physical reason a wrong profile is rejected before any pin is even reached.

### The geometric closure law

Bottom pin length equals the effective plug diameter minus the root depth of the cut under it. For Schlage every pair in the table sums to 0.500 in exactly. For Kwikset every pair sums to 0.501 in. The locksmithledger masterkeying article names this the effective plug diameter. Label WEB for the name and READ for the arithmetic since I checked it against both tables. A service rule from the same trade literature says the key in knob pin stack should total 0.515 in for correct spring pressure. Label WEB, corroborate in iteration 2.

## Tolerances and why locks bind

Plug to shell radial clearance and chamber placement error are the difference between a lock that turns and one that binds. The trade and locksport literature agrees on the mechanism. Manufacturing leaves roughly a thousandth of an inch of slack in the cylinder, chambers are not drilled perfectly on line, and under torque the plug rotates a fraction of a degree until one pin carries the load. That pin is the binding pin, and binding order is the fingerprint of per chamber positional error. Sources are art-of-lockpicking.com and lockpickworld.com and practicalpicking.wordpress.com. Label WEB. No hard per chamber error figure was found in iteration 1 beyond the order of one thousandth of an inch. This matters for the sim because a lock built with zero chamber error would have no binding order at all, which real locks never show. The sim should author small per chamber offsets as a manufacturing realism parameter, defaulted near 0.001 in, and disclose it.

The factory depth tolerances above are the key side of the same story. A Kwikset cut may be 76 um off nominal and must still work, so the working clearance at the shear line is at least that large. This gives the sim a measurable acceptance band rather than a guess.

## Forces and torques, from the standard read first hand

ANSI BHMA A156.5 2014 is the American standard for cylinders. I read the committee review PDF first hand. Label READ for everything in this table. An earlier automated summary of the same PDF invented wrong numbers, which was caught by reading. The real requirements follow.

| Test | Requirement |
|---|---|
| Break in before testing | 25 key insertions with rotation |
| Force to insert key, 5 or 6 pins | at most 3 lbf = 13 N |
| Force to insert key, 7 or more pins | at most 5 lbf = 22 N |
| Force to extract key | same limits as insertion |
| Torque to rotate plug, no cam load, Grade 1 | at most 18 ozf in = 0.14 N m |
| Torque to rotate plug, Grade 2 | 0.19 N m |
| Torque to rotate plug, Grade 3 | 0.25 N m |
| Cycle test cam preload | 3 in lbf = 0.34 N m held through each cycle |
| One cycle | full insertion, rotate at least 180 deg, return, extract |
| Cycle counts Grade 1 / 2 / 3 | 40000 / 20000 / 10000 |
| Cycle rate | at most 30 cycles per minute |
| Post cycle insertion force, 5 or 6 pins | at most 6 lbf = 26 N |
| Post cycle plug torque | at most 13 in lb = 1.47 N m |
| Plug pulling, Grade 1, bored lock | withstands 500 lbf = 2200 N axial |
| Plug torque attack, Grade 1 | plug must not rotate more than 45 deg at 300 lbf in = 34 N m |
| Key strength | key survives 23 in lb = 2.6 N m for 5 s, then still operates at no more than 13 in lb = 1.3 N m |
| Lubrication | factory application only, none added for testing |

These numbers are the verifier suite. Operational tests gate the healthy lock. The post cycle limits quantify how much degradation wear is allowed to cause. The strength tests gate what must NOT happen, meaning the wrong key or no key cases must hold against 34 N m without the plug passing 45 degrees.

## Springs

One mechanism blog states pin springs give roughly 0.2 to 0.5 N at full compression. Label BLOG, single source, not yet corroborated. Rekeying kits sell 0.115 in diameter springs matched to the pin bore. Label WEB. No free length or spring rate was found in iteration 1. The honest path is a calibration anchored to the A156.5 insertion force gate. Five stacks riding over cut ramps under spring load plus friction must total under 13 N of axial resistance, and the springs must still reseat pins reliably, which brackets the spring force from both sides. This mirrors the cohesion ladder method from the titration project where the knob was anchored to an independent real observable.

## Materials, friction, wear

Plugs, shells, and most pins are brass. Better pins and better keys are nickel silver, a copper nickel zinc alloy near 60 20 20. Key blanks are brass or nickel silver. Springs are steel. Sources are abus.com and keys4classics.com and the nickel silver wikipedia page. Label WEB. Densities from standard tables are 8.4 to 8.7 g per cm3 for both alloys, so a single pin of 0.115 in diameter and 0.2 in length weighs about 0.6 g.

Friction for brass on brass is reported as 0.9 static dry and 0.6 lubricated in a valve design handbook table. Label WEB. Friction tables scatter badly and locks run with factory lubricant on polished surfaces, so the working range is treated as roughly 0.3 to 0.6 and the exact value becomes a calibration target anchored to the A156.5 insertion and rotation gates, never a free knob.

Wear is documented forensically at lockpickingforensics.com with photographed timelines. Label WEB but a strong specialist source. Pin tips lose factory milling marks and polish progressively. About 250 uses over 3 to 6 months develops a visible ring on the pin tip. About 1500 uses removes most milling marks on front pins. About 5000 uses polishes front pins to a uniform surface while rear pins stay fresher, because every insertion drags the whole key length under the front pins but only the key tip under the rear pin. Keys wear rounded on the cut edges, then lift pins late and at an angle. Locksmith sources add that worn brass pins plus a worn key drop the effective lift below the shear line and the lock stops opening, and that a key cut fresh to factory code can fail in a lock whose pins are themselves worn. Wear in the sim therefore has two real observables. Geometry loss on key cuts and pin tips of order a few thousandths of an inch, and the A156.5 post cycle force growth limits.

## Simulation feasibility, the Factory precedent

NVIDIA Factory, published at RSS 2022, is the load bearing precedent. I read the relevant sections of the paper PDF first hand. Label READ. Factory simulates nut and bolt thread engagement in PhysX with SDF collision, including M4 nuts whose thread pitch is 0.7 mm, and pegs in holes at the ISO clearance of 0.104 mm. For contact profiling experiments they introduced clearances as small as 2 um and even a negative clearance of 1 um. Their stable recipe on the nut and bolt scene is a Gauss Seidel solver with 1 substep and 16 iterations at a timestep of 1/60 s, with SDF resolutions of 256 cubed or greater, and contact reduction bringing memory to 768 KB per frame. Earlier work needed a 1 ms timestep with 10 substeps for the same contact problem.

The lock is the same regime. Pin diameter 2.9 mm, cut increment 0.58 mm, working clearances 25 to 76 um, all larger than Factory's 2 um demonstrations. The PhysX contact offset rule from the Isaac Gym Factory documentation is to keep the contact offset at least one order of magnitude above v times dt over n where v is the characteristic speed, so slow key motion at mm per second scales the required offsets well below the feature sizes here. SDF collision in Isaac Sim requires the GPU pipeline.

One local caution from this repository. The titration project found PhysX defaults skin contacts at about 2 cm, which is far above every feature in this lock, so every collider in the lock must author explicit contact and rest offsets. That finding is recorded in titrate FINDINGS law form and was verified there by measurement.

## The deadbolt the plug drives

A single cylinder residential deadbolt has a one inch bolt throw and a 7/8 in bolt diameter, fits a 2 1/8 in cross bore and a 1 in edge bore, and comes in 2 3/8 in or 2 3/4 in backsets. Label WEB, iteration 2, multiple vendor listings agree. Grade 1 is the strongest residential grade. This gives the sim a real bolt to actuate. The plug rotation must drive a cam or tailpiece that translates into a one inch linear bolt throw.

## What iteration 2 proved is not on the open web

Two numbers were searched hard and are genuinely not published as open data, which is itself a finding rather than a missing homework item.

The exact KW1 warding cross section as a dimensioned drawing does not exist in the open literature because it is anti duplication proprietary geometry. The real profile is nonetheless encoded in community parametric key models such as the OpenSCAD and printable KW1 blanks, and it can be recovered by tracing a macro photograph of a real key end on against the known blade thickness of 2.03 mm and blade height of 8.51 mm. This is a probe, not a search, and it is P3 below.

The exact tumbler spring free length and spring rate are not published by the lock makers. Rekeying vendors sell the springs by fit, not by force curve. The single available force figure is the 0.2 to 0.5 N at full compression blog claim from iteration 1, still uncorroborated. The honest closure is calibration against the A156.5 insertion force gate, exactly as the titration cohesion knob was calibrated against pendant drop volume rather than guessed. This is a probe, P1 and P5 below.

## Remaining gaps to close by probe, not by search

- KW1 warding cross section. Recover by tracing a macro photo or a community parametric model against the known blade thickness. Closes in P3.
- Spring free length and rate. Calibrate against the 13 N insertion gate and the reseat requirement. Closes in P1 and P5.
- Per chamber positional error magnitude. No hard figure beyond order one thousandth of an inch. Becomes a disclosed manufacturing realism parameter whose observable is a stable binding order. Closes in P4.
- Pin tip and chamfer geometry. Kwikset key pins taper on both ends, Schlage bottom pins are pointed, chamber mouths are chamfered. Exact radii and angles unpublished. Start from the factory drawing shapes, refine so insertion force matches the gate. Closes in P1 and P3.
- Key insertion force profile over time. No source gives a time curve. The A156.5 static insertion and extraction limits are the gates.

## KW1 warding reconstruction (for P3)

The exact KW1 warding cross section is not published, because it is anti
duplication proprietary geometry. What is public is qualitative. A KW1 blade
carries two longitudinal grooves on its front face, a narrow one just right of
centre and a wider one to its left, with a different single groove on the back,
and the blade envelope is 2.03 mm thick by 8.51 mm tall. The functional role of
warding is not in doubt. Ridges inside the keyway ride in the blade grooves, so
a blade whose grooves do not match the ridges cannot enter, which is why a KW1
lock rejects an SC1 blank before any pin is touched.

The build therefore reconstructs a KW1 representative warded profile rather than
copies a secret drawing, and labels it a reconstruction. The plug keyway is a
slot matching the blade envelope plus a small clearance, with two ward ridges
protruding from the side walls at fixed heights. The correct key is a blade of
the true envelope with grooves milled exactly where those ridges sit, so it
slides in. A foreign blank is the same envelope without the matching grooves, so
a ridge blocks it. This reproduces the real behaviour, that a non matching
profile is physically refused, and the exact ridge heights are a disclosed
design choice, not a claimed factory value. The observable that validates it is
in P3, the correct blank inserts under the 13 N gate and the foreign blank
cannot pass.

## Probe ladder before any full build

- P1. One chamber, one spring, one driver, one key pin, real dimensions and offsets. Gate. The stack seats under spring force without jitter and holds a 25 um step at the shear ledge under plug torque without penetration.
- P2. One stack inside a rotating plug in a shell. Gate. Wrong lift binds the plug within a fraction of a degree of slop and right lift rotates freely, with the measured slop matching the authored clearance.
- P3. SDF key blade inside a warded keyway. Gate. The correct blank inserts under 13 N, a foreign blank cannot enter, and the bitted key produces a ramped force profile as each cut rides each pin.
- P4. Five stacks with authored chamber error. Gate. A binding order exists and is stable across runs, and the correct key opens while every single increment error key fails.
- P5. The A156.5 battery as an automated verifier. Insertion force, extraction force, unloaded plug torque, the 0.34 N m loaded cycle, and the 34 N m attack hold.
