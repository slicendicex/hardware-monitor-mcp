import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from hardware_monitor import cpu, gpu, memory, system
from hardware_monitor.readings import MIB


def test_cpu(monkeypatch):
    sample = Mock(return_value=[10, 30])
    monkeypatch.setattr(cpu.psutil, "cpu_percent", sample)
    monkeypatch.setattr(cpu.psutil, "cpu_freq", lambda: None)
    monkeypatch.setattr(cpu.psutil, "cpu_count", lambda logical: 2 if logical else 1)
    data = cpu.get_cpu_stats()
    sample.assert_called_once_with(interval=0.2, percpu=True)
    assert data["utilization_percent"] == 20
    assert data["physical_core_count"] == 1 and data["logical_core_count"] == 2
    assert data["current_frequency_mhz"] is None
    assert data["unavailable"]["current_frequency_mhz"]


def test_memory(monkeypatch):
    sample = SimpleNamespace(total=8*MIB, available=6*MIB, used=2*MIB, percent=25)
    monkeypatch.setattr(memory.psutil, "virtual_memory", lambda: sample)
    assert memory.get_ram_stats() == dict(total_mib=8, available_mib=6, used_mib=2,
                                          utilization_percent=25, unavailable={})
    monkeypatch.setattr(memory.psutil, "virtual_memory", Mock(side_effect=OSError))
    data = memory.get_ram_stats()
    assert all(data[k] is None and reason for k, reason in data["unavailable"].items())


@pytest.fixture
def nvml(monkeypatch):
    api = Mock(wraps=gpu.nv)
    api.NVMLError = gpu.nv.NVMLError
    api.nvmlInit.return_value = None
    api.nvmlShutdown.return_value = None
    api.nvmlDeviceGetCount.return_value = 1
    api.nvmlDeviceGetHandleByIndex.return_value = object()
    api.nvmlDeviceGetName.return_value = "Test GPU"
    api.nvmlDeviceGetMemoryInfo.return_value = SimpleNamespace(total=4*MIB, used=MIB, free=3*MIB)
    api.nvmlDeviceGetUtilizationRates.return_value = SimpleNamespace(gpu=60, memory=7)
    api.nvmlDeviceGetTemperature.side_effect = gpu.nv.NVMLError_NotSupported()
    api.nvmlDeviceGetPowerUsage.return_value = 42500
    api.nvmlDeviceGetPowerManagementLimit.return_value = 160000
    monkeypatch.setattr(gpu, "nv", api)
    return api


def test_gpu_partial(nvml):
    data = gpu.get_gpu_stats()["gpu"]
    assert data["temperature_c"] is None and data["unavailable"]["temperature_c"]
    assert (data["power_w"], data["power_limit_w"]) == (42.5, 160)
    assert (data["memory_utilization_percent"], data["vram_used_percent"]) == (7, 25)
    nvml.nvmlShutdown.assert_called_once()
    json.dumps(data, allow_nan=False)


def test_no_gpu(nvml):
    nvml.nvmlDeviceGetCount.return_value = 0
    assert gpu.get_gpu_stats()["unavailable"]["gpu"]
    nvml.nvmlShutdown.assert_called_once()
    nvml.nvmlInit.side_effect = nvml.NVMLError(12)
    assert gpu.get_gpu_stats()["gpu"] is None
    nvml.nvmlShutdown.assert_called_once()


def test_system_allowlist(monkeypatch):
    monkeypatch.setattr(system, "get_gpu_stats", lambda: {"gpu": None, "unavailable": {"gpu": "absent"}})
    data = system.get_system_info()
    assert set(data) == {"os", "os_release", "python_version", "cpu_model", "physical_core_count",
                         "logical_core_count", "ram_total_mib", "gpu_model", "vram_total_mib", "unavailable"}
    assert data["gpu_model"] is None and data["unavailable"]["gpu_model"] == "absent"
