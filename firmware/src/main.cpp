// Air Quality Monitor node: WeMos D1 (ESP8266) + BME680
//
// Reads the BME680 every 30 s, works out an indoor air-quality index on the
// device, and sends each reading as JSON:
//   - over Wi-Fi to an MQTT broker (topic aq/<node>/reading)
//   - and over USB serial, so the board still works without Wi-Fi
//
// If Wi-Fi or the broker drops, readings are kept in a small buffer and sent
// when the link comes back, with their age so the backend can timestamp them.
//
// MQTT topics (<node> is NODE_ID):
//   aq/<node>/reading  readings (JSON)
//   aq/<node>/status   "online" / "offline" (retained; "offline" is the last will)
//   aq/<node>/cmd      commands in: READ, STATUS, INFO, PING
//   aq/<node>/reply    replies to commands
// The same commands also work over serial.

#include <Arduino.h>
#include <Wire.h>
#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BME680.h>

#if __has_include("secrets.h")
#include "secrets.h"
#else
#error "Copy include/secrets.example.h to include/secrets.h and add your Wi-Fi and broker details"
#endif

// ============ CONFIGURATION ============
const char* NODE_ID = "bme680_node_01";
const char* LOCATION = "Room";
const unsigned long READING_INTERVAL = 30000;  // 30 s between readings
const long SERIAL_BAUD = 115200;

const unsigned long RECONNECT_MIN_MS = 1000;   // first retry after 1 s
const unsigned long RECONNECT_MAX_MS = 30000;  // back off up to 30 s
const int BUFFER_SIZE = 20;                    // readings kept while offline (10 min)

// ============ READING STORE ============
struct Reading {
  float temperature;
  float humidity;
  float pressure;
  float gasResistance;
  int aqi;
  uint32_t number;
  uint32_t takenAtMs;   // millis() when it was measured
};

Reading offlineBuffer[BUFFER_SIZE];
int bufferStart = 0;    // oldest reading
int bufferCount = 0;
uint32_t droppedReadings = 0;

// ============ GLOBALS ============
Adafruit_BME680 bme;
WiFiClient wifiClient;
PubSubClient mqtt(wifiClient);

char topicReading[48], topicStatus[48], topicCmd[48], topicReply[48];

unsigned long lastReading = 0;
unsigned long lastConnectAttempt = 0;
unsigned long reconnectDelay = RECONNECT_MIN_MS;
uint32_t readingCount = 0;
bool sensorOK = false;

// ============ PROTOTYPES ============
void takeReading();
void sendReading(const Reading& r);
int formatReading(const Reading& r, char* out, size_t len);
void bufferReading(const Reading& r);
void flushBuffer();
void maintainMqtt();
void onMqttMessage(char* topic, byte* payload, unsigned int length);
void handleCommand(String cmd);
void reply(const char* json);
int calculateAQI(float gasRes, float humidity);

