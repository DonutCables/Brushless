import board
import time
from hardware import DISPLAY, MOTOR1, ENCODER, ENC, UP, DOWN, RTRIG

## Control initializations
# Encoder values
position = ENCODER.position
last_position = position
# Adjustable options setup for adjustment via menu
IDLE_SPEED = [-1, -.9, -.8]
TEST1 = [-3, 0]
TEST2 = [-2, .5, 2, 4]
idle_index = 0
test1_index = 0
test2_index = 0
INDEXED_OPTIONS = [IDLE_SPEED, TEST1, TEST2]
MENU_INDEXES = [idle_index, test1_index, test2_index]
MENU_ITEMS = ["Idle Speed", "Test 1", "Test 2"]
menu_dex = 0

## Setting default ESC speeds
escIdle = -1
escVar = -100
escZero = -1
escMin = -.85
escMax = 1

## Core functions
# Options menu, scrolling occurs by incrementing/decrementing the main index, then using that to inc/dec the index of each option
def menu():
    """Presents a menu of options and scrolling/selection functionality"""
    time.sleep(.5)
    global menu_dex, idle_index, position, last_position
    # Names the optionset using main index, then option inside of the set using per-optionset index
    # print() will be replaced with display functions later
    print(f"{MENU_ITEMS[menu_dex]} = {INDEXED_OPTIONS[menu_dex][MENU_INDEXES[menu_dex]]}")
    while True:
        position = ENCODER.position
        # This part just handles down/up presses to cycle through the optionsets
        if not DOWN.value:
            time.sleep(.1)
            menu_dex += 1
            if menu_dex == len(MENU_INDEXES):
                menu_dex = 0
            print(f"{MENU_ITEMS[menu_dex]} = {INDEXED_OPTIONS[menu_dex][MENU_INDEXES[menu_dex]]}")
        elif not UP.value:
            time.sleep(.1)
            menu_dex -= 1                
            if menu_dex < 0:
                menu_dex = len(MENU_INDEXES) - 1
            print(f"{MENU_ITEMS[menu_dex]} = {INDEXED_OPTIONS[menu_dex][MENU_INDEXES[menu_dex]]}")
        # This is for encoder scrolling the options inside the optionsets
        if position != last_position:
            if position > last_position:
                MENU_INDEXES[menu_dex] += 1
                if MENU_INDEXES[menu_dex] == len(INDEXED_OPTIONS[menu_dex]):
                    MENU_INDEXES[menu_dex] = 0
                print(f"{MENU_ITEMS[menu_dex]} = {INDEXED_OPTIONS[menu_dex][MENU_INDEXES[menu_dex]]}")
            elif position < last_position:
                MENU_INDEXES[menu_dex] -= 1
                if MENU_INDEXES[menu_dex] < 0:
                    MENU_INDEXES[menu_dex] = len(INDEXED_OPTIONS[menu_dex]) - 1
                print(f"{MENU_ITEMS[menu_dex]} = {INDEXED_OPTIONS[menu_dex][MENU_INDEXES[menu_dex]]}")
            last_position = position
        # Exits via center press
        if not ENC.value:
            print("leaving")
            time.sleep(.5)
            break

## ESC arm sequence
def esc_arm():
    time.sleep(.5)
    MOTOR1.throttle = escZero
    MOTOR1.throttle = escMax
    MOTOR1.throttle = escMin
    time.sleep(3)
    MOTOR1.throttle = escZero
    time.sleep(1)
    print("ESC armed")
    time.sleep(1)

esc_arm()

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
        print("enc")
        menu()
