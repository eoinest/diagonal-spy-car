// Run: node firmware/tests/web_control_ui_test.mjs
// No web server: browser events, sockets and time are isolated test doubles.
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
const source = readFileSync(new URL('../receiver_s2/web/control.js', import.meta.url), 'utf8');

function fixture() {
  let now = 0, timerId = 0;
  const timers = new Map();
  class Events {
    listeners = {};
    addEventListener(type, fn) { (this.listeners[type] ||= []).push(fn); }
    emit(type, event = {}) { for (const fn of this.listeners[type] || []) fn(event); }
  }
  class Element extends Events {
    textContent = ''; attributes = {}; captured = null; offsetWidth = 76;
    style = {values: {}, setProperty(k, v) { this.values[k] = v; }};
    classList = {toggle() {}};
    setAttribute(k, v) { this.attributes[k] = v; }
    getBoundingClientRect() { return {left: 0, top: 0, width: 240, height: 240}; }
    setPointerCapture(id) { this.captured = id; }
    hasPointerCapture(id) { return this.captured === id; }
    releasePointerCapture(id) { if (this.captured === id) this.captured = null; }
  }
  const elements = new Map();
  const document = new Events();
  document.hidden = false;
  document.getElementById = id => {
    if (!elements.has(id)) elements.set(id, new Element());
    return elements.get(id);
  };
  document.querySelector = () => ({content: 'test token&only'});
  const window = new Events();
  class Socket extends Events {
    static OPEN = 1; static CLOSING = 2; static all = [];
    readyState = 0; sent = [];
    constructor(url) { super(); this.url = url; Socket.all.push(this); }
    send(data) { assert.equal(this.readyState, 1); this.sent.push(data); }
    close() { this.readyState = 3; this.emit('close'); }
    open() { this.readyState = 1; this.emit('open'); }
    reply(data = {}) {
      this.emit('message', {data: JSON.stringify({token: 42, ready: true, armed: false, battery: 7.8, reason: 'Ready', reset: false, ...data})});
    }
  }
  function schedule(fn, delay, repeat = 0) {
    const id = ++timerId; timers.set(id, {fn, at: now + delay, repeat}); return id;
  }
  function advance(ms) {
    const until = now + ms;
    for (;;) {
      const due = [...timers.entries()].filter(([, t]) => t.at <= until).sort((a, b) => a[1].at - b[1].at || a[0] - b[0])[0];
      if (!due) break;
      const [id, timer] = due; now = timer.at;
      if (timer.repeat) timer.at += timer.repeat; else timers.delete(id);
      timer.fn();
    }
    now = until;
  }
  vm.runInNewContext(source, {
    document, window, WebSocket: Socket, location: {protocol: 'http:', host: 'spy-car.local'},
    performance: {now: () => now}, setTimeout: (fn, ms) => schedule(fn, ms),
    clearTimeout: id => timers.delete(id), setInterval: (fn, ms) => schedule(fn, ms, ms),
    console
  });
  const pad = document.getElementById('joystick');
  function point(type, x = 192, y = 120, id = 1) {
    pad.emit(type, {pointerId: id, pointerType: 'touch', isPrimary: true, button: 0,
      clientX: x, clientY: y, preventDefault() {}});
  }
  function online() {
    const s = Socket.all.at(-1); s.open(); assert.equal(s.sent[0], 'hello');
    s.reply(); assert.equal(s.sent.at(-1), '42,0,0,0'); s.reply(); return s;
  }
  function armed() {
    const s = online(); point('pointerdown'); advance(50);
    assert.equal(s.sent.at(-1), '42,1,0,0'); s.reply({armed: true}); return s;
  }
  return {Socket, pad, point, advance, online, armed, window, document, elements,
    elapseWithoutTimers: ms => { now += ms; }};
}

