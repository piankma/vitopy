import time

import machine
import ntptime
import urequests

from iotfx.logging import Logging

log = Logging("NTP")


class NTP:
    def __init__(self):
        self.rtc = machine.RTC()
        ntptime.host = "pl.pool.ntp.org"

    def get_timezones(self) -> list[str]:
        """
        Get a list of available timezones.

        Returns:
            list[str]: A list of timezones.
        """
        data = urequests.get("http://worldtimeapi.org/api/timezone")
        return data.json()

    def get_timezone_offset(self, timezone: str) -> int:
        """
        Get the offset for a given timezone.

        Args:
            timezone (str): The timezone to get the offset for.
                Data is available at http://worldtimeapi.org/api/timezone

        Returns:
            int: The offset in seconds.
        """
        data = urequests.get(f"http://worldtimeapi.org/api/timezone/{timezone}")
        data = data.json()

        log.info(
            f"Timezone: {timezone} has offset {data['utc_offset']}"
            + f"{' with DST' if data['dst'] else ''}"
        )
        return int(data["raw_offset"]) + int(data["dst_offset"])

    def get_timezone_for_current_ip(self) -> int:
        """
        Retrieve the timezone for the current IP address.

        Returns:
            int: The offset in seconds.

        Raises:
            ValueError: If the request fails.
        """
        data = urequests.get("http://worldtimeapi.org/api/ip")
        data = data.json()

        log.info(
            f"Timezone for IP: {data['client_ip']} is {data['timezone']} ({data['utc_offset']})"
            + f"{" with DST" if data['dst'] else ''}"
        )
        return int(data["raw_offset"]) + int(data["dst_offset"])

    def set_time_auto(self) -> int:
        """
        Set the time automatically using the current IP address.

        Returns:
            int: The time set in seconds since the epoch.

        Raises:
            ValueError: If the request fails.
        """
        timezone = self.get_timezone_for_current_ip()
        t = ntptime.time() + timezone
        self.rtc.datetime(time.localtime(t))

        d_year, d_month, d_day, t_hr, t_min, t_sec, *_ = time.localtime(t)
        log.info(
            f"Time set to {d_year}-{d_month:02}-{d_day:02} {t_hr:02}:{t_min:02}:{t_sec:02}"
        )

        return t
