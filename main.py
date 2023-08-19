from time import sleep, monotonic
from gc import enable, collect, mem_free
from hardware import DISPLAY, MOTOR1, MOTOR2, ENCODER, ENC, UP, DOWN, DTRIG, RTRIG, DFSWITCH, DBSWITCH, RELAYH, RELAYL

## Control initializations
# Encoder values
position = ENCODER.position
last_position = position

# List of dicts that each define an option and its parameters
OPTIONS = [
    {"name": "Idle Speed", "options": [-1, -.9, -.8], "index": 0},
    {"name": "Burst", "options": ["Auto", 3, 5, 15], "index": 0},
    {"name": "Rev Speed", "options": [0, .3, .6, .9], "index": 0},
]

## Setting default ESC speeds
escIdle = -1
escZero = -1
escMin = -.9
escMax = 1

## Core functions
# Options menu, uses the OPTIONS list of dicts to change options as you view them
def menu():
    """Presents a menu of options and scrolling/selection functionality"""
    sleep(.5)
    global position, last_position
    option_count = len(OPTIONS)
    current_option = 0
    current = OPTIONS[current_option]
    print(f"{current['name']} = {current['options'][current['index']]}")
    while ENC.value:
        position = ENCODER.position
        if not DOWN.value or not UP.value:
            # If down button is pressed, move down the parameter list
            if not DOWN.value:
                sleep(.2)
                current_option = (current_option + 1) % option_count
            # If up button is pressed, move up the parameter list
            elif not UP.value:
                sleep(.2)
                current_option = (current_option - 1) % option_count
            current = OPTIONS[current_option]
            print(f"{current['name']} = {current['options'][current['index']]}")
        if position != last_position:
            if position > last_position:
                current['index'] = (current['index'] + 1) % len(current['options'])
            elif position < last_position:
                current['index'] = (current['index'] - 1) % len(current['options'])
            current = OPTIONS[current_option]
            print(f"{current['name']} = {current['options'][current['index']]}")
            last_position = position
    print("leaving")
    sleep(.5)

# Idling loop, allows going to menu() to change settings but leaves the loop during revving
def idle_loop():
    """Sets wheels to idle speed and allows entering menu for settings or proceeding to revving loop"""
    print("idle speed", monotonic())
    escIdle = OPTIONS[0]["options"][OPTIONS[0]["index"]]
    print(escIdle)
    MOTOR1.throttle, MOTOR2.throttle = escIdle, escIdle
    while not RTRIG.value:
        if not ENC.value:
            print("enc")
            sleep(.5)
            menu()
            escIdle = OPTIONS[0]["options"][OPTIONS[0]["index"]]
            print(escIdle)
            MOTOR1.throttle, MOTOR2.throttle = escIdle, escIdle
    print("revving now", monotonic())
    revving_loop()

# Revving loop
def revving_loop():
    """Sets wheels to revving speed then handles trigger presses"""
    escSpeed = OPTIONS[2]["options"][OPTIONS[2]["index"]]
    print(escSpeed)
    MOTOR1.throttle, MOTOR2.throttle = escSpeed, escSpeed
    print("rev speed set", monotonic())
    while RTRIG.value:
        DTRIG.update()
        pulse = OPTIONS[1]["options"][OPTIONS[1]["index"]]
        if DTRIG.fell:
            print("trigger pressed")
            DFSWITCH.update()
            DBSWITCH.update()
            if pulse == "Auto":
                print("auto")
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
                print(pulse)
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
    MOTOR1.throttle, MOTOR2.throttle = escZero, escZero
    MOTOR1.throttle, MOTOR2.throttle = escMax, escMax
    MOTOR1.throttle, MOTOR2.throttle = escMin, escMin
    sleep(3)
    MOTOR1.throttle, MOTOR2.throttle = escZero, escZero
    sleep(1)
    print("ESC armed")
    sleep(1)

esc_arm()

enable()

if __name__ == "__main__":
    idle_loop()
