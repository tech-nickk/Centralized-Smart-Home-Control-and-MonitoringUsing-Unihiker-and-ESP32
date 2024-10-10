#include <WiFi.h>
#include <ArduinoJson.h>
#include <DHT.h>

const char* ssid = "*******";
const char* password = "********";

#define DHTPIN D1     // Digital pin connected to the DHT sensor
#define DHTTYPE DHT11   // DHT 11

DHT dht(DHTPIN, DHTTYPE);

// Define pins for appliances
const int LIGHT_PIN = D6;
const int TV_PIN = D5;
const int FAN_PIN = D4;
const int AC_PIN = D3;

WiFiServer server(8080);

void setup() {
  Serial.begin(115200);
  
  // Connect to Wi-Fi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Connecting to WiFi...");
  }
  Serial.println("Connected to WiFi");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());

  // Initialize DHT sensor
  dht.begin();

  // Set up appliance control pins
  pinMode(LIGHT_PIN, OUTPUT);
  pinMode(TV_PIN, OUTPUT);
  pinMode(FAN_PIN, OUTPUT);
  pinMode(AC_PIN, OUTPUT);

  // Start the server
  server.begin();
}

void loop() {
  WiFiClient client = server.available();
  if (client) {
    Serial.println("New client connected");
    String request = client.readStringUntil('\r');
    client.flush();

    StaticJsonDocument<200> doc;
    DeserializationError error = deserializeJson(doc, request);

    if (error) {
      Serial.print(F("deserializeJson() failed: "));
      Serial.println(error.f_str());
      client.stop();
      return;
    }

    String command = doc["command"];

    if (command == "get") {
      // float temperature = dht.readTemperature();
      // float humidity = dht.readHumidity();
      float temperature = 25;
      float humidity = 72;

      StaticJsonDocument<200> response;
      // response["temperature"] = isnan(temperature) ? nullptr : temperature;
      // response["humidity"] = isnan(humidity) ? nullptr : humidity;

      response["temperature"] = temperature;
      response["humidity"] = humidity;


      response["appliances"]["Light"] = digitalRead(LIGHT_PIN);
      response["appliances"]["TV"] = digitalRead(TV_PIN);
      response["appliances"]["Fan"] = digitalRead(FAN_PIN);
      response["appliances"]["AC"] = digitalRead(AC_PIN);

      String jsonResponse;
      serializeJson(response, jsonResponse);
      client.println(jsonResponse);
    }
    else if (command == "set") {
      String appliance = doc["appliance"];
      bool status = doc["status"];

      int pin = -1;
      if (appliance == "Light") pin = LIGHT_PIN;
      else if (appliance == "TV") pin = TV_PIN;
      else if (appliance == "Fan") pin = FAN_PIN;
      else if (appliance == "AC") pin = AC_PIN;

      if (pin != -1) {
        digitalWrite(pin, status ? HIGH : LOW);
        client.println("{\"status\":\"success\"}");
      }
      else {
        client.println("{\"status\":\"error\",\"message\":\"Invalid appliance\"}");
      }
    }
    else {
      client.println("{\"status\":\"error\",\"message\":\"Invalid command\"}");
    }

    client.stop();
    Serial.println("Client disconnected");
  }
}