let count = 0;
function test(name, fn) { fn(); ++count; console.log(`PASS ${name}`); }
test('same-origin token handshake; unavailable state prevents gestures', () => {
  const f = fixture(), s = f.Socket.all[0];
  assert.equal(s.url, 'ws://spy-car.local/ws?token=test%20token%26only');
  f.point('pointerdown'); assert.equal(s.sent.length, 0);
  s.open(); s.reply({ready: false, reason: 'Calibrate servo neutral'});
  s.reply({ready: false}); f.point('pointerdown'); f.advance(50);
  assert.equal(s.sent.at(-1), '42,0,0,0');
});
test('center-only arming, then continuous circular right/forward control', () => {
  const f = fixture(), s = f.online(); f.point('pointerdown', 999, -999); f.advance(50);
  assert.equal(s.sent.at(-1), '42,1,0,0'); s.reply({armed: false}); f.advance(50);
  assert.equal(s.sent.at(-1), '42,1,0,0'); s.reply({armed: true}); f.advance(50);
  const [, held, x, y] = s.sent.at(-1).split(',').map(Number);
  assert.equal(held, 1); assert.ok(x > 0 && y > 0 && Math.hypot(x, y) <= 1000);
});
test('only one movement outstanding; release bypasses it immediately', () => {
  const f = fixture(), s = f.armed(); f.advance(50);
  const sent = s.sent.length; f.advance(100); assert.equal(s.sent.length, sent);
  f.point('pointerup'); assert.equal(s.sent.at(-1), 'stop');
  s.reply({reset: true}); f.advance(50);
  assert.equal(s.sent.at(-1), '42,0,0,0');
  assert.equal(f.elements.get('speed').textContent, '0');
});
test('new gesture cannot use an old gesture arming acknowledgement', () => {
  const f = fixture(), s = f.online(); f.point('pointerdown'); f.advance(50);
  f.point('pointerup'); f.point('pointerdown', 192, 120, 2);
  s.reply({armed: true}); f.advance(50);
  assert.equal(s.sent.at(-1), '42,1,0,0');
});
test('server reset cancels gesture without recursively sending stop', () => {
  const f = fixture(), s = f.armed(); f.advance(50);
  const stops = s.sent.filter(x => x === 'stop').length;
  s.reply({reset: true, armed: false}); f.advance(50);
  assert.equal(s.sent.filter(x => x === 'stop').length, stops);
  assert.equal(s.sent.at(-1), '42,0,0,0');
});
for (const kind of ['pointercancel', 'lostpointercapture', 'blur', 'hidden', 'stop']) {
  test(`${kind} cancels motion immediately`, () => {
    const f = fixture(), s = f.armed();
    if (kind === 'blur') f.window.emit('blur');
    else if (kind === 'hidden') { f.document.hidden = true; f.document.emit('visibilitychange'); }
    else if (kind === 'stop') f.elements.get('stop').emit('click');
    else f.point(kind);
    assert.equal(s.sent.at(-1), 'stop');
    assert.equal(f.elements.get('drive-state').textContent, 'Stopped');
  });
}
test('stale acknowledgement disconnects and reconnect never resumes hold', () => {
  const f = fixture(), s = f.armed(); f.advance(50); f.advance(181);
  assert.equal(s.readyState, 3); assert.equal(f.pad.attributes['aria-disabled'], 'true');
  f.advance(750); const fresh = f.online(); f.advance(50);
  assert.equal(fresh.sent.at(-1), '42,0,0,0');
  assert.equal(f.elements.get('drive-state').textContent, 'Stopped');
});
test('unacknowledged stop also times out', () => {
  const f = fixture(), s = f.online(); f.elements.get('stop').emit('click');
  f.advance(181); assert.equal(s.readyState, 3);
});
test('late ACK cannot evade watchdog after a suspended event loop', () => {
  const f = fixture(), s = f.armed(); f.advance(50);
  f.elapseWithoutTimers(181); s.reply({armed: true});
  assert.equal(s.readyState, 3);
});
test('unexpected server disarm requires a fresh gesture', () => {
  const f = fixture(), s = f.armed(); f.advance(50);
  s.reply({armed: false}); f.advance(50);
  assert.equal(s.sent.at(-1), '42,0,0,0');
  assert.equal(f.elements.get('drive-state').textContent, 'Stopped');
});
test('malformed status disconnects; reason is treated as text', () => {
  const f = fixture(), s = f.online(); s.reply({reason: '<img onerror=bad>'});
  assert.equal(f.elements.get('status').textContent, '<img onerror=bad>');
  s.reply({token: -1}); assert.equal(s.readyState, 3);
});
console.log(`web_control_ui_test: ${count} cases passed`);
