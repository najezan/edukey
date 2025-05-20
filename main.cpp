/**
 * ESP32 MFRC522 RFID Integration for Face Recognition System
 * Using MFRC522v2 library for improved reliability
 * Supports both Identify and Add/Edit modes
 */

#include <SPI.h>
#include <MFRC522v2.h>
#include <MFRC522DriverSPI.h>
#include <MFRC522DriverPinSimple.h>
#include <MFRC522Constants.h>
#include <WiFi.h>
#include <ArduinoJson.h>

// Pin definitions for MFRC522
#define RST_PIN         22
#define SS_PIN          5
#define LED_PIN         2  // Built-in LED on most ESP32 boards
#define BUZZER_PIN      15 // Optional buzzer pin
#define MODE_SWITCH_PIN 4  // Optional physical switch for mode selection

// Network configuration
const char* ssid = "WIFI@KHOS-SISWA";         // Replace with your WiFi SSID
const char* password = "";  // Replace with your WiFi password
const char* serverIP = "192.168.200.88";     // Replace with your computer's IP address
const int serverPort = 8080;

// RFID reader instance with the new library
MFRC522DriverPinSimple ss_pin(SS_PIN);
MFRC522DriverSPI driver{ss_pin};
MFRC522 rfid{driver};

// Variables for card reading
String lastCardID = "";
unsigned long lastReadTime = 0;
const int cardReadCooldown = 3000; // 3 seconds cooldown between same card reads

// Mode selection
bool identifyMode = true; // true = identify mode, false = add/edit mode
unsigned long lastModeChangeTime = 0;
const int modeChangeCooldown = 1000; // 1 second cooldown for mode changes

// LED patterns for different modes
const int identifyModePattern[] = {500, 500}; // Slow blink for identify mode
const int addEditModePattern[] = {200, 200};  // Fast blink for add/edit mode
unsigned long lastLedToggleTime = 0;
int currentPatternIndex = 0;

// WiFi client
WiFiClient client;

// Function declarations
void connectToWiFi();
String getCardIDString();
void sendCardToServer(String cardID);
void blinkLED(int count, int interval);
void updateModeLED();
void beepSuccess();
void beepError();
void beepNewCard();
void beepModeChange();
void checkModeSwitch();

void setup() {
  // Initialize serial communication
  Serial.begin(115200);
  delay(1000); // Give time for serial to connect
  Serial.println("Starting RFID system...");
  
  // Initialize SPI bus
  SPI.begin();
  
  // Initialize MFRC522
  rfid.PCD_Init();
  
  // Show MFRC522 version
  byte version = rfid.PCD_GetVersion();
  Serial.print(F("MFRC522 firmware version: 0x"));
  Serial.println(version, HEX);
  
  // Initialize LED, buzzer and mode switch
  pinMode(LED_PIN, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(MODE_SWITCH_PIN, INPUT_PULLUP);
  digitalWrite(LED_PIN, LOW);
  digitalWrite(BUZZER_PIN, LOW);
  
  // Connect to WiFi
  connectToWiFi();
  
  // Initial mode notification
  Serial.print("Starting in ");
  Serial.print(identifyMode ? "IDENTIFY" : "ADD/EDIT");
  Serial.println(" mode");
  beepModeChange();
  
  Serial.println("RFID System ready. Waiting for cards...");
}

void loop() {
  // Check WiFi connection and reconnect if needed
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi connection lost. Reconnecting...");
    connectToWiFi();
  }
  
  // Check for mode switch changes
  checkModeSwitch();
  
  // Update LED pattern based on current mode
  updateModeLED();
  
  // Look for new cards
  if (rfid.PICC_IsNewCardPresent()) {
    if (rfid.PICC_ReadCardSerial()) {
      // Get card ID
      String cardID = getCardIDString();
      unsigned long currentTime = millis();
      
      // Check if it's a new card or if enough time has passed since last read
      if (cardID != lastCardID || (currentTime - lastReadTime > cardReadCooldown)) {
        lastCardID = cardID;
        lastReadTime = currentTime;
        
        Serial.print("Card detected: ");
        Serial.println(cardID);
        
        // Provide feedback
        blinkLED(3, 100);
        
        // Send card ID to server with current mode
        sendCardToServer(cardID);
      }
      
      // Halt PICC and stop encryption
      rfid.PICC_HaltA();
      rfid.PCD_StopCrypto1();
    }
  }
  
  // Small delay to prevent CPU overload
  delay(50);
}

void checkModeSwitch() {
  // Read the mode switch
  bool switchState = digitalRead(MODE_SWITCH_PIN) == LOW; // LOW when pressed (active low)
  unsigned long currentTime = millis();
  
  // Check if switch is pressed and cooldown has passed
  if (switchState && (currentTime - lastModeChangeTime > modeChangeCooldown)) {
    // Toggle mode
    identifyMode = !identifyMode;
    lastModeChangeTime = currentTime;
    
    // Notify mode change
    Serial.print("Mode changed to: ");
    Serial.println(identifyMode ? "IDENTIFY" : "ADD/EDIT");
    
    // Reset LED pattern
    currentPatternIndex = 0;
    lastLedToggleTime = currentTime;
    
    // Beep to indicate mode change
    beepModeChange();
  }
}

void updateModeLED() {
  unsigned long currentTime = millis();
  const int* pattern = identifyMode ? identifyModePattern : addEditModePattern;
  int patternLength = 2; // Both patterns have 2 elements (on time, off time)
  
  if (currentTime - lastLedToggleTime > pattern[currentPatternIndex]) {
    // Toggle LED
    digitalWrite(LED_PIN, !digitalRead(LED_PIN));
    
    // Move to next pattern element
    currentPatternIndex = (currentPatternIndex + 1) % patternLength;
    
    // Update toggle time
    lastLedToggleTime = currentTime;
  }
}

