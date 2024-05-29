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
    MOTORS,
    NOID,
    DTRIGB,
    DTRIG,
    RTRIGB,
    SEMIB,
    SEMI,
    BURSTB,
    BURST,
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
        escCapLow=44,
        escCapMid=59,
        escCapHigh=74,
        escNoidLow=5,
        escNoidHigh=95,
        extendTimeMS=20,
        retractTimeMS=35,
        burstCount=5,
        burstDelayMS=0,
        spoolDown=0,
    ):
        self.mIndex = 0
        self.escZero = 0
        self.escMin = 5
        self.escMid = 50
        self.escMax = 95
        self.noidPolarity = False
        self.mode = None
        self.escIdle = escIdle
        self.escRev = escRev
        self.escCapLow = escCapLow
        self.escCapMid = escCapMid
        self.escCapHigh = escCapHigh
        self.escNoidLow = escNoidLow
        self.escNoidHigh = escNoidHigh
        self.extendTimeMS = extendTimeMS
        self.retractTimeMS = retractTimeMS
        self.burstCount = burstCount
        self.burstDelayMS = burstDelayMS
        self.spoolDown = spoolDown
        self.optNames = [
            "escIdle",
            "escRev",
            "escCapLow",
            "escCapMid",
            "escCapHigh",
            "escNoidLow",
            "escNoidHigh",
            "extendTimeMS",
            "retractTimeMS",
            "burstCount",
            "burstDelayMS",
            "spoolDown",
        ]

    def gettr(self):
        return getattr(self, self.optNames[self.mIndex])

    def menu_print(self):
        """Prints menu options"""
        print(
            f"{self.optNames[self.mIndex]} = {getattr(self, self.optNames[self.mIndex])}"
        )

    def motors_throttle(self, throttle):
        """Sets motors to throttle value"""
        set_throttle = max(min(1.0, ((throttle / 50) - 1)), -1.0)
        MOTORS.throttle = set_throttle

    def motors_idle(self):
        """Sets motors to idle speed"""
        self.motors_throttle(self.escIdle)

    def motors_rev(self):
        """Sets motors to rev speed"""
        self.motors_throttle(self.escRev)

    def noid_throttle(self, throttle):
        """Sets solenoid throttle"""
        set_throttle = max(min(1.0, ((throttle / 50) - 1)), -1.0)
        NOID.throttle = set_throttle

    def noid_trigger(self):
        """Sets solenoid to trigger"""
        if self.noidPolarity:
            self.noid_throttle(self.escNoidHigh)
        elif not self.noidPolarity:
            self.noid_throttle(self.escNoidLow)

    def noid_release(self):
        """Sets solenoid to release"""
        self.noid_throttle(self.escMid)

    def noid_trigger_release(self):
        """Sets solenoid to trigger then release"""
        self.noid_trigger()
        tsleep(self.extendTimeMS / 1000)
        self.noid_release()
        tsleep(self.retractTimeMS / 1000)
        self.noidPolarity ^= True


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
        "12h", nvm[0:24]
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
    modetime1 = monotonic() - 2
    modetime2 = monotonic() - 2
    while True:
        if SEMIB.pressed:
            if monotonic() - modetime2 < 2:
                BStates.mode = "binary"
            else:
                BStates.mode = "semi"
                modetime2 = monotonic()
            print(BStates.mode)
        if BURSTB.pressed:
            if monotonic() - modetime1 < 2:
                BStates.mode = "auto"
            else:
                BStates.mode = "burst"
                modetime1 = monotonic()
            print(BStates.mode)
        if RTRIGB.pressed:
            await revving_loop()
            if BStates.spoolDown == 0:
                BStates.motors_idle()
            elif BStates.spoolDown > 1:
                spoolspd = BStates.escRev
            BStates.noid_throttle(BStates.escMid)
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
    burst_count = BStates.burstCount
    BStates.motors_rev()
    while True:
        if DTRIGB.pressed:
            if BStates.mode == "semi" or BStates.mode == "binary":
                BStates.noid_trigger_release()
            elif BStates.mode == "burst":
                for _ in range(burst_count):
                    BStates.noid_trigger_release()
                    tsleep(BStates.burstDelayMS / 1000)
                burst_count = BStates.burstCount
            elif BStates.mode == "auto":
                while not DTRIG.value:
                    BStates.noid_trigger_release()
                    tsleep(BStates.burstDelayMS / 1000)
            await sleep(0)
        if DTRIGB.released and BStates.mode == "binary":
            BStates.noid_trigger_release()
        if RTRIGB.value:
            break
        await sleep(0)


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
                nvm[0:24] = pack(
                    "12h",  # h = short, 2 bytes each. i = int, 4 bytes each
                    BStates.escIdle,
                    BStates.escRev,
                    BStates.escCapLow,
                    BStates.escCapMid,
                    BStates.escCapHigh,
                    BStates.escNoidLow,
                    BStates.escNoidHigh,
                    BStates.extendTimeMS,
                    BStates.retractTimeMS,
                    BStates.burstCount,
                    BStates.burstDelayMS,
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
    BStates.motors_throttle(BStates.escMax)
    BStates.motors_throttle(BStates.escMin)
    tsleep(3)
    BStates.motors_throttle(BStates.escZero)
    print("ESC armed")


def starting_values():
    if not SEMI.value:
        setattr(BStates, "escRev", BStates.escCapMid)
    elif not BURST.value:
        setattr(BStates, "escRev", BStates.escCapHigh)
    else:
        setattr(BStates, "escRev", BStates.escCapLow)


#starting_values()

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
