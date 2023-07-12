import board
import pulseio

from digitalio import DigitalInOut, Direction, Pull
from analogio import AnalogOut, AnalogIn
#import adafruit_dotstar as dotstar
from adafruit_debouncer import Debouncer
from adafruit_motor import servo
import time

import neopixel


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

def wheel(pos, order):
    # Input a value 0 to 255 to get a color value.
    # The colours are a transition r - g - b - back to r.
    if pos < 0 or pos > 255:
        r = g = b = 0
    elif pos < 85:
        r = int(pos * 3)
        g = int(255 - pos*3)
        b = 0
    elif pos < 170:
        pos -= 85
        r = int(255 - pos*3)
        g = 0
        b = int(pos*3)
    else:
        pos -= 170
        r = 0
        g = int(pos*3)
        b = int(255 - pos*3)
    return (r, g, b) if order == neopixel.RGB or order == neopixel.GRB else (r, g, b, 0)


def rainbow_cycle(j, order, num_pixels, pixels):
    for i in range(0,num_pixels):
        pixel_index = (i * 256 // num_pixels) + j
        pixels[i] = wheel(pixel_index & 255, order)
    pixels.show()


# Neo Pixel setup
pixel_pin = board.D5
num_pixels = 10
ORDER = neopixel.GRB
pixels = neopixel.NeoPixel(pixel_pin, num_pixels, brightness=0.8, auto_write=False,
                           pixel_order=ORDER)
pixels.fill((175,77,205))
pixels.show()

#Brushless Setup
escOut = pulseio.PWMOut(board.D9, duty_cycle=0, frequency=50)
#escOut.duty_cycle = setSpeed(0)
motor1 = servo.Servo(escOut, min_pulse=1000, max_pulse=2000)#, min_pulse=1.0, max_pulse=2.0)
motor1.angle = 0
escOut2 = pulseio.PWMOut(board.D10, duty_cycle=0, frequency=50)
#escOut2.duty_cycle = setSpeed(0)
motor2 = servo.Servo(escOut2, min_pulse=1000, max_pulse=2000)#, min_pulse=1.0, max_pulse=2.0)
motor2.angle = 0

#Switches setup
switchLowPin = DigitalInOut(board.D11)
switchLowPin.direction = Direction.OUTPUT
switchLowPin.value = True
switchHighPin = DigitalInOut(board.D12)
switchHighPin.direction = Direction.OUTPUT
switchHighPin.value = False
trig1Pin = DigitalInOut(board.A4)
trig1Pin.direction = Direction.INPUT
trig1Pin.pull = Pull.UP
trigger1 = Debouncer(trig1Pin)
trig2Pin = DigitalInOut(board.A5)
trig2Pin.direction = Direction.INPUT
trig2Pin.pull = Pull.UP
trigger2 = Debouncer(trig2Pin)
dartDoorPin = DigitalInOut(board.SCK)
dartDoorPin.direction = Direction.INPUT
dartDoorPin.pull = Pull.UP
dartDoorSwitch = Debouncer(dartDoorPin)

#Potentiometer setup
escSpeedHighPin = DigitalInOut(board.A1)
escSpeedHighPin.direction = Direction.OUTPUT
escSpeedHighPin.value = True
escSpeedPin = AnalogIn(board.A0)
escSpeed = 0
# escSpeed = setSpeed(getVoltage(escSpeedPin))

#DC Motor setup 
dartFeedPin = DigitalInOut(board.A3)
dartFeedPin.direction = Direction.OUTPUT
dartFeedPin.value = False
rotatePin = DigitalInOut(board.A2)
rotatePin.direction = Direction.OUTPUT
rotatePin.value = False
startTime = time.monotonic()
stopTime = time.monotonic()


# Uncomment for calibration of ESC's.
#while True: 
#   calibrateESC(motor1, motor2, escSpeedPin)
#   time.sleep(0.001)
#time.sleep(10)

# Counters and position variables 
trig1Count = 0
trig2Count = 0
# following are positional counters of neopixels
t2cnt = 0
t1cnt = 0
# position of color wheel variable
pcolor = 0
# current color 
COLOR = (0,0,0)

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
        pixels[5] = (0,255,0)
        pixels[6] = (0,255,0)
        rainbow_cycle(pcolor, ORDER, 5, pixels)
        pcolor += 1
        if pcolor == 256:
            pcolor = 0
        t1cnt = 0
        t2cnt = 0
        COLOR = (0,255,0)
        trig1Count = 0
        trig2Count = 0
    elif not trigger1.value:
        # Begin rotating the barrel
        rotatePin.value = True
        if trigger2.value and not dartDoorSwitch.value:
            pixels.fill((0,0,0,))

            pixels[5] = (255,255,0)
            pixels[6] = (255,255,0)
            pixels[t1cnt] = COLOR  
            pixels.show()
            if trig1Count % 2 == 0:
                t1cnt += 1
                if t1cnt == 5:
                    t1cnt = 0
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
            # second trigger pressed, change color to red
            COLOR = (255,0,0)
            # do not enable dart feed if the dart feed door is open
            pixels.fill((0,0,0))
            pixels[5] = (255,0,0)
            pixels[6] = (255,0,0)
            pixels[t2cnt] = COLOR
            pixels.show()
            if trig2Count % 2 == 0:
                t2cnt += 1
                if t2cnt == 5:
                    t2cnt = 0
            pixels.show()
            # turn on brushless motors 
            escSpeed = getAngle(escSpeedPin)
            motor1.angle = escSpeed
            motor2.angle = escSpeed
            # delay starting up the dart feeder so the brushless motors have time to spin up
            if time.monotonic() - curTime > 0.25:
                dartFeedPin.value = True

    dartDoorSwitch.update()
    if dartDoorSwitch.rose:
        stopTime = time.monotonic()
    if dartDoorSwitch.value:
        # Dart door is open - kill everything and set color
        t2cnt = 0
        t1cnt = 0
        trig2Count = 0
        trig1Count = 0
        pixels.fill((0,0,255))
        pixels.show()
        COLOR = (0,255,0)
        # ensure that dart feed is disabled if the door is open 
        dartFeedPin.value = False
        rotatePin.value = False

        # delay turning off the brushless motors to clear any darts
        if time.monotonic() - stopTime > 0.25:
            motor1.angle = 0
            motor2.angle = 0
        # reset curTime in case we're holding teh triggers down still while door is open so 
        # firing re-starts as if we just pressed the triggers
        curTime = time.monotonic()
    time.sleep(0.001)
