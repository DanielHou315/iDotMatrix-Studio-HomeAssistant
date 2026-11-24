// iDotMatrix Studio sidebar panel. Plain web component, no build step.

const PALETTE = [
  "#ffffff", "#000000", "#ff3b30", "#ff9500", "#ffcc00", "#34c759", "#00c7be", "#30b0ff",
  "#007aff", "#5856d6", "#af52de", "#ff2d55", "#a2845e", "#8e8e93", "#ff8ad8", "#7cff6b",
];

const MODES = [
  { id: "draw", label: "Draw", icon: "M20.71 7.04c.39-.39.39-1.04 0-1.41l-2.34-2.34c-.37-.39-1.02-.39-1.41 0l-1.84 1.83 3.75 3.75M3 17.25V21h3.75L17.81 9.93l-3.75-3.75L3 17.25Z" },
  { id: "text", label: "Text", icon: "M5 4v3h5.5v12h3V7H19V4H5Z" },
  { id: "clock", label: "Clock", icon: "M12 20a8 8 0 1 0 0-16 8 8 0 0 0 0 16m0-18a10 10 0 1 1 0 20 10 10 0 0 1 0-20m.5 5v5.25l4.5 2.67-.75 1.23L11 13V7h1.5Z" },
  { id: "gallery", label: "Gallery", icon: "M8.5 13.5l2.5 3 3.5-4.5 4.5 6H5m16 1V5a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2Z" },
  { id: "effect", label: "Effects", icon: "M7.5 5.6 10 7 8.6 4.5 10 2 7.5 3.4 5 2l1.4 2.5L5 7l2.5-1.4m12 9.8L17 14l1.4 2.5L17 19l2.5-1.4L22 19l-1.4-2.5L22 14l-2.5 1.4M22 2l-2.5 1.4L17 2l1.4 2.5L17 7l2.5-1.4L22 7l-1.4-2.5L22 2m-8.6 5.3a1 1 0 0 0-1.4 0L1.3 18a1 1 0 0 0 0 1.4l2.3 2.3a1 1 0 0 0 1.4 0L15.7 11a1 1 0 0 0 0-1.4l-2.3-2.3m-1 5.5-2.1-2.1 2.4-2.4 2.1 2.1-2.4 2.4Z" },
  { id: "color", label: "Color", icon: "M17.5 12a1.5 1.5 0 0 1-1.5-1.5A1.5 1.5 0 0 1 17.5 9a1.5 1.5 0 0 1 1.5 1.5 1.5 1.5 0 0 1-1.5 1.5m-3-4A1.5 1.5 0 0 1 13 6.5 1.5 1.5 0 0 1 14.5 5 1.5 1.5 0 0 1 16 6.5 1.5 1.5 0 0 1 14.5 8m-5 0A1.5 1.5 0 0 1 8 6.5 1.5 1.5 0 0 1 9.5 5 1.5 1.5 0 0 1 11 6.5 1.5 1.5 0 0 1 9.5 8m-3 4A1.5 1.5 0 0 1 5 10.5 1.5 1.5 0 0 1 6.5 9 1.5 1.5 0 0 1 8 10.5 1.5 1.5 0 0 1 6.5 12M12 3a9 9 0 0 0-9 9 9 9 0 0 0 9 9 1.5 1.5 0 0 0 1.5-1.5c0-.39-.15-.74-.39-1-.23-.27-.38-.62-.38-1a1.5 1.5 0 0 1 1.5-1.5H16a5 5 0 0 0 5-5c0-4.42-4.03-8-9-8Z" },
  { id: "score", label: "Score", icon: "M2 5v14h20V5H2m9 12H4V7h7v10m9 0h-7V7h7v10M6 9h3v6H6V9m9 0h3v6h-3V9Z" },
  { id: "timer", label: "Timer", icon: "M15 1H9v2h6V1m-4 13h2V8h-2v6m8.03-6.61 1.42-1.42c-.43-.51-.9-.99-1.41-1.41l-1.42 1.42A8.96 8.96 0 0 0 12 4a9 9 0 0 0-9 9 9 9 0 0 0 9 9 9 9 0 0 0 7.03-14.61M12 20a7 7 0 0 1-7-7 7 7 0 0 1 7-7 7 7 0 0 1 7 7 7 7 0 0 1-7 7Z" },
  { id: "designs", label: "Designs", icon: "M4 2h16a2 2 0 0 1 2 2v16a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2m0 2v8h7V4H4m9 0v4h7V4h-7m0 6v10h7V10h-7M4 14v6h7v-6H4Z" },
  { id: "settings", label: "Settings", icon: "M12 15.5A3.5 3.5 0 0 1 8.5 12 3.5 3.5 0 0 1 12 8.5a3.5 3.5 0 0 1 3.5 3.5 3.5 3.5 0 0 1-3.5 3.5m7.43-2.53c.04-.32.07-.64.07-.97 0-.33-.03-.66-.07-1l2.11-1.63c.19-.15.24-.42.12-.64l-2-3.46c-.12-.22-.39-.31-.61-.22l-2.49 1c-.52-.39-1.06-.73-1.69-.98l-.37-2.65A.506.506 0 0 0 14 2h-4c-.25 0-.46.18-.5.42l-.37 2.65c-.63.25-1.17.59-1.69.98l-2.49-1c-.22-.09-.49 0-.61.22l-2 3.46c-.13.22-.07.49.12.64L4.57 11c-.04.34-.07.67-.07 1 0 .33.03.65.07.97l-2.11 1.66c-.19.15-.25.42-.12.64l2 3.46c.12.22.39.3.61.22l2.49-1.01c.52.4 1.06.74 1.69.99l.37 2.65c.04.24.25.42.5.42h4c.25 0 .46-.18.5-.42l.37-2.65c.63-.26 1.17-.59 1.69-.99l2.49 1.01c.22.08.49 0 .61-.22l2-3.46c.12-.22.07-.49-.12-.64l-2.11-1.66Z" },
];

const TEXT_MODES = ["Static", "Scroll left", "Scroll right", "Scroll up", "Scroll down", "Blink", "Fade", "Tetris", "Fill"];
const TEXT_COLOR_MODES = ["White", "Solid color", "Rainbow 1", "Rainbow 2", "Rainbow 3", "Rainbow 4"];

const hexToRgb = (hex) => [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16));
const rgbToHex = (rgb) => "#" + rgb.map((c) => c.toString(16).padStart(2, "0")).join("");
const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
// Only inline PNG data URLs are used as images; anything else is dropped.
const safeImg = (s) => (/^data:image\/png;base64,[A-Za-z0-9+\/]+=*$/.test(s || "") ? s : "");

function toBase64(bytes) {
  let s = "";
  for (let i = 0; i < bytes.length; i += 0x8000) s += String.fromCharCode.apply(null, bytes.subarray(i, i + 0x8000));
  return btoa(s);
}
function fromBase64(b64) {
  const s = atob(b64);
  const out = new Uint8Array(s.length);
  for (let i = 0; i < s.length; i++) out[i] = s.charCodeAt(i);
  return out;
}
function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result.split(",", 2)[1]);
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

/** Re-encode large stills so uploads stay well under the 4 MB websocket limit. */
async function shrinkStill(file) {
  const bmp = await createImageBitmap(file);
  const edge = 1024;
  if (file.size < 1.5 * 1024 * 1024 && Math.max(bmp.width, bmp.height) <= edge) return file;
  const scale = Math.min(1, edge / Math.max(bmp.width, bmp.height));
  const c = document.createElement("canvas");
  c.width = Math.round(bmp.width * scale);
  c.height = Math.round(bmp.height * scale);
  c.getContext("2d").drawImage(bmp, 0, 0, c.width, c.height);
  return new Promise((resolve) => c.toBlob(resolve, "image/png"));
}

