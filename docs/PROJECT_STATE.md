# Оперативное состояние

| Раздел | Актуальное состояние |
|---|---|
| Current version | v0.1, версия Python-пакета 0.1.0. |
| Last updated | 2026-11-25 |
| Release status | Первая публичная версия исходников v0.1, без релизного тега. |
| Implementation status | Локальный MVP реализован и проверен на Windows. Критерии v0.1 выполнены. |
| Project objective | Предоставлять Local AI Lab аппаратные измерения Windows для исследования локального инференса. |
| Implemented features | Пять read-only MCP-инструментов для CPU, RAM, GPU, сведений о системе и объединённого снимка с UTC. |
| Key files and entry points | Точка запуска — `hardware_monitor.server`. Сборщики — в `src/hardware_monitor/`, тесты — в `tests/`, версии зависимостей — в `pyproject.toml` и `requirements-win314.txt`. |
| Runtime environment | Windows 10 x64, Python 3.14.3. Разработка в WSL Ubuntu. |
| Commands to install, run and test | [Команды PowerShell установки и запуска](../README.md#установка-и-запуск-в-powershell) и [локальной проверки](../README.md#локальная-проверка). |
| Verification status — локально, предыдущая проверка Codex | 25.11.2026, Windows, `python -m pytest -q` в проектной .venv — 6 passed, 1 warning. Через loopback проверены initialize, tools/list и tools/call всех пяти инструментов. На стенде ранее подтверждено чтение реальных показаний CPU и NVIDIA GPU. |
| Verification status — externally verified | По сообщению пользователя, Windows 10 и Python 3.14.3: OpenAI Secure MCP Tunnel через HTTP-прокси; ChatGPT обнаружил и вызвал get_system_info, get_cpu_stats, get_ram_stats, get_gpu_stats и get_snapshot (5/5). Получены реальные показатели CPU, RAM и NVIDIA GPU. |
| Known limitations | Предупреждение pydantic-settings о поле lifespan в SDK. Независимая сверка показателей с HWMonitor пока не завершена. [Ограничения измерений](../CHANGELOG.md#known-limitations). |
| Current task | Обе задачи входа Windows зарегистрированы. Туннель запущен задачей Windows с параметрами из DPAPI, успешный опрос control plane подтверждён. На ручном экземпляре сервера проверен локальный get_snapshot. [Управление автозапуском](../README.md#автозапуск-при-входе-в-windows). |
| Next version | v0.2 — непрерывный мониторинг. |
| Next actions | Проверить свежий get_snapshot из ChatGPT после перезагрузки и входа в Windows. При поручении v0.2 сверить критерии с ROADMAP.md и составить план периодического сбора. |
