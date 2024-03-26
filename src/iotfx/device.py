def get_device_info(print_info=False):
    """
    Return the device name and MicroPython version.

    Args:
        print_info (bool): Print the device information.

    Returns:
        dict: The device name and MicroPython version.
    """
    import os
    import esp32
    import machine

    data = {
        "micropython": os.uname().version,
        "device": os.uname().machine,
        "temperature": (esp32.raw_temperature() - 32) / 1.8,
        "frequency": machine.freq(),
    }

    if print_info:
        print("Device info:")
        print(f"    MicroPython: {data['micropython']}")
        print(f"    Device name: {data['device']}")
        print(f"    Temperature: {data['temperature']:0.2f}*C")
        print(f"    Frequency: {data["frequency"]/1_000_000:0.2f}MHz")
        print()

    return data


def get_fw_version(print_info=False):
    """
    Return the firmware version and name.

    Args:
        print_info (bool): Print the firmware information.

    Returns:
        dict: The firmware version and name.
    """
    import project

    data = {
        "version": project.VERSION,
        "name": project.NAME,
    }

    if print_info:
        print("App: ")
        print(f"    Name: {data['name']}")
        print(f"    Version: {data['version']}")
        print()

    return data


def get_memory_info(print_info=False):
    """
    Return the memory info.

    Args:
        print_info (bool): Print the memory information.

    Returns:
        dict: The memory information. If unit is not provided, the values are in bytes.
    """
    import gc

    data = {
        "free": gc.mem_free(),
        "allocated": gc.mem_alloc(),
        "total": gc.mem_free() + gc.mem_alloc(),
    }

    if print_info:
        print("Memory info:")
        print(f"    Free: {data['free']/1024:0.2f}kB")
        print(f"    Allocated: {data['allocated']/1024:0.2f}kB")
        print(f"    Total: {data['total']/1024:0.2f}kB")
        print()

    return data


def get_storage_info(print_info=False):
    """
    Return the storage info.

    Returns:
        dict: The storage information. If unit is not provided, the values are in bytes."""
    import os

    (
        f_bsize,
        f_frsize,
        f_blocks,
        f_bfree,
        f_bavail,
        f_files,
        f_ffree,
        f_favail,
        f_flag,
        f_namemax,
    ) = os.statvfs("/")

    data = {
        "free": (f_bfree * f_frsize),
        "used": ((f_blocks - f_bfree) * f_frsize),
        "total": (f_blocks * f_frsize),
    }

    if print_info:
        print("Storage info:")
        print(f"    Free: {data['free']/1024:0.2f}kB")
        print(f"    Used: {data['used']/1024:0.2f}kB")
        print(f"    Total: {data['total']/1024:0.2f}kB")
        print()

    return data


def print_all():
    get_device_info(print_info=True)
    get_fw_version(print_info=True)
    get_memory_info(print_info=True)
    get_storage_info(print_info=True)
