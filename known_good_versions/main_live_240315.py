"""
Imports
"""
# region
from struct import pack, unpack
from microcontroller import nvm
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
    DISPLAY,
)

if DISPLAY == None:
    no_encoder = True
else:
    no_encoder = False
    from hardware import (
        ENCODER,
        ENCB,
        UPB,
        LEFTB,
        DOWNB,
        RIGHTB,
    )

# endregion
"""
State initializations and core background functions
"""
# region


class BlasterStates:
    """Manages blaster states"""

    def __init__(
        self,
        escIdle=0,
        escRev=25,
        extendTimeMS=20,
        retractTimeMS=35,
        burstCount=5,
        spoolDown=0,
    ):
        self.mIndex = 0
        self.escZero = 0
        self.escMin = 5
        self.escMax = 95
        self.escIdle = escIdle
        self.escRev = escRev
        self.extendTimeMS = extendTimeMS
        self.retractTimeMS = retractTimeMS
        self.burstCount = burstCount
        self.spoolDown = spoolDown
        self.optNames = [
            "escIdle",
            "escRev",
            "extendTimeMS",
            "retractTimeMS",
            "burstCount",
            "spoolDown",
        ]

    def gettr(self):
        return getattr(self, self.optNames[self.mIndex])

    def menu_print(self):
        """Prints menu options"""
        print(
            f"{self.optNames[self.mIndex]} = {getattr(self, self.optNames[self.mIndex])}"
        )

    def motors_idle(self):
        """Sets motors to idle speed"""
        idle_throttle = max(min(1.0, ((self.escIdle / 50) - 1)), -1.0)
        MOTOR1.throttle = MOTOR2.throttle = idle_throttle

    def motors_rev(self):
        """Sets motors to rev speed"""
        rev_throttle = max(min(1.0, ((self.escRev / 50) - 1)), -1.0)
        MOTOR1.throttle = MOTOR2.throttle = rev_throttle

    def motors_throttle(self, throttle):
        """Sets motors to throttle value"""
        set_throttle = max(min(1.0, ((throttle / 50) - 1)), -1.0)
        MOTOR1.throttle = MOTOR2.throttle = set_throttle

    def relay_trigger(self):
        """Sets relay to trigger"""
        RELAY1.value = RELAY2.value = False

    def relay_release(self):
        """Sets relay to release"""
        RELAY1.value = RELAY2.value = True

    def relay_trigger_release(self):
        """Sets relay to trigger then release"""
        self.relay_trigger()
        tsleep(self.extendTimeMS / 1000)
        self.relay_release()
        tsleep(self.retractTimeMS / 1000)


class ENCStates:
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
            LEFTB.update()
            DOWNB.update()
            RIGHTB.update()
        DTRIGB.update()
        RTRIGB.update()
        SEMIB.update()
        BURSTB.update()
        await sleep(0)


## Load saved values from NVM
try:
    saved_values = unpack(
        "6h", nvm[0:12]
    )  # h = short, 2 bytes each. i = int, 4 bytes each
    print(saved_values)
except:
    saved_values = None
    print("Load failed")
    pass

## Initialize states
if saved_values is None:
    BStates = BlasterStates()
else:
    BStates = BlasterStates(*saved_values)
if not no_encoder:
    ENCS = ENCStates(ENCODER)

# endregion
"""
Primary functions
"""
# region


async def idle_loop():
    """Sets wheels to idle speed and allows entering menu for settings or proceeding to revving loop"""
    print("Idle start")
    BStates.motors_idle()
    spoolspd = BStates.escIdle
    spooltime = monotonic()
    while True:
        if SEMIB.pressed:
            print("Semi")
        if BURSTB.pressed:
            print("Burst")
        if RTRIGB.pressed:
            print("Enter rev loop")
            await revving_loop()
            if BStates.spoolDown == 0:
                print("no spooldown")
                BStates.motors_idle()
            elif BStates.spoolDown > 1:
                print(f"spooling down rate {BStates.spoolDown}")
                spoolspd = BStates.escRev
        if spoolspd > BStates.escIdle and monotonic() - spooltime > (
            BStates.spoolDown / 1000
        ):
            spooltime = monotonic()
            spoolspd -= 1
            BStates.motors_throttle(spoolspd)
        if not no_encoder:
            if ENCB.pressed:
                print("Enter menu")
                await menu()
                BStates.motors_idle()
        await sleep(0)


async def revving_loop():
    """Sets wheels to revving speed then handles trigger presses"""
    print("Revving now")
    burst_count = BStates.burstCount
    BStates.motors_rev()
    complete = 0
    while True:
        if DTRIGB.pressed:
            print("trigger pressed")
            if not SEMIB.value:
                BStates.relay_trigger_release()
                print("single fire")
            if not BURSTB.value:
                for _ in range(burst_count):
                    BStates.relay_trigger_release()
                    complete += 1
                    print("burst", complete)
                burst_count = BStates.burstCount
                complete = 0
            await sleep(0)
        if RTRIGB.value:
            break
        await sleep(0)
    print("Leaving revving")


async def menu():
    """Options Menu"""
    await sleep(0.5)
    BStates.menu_print()
    while True:
        if UPB.pressed:
            BStates.mIndex = (BStates.mIndex - 1) % len(BStates.optNames)
            BStates.menu_print()
        elif DOWNB.pressed:
            BStates.mIndex = (BStates.mIndex + 1) % len(BStates.optNames)
            BStates.menu_print()
        elif LEFTB.pressed:
            option = 0
            setattr(BStates, BStates.optNames[BStates.mIndex], option)
            BStates.menu_print()
        elif RIGHTB.pressed:
            if "esc" in BStates.optNames[BStates.mIndex]:
                option = 100
            else:
                option = 50
            setattr(BStates, BStates.optNames[BStates.mIndex], option)
            BStates.menu_print()
        if ENCS._was_rotated.is_set():
            if "esc" in BStates.optNames[BStates.mIndex]:
                option = ENCS.encoder_handler(BStates.gettr(), 1) % 101
            else:
                option = ENCS.encoder_handler(BStates.gettr(), 1) % 51
            setattr(BStates, BStates.optNames[BStates.mIndex], option)
            BStates.menu_print()
        if ENCB.short_count > 0:
            break
        if ENCB.long_press:
            print("Saving values to NVM")
            try:
                nvm[0:12] = pack(
                    "6h",  # h = short, 2 bytes each. i = int, 4 bytes each
                    BStates.escIdle,
                    BStates.escRev,
                    BStates.extendTimeMS,
                    BStates.retractTimeMS,
                    BStates.burstCount,
                    BStates.spoolDown,
                )
            except:
                print("NVM write failed")
                pass
            BStates.menu_print()
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
    tsleep(0.1)
    BStates.motors_throttle(BStates.escZero)
    tsleep(4)
    print("ESC armed")


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
