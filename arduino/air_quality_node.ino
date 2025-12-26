#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BME680.h>

// ============ CONFIGURATION ============
const char* NODE_ID = "bme680_node_01";
const char* LOCATION = "Room";
const unsigned long READING_INTERVAL = 30000;  // 30 seconds
const long SERIAL_BAUD = 115200;

// ============ SENSOR ============
Adafruit_BME680 bme;

// ============ VARIABLES ============
unsigned long lastReading = 0;
int readingCount = 0;
bool sensorOK = false;

// ============ SETUP ============
void setup() {
  Serial.begin(SERIAL_BAUD);
  while (!Serial) delay(10);
  
  delay(1000);
  Serial.println();
  Serial.println("================================");
  Serial.println("  Air Quality Monitor v1.0");
  Serial.println("================================");
  
  // Initialize BME680
  Serial.print("Initializing BME680... ");
  
  if (!bme.begin()) {
    Serial.println("FAILED!");
    Serial.println("Check wiring:");
    Serial.println("  VCC -> 3.3V");
    Serial.println("  GND -> GND");
    Serial.println("  SCL -> D15/SCL (GPIO5)");
    Serial.println("  SDA -> D14/SDA (GPIO4)");
    Serial.println("  SDO -> GND");
    Serial.println("  CS  -> 3.3V");
    sensorOK = false;
  } else {
    Serial.println("OK!");
    
    // Configure sensor
    bme.setTemperatureOversampling(BME680_OS_8X);
    bme.setHumidityOversampling(BME680_OS_2X);
    bme.setPressureOversampling(BME680_OS_4X);
    bme.setIIRFilterSize(BME680_FILTER_SIZE_3);
    bme.setGasHeater(320, 150);  // 320°C for 150ms
    
    sensorOK = true;
    Serial.println("Sensor configured. Starting readings...\n");
  }
  
  // Send initial status
  sendStatus(sensorOK ? "ready" : "error");
}

// ============ MAIN LOOP ============
void loop() {
  // Handle serial commands from Pi
  if (Serial.available() > 0) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    handleCommand(cmd);
  }
  
  // Read sensor at interval
  if (sensorOK && (millis() - lastReading >= READING_INTERVAL)) {
    lastReading = millis();
    readAndSend();
  }
}

// ============ SENSOR READING ============
void readAndSend() {
  // Trigger reading
  if (!bme.performReading()) {
    sendError("read_failed");
    return;
  }
  
  readingCount++;
  
  // Get values
  float temp = bme.temperature;
  float humidity = bme.humidity;
  float pressure = bme.pressure / 100.0;  // hPa
  float gasResistance = bme.gas_resistance;
  
  // Calculate simple AQI (0-500 scale)
  int aqi = calculateAQI(gasResistance, humidity);
  
  // Send JSON
  Serial.print("{");
  Serial.print("\"type\":\"reading\",");
  Serial.print("\"node_id\":\""); Serial.print(NODE_ID); Serial.print("\",");
  Serial.print("\"location\":\""); Serial.print(LOCATION); Serial.print("\",");
  Serial.print("\"temperature\":"); Serial.print(temp, 2); Serial.print(",");
  Serial.print("\"humidity\":"); Serial.print(humidity, 2); Serial.print(",");
  Serial.print("\"pressure\":"); Serial.print(pressure, 2); Serial.print(",");
  Serial.print("\"gas_resistance\":"); Serial.print(gasResistance, 0); Serial.print(",");
  Serial.print("\"aqi\":"); Serial.print(aqi); Serial.print(",");
  Serial.print("\"reading_num\":"); Serial.print(readingCount);
  Serial.println("}");
}

// ============ AQI CALCULATION ============
// Realistic indoor AQI based on gas resistance
// BME680 gas resistance: higher = cleaner air
// Calibrated for typical indoor environments
int calculateAQI(float gasRes, float humidity) {
  // Humidity compensation (BME680 gas sensor is humidity-sensitive)
  float humidityFactor = 0.25 * (humidity - 40.0);
  float compensated = gasRes * (1.0 + humidityFactor / 100.0);
  
  // REALISTIC INDOOR CALIBRATION
  // Typical indoor gas resistance: 30,000 - 150,000 ohms
  // Very clean outdoor air: 200,000+ ohms (rare indoors)
  
  int aqi;
  if (compensated > 150000) {
    // Excellent - very clean air (rare indoors)
    aqi = map(compensated, 150000, 300000, 25, 0);
  } else if (compensated > 100000) {
    // Good - well-ventilated room
    aqi = map(compensated, 100000, 150000, 50, 25);
  } else if (compensated > 70000) {
    // Moderate - normal indoor air
    aqi = map(compensated, 70000, 100000, 75, 50);
  } else if (compensated > 50000) {
    // Moderate - typical occupied room
    aqi = map(compensated, 50000, 70000, 100, 75);
  } else if (compensated > 35000) {
    // Unhealthy for Sensitive - stuffy room, needs ventilation
    aqi = map(compensated, 35000, 50000, 150, 100);
  } else if (compensated > 20000) {
    // Unhealthy - poor ventilation or VOC source nearby
    aqi = map(compensated, 20000, 35000, 200, 150);
  } else {
    // Very Unhealthy - cooking, chemicals, or very poor air
    aqi = map(compensated, 5000, 20000, 350, 200);
  }
  
  return constrain(aqi, 0, 500);
}

// ============ COMMANDS ============
void handleCommand(String cmd) {
  if (cmd == "READ") {
    readAndSend();
  } 
  else if (cmd == "STATUS") {
    sendStatus(sensorOK ? "ok" : "error");
  }
  else if (cmd == "INFO") {
    Serial.print("{\"type\":\"info\",");
    Serial.print("\"node_id\":\""); Serial.print(NODE_ID); Serial.print("\",");
    Serial.print("\"location\":\""); Serial.print(LOCATION); Serial.print("\",");
    Serial.print("\"interval_ms\":"); Serial.print(READING_INTERVAL); Serial.print(",");
    Serial.print("\"total_readings\":"); Serial.print(readingCount);
    Serial.println("}");
  }
  else if (cmd == "PING") {
    Serial.println("{\"type\":\"pong\"}");
  }
}

void sendStatus(const char* status) {
  Serial.print("{\"type\":\"status\",");
  Serial.print("\"node_id\":\""); Serial.print(NODE_ID); Serial.print("\",");
  Serial.print("\"status\":\""); Serial.print(status); Serial.print("\"");
  Serial.println("}");
}

void sendError(const char* error) {
  Serial.print("{\"type\":\"error\",");
  Serial.print("\"node_id\":\""); Serial.print(NODE_ID); Serial.print("\",");
  Serial.print("\"error\":\""); Serial.print(error); Serial.print("\"");
  Serial.println("}");
}
