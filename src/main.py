import asyncio
import gc

from iotfx.captive import captive_app
from iotfx.logging import Logging
from iotfx.networking import Networking
from iotfx.status_led import StatusLed

nm = Networking()
led = StatusLed(23)
log = Logging("MAIN")


async def start_captive():
    await nm.ap_start()
    captive_app.run(port=80)


async def start():
    try:
        wifi_ssid, wifi_pass = await nm.get_wifi_credentials()
    except ValueError:
        log.info("No WiFi credentials found, starting captive portal.")
        await start_captive()



if __name__ == "__main__":
    gc.collect()
    loop = asyncio.run(start())
