import board
from digitalio import DigitalInOut, Pull
from pwmio import PWMOut
from analogio import AnalogIn
from adafruit_debouncer import Debouncer
from adafruit_motor import servo

def getVoltage(curPin):
    return (curPin.value * 3.3) / 65536.0

def valMap(value, istart, istop, ostart, ostop):
  return ostart + (ostop - ostart) * ((value - istart) / (istop - istart))

def getAngle(curPin):
    voltin = getVoltage(curPin)
    return(valMap(int(voltin*10), 0, 32, 0, 180))

escOut = PWMOut(board.GP2, duty_cycle=0, frequency=50)
motor1 = servo.Servo(escOut, min_pulse=1000, max_pulse=2000)
motor1.angle = 0

trig1Pin = DigitalInOut(board.GP16)
trig1Pin.switch_to_input(Pull.UP)
trigger1 = Debouncer(trig1Pin)

escSpeedPin = AnalogIn(board.GP26)
escSpeed = 0

while True:
    trigger1.update()
    if not trigger1.value:
        escSpeed = getAngle(escSpeedPin)
        motor1.angle = escSpeed
    escSpeed = 0
    motor1.angle = escSpeed
    