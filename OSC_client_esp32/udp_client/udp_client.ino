//Created by huyyoo ___ 12/02/2021

#define DELAY 0

//************Connect WIFI***************//
#include <WiFi.h>
#include <WiFiUdp.h>
#include <OSCMessage.h>
char ssid[] = "hub_1";         
char pass[] = "32013201";       
WiFiUDP Udp;       

//debug
const IPAddress outIp(192,168,0,14);     
const unsigned int outPort = 5589;          
const unsigned int localPort = 7777;  
const int sensorPin = 34;


void setup() {
  Serial.begin(115200);
  connectWifi();
  analogReadResolution(16);
  delay(1000);
}

void loop() {
  OSCMessage msg("/mimosa09");
  msg.add(analogRead(sensorPin));
  Udp.beginPacket(outIp, outPort);
  msg.send(Udp);
  Udp.endPacket();
  msg.empty();
  
  delay(DELAY);
}

void connectWifi(){
   // Connect to WiFi network
    Serial.println();
    Serial.println();
    Serial.print("Connecting to ");
    Serial.println(ssid);
    
    WiFi.begin(ssid, pass);
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    
    Serial.println("");
    Serial.println("WiFi connected");
    Serial.println("IP address: ");
    Serial.println(WiFi.localIP());
    Serial.println("Starting UDP");
    
    Udp.begin(localPort);
    
    Serial.print("Local port: ");
#ifdef ESP32
    Serial.println(localPort);
#else
    Serial.println(Udp.localPort());
#endif
}
