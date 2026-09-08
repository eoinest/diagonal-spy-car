#pragma once
#include <stdint.h>

namespace spycar {
// Once entered, maintenance is latched for this boot, including failures.
class MaintenanceGate {
 public:
  bool active = false;
  bool inhibit = false;
  bool update(bool pressed, uint32_t now) {
    if (active) return false;
    inhibit = pressed;
    if (!pressed) {
      released_ = true;
      timing_ = false;
      return false;
    }
    if (!released_) return false;
    if (!timing_) { since_ = now; timing_ = true; }
    if (now - since_ < 3000) return false;
    active = inhibit = true;
    return true;
  }
 private:
  bool released_ = false;
  bool timing_ = false;
  uint32_t since_ = 0;
};
} // namespace spycar