// ============ SETUP ============
void setup() {
  Serial.begin(SERIAL_BAUD);
  delay(1000);
  Serial.println();
  Serial.println("================================");
  Serial.println("  Air Quality Monitor v2.0 (Wi-Fi/MQTT)");
  Serial.println("================================");

  // BME680: SDO to GND gives 0x76, SDO to 3.3V gives 0x77
  Serial.print("Initializing BME680... ");
  sensorOK = bme.begin(0x76) || bme.begin(0x77);
  if (!sensorOK) {
    Serial.println("FAILED! Check wiring: SDA->GPIO4, SCL->GPIO5, VCC->3.3V, GND->GND");
  } else {
    Serial.println("OK!");
    bme.setTemperatureOversampling(BME680_OS_8X);
    bme.setHumidityOversampling(BME680_OS_2X);
    bme.setPressureOversampling(BME680_OS_4X);
    bme.setIIRFilterSize(BME680_FILTER_SIZE_3);
    bme.setGasHeater(320, 150);  // 320 C for 150 ms
  }

  snprintf(topicReading, sizeof(topicReading), "aq/%s/reading", NODE_ID);
  snprintf(topicStatus, sizeof(topicStatus), "aq/%s/status", NODE_ID);
  snprintf(topicCmd, sizeof(topicCmd), "aq/%s/cmd", NODE_ID);
  snprintf(topicReply, sizeof(topicReply), "aq/%s/reply", NODE_ID);

  // Wi-Fi: station mode, the SDK reconnects on its own after a drop
  WiFi.mode(WIFI_STA);
  WiFi.persistent(false);
  WiFi.setAutoReconnect(true);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  Serial.print("Wi-Fi: connecting to ");
  Serial.println(WIFI_SSID);

  mqtt.setServer(MQTT_HOST, MQTT_PORT);
  mqtt.setCallback(onMqttMessage);
  mqtt.setBufferSize(512);     // default 256 is close to one reading's size
  mqtt.setSocketTimeout(2);    // a dead broker must not stall the sensor loop
  mqtt.setKeepAlive(60);

  reply(sensorOK ? "{\"type\":\"status\",\"status\":\"ready\"}"
                 : "{\"type\":\"status\",\"status\":\"error\"}");
}

// ============ MAIN LOOP ============
void loop() {
  maintainMqtt();
  mqtt.loop();

  if (Serial.available() > 0) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    handleCommand(cmd);
  }

  if (sensorOK && (millis() - lastReading >= READING_INTERVAL)) {
    lastReading = millis();
    takeReading();
  }
}

// ============ CONNECTION HANDLING ============
// Called every loop. Never blocks for long: it only tries to connect when the
// back-off timer allows, and doubles the wait after each failed attempt.
void maintainMqtt() {
  if (mqtt.connected()) return;
  if (WiFi.status() != WL_CONNECTED) return;  // SDK is still reconnecting Wi-Fi
  if (millis() - lastConnectAttempt < reconnectDelay) return;

  lastConnectAttempt = millis();
  Serial.print("MQTT: connecting to ");
  Serial.print(MQTT_HOST);
  Serial.print("... ");

  // Last will: if the node vanishes, the broker publishes "offline" for it
  bool ok = mqtt.connect(NODE_ID, nullptr, nullptr,
                         topicStatus, 1, true, "{\"status\":\"offline\"}");
  if (ok) {
    Serial.println("connected");
    reconnectDelay = RECONNECT_MIN_MS;
    mqtt.publish(topicStatus, "{\"status\":\"online\"}", true);
    mqtt.subscribe(topicCmd);
    flushBuffer();
  } else {
    Serial.print("failed (state ");
    Serial.print(mqtt.state());
    Serial.print("), retry in ");
    reconnectDelay = min(reconnectDelay * 2, RECONNECT_MAX_MS);
    Serial.print(reconnectDelay / 1000);
    Serial.println(" s");
  }
}

// ============ SENSOR READING ============
void takeReading() {
  if (!bme.performReading()) {
    reply("{\"type\":\"error\",\"error\":\"read_failed\"}");
    return;
  }

  Reading r;
  r.temperature = bme.temperature;
  r.humidity = bme.humidity;
  r.pressure = bme.pressure / 100.0;  // hPa
  r.gasResistance = bme.gas_resistance;
  r.aqi = calculateAQI(r.gasResistance, r.humidity);
  r.number = ++readingCount;
  r.takenAtMs = millis();

  sendReading(r);
}

// Always prints to serial; publishes over MQTT if connected, otherwise buffers.
void sendReading(const Reading& r) {
  char json[320];
  formatReading(r, json, sizeof(json));
  Serial.println(json);

  if (mqtt.connected() && bufferCount == 0) {
    if (!mqtt.publish(topicReading, json)) bufferReading(r);
  } else {
    bufferReading(r);
    if (mqtt.connected()) flushBuffer();  // keep the order: oldest first
  }
}

