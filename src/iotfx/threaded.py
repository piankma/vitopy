import machine
import _thread as threading
import time
from iotfx.logging import Logging

log = Logging("UTIL")


def reboot(time_seconds: int):
    """
    Reboot the device after a specified amount of time.
    Creates a new thread to not block the main one.

    Args:
        time_seconds (int): The amount of time in seconds to wait before rebooting.
    """
    def _reboot_thr():
        log.info(f"Rebooting in {time_seconds} seconds.")
        time.sleep(time_seconds)
        log.info("Rebooting NOW!")
        machine.reset()

    threading.start_new_thread(_reboot_thr, (time_seconds,))
