// Adjustable Values

// 130fps 3s Lipo = 1400
// 130fps 3s LiHV = 1375

const int motorMin = 1150;  // Motor Minimum speed, default 1150
const int motorMid = 1475;  // Motor Medium speed, default 1475 for ~130fps
const int motorMax = 2000;  // Motor Maximum speed, default 2000 for ~200fps
int solenoidOn = 45;        // Solenoid  On Delay, default 45ms
int solenoidOff = 55;       // Solenoid  Off Delay, default 55ms

// Libraries
#include <Servo.h>

// Switches
#define REV 3
#define TRIGGER 4
#define REV_1 5
#define REV_2 6
#define SELECT_1 11
#define SELECT_2 12

//Trigger and Burst States
int TriggerState = LOW;
int LastTriggerState = HIGH;

// Solenoid
#define MOSFET 2
int solenoidDelay;

// ESC Controls
Servo ESC1;
Servo ESC2;
Servo ESC3;
Servo ESC4;

// ESC values
int escSpeed;
int escLow = 1000;
int revDown = 1000;

void setup() {
  pinMode(REV, INPUT_PULLUP);
  pinMode(TRIGGER, INPUT_PULLUP);
  pinMode(REV_1, INPUT_PULLUP);
  pinMode(REV_2, INPUT_PULLUP);
  pinMode(SELECT_1, INPUT_PULLUP);
  pinMode(SELECT_2, INPUT_PULLUP);
  pinMode(MOSFET, OUTPUT);
  ESC1.attach(7, 1000, motorMax);
  ESC2.attach(8, 1000, motorMax);
  ESC3.attach(9, 1000, motorMax);
  ESC4.attach(10, 1000, motorMax);
  ESC1.write(escLow);
  ESC2.write(escLow);
  ESC3.write(escLow);
  ESC4.write(escLow);
  delay(6000);
}
// Rev Flywheels
void revup() {
  solenoidDelay = 200;               // Delay to prevent darts being pushed too early
  while (digitalRead(REV) == LOW) {  // Rev trigger pressed
    revMode();
    ESC1.write(escSpeed);
    ESC2.write(escSpeed);
    ESC3.write(escSpeed);
    ESC4.write(escSpeed);
    delay(solenoidDelay);
    selectFire();
    solenoidDelay = 0;               // Resets delay after firing 1st shot
    if (digitalRead(REV) == HIGH) {  // Rev trigger released
      revdown();
    }
  }
}
// Gradually rev flywheels down
void revdown() {
  for (revDown = escSpeed; revDown >= escLow; revDown -= 10) {
    ESC1.write(revDown);
    ESC2.write(revDown);
    ESC3.write(revDown);
    ESC4.write(revDown);
    if (digitalRead(REV) == LOW) {  // Rev trigger pressed
      break;
      revup();
    }
    delay(15);
  }
}
// Rev speed control
void revMode() {
  //Check Select Rev Switch
  if (digitalRead(REV_1) == HIGH && digitalRead(REV_2) == LOW) {  // Low Rev
    escSpeed = motorMin;
  } else if (digitalRead(REV_1) == HIGH && digitalRead(REV_2) == HIGH) {  // Med Rev
    escSpeed = motorMid;
  } else if (digitalRead(REV_1) == LOW && digitalRead(REV_2) == HIGH) {  // Max Rev
    escSpeed = motorMax;
  }
}
// Check Select Fire Switch
void selectFire() {
  if (digitalRead(SELECT_1) == HIGH && digitalRead(SELECT_2) == LOW) {  // Safety
    digitalWrite(MOSFET, LOW);
  } else if (digitalRead(SELECT_1) == LOW && digitalRead(SELECT_2) == HIGH) {  // Semi Auto
    semiAuto();
  } else if (digitalRead(SELECT_1) == HIGH && digitalRead(SELECT_2) == HIGH) {  // Full Auto
    fullAuto();
  }
}
void semiAuto() {  // Semi Auto
  TriggerState = digitalRead(TRIGGER);
  if (TriggerState != LastTriggerState) {
    if ((TriggerState == LOW)) {
      digitalWrite(MOSFET, HIGH);
      delay(solenoidOn);
      digitalWrite(MOSFET, LOW);
    } else {
      digitalWrite(MOSFET, LOW);
    }
    delay(20);
    LastTriggerState = TriggerState;
  }
}

void fullAuto() {  // Full Auto
  if (digitalRead(TRIGGER) == LOW) {
    digitalWrite(MOSFET, HIGH);
    delay(solenoidOn);
    digitalWrite(MOSFET, LOW);
    delay(solenoidOff);
    if (digitalRead(TRIGGER) == HIGH) {
      digitalWrite(MOSFET, LOW);
    }
  }
}

void loop() {
  revup();
}
