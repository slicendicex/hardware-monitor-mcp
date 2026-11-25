# Hardware Monitor MCP v0.1

Локальный сервер телеметрии Windows для Local AI Lab. Рабочая точка подключения — `http://127.0.0.1:8765/mcp`, транспорт Streamable HTTP. Сбор выполняется по запросу. Сервер предоставляет пять инструментов без аргументов с аннотацией `readOnlyHint`.

## Установка и запуск в PowerShell

Из каталога проекта на Windows x64 с установленным Python 3.14 выполните следующие команды. Для загрузки пакетов потребуется доступ к PyPI через настроенный в вашей среде прокси.

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -c requirements-win314.txt -e ".[test]"
.\.venv\Scripts\python.exe -m hardware_monitor.server
```

Для остановки нажмите Ctrl+C. Виртуальное окружение используется напрямую, поэтому менять политику выполнения PowerShell не требуется.

## Локальная проверка

```powershell
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -c "from hardware_monitor.server import get_snapshot; import json; print(json.dumps(get_snapshot(), indent=2))"
```

Последняя команда снимает показания на машине запуска. Интеграционный тест поднимает тот же MCP app на свободном порту loopback, выполняет initialize, tools/list и вызывает каждый инструмент через SDK. На Windows проверьте модель GPU и общий объём VRAM, а также изменение загрузки под обычной рабочей нагрузкой. Тесты WSL характеризуют окружение WSL.

## Подключение к существующему туннелю

Запустите сервер в Windows и оставьте окно PowerShell открытым. Локальный адрес назначения для уже настроенного tunnel-client — `http://127.0.0.1:8765/mcp`. Если действующий маршрут указывает на этот адрес, запустите клиент привычной командой и выберите существующее подключение в ChatGPT. Запрос `get_system_info` передаст в ChatGPT характеристики оборудования. При несовпадении адреса действующего маршрута потребуется отдельное согласование настройки туннеля. Для локальной проверки запуск туннеля не требуется.

## Автозапуск при входе в Windows

Из корня проекта в обычном Windows PowerShell один раз выполните:

```powershell
.\.venv\Scripts\python.exe .\ops\windows_startup.py install
```

Используйте PowerShell с окружением ручного запуска или введите недостающие значения в скрытые запросы: существующий tunnel ID, ключ control plane и полный URL прокси. Установщик берёт их из CONTROL_PLANE_TUNNEL_ID, CONTROL_PLANE_API_KEY (также поддерживается OPENAI_API_KEY) и CONTROL_PLANE_HTTP_PROXY. Вводите секреты только в локальном приглашении. Копия хранится под Windows DPAPI текущего пользователя в `%LOCALAPPDATA%\HardwareMonitorMCP\connection.dpapi`. Для смены параметра повторите install из сеанса с новым значением переменной.

Планировщик создаёт две задачи «Hardware Monitor MCP - Server» и «Hardware Monitor MCP - Tunnel» с триггером входа пользователя и обычными правами. Для запуска используется Windows pythonw.exe. Клиент ожидается в соседней папке `..\tunnel_client\tunnel-client.exe`. После перемещения проекта потребуется заново настроить задачи. Сервер стартует независимо от сети. Клиент v0.0.21 сам повторяет обращения к недоступному прокси. Работающий клиент из той же папки и занятый порт сохраняются.

```powershell
.\.venv\Scripts\python.exe .\ops\windows_startup.py status
.\.venv\Scripts\python.exe .\ops\windows_startup.py remove
```

Первая команда проверяет задачи, владельца порта, MCP initialize и готовность туннеля с успешным control-plane poll. `managed=True` указывает на запуск через проектный фоновый скрипт. Код задачи 20 означает пропуск из-за занятого порта или уже работающего клиента, 21 — отсутствие сохранённых реквизитов. Для проверки свежих данных после обычного входа попросите ChatGPT вызвать get_snapshot и проверьте timestamp_utc. Команда remove останавливает задачи и удаляет их вместе с копией DPAPI; ручная конфигурация остаётся доступной.

По подтверждению пользователя, ChatGPT успешно вызвал `get_snapshot` через существующий туннель. Сквозная проверка автозапуска после перезагрузки и входа в Windows остаётся открытой.

## Документация проекта

- [ROADMAP.md](ROADMAP.md) — границы версий и критерии готовности.
- [AGENTS.md](AGENTS.md) — порядок начала сессии и разработки.
- [PROJECT_STATE.md](docs/PROJECT_STATE.md) — текущая версия, последние проверки и ближайшая задача.
- [ARCHITECTURE.md](docs/ARCHITECTURE.md) — модули, инструменты и смысл показателей.
- [Архитектурные решения](docs/decisions/) — принятые решения и их последствия.
- [LESSONS.md](docs/LESSONS.md) — разбор воспроизводимых проблем и способы проверки.
- [CHANGELOG.md](CHANGELOG.md) — изменения и ограничения выпусков.

Прямые зависимости закреплены в pyproject.toml, версии зависимостей Windows x64 Python 3.14 — в requirements-win314.txt. [Документация SDK ветки 1.x](https://github.com/modelcontextprotocol/python-sdk/tree/v1.x) · [psutil](https://psutil.readthedocs.io/) · [NVIDIA NVML](https://docs.nvidia.com/deploy/nvml-api/)
