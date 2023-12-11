"""
Imports
"""
# region
from time import monotonic
from time import sleep as tsleep
from gc import enable, mem_free
from asyncio import sleep, create_task, gather, run, Event
from hardware import (
    MOTOR1,
    MOTOR2,
    DTRIGB,
    RTRIGB,
    SEMIB,
    BURSTB,
    RELAY1,
    RELAY2,
)

try:
    from hardware import DISPLAY
except:
    pass
no_encoder = False
try:
    from hardware import (
        ENCODER,
        ENCB,
        UPB,
        LEFTB,
        DOWNB,
        RIGHTB,
    )
except Exception:
    no_encoder = True
    pass
# endregion
"""
State initializations and core background functions
"""


# region
class Blaster_States:
    """Manages blaster states"""

    def __init__(self):
        self.menu_index = 0
        self.escZero = -1
        self.escMin = -0.95
        self.escMax = 1
        self.escIdle = -1
        self.escRev = -0.05
        self.burstCount = 8
        self.burstCap = 20
        self.optionNames = ["escIdle", "escRev", "burstCount"]

    def motors_idle(self):
        """Sets motors to idle speed"""
        MOTOR1.throttle, MOTOR2.throttle = self.escIdle, self.escIdle

    def motors_rev(self):
        """Sets motors to rev speed"""
        MOTOR1.throttle, MOTOR2.throttle = self.escRev, self.escRev

    def relay_trigger(self):
        """Sets relay to trigger"""
        RELAY1.value, RELAY2.value = False, False

    def relay_release(self):
        """Sets relay to release"""
        RELAY1.value, RELAY2.value = True, True

    def relay_trigger_release(self, time1=0.020, time2=0.035):
        """Sets relay to trigger then release"""
        self.relay_trigger()
        tsleep(time1)
        self.relay_release()
        tsleep(time2)


class ENC_States:
    """Manages encoder rotation"""

    def __init__(self, encoder):
        self.encoder = encoder
        self.last_position = self.encoder.position
        self._was_rotated = Event()

    async def update(self):
        """Updates the pressed state of the encoder"""
        while True:
            if (
                self.encoder.position != self.last_position
                and not self._was_rotated.is_set()
            ):
                self._was_rotated.set()
            await sleep(0)

    def encoder_handler(self, x, y):
        """Handles encoder rotation"""
        while True:
            if self.encoder.position > self.last_position:
                self.last_position = self.encoder.position
                self._was_rotated.clear()
                return x + y
            elif self.encoder.position < self.last_position:
                self.last_position = self.encoder.position
                self._was_rotated.clear()
                return x - y


async def button_monitor():
    """Aync function to monitor buttons"""
    while True:
        if not no_encoder:
            ENCB.update()
            UPB.update()
            DOWNB.update()
        DTRIGB.update()
        RTRIGB.update()
        SEMIB.update()
        BURSTB.update()
        await sleep(0)


BlasterS = Blaster_States()
if not no_encoder:
    ENCS = ENC_States(ENCODER)
# endregion
"""
Primary functions
"""


# region
async def idle_loop():
    """Sets wheels to idle speed and allows entering menu for settings or proceeding to revving loop"""
    print("Idle start")
    BlasterS.motors_idle()
    while True:
        if SEMIB.pressed:
            print("Semi")
        if BURSTB.pressed:
            print("Burst")
        if RTRIGB.pressed:
            print("Enter rev loop")
            await revving_loop()
            BlasterS.motors_idle()
        if not no_encoder:
            if ENCB.pressed:
                print("Enter menu")
                await menu()
                BlasterS.motors_idle()
        await sleep(0)


async def revving_loop():
    """Sets wheels to revving speed then handles trigger presses"""
    print("Revving now")
    burst_count = BlasterS.burstCount
    BlasterS.motors_rev()
    complete = 0
    while True:
        if DTRIGB.pressed:
            print("trigger pressed")
            if not SEMIB.value:
                BlasterS.relay_trigger_release()
                print("single fire")
            if not BURSTB.value:
                for _ in range(burst_count):
                    BlasterS.relay_trigger_release(0.02, 0.035)
                    complete += 1
                    print("burst", complete)
                burst_count = BlasterS.burstCount
                complete = 0
            await sleep(0)
        if RTRIGB.value:
            break
        await sleep(0)
    print("Leaving revving")


async def menu():
    """Options Menu"""
    await sleep(0.5)
    print(
        f"{BlasterS.optionNames[BlasterS.menu_index]} = {getattr(BlasterS, BlasterS.optionNames[BlasterS.menu_index])}"
    )
    while True:
        if UPB.pressed:
            BlasterS.menu_index = (BlasterS.menu_index - 1) % len(BlasterS.optionNames)
            print(
                f"{BlasterS.optionNames[BlasterS.menu_index]} = {getattr(BlasterS, BlasterS.optionNames[BlasterS.menu_index])}"
            )
        elif DOWNB.pressed:
            BlasterS.menu_index = (BlasterS.menu_index + 1) % len(BlasterS.optionNames)
            print(
                f"{BlasterS.optionNames[BlasterS.menu_index]} = {getattr(BlasterS, BlasterS.optionNames[BlasterS.menu_index])}"
            )
        if ENCS._was_rotated.is_set():
            if BlasterS.menu_index == 2:
                option = (
                    ENCS.encoder_handler(BlasterS.burstCount, 1) % BlasterS.burstCap
                )
            else:
                optionx100 = ENCS.encoder_handler(
                    getattr(BlasterS, BlasterS.optionNames[BlasterS.menu_index]) * 100,
                    1,
                )
                option = round(max(min(100, optionx100), -100) / 100, 2)
            setattr(BlasterS, BlasterS.optionNames[BlasterS.menu_index], option)
            print(
                f"{BlasterS.optionNames[BlasterS.menu_index]} = {getattr(BlasterS, BlasterS.optionNames[BlasterS.menu_index])}"
            )
        if ENCB.short_count > 0:
            break
        await sleep(0)
    print("Leaving menu")
    print(mem_free())
    await sleep(0.5)


# endregion
"""
Loop setup
"""
# region


def esc_arm():
    tsleep(0.25)
    MOTOR1.throttle, MOTOR2.throttle = BlasterS.escZero, BlasterS.escZero
    tsleep(0.2)
    MOTOR1.throttle, MOTOR2.throttle = BlasterS.escMax, BlasterS.escMax
    tsleep(0.2)
    MOTOR1.throttle, MOTOR2.throttle = BlasterS.escMin, BlasterS.escMin
    tsleep(3)
    MOTOR1.throttle, MOTOR2.throttle = BlasterS.escZero, BlasterS.escZero
    tsleep(1)
    print("ESC armed")
    tsleep(1)


enable()

esc_arm()


async def main():
    main_task = create_task(idle_loop())
    button_task = create_task(button_monitor())
    if not no_encoder:
        encoder_task = create_task(ENCS.update())
        await gather(main_task, button_task, encoder_task)
    else:
        await gather(main_task, button_task)


if __name__ == "__main__":
    run(main())
# endregion
