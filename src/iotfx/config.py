import esp32
from iotfx.logging import Logging

log = Logging("NVS")


class Config:
    def __init__(self, section: str) -> None:
        self.section = section
        self.nvs = esp32.NVS(self.section)

    async def get(self, key: str, raises: bool = True) -> str | None:
        """
        Get the value of the key from the NVS.

        Args:
            key (str): The key to get the value from.
            raises (bool): Whether to raise an error if the key is not found.

        Returns:
            str: The value of the key.
        """
        try:
            key_name, buf_size = key.split(":")
        except ValueError:
            log.error("Key must be in the format 'key_name:buf_size'")
            raise ValueError("Key must be in the format 'key_name:buf_size'")

        buf = bytearray(int(buf_size))
        try:
            self.nvs.get_blob(key_name, buf)
            value = buf.decode("ascii")
            log.debug(f"Reading {self.section}.{key_name}: {value}")
            return value
        except OSError as e:
            if raises:
                log.error(f"Key {self.section}.{key} not found")
                raise KeyError(f"Key {self.section}.{key} not found") from e

            log.warning(f"Key {self.section}.{key} not found, returning None")
            return None

    async def set(self, key: str, value: str) -> None:
        """
        Set the value of the key in the NVS.

        Args:
            key (str): The key to set the value of.
            value (str): The value to set the key to.
        """
        try:
            key_name, _ = key.split(":")
        except ValueError:
            log.error("Key must be in the format 'key_name:buf_size'")
            raise

        data = value.encode("ascii")

        log.debug(f"Writing {self.section}.{key_name}: {value}")
        self.nvs.set_blob(key_name, data)
        self.nvs.commit()

    async def delete(self, key: str) -> None:
        """
        Delete the key from the NVS.

        Args:
            key (str): The key to delete.
        """
        try:
            key_name, _ = key.split(":")
        except ValueError:
            log.error("Key must be in the format 'key_name:buf_size'")
            raise

        log.debug(f"Deleting {self.section}.{key_name}")
        self.nvs.erase_key(key_name)
        self.nvs.commit()
