# ADR-001 — Разработка в WSL, измерения в Windows

| Поле | Значение |
|---|---|
| Date | 2026-11-25 (дата фиксации решения v0.1) |
| Status | Accepted |
| Context | Инструменты разработки находятся в WSL Ubuntu. Объект наблюдения — хост Windows. |
| Alternatives | Сравнение альтернатив в материалах проекта не зафиксировано. |
| Decision | Вести разработку через Codex CLI в WSL, запускать сервер и проверять датчики в Windows Python 3.14. |
| Rationale | Требуются показатели ОС и драйвера на целевом хосте. |
| Consequences | Для приёмки аппаратных показаний нужен запуск Windows-интерпретатора. Его можно вызвать из WSL. |
| Related files | [README](../../README.md), [system.py](../../src/hardware_monitor/system.py) |
