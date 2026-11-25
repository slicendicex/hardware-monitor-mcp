import psutil

from .readings import MIB, read


def get_ram_stats() -> dict[str, object]:
    """Return physical memory from one OS measurement."""
    result = {"unavailable": {}}
    try:
        memory = psutil.virtual_memory()
    except (psutil.Error, OSError, NotImplementedError) as exc:
        for field in ("total_mib", "used_mib", "available_mib", "utilization_percent"):
            result[field] = None
            result["unavailable"][field] = type(exc).__name__
        return result
    for field in ("total", "used", "available"):
        read(result, field + "_mib", lambda: getattr(memory, field) / MIB)
    result["utilization_percent"] = memory.percent
    return result
