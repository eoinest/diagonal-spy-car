#pragma once
#include <ESPmDNS.h>
#include <esp_http_server.h>
#include <esp_random.h>
#include <unistd.h>
#include <atomic>
#include "web_control_protocol.h"
#include "web_assets.h"
#if __has_include("web.private.h")
#include "web.private.h"
#else
#include "web_config.h"
#endif

bool queueWebCommand(const spycar::Packet &packet, uint32_t issuedAt);
void requestWebStop();

enum class WebDriveState { Ready, ServoSetup, BatterySetup, BatteryLow, OutputFault, Maintenance };

class WebControl {
 public:
  void begin() {
    station_ = strlen(WEB_WIFI_SSID) != 0;
    if (station_) {
      WiFi.mode(WIFI_STA);
      WiFi.setHostname(WEB_HOSTNAME);
      WiFi.setAutoReconnect(true);
      WiFi.begin(WEB_WIFI_SSID, WEB_WIFI_PASSWORD);
      Serial.println("Joining configured Wi-Fi for browser control.");
    } else {
      const size_t length = strlen(OTA_PASSWORD);
      if (length < 12 || length > 63) {
        Serial.println("Browser AP disabled: set OTA_PASSWORD in ota.private.h.");
        return;
      }
      WiFi.mode(WIFI_AP);
      WiFi.softAPConfig(IPAddress(192,168,4,1), IPAddress(192,168,4,1), IPAddress(255,255,255,0));
      if (!WiFi.softAP(WEB_SSID, OTA_PASSWORD, 1, false, 2)) return;
    }
    configured_ = true;
    WiFi.setSleep(false);
  }

  void tick() {
    if (!configured_) return;
    const bool connected = !station_ || WiFi.status() == WL_CONNECTED;
    if (!connected) {
      if (wasConnected_) requestWebStop();
      wasConnected_ = false;
      return;
    }
    wasConnected_ = true;
    if (!server_ && !failed_) startServer();
  }

  bool ready() const { return server_ && wasConnected_; }
  uint32_t session() const { return activeSession_.load(); }
  void status(WebDriveState state, bool armed, float volts) {
    state_ = state;
    armed_ = armed;
    millivolts_ = isfinite(volts) && volts > 0 ? int(volts * 1000) : 0;
  }
  bool stop() {
    configured_ = false;
    requestWebStop();
    MDNS.end();
    if (server_ && httpd_stop(server_) != ESP_OK) return false;
    server_ = nullptr;
    return true;
  }

 private:
  httpd_handle_t server_ = nullptr;
  bool station_ = false, configured_ = false, wasConnected_ = false, failed_ = false;
  int owner_ = -1; // Used only by httpd task; session protects against fd reuse.
  std::atomic<uint32_t> activeSession_{0};
  std::atomic<WebDriveState> state_{WebDriveState::ServoSetup};
  std::atomic<bool> armed_{false};
  std::atomic<int> millivolts_{0};
  spycar::WebChallenge challenge_;
  uint32_t sequence_ = 0;
  uint32_t ownerLastCommand_ = 0;
  char pageToken_[33] = {};

  uint32_t randomNonzero() {
    uint32_t value;
    do { value = esp_random(); } while (!value);
    return value;
  }
  void revoke() {
    activeSession_ = randomNonzero();
    sequence_ = 0;
    challenge_.issue(0, millis());
    requestWebStop(); // Main loop services this before any movement backlog.
  }
  static WebControl &self(httpd_req_t *r) { return *static_cast<WebControl *>(r->user_ctx); }
  static void closeClient(httpd_handle_t h, int fd) {
    auto *car = static_cast<WebControl *>(httpd_get_global_user_ctx(h));
    if (car->owner_ == fd) { car->revoke(); car->owner_ = -1; }
    close(fd);
  }
  static void keepContext(void *) {} // Instance is static; httpd must not free it.

