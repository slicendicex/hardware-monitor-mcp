import asyncio
import json
import socket
from contextlib import closing
from datetime import datetime, timedelta

import httpx
import uvicorn
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from hardware_monitor.server import server


async def check_tools(url):
    async with httpx.AsyncClient(trust_env=False) as http:
        async with streamable_http_client(url, http_client=http) as (reader, writer, _):
            async with ClientSession(reader, writer) as session:
                await session.initialize()
                tools = (await session.list_tools()).tools
                assert {tool.name for tool in tools} == {
                    "get_cpu_stats", "get_ram_stats", "get_gpu_stats", "get_system_info", "get_snapshot"}
                for tool in tools:
                    assert tool.annotations.readOnlyHint is True
                    reply = await session.call_tool(tool.name, {})
                    assert not reply.isError and isinstance(reply.structuredContent, dict)
                    data = reply.structuredContent
                    json.dumps(data, allow_nan=False)
                    if tool.name == "get_snapshot":
                        assert set(data) == {"cpu", "ram", "gpu", "timestamp_utc"}
                        assert datetime.fromisoformat(data["timestamp_utc"]).utcoffset() == timedelta(0)


async def smoke():
    assert (server.settings.host, server.settings.port, server.settings.streamable_http_path) == (
        "127.0.0.1", 8765, "/mcp")
    with closing(socket.socket()) as sock:
        sock.bind(("127.0.0.1", 0))
        host, port = sock.getsockname()
        runner = uvicorn.Server(uvicorn.Config(server.streamable_http_app(), log_level="warning"))
        task = asyncio.create_task(runner.serve(sockets=[sock]))
        try:
            while not runner.started:
                if task.done():
                    await task
                    raise RuntimeError("Server exited before startup")
                await asyncio.sleep(0.02)
            await check_tools(f"http://{host}:{port}/mcp")
        finally:
            runner.should_exit = True
            await task


def test_streamable_http():
    asyncio.run(asyncio.wait_for(smoke(), timeout=30))
