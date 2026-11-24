# Changelog

Notable changes per release. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and versions follow [Semantic Versioning](https://semver.org/). Add a line under **Unreleased** in
the same PR as the change.

## [Unreleased]

## [0.1.0] - 2026-11-23

First release.

### Added

- Integration for iDotMatrix Bluetooth panels (16×16, 32×32, 64×64): discovery, a `light`
  for power and brightness, a `select` of saved designs, a clock-sync `button`, and actions for
  text, clock, colour, effects, images, GIFs, scoreboard, countdown and stopwatch.
- Sidebar panel modelled on the phone app: live drawing, text, clock, effects, timers, designs,
  and a gallery with uploads, an exact LED preview and a fit score.
- 13 original built-in animations.
- Automatic panel size detection: setup reads the size from the panel, and every connection
  checks it, correcting the setting instead of sending content that could crash the panel.
- Reliable, fast uploads: chunk acknowledgements, the negotiated Bluetooth write size, and GIFs
  encoded the way the firmware expects.
- Integration icon, and the panel's firmware version on its device page.
- HACS packaging.

### Security

- Changing the shared library or saved designs needs an admin; other users can still show
  content on the panel.
- Image decoding is bounded: oversized images are refused before decoding, and the library and
  designs have size limits.
