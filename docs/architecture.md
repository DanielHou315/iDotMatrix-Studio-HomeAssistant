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

Findings from a real 16x16 panel (firmware 3.16), several matching the notes in
[markusressel/idotmatrix-api-client](https://github.com/markusressel/idotmatrix-api-client/blob/main/docs/DEVICE-PROTOCOL.md):

- **Panel size must be right.** Text drawn in 16x32 glyph cells crashes a 16x16 panel (it beeps
  and reboots); it needs 8x16 cells.
- **Write size.** BlueZ reports 20-byte writes until the MTU is known, which it may never learn
  by itself. After connecting we acquire the MTU explicitly (509 here); otherwise a 15 KB GIF
  takes 12 s instead of about 1 s.
- **Upload acknowledgements.** The panel answers every 4 KB chunk on `0xFA03` with
  `05 00 <kind> 00 <status>`: `01` send the next chunk, `03` finished, `02` no room, `00`
  rejected. Sending the next chunk early makes it drop the upload silently, so we wait for each
  answer (5 s, like the official app). A 21 KB, 64-frame GIF plays fine this way.
- **GIF color tables.** Frames whose color tables differ in size are garbled or dropped, so every
  GIF uses one 256-entry global table and no per-frame tables.