  bool allowedOrigin(httpd_req_t *r) {
    char origin[100], query[80];
    if (httpd_req_get_hdr_value_str(r, "Origin", origin, sizeof(origin)) != ESP_OK ||
        httpd_req_get_url_query_str(r, query, sizeof(query)) != ESP_OK) return false;
    const String expectedQuery = String("token=") + pageToken_;
    if (expectedQuery != query) return false;
    const String mdns = String("http://") + WEB_HOSTNAME + ".local";
    const String ip = String("http://") + (station_ ? WiFi.localIP() : WiFi.softAPIP()).toString();
    return mdns == origin || mdns + ":80" == origin || ip == origin || ip + ":80" == origin;
  }

  esp_err_t reply(httpd_req_t *r, bool reset) {
    const uint32_t token = randomNonzero();
    challenge_.issue(token, millis());
    static const char *reasons[] = {"Ready", "Calibrate servo neutral", "Calibrate battery sensing",
                                   "Battery low or invalid", "Output fault", "Update mode"};
    const WebDriveState state = state_.load();
    char voltage[20] = "null";
    const int mv = millivolts_.load();
    if (mv) snprintf(voltage, sizeof(voltage), "%.3f", mv / 1000.0);
    char payload[240];
    snprintf(payload, sizeof(payload),
             "{\"token\":%lu,\"ready\":%s,\"armed\":%s,\"battery\":%s,\"reason\":\"%s\",\"reset\":%s}",
             (unsigned long)token, state == WebDriveState::Ready ? "true" : "false",
             armed_.load() && !reset ? "true" : "false", voltage, reasons[int(state)], reset ? "true" : "false");
    httpd_ws_frame_t frame = {};
    frame.type = HTTPD_WS_TYPE_TEXT;
    frame.payload = reinterpret_cast<uint8_t *>(payload);
    frame.len = strlen(payload);
    return httpd_ws_send_frame(r, &frame);
  }

  static esp_err_t socketHandler(httpd_req_t *r) {
    auto &car = self(r);
    const int fd = httpd_req_to_sockfd(r);
    if (r->method == HTTP_GET) {
      if (httpd_ws_get_fd_info(r->handle, fd) != HTTPD_WS_CLIENT_WEBSOCKET) return ESP_FAIL;
      if (!car.allowedOrigin(r)) {
        // IDF has already sent 101 before this handler. Close the socket;
        // do not send an HTTP error into an upgraded WebSocket connection.
        return ESP_FAIL;
      }
      if (car.owner_ != -1) {
        if (millis() - car.ownerLastCommand_ < 2000) {
          return ESP_FAIL;
        }
        // A vanished phone can leave a half-open TCP socket. Allow takeover
        // only after well beyond the drive timeout, and invalidate its session.
        httpd_sess_trigger_close(car.server_, car.owner_);
      }
      car.owner_ = fd;
      car.ownerLastCommand_ = millis();
      car.revoke();
      return ESP_OK; // Client sends 'hello' once the upgrade is complete.
    }
    if (fd != car.owner_) return ESP_FAIL;
    httpd_ws_frame_t frame = {};
    if (httpd_ws_recv_frame(r, &frame, 0) != ESP_OK) return ESP_FAIL;
    if (frame.type != HTTPD_WS_TYPE_TEXT || !frame.final || frame.len == 0 || frame.len > 48) {
      car.revoke();
      return ESP_FAIL;
    }
    char data[49] = {};
    frame.payload = reinterpret_cast<uint8_t *>(data);
    if (httpd_ws_recv_frame(r, &frame, 48) != ESP_OK) return ESP_FAIL;
    if ((frame.len == 5 && memcmp(data,"hello",5) == 0) ||
        (frame.len == 4 && memcmp(data,"stop",4) == 0)) {
      car.revoke();
      return car.reply(r, true);
    }
    spycar::WebInput input;
    const uint32_t issuedAt = car.challenge_.issuedAt;
    if (!spycar::parseWebInput(data, frame.len, input) || !car.challenge_.consume(input.token, millis())) {
      car.revoke();
      return car.reply(r, true);
    }
    spycar::Packet packet = {};
    packet.magic = spycar::kMagic;
    packet.version = spycar::kVersion;
    packet.session = car.activeSession_.load();
    packet.sequence = ++car.sequence_;
    packet.flags = input.held ? spycar::kDeadman : 0;
    packet.throttle = input.y;
    packet.steering = -input.x; // Preserve legacy packet's left-positive mix.
    if (!queueWebCommand(packet, issuedAt)) {
      car.revoke();
      return car.reply(r, true);
    }
    car.ownerLastCommand_ = millis();
    return car.reply(r, false);
  }

