import board
from digitalio import DigitalInOut, Pull, DriveMode
from busio import I2C
from pwmio import PWMOut
from adafruit_debouncer import Button
from displayio import I2CDisplay, release_displays
from adafruit_displayio_ssd1306 import SSD1306
from adafruit_motor import servo
from rotaryio import IncrementalEncoder
from touchio import TouchIn


## I2C assignments
release_displays()
i2c = I2C(board.GP21, board.GP20)
oled_interface = I2CDisplay(i2c, device_address=0x3C)
DISPLAY = SSD1306(oled_interface, width=128, height=64)

## ESC output creation
# Outputs in 2ms PWM standard
esc1Out = PWMOut(board.GP0, frequency=100)
esc4Out = PWMOut(board.GP1, frequency=100)
# Flywheels as a single output signal
MOTORS = servo.ContinuousServo(esc1Out, min_pulse=1000, max_pulse=2000)
# Solenoid as a brushed "motor"
NOID = servo.ContinuousServo(esc4Out, min_pulse=1000, max_pulse=2000)

## Initialize all switches
RTRIG = DigitalInOut(board.GP22)
DTRIG = DigitalInOut(board.GP26)
SEMI = DigitalInOut(board.GP7)
BURST = DigitalInOut(board.GP8)

for button in (RTRIG, DTRIG, SEMI, BURST):
    button.switch_to_input(Pull.UP)

RTRIGB = Button(RTRIG)
DTRIGB = Button(DTRIG)
SEMIB = Button(SEMI)
BURSTB = Button(BURST)

## Encoder inits

ENCODER = IncrementalEncoder(board.GP11, board.GP12)
ENC = DigitalInOut(board.GP13)
UP = DigitalInOut(board.GP14)
LEFT = DigitalInOut(board.GP15)
DOWN = DigitalInOut(board.GP16)
RIGHT = DigitalInOut(board.GP17)

for button in (ENC, UP, LEFT, DOWN, RIGHT):
    button.switch_to_input(Pull.UP)

ENCB = Button(ENC, long_duration_ms=2000)
UPB = Button(UP)
LEFTB = Button(LEFT)
DOWNB = Button(DOWN)
RIGHTB = Button(RIGHT)

