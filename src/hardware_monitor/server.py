from datetime import datetime, timezone

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from .cpu import get_cpu_stats
from .gpu import get_gpu_stats
from .memory import get_ram_stats
from .system import get_system_info

server = FastMCP("Hardware Monitor", host="127.0.0.1", port=8765,
                 streamable_http_path="/mcp", stateless_http=True, json_response=True)


def get_snapshot() -> dict[str, object]:
    """Sample CPU, RAM and GPU sequentially and timestamp completion in UTC."""
    result = {"cpu": get_cpu_stats(), "ram": get_ram_stats(), "gpu": get_gpu_stats()}
    result["timestamp_utc"] = datetime.now(timezone.utc).isoformat()
    return result


for tool in (get_cpu_stats, get_ram_stats, get_gpu_stats, get_system_info, get_snapshot):
    server.tool(annotations=ToolAnnotations(readOnlyHint=True))(tool)


if __name__ == "__main__":
    server.run(transport="streamable-http")
