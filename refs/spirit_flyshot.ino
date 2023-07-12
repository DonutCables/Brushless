//"Reach With Precision"
//SPIRIT
//A brushless flywheel blaster
//By wonderboy
//Software revision 23.6.20

#include <ClickButton.h>
#include <Servo.h>
#include <MicroView.h>

#define VOLT_PIN A0
#define TRIG_PIN 2
#define SOLENOID_PIN 3
#define ESC_PIN 5
#define MENU_PIN 6

#define MOTOR_P_DIV2 7
#define T0H 100
#define T1H 400
#define TL 500

#define FULL 2000
#define OFF 1000

#define SAFETYTIMEOUT 10000

#define MAXRPM 40000
#define MINRPM 5000
#define FIVEPERCENT 1750

#define MAXROFDELAY 35
#define HIGHROFDELAY 65
#define MIDROFDELAY 95
#define MINROFDELAY 215

#define SEMI 1
#define BURST 3
#define BINARY 4
#define AUTO 2
#define DEVOTION 5

Servo esc;
ClickButton trig(TRIG_PIN, LOW, CLICKBTN_PULLUP);
ClickButton menu(MENU_PIN, LOW, CLICKBTN_PULLUP);

const bool bcar = true;  //set to true if the BCAR muzzle is installed

const long HIGHPOWER = MINRPM + (FIVEPERCENT * (15L + bcar));  //target RPM 31250
const long MIDPOWER = MINRPM + (FIVEPERCENT * (10L + bcar));   //target RPM 22500
const long LOWPOWER = MINRPM + (FIVEPERCENT * (6L + bcar));    //target RPM 15550
const int singleShotPulse = 35;                                //power pulse time for solenoid
const int spinDownTime = 500;                                  //how long to wait before powering off flywheels after firing
int recentShotBuffer = 1800;                                   //how long you can shoot with reduced delay after a recent shot, thanks torukmakto4
int spinDownBuffer = 5000;                                     //how long you can shoot with reduced delay while the flywheels should still be slowing down, thanks torukmakto4
int spinDownCompensation = 80;                                 //spin up delay reduction value for spinDown state
int recentShotCompensation = 130;                              //spin up delay reduction value for recentShot state
int delayReduction = 0;                                        //delay reduction value applied to spinUpDelay under certain conditions
int spinUpDelay = 180;                                         //how long to wait on flywheel spin up from rest before firing
int singleShotDelay = HIGHROFDELAY;                            //how long to wait after powering solenoid before it can be powered again
int mode = SEMI;                                               //fire mode
long targetRPM = HIGHPOWER;                                    //RPM value
int burstCount = 3;                                            //how many shots to fire in burst mode
int shotCount = 0;                                             //shot counter
int devotionCount = 0;                                         //devotion mode shot counter
int selected = 1;                                              //menu selection
bool rev = false;                                              //flywheels spun up?
bool settings = false;                                         //in settings mode?
bool shot = false;                                             //shot was fired? (SEMI, BURST, TURBO)
bool lock = false;                                             //when true, fire mode cannot be changed
long spinDownTimer = 0;                                        //counts up while the flywheels are spinning down
long lastRevTime = 0;                                          //stores timestamp of last rev
long safetyTimer = 0;                                          //counts up while revving for safety shutoff

void setup() {
  pinMode(VOLT_PIN, INPUT);
  pinMode(SOLENOID_PIN, OUTPUT);
  digitalWrite(SOLENOID_PIN, LOW);
  menu.debounceTime = 40;
  trig.debounceTime = 10;
  menu.longClickTime = 2000;  //how long to wait before entering settings mode when menu button held
  trig.longClickTime = 750;   //how long to wait before locking fire mode when menu and trigger held

  //set operating parameters
  String str = "SPIRIT\nHigh PowerMode\n>>>>>>>>>>";
  if (digitalRead(MENU_PIN) == LOW) {
    targetRPM = LOWPOWER;
    spinUpDelay = 150;
    spinDownBuffer = 4000;
    str = "SPIRIT\nLow Power\nMode\n>>>>>>>>>>";
  } else if (digitalRead(TRIG_PIN) == LOW) {
    targetRPM = MIDPOWER;
    spinUpDelay = 165;
    spinDownBuffer = 4500;
    str = "SPIRIT\nMid Power\nMode\n>>>>>>>>>>";
  }

  if (targetRPM < HIGHPOWER) {
    spinDownCompensation = 70;
    recentShotCompensation = 120;
    singleShotDelay = MIDROFDELAY;
  }

  //startup animation
  int len = str.length() + 1;
  char msg[len];
  str.toCharArray(msg, len);

  uView.begin();
  uView.clear(PAGE);
  uView.setCursor(0, 0);
  uView.setFontType(1);
  for (int i = 0; i < sizeof(msg); i++) {
    if (i > 6) {
      uView.setFontType(0);
    } else {
      delay(70);
    }
    if (i == 16) {
      //initialize ESCs
      esc.attach(ESC_PIN, OFF, FULL);
      esc.writeMicroseconds(OFF);
      updateSpeed(targetRPM);
    }
    uView.print(msg[i]);
    uView.display();
    delay(60);
  }
}

void loop() {
  trig.Update();
  menu.Update();

  //if menu button is held switch to settings screen. if it is pressed on the main screen, change fire mode
  if (!trig.depressed && menu.clicks != 0) {
    if (menu.clicks < 0) {
      settings = !settings;
      menu.clicks = 0;
      updateSpeed(targetRPM);
    } else if (menu.clicks > 0 && !settings && !lock) {
      mode++;
      if (mode > 5) {
        mode = 1;
      }
    }
  }

  //if not in settings mode, while trigger is pressed, spin up the flywheels and fire (mode dependent)
  if (!settings) {
    if (trig.depressed && !menu.depressed && safetyTimer < SAFETYTIMEOUT) {
      spinOn();
      switch (mode) {
        case SEMI:
        case BINARY:
          if (!shot) {
            fireOnce();
            shot = true;
          }
          break;
        case BURST:
          if (!shot) {
            for (int i = 0; i < burstCount; i++) {
              fireOnce();
            }
            shot = true;
          }
          break;
        case AUTO:
        case DEVOTION:
          fireOnce();
          break;
      }
    } else {
      if (mode == BINARY && shot) {
        fireOnce();
      }
      spinOff();
      devotionCount = 0;
      shot = false;
      digitalWrite(SOLENOID_PIN, LOW);
    }

    //if menu is held and trigger is held, lock/unlock the fire mode
    if (menu.depressed && trig.clicks < 0) {
      lock = !lock;
      menu.clicks = 0;
    }

    if (shotCount > 999) {
      shotCount = 0;
    }

    displayMain();
  } else {
    //settings menu
    if (menu.clicks != 0) {
      selected++;
    }
    if (selected > 4) {
      selected = 1;
    }
    if (trig.clicks > 0) {
      switch (selected) {
        case 1:
          targetRPM += FIVEPERCENT;
          if (targetRPM > MAXRPM) {
            targetRPM = MINRPM;
          }
          break;
        case 2:
          burstCount++;
          if (burstCount > 6) {
            burstCount = 2;
          }
          break;
        case 3:
          singleShotDelay -= 10;
          if (singleShotDelay < MAXROFDELAY) {
            singleShotDelay = MINROFDELAY;
          }
          break;
        case 4:
          spinUpDelay += 10;
          if (spinUpDelay > 500) {
            spinUpDelay = 100;
          }
          break;
      }
    }
    esc.writeMicroseconds(OFF);
    digitalWrite(SOLENOID_PIN, LOW);
    shotCount = 0;
    displaySettings(selected);
  }
}

//actuate the solenoid, and increment shot counter
void fireOnce() {
  digitalWrite(SOLENOID_PIN, HIGH);
  delay(singleShotPulse);
  digitalWrite(SOLENOID_PIN, LOW);
  if (mode != DEVOTION) {
    delay((mode == BINARY || mode == SEMI) ? MAXROFDELAY : singleShotDelay);  //reduce delay to minimum when in binary or semi auto for best trigger response
  } else {
    if (devotionCount >= 15) {
      delay(MAXROFDELAY);  //clamp to max ROF after 15 shots
    } else {
      delay(constrain((MINROFDELAY - 50 + (0.5 * devotionCount * devotionCount) - (18 * devotionCount)), MAXROFDELAY, MINROFDELAY));  //polynomial delay ramping for Devotion mode
    }
    devotionCount++;
  }
  shotCount++;
}

//spin up the flywheels, delay activities for set period to allow flywheels to accelerate. reset the spin down timer
void spinOn() {
  if (!rev) {
    esc.writeMicroseconds(FULL);
    delay(spinUpDelay - delayReduction);
  }

  esc.writeMicroseconds(FULL);
  rev = true;
  delayReduction = recentShotCompensation;
  spinDownTimer = millis();
  safetyTimer = millis() - lastRevTime;
}

//cut power to the flywheels, but only after a set time
void spinOff() {
  if (millis() - spinDownTimer >= spinDownTime) {
    esc.writeMicroseconds(OFF);
    rev = false;
    lastRevTime = millis();
  }

  if (millis() - spinDownTimer >= recentShotBuffer) {
    delayReduction = spinDownCompensation;
  }

  if (millis() - spinDownTimer >= spinDownBuffer) {
    delayReduction = 0;
  }
}

//main (firing) screen display output
void displayMain() {
  int throttle = map(targetRPM, MINRPM, MAXRPM, 0, 100);
  int countH = 53;
  uView.clear(PAGE);
  uView.setCursor(0, 0);
  uView.print("SPIRIT");
  if (throttle > 9) {
    countH -= 6;
  }
  if (throttle > 99) {
    countH -= 6;
  }
  uView.setCursor(countH, 41);
  uView.print(throttle);
  uView.print("%");
  uView.lineH(0, 9, 64);

  countH = 28;
  if (shotCount > 9) {
    countH -= 6;
  }
  if (shotCount > 99) {
    countH -= 6;
  }
  uView.setCursor(countH, 15);
  uView.setFontType(2);
  uView.print(shotCount);

  uView.setFontType(0);
  uView.lineH(0, 38, 64);
  uView.setCursor(0, 41);
  String modeStr;
  switch (mode) {
    case SEMI:
      modeStr = "Semi";
      break;
    case BURST:
      modeStr = "Burst";
      break;
    case AUTO:
      modeStr = "Auto";
      break;
    case BINARY:
      modeStr = "Echo";
      break;
    case DEVOTION:
      modeStr = "Ramp";
      break;
  }
  if (lock) {
    modeStr = modeStr + "*";
  } else {
    modeStr.replace("*", "");
  }
  uView.print(modeStr);
  batt();
  uView.display();
}

//settings screen display output
void displaySettings(int selected) {
  int t = millis() / 1000;
  int hours = t / 3600;
  t %= 3600;
  int minutes = t / 60;
  t %= 60;
  int seconds = t;

  int throttle = map(targetRPM, MINRPM, MAXRPM, 0, 100);
  int fireRate = 1000 / (singleShotDelay + singleShotPulse);

  uView.clear(PAGE);
  uView.setCursor(0, 0);
  uView.print("0");
  uView.print(hours);
  uView.print(":");
  if (minutes < 10) {
    uView.print("0");
  }
  uView.print(minutes);
  uView.print(":");
  if (seconds < 10) {
    uView.print("0");
  }
  uView.print(seconds);
  uView.lineH(0, 9, 64);
  uView.setCursor(0, 11);
  uView.print("Thrttl ");
  uView.setCursor(40, 11);
  if (selected == 1) {
    uView.setColor(BLACK);
  }
  uView.print(throttle);
  uView.setColor(WHITE);
  uView.setCursor(0, 20);
  uView.print("BrstCnt ");
  uView.setCursor(46, 20);
  if (selected == 2) {
    uView.setColor(BLACK);
  }
  uView.print(burstCount);
  uView.setColor(WHITE);
  uView.setCursor(0, 29);
  uView.print("FireRte ");
  uView.setCursor(46, 29);
  if (selected == 3) {
    uView.setColor(BLACK);
  }
  uView.print(fireRate);
  uView.setColor(WHITE);
  uView.setCursor(0, 38);
  uView.print("RevDly ");
  uView.setCursor(40, 38);
  if (selected == 4) {
    uView.setColor(BLACK);
  }
  uView.print(spinUpDelay);
  uView.setColor(WHITE);
  uView.display();
}

//update the Flyshot set speed via PWM signal (thanks u/dpairsoft!)
void updateSpeed(long MotorRPM) {
  esc.detach();
  unsigned long SetPoint = (unsigned long)320000000 / (MotorRPM * MOTOR_P_DIV2);
  unsigned int packet = SetPoint | 0x8000;

  for (int pksend = 0; pksend < 10; pksend++) {
    // Send the leading throttle-range pulse
    digitalWrite(ESC_PIN, HIGH);
    delayMicroseconds(1000);

    digitalWrite(ESC_PIN, LOW);
    delayMicroseconds(10);

    // Send the packet MSB first
    for (int i = 15; i >= 0; i--) {
      if (packet & (0x0001 << i)) {
        // Send a T1H pulse
        digitalWrite(ESC_PIN, HIGH);
        delayMicroseconds(T1H);
        digitalWrite(ESC_PIN, LOW);
        delayMicroseconds(TL);
      } else {
        // Send a T0H pulse
        digitalWrite(ESC_PIN, HIGH);
        delayMicroseconds(T0H);
        digitalWrite(ESC_PIN, LOW);
        delayMicroseconds(TL);
      }
    }

    // Send the trailing throttle-range pulse
    digitalWrite(ESC_PIN, HIGH);
    delayMicroseconds(1000);
    digitalWrite(ESC_PIN, LOW);
    delayMicroseconds(10);
  }

  esc.attach(ESC_PIN, OFF, FULL);
}

//read battery voltage and display as image
void batt() {
  int v = floor((analogRead(VOLT_PIN) * 0.164));

  if (v >= 160) {
    bFull();
  } else if (v < 160 && v >= 150) {
    bClear();
    bOK();
  } else if (v < 150 && v >= 130) {
    bClear();
    bLow();
  } else {
    bClear();
    bDead();
  }
}

