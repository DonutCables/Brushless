import board
import time
from hardware import DISPLAY, MOTOR1, ENCODER, ENC, UP, DOWN, RTRIG

## Control initializations
# Encoder values
position = ENCODER.position
last_position = position
# Menus
menu_option_index = 0
MENU_OPTIONS = ["Idle Speed", ]

## Setting default ESC speeds
escSpeed = -1
escIdle = -1
escVar = -100
escZero = -1
escMin = -.85
escMax = 1

## Core functions
# Options menu
def menu():
    global main_menu_option_index, position, last_position
    while True:
        position = ENCODER.position
        if position != last_position:
            if position > last_position:
                print("down")
            elif position < last_position:
                print("up")
            last_position = position


## ESC arm sequence
time.sleep(.5)
MOTOR1.throttle = escZero
MOTOR1.throttle = escMax
MOTOR1.throttle = escMin
time.sleep(3)
MOTOR1.throttle = escZero
time.sleep(2)

while True:
    position = ENCODER.position
    if not RTRIG.value:
        MOTOR1.throttle = escVar / 100
    else:
        MOTOR1.throttle = escIdle
    if position != last_position:
        if position > last_position and escVar < 100:
            escVar += 1
            print(escVar)
        elif position < last_position and escVar > -100:
            escVar -= 1
            print(escVar)
        last_position = position
    if not ENC.value:
        menu()
