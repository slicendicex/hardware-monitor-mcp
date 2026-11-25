import pynvml as nv

from .readings import MIB, read


def device_stats(handle):
    result = {"unavailable": {}}
    read(result, "name", lambda: nv.nvmlDeviceGetName(handle))
    for getter, fields in (
        (nv.nvmlDeviceGetUtilizationRates,
         (("gpu", "utilization_percent", 1), ("memory", "memory_utilization_percent", 1))),
        (nv.nvmlDeviceGetMemoryInfo,
         (("total", "vram_total_mib", MIB), ("used", "vram_used_mib", MIB),
          ("free", "vram_free_mib", MIB))),
    ):
        try:
            sample = getter(handle)
        except nv.NVMLError as exc:
            for _, field, _ in fields:
                result[field] = None
                result["unavailable"][field] = type(exc).__name__
        else:
            for attr, field, divisor in fields:
                value = getattr(sample, attr)
                read(result, field, lambda: value / divisor if value not in
                     (2**32 - 1, 2**64 - 1) else None)
    read(result, "vram_used_percent", lambda: 100 * result["vram_used_mib"] /
         result["vram_total_mib"] if result["vram_total_mib"] and
         result["vram_used_mib"] is not None else None)
    read(result, "temperature_c", lambda: nv.nvmlDeviceGetTemperature(handle, nv.NVML_TEMPERATURE_GPU))
    read(result, "power_w", lambda: nv.nvmlDeviceGetPowerUsage(handle) / 1000)
    read(result, "power_limit_w", lambda: nv.nvmlDeviceGetPowerManagementLimit(handle) / 1000)
    return result


def get_gpu_stats() -> dict[str, object]:
    """Read the first NVIDIA GPU (NVML index zero)."""
    result = {"unavailable": {}}
    initialized = False
    try:
        nv.nvmlInit()
        initialized = True
        if nv.nvmlDeviceGetCount():
            result["gpu"] = device_stats(nv.nvmlDeviceGetHandleByIndex(0))
        else:
            result["gpu"] = None
            result["unavailable"]["gpu"] = "No NVIDIA GPU detected"
    except (nv.NVMLError, OSError) as exc:
        result["gpu"] = None
        result["unavailable"]["gpu"] = type(exc).__name__
    finally:
        if initialized:
            try:
                nv.nvmlShutdown()
            except nv.NVMLError as exc:
                result["unavailable"]["nvml_shutdown"] = type(exc).__name__
    return result
