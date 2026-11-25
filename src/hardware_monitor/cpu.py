import psutil

from .readings import read


def counts(result):
    read(result, "physical_core_count", lambda: psutil.cpu_count(logical=False))
    read(result, "logical_core_count", lambda: psutil.cpu_count(logical=True))


def frequency():
    freq = psutil.cpu_freq()
    return freq.current if freq and freq.current > 0 else None


def get_cpu_stats() -> dict[str, object]:
    """Sample logical CPU utilization over 200 ms, counts and reported frequency."""
    result = {"unavailable": {}}
    read(result, "per_logical_cpu_utilization_percent",
         lambda: psutil.cpu_percent(interval=0.2, percpu=True) or None)
    samples = result["per_logical_cpu_utilization_percent"]
    read(result, "utilization_percent",
         lambda: round(sum(samples) / len(samples), 2) if samples else None)
    counts(result)
    read(result, "current_frequency_mhz", frequency)
    return result
