import asyncio

from machine import Pin

from iotfx.logging import Logging

log = Logging("LED")


class StatusLed:
    def __init__(self, pin):
        self.pin = pin
        self.led = Pin(pin, Pin.OUT)
        self.led.value(0)  # Turn off the LED first
        self._thread_name = f"t_led_{pin}"
        self._stop_blinking = False

    def on(self):
        self.led.value(1)

    def off(self):
        self.led.value(0)

    def toggle(self):
        self.led.value(not self.led.value())

    async def _blink(self, times=10, delay=0.5):
        for _ in range(times):
            if self._stop_blinking:
                break
            self.on()
            await asyncio.sleep(delay)
            self.off()
            await asyncio.sleep(delay)

    def blink_stop(self):
        self._stop_blinking = True

    async def blink(self, times=10, delay=0.5):
        log.info(f"Blinking {times}x every {delay}s on pin {self.pin}.")
        asyncio.get_event_loop().create_task(self._blink(times, delay))

    # async def blink_thread(self, times=10, delay=0.5):
    #     log.debug(f"Starting thread: {self._thread_name}")
    #     threading.start_new_thread(await self.blink, (times, delay))
