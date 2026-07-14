#include <SPI.h>
#include <MFRC522.h>
#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <ArduinoJson.h>

#define SS_PIN D2
#define RST_PIN D1

MFRC522 mfrc522(SS_PIN, RST_PIN);
const char* ssid = "...";       // Change this to your WiFi SSID
const char* password = "17071974"; // Change this to your WiFi Password
const char* serverURL = "http://localhost:5000/api/rfid"; // Change to your backend API URL

WiFiClient client;

void setup() {
    Serial.begin(115200);
    SPI.begin();
    mfrc522.PCD_Init();

    WiFi.begin(ssid, password);
    Serial.print("Connecting to WiFi");

    while (WiFi.status() != WL_CONNECTED) {
        delay(1000);
        Serial.print(".");
    }
    Serial.println("\nWiFi Connected!");
}

void loop() {
    if (!mfrc522.PICC_IsNewCardPresent()) {
        return;
    }
    if (!mfrc522.PICC_ReadCardSerial()) {
        return;
    }

    String rfidTag = "";
    for (byte i = 0; i < mfrc522.uid.size; i++) {
        rfidTag += String(mfrc522.uid.uidByte[i], HEX);
    }
    rfidTag.toUpperCase();

    Serial.print("RFID Scanned: ");
    Serial.println(rfidTag);

    sendToServer(rfidTag);

    delay(2000);  // Wait before scanning again
}

void sendToServer(String tag) {
    if (WiFi.status() == WL_CONNECTED) {
        HTTPClient http;
        http.begin(client, serverURL);
        http.addHeader("Content-Type", "application/json");

        StaticJsonDocument<200> jsonDoc;
        jsonDoc["rfid"] = tag;

        String requestBody;
        serializeJson(jsonDoc, requestBody);

        int httpResponseCode = http.POST(requestBody);
        Serial.print("Server Response: ");
        Serial.println(httpResponseCode);

        http.end();
    } else {
        Serial.println("WiFi Disconnected!");
    }
}
