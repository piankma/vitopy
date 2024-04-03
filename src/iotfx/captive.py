from microdot import Microdot

from iotfx.logging import Logging
from iotfx.networking import Networking
from iotfx.threaded import reboot

captive_app = Microdot()
log = Logging("API_C")
nm = Networking()


@captive_app.route("/api/v1/status")
async def status(request):
    return await nm.station_info


@captive_app.route("/api/v1/scan")
async def scan(request):
    return await nm.scan()


@captive_app.route("/api/v1/store", methods=["POST"])
async def store(request):
    data = request.json
    if any([
        "ssid" not in data,
        "password" not in data,
        not isinstance(data["ssid"], str),
        not isinstance(data["password"], str),
        not 1 < len(data["ssid"]) < 32,
        not 1 < len(data["password"]) < 64
    ]):
        return {"code": "POST_INVALID"}, 400

    result, reason = await nm.sta_connect(data["ssid"], data["password"])
    if not result:
        return {"code": f"WLAN_CONNECT_{reason}"}, 400
    else:
        reboot(10)
        await nm.set_wifi_credentials(data["ssid"], data["password"])
        return {"connected": True}
