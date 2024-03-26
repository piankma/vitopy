import time


class Logging:
    def __init__(self, tag: str) -> None:
        """
        Initialize the logging class.

        Args:
            tag (str): The tag to be used in the logs.
        """
        self.tag = tag

        # shorthand for logging levels
        self.debug = lambda msg, **fields: self._log("DEBUG", msg, **fields)
        self.info = lambda msg, **fields: self._log("INFO", msg, **fields)
        self.warning = lambda msg, **fields: self._log("WARN", msg, **fields)
        self.error = lambda msg, **fields: self._log("ERROR", msg, **fields)
        self.fatal = lambda msg, **fields: self._log("FATAL", msg, **fields)

    def _log(self, level: str, message: str, **fields):
        # TODO: remote logger
        message = f"[{level:>5}] {time.time():>8}: {self.tag} - {message}"
        prefix_len = message.index(" - ") + 5
        for k, v in fields.items():
            message += f"\n{' '*prefix_len}{k}: {v}"

        print(message)