class IdmStudioPanel extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._panels = [];
    this._entryId = null;
    this._mode = "draw";
    this._tool = "pen";
    this._color = "#ff3b30";
    this._live = true;
    this._pending = new Map();
    this._history = [];
    this._busy = false;
    this._form = {
      text: { text: "Hello!", mode: 1, speed: 90, color_mode: 1, color: "#30b0ff", bg: false, background: "#000000" },
      clock: { style: 0, show_date: true, hour24: true, color: "#ffffff" },
      effect: { style: 0, colors: ["#ff3b30", "#ffcc00", "#30b0ff"] },
      color: "#ff9500",
      timer: { minutes: 5, seconds: 0 },
      image: null,
    };
  }

  set hass(hass) {
    const first = !this._hass;
    this._hass = hass;
    if (first) this._subscribe();
    const menu = this.shadowRoot.querySelector("ha-menu-button");
    if (menu) menu.hass = hass;
  }
  set narrow(narrow) {
    this._narrow = narrow;
    const menu = this.shadowRoot.querySelector("ha-menu-button");
    if (menu) menu.narrow = narrow;
  }

  disconnectedCallback() {
    clearTimeout(this._retry);
    if (this._unsub) this._unsub.then((u) => u()).catch(() => {});
    this._unsub = null;
    this._subscribed = false;
  }
  connectedCallback() {
    if (this._hass && !this._subscribed) this._subscribe();
  }

  _subscribe() {
    this._subscribed = true;
    this._loaded = false;
    this._error = null;
    this._render();
    this._unsub = this._hass.connection.subscribeMessage((msg) => this._onState(msg.panels), { type: "idm_studio/subscribe" });
    // Fails while the integration is still starting (e.g. right after a restart): say so and retry.
    this._unsub.catch((err) => {
      this._unsub = null;
      this._error = err?.message || err?.code || String(err);
      this._render();
      clearTimeout(this._retry);
      this._retry = setTimeout(() => this._hass && this.isConnected && this._subscribe(), 5000);
    });
  }

  // Not `panel`: Home Assistant sets that property to the panel config.
  get _current() {
    return this._panels.find((p) => p.entry_id === this._entryId);
  }

  _onState(panels) {
    this._loaded = true;
    this._error = null;
    this._panels = panels;
    if (!this._current && panels.length) this._entryId = panels[0].entry_id;
    const p = this._current;
    if (p && (!this._buf || this._buf.length !== p.size * p.size * 3)) {
      this._size = p.size;
      this._buf = fromBase64(p.canvas);
      this._render();
      return;
    }
    // Pick up canvas changes made elsewhere (designs, services) when not mid-stroke.
    if (p && !this._drawing && !this._pending.size && !this._sending) this._buf = fromBase64(p.canvas);
    if (!this.shadowRoot.querySelector(".layout")) this._render();
    else this._renderStatus();
  }

  // --- backend calls -----------------------------------------------------------

  async _run(action, data = {}, { quiet = false } = {}) {
    if (!this._current) return false;
    try {
      if (!quiet) this._setBusy(true);
      await this._hass.callWS({ type: "idm_studio/run", entry_id: this._entryId, action, data });
      return true;
    } catch (err) {
      this._toast(`${action} failed: ${err.message || err}`);
      return false;
    } finally {
      if (!quiet) this._setBusy(false);
    }
  }

  async _saveDesign(action, data, thumb) {
    const name = (this.shadowRoot.querySelector("#design-name")?.value || "").trim() || prompt("Name this design");
    if (!name) return;
    try {
      await this._hass.callWS({ type: "idm_studio/design/save", entry_id: this._entryId, name, action, data, ...(thumb ? { thumb } : {}) });
      this._toast(`Saved "${name}"`);
    } catch (err) {
      this._toast(`Save failed: ${err.message || err}`);
    }
  }

  _toast(message) {
    this.dispatchEvent(new CustomEvent("hass-notification", { detail: { message }, bubbles: true, composed: true }));
  }

  _setBusy(busy) {
    this._busy = busy;
    this.shadowRoot.querySelector(".screen-wrap")?.classList.toggle("busy", busy);
  }

  // --- LED screen ----------------------------------------------------------------

  _paintScreen() {
    const canvas = this.shadowRoot.querySelector("#screen");
    if (!canvas || !this._buf) return;
    const n = this._size;
    const px = canvas.width / n;
    const ctx = canvas.getContext("2d");
    const state = this._current?.state;
    // The panel's own brightness, so the preview dims like the real thing.
    const level = !state || state.power ? 0.3 + 0.7 * ((state?.brightness ?? 100) / 100) : 0;
    ctx.globalCompositeOperation = "source-over";
    ctx.filter = "none";
    ctx.fillStyle = "#050505";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    // Each LED is a rounded square filling 80% of its cell, leaving an even gap.
    const side = px * 0.8;
    const inset = (px - side) / 2;
    const corner = side * 0.22;
    for (let y = 0; y < n; y++) {
      for (let x = 0; x < n; x++) {
        const o = (y * n + x) * 3;
        // LEDs cannot show very dark tones; they read as off.
        let r = this._buf[o], g = this._buf[o + 1], b = this._buf[o + 2];
        if (Math.max(r, g, b) < 10) r = g = b = 0;
        ctx.fillStyle = r + g + b && level ? `rgb(${r * level},${g * level},${b * level})` : "#141414";
        ctx.beginPath();
        ctx.roundRect(x * px + inset, y * px + inset, side, side, corner);
        ctx.fill();
      }
    }
    if (level) {
      // Soft bloom: a blurred copy added on top, like light spilling through the diffuser.
      ctx.globalCompositeOperation = "lighter";
      ctx.filter = `blur(${px * 0.55}px)`;
      ctx.globalAlpha = 0.55;
      ctx.drawImage(canvas, 0, 0);
      ctx.globalAlpha = 1;
      ctx.filter = "none";
      ctx.globalCompositeOperation = "source-over";
    }
  }

  _thumb() {
    const n = this._size;
    const c = document.createElement("canvas");
    c.width = c.height = n;
    const img = c.getContext("2d").createImageData(n, n);
    for (let i = 0; i < n * n; i++) {
      img.data.set([this._buf[i * 3], this._buf[i * 3 + 1], this._buf[i * 3 + 2], 255], i * 4);
    }
    c.getContext("2d").putImageData(img, 0, 0);
    return c.toDataURL("image/png");
  }

  /** Render an approximate preview into the buffer from a 2D-canvas drawing callback. */
  _simulate(draw) {
    const n = this._size;
    const c = document.createElement("canvas");
    c.width = c.height = n;
    const ctx = c.getContext("2d");
    ctx.fillStyle = "#000";
    ctx.fillRect(0, 0, n, n);
    draw(ctx, n);
    const data = ctx.getImageData(0, 0, n, n).data;
    const buf = new Uint8Array(n * n * 3);
    for (let i = 0; i < n * n; i++) buf.set([data[i * 4], data[i * 4 + 1], data[i * 4 + 2]], i * 3);
    this._preview = buf;
    this._paintPreview();
  }

  _paintPreview() {
    if (this._mode === "gallery" && this._anim) this._preview = this._anim.frames[this._anim.i];
    if (this._mode === "draw" || !this._preview) {
      this._paintScreen();
      return;
    }
    const saved = this._buf;
    this._buf = this._preview;
    this._paintScreen();
    this._buf = saved;
  }

  _cell(ev) {
    const canvas = this.shadowRoot.querySelector("#screen");
    const rect = canvas.getBoundingClientRect();
    const x = Math.floor(((ev.clientX - rect.left) / rect.width) * this._size);
    const y = Math.floor(((ev.clientY - rect.top) / rect.height) * this._size);
    return x >= 0 && y >= 0 && x < this._size && y < this._size ? [x, y] : null;
  }

  _setPixel(x, y, rgb) {
    const o = (y * this._size + x) * 3;
    if (this._buf[o] === rgb[0] && this._buf[o + 1] === rgb[1] && this._buf[o + 2] === rgb[2]) return;
    this._buf.set(rgb, o);
    this._pending.set(`${x},${y}`, [x, y, ...rgb]);
  }

  _fill(x, y, rgb) {
    const n = this._size;
    const o = (y * n + x) * 3;
    const target = [this._buf[o], this._buf[o + 1], this._buf[o + 2]];
    if (target.every((v, i) => v === rgb[i])) return;
    const stack = [[x, y]];
    while (stack.length) {
      const [cx, cy] = stack.pop();
      if (cx < 0 || cy < 0 || cx >= n || cy >= n) continue;
      const co = (cy * n + cx) * 3;
      if (this._buf[co] !== target[0] || this._buf[co + 1] !== target[1] || this._buf[co + 2] !== target[2]) continue;
      this._setPixel(cx, cy, rgb);
      stack.push([cx + 1, cy], [cx - 1, cy], [cx, cy + 1], [cx, cy - 1]);
    }
  }

  _pointer(ev, phase) {
    if (this._mode === "gallery") return this._panPointer(ev, phase);
    if (this._mode !== "draw") return;
    if (phase === "down") {
      this._drawing = true;
      this._history.push(this._buf.slice());
      if (this._history.length > 30) this._history.shift();
      ev.target.setPointerCapture(ev.pointerId);
    }
    if (!this._drawing) return;
    if (phase === "up") {
      this._drawing = false;
      this._flush();
      return;
    }
    const cell = this._cell(ev);
    if (!cell) return;
    const [x, y] = cell;
    if (this._tool === "picker") {
      const o = (y * this._size + x) * 3;
      this._color = rgbToHex([this._buf[o], this._buf[o + 1], this._buf[o + 2]]);
      this._tool = "pen";
      this._history.pop();
      this._drawing = false;
      this._renderControls();
      return;
    }
    if (this._tool === "fill") {
      if (phase === "down") this._fill(x, y, hexToRgb(this._color));
    } else {
      // Pointer events skip cells on fast strokes, so join them with a line.
      const rgb = this._tool === "eraser" ? [0, 0, 0] : hexToRgb(this._color);
      const [x0, y0] = phase === "down" || !this._last ? [x, y] : this._last;
      const steps = Math.max(Math.abs(x - x0), Math.abs(y - y0));
      for (let i = 0; i <= steps; i++) {
        const t = steps ? i / steps : 0;
        this._setPixel(Math.round(x0 + (x - x0) * t), Math.round(y0 + (y - y0) * t), rgb);
      }
    }
    this._last = [x, y];
    this._paintScreen();
    this._scheduleFlush();
  }

  _scheduleFlush() {
    if (!this._live || this._flushTimer) return;
    this._flushTimer = setTimeout(() => this._flush(), 120);
  }

  async _flush() {
    clearTimeout(this._flushTimer);
    this._flushTimer = null;
    if (!this._live || !this._pending.size || this._sending) return;
    const pixels = [...this._pending.values()];
    this._pending.clear();
    this._sending = true;
    // Big changes (fill, clear) go faster as one image than as many pixels.
    if (pixels.length > 200) await this._run("image", { rgb: toBase64(this._buf) }, { quiet: true });
    else await this._run("pixels", { pixels }, { quiet: true });
    this._sending = false;
    if (this._pending.size) this._scheduleFlush();
  }

  // --- rendering -------------------------------------------------------------------

  _render() {
    const root = this.shadowRoot;
    root.innerHTML = `<style>${STYLE}</style>
      <div class="toolbar">
        <ha-menu-button></ha-menu-button>
        <div class="title">iDotMatrix</div>
        <div id="status"></div>
      </div>
      ${this._current ? this._layout() : `<div class="empty">${this._emptyMessage()}</div>`}`;
    const menu = root.querySelector("ha-menu-button");
    menu.hass = this._hass;
    menu.narrow = this._narrow;
    if (!this._current) return;
    const canvas = root.querySelector("#screen");
    canvas.addEventListener("pointerdown", (e) => this._pointer(e, "down"));
    canvas.addEventListener("pointermove", (e) => this._pointer(e, "move"));
    canvas.addEventListener("pointerup", (e) => this._pointer(e, "up"));
    canvas.addEventListener("pointercancel", (e) => this._pointer(e, "up"));
    root.querySelector(".modes").addEventListener("click", (e) => {
      const btn = e.target.closest("[data-mode]");
      if (!btn) return;
      this._mode = btn.dataset.mode;
      this._preview = null;
      this._stopAnim();
      root.querySelectorAll("[data-mode]").forEach((b) => b.classList.toggle("active", b === btn));
      this._renderControls();
    });
    this._renderStatus();
    this._renderControls();
  }

  _emptyMessage() {
    if (this._error) return `Can't reach iDotMatrix Studio (${esc(this._error)}). It may still be starting; retrying&hellip;`;
    if (!this._loaded) return "Connecting&hellip;";
    return "No iDotMatrix panel is set up yet. Add one under Settings &rarr; Devices &amp; services.";
  }

  _layout() {
    return `<div class="layout">
      <section class="device">
        <div class="screen-wrap"><canvas id="screen" width="640" height="640"></canvas><div class="spinner"></div></div>
        <div class="row power-row">
          <button class="icon-btn" id="power" title="Power"><svg viewBox="0 0 24 24"><path d="M16.56 5.44l-1.45 1.45A5.97 5.97 0 0 1 18 12a6 6 0 0 1-6 6 6 6 0 0 1-6-6c0-2.17 1.16-4.06 2.88-5.12L7.44 5.44A7.96 7.96 0 0 0 4 12a8 8 0 0 0 8 8 8 8 0 0 0 8-8c0-2.72-1.36-5.12-3.44-6.56M13 3h-2v10h2"/></svg></button>
          <svg class="sun" viewBox="0 0 24 24"><path d="M12 8a4 4 0 0 0-4 4 4 4 0 0 0 4 4 4 4 0 0 0 4-4 4 4 0 0 0-4-4m0 10a6 6 0 0 1-6-6 6 6 0 0 1 6-6 6 6 0 0 1 6 6 6 6 0 0 1-6 6m8-9.31V4h-4.69L12 .69 8.69 4H4v4.69L.69 12 4 15.31V20h4.69L12 23.31 15.31 20H20v-4.69L23.31 12 20 8.69Z"/></svg>
          <input type="range" id="brightness" min="5" max="100">
        </div>
      </section>
      <section class="studio">
        <nav class="modes">${MODES.map((m) => `<button data-mode="${m.id}" class="${m.id === this._mode ? "active" : ""}"><svg viewBox="0 0 24 24"><path d="${m.icon}"/></svg><span>${m.label}</span></button>`).join("")}</nav>
        <div class="card" id="controls"></div>
      </section>
    </div>`;
  }

  _renderStatus() {
    const root = this.shadowRoot;
    const p = this._current;
    const status = root.querySelector("#status");
    if (!status || !p) return;
    const picker = this._panels.length > 1
      ? `<select id="panel-pick">${this._panels.map((x) => `<option value="${esc(x.entry_id)}" ${x.entry_id === this._entryId ? "selected" : ""}>${esc(x.name)}</option>`).join("")}</select>`
      : `<span class="name">${esc(p.name)}</span>`;
    status.innerHTML = `${picker}<span class="dot ${p.connected ? "on" : ""}" title="${p.connected ? "Connected" : "Idle (connects on demand)"}"></span>`;
    root.querySelector("#panel-pick")?.addEventListener("change", (e) => {
      this._entryId = e.target.value;
      this._buf = null;
      this._onState(this._panels);
    });
    const power = root.querySelector("#power");
    if (power) {
      power.classList.toggle("on", p.state.power);
      power.onclick = () => this._run("power", { on: !p.state.power });
    }
    const bright = root.querySelector("#brightness");
    if (bright && document.activeElement !== this && !this._brightDrag) {
      bright.value = p.state.brightness;
      bright.onpointerdown = () => (this._brightDrag = true);
      bright.onchange = async () => {
        this._brightDrag = false;
        await this._run("brightness", { value: Number(bright.value) }, { quiet: true });
      };
    }
    if (this._mode === "designs" || this._mode === "settings") this._renderControls();
    this._paintPreview();
  }

  _renderControls() {
    const el = this.shadowRoot.querySelector("#controls");
    if (!el) return;
    const fn = this[`_controls_${this._mode}`];
    el.innerHTML = "";
    fn.call(this, el);
    this._paintPreview();
  }

  _saveRow(onSave) {
    return [`<div class="row save"><input id="design-name" placeholder="Design name"><button class="ghost" id="save">Save design</button></div>`, (el) => el.querySelector("#save").addEventListener("click", onSave)];
  }

  _controls_draw(el) {
    const tools = [["pen", "Pen"], ["eraser", "Eraser"], ["fill", "Fill"], ["picker", "Pick"]];
    const [saveHtml, bindSave] = this._saveRow(() => this._saveDesign("image", { rgb: toBase64(this._buf) }, this._thumb()));
    el.innerHTML = `
      <div class="row tools">${tools.map(([id, label]) => `<button class="chip ${this._tool === id ? "active" : ""}" data-tool="${id}">${label}</button>`).join("")}</div>
      <div class="palette">${PALETTE.map((c) => `<button class="swatch ${c === this._color ? "active" : ""}" data-color="${c}" style="background:${c}"></button>`).join("")}
        <label class="swatch custom" style="background:${this._color}"><input type="color" id="custom" value="${this._color}"></label></div>
      <div class="row">
        <label class="toggle"><input type="checkbox" id="live" ${this._live ? "checked" : ""}> Live drawing</label>
        <span class="spacer"></span>
        <button class="ghost" id="undo">Undo</button>
        <button class="ghost" id="clear">Clear</button>
        <button class="primary" id="send">Send</button>
      </div>
      ${saveHtml}`;
    bindSave(el);
    el.querySelectorAll("[data-tool]").forEach((b) => b.addEventListener("click", () => { this._tool = b.dataset.tool; this._renderControls(); }));
    el.querySelectorAll("[data-color]").forEach((b) => b.addEventListener("click", () => { this._color = b.dataset.color; if (this._tool === "eraser") this._tool = "pen"; this._renderControls(); }));
    el.querySelector("#custom").addEventListener("change", (e) => { this._color = e.target.value; this._renderControls(); });
    el.querySelector("#live").addEventListener("change", (e) => { this._live = e.target.checked; });
    el.querySelector("#undo").addEventListener("click", () => {
      const prev = this._history.pop();
      if (!prev) return;
      this._buf = prev;
      this._paintScreen();
      if (this._live) this._run("image", { rgb: toBase64(this._buf) }, { quiet: true });
    });
    el.querySelector("#clear").addEventListener("click", () => {
      this._history.push(this._buf.slice());
      this._buf.fill(0);
      this._pending.clear();
      this._paintScreen();
      this._run("clear");
    });
    el.querySelector("#send").addEventListener("click", () => this._run("image", { rgb: toBase64(this._buf) }));
  }

  _controls_text(el) {
    const f = this._form.text;
    const [saveHtml, bindSave] = this._saveRow(() => this._saveDesign("text", this._textData()));
    el.innerHTML = `
      <textarea id="text" rows="2" maxlength="200">${esc(f.text)}</textarea>
      <div class="grid2">
        <label>Animation<select id="mode">${TEXT_MODES.map((m, i) => `<option value="${i}" ${i === f.mode ? "selected" : ""}>${m}</option>`).join("")}</select></label>
        <label>Color<select id="color_mode">${TEXT_COLOR_MODES.map((m, i) => `<option value="${i}" ${i === f.color_mode ? "selected" : ""}>${m}</option>`).join("")}</select></label>
        <label>Speed<input type="range" id="speed" min="1" max="100" value="${f.speed}"></label>
        <label>Text color<input type="color" id="color" value="${f.color}"></label>
        <label class="toggle"><input type="checkbox" id="bg" ${f.bg ? "checked" : ""}> Background</label>
        <label>Background color<input type="color" id="background" value="${f.background}"></label>
      </div>
      <div class="row"><span class="hint">Preview is approximate; the panel animates the text itself.</span><span class="spacer"></span><button class="primary" id="send">Show text</button></div>
      ${saveHtml}`;
    bindSave(el);
    const update = () => {
      f.text = el.querySelector("#text").value;
      f.mode = Number(el.querySelector("#mode").value);
      f.color_mode = Number(el.querySelector("#color_mode").value);
      f.speed = Number(el.querySelector("#speed").value);
      f.color = el.querySelector("#color").value;
      f.bg = el.querySelector("#bg").checked;
      f.background = el.querySelector("#background").value;
      this._previewText();
    };
    el.querySelectorAll("input,select,textarea").forEach((i) => i.addEventListener("input", update));
    el.querySelector("#send").addEventListener("click", () => f.text.trim() && this._run("text", this._textData()));
    this._previewText();
  }

  _textData() {
    const f = this._form.text;
    return { text: f.text, mode: f.mode, speed: f.speed, color_mode: f.color_mode, color: hexToRgb(f.color), ...(f.bg ? { background: hexToRgb(f.background) } : {}) };
  }

  _previewText() {
    const f = this._form.text;
    this._simulate((ctx, n) => {
      if (f.bg) { ctx.fillStyle = f.background; ctx.fillRect(0, 0, n, n); }
      const grad = ctx.createLinearGradient(0, 0, n, 0);
      ["#ff3b30", "#ffcc00", "#34c759", "#30b0ff", "#af52de"].forEach((c, i) => grad.addColorStop(i / 4, c));
      ctx.fillStyle = f.color_mode === 0 ? "#fff" : f.color_mode === 1 ? f.color : grad;
      ctx.font = `bold ${Math.round(n * 0.8)}px sans-serif`;
      ctx.textBaseline = "middle";
      ctx.fillText(f.text || " ", 1, n / 2 + 1);
    });
  }

  _controls_clock(el) {
    const f = this._form.clock;
    const [saveHtml, bindSave] = this._saveRow(() => this._saveDesign("clock", this._clockData()));
    el.innerHTML = `
      <div class="label">Style</div>
      <div class="row wrap">${Array.from({ length: 8 }, (_, i) => `<button class="chip ${i === f.style ? "active" : ""}" data-style="${i}">${i + 1}</button>`).join("")}</div>
      <div class="grid2">
        <label class="toggle"><input type="checkbox" id="date" ${f.show_date ? "checked" : ""}> Show date</label>
        <label class="toggle"><input type="checkbox" id="h24" ${f.hour24 ? "checked" : ""}> 24-hour</label>
        <label>Color<input type="color" id="color" value="${f.color}"></label>
      </div>
      <div class="row"><span class="hint">Styles are built into the panel; try them to see each one.</span><span class="spacer"></span><button class="primary" id="send">Show clock</button></div>
      ${saveHtml}`;
    bindSave(el);
    const send = () => this._run("clock", this._clockData());
    el.querySelectorAll("[data-style]").forEach((b) => b.addEventListener("click", () => { f.style = Number(b.dataset.style); this._renderControls(); send(); }));
    el.querySelector("#date").addEventListener("change", (e) => { f.show_date = e.target.checked; send(); });
    el.querySelector("#h24").addEventListener("change", (e) => { f.hour24 = e.target.checked; send(); });
    el.querySelector("#color").addEventListener("change", (e) => { f.color = e.target.value; this._previewClock(); send(); });
    el.querySelector("#send").addEventListener("click", send);
    this._previewClock();
  }

  _clockData() {
    const f = this._form.clock;
    return { style: f.style, show_date: f.show_date, hour24: f.hour24, color: hexToRgb(f.color) };
  }

  _previewClock() {
    const f = this._form.clock;
    const now = new Date();
    let h = now.getHours();
    if (!f.hour24) h = h % 12 || 12;
    this._simulate((ctx, n) => {
      ctx.fillStyle = f.color;
      ctx.font = `bold ${Math.round(n * 0.42)}px monospace`;
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(String(h).padStart(2, "0"), n / 2, n * 0.27);
      ctx.fillText(String(now.getMinutes()).padStart(2, "0"), n / 2, n * 0.72);
    });
  }

  // --- gallery -----------------------------------------------------------------

  async _loadMedia() {
    try {
      this._media = (await this._hass.callWS({ type: "idm_studio/media/list" })).items;
    } catch (err) {
      this._toast(`Could not load the gallery: ${err.message || err}`);
      this._media = [];
    }
  }

  _stopAnim() {
    clearTimeout(this._anim?.timer);
    this._anim = null;
  }

  _startAnim(frames, delays) {
    this._stopAnim();
    const anim = { frames, delays, i: 0, timer: null };
    this._anim = anim;
    const tick = () => {
      if (this._anim !== anim) return;
      this._paintPreview();
      if (frames.length < 2) return;
      anim.timer = setTimeout(() => {
        anim.i = (anim.i + 1) % frames.length;
        tick();
      }, delays[anim.i] || 100);
    };
    tick();
  }

  _schedulePreview() {
    clearTimeout(this._previewTimer);
    this._previewTimer = setTimeout(() => this._fetchPreview(), 120);
  }

  async _fetchPreview() {
    if (!this._sel) return;
    const ticket = (this._previewTicket = (this._previewTicket || 0) + 1);
    try {
      const res = await this._hass.callWS({ type: "idm_studio/preview", entry_id: this._entryId, view: { id: this._sel, ...this._view } });
      if (ticket !== this._previewTicket || this._mode !== "gallery") return;
      this._previewResult = res;
      this._startAnim(res.frames.map(fromBase64), res.delays);
      this._renderAnalysis();
    } catch (err) {
      this._toast(`Preview failed: ${err.message || err}`);
    }
  }

  _renderAnalysis() {
    const box = this.shadowRoot.querySelector("#analysis");
    const res = this._previewResult;
    if (!box || !res) return;
    const a = res.analysis;
    const secs = a.duration_ms ? `, ${(a.duration_ms / 1000).toFixed(1)} s loop` : "";
    box.innerHTML = `
      <div class="fit ${a.level}"><span class="score">${a.score}</span><span>${{ good: "Good fit", fair: "Some detail lost", poor: "Too detailed" }[a.level]}</span></div>
      <ul>${a.notes.map((n) => `<li>${esc(n)}</li>`).join("")}</ul>
      <div class="hint">${a.frames} frame${a.frames > 1 ? "s" : ""}${secs} &middot; source ${a.source[0]}&times;${a.source[1]}</div>`;
  }

  _panPointer(ev, phase) {
    if (!this._sel) return;
    const canvas = this.shadowRoot.querySelector("#screen");
    if (phase === "down") {
      this._pan = { x: ev.clientX, y: ev.clientY, vx: this._view.x, vy: this._view.y };
      canvas.setPointerCapture(ev.pointerId);
      return;
    }
    if (!this._pan) return;
    if (phase === "up") {
      this._pan = null;
      return;
    }
    const rect = canvas.getBoundingClientRect();
    const clamp = (v) => Math.max(-1, Math.min(1, v));
    this._view.x = clamp(this._pan.vx - ((ev.clientX - this._pan.x) / rect.width) * 2);
    this._view.y = clamp(this._pan.vy - ((ev.clientY - this._pan.y) / rect.height) * 2);
    this._schedulePreview();
  }

  async _upload(files) {
    for (const file of files) {
      if (!file.type.startsWith("image/")) continue;
      let blob = file;
      const isGif = file.type === "image/gif";
      if (isGif && file.size > 3 * 1024 * 1024) {
        this._toast(`${file.name} is over 3 MB; trim the GIF first`);
        continue;
      }
      if (!isGif) blob = await shrinkStill(file);
      try {
        this._setBusy(true);
        const res = await this._hass.callWS({ type: "idm_studio/media/upload", name: file.name.replace(/\.[^.]+$/, ""), file: await fileToBase64(blob) });
        await this._loadMedia();
        this._select(res.id);
      } catch (err) {
        this._toast(`Upload of ${file.name} failed: ${err.message || err}`);
      } finally {
        this._setBusy(false);
      }
    }
  }

  _select(id) {
    this._sel = id;
    // Built-in art is drawn for the panel, so keep its pixels crisp.
    this._view = { fit: "cover", zoom: 1, x: 0, y: 0, sharp: id.startsWith("builtin:") };
    this._previewResult = null;
    this._renderControls();
    this._fetchPreview();
  }

  _controls_gallery(el) {
    if (!this._media) {
      el.innerHTML = `<div class="hint">Loading gallery&hellip;</div>`;
      this._loadMedia().then(() => this._mode === "gallery" && this._renderControls());
      return;
    }
    const item = this._media.find((m) => m.id === this._sel);
    const v = this._view || {};
    const tiles = (list) => list.map((m) => `
      <button class="tile ${m.id === this._sel ? "active" : ""}" data-id="${esc(m.id)}" title="${esc(m.name)}">
        <img src="${safeImg(m.thumb)}" alt=""><span>${esc(m.name)}</span>${m.kind === "gif" ? '<i class="gif">GIF</i>' : ""}
      </button>`).join("");
    const mine = this._media.filter((m) => !m.builtin);
    const builtin = this._media.filter((m) => m.builtin);
    el.innerHTML = `
      <label class="drop" id="drop"><input type="file" id="file" accept="image/*" multiple>
        <span>Drop images or GIFs here, or click to upload</span></label>
      ${item ? `
      <div class="editor">
        <div class="row"><b class="grow">${esc(item.name)}</b>${item.builtin ? "" : `<button class="ghost" id="delete">Delete</button>`}</div>
        <div id="analysis"><div class="hint">Analysing&hellip;</div></div>
        <div class="grid2">
          <label>Framing<select id="fit">
            <option value="cover">Fill (crop)</option><option value="contain">Fit (letterbox)</option><option value="stretch">Stretch</option>
          </select></label>
          <label class="toggle"><input type="checkbox" id="sharp" ${v.sharp ? "checked" : ""}> Sharp pixels</label>
          <label class="span2">Zoom <input type="range" id="zoom" min="1" max="8" step="0.1" value="${v.zoom}"></label>
        </div>
        <div class="hint">Drag the screen to pan. The preview shows exactly what the panel will get.</div>
        <div class="row wrap">
          <button class="ghost" id="reset">Reset framing</button>
          <span class="spacer"></span>
          ${item.kind === "gif" ? "" : `<button class="ghost" id="edit">Edit in Draw</button>`}
          <button class="primary" id="send">Show on panel</button>
        </div>
        <div class="row save"><input id="design-name" placeholder="Design name" value="${esc(item.name)}"><button class="ghost" id="save">Save design</button></div>
      </div>` : ""}
      ${mine.length ? `<div class="label">Your uploads</div><div class="tiles">${tiles(mine)}</div>` : ""}
      <div class="label">Built-in animations</div><div class="tiles">${tiles(builtin)}</div>`;

    const drop = el.querySelector("#drop");
    el.querySelector("#file").addEventListener("change", (e) => this._upload([...e.target.files]));
    drop.addEventListener("dragover", (e) => { e.preventDefault(); drop.classList.add("over"); });
    drop.addEventListener("dragleave", () => drop.classList.remove("over"));
    drop.addEventListener("drop", (e) => { e.preventDefault(); drop.classList.remove("over"); this._upload([...e.dataTransfer.files]); });
    el.querySelectorAll(".tile").forEach((t) => t.addEventListener("click", () => this._select(t.dataset.id)));
    if (!item) return;

    const fit = el.querySelector("#fit");
    fit.value = v.fit;
    fit.addEventListener("change", () => { v.fit = fit.value; this._schedulePreview(); });
    el.querySelector("#sharp").addEventListener("change", (e) => { v.sharp = e.target.checked; this._schedulePreview(); });
    el.querySelector("#zoom").addEventListener("input", (e) => { v.zoom = Number(e.target.value); this._schedulePreview(); });
    el.querySelector("#reset").addEventListener("click", () => this._select(item.id));
    el.querySelector("#send").addEventListener("click", () => this._run("media", { id: item.id, ...v }));
    el.querySelector("#save").addEventListener("click", () => {
      const first = this._anim?.frames[0];
      this._saveDesign("media", { id: item.id, ...v }, first ? this._thumbOf(first) : item.thumb);
    });
    el.querySelector("#edit")?.addEventListener("click", () => {
      const first = this._anim?.frames[0];
      if (!first) return;
      this._history.push(this._buf.slice());
      this._buf = first.slice();
      this._mode = "draw";
      this._stopAnim();
      this._render();
      this._run("image", { rgb: toBase64(this._buf) });
    });
    el.querySelector("#delete")?.addEventListener("click", async () => {
      if (!confirm(`Delete ${item.name}? Designs that use it will stop working.`)) return;
      await this._hass.callWS({ type: "idm_studio/media/delete", media_id: item.id });
      this._sel = null;
      this._stopAnim();
      this._preview = null;
      await this._loadMedia();
      this._renderControls();
    });
    if (this._previewResult) this._renderAnalysis();
  }

  _thumbOf(buf) {
    const saved = this._buf;
    this._buf = buf;
    const t = this._thumb();
    this._buf = saved;
    return t;
  }

  _previewThumb() {
    const saved = this._buf;
    this._buf = this._preview;
    const t = this._thumb();
    this._buf = saved;
    return t;
  }

  _controls_effect(el) {
    const f = this._form.effect;
    const [saveHtml, bindSave] = this._saveRow(() => this._saveDesign("effect", this._effectData()));
    el.innerHTML = `
      <div class="label">Effect</div>
      <div class="row wrap">${Array.from({ length: 7 }, (_, i) => `<button class="chip ${i === f.style ? "active" : ""}" data-style="${i}">${i + 1}</button>`).join("")}</div>
      <div class="label">Colors (2 to 7)</div>
      <div class="row wrap">${f.colors.map((c, i) => `<span class="color-chip"><input type="color" data-i="${i}" value="${c}">${f.colors.length > 2 ? `<button class="x" data-rm="${i}">&times;</button>` : ""}</span>`).join("")}
        ${f.colors.length < 7 ? `<button class="chip" id="add">+ Add</button>` : ""}</div>
      <div class="row"><span class="spacer"></span><button class="primary" id="send">Show effect</button></div>
      ${saveHtml}`;
    bindSave(el);
    el.querySelectorAll("[data-style]").forEach((b) => b.addEventListener("click", () => { f.style = Number(b.dataset.style); this._renderControls(); this._run("effect", this._effectData()); }));
    el.querySelectorAll("input[data-i]").forEach((i) => i.addEventListener("input", () => { f.colors[Number(i.dataset.i)] = i.value; this._previewEffect(); }));
    el.querySelectorAll("[data-rm]").forEach((b) => b.addEventListener("click", () => { f.colors.splice(Number(b.dataset.rm), 1); this._renderControls(); }));
    el.querySelector("#add")?.addEventListener("click", () => { f.colors.push(PALETTE[(f.colors.length * 3) % PALETTE.length]); this._renderControls(); });
    el.querySelector("#send").addEventListener("click", () => this._run("effect", this._effectData()));
    this._previewEffect();
  }

  _effectData() {
    const f = this._form.effect;
    return { style: f.style, colors: f.colors.map(hexToRgb) };
  }

  _previewEffect() {
    const f = this._form.effect;
    this._simulate((ctx, n) => {
      const grad = ctx.createLinearGradient(0, 0, n, n);
      f.colors.forEach((c, i) => grad.addColorStop(i / (f.colors.length - 1), c));
      ctx.fillStyle = grad;
      ctx.fillRect(0, 0, n, n);
    });
  }

  _controls_color(el) {
    const [saveHtml, bindSave] = this._saveRow(() => this._saveDesign("color", { color: hexToRgb(this._form.color) }, this._previewThumb()));
    el.innerHTML = `
      <div class="palette big">${PALETTE.filter((c) => c !== "#000000").map((c) => `<button class="swatch" data-color="${c}" style="background:${c}"></button>`).join("")}
        <label class="swatch custom" style="background:${this._form.color}"><input type="color" id="custom" value="${this._form.color}"></label></div>
      <div class="hint">Fills the whole panel with one color, like a lamp.</div>
      ${saveHtml}`;
    bindSave(el);
    const pick = (c) => {
      this._form.color = c;
      this._simulate((ctx, n) => { ctx.fillStyle = c; ctx.fillRect(0, 0, n, n); });
      this._run("color", { color: hexToRgb(c) });
    };
    el.querySelectorAll("[data-color]").forEach((b) => b.addEventListener("click", () => pick(b.dataset.color)));
    el.querySelector("#custom").addEventListener("change", (e) => pick(e.target.value));
    this._simulate((ctx, n) => { ctx.fillStyle = this._form.color; ctx.fillRect(0, 0, n, n); });
  }

  _controls_score(el) {
    const s = { ...this._current.state.scoreboard };
    const [saveHtml, bindSave] = this._saveRow(() => this._saveDesign("scoreboard", { ...s }));
    el.innerHTML = `
      <div class="score">
        ${["left", "right"].map((side) => `<div class="side">
          <button class="big" data-side="${side}" data-d="1">+</button>
          <input type="number" min="0" max="999" data-num="${side}" value="${s[side]}">
          <button class="big" data-side="${side}" data-d="-1">&minus;</button></div>`).join('<div class="colon">:</div>')}
      </div>
      <div class="row"><span class="spacer"></span><button class="ghost" id="reset">Reset</button><button class="primary" id="send">Show scoreboard</button></div>
      ${saveHtml}`;
    bindSave(el);
    const send = () => {
      clearTimeout(this._scoreTimer);
      this._scoreTimer = setTimeout(() => this._run("scoreboard", { ...s }, { quiet: true }), 250);
    };
    const show = () => {
      el.querySelectorAll("[data-num]").forEach((i) => (i.value = s[i.dataset.num]));
      this._simulate((ctx, n) => {
        ctx.font = `bold ${Math.round(n * 0.38)}px monospace`;
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillStyle = "#ff3b30"; ctx.fillText(String(s.left), n * 0.5, n * 0.27);
        ctx.fillStyle = "#30b0ff"; ctx.fillText(String(s.right), n * 0.5, n * 0.73);
      });
    };
    el.querySelectorAll("[data-side]").forEach((b) => b.addEventListener("click", () => {
      const k = b.dataset.side;
      s[k] = Math.max(0, Math.min(999, s[k] + Number(b.dataset.d)));
      show(); send();
    }));
    el.querySelectorAll("[data-num]").forEach((i) => i.addEventListener("change", () => {
      s[i.dataset.num] = Math.max(0, Math.min(999, Number(i.value) || 0));
      show(); send();
    }));
    el.querySelector("#reset").addEventListener("click", () => { s.left = s.right = 0; show(); send(); });
    el.querySelector("#send").addEventListener("click", () => this._run("scoreboard", { ...s }));
    show();
  }

  _controls_timer(el) {
    const t = this._form.timer;
    el.innerHTML = `
      <div class="label">Countdown</div>
      <div class="row">
        <input type="number" id="min" min="0" max="255" value="${t.minutes}" class="num"> min
        <input type="number" id="sec" min="0" max="59" value="${t.seconds}" class="num"> sec
      </div>
      <div class="row wrap">${["start", "pause", "restart", "stop"].map((a) => `<button class="chip" data-cd="${a}">${a[0].toUpperCase() + a.slice(1)}</button>`).join("")}</div>
      <div class="label">Stopwatch</div>
      <div class="row wrap">${["start", "pause", "resume", "reset"].map((a) => `<button class="chip" data-sw="${a}">${a[0].toUpperCase() + a.slice(1)}</button>`).join("")}</div>`;
    const read = () => {
      t.minutes = Math.max(0, Math.min(255, Number(el.querySelector("#min").value) || 0));
      t.seconds = Math.max(0, Math.min(59, Number(el.querySelector("#sec").value) || 0));
    };
    el.querySelectorAll("[data-cd]").forEach((b) => b.addEventListener("click", () => { read(); this._run("countdown", { action: b.dataset.cd, minutes: t.minutes, seconds: t.seconds }); }));
    el.querySelectorAll("[data-sw]").forEach((b) => b.addEventListener("click", () => this._run("stopwatch", { action: b.dataset.sw })));
    this._simulate((ctx, n) => {
      ctx.fillStyle = "#ffcc00";
      ctx.font = `bold ${Math.round(n * 0.34)}px monospace`;
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(`${String(t.minutes).padStart(2, "0")}`, n / 2, n * 0.28);
      ctx.fillText(`${String(t.seconds).padStart(2, "0")}`, n / 2, n * 0.72);
    });
  }

  _controls_designs(el) {
    const p = this._current;
    const current = p.state.design;
    if (!p.designs.length) {
      el.innerHTML = `<div class="hint">No saved designs yet. Use "Save design" in any mode. Saved designs also appear in the Design entity, so automations and HomeKit can pick them.</div>`;
      return;
    }
    el.innerHTML = `<div class="designs">${p.designs.map((d) => `
      <div class="design ${d.id === current ? "active" : ""}" data-id="${esc(d.id)}">
        ${d.thumb ? `<img src="${safeImg(d.thumb)}" alt="">` : `<div class="glyph">${esc(d.action)}</div>`}
        <span>${esc(d.name)}</span>
        <button class="x" data-del="${esc(d.id)}" title="Delete">&times;</button>
      </div>`).join("")}</div>`;
    el.querySelectorAll(".design").forEach((d) => d.addEventListener("click", (e) => {
      if (e.target.closest("[data-del]")) return;
      this._run("design", { id: d.dataset.id });
    }));
    el.querySelectorAll("[data-del]").forEach((b) => b.addEventListener("click", async () => {
      await this._hass.callWS({ type: "idm_studio/design/delete", entry_id: this._entryId, design_id: b.dataset.del });
    }));
  }

  _controls_settings(el) {
    const p = this._current;
    el.innerHTML = `
      <div class="grid2">
        <label class="toggle"><input type="checkbox" id="flip" ${p.state.flip ? "checked" : ""}> Rotate 180&deg;</label>
        <button class="ghost" id="sync">Sync clock</button>
      </div>
      <dl>
        <dt>Panel</dt><dd>${esc(p.name)}</dd>
        <dt>Address</dt><dd>${esc(p.address)}</dd>
        <dt>Size</dt><dd>${p.size} &times; ${p.size}</dd>
        <dt>Link</dt><dd>${p.connected ? "Connected" : "Idle, connects when you send something"}</dd>
      </dl>`;
    el.querySelector("#flip").addEventListener("change", (e) => this._run("flip", { flip: e.target.checked }));
    el.querySelector("#sync").addEventListener("click", async () => (await this._run("sync_time")) && this._toast("Clock synced"));
  }
}

