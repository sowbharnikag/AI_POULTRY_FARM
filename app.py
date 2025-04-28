#include <WiFi.h>
#include <HTTPClient.h>

const char* ssid = "YOUR_WIFI";
const char* password = "YOUR_PASSWORD";

void setup() {
  WiFi.begin(ssid, password);
  Serial.begin(115200);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Connecting..");
  }
}

void loop() {
  if(WiFi.status()== WL_CONNECTED){
    HTTPClient http;
    
    String serverName = "https://sheetdb.io/api/v1/YOUR_SHEETDB_ID";

    http.begin(serverName);
    http.addHeader("Content-Type", "application/json");

    float temperature = 28.5;
    float humidity = 60.2;
    String payload = "{\"data\": [{\"Temperature\": \"" + String(temperature) + "\", \"Humidity\": \"" + String(humidity) + "\", \"Timestamp\": \"" + String(millis()/1000) + "\"}]}";

    int httpResponseCode = http.POST(payload);

    if(httpResponseCode>0){
      String response = http.getString();
      Serial.println(response);
    }
    http.end();
  }
  delay(10000); // send every 10 seconds
}
