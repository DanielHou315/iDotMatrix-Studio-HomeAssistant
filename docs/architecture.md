# Architecture

```
sidebar panel (frontend/panel.js)
   │  websocket: idm_studio/subscribe, run, preview, media/*, design/*
   ▼
__init__.py ── services (idm_studio.text, .clock, .media, ...)
   │
runtime.IdmDisplay ── one per panel: validates actions, remembers state,
   │                   saved designs, the drawing canvas
   ├── media.py     framing (fill/fit/stretch, zoom, pan, sharp) and fit analysis
   ├── library.py   built-in art + uploads in <config>/idm_studio/media
   ├── protocol.py  pure packet builders
   └── device.IdmConnection ── BLE link: connects on demand, syncs the clock
                               on connect, drops after 2 min idle
```

## One source of truth for images

`media.prepare()` produces the exact frames sent to the panel. The sidebar preview asks the
server for those same frames (`idm_studio/preview`) instead of resizing in the browser, so what
you see is what the panel shows.

## Fit analysis

`media._detail_loss()` renders the framed image at 4x panel resolution, shrinks it to the panel
(area average), scales it back up, and measures how much of the image's variance disappeared.
That share is the detail finer than one LED. Below 12 % is a good fit, below 30 % fair, otherwise
poor. It also flags very dark images and pixel art (suggests Sharp pixels).

## Protocol

Packets are verified byte for byte against the GPL-3.0 reference client used by
[tukies/iDotMatrix-HomeAssistant](https://github.com/tukies/iDotMatrix-HomeAssistant)
(`scripts/compare_reference.py`). Writes go to characteristic `0xFA02` in chunks of at most
509 bytes with response; bulk transfers (images, GIFs, text) carry a 16-byte header with size
and CRC32, split into 4 KB chunks.
