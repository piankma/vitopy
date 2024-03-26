import _thread as threading
import time

import machine
from microdot import Microdot

from iotfx.logging import Logging
from iotfx.networking import Networking

captive_app = Microdot()
log = Logging("CAPTIVE")
nm = Networking()


def _reset_in(seconds):
    log.info(f"Resetting in {seconds} seconds.")
    time.sleep(seconds)
    log.info("Resetting NOW!")
    machine.reset()


@captive_app.route("/api/v1/status")
async def status(request):
    return await nm.station_info


@captive_app.route("/api/v1/scan")
async def scan(request):
    return await nm.scan()


@captive_app.route("/api/v1/store", methods=["POST"])
async def store(request):
    data = request.json
    if "ssid" not in data or "password" not in data:
        return {"error_code": "POST_INVALID"}, 400

    result, reason = await nm.sta_connect(data["ssid"], data["password"])
    if not result:
        return {"error_code": f"WLAN_CONNECT_{reason}"}, 400
    else:
        threading.start_new_thread(_reset_in, (5,))
        await nm.set_wifi_credentials(data["ssid"], data["password"])
        return {"connected": True}
