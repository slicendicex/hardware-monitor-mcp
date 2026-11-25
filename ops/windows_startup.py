"""Windows logon tasks for Hardware Monitor MCP. Run with the project's Windows venv."""
import argparse
import getpass
import json
import os
import re
import runpy
import subprocess
import sys
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit

import psutil
import win32api
import win32com.client
import win32crypt
import win32security

SCRIPT = Path(__file__).resolve()
ROOT = SCRIPT.parent.parent
PYTHONW = ROOT / ".venv/Scripts/pythonw.exe"
CLIENT = ROOT.parent / "tunnel_client/tunnel-client.exe"
STATE = Path(os.environ["LOCALAPPDATA"]) / "HardwareMonitorMCP"
SECRET = STATE / "connection.dpapi"
URL = "http://127.0.0.1:8765/mcp"
NAMES = {"server": "Hardware Monitor MCP - Server", "tunnel": "Hardware Monitor MCP - Tunnel"}
SOURCE = "HardwareMonitorMCP-v0.1 " + str(ROOT)
KEYS = ("CONTROL_PLANE_TUNNEL_ID", "CONTROL_PLANE_API_KEY", "CONTROL_PLANE_HTTP_PROXY")
NO_WINDOW = subprocess.CREATE_NO_WINDOW


def settings():
    if SECRET.exists():
        blob = win32crypt.CryptUnprotectData(SECRET.read_bytes(), None, None, None, 1)[1]
        return json.loads(blob)
    return {}


def configure(interactive):
    values = settings()
    for key in KEYS:
        value = os.getenv(key)
        if key == "CONTROL_PLANE_API_KEY":
            value = value or os.getenv("OPENAI_API_KEY")
        value = value or values.get(key)
        if not value and interactive:
            if not sys.stdin.isatty():
                raise ValueError("Run install in interactive Windows PowerShell.")
            value = getpass.getpass(key + " (hidden): ").strip()
        if not value:
            if interactive:
                raise ValueError("Required connection setting is empty.")
            return False
        values[key] = value
    try:
        proxy = urlsplit(values[KEYS[2]])
        valid = proxy.scheme in ("http", "https") and bool(proxy.hostname) and proxy.port != 0
    except ValueError:
        valid = False
    if not valid:
        raise ValueError("Invalid proxy URL.")
    if not re.fullmatch(r"tunnel_(?:[a-z0-9]{4}_)?[a-z0-9]{32}", values[KEYS[0]]):
        raise ValueError("Invalid tunnel ID.")
    STATE.mkdir(parents=True, exist_ok=True)
    encrypted = win32crypt.CryptProtectData(json.dumps(values).encode(), None, None, None, None, 1)
    import tempfile
    with tempfile.NamedTemporaryFile(dir=STATE, delete=False) as temp:
        temp.write(encrypted)
    os.replace(temp.name, SECRET)
    return True


def listeners():
    return [c for c in psutil.net_connections("tcp") if c.status == psutil.CONN_LISTEN]


def clients():
    found = []
    for p in psutil.process_iter(["name"]):
        if (p.info["name"] or "").lower() == CLIENT.name.lower():
            try:
                if Path(p.exe()) == CLIENT:
                    found.append(p)
            except psutil.NoSuchProcess:
                continue
    return found


def owned(pid, role):
    try:
        p = psutil.Process(pid)
        for ancestor in [p, *p.parents()]:
            args = ancestor.cmdline()
            if str(SCRIPT).lower() in [a.lower() for a in args] and role in args:
                return True
    except (psutil.Error, OSError):
        pass
    return False


def worker(role):
    # pythonw supplies no console streams; Uvicorn inspects isatty() on startup.
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w")
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w")
    if role == "server":
        if any(c.laddr.port == 8765 for c in listeners()):
            return 20
        os.chdir(ROOT)
        runpy.run_module("hardware_monitor.server", run_name="__main__")
        return 0
    if clients():
        return 20
    values = settings()
    if not values:
        return 21
    env = os.environ.copy()
    env.update(values)
    env.update(LOG_FILE="stdout", LOG_HTTP_RAW_UNSAFE="false", OPEN_WEB_UI="false")
    args = [str(CLIENT), "run", "--mcp.server-url=" + URL, "--health.listen-addr", "127.0.0.1:0"]
    return subprocess.run(args, cwd=CLIENT.parent, env=env, creationflags=NO_WINDOW,
                          stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                          stderr=subprocess.DEVNULL).returncode


def scheduler():
    service = win32com.client.Dispatch("Schedule.Service")
    service.Connect()
    return service, service.GetFolder("\\")


