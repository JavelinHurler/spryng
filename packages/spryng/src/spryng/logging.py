from typing import Callable

def log_to_console(clazz: type, level: str, message: str):
    print(f"[{level}] {clazz.__module__}.{clazz.__name__}: {message}")

class LoggerManager:
    callbacks: list[Callable[[type, str, str], None]] = [log_to_console]

    @classmethod
    def log(cls, owner: type, level: str, message: str):
        for callback in cls.callbacks:
            callback(owner, level, message)

    @classmethod
    def get_logger(cls, owner: type):
        return Logger(owner)

    @classmethod
    def decorate(cls, clazz: type):
        annotations = getattr(clazz, "__annotations__", {})

        if "log" not in annotations:
            raise Exception(
                f"Trying to decorate class {clazz.__module__}.{clazz.__name__} with logger, "
                "but static field log is not present"
            )

        if annotations["log"] is not Logger:
            raise Exception(
                f"Trying to decorate class {clazz.__module__}.{clazz.__name__} with logger, "
                "but static field log is not of type Logger"
            )

        clazz.log = cls.get_logger(clazz)

        return clazz


class Logger:
    def __init__(self, owner: type):
        self._owner = owner

    def info(self, msg: str):
        LoggerManager.log(self._owner, "INFO", msg)

    def warning(self, msg: str):
        LoggerManager.log(self._owner, "WARNING", msg)

    def error(self, msg: str):
        LoggerManager.log(self._owner, "ERROR", msg)

    def debug(self, msg: str):
        LoggerManager.log(self._owner, "DEBUG", msg)