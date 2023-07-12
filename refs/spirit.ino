//"Reach With Precision"
//SPIRIT
//A brushless flywheel blaster
//By wonderboy
//Software revision 23.4.13

#include <ClickButton.h>
#include <Servo.h>
#include <MicroView.h>

#define VOLT_PIN A0
#define TRIG_PIN 2
#define SOLENOID_PIN 3
#define ESC_PIN 5
#define MENU_PIN 6

#define FULLPOWER 2000
#define HIGHPOWER 1700
#define HALFPOWER 1400
#define MIDPOWER 1140
#define LOWPOWER 1070
#define OFF 1000

#define MAXROFDELAY 40
#define HIGHROFDELAY 80
#define MIDROFDELAY 100
#define MINROFDELAY 210

#define SEMI 1
#define BURST 2
#define BINARY 3
#define AUTO 4

Servo esc;
ClickButton trig(TRIG_PIN, LOW, CLICKBTN_PULLUP);
ClickButton menu(MENU_PIN, LOW, CLICKBTN_PULLUP);

int singleShotPulse = 40;            //power pulse time for solenoid
int spinDownTime = 500;              //how long to wait before powering off flywheels after firing
int recentShotBuffer = 1700;         //how long you can shoot with reduced delay after a recent shot, thanks torukmakto4
int spinDownBuffer = 5000;           //how long you can shoot with reduced delay while the flywheels should still be slowing down, thanks torukmakto4
int spinDownCompensation = 80;       //spin up delay reduction value for spinDown state
int recentShotCompensation = 130;    //spin up delay reduction value for recentShot state
int delayReduction = 0;              //delay reduction value applied to spinUpDelay under certain conditions
int origSpinUpDelay = 0;             //stores spinUpDelay before any edits in the menu
int spinUpDelay = 200;               //how long to wait on flywheel spin up from rest before firing
int singleShotDelay = HIGHROFDELAY;  //how long to wait after powering solenoid before it can be powered again
int mode = SEMI;                     //fire mode
int power = HIGHPOWER;               //throttle value (1000-2000)
int revPower = FULLPOWER;            //throttle value for initial spinup
int burstCount = 3;                  //how many shots to fire in burst mode
int shotCount = 0;                   //shot counter
int selected = 1;                    //menu selection
boolean rev = false;                 //flywheels spun up?
boolean settings = false;            //in settings mode?
boolean shot = false;                //shot was fired? (SEMI, BURST, TURBO)
boolean competition = false;         //when true, flywheels will spin at LOWPOWER throttle at all times
boolean lock = false;                //when true, fire mode cannot be changed
unsigned long spinDownTimer = 0;     //counts while the flywheels are spinning down

void setup() {
  pinMode(VOLT_PIN, INPUT);
  pinMode(SOLENOID_PIN, OUTPUT);
  digitalWrite(SOLENOID_PIN, LOW);
  origSpinUpDelay = spinUpDelay;
  menu.debounceTime = 50;
  menu.longClickTime = 2000;  //how long to wait before entering settings mode when menu button held
  trig.longClickTime = 750;   //how long to wait before locking fire mode when menu and trigger held

  //set operating parameters
  String str;
  if (digitalRead(MENU_PIN) == LOW) {
    power = LOWPOWER;
    revPower = HALFPOWER;
    spinDownBuffer = 3000;
    spinDownCompensation = 160;
    recentShotCompensation = 180;
    singleShotDelay = MIDROFDELAY;
    str = "SPIRIT\nLow Power\nMode\n>>>>>>>>>>";
  } else {
    str = "SPIRIT\nHigh PowerMode\n>>>>>>>>>>";
  }
  if (power == HIGHPOWER && digitalRead(TRIG_PIN) == LOW) {
    competition = !competition;
    str = "SPIRIT\nHigh PowerComp Mode\n>>>>>>>>>>";
  }
  if (power == LOWPOWER && digitalRead(TRIG_PIN) == LOW) {
    power = MIDPOWER;
    revPower = HALFPOWER;
    spinDownBuffer = 4000;
    spinDownCompensation = 130;
    recentShotCompensation = 160;
    singleShotDelay = MIDROFDELAY;
    str = "SPIRIT\nMid Power\nMode\n>>>>>>>>>>";
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
      esc.attach(ESC_PIN, OFF, FULLPOWER);
      esc.writeMicroseconds(OFF);
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
    } else if (menu.clicks > 0 && !settings && !lock) {
      mode++;
      if (mode > 4) {
        mode = 1;
      }
    }
  }

  //if not in settings mode, while trigger is pressed, spin up the flywheels and fire (mode dependent)
  if (!settings) {
    if (trig.depressed && !menu.depressed) {
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
          fireOnce();
          break;
      }
    } else {
      if (mode == BINARY && shot) {
        fireOnce();
      }
      spinOff();
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
    if (trig.clicks != 0) {
      selected++;
    }
    if (selected > 4) {
      selected = 1;
    }
    if (menu.clicks > 0) {
      switch (selected) {
        case 1:
          if (power == LOWPOWER) {
            power = MIDPOWER;
          } else if (power == MIDPOWER) {
            power = 1200;
          } else {
            power += 50;
          }
          if (power > FULLPOWER) {
            power = LOWPOWER;
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
            spinUpDelay = origSpinUpDelay;
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
  //reduce delay to minimum when in binary or semi auto for best trigger response
  delay((mode == BINARY || mode == SEMI) ? MAXROFDELAY : singleShotDelay);
  shotCount++;
}

//spin up the flywheels, delay activities for set period to allow flywheels to accelerate. reset the spin down timer
void spinOn() {
  if (!rev) {
    esc.writeMicroseconds(revPower);
    delay(spinUpDelay - delayReduction);
  }

  esc.writeMicroseconds(power);
  rev = true;
  delayReduction = recentShotCompensation;
  spinDownTimer = millis();
}

//cut power to the flywheels, but only after a set time
void spinOff() {
  if (millis() - spinDownTimer >= spinDownTime) {
    esc.writeMicroseconds(competition ? LOWPOWER : OFF);
    rev = false;
  }

  if (millis() - spinDownTimer >= recentShotBuffer) {
    delayReduction = spinDownCompensation;
  }

  if (millis() - spinDownTimer >= spinDownBuffer && !competition) {
    delayReduction = 0;
  }
}

//main (firing) screen display output
void displayMain() {
  int throttle = map(power, OFF, FULLPOWER, 0, 100);
  int countH = 53;
  uView.clear(PAGE);
  uView.setCursor(0, 0);
  uView.print("SPIRIT");
  if (!competition) {
    if (throttle > 9) {
      countH -= 6;
    }
    if (throttle > 99) {
      countH -= 6;
    }
    uView.setCursor(countH, 41);
    uView.print(throttle);
    uView.print("%");
  } else {
    uView.setCursor(41, 41);
    uView.print("KILL");
  }
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
      modeStr = "Turbo";
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

  int throttle = map(power, OFF, FULLPOWER, 0, 100);
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

//read battery voltage and display as image
void batt() {
  int v = floor((analogRead(VOLT_PIN) * 0.164));

  if (v >= 156) {
    bFull();
  } else if (v < 156 && v >= 140) {
    bClear();
    bOK();
  } else if (v < 140 && v >= 124) {
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