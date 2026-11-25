"""Record unavailable readings without copying host-specific exception messages."""
import psutil
from pynvml import NVMLError

MIB = 1024 ** 2


def read(result, field, getter):
    try:
        value = getter()
        if value is None or value == "":
            raise ValueError("unavailable")
    except (NVMLError, psutil.Error, OSError, NotImplementedError, ValueError) as exc:
        result["unavailable"][field] = type(exc).__name__
        if isinstance(exc, ValueError):
            result["unavailable"][field] = "Source returned no usable reading"
        value = None
    result[field] = value
