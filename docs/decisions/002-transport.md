# ADR-002 — Streamable HTTP через OpenAI Secure MCP Tunnel

| Поле | Значение |
|---|---|
| Date | 2026-11-25 (дата фиксации решения v0.1) |
| Status | Accepted |
| Context | ChatGPT требуется доступ к локальному MCP. Внешняя сеть стенда доступна через прокси. |
| Alternatives | Сравнение альтернатив в материалах проекта не зафиксировано. |
| Decision | Слушать 127.0.0.1:8765/mcp через Streamable HTTP. Внешнее соединение обслуживает существующий Windows tunnel-client. |
| Rationale | Такая схема сохраняет требуемую привязку сервера к loopback и использует настроенный туннель. |
| Consequences | Локальный MCP-вызов и сквозной путь через прокси проверяются отдельно. |
| Related files | [server.py](../../src/hardware_monitor/server.py), [README](../../README.md) |
