import platform

from .cpu import counts
from .gpu import get_gpu_stats
from .memory import get_ram_stats
from .readings import read


def cpu_model():
    if platform.system() == "Windows":
        import winreg
        path = r"HARDWARE\DESCRIPTION\System\CentralProcessor\0"
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path) as key:
            return winreg.QueryValueEx(key, "ProcessorNameString")[0].strip()
    return platform.processor()


def get_system_info() -> dict[str, object]:
    """Return allowlisted hardware and runtime characteristics."""
    result = {"unavailable": {}, "os": platform.system(), "os_release": platform.release(),
              "python_version": platform.python_version()}
    read(result, "cpu_model", cpu_model)
    counts(result)
    ram = get_ram_stats()
    gpu = get_gpu_stats()
    for dest, source, key in (("ram_total_mib", ram, "total_mib"),
                              ("gpu_model", gpu["gpu"] or {}, "name"),
                              ("vram_total_mib", gpu["gpu"] or {}, "vram_total_mib")):
        result[dest] = source.get(key)
        if result[dest] is None:
            result["unavailable"][dest] = (source.get("unavailable", {}).get(key)
                                            or gpu["unavailable"].get("gpu"))
    return result
