# LaundryFold calibration data contract

This directory intentionally contains no fabricated real measurements.
`schema.json` defines the minimum record for a named physical specimen. Raw
machine exports remain immutable; processed curves and fitted profiles link back
to them by SHA-256 hash.

Required initial measurements are:

- conditioned geometry, mass, and areal density;
- thickness across a pressure loading/unloading cycle;
- cyclic warp, weft, and bias/shear coupons;
- pure/cantilever bending in both material directions and faces;
- cloth--table, cloth--cloth, and cloth--finger friction versus load/speed;
- crease recovery versus direction, pressure, dwell, recovery time, and cycle;
- drape, corner-drop, swing, and gripper squeeze/pull/lift trials; and
- held-out real half-fold trajectories with registered material landmarks,
  force/pressure, release, and settling.

Calibration, validation, and test assignments are frozen before fitting.