int formatReading(const Reading& r, char* out, size_t len) {
  return snprintf(out, len,
    "{\"type\":\"reading\",\"node_id\":\"%s\",\"location\":\"%s\","
    "\"temperature\":%.2f,\"humidity\":%.2f,\"pressure\":%.2f,"
    "\"gas_resistance\":%.0f,\"aqi\":%d,\"reading_num\":%lu,\"age_ms\":%lu}",
    NODE_ID, LOCATION, r.temperature, r.humidity, r.pressure,
    r.gasResistance, r.aqi, (unsigned long)r.number,
    (unsigned long)(millis() - r.takenAtMs));
}

// Ring buffer: when full, the oldest reading is dropped.
void bufferReading(const Reading& r) {
  if (bufferCount == BUFFER_SIZE) {
    bufferStart = (bufferStart + 1) % BUFFER_SIZE;
    bufferCount--;
    droppedReadings++;
  }
  offlineBuffer[(bufferStart + bufferCount) % BUFFER_SIZE] = r;
  bufferCount++;
}

void flushBuffer() {
  char json[320];
  while (bufferCount > 0 && mqtt.connected()) {
    formatReading(offlineBuffer[bufferStart], json, sizeof(json));
    if (!mqtt.publish(topicReading, json)) break;  // try again next time
    bufferStart = (bufferStart + 1) % BUFFER_SIZE;
    bufferCount--;
  }
}

// ============ AQI CALCULATION ============
// Indoor air-quality index (0-500) from BME680 gas resistance.
// Higher resistance means cleaner air. Calibrated for typical indoor rooms.
int calculateAQI(float gasRes, float humidity) {
  // Humidity compensation (the gas sensor is humidity-sensitive)
  float humidityFactor = 0.25 * (humidity - 40.0);
  float compensated = gasRes * (1.0 + humidityFactor / 100.0);

  int aqi;
  if (compensated > 150000)      aqi = map(compensated, 150000, 300000, 25, 0);
  else if (compensated > 100000) aqi = map(compensated, 100000, 150000, 50, 25);
  else if (compensated > 70000)  aqi = map(compensated, 70000, 100000, 75, 50);
  else if (compensated > 50000)  aqi = map(compensated, 50000, 70000, 100, 75);
  else if (compensated > 35000)  aqi = map(compensated, 35000, 50000, 150, 100);
  else if (compensated > 20000)  aqi = map(compensated, 20000, 35000, 200, 150);
  else                           aqi = map(compensated, 5000, 20000, 350, 200);

  return constrain(aqi, 0, 500);
}

// ============ COMMANDS ============
void onMqttMessage(char* topic, byte* payload, unsigned int length) {
  String cmd;
  for (unsigned int i = 0; i < length; i++) cmd += (char)payload[i];
  cmd.trim();
  handleCommand(cmd);
}

void handleCommand(String cmd) {
  char json[200];
  if (cmd == "READ") {
    takeReading();
  } else if (cmd == "STATUS") {
    snprintf(json, sizeof(json),
      "{\"type\":\"status\",\"node_id\":\"%s\",\"sensor\":\"%s\",\"wifi_rssi\":%d,"
      "\"buffered\":%d,\"dropped\":%lu}",
      NODE_ID, sensorOK ? "ok" : "error", WiFi.RSSI(), bufferCount,
      (unsigned long)droppedReadings);
    reply(json);
  } else if (cmd == "INFO") {
    snprintf(json, sizeof(json),
      "{\"type\":\"info\",\"node_id\":\"%s\",\"location\":\"%s\",\"interval_ms\":%lu,"
      "\"total_readings\":%lu,\"ip\":\"%s\"}",
      NODE_ID, LOCATION, READING_INTERVAL, (unsigned long)readingCount,
      WiFi.localIP().toString().c_str());
    reply(json);
  } else if (cmd == "PING") {
    reply("{\"type\":\"pong\"}");
  }
}

// Replies go to serial and, when connected, to aq/<node>/reply.
void reply(const char* json) {
  Serial.println(json);
  if (mqtt.connected()) mqtt.publish(topicReply, json);
}
