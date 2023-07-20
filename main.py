import board
import time
from hardware import DISPLAY, MOTOR1, ENCODER, ENC, UP, DOWN, TRIG, RTRIG

## Control initializations
# Encoder values
position = ENCODER.position
last_position = position
# Parameters each with multiple options that can be selected
IDLE_SPEED = [-1, -.9, -.8]
TEST1 = [-3, 0]
TEST2 = [-2, .5, 2, 4]
# Using list indexes to select which option list to display and scroll
idle_index = 0
test1_index = 0
test2_index = 0
# Using a single index to scroll three lists for parameter display string, index, and value
# All must have the same length
INDEXED_OPTIONS = [IDLE_SPEED, TEST1, TEST2]
MENU_INDEXES = [idle_index, test1_index, test2_index]
MENU_ITEMS = ["Idle Speed", "Test 1", "Test 2"]
master_index = 0

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
    global master_index, position, last_position
    # Names the optionset using main index, then option inside of the set using per-optionset index
    # print() will be replaced with display output functions later
    print(f"{MENU_ITEMS[master_index]} = {INDEXED_OPTIONS[master_index][MENU_INDEXES[master_index]]}")
    while True:
        position = ENCODER.position
        # If down button is pressed, move down the parameter list
        if not DOWN.value:
            time.sleep(.1)
            master_index += 1
            if master_index == len(MENU_INDEXES):
                master_index = 0
            print(f"{MENU_ITEMS[master_index]} = {INDEXED_OPTIONS[master_index][MENU_INDEXES[master_index]]}")
        # If up button is pressed, move up the parameter list
        elif not UP.value:
            time.sleep(.1)
            master_index -= 1                
            if master_index < 0:
                master_index = len(MENU_INDEXES) - 1
            print(f"{MENU_ITEMS[master_index]} = {INDEXED_OPTIONS[master_index][MENU_INDEXES[master_index]]}")
        if position != last_position:
            # If encoder spins right/down, cycle right/down in the indexed parameter values
            if position > last_position:
                MENU_INDEXES[master_index] += 1
                if MENU_INDEXES[master_index] == len(INDEXED_OPTIONS[master_index]):
                    MENU_INDEXES[master_index] = 0
            # If encoder spins left/up, cycle left/up in the indexed parameter values
            elif position < last_position:
                MENU_INDEXES[master_index] -= 1
                if MENU_INDEXES[master_index] < 0:
                    MENU_INDEXES[master_index] = len(INDEXED_OPTIONS[master_index]) - 1
            print(f"{MENU_ITEMS[master_index]} = {INDEXED_OPTIONS[master_index][MENU_INDEXES[master_index]]}")
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
    escIdle = IDLE_SPEED[idle_index]
    MOTOR1.throttle = escIdle
    while RTRIG.value:
        MOTOR1.throttle = escVar / 100
        print("revving")
        if not TRIG.value:
            print("put firing code here")
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