const STYLE = `
:host { display: block; min-height: 100vh; background: var(--primary-background-color); color: var(--primary-text-color); font-family: var(--paper-font-body1_-_font-family, Roboto, sans-serif); }
* { box-sizing: border-box; }
.toolbar { display: flex; align-items: center; height: var(--header-height, 56px); padding: 0 12px; gap: 8px; background: var(--app-header-background-color, var(--primary-color)); color: var(--app-header-text-color, #fff); border-bottom: var(--app-header-border-bottom, none); }
.title { font-size: 20px; flex: 1; margin-left: 4px; }
#status { display: flex; align-items: center; gap: 8px; font-size: 14px; }
#status select { background: transparent; color: inherit; border: 1px solid rgba(255,255,255,.4); border-radius: 6px; padding: 4px; }
.dot { width: 10px; height: 10px; border-radius: 50%; background: #888; }
.dot.on { background: #34c759; box-shadow: 0 0 6px #34c759; }
.empty { padding: 32px; text-align: center; color: var(--secondary-text-color); }
.layout { display: grid; grid-template-columns: minmax(260px, 440px) minmax(300px, 1fr); gap: 24px; padding: 24px; max-width: 1200px; margin: 0 auto; }
@media (max-width: 800px) { .layout { grid-template-columns: 1fr; padding: 16px; gap: 16px; } }
.device { display: flex; flex-direction: column; gap: 12px; }
.screen-wrap { position: relative; background: #000; border-radius: 20px; padding: 14px; box-shadow: 0 10px 30px rgba(0,0,0,.35), inset 0 0 0 2px #1c1c1c; }
#screen { width: 100%; aspect-ratio: 1; display: block; touch-action: none; cursor: crosshair; border-radius: 6px; }
.spinner { position: absolute; top: 10px; right: 10px; width: 18px; height: 18px; border-radius: 50%; border: 2px solid #555; border-top-color: #fff; opacity: 0; animation: spin .8s linear infinite; }
.busy .spinner { opacity: 1; }
@keyframes spin { to { transform: rotate(360deg); } }
.row { display: flex; align-items: center; gap: 8px; margin: 10px 0; }
.row.wrap { flex-wrap: wrap; }
.spacer { flex: 1; }
.power-row { background: var(--card-background-color); border-radius: 14px; padding: 8px 14px; margin: 0; }
.power-row input { flex: 1; accent-color: var(--primary-color); }
.sun { width: 20px; fill: var(--secondary-text-color); }
.icon-btn { width: 40px; height: 40px; border-radius: 50%; border: none; background: var(--secondary-background-color); cursor: pointer; display: grid; place-items: center; }
.icon-btn svg { width: 22px; fill: var(--secondary-text-color); }
.icon-btn.on { background: var(--primary-color); }
.icon-btn.on svg { fill: #fff; }
.studio { display: flex; flex-direction: column; gap: 16px; min-width: 0; }
.modes { display: grid; grid-template-columns: repeat(5, 1fr); gap: 8px; }
@media (max-width: 480px) { .modes { grid-template-columns: repeat(5, 1fr); gap: 4px; } .modes span { font-size: 10px; } }
.modes button { display: flex; flex-direction: column; align-items: center; gap: 4px; padding: 10px 4px; border-radius: 14px; border: none; cursor: pointer; background: var(--card-background-color); color: var(--primary-text-color); box-shadow: var(--ha-card-box-shadow, none); font-size: 12px; }
.modes svg { width: 26px; height: 26px; fill: var(--secondary-text-color); }
.modes button.active { background: var(--primary-color); color: #fff; }
.modes button.active svg { fill: #fff; }
.card { background: var(--card-background-color); border-radius: var(--ha-card-border-radius, 12px); padding: 16px; box-shadow: var(--ha-card-box-shadow, none); border: 1px solid var(--divider-color); }
.label { font-size: 13px; color: var(--secondary-text-color); margin-top: 8px; }
.hint { font-size: 12px; color: var(--secondary-text-color); }
button.chip, button.ghost, button.primary { border-radius: 18px; padding: 8px 14px; cursor: pointer; font-size: 14px; border: 1px solid var(--divider-color); background: transparent; color: var(--primary-text-color); }
button.chip.active { background: var(--primary-color); color: #fff; border-color: var(--primary-color); }
button.primary { background: var(--primary-color); border-color: var(--primary-color); color: #fff; }
.palette { display: grid; grid-template-columns: repeat(auto-fill, minmax(30px, 1fr)); gap: 6px; margin: 8px 0; }
.palette.big { grid-template-columns: repeat(auto-fill, minmax(44px, 1fr)); }
.swatch { aspect-ratio: 1; border-radius: 50%; border: 2px solid var(--divider-color); cursor: pointer; position: relative; padding: 0; }
.swatch.active { outline: 3px solid var(--primary-color); outline-offset: 1px; }
.swatch.custom { display: block; background-image: conic-gradient(red, yellow, lime, aqua, blue, magenta, red) !important; }
.swatch input { opacity: 0; position: absolute; inset: 0; width: 100%; height: 100%; cursor: pointer; }
.toggle { display: flex; align-items: center; gap: 6px; font-size: 14px; }
.grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 10px 16px; margin: 10px 0; }
.grid2 label:not(.toggle) { display: flex; flex-direction: column; gap: 4px; font-size: 13px; color: var(--secondary-text-color); }
select, input[type=number], input:not([type]), textarea { background: var(--secondary-background-color); color: var(--primary-text-color); border: 1px solid var(--divider-color); border-radius: 8px; padding: 8px; font: inherit; }
textarea { width: 100%; resize: vertical; font-size: 18px; }
input[type=color] { width: 100%; height: 36px; border: none; background: none; padding: 0; cursor: pointer; }
.color-chip { position: relative; width: 44px; }
.color-chip input { height: 44px; border-radius: 50%; }
.x { position: absolute; top: -6px; right: -6px; width: 20px; height: 20px; border-radius: 50%; border: none; background: var(--error-color, #db4437); color: #fff; cursor: pointer; line-height: 1; padding: 0; }
.save { border-top: 1px solid var(--divider-color); padding-top: 12px; margin-top: 14px; }
.save input { flex: 1; min-width: 0; }
.drop { display: block; border: 2px dashed var(--divider-color); border-radius: 12px; padding: 24px; text-align: center; cursor: pointer; color: var(--secondary-text-color); }
.drop input { display: none; }
.score { display: flex; justify-content: center; align-items: center; gap: 16px; margin: 8px 0; }
.side { display: flex; flex-direction: column; align-items: center; gap: 8px; }
.side input { width: 96px; font-size: 36px; text-align: center; }
.colon { font-size: 40px; color: var(--secondary-text-color); }
button.big { width: 64px; height: 44px; border-radius: 12px; border: none; background: var(--secondary-background-color); color: var(--primary-text-color); font-size: 24px; cursor: pointer; }
.num { width: 80px; }
.designs { display: grid; grid-template-columns: repeat(auto-fill, minmax(96px, 1fr)); gap: 12px; }
.design { position: relative; display: flex; flex-direction: column; align-items: center; gap: 6px; padding: 8px; border-radius: 12px; cursor: pointer; border: 1px solid var(--divider-color); font-size: 13px; text-align: center; }
.design.active { border-color: var(--primary-color); box-shadow: 0 0 0 2px var(--primary-color); }
.design img, .design .glyph { width: 72px; height: 72px; image-rendering: pixelated; border-radius: 8px; background: #000; }
.design .glyph { display: grid; place-items: center; color: #ffcc00; font-family: monospace; text-transform: uppercase; font-size: 12px; }
.drop.over { border-color: var(--primary-color); color: var(--primary-color); }
.tiles { display: grid; grid-template-columns: repeat(auto-fill, minmax(84px, 1fr)); gap: 10px; margin: 8px 0 14px; }
.tile { position: relative; display: flex; flex-direction: column; align-items: center; gap: 4px; padding: 6px; border-radius: 12px; border: 1px solid var(--divider-color); background: transparent; color: var(--primary-text-color); cursor: pointer; font-size: 12px; }
.tile.active { border-color: var(--primary-color); box-shadow: 0 0 0 2px var(--primary-color); }
.tile img { width: 64px; height: 64px; image-rendering: pixelated; border-radius: 6px; background: #000; }
.tile span { max-width: 100%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.tile .gif { position: absolute; top: 4px; right: 4px; font-style: normal; font-size: 9px; background: var(--primary-color); color: #fff; border-radius: 4px; padding: 1px 4px; }
.editor { border: 1px solid var(--divider-color); border-radius: 12px; padding: 12px; margin: 12px 0; }
.grow { flex: 1; }
.span2 { grid-column: span 2; }
.fit { display: flex; align-items: center; gap: 10px; font-weight: 500; }
.fit .score { display: grid; place-items: center; width: 40px; height: 40px; border-radius: 50%; color: #fff; font-size: 15px; }
.fit.good .score { background: var(--success-color, #34c759); }
.fit.fair .score { background: var(--warning-color, #ff9500); }
.fit.poor .score { background: var(--error-color, #db4437); }
#analysis ul { margin: 6px 0; padding-left: 20px; font-size: 13px; }
dl { display: grid; grid-template-columns: auto 1fr; gap: 6px 16px; font-size: 14px; }
dt { color: var(--secondary-text-color); }
dd { margin: 0; }
`;

// A new panel.js URL (after an update) loads this module again in open tabs.
if (!customElements.get("idm-studio-panel")) customElements.define("idm-studio-panel", IdmStudioPanel);
