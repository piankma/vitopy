import asyncio
import machine
import network
import ntptime
import time
import project

from iotfx.config import Config
from iotfx.logging import Logging
from iotfx.singleton import singleton

cfg = Config("network")
log = Logging("NET")
log_ntp = Logging("NTP")

AUTH_MODE = {
    "0": "OPEN",
    "1": "WEP",
    "2": "WPA-PSK",
    "3": "WPA2-PSK",
    "4": "WPA/WPA2-PSK",
    "5": "WPA2-ENTERPRISE",
    "6": "WPA/WPA2-ENTERPRISE",
    "7": "WPA3-PSK",
    "8": "WPA2/WPA3-PSK",
    "9": "OWE",
    "10": "MAX",
}
WLAN_STATUS = {
    "200": "BEACON_TIMEOUT",
    "201": "NO_AP_FOUND",
    "202": "AUTH_FAIL",
    "203": "ASSOC_FAIL",
    "204": "HANDSHAKE_TIMEOUT",
    "1000": "IDLE",
    "1001": "CONNECTING",
    "1010": "GOT_IP",
}


@singleton
class Networking:
    def __init__(self) -> None:
        self._app_name = project.NAME
        self.wlan_sta = network.WLAN(network.STA_IF)
        self.wlan_ap = network.WLAN(network.AP_IF)

    @property
    async def station_info(self) -> dict:
        """
        Retrieves information about WiFi adapter and current connection.

        Returns:
            dict: The information about WiFi adapter and current connection
        """
        previous_state = self.wlan_sta.active()
        if previous_state is False:
            self.wlan_sta.active(True)

        if not self.wlan_sta.isconnected():
            return {
                "status": WLAN_STATUS[str(self.wlan_sta.status())],
                "is_connected": False,
            }

        try:
            return {
                "ssid": self.wlan_sta.config("ssid"),
                "channel": self.wlan_sta.config("channel"),
                "is_hidden": bool(self.wlan_sta.config("hidden")),
                "security": AUTH_MODE[str(self.wlan_sta.config("authmode"))],
                "key": self.wlan_sta.config("password"),
                "txpower": self.wlan_sta.config("txpower"),
            }
        except ValueError:
            pass

        if previous_state is False:
            self.wlan_sta.active(False)

        return {}

    @property
    def _default_ap_ssid(self):
        macaddr_short = self.wlan_ap.config("mac").hex()[-6:]
        return f"{self._app_name}-{macaddr_short}"

    async def get_hostname(self):
        """
        Retrieves the hostname of the device.

        Returns:
            str: The hostname of the device
        """
        return network.hostname()

    async def set_hostname(self, hostname=None):
        """
        Sets the hostname of the device.

        Args:
            hostname (str, optional): The hostname to set. If not provided, the hostname will be
                set to the value in config, or a generated hostname if no value is present in
                config.

        Returns:
            str: The hostname of the device
        """
        HOSTNAME_KEY: str = "hostname:16"

        if hostname:
            if len(hostname) > 16:
                raise ValueError("Hostname must be 16 characters or less")

            log.info(f"Setting hostname to {hostname}")
            network.hostname(hostname)
            await cfg.set(HOSTNAME_KEY, hostname)
            return network.hostname()

        configured_hostname = await cfg.get(HOSTNAME_KEY, raises=False)
        if configured_hostname:
            log.info(f"Setting hostname to {configured_hostname}")
            network.hostname(configured_hostname)
            return network.hostname()

        hostname = self.generate_hostname()
        if len(await hostname) > 16:
            raise ValueError("Hostname must be 16 characters or less")

        log.info(f"Setting hostname to generated: {hostname}")
        network.hostname(hostname)
        await cfg.set(HOSTNAME_KEY, await hostname)

        return network.hostname()

    async def get_wifi_credentials(self) -> tuple[str, str]:
        """
        Retrieves the SSID and password of the wifi network.

        Returns:
            tuple[str, str]: The SSID and password of the wifi network

        Raises:
            ValueError: If the SSID or password is not found in the config
        """
        CFG_SSID_KEY: str = "ssid:32"
        CFG_PASSWORD_KEY: str = "password:32"

        ssid = await cfg.get(CFG_SSID_KEY, raises=False)
        password = await cfg.get(CFG_PASSWORD_KEY, raises=False)
        if any([not ssid, not password]):
            raise ValueError("SSID or password not found in config")

        return ssid, password  # type: ignore

    async def set_wifi_credentials(self, ssid: str, password: str):
        """
        Sets the SSID and password of the wifi network.

        Args:
            ssid (str): The SSID of the wifi network
            password (str): The password of the wifi network
        """
        CFG_SSID_KEY: str = "ssid:32"
        CFG_PASSWORD_KEY: str = "password:32"

        await cfg.set(CFG_SSID_KEY, ssid)
        await cfg.set(CFG_PASSWORD_KEY, password)

    async def generate_hostname(self, unique: bool = True):
        """
        Generates a hostname for the device.

        Args:
            unique (bool, optional): If True, the hostname will be unique to the device by using
                the last 6 characters of the MAC address. If False, the hostname will contain the
                just the app name.

        Returns:
            str: The generated hostname
        """
        if not unique:
            return self._app_name.lower()

        macaddr = self.wlan_sta.config("mac").hex()[-6:]
        return f"{self._app_name.lower()}_{macaddr}"

    async def sync_ntp(self):
        """
        Synchronizes the device's time with an NTP server.

        Returns:
            tuple(int, int, int, int, int, int, int, int): The current date and time
        """
        rtc = machine.RTC()
        ntptime.settime()
        log_ntp.info(f"Time synchronized with NTP server, it's now {rtc.datetime()}")
        return rtc.datetime()

    async def scan(self):
        """
        Scans for wifi networks.

        Returns:
            dict: A dictionary of wifi networks with the SSID as the key and a dictionary of
                network information as the value. The network information dictionary contains the
                following keys:
                    bssid (str): The BSSID of the network
                    channel (int): The channel of the network
                    rssi (int): The RSSI of the network
                    security (str): The security type of the network
                    is_hidden (bool): True if the network is hidden, False otherwise

        Raises:
            OSError: If the network interface is not in STA mode
        """
        previous_state = self.wlan_sta.active()
        if not previous_state:
            self.wlan_sta.active(True)

        result = {}
        for entry in self.wlan_sta.scan():
            ssid, bssid, channel, rssi, security, hidden = entry
            log.info(f"Found SSID: {ssid.decode()} ({rssi} dBm)")
            result[ssid.decode()] = {
                "bssid": bssid.hex(":"),
                "channel": int(channel),
                "rssi": int(rssi),
                "security": AUTH_MODE[str(security)],
                "is_hidden": bool(hidden),
                "is_connected": ssid.decode() == self.wlan_sta.config("ssid")
                if self.wlan_sta.isconnected()
                else False,
            }

            # map RSSI to human-readable bars
            if result[ssid.decode()]["rssi"] > -50:
                result[ssid.decode()]["rssi_bars"] = 4
            elif result[ssid.decode()]["rssi"] > -60:
                result[ssid.decode()]["rssi_bars"] = 3
            elif result[ssid.decode()]["rssi"] > -70:
                result[ssid.decode()]["rssi_bars"] = 2
            elif result[ssid.decode()]["rssi"] > -80:
                result[ssid.decode()]["rssi_bars"] = 1
            else:
                result[ssid.decode()]["rssi_bars"] = 0

        if previous_state is False:
            self.wlan_sta.active(False)

        return result

    async def ap_start(self, ssid=None, password=None, callback=None):
        """
        Starts an access point with the given SSID and password.

        Args:
            ssid (str, Optional): The SSID of the access point. If not provided, the SSID will be
                genearted from the app name and the last 6 characters of the MAC address.
            password (str, Optional): The password of the access point. If not provided, the
                access point will be open. If given, the access point will be secured with WPA2.
            callback (function, Optional): A callback function to call when the access point is
                started. The function should take 3 arguments: the SSID, the mac address, and the
                hostname of the device.

        Returns:
            None
        """
        self.wlan_ap.active(True)
        self.wlan_ap.config(
            essid=ssid or self._default_ap_ssid,
            password=password or "",
            authmode=network.AUTH_WPA_WPA2_PSK if password else network.AUTH_OPEN,
            pm=network.WLAN.PM_NONE,  # type: ignore
        )
        await self.set_hostname()

        log.info("Access point started")
        ifconf = self.wlan_ap.ifconfig()
        diag_msg = {
            "MAC": self.wlan_ap.config("mac").hex(":"),
            "IP": ifconf[0],
            "Netmask": ifconf[1],
            "Gateway": ifconf[2],
            "DNS": ifconf[3],
            "Channel": self.wlan_ap.config("channel"),
            "Hostname": await self.get_hostname(),
        }
        log.info("Diagnostic data:", **diag_msg)

        if callback:
            callback(ssid, self.wlan_ap.config("mac").hex(":"), self.get_hostname())

    async def ap_stop(self, callback=None):
        """
        Stops the access point.

        Args:
            callback (function, Optional): A callback function to call when the access point is
                stopped. The function should take 1 argument: the SSID of the access point.
        """
        ssid = self.wlan_ap.config("essid")
        log.info(f"Stopping access point {ssid}")
        self.wlan_ap.active(False)

        if callback:
            callback(ssid)

    async def sta_connect(
        self,
        ssid: str,
        password: str,
        timeout: int = 60,
        callback_connecting=None,
        callback_connected=None,
    ):
        """
        Connects to a wifi network.

        Args:
            ssid (str): The SSID of the network to connect to
            password (str): The password of the network
            timeout (int, Optional): The maximum time to wait for the connection to be established.
                Default is 30 seconds.
            callback_connecting (function, Optional): A callback function to call when the connection
                is being established. The function should take 1 argument: the SSID of the network.
            callback_connected (function, Optional): A callback function to call when the connection is
                established. The function should take 6 arguments: SSID, signal strength, IP address,
                Netmask, Gateway and DNS address.

        Returns:
            None
        """
        if not self.wlan_sta.active():
            self.wlan_sta.active(True)

        self.wlan_sta.connect(ssid, password)
        start_time = time.time()
        start_time_error = None
        log.info(f"Connecting to {ssid}")

        if callback_connecting:
            callback_connecting(ssid)

        while not self.wlan_sta.isconnected():
            status = WLAN_STATUS[str(self.wlan_sta.status())]
            log.debug(f"Connecting... status: {status}")

            if status in ["NO_AP_FOUND", "AUTH_FAIL"]:
                # bug: the statuses persist even after the connection is disconnected
                #  disconnecting and deactivating the interface does nothing really,
                #  so we check if the same status happens for more than 5 seconds.
                #  (for most cases it was enough, we'll see though)
                if not start_time_error:
                    start_time_error = time.time()

                if time.time() - start_time_error > 5:  # type: ignore
                    log.error(f"Failed to connect to {ssid}")
                    self.wlan_sta.disconnect()
                    self.wlan_sta.active(False)
                    return False, status

            if time.time() - start_time > timeout:  # type: ignore
                log.error(f"Connection to {ssid} timed out")
                self.wlan_sta.disconnect()
                self.wlan_sta.active(False)
                return False, str(WLAN_STATUS["200"])

            await asyncio.sleep(1)

        log.info(f"Connected to {ssid}")
        if callback_connected:
            ifconf = self.wlan_sta.ifconfig()
            callback_connected(
                ssid,
                self.wlan_sta.status("rssi"),
                ifconf[0],
                ifconf[1],
                ifconf[2],
                ifconf[3],
            )

        return True, WLAN_STATUS[str(self.wlan_sta.status())]

    async def sta_disconnect(self, callback=None):
        """
        Disconnects from the wifi network.

        Args:
            callback (function, Optional): A callback function to call when the connection is
                disconnected. The function should take 1 argument: the SSID of the network.
        """
        ssid = self.wlan_sta.config("ssid")
        log.info(f"Disconnecting from {ssid}")
        self.wlan_sta.disconnect()
        self.wlan_sta.active(False)

        if callback:
            callback(ssid)
