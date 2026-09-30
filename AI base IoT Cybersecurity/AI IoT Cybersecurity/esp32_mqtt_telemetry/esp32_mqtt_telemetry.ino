#include <WiFi.h>
#include <PubSubClient.h>

// ===================== USER SETTINGS =====================
const char* WIFI_SSID = "YOUR_WIFI_NAME";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";

// IMPORTANT:
// Use the LAN IP address of the PC running Mosquitto.
// Do NOT use 127.0.0.1 here.
const char* MQTT_SERVER = "192.168.1.100";
const int MQTT_PORT = 1883;

// =========================================================

WiFiClient espClient;
PubSubClient mqtt(espClient);

String deviceId;

void connectWiFi() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  Serial.print("WiFi connecting");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println();
  Serial.print("WiFi IP: ");
  Serial.println(WiFi.localIP());
}

void connectMQTT() {
  while (!mqtt.connected()) {
    Serial.print("MQTT connecting...");

    if (mqtt.connect(deviceId.c_str())) {
      Serial.println("connected");
    } else {
      Serial.print("failed, rc=");
      Serial.println(mqtt.state());
      delay(2000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  delay(500);

  uint64_t chipid = ESP.getEfuseMac();
  deviceId = "ESP32_" + String((uint32_t)(chipid >> 32), HEX) +
             String((uint32_t)chipid, HEX);

  deviceId.toUpperCase();

  connectWiFi();

  mqtt.setServer(MQTT_SERVER, MQTT_PORT);
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    connectWiFi();
  }

  if (!mqtt.connected()) {
    connectMQTT();
  }

  mqtt.loop();

  static unsigned long lastSend = 0;

  if (millis() - lastSend >= 2000) {
    lastSend = millis();

    float temperature = 28.0 + ((millis() / 1000) % 5);

    String topic = "iot/" + deviceId + "/telemetry";

    String payload = "{";
    payload += "\"device\":\"" + deviceId + "\",";
    payload += "\"temperature\":" + String(temperature, 2) + ",";
    payload += "\"status\":\"normal\",";
    payload += "\"uptime_ms\":" + String(millis());
    payload += "}";

    mqtt.publish(topic.c_str(), payload.c_str());

    Serial.print("Published: ");
    Serial.println(payload);
  }
}
