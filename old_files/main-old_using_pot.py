import board
import time
from digitalio import DigitalInOut, Pull
from pwmio import PWMOut
from analogio import AnalogIn
from adafruit_debouncer import Debouncer
from adafruit_motor import servo

def scale_to_range(x, input_min=0, input_max=65536, output_min=-1, output_max=1):
    return ((x - input_min) / (input_max - input_min)) * (output_max - output_min) + output_min

escOut = PWMOut(board.GP0, frequency=50)
motor1 = servo.ContinuousServo(escOut, min_pulse=1000, max_pulse=2000)

trig1Pin = DigitalInOut(board.GP16)
trig1Pin.switch_to_input(Pull.UP)
trigger1 = Debouncer(trig1Pin)

escSpeedPin = AnalogIn(board.GP26)
escspeed = 0
esczero = -1
escmin = -.8
escmax = 1
escmid = .5

time.sleep(.1)
motor1.throttle = esczero
motor1.throttle = escmax
motor1.throttle = escmin
time.sleep(3)
motor1.throttle = esczero
time.sleep(2)

while True:
    if trig1Pin.value:
        #escSpeed = 0 #scale_to_range(escSpeedPin.value)
        #print(escSpeed)
        motor1.throttle = -1
    else:
        escSpeed = scale_to_range(escSpeedPin.value)
        motor1.throttle = escSpeed 
