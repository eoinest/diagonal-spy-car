#include "../receiver_s2/web_control_protocol.h"
#include <assert.h>
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <initializer_list>
bool parse(const char *s) { spycar::WebInput i; return spycar::parseWebInput(s, strlen(s), i); }
int main() {
  assert(parse("1,0,0,0"));
  assert(parse("4294967295,1,-1000,1000"));
  for (const char *s : {"", "0,1,0,0", "1,2,0,0", "1,0,1,0", "1,1,1001,0",
      "4294967296,1,0,0", "1,1,-99999999999,0", "1,1,0,0garbage", "1,1,0", "1,1,0,0,0"}) assert(!parse(s));
  spycar::WebInput input;
  assert(!spycar::parseWebInput("1,1,0,0\0oops", 12, input));
  spycar::WebChallenge challenge;
  challenge.issue(42, 100);
  assert(challenge.consume(42, 299));
  assert(!challenge.consume(42, 299));
  challenge.issue(43, 100);
  assert(!challenge.consume(43, 300));
  challenge.issue(44, 0xfffffff0U);
  assert(challenge.consume(44, 40));
  challenge.issue(45, 100);
  assert(!challenge.consume(46, 101));
  assert(!challenge.consume(45, 102));
  auto forward = spycar::mixJoystick(0,1000);
  assert(forward.left == 1000 && forward.right == 1000);
  auto reverse = spycar::mixJoystick(0,-1000);
  assert(reverse.left == -1000 && reverse.right == -1000);
  auto right = spycar::mixJoystick(1000,0);
  assert(right.left == 1000 && right.right == -1000);
  auto left = spycar::mixJoystick(-1000,0);
  assert(left.left == -1000 && left.right == 1000);
  auto diagonal = spycar::mixJoystick(707,707);
  assert(diagonal.left >= 999 && diagonal.right == 0);
  auto half = spycar::mixJoystick(0,530);
  assert(half.left == 500 && half.right == 500);
  assert(spycar::mixJoystick(30,30).left == 0);
  for (int x=-1000; x<=1000; x+=50) for (int y=-1000; y<=1000; y+=50) {
    auto result=spycar::mixJoystick(x,y);
    assert(abs(result.left)<=1000 && abs(result.right)<=1000);
    auto mirrored=spycar::mixJoystick(-x,y);
    assert(result.left==mirrored.right && result.right==mirrored.left);
  }
  puts("Web control: parsing, stale/reused tokens, wrap, directional/radial mixing passed");
}
