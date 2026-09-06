#pragma once
#include <stdint.h>

namespace spycar {
constexpr uint32_t kMagic = 0x53505943;
constexpr uint8_t kVersion = 1;
constexpr uint8_t kDeadman = 1;
constexpr uint32_t kTimeoutMs = 250;
constexpr int kNeutralWindow = 40;

struct __attribute__((packed)) Packet {
  uint32_t magic;
  uint8_t version;
  uint8_t flags;
  uint16_t reserved;
  uint32_t session;
  uint32_t sequence;
  int16_t throttle;  // -1000..1000
  int16_t steering;  // -1000..1000; positive turns left
};
static_assert(sizeof(Packet) == 20, "Unexpected wire format");

inline bool valid(const Packet &p) {
  return p.magic == kMagic && p.version == kVersion && p.reserved == 0 &&
         !(p.flags & ~kDeadman) && p.session != 0 &&
         p.throttle >= -1000 && p.throttle <= 1000 &&
         p.steering >= -1000 && p.steering <= 1000;
}
inline bool centered(const Packet &p) {
  return p.throttle >= -kNeutralWindow && p.throttle <= kNeutralWindow &&
         p.steering >= -kNeutralWindow && p.steering <= kNeutralWindow;
}
inline bool newer(uint32_t incoming, uint32_t previous) {
  const uint32_t difference = incoming - previous;
  return difference != 0 && difference < 0x80000000UL;
}

class DriveGate {
 public:
  bool armed = false;
  int16_t throttle = 0;
  int16_t steering = 0;

  void stop() {
    armed = false;
    ready_ = false;
    throttle = steering = 0;
  }
  void inhibit(bool value) {
    inhibited_ = value;
    if (value) stop();
  }
  void tick(uint32_t now) {
    if (!known_ || now - received_ >= kTimeoutMs) stop();
  }
  bool accept(const Packet &p, uint32_t receivedAt, uint32_t now) {
    tick(now);
    if (!valid(p) || now - receivedAt >= kTimeoutMs) return false;
    const bool released = !(p.flags & kDeadman);
    if (!known_ || p.session != session_) {
      stop();
      // A new boot/session cannot begin with held throttle or deadman.
      if (!released || !centered(p)) return false;
      session_ = p.session;
      known_ = true;
    } else if (!newer(p.sequence, sequence_)) {
      return false;
    }
    sequence_ = p.sequence;
    received_ = receivedAt;
    if (inhibited_) {
      stop();
      return true;
    }
    if (released) {
      stop();
      ready_ = centered(p);
    } else if (!armed) {
      armed = ready_ && centered(p);
      ready_ = false;
    }
    throttle = armed ? p.throttle : 0;
    steering = armed ? p.steering : 0;
    return true;
  }

 private:
  bool known_ = false;
  bool ready_ = false;
  bool inhibited_ = true;
  uint32_t session_ = 0;
  uint32_t sequence_ = 0;
  uint32_t received_ = 0;
};
}  // namespace spycar