//battery bitmaps
void bClear() {
  uView.pixel(50, 0, 0, 0);
  uView.pixel(50, 1, 0, 0);
  uView.pixel(50, 2, 0, 0);
  uView.pixel(50, 3, 0, 0);
  uView.pixel(50, 5, 0, 0);
  uView.pixel(55, 0, 0, 0);
  uView.pixel(56, 0, 0, 0);
  uView.pixel(57, 0, 0, 0);
  uView.pixel(58, 0, 0, 0);
  uView.pixel(59, 0, 0, 0);
  uView.pixel(60, 0, 0, 0);
  uView.pixel(61, 0, 0, 0);
  uView.pixel(62, 0, 0, 0);
  uView.pixel(63, 0, 0, 0);
  uView.pixel(55, 1, 0, 0);
  uView.pixel(63, 1, 0, 0);
  uView.pixel(54, 2, 0, 0);
  uView.pixel(55, 2, 0, 0);
  uView.pixel(57, 2, 0, 0);
  uView.pixel(59, 2, 0, 0);
  uView.pixel(61, 2, 0, 0);
  uView.pixel(63, 2, 0, 0);
  uView.pixel(54, 3, 0, 0);
  uView.pixel(55, 3, 0, 0);
  uView.pixel(57, 3, 0, 0);
  uView.pixel(59, 3, 0, 0);
  uView.pixel(61, 3, 0, 0);
  uView.pixel(63, 3, 0, 0);
  uView.pixel(55, 4, 0, 0);
  uView.pixel(63, 4, 0, 0);
  uView.pixel(55, 5, 0, 0);
  uView.pixel(56, 5, 0, 0);
  uView.pixel(57, 5, 0, 0);
  uView.pixel(58, 5, 0, 0);
  uView.pixel(59, 5, 0, 0);
  uView.pixel(60, 5, 0, 0);
  uView.pixel(61, 5, 0, 0);
  uView.pixel(62, 5, 0, 0);
  uView.pixel(63, 5, 0, 0);
}
void bFull() {
  uView.pixel(55, 0);
  uView.pixel(56, 0);
  uView.pixel(57, 0);
  uView.pixel(58, 0);
  uView.pixel(59, 0);
  uView.pixel(60, 0);
  uView.pixel(61, 0);
  uView.pixel(62, 0);
  uView.pixel(63, 0);
  uView.pixel(55, 1);
  uView.pixel(63, 1);
  uView.pixel(54, 2);
  uView.pixel(55, 2);
  uView.pixel(57, 2);
  uView.pixel(59, 2);
  uView.pixel(61, 2);
  uView.pixel(63, 2);
  uView.pixel(54, 3);
  uView.pixel(55, 3);
  uView.pixel(57, 3);
  uView.pixel(59, 3);
  uView.pixel(61, 3);
  uView.pixel(63, 3);
  uView.pixel(55, 4);
  uView.pixel(63, 4);
  uView.pixel(55, 5);
  uView.pixel(56, 5);
  uView.pixel(57, 5);
  uView.pixel(58, 5);
  uView.pixel(59, 5);
  uView.pixel(60, 5);
  uView.pixel(61, 5);
  uView.pixel(62, 5);
  uView.pixel(63, 5);
}
void bOK() {
  uView.pixel(55, 0);
  uView.pixel(56, 0);
  uView.pixel(57, 0);
  uView.pixel(58, 0);
  uView.pixel(59, 0);
  uView.pixel(60, 0);
  uView.pixel(61, 0);
  uView.pixel(62, 0);
  uView.pixel(63, 0);
  uView.pixel(55, 1);
  uView.pixel(63, 1);
  uView.pixel(54, 2);
  uView.pixel(55, 2);
  uView.pixel(59, 2);
  uView.pixel(61, 2);
  uView.pixel(63, 2);
  uView.pixel(54, 3);
  uView.pixel(55, 3);
  uView.pixel(59, 3);
  uView.pixel(61, 3);
  uView.pixel(63, 3);
  uView.pixel(55, 4);
  uView.pixel(63, 4);
  uView.pixel(55, 5);
  uView.pixel(56, 5);
  uView.pixel(57, 5);
  uView.pixel(58, 5);
  uView.pixel(59, 5);
  uView.pixel(60, 5);
  uView.pixel(61, 5);
  uView.pixel(62, 5);
  uView.pixel(63, 5);
}
void bLow() {
  uView.pixel(55, 0);
  uView.pixel(56, 0);
  uView.pixel(57, 0);
  uView.pixel(58, 0);
  uView.pixel(59, 0);
  uView.pixel(60, 0);
  uView.pixel(61, 0);
  uView.pixel(62, 0);
  uView.pixel(63, 0);
  uView.pixel(55, 1);
  uView.pixel(63, 1);
  uView.pixel(54, 2);
  uView.pixel(55, 2);
  uView.pixel(61, 2);
  uView.pixel(63, 2);
  uView.pixel(54, 3);
  uView.pixel(55, 3);
  uView.pixel(61, 3);
  uView.pixel(63, 3);
  uView.pixel(55, 4);
  uView.pixel(63, 4);
  uView.pixel(55, 5);
  uView.pixel(56, 5);
  uView.pixel(57, 5);
  uView.pixel(58, 5);
  uView.pixel(59, 5);
  uView.pixel(60, 5);
  uView.pixel(61, 5);
  uView.pixel(62, 5);
  uView.pixel(63, 5);
}
void bDead() {
  uView.pixel(55, 0);
  uView.pixel(56, 0);
  uView.pixel(57, 0);
  uView.pixel(58, 0);
  uView.pixel(59, 0);
  uView.pixel(60, 0);
  uView.pixel(61, 0);
  uView.pixel(62, 0);
  uView.pixel(63, 0);
  uView.pixel(55, 1);
  uView.pixel(63, 1);
  uView.pixel(54, 2);
  uView.pixel(55, 2);
  uView.pixel(63, 2);
  uView.pixel(54, 3);
  uView.pixel(55, 3);
  uView.pixel(63, 3);
  uView.pixel(55, 4);
  uView.pixel(63, 4);
  uView.pixel(55, 5);
  uView.pixel(56, 5);
  uView.pixel(57, 5);
  uView.pixel(58, 5);
  uView.pixel(59, 5);
  uView.pixel(60, 5);
  uView.pixel(61, 5);
  uView.pixel(62, 5);
  uView.pixel(63, 5);
  uView.pixel(50, 0);
  uView.pixel(50, 1);
  uView.pixel(50, 2);
  uView.pixel(50, 3);
  uView.pixel(50, 5);
}