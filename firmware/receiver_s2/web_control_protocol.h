#pragma once
#include <stdint.h>
#include <stddef.h>
#include <math.h>

namespace spycar {
constexpr uint32_t kWebChallengeMs = 200;
struct WebInput { uint32_t token; bool held; int x, y; };

// Four bounded decimal fields. Do not allow sscanf integer overflow, embedded
// NULs, trailing input or out-of-range commands to become movement.
inline bool parseWebInput(const char *data, size_t length, WebInput &out) {
  if (!length || length > 48) return false;
  int64_t values[4] = {};
  size_t pos = 0;
  for (int field = 0; field < 4; ++field) {
    bool negative = false;
    if (pos < length && data[pos] == '-' && field >= 2) { negative = true; ++pos; }
    const size_t start = pos;
    uint64_t value = 0;
    while (pos < length && data[pos] >= '0' && data[pos] <= '9') {
      value = value * 10 + data[pos++] - '0';
      if (value > UINT32_MAX || pos - start > 10) return false;
    }
    if (pos == start) return false;
    values[field] = negative ? -int64_t(value) : int64_t(value);
    if (field < 3 && (pos >= length || data[pos++] != ',')) return false;
  }
  if (pos != length || values[0] == 0 || values[1] > 1 ||
      values[2] < -1000 || values[2] > 1000 || values[3] < -1000 || values[3] > 1000 ||
      (!values[1] && (values[2] || values[3]))) return false;
  out = {uint32_t(values[0]), bool(values[1]), int(values[2]), int(values[3])};
  return true;
}

class WebChallenge {
 public:
  void issue(uint32_t token, uint32_t now) { token_ = token; issuedAt = now; }
  bool consume(uint32_t token, uint32_t now) {
    const bool valid = token_ && token == token_ && now - issuedAt < kWebChallengeMs;
    token_ = 0; // Single use, including rejected attempts.
    return valid;
  }
  uint32_t issuedAt = 0;
 private:
  uint32_t token_ = 0;
};

struct WheelMix { int left, right; };
inline WheelMix mixJoystick(int x, int y) {
  // x right, y forward. The fastest wheel follows radial displacement;
  // normalize the directional mix before applying radius and a 6% dead zone.
  const float radius = sqrtf(float(x) * x + float(y) * y);
  if (radius <= 60) return {0, 0};
  const float speed = (fminf(radius, 1000) - 60) / 940;
  const float left = y + x, right = y - x;
  const float maximum = fmaxf(fabsf(left), fabsf(right));
  return {int(lroundf(left / maximum * speed * 1000)),
          int(lroundf(right / maximum * speed * 1000))};
}
} // namespace spycar
