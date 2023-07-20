import board
from busio import I2C
from rotaryio import IncrementalEncoder
from digitalio import DigitalInOut, Pull
from touchio import TouchIn
from pwmio import PWMOut
from adafruit_motor import servo
from displayio import I2CDisplay, release_displays
from adafruit_displayio_ssd1306 import SSD1306

## I2C display assignments
release_displays()
oled_I2C = I2C(board.GP11, board.GP10)
oled_interface = I2CDisplay(oled_I2C, device_address=0x3c)
DISPLAY = SSD1306(oled_interface, width=128, height=64)

## ESC output creation
escOut = PWMOut(board.GP0, frequency=50)
MOTOR1 = servo.ContinuousServo(escOut, min_pulse=1000, max_pulse=2000)

## Initialize all io
# Add all pin assignments to a tuple in the order of io assignment
iopins = (board.GP2, board.GP3, board.GP4, board.GP5, board.GP6, board.GP21, board.GP26)
# Encoder rotation from the first two pins
ENCODER = IncrementalEncoder(iopins[0], iopins[1])
# Encoder press along with all other inputs
ENC, UP, DOWN, TRIG = (DigitalInOut(pin) for pin in iopins[2:6])
for button in (ENC, UP, DOWN, TRIG):
    button.switch_to_input(Pull.UP)

RTRIG = TouchIn(iopins[-1])
