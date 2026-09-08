#include "../receiver_s2/maintenance_gate.h"
#include <assert.h>
#include <stdio.h>

int main() {
  spycar::MaintenanceGate gate;
  // A button held at startup must first be released.
  assert(!gate.update(true, 0) && gate.inhibit);
  assert(!gate.update(true, 4000) && !gate.active);
  assert(!gate.update(false, 4001) && !gate.inhibit);
  assert(!gate.update(true, 5000) && gate.inhibit);
  assert(!gate.update(true, 7999));
  assert(gate.update(true, 8000) && gate.active);
  assert(!gate.update(false, 9000) && gate.active && gate.inhibit);
  // Short presses/bounce reset the timer; never activate on release.
  spycar::MaintenanceGate shortPress;
  shortPress.update(false, 0);
  assert(!shortPress.update(true, 100));
  assert(!shortPress.update(false, 3099));
  assert(!shortPress.update(true, 3100));
  assert(!shortPress.update(true, 6099));
  assert(shortPress.update(true, 6100));
  // uint32_t millis wrap must not skip or delay the hold.
  spycar::MaintenanceGate wrap;
  wrap.update(false, 0xfffffff0U);
  wrap.update(true, 0xfffffff1U);
  assert(!wrap.update(true, 2984));
  assert(wrap.update(true, 2985));
  puts("Maintenance gate tests passed");
}