void connectToWiFi() {
  Serial.print("Connecting to WiFi network: ");
  Serial.println(ssid);
  
  // Start WiFi connection
  WiFi.begin(ssid, password);
  
  // Wait for connection with timeout and visual feedback
  int maxAttempts = 20;
  while (WiFi.status() != WL_CONNECTED && maxAttempts > 0) {
    digitalWrite(LED_PIN, !digitalRead(LED_PIN));  // Toggle LED
    delay(500);
    Serial.print(".");
    maxAttempts--;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println();
    Serial.println("WiFi connected successfully");
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());
    digitalWrite(LED_PIN, HIGH);  // Turn LED on when connected
  } else {
    Serial.println();
    Serial.println("WiFi connection failed");
    digitalWrite(LED_PIN, LOW);   // Turn LED off on failure
    beepError();
    
    // Wait and try again
    delay(5000);
  }
}

String getCardIDString() {
  String cardID = "";
  for (byte i = 0; i < rfid.uid.size; i++) {
    if (rfid.uid.uidByte[i] < 0x10) {
      cardID += "0";
    }
    cardID += String(rfid.uid.uidByte[i], HEX);
  }
  cardID.toUpperCase();
  return cardID;
}

void sendCardToServer(String cardID) {
  Serial.print("Sending card ID to server: ");
  Serial.println(cardID);
  
  // Create JSON document with mode information
  StaticJsonDocument<128> jsonDoc;
  jsonDoc["card_id"] = cardID;
  jsonDoc["mode"] = identifyMode ? "identify" : "add_edit";
  
  // Serialize JSON to string
  String jsonString;
  serializeJson(jsonDoc, jsonString);
  
  Serial.print("JSON payload: ");
  Serial.println(jsonString);
  
  // Connect to server
  Serial.print("Connecting to server at ");
  Serial.print(serverIP);
  Serial.print(":");
  Serial.println(serverPort);
  
  if (client.connect(serverIP, serverPort)) {
    Serial.println("Connected to server");
    
    // SIMPLIFIED HTTP REQUEST - Just send the JSON directly
    client.println(jsonString);
    
    // Wait for response with timeout
    unsigned long timeout = millis();
    while (client.connected() && millis() - timeout < 5000) {
      if (client.available()) {
        // Read response
        String response = client.readString();
        Serial.println("Server response:");
        Serial.println(response);
        
        // Parse JSON response
        StaticJsonDocument<128> responseDoc;
        DeserializationError error = deserializeJson(responseDoc, response);
        
        if (!error) {
          const char* status = responseDoc["status"];
          bool isNew = responseDoc["is_new"] | false;  // Default to false if not present
          
          if (String(status) == "success") {
            const char* person = responseDoc["person"];
            Serial.print("Authentication successful for: ");
            Serial.println(person);
            blinkLED(5, 50);  // Fast blink for success
            beepSuccess();
          } 
          else if (String(status) == "new_card") {
            Serial.println("New card detected");
            
            if (identifyMode) {
              // In identify mode, new cards just get a warning
              Serial.println("Card not registered (Identify Mode)");
              blinkLED(2, 500);  // Slow blink for warning
              beepError();
            } else {
              // In add/edit mode, new cards trigger registration
              Serial.println("Waiting for registration (Add/Edit Mode)");
              blinkLED(3, 200);  // Medium blink for registration
              beepNewCard();
            }
          }
          else {
            const char* message = responseDoc["message"];
            Serial.print("Authentication failed: ");
            Serial.println(message);
            digitalWrite(LED_PIN, LOW);  // Turn off LED for failure
            delay(1000);
            digitalWrite(LED_PIN, HIGH);  // Turn back on
            beepError();
          }
        } else {
          Serial.print("JSON parsing error: ");
          Serial.println(error.c_str());
          beepError();
        }
        break;
      }
      delay(10);
    }
    
    // Close connection
    client.stop();
    Serial.println("Connection closed");
  } else {
    Serial.println("Connection to server failed");
    beepError();
  }
}

void blinkLED(int count, int interval) {
  for (int i = 0; i < count; i++) {
    digitalWrite(LED_PIN, HIGH);
    delay(interval);
    digitalWrite(LED_PIN, LOW);
    delay(interval);
  }
  digitalWrite(LED_PIN, HIGH);  // Leave LED on after blinking
}

void beepSuccess() {
  // Sound success beep pattern (two short beeps)
  for (int i = 0; i < 2; i++) {
    digitalWrite(BUZZER_PIN, HIGH);
    delay(100);
    digitalWrite(BUZZER_PIN, LOW);
    delay(100);
  }
}

void beepError() {
  // Sound error beep pattern (one long beep)
  digitalWrite(BUZZER_PIN, HIGH);
  delay(500);
  digitalWrite(BUZZER_PIN, LOW);
}

void beepNewCard() {
  // Sound new card beep pattern (three short beeps)
  for (int i = 0; i < 3; i++) {
    digitalWrite(BUZZER_PIN, HIGH);
    delay(100);
    digitalWrite(BUZZER_PIN, LOW);
    delay(100);
  }
}

void beepModeChange() {
  // Sound mode change beep pattern (one short, one long)
  digitalWrite(BUZZER_PIN, HIGH);
  delay(100);
  digitalWrite(BUZZER_PIN, LOW);
  delay(100);
  digitalWrite(BUZZER_PIN, HIGH);
  delay(300);
  digitalWrite(BUZZER_PIN, LOW);
}
