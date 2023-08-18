import board
from digitalio import DigitalInOut, Pull, DriveMode
from time import monotonic
from adafruit_debouncer import Debouncer

pins = (board.GP22, board.GP2, board.GP3, board.GP7, board.GP8)

SWITCH, FSWITCH, BSWITCH, RELAYH, RELAYL = (DigitalInOut(pin) for pin in pins)
for switch in [SWITCH, FSWITCH, BSWITCH]:
    switch.switch_to_input(Pull.UP)
DFSWITCH = Debouncer(FSWITCH)
DBSWITCH = Debouncer(BSWITCH)
for relay in [RELAYH, RELAYL]:
    relay.switch_to_output(False, DriveMode.PUSH_PULL)

pulse_count = 15

while True:
    pulse_index = pulse_count
    while not SWITCH.value:
        RELAYH.value = True
        while pulse_index > 0:
            DFSWITCH.update()
            DBSWITCH.update()
            if not BSWITCH.value:
                RELAYL.value = True
            if DBSWITCH.fell:
                RELAYL.value = True
                print("on", monotonic())
            if DFSWITCH.fell:
                RELAYL.value = False
                print("off", monotonic())
                pulse_index -= 1
    RELAYH.value, RELAYL.value = False, False
