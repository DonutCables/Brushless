import board
from busio import I2C
from rotaryio import IncrementalEncoder
from digitalio import DigitalInOut, Pull, DriveMode
from touchio import TouchIn
from pwmio import PWMOut
from adafruit_motor import servo
from displayio import I2CDisplay, release_displays
from adafruit_displayio_ssd1306 import SSD1306
from adafruit_debouncer import Debouncer

## I2C display assignments
release_displays()
oled_I2C = I2C(board.GP21, board.GP20)
oled_interface = I2CDisplay(oled_I2C, device_address=0x3c)
DISPLAY = SSD1306(oled_interface, width=128, height=64)

## ESC output creation
esc1Out = PWMOut(board.GP0, frequency=50)
esc2Out = PWMOut(board.GP1, frequency=50)
MOTOR1 = servo.ContinuousServo(esc1Out, min_pulse=1000, max_pulse=2000)
MOTOR2 = servo.ContinuousServo(esc2Out, min_pulse=1000, max_pulse=2000)

## Initialize all io
# Add all pin assignments to a tuple in the order of io assignment
iopins = (board.GP11, board.GP12, board.GP13, board.GP14, board.GP15, board.GP22, board.GP26)
# Encoder rotation from the first two pins
ENCODER = IncrementalEncoder(iopins[0], iopins[1])
# Encoder press along with all other inputs
ENC, UP, DOWN, TRIG = (DigitalInOut(pin) for pin in iopins[2:6])
for button in (ENC, UP, DOWN, TRIG):
    button.switch_to_input(Pull.UP)
# Debouncing firing trigger
DTRIG = Debouncer(TRIG)
# Cap touch for rev trigger
RTRIG = TouchIn(iopins[-1])

# IO for controlling solenoid cycling
solpins = (board.GP2, board.GP3, board.GP7, board.GP8)
FSWITCH, BSWITCH, RELAYH, RELAYL = (DigitalInOut(pin) for pin in solpins)
for switch in [FSWITCH, BSWITCH]:
    switch.switch_to_input(Pull.UP)
DFSWITCH = Debouncer(FSWITCH)
DBSWITCH = Debouncer(BSWITCH)
for relay in [RELAYH, RELAYL]:
    relay.switch_to_output(False, DriveMode.PUSH_PULL)
