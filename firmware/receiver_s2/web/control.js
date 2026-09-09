/* Same-host controller. Every drive command consumes the last server token. */
(() => {
  'use strict';
  const pad = document.getElementById('joystick');
  const knob = document.getElementById('knob');
  const status = document.getElementById('status');
  const dot = document.getElementById('connection-dot');
  const speed = document.getElementById('speed');
  const driveState = document.getElementById('drive-state');
  const SEND_MS = 50, ACK_MS = 180, RECONNECT_MS = 750;
  let socket = null, reconnectTimer = null, ackTimer = null;
  let token = null, ready = false, held = false, pointer = null;
  let phase = 'stopped', gesture = 0, desired = {x: 0, y: 0};
  let pending = null, lastSent = -Infinity;

  function connected() { return socket && socket.readyState === WebSocket.OPEN; }
  function render() {
    pad.setAttribute('aria-disabled', String(!ready || !connected()));
    pad.classList.toggle('held', held);
    dot.classList.toggle('ready', ready && connected());
    speed.textContent = phase === 'driving' ? String(Math.round(Math.hypot(desired.x, desired.y) / 10)) : '0';
    driveState.textContent = phase === 'arming' ? 'Hold to arm…' : held ? 'Driving' : 'Stopped';
  }
  function clearPending() {
    if (ackTimer !== null) clearTimeout(ackTimer);
    ackTimer = null; pending = null;
  }
  function cancelGesture(sendStop) {
    const oldPointer = pointer;
    pointer = null; held = false; phase = 'stopped'; desired = {x: 0, y: 0};
    ++gesture;
    pad.style.setProperty('--knob-x', '0px');
    pad.style.setProperty('--knob-y', '0px');
    if (oldPointer !== null && pad.hasPointerCapture(oldPointer)) pad.releasePointerCapture(oldPointer);
    // "stop" intentionally bypasses the outstanding-command restriction.
    if (sendStop && connected()) {
      token = null; // Stop invalidates the old token; wait for its fresh reply.
      if (!pending) {
        pending = {gesture, centeredHold: false, sentAt: performance.now()};
        const current = socket;
        ackTimer = setTimeout(() => {
          if (socket === current && pending) disconnect('Response timed out');
        }, ACK_MS + 1);
      }
      try { socket.send('stop'); } catch (_) { disconnect('Connection lost'); }
    }
    render();
  }
  function scheduleReconnect() {
    if (reconnectTimer !== null) return;
    reconnectTimer = setTimeout(() => { reconnectTimer = null; connect(); }, RECONNECT_MS);
  }
  function disconnect(message) {
    const old = socket;
    socket = null; ready = false; token = null;
    clearPending(); cancelGesture(false);
    status.textContent = message + ' · reconnecting…';
    if (old && old.readyState < WebSocket.CLOSING) old.close();
    scheduleReconnect();
  }
  function pump() {
    if (!connected() || token === null || pending || performance.now() - lastSent < SEND_MS) return;
    const active = held && ready;
    const move = active && phase === 'driving' ? desired : {x: 0, y: 0};
    pending = {gesture, centeredHold: active && phase === 'arming', sentAt: performance.now()};
    const packet = `${token},${active ? 1 : 0},${move.x},${move.y}`;
    token = null; lastSent = performance.now();
    const current = socket;
    ackTimer = setTimeout(() => {
      if (socket === current && pending) disconnect('Response timed out');
    }, ACK_MS + 1);
    try { socket.send(packet); } catch (_) { disconnect('Connection lost'); }
  }
  function connect() {
    cancelGesture(false); clearPending(); ready = false; token = null; lastSent = -Infinity;
    status.textContent = 'Connecting…'; render();
    let current;
    try {
      const bootstrap = document.querySelector('meta[name="control-token"]').content;
      current = new WebSocket(`${location.protocol === 'https:' ? 'wss:' : 'ws:'}//${location.host}/ws?token=${encodeURIComponent(bootstrap)}`);
    } catch (_) { disconnect('Connection unavailable'); return; }
    socket = current;
    current.addEventListener('open', () => {
      if (socket !== current) return;
      status.textContent = 'Checking the car…';
      pending = {gesture, centeredHold: false, sentAt: performance.now()};
      ackTimer = setTimeout(() => {
        if (socket === current && pending) disconnect('Response timed out');
      }, ACK_MS + 1);
      try { current.send('hello'); } catch (_) { disconnect('Connection lost'); }
    });
    current.addEventListener('message', event => {
      if (socket !== current) return;
      // A suspended event loop can deliver a late message before its timer.
      if (pending && performance.now() - pending.sentAt > ACK_MS) {
        disconnect('Response timed out'); return;
      }
      let data;
      try { data = JSON.parse(event.data); } catch (_) { disconnect('Invalid car response'); return; }
      if (!data || !Number.isInteger(data.token) || data.token < 0 || data.token > 0xffffffff ||
          typeof data.ready !== 'boolean' || typeof data.armed !== 'boolean' || typeof data.reset !== 'boolean') {
        disconnect('Invalid car response'); return;
      }
      const acknowledged = pending;
      clearPending(); token = data.token; ready = data.ready;
      if (data.reset) cancelGesture(false); // Never answer a reset with another stop.
      else if (!ready && held) cancelGesture(true);
      else if (held && phase === 'driving' && !data.armed) cancelGesture(false);
      else if (held && phase === 'arming' && acknowledged && acknowledged.centeredHold &&
               acknowledged.gesture === gesture && data.armed) phase = 'driving';
      status.textContent = typeof data.reason === 'string' && data.reason ? data.reason : ready ? 'Ready' : 'Not ready';
      render(); pump();
    });
    current.addEventListener('close', () => { if (socket === current) disconnect('Disconnected'); });
    current.addEventListener('error', () => { if (socket === current) disconnect('Connection lost'); });
  }
  function updatePosition(event) {
    const rect = pad.getBoundingClientRect();
    const radius = Math.max(1, Math.min(rect.width, rect.height) / 2 - knob.offsetWidth / 2 - 10);
    let x = (event.clientX - rect.left - rect.width / 2) / radius;
    let y = (rect.top + rect.height / 2 - event.clientY) / radius;
    const length = Math.hypot(x, y);
    if (length > 1) { x /= length; y /= length; }
    let ix = Math.round(x * 1000), iy = Math.round(y * 1000);
    const roundedLength = Math.hypot(ix, iy);
    if (roundedLength > 1000) { ix = Math.trunc(ix * 1000 / roundedLength); iy = Math.trunc(iy * 1000 / roundedLength); }
    desired = {x: ix, y: iy};
    pad.style.setProperty('--knob-x', `${x * radius}px`);
    pad.style.setProperty('--knob-y', `${-y * radius}px`);
    render();
  }
  pad.addEventListener('pointerdown', event => {
    if (!ready || !connected() || held || event.isPrimary === false || (event.pointerType === 'mouse' && event.button !== 0)) return;
    event.preventDefault(); pointer = event.pointerId; held = true; phase = 'arming'; ++gesture;
    pad.setPointerCapture(pointer); updatePosition(event); pump();
  });
  pad.addEventListener('pointermove', event => {
    if (held && event.pointerId === pointer) { event.preventDefault(); updatePosition(event); }
  });
  function release(event) {
    if (held && event.pointerId === pointer) cancelGesture(true);
  }
  pad.addEventListener('pointerup', release);
  pad.addEventListener('pointercancel', release);
  pad.addEventListener('lostpointercapture', release);
  window.addEventListener('blur', () => cancelGesture(true));
  window.addEventListener('pagehide', () => cancelGesture(true));
  document.addEventListener('visibilitychange', () => { if (document.hidden) cancelGesture(true); });
  setInterval(pump, 25);
  connect();
})();
