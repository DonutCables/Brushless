"""
Imports
"""
# region
from time import sleep as tsleep
from gc import enable
from asyncio import sleep, create_task, gather, run
from hardware import (
    MOTOR_EDF,
    MOTOR_AG,
    FTRIGB,
    ATRIGB,
)


# endregion
"""
Primary functions
"""
# region


async def button_monitor():
    """Aync function to monitor buttons"""
    while True:
        FTRIGB.update()
        ATRIGB.update()
        await sleep(0)


async def main_loop():
    """Sets motors to off and waits for triggers"""
    print("Idle start")
    MOTOR_EDF.throttle = -1  # 0% power, Adjust to 0 if the ESC is bidirectional
    MOTOR_AG.value = True  # Release relay, May need to be False
    while True:
        if FTRIGB.pressed:
            MOTOR_EDF.throttle = 0  # 50% power, 0.5 if the ESC is bidirectional
            print("Fan on")
        if FTRIGB.released:
            MOTOR_EDF.throttle = -1  # 0% power, 0 if the ESC is bidirectional
            print("Fan off")
        if ATRIGB.pressed:
            MOTOR_AG.value = False  # Trigger relay, May need to be True
            print("Agitator on")
        if ATRIGB.released:
            MOTOR_AG.value = True  # Release relay, May need to be False
            print("Agitator off")
        await sleep(0)


# endregion
"""
Loop setup
"""
# region


def esc_arm():
    """Arms the ESC by setting throttle to off for 4 seconds
    This sequence works for the AM32 ESC I use but I haven't tried it with BL32
    so it might just not arm it
    """
    tsleep(0.1)
    MOTOR_EDF.throttle = -1  # 0% power, Might need to be 0 if the ESC is bidirectional
    tsleep(4)
    print("ESC armed")


enable()  # Enable garbage collection

esc_arm()  # Run arm function


async def main():
    """Creates main asynchronous tasks"""
    main_task = create_task(main_loop())
    button_task = create_task(button_monitor())
    await gather(main_task, button_task)


if __name__ == "__main__":
    run(main())
# endregion
