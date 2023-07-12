import board
import pulseio

from digitalio import DigitalInOut, Direction, Pull
from analogio import AnalogIn
from adafruit_debouncer import Debouncer
from adafruit_motor import servo
import time

# Helper to convert analog input to voltage
def getVoltage(curPin):
    return (curPin.value * 3.3) / 65536.0

def valMap(value, istart, istop, ostart, ostop):
  return ostart + (ostop - ostart) * ((value - istart) / (istop - istart))

def getAngle(curPin):
    voltin = getVoltage(curPin)
    return(valMap(int(voltin*10), 0, 32, 0, 180))

def calibrateESC(m1, m2, escSpdPin):
    # ESC Calibration requires you to start out high, then adjust to low and wait for beeps and then power off
    escSpeed = getAngle(escSpdPin)
    m1.angle = escSpeed
    m2.angle = escSpeed

#Brushless Setup
escOut = pulseio.PWMOut(board.GP2, duty_cycle=0, frequency=50)
#escOut.duty_cycle = setSpeed(0)
motor1 = servo.Servo(escOut, min_pulse=1000, max_pulse=2000)#, min_pulse=1.0, max_pulse=2.0)
motor1.angle = 0
escOut2 = pulseio.PWMOut(board.GP3, duty_cycle=0, frequency=50)
#escOut2.duty_cycle = setSpeed(0)
motor2 = servo.Servo(escOut2, min_pulse=1000, max_pulse=2000)#, min_pulse=1.0, max_pulse=2.0)
motor2.angle = 0

#Switches setup
switchLowPin = DigitalInOut(board.GP6)
switchLowPin.direction = Direction.OUTPUT
switchLowPin.value = True
switchHighPin = DigitalInOut(board.GP7)
switchHighPin.direction = Direction.OUTPUT
switchHighPin.value = False
trig1Pin = DigitalInOut(board.GP8)
trig1Pin.direction = Direction.INPUT
trig1Pin.pull = Pull.UP
trigger1 = Debouncer(trig1Pin)
trig2Pin = DigitalInOut(board.A5)
trig2Pin.direction = Direction.INPUT
trig2Pin.pull = Pull.UP
trigger2 = Debouncer(trig2Pin)

#Potentiometer setup
escSpeedHighPin = DigitalInOut(board.A1)
escSpeedHighPin.direction = Direction.OUTPUT
escSpeedHighPin.value = True
escSpeedPin = AnalogIn(board.GP26)
escSpeed = 0
# escSpeed = setSpeed(getVoltage(escSpeedPin))

# Uncomment for calibration of ESC's.
#while True: 
#   calibrateESC(motor1, motor2, escSpeedPin)
#   time.sleep(0.001)
#time.sleep(10)

# Counters and position variables 
trig1Count = 0
trig2Count = 0

while True:
    trigger1.update()
    if trigger1.value and not dartDoorSwitch.value:
        # Do not spin the barrel when first trigger is not pressed
        rotatePin.value = False
        dartFeedPin.value = False
        # reset timer for starting dart feeder
        curTime = time.monotonic()
        motor1.angle = 0
        motor2.angle = 0
    elif not trigger1.value:
        # Begin rotating the barrel
        rotatePin.value = True
        if trigger2.value and not dartDoorSwitch.value:
            trigger2.update()
        if trigger2.rose:
            # reset stop time on initial trigger release 
            stopTime = time.monotonic()
        if trigger2.value:
            # secondary trigger is not pressed
            trig2Count = 0
            t2cnt = 0
            # turn off dart feeder when second trigger is not pressed
            dartFeedPin.value = False
            # delay turning off the brushless motors for a bit to clear any darts
            if time.monotonic() -stopTime > .25:
                # turn off brushless motors
                motor1.angle = 0
                motor2.angle = 0            
            # continue resetting start timer for dart feeder if trigger 2 is not pressed
            curTime = time.monotonic()
        elif not dartDoorSwitch.value:
            # turn on brushless motors 
            escSpeed = getAngle(escSpeedPin)
            motor1.angle = escSpeed
            motor2.angle = escSpeed
            # delay starting up the dart feeder so the brushless motors have time to spin up
            if time.monotonic() - curTime > 0.25:
                dartFeedPin.value = True
    time.sleep(0.001)
