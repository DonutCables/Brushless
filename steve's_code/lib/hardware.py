import board
from digitalio import DigitalInOut, Pull, DriveMode
from pwmio import PWMOut
from adafruit_debouncer import Button
from adafruit_motor import servo


## ESC output creation
# 50hz PWM frequency for ESC
escOut = PWMOut(board.D0, frequency=50)  # Pin 0 for ESC signal
# Creates a continuous servo object for the ESC
MOTOR_EDF = servo.ContinuousServo(escOut, min_pulse=1000, max_pulse=2000)

## Brushed motor output creation
MOTOR_AG = DigitalInOut(board.D1)  # Pin 1 for relay signal
# Sets a digital output for the brushed motor relay
# May need to use value=False here depending on relay
MOTOR_AG.switch_to_output(value=True, drive_mode=DriveMode.PUSH_PULL)

## Initialize all switches
# Switches trigger when pulled to ground
FTRIG = DigitalInOut(board.D2)  # Pin 2 for the fan trigger
FTRIG.switch_to_input(Pull.UP)
ATRIG = DigitalInOut(board.D3)  # Pin 3 for the agitator trigger
ATRIG.switch_to_input(Pull.UP)

# Software debouncing and fancier functions for triggers
FTRIGB = Button(FTRIG)
ATRIGB = Button(ATRIG)