def existing(folder):
    tasks = {t.Name: t for t in folder.GetTasks(1) if t.Name in NAMES.values()}
    if any(t.Definition.RegistrationInfo.Source != SOURCE for t in tasks.values()):
        raise ValueError("Task name collision. Existing task was preserved.")
    return tasks


def install(interactive):
    if not PYTHONW.is_file() or not CLIENT.is_file():
        raise ValueError("Windows venv or tunnel-client.exe missing.")
    service, folder = scheduler()
    existing(folder)
    ready = configure(interactive)
    token = win32security.OpenProcessToken(win32api.GetCurrentProcess(), 8)
    sid = win32security.ConvertSidToStringSid(win32security.GetTokenInformation(token, 1)[0])
    for role, name in NAMES.items():
        task = service.NewTask(0)
        task.RegistrationInfo.Source = SOURCE
        task.Principal.UserId = sid
        task.Principal.LogonType = 3  # interactive token
        task.Principal.RunLevel = 0
        trigger = task.Triggers.Create(9)  # logon
        trigger.UserId = sid
        task.Settings.ExecutionTimeLimit = "PT0S"
        task.Settings.MultipleInstances = 2  # ignore new
        task.Settings.DisallowStartIfOnBatteries = False
        task.Settings.StopIfGoingOnBatteries = False
        action = task.Actions.Create(0)
        action.Path = str(PYTHONW)
        action.Arguments = subprocess.list2cmdline([str(SCRIPT), role])
        action.WorkingDirectory = str(ROOT)
        registered = folder.RegisterTaskDefinition(name, task, 6, sid, None, 3)
        if registered.State != 4 and (role == "server" or ready):
            registered.Run(None)
    print("Tasks registered. Connection settings " + ("saved." if ready else "require interactive install."))


def status():
    _, folder = scheduler()
    tasks = existing(folder)
    for role, name in NAMES.items():
        task = tasks.get(name)
        print(role, "task:", ("running" if task.State == 4 else "registered") if task else "absent",
              "last result:", task.LastTaskResult if task else "-")
    sockets = listeners()
    local = [c for c in sockets if c.laddr.ip == "127.0.0.1" and c.laddr.port == 8765]
    print("Server listener:", ", ".join(f"PID {c.pid} managed={owned(c.pid, 'server')}" for c in local) or "absent")
    try:
        body = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
            "protocolVersion": "2025-03-26", "capabilities": {}, "clientInfo": {"name": "local-status", "version": "1"}}}
        request = urllib.request.Request(URL, data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json", "Accept": "application/json, text/event-stream"})
        with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(request, timeout=4) as response:
            ok = json.load(response)["result"]["serverInfo"]["name"] == "Hardware Monitor"
    except (OSError, KeyError, ValueError):
        ok = False
    print("Local Hardware Monitor MCP initialize:", ok)
    processes = clients()
    print("Tunnel processes:", len(processes), "connection settings saved:", SECRET.exists())
    for p in processes:
        ports = [c.laddr.port for c in sockets if c.pid == p.pid and c.laddr.ip == "127.0.0.1"]
        try:
            ready = any(subprocess.run([str(CLIENT), "health", "--port", str(port), "--pid", str(p.pid),
                                    "--require-control-plane-poll"], stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL, timeout=8).returncode == 0 for port in ports)
        except subprocess.TimeoutExpired:
            ready = "health check timed out"
        print(f"Tunnel PID {p.pid} managed={owned(p.pid, 'tunnel')} ready with successful poll={ready}")
    print("ChatGPT end-to-end: verify by requesting get_snapshot.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["install", "status", "remove", *NAMES])
    parser.add_argument("--no-prompt", action="store_true")
    args = parser.parse_args()
    if args.command in NAMES:
        return worker(args.command)
    if args.command == "install":
        install(not args.no_prompt)
    elif args.command == "status":
        status()
    else:
        _, folder = scheduler()
        for name, task in existing(folder).items():
            if task.State == 4:
                task.Stop(0)
            folder.DeleteTask(name, 0)
        SECRET.unlink(missing_ok=True)
        print("Logon tasks and autostart credential copy removed.")


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:
        # No exception payloads: native/configuration errors can contain credentials.
        print("Operation failed:", str(error) if type(error) is ValueError and str(error) in (
            "Run install in interactive Windows PowerShell.", "Required connection setting is empty.",
            "Invalid proxy URL.", "Invalid tunnel ID.", "Task name collision. Existing task was preserved.",
            "Windows venv or tunnel-client.exe missing.") else type(error).__name__, "code:", getattr(error, "hresult", "-"), file=sys.stderr)
        sys.exit(1)