  static esp_err_t indexHandler(httpd_req_t *r) {
    String page = FPSTR(CONTROL_INDEX);
    page.replace("%CONTROL_TOKEN%", self(r).pageToken_);
    httpd_resp_set_type(r, "text/html");
    httpd_resp_set_hdr(r, "Cache-Control", "no-store");
    httpd_resp_set_hdr(r, "X-Frame-Options", "DENY");
    // Explicit WebSocket origins also support browsers that do not map
    // connect-src 'self' from HTTP to WS. Do not derive this from Host.
    const auto &car = self(r);
    const String policy = String("default-src 'self'; frame-ancestors 'none'; base-uri 'none'; connect-src 'self' ws://") +
      WEB_HOSTNAME + ".local ws://" + (car.station_ ? WiFi.localIP() : WiFi.softAPIP()).toString();
    httpd_resp_set_hdr(r, "Content-Security-Policy", policy.c_str());
    return httpd_resp_send(r, page.c_str(), page.length());
  }
  static esp_err_t scriptHandler(httpd_req_t *r) {
    httpd_resp_set_type(r, "text/javascript");
    httpd_resp_set_hdr(r, "Cache-Control", "no-store");
    return httpd_resp_sendstr(r, CONTROL_JS);
  }
  static esp_err_t styleHandler(httpd_req_t *r) {
    httpd_resp_set_type(r, "text/css");
    return httpd_resp_sendstr(r, CONTROL_CSS);
  }

  void startServer() {
    snprintf(pageToken_, sizeof(pageToken_), "%08lx%08lx%08lx%08lx", (unsigned long)esp_random(),
             (unsigned long)esp_random(), (unsigned long)esp_random(), (unsigned long)esp_random());
    httpd_config_t config = HTTPD_DEFAULT_CONFIG();
    config.task_priority = 2; // Motor/timeout loop runs at priority 3.
    config.stack_size = 6144;
    config.max_open_sockets = 4;
    config.recv_wait_timeout = config.send_wait_timeout = 1;
    config.global_user_ctx = this;
    config.global_user_ctx_free_fn = keepContext;
    config.close_fn = closeClient;
    if (httpd_start(&server_, &config) != ESP_OK) { failed_ = true; return; }
    const char *paths[] = {"/", "/control.js", "/style.css", "/ws"};
    esp_err_t (*handlers[])(httpd_req_t *) = {indexHandler, scriptHandler, styleHandler, socketHandler};
    for (int i=0; i<4; ++i) {
      httpd_uri_t uri = {};
      uri.uri = paths[i]; uri.method = HTTP_GET; uri.handler = handlers[i]; uri.user_ctx = this;
      uri.is_websocket = i == 3;
      if (httpd_register_uri_handler(server_, &uri) != ESP_OK) { stop(); failed_ = true; return; }
    }
    if (MDNS.begin(WEB_HOSTNAME)) MDNS.addService("http", "tcp", 80);
    Serial.printf("Browser control: http://%s.local/ or http://%s/\n", WEB_HOSTNAME,
                  (station_ ? WiFi.localIP() : WiFi.softAPIP()).toString().c_str());
  }
};
