#include <cassert>
#include <cstdio>
#include "SpyCarProtocol.h"

using namespace spycar;

Packet packet(uint32_t sequence, bool held = false, int throttle = 0,
              uint32_t session = 1) {
  return {kMagic, kVersion, uint8_t(held ? kDeadman : 0), 0, session, sequence,
          int16_t(throttle), 0};
}

void arm(DriveGate &gate, uint32_t time = 100) {
  gate.inhibit(false);
  assert(gate.accept(packet(1), time, time));
  assert(gate.accept(packet(2, true), time + 20, time + 20));
  assert(gate.armed);
}

int main() {
  {
    DriveGate gate;
    gate.accept(packet(1), 100, 100);
    gate.accept(packet(2, true), 120, 120);
    assert(!gate.armed); // Inhibited by default.
  }
  {
    DriveGate gate;
    gate.inhibit(false);
    assert(!gate.accept(packet(1, true, 800), 100, 100));
    gate.accept(packet(2), 120, 120);
    gate.accept(packet(3, true, 800), 140, 140);
    assert(!gate.armed); // Pressing with moved stick consumes readiness.
    gate.accept(packet(4, true), 160, 160);
    assert(!gate.armed);
    gate.accept(packet(5), 180, 180);
    gate.accept(packet(6, true), 200, 200);
    assert(gate.armed);
  }
  {
    DriveGate gate;
    arm(gate);
    gate.accept(packet(3, true, 750), 140, 140);
    assert(gate.throttle == 750);
    gate.accept(packet(4, false, 750), 160, 160);
    assert(!gate.armed && gate.throttle == 0);
    gate.accept(packet(5, true), 180, 180);
    assert(!gate.armed); // Release must also be centered.
  }
  {
    DriveGate gate;
    arm(gate);
    gate.accept(packet(3, true, 600), 140, 140);
    gate.tick(389);
    assert(gate.armed); // Fresh through timeout-1, expires exactly at timeout.
    gate.tick(390);
    assert(!gate.armed && gate.throttle == 0);
    gate.accept(packet(4, true), 400, 400);
    assert(!gate.armed); // Reconnected held deadman cannot rearm.
    gate.accept(packet(5), 420, 420);
    gate.accept(packet(6, true), 440, 440);
    assert(gate.armed);
  }
  {
    DriveGate gate;
    arm(gate);
    assert(!gate.accept(packet(2, true, 1000), 200, 200));
    assert(!gate.accept(packet(1, true, 1000), 220, 220));
    gate.tick(370);
    assert(!gate.armed); // Duplicates do not refresh freshness.
    assert(!gate.accept(packet(3), 100, 400)); // Queue age is checked.
  }
  {
    DriveGate gate;
    arm(gate);
    assert(!gate.accept(packet(1, true, 900, 2), 140, 140));
    assert(!gate.armed); // New session immediately disarms.
    gate.accept(packet(2, false, 0, 2), 160, 160);
    gate.accept(packet(3, true, 0, 2), 180, 180);
    assert(gate.armed);
    gate.inhibit(true);
    gate.accept(packet(4, false, 0, 2), 200, 200);
    gate.inhibit(false);
    gate.accept(packet(5, true, 0, 2), 220, 220);
    assert(!gate.armed); // Release while inhibited cannot prepare rearming.
  }
  {
    DriveGate gate;
    gate.inhibit(false);
    gate.accept(packet(0xfffffffeUL), 0xffffffd0UL, 0xffffffd0UL);
    gate.accept(packet(0xffffffffUL, true), 0xffffffe0UL, 0xffffffe0UL);
    gate.accept(packet(0, true, 100), 0xfffffff0UL, 0xfffffff0UL);
    gate.accept(packet(1, true, 200), 0x10, 0x10);
    assert(gate.armed && gate.throttle == 200);
    gate.tick(0x10 + kTimeoutMs);
    assert(!gate.armed); // Sequence and millis wrap both work.
  }
  {
    Packet p = packet(1);
    assert(valid(p));
    p.throttle = 1001; assert(!valid(p));
    p.throttle = 0; p.flags = 2; assert(!valid(p));
    p.flags = 0; p.version = 9; assert(!valid(p));
    p.version = kVersion; p.session = 0; assert(!valid(p));
  }
  puts("PASS: arming, inhibition, deadman, expiry, replay, session, wrap, validation");
}
