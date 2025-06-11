#include <SoftwareSerial.h>
SoftwareSerial BTSerial(2, 3);  // RX, TX

const int IN1[] = {4, 6, 8, 10};  // Motor IN1 pinleri
const int IN2[] = {5, 7, 9, 11};  // Motor IN2 pinleri
const int motorCount = 4;

bool motorActive[motorCount] = {false};
unsigned long motorEndTime[motorCount] = {0};
String inputBuffer = "";

void setup() {
  Serial.begin(9600);       // Serial Monitor için
  BTSerial.begin(9600);     // Bluetooth için

  for (int i = 0; i < motorCount; i++) {
    pinMode(IN1[i], OUTPUT);
    pinMode(IN2[i], OUTPUT);
  }

  Serial.println("🟢 System ON - Waiting for Bluetooth data...");
}

void loop() {
  // Bluetooth üzerinden gelen veriyi satır bazlı oku
  while (BTSerial.available()) {
    char c = BTSerial.read();
    if (c == '\n') {
      processData(inputBuffer);
      inputBuffer = "";  // Buffer sıfırla
    } else {
      inputBuffer += c;
    }
  }

  // Motorları süreye göre durdur
  unsigned long now = millis();
  for (int i = 0; i < motorCount; i++) {
    if (motorActive[i] && now >= motorEndTime[i]) {
      digitalWrite(IN1[i], LOW);
      digitalWrite(IN2[i], LOW);
      motorActive[i] = false;
      Serial.print("🛑 Motor ");
      Serial.print(i + 1);
      Serial.println(" stopped.");
    }
  }
}

void processData(String data) {
  data.trim();
  Serial.print("📥 Received: ");
  Serial.println(data);

  int firstComma = data.indexOf(',');
  int secondComma = data.indexOf(',', firstComma + 1);
  int thirdComma = data.indexOf(',', secondComma + 1);

  if (firstComma == -1 || secondComma == -1 || thirdComma == -1) {
    Serial.println("⚠️ Invalid data format (missing commas)!");
    return;
  }

  int motor_id = data.substring(0, firstComma).toInt();
  int freq = data.substring(firstComma + 1, secondComma).toInt();
  int pwm = data.substring(secondComma + 1, thirdComma).toInt();
  float duration = data.substring(thirdComma + 1).toFloat();

  if (motor_id >= 1 && motor_id <= motorCount) {
    int idx = motor_id - 1;
    unsigned long now = millis();
    unsigned long durationMs = duration * 1000;

    analogWrite(IN1[idx], pwm);
    digitalWrite(IN2[idx], LOW);

    motorActive[idx] = true;
    motorEndTime[idx] = now + durationMs;

    Serial.print("🎵 Motor ");
    Serial.print(motor_id);
    Serial.print(" ON - PWM: ");
    Serial.print(pwm);
    Serial.print(", Duration: ");
    Serial.print(duration, 2);
    Serial.println("s");
  } else {
    Serial.println("⚠️ Invalid motor ID!");
  }
}

