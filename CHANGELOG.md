# Changelog

Notable changes per release. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and versions follow [Semantic Versioning](https://semver.org/). Add a line under **Unreleased** in
the same PR as the change.

## [Unreleased]

### Added

- Integration for iDotMatrix Bluetooth panels (16×16, 32×32, 64×64): discovery, a `light`
  for power and brightness, a `select` of saved designs, a clock-sync `button`, and actions for
  text, clock, colour, effects, images, GIFs, scoreboard, countdown and stopwatch.
- Sidebar panel modelled on the phone app: live drawing, text, clock, effects, timers, designs,
  and a gallery with uploads, an exact LED preview and a fit score.
- 13 original built-in animations.
- HACS packaging, CI, issue templates and an automated release workflow.

### Fixed

- Uploads wait for the panel's acknowledgement of every chunk, so larger GIFs are no longer
  dropped.
- Uploads use the negotiated Bluetooth write size instead of 20-byte writes (about 10× faster).
- GIF frames share one full palette, so the panel no longer garbles frames.
