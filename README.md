# Gym Anything Pages

This is the public deployment surface for the Gym Anything organization.

- `/` is the organization landing page.
- `/robotics/` is a generated, sanitized Environment Atlas export.

The source of truth lives in the private
`gym-anything/gym_anything_for_robotics` repository. The deployment workflow
replaces the Robotics export after changes land on `main`; do not edit generated
files in `robotics/` by hand.
