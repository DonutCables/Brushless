import board
from time import sleep, monotonic
from gc import collect
from hardware import DISPLAY, MOTOR1, MOTOR2, ENCODER, ENC, UP, DOWN, DTRIG, RTRIG, DFSWITCH, DBSWITCH, RELAYH, RELAYL

## Control initializations
# Encoder values
position = ENCODER.position
last_position = position
# Parameters each with multiple options that can be selected
IDLE_SPEED = [-1, -.9, -.8]
BURST = ["Auto", 3, 5, 15]
REV_SPEED = [0, .3, .6, .9]
# Using list indexes to select which option list to display and scroll
# Change initial index values to adjust default parameters
idle_index = 0
burst_index = 0
rev_index = 0
# Using a single index to scroll three lists for parameter display string, index, and value
# All must have the same length
INDEXED_OPTIONS = [IDLE_SPEED, BURST, REV_SPEED]
MENU_INDEXES = [idle_index, burst_index, rev_index]
MENU_ITEMS = ["Idle Speed", "Burst", "Rev Speed"]
master_index = 0

## Setting default ESC speeds
escIdle = -1
escZero = -1
escMin = -.9
escMax = 1

## Core functions
# Options menu, scrolling occurs by incrementing/decrementing the main index, then using that to inc/dec the index of each option
def menu():
    """Presents a menu of options and scrolling/selection functionality"""
    sleep(.5)
    global master_index, position, last_position
    # Names the optionset using main index, then option inside of the set using per-optionset index
    # print() will be replaced with display output functions later
    print(f"{MENU_ITEMS[master_index]} = {INDEXED_OPTIONS[master_index][MENU_INDEXES[master_index]]}")
    while ENC.value:
        position = ENCODER.position
        # If down button is pressed, move down the parameter list
        if not DOWN.value:
            sleep(.1)
            master_index += 1
            if master_index == len(MENU_INDEXES):
                master_index = 0
            print(f"{MENU_ITEMS[master_index]} = {INDEXED_OPTIONS[master_index][MENU_INDEXES[master_index]]}")
        # If up button is pressed, move up the parameter list
        elif not UP.value:
            sleep(.1)
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
    print("leaving")
    sleep(.5)

# Idling loop
def idle_loop():
    """Sets wheels to idle speed and allows entering menu for settings or proceeding to revving loop"""
    collect()
    print("idle speed", monotonic())
    escIdle = IDLE_SPEED[idle_index]
    MOTOR1.throttle, MOTOR2.throttle = escIdle, escIdle
    while not RTRIG.value:
        if not ENC.value:
            print("enc")
            sleep(.5)
            menu()
    print("revving now", monotonic())
    revving_loop()

# Revving loop, sets wheels to revving speed then handles trigger presses
def revving_loop():
    escSpeed = REV_SPEED[rev_index]
    MOTOR1.throttle, MOTOR2.throttle = escSpeed, escSpeed
    print("rev speed set", monotonic())
    while RTRIG.value:
        DTRIG.update()
        pulse = BURST[burst_index]
        if DTRIG.fell:
            print("trigger pressed")
            DFSWITCH.update()
            DBSWITCH.update()
            if pulse == "Auto":
                while DTRIG.value:
                    DFSWITCH.update()
                    DBSWITCH.update()
                    if not DBSWITCH.value:
                        RELAYL.value, RELAYH.value = True, True
                    if DBSWITCH.fell:
                        RELAYL.value, RELAYH.value = True, True
                        print("on", monotonic())
                    if DFSWITCH.fell:
                        RELAYL.value, RELAYH.value = False, False
                        print("off", monotonic())
            else:
                while isinstance(pulse, int) and pulse > 0:
                    DFSWITCH.update()
                    DBSWITCH.update()
                    if not DBSWITCH.value:
                        RELAYL.value, RELAYH.value = True, True
                    if DBSWITCH.fell:
                        RELAYL.value, RELAYH.value = True, True
                        print("on", monotonic())
                    if DFSWITCH.fell:
                        RELAYL.value, RELAYH.value = False, False
                        pulse -= 1
                        print("off", monotonic())
        RELAYL.value, RELAYH.value = False, False
    print("stopped revving")
    idle_loop()

## ESC arm sequence
def esc_arm():
    sleep(.5)
    MOTOR1.throttle = escZero
    MOTOR1.throttle = escMax
    MOTOR1.throttle = escMin
    sleep(3)
    MOTOR1.throttle = escZero
    sleep(1)
    print("ESC armed")
    sleep(1)

esc_arm()

if __name__ == "__main__":
    idle_loop()
