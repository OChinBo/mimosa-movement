//Created by ChungYuan ___ 14/06/2021

#include <WiFi.h>
#include <ArduinoJson.h>
#include <OSCMessage.h>

//const char *ssid = "hub1";
//const char *password = "32013201";
const char *ssid = "Chung-2.4G";
const char *password = "20783068";
const char *oscAddress = "/mimosa09";

const IPAddress serverIP(192,168,0,16);
uint16_t serverPort = 5589;
const int sensorPin = 34;

StaticJsonDocument<200> json_doc;
WiFiClient client;

void setup(){
    Serial.begin(115200);
    connectWifi();
    analogReadResolution(8);
    delay(1000);
}

void loop(){
    Serial.println("嘗試訪問伺服器:");
    Serial.println(serverIP);
    
    if (client.connect(serverIP, serverPort)){ //嘗試訪問目標地址
    
        Serial.println("訪問成功");

//        client.print("Hello world!");                     //像伺服器發送數據
        while (client.connected()){ //如果已連接或有收到的未讀取的數據
        
//            if (client.available()){
                  
                  char json_output[40];
                  json_doc["address"] = oscAddress;
                  json_doc["data"] = analogRead(sensorPin);
                  serializeJson(json_doc, json_output);
                  Serial.println(json_output);
                  
                  client.print(json_output);
  //              client.write(json_output, 40);
//            }
        }
        Serial.println("關閉當前連接");
        client.stop(); //關閉客戶端
    }
    else{
        Serial.println("訪問失敗");
        client.stop(); //關閉客戶端
    }
    delay(3000);
}

void connectWifi(){
    // Connect to WiFi network
    Serial.println();
    Serial.println();
    Serial.print("Connecting to ");
    Serial.println(ssid);
    
    WiFi.mode(WIFI_STA);
    WiFi.setSleep(false); //關閉STA模式下wifi休眠,提高響應速度
    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED)
    {
        delay(500);
        Serial.print(".");
    }
    Serial.println("Connected");
    Serial.print("IP Address:");
    Serial.println(WiFi.localIP());
    
    
}
