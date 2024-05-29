import board
from digitalio import DigitalInOut, Pull, DriveMode
from busio import I2C
from pwmio import PWMOut
from adafruit_debouncer import Button
from displayio import I2CDisplay, release_displays
from adafruit_displayio_ssd1306 import SSD1306
from adafruit_seesaw import seesaw, rotaryio, digitalio
from adafruit_motor import servo


## I2C assignments
release_displays()
try:
    i2c = I2C(board.GP1, board.GP0)
    seesaw = seesaw.Seesaw(i2c, addr=0x49)
except RuntimeError:
    i2c = None
    pass
try:
    oled_interface = I2CDisplay(i2c, device_address=0x3C)
    DISPLAY = SSD1306(oled_interface, width=128, height=64)
except Exception:
    DISPLAY = None
    pass

## ESC output creation
# Outputs in 2ms PWM standard
esc1Out = PWMOut(board.GP2, frequency=100)
esc4Out = PWMOut(board.GP3, frequency=100)
# Flywheels as a single output signal
MOTORS = servo.ContinuousServo(esc1Out, min_pulse=1000, max_pulse=2000)
# Solenoid as a brushed "motor"
NOID = servo.ContinuousServo(esc4Out, min_pulse=1000, max_pulse=2000)

## Initialize all switches
RTRIG = DigitalInOut(board.GP4)
DTRIG = DigitalInOut(board.GP6)
SEMI = DigitalInOut(board.GP7)
BURST = DigitalInOut(board.GP8)

for button in (RTRIG, DTRIG, SEMI, BURST):
    button.switch_to_input(Pull.UP)

RTRIGB = Button(RTRIG)
DTRIGB = Button(DTRIG)
SEMIB = Button(SEMI)
BURSTB = Button(BURST)

## Encoder inits
try:
    seesaw.pin_mode(1, seesaw.INPUT_PULLUP)
    seesaw.pin_mode(2, seesaw.INPUT_PULLUP)
    seesaw.pin_mode(3, seesaw.INPUT_PULLUP)
    seesaw.pin_mode(4, seesaw.INPUT_PULLUP)
    seesaw.pin_mode(5, seesaw.INPUT_PULLUP)

    ENCODER = rotaryio.IncrementalEncoder(seesaw)
    ENC = digitalio.DigitalIO(seesaw, 1)
    UP = digitalio.DigitalIO(seesaw, 2)
    LEFT = digitalio.DigitalIO(seesaw, 3)
    DOWN = digitalio.DigitalIO(seesaw, 4)
    RIGHT = digitalio.DigitalIO(seesaw, 5)

    ENCB = Button(ENC, long_duration_ms=2000)
    UPB = Button(UP)
    LEFTB = Button(LEFT)
    DOWNB = Button(DOWN)
    RIGHTB = Button(RIGHT)
except:
    pass
