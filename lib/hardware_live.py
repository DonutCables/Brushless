import board
from digitalio import DigitalInOut, Pull, DriveMode
from pwmio import PWMOut
from adafruit_debouncer import Button
from displayio import I2CDisplay, release_displays
from adafruit_displayio_ssd1306 import SSD1306
from adafruit_seesaw import seesaw, rotaryio, digitalio
from adafruit_motor import servo


## I2C assignments
release_displays()
try:
    i2c = board.STEMMA_I2C()
    seesaw = seesaw.Seesaw(i2c, addr=0x49)
except RuntimeError:
    pass
try:
    oled_interface = I2CDisplay(i2c, device_address=0x3c)
    DISPLAY = SSD1306(oled_interface, width=128, height=64)
except Exception as e:
    print(e)
    pass

## ESC output creation
esc1Out = PWMOut(board.D0, frequency=50)
esc2Out = PWMOut(board.D1, frequency=50)
MOTOR1 = servo.ContinuousServo(esc1Out, min_pulse=1000, max_pulse=2000)
MOTOR2 = servo.ContinuousServo(esc2Out, min_pulse=1000, max_pulse=2000)

## Initialize all switches
RTRIG = DigitalInOut(board.D3)
DTRIG = DigitalInOut(board.D4)
SEMI = DigitalInOut(board.D5)
BURST = DigitalInOut(board.D6)

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

    ENCB = Button(ENC)
    UPB = Button(UP)
    LEFTB = Button(LEFT)
    DOWNB = Button(DOWN)
    RIGHTB = Button(RIGHT)
except:
    pass

## IO for controlling solenoid cycling
RELAY1 = DigitalInOut(board.D9)
RELAY2 = DigitalInOut(board.D10)
for relay in [RELAY1, RELAY2]:
    relay.switch_to_output(True, DriveMode.PUSH_PULL)
