import asyncio
import json
import os
import re
from collections import defaultdict, deque
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

HERE = Path(__file__).parent
SERVICES_FILE = Path.cwd() / "services.json"
ENV_FILE = Path.cwd() / ".overmind.env"
FRONTEND_DIST = HERE / "frontend" / "dist"

# --- Global state ---
PROCS: dict[str, dict[str, asyncio.subprocess.Process]] = {}
LOG_BUFFER: dict[str, deque] = defaultdict(lambda: deque(maxlen=500))
LOG_QUEUES: dict[str, list[asyncio.Queue]] = defaultdict(list)
TUNNEL_URLS: dict[str, str] = {}
BUILD_RUNNING: set[str] = set()

TUNNEL_RE = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com")


def load_services() -> list[dict]:
    return json.loads(SERVICES_FILE.read_text())["services"]


def load_env() -> dict[str, str]:
    env = {}
    for line in ENV_FILE.read_text().splitlines():
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env


def get_status(name: str) -> str:
    if name in BUILD_RUNNING:
        return "building"
    procs = PROCS.get(name, {})
    if procs and all(p.returncode is None for p in procs.values()):
        return "running"
    return "stopped"


app = FastAPI()


@app.get("/api/services")
async def list_services():
    services = load_services()
    return [
        {
            "name": svc["name"],
            "sam_port": svc["sam_port"],
            "proxy_port": svc["proxy_port"],
            "status": get_status(svc["name"]),
            "tunnel_url": TUNNEL_URLS.get(svc["name"]),
        }
        for svc in services
    ]


async def _read_stream(name: str, process_type: str, stream: asyncio.StreamReader) -> None:
    while True:
        line = await stream.readline()
        if not line:
            break
        text = line.decode("utf-8", errors="replace").rstrip()
        msg = {"process": process_type, "line": text}
        LOG_BUFFER[name].append(msg)
        if process_type == "tunnel":
            m = TUNNEL_RE.search(text)
            if m:
                TUNNEL_URLS[name] = m.group(0)
        for q in list(LOG_QUEUES[name]):
            await q.put(msg)


async def _spawn_sam(name: str, svc: dict, base_env: dict) -> asyncio.subprocess.Process:
    backend_path = base_env.get("BACKEND_PATH", "")
    sam_port = svc["sam_port"]
    extra_args = svc.get("sam_extra_args", "").split() if svc.get("sam_extra_args") else []
    sam_cmd = ["sam", "local", "start-lambda", "--env-vars", "env.json", "--port", str(sam_port)] + extra_args
    return await asyncio.create_subprocess_exec(
        *sam_cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        cwd=f"{backend_path}/functions/{name}",
        env=base_env,
    )


async def _start_service(name: str, svc: dict, env_vars: dict) -> None:
    base_env = os.environ.copy()
    base_env.update(env_vars)

    dev_path = env_vars.get("DEV_PATH", "")
    sam_port = svc["sam_port"]
    proxy_port = svc["proxy_port"]
    function_name = svc.get("function_name", "FunctionImp")

    sam_proc = await _spawn_sam(name, svc, base_env)

    proxy_env = base_env.copy()
    proxy_env["LAMBDA_PORT"] = str(sam_port)
    proxy_env["PROXY_PORT"] = str(proxy_port)
    if function_name != "FunctionImp":
        proxy_env["FUNCTION_NAME"] = function_name
    proxy_proc = await asyncio.create_subprocess_exec(
        "python3", f"{dev_path}/proxy.py",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        env=proxy_env,
    )

    tunnel_proc = await asyncio.create_subprocess_exec(
        "cloudflared", "tunnel", "--url", f"http://localhost:{proxy_port}",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        env=base_env,
    )

    PROCS[name] = {"sam": sam_proc, "proxy": proxy_proc, "tunnel": tunnel_proc}
    asyncio.create_task(_read_stream(name, "sam", sam_proc.stdout))
    asyncio.create_task(_read_stream(name, "proxy", proxy_proc.stdout))
    asyncio.create_task(_read_stream(name, "tunnel", tunnel_proc.stdout))


async def _stop_proc(proc: asyncio.subprocess.Process) -> None:
    try:
        proc.terminate()
    except ProcessLookupError:
        return
    try:
        await asyncio.wait_for(proc.wait(), timeout=5.0)
    except asyncio.TimeoutError:
        try:
            proc.kill()
        except ProcessLookupError:
            pass
        await proc.wait()


async def _stop_service(name: str) -> None:
    procs = PROCS.pop(name, {})
    TUNNEL_URLS.pop(name, None)
    for proc in procs.values():
        try:
            proc.terminate()
        except ProcessLookupError:
            pass
    for proc in procs.values():
        try:
            await asyncio.wait_for(proc.wait(), timeout=5.0)
        except asyncio.TimeoutError:
            try:
                proc.kill()
            except ProcessLookupError:
                pass


async def _restart_sam_only(name: str, svc: dict, env_vars: dict) -> Optional[str]:
    """Restart only the SAM process. Returns an error message, or None on success."""
    procs = PROCS.get(name)
    if not procs or "sam" not in procs:
        return "Service is not running; start it first"

    old_sam = procs["sam"]
    await _stop_proc(old_sam)

    base_env = os.environ.copy()
    base_env.update(env_vars)
    sam_proc = await _spawn_sam(name, svc, base_env)
    procs["sam"] = sam_proc
    asyncio.create_task(_read_stream(name, "sam", sam_proc.stdout))
    return None


def _find_service(name: str) -> Optional[dict]:
    for svc in load_services():
        if svc["name"] == name:
            return svc
    return None


@app.post("/api/services/{name}/start")
async def start_service(name: str):
    svc = _find_service(name)
    if not svc:
        return JSONResponse({"error": f"Unknown service: {name}"}, status_code=404)
    if get_status(name) == "running":
        return {"ok": True, "note": "already running"}
    await _start_service(name, svc, load_env())
    return {"ok": True}


@app.post("/api/services/{name}/stop")
async def stop_service(name: str):
    svc = _find_service(name)
    if not svc:
        return JSONResponse({"error": f"Unknown service: {name}"}, status_code=404)
    await _stop_service(name)
    return {"ok": True}


@app.post("/api/services/{name}/restart")
async def restart_service(name: str, scope: str = "all"):
    svc = _find_service(name)
    if not svc:
        return JSONResponse({"error": f"Unknown service: {name}"}, status_code=404)
    if scope not in ("all", "sam"):
        return JSONResponse(
            {"error": f"Invalid scope: {scope}. Use 'all' or 'sam'."},
            status_code=400,
        )
    if scope == "sam":
        err = await _restart_sam_only(name, svc, load_env())
        if err:
            return JSONResponse({"error": err}, status_code=409)
        return {"ok": True, "scope": "sam"}
    await _stop_service(name)
    await _start_service(name, svc, load_env())
    return {"ok": True, "scope": "all"}


@app.post("/api/services/{name}/build")
async def build_service(name: str):
    svc = _find_service(name)
    if not svc:
        return JSONResponse({"error": f"Unknown service: {name}"}, status_code=404)
    if name in BUILD_RUNNING:
        return {"ok": True, "note": "build already in progress"}

    async def _run_build():
        BUILD_RUNNING.add(name)
        try:
            proc = await asyncio.create_subprocess_exec(
                "make", f"build-{name}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=str(HERE),
            )
            async for line in proc.stdout:
                text = line.decode("utf-8", errors="replace").rstrip()
                msg = {"process": "build", "line": text}
                LOG_BUFFER[name].append(msg)
                for q in list(LOG_QUEUES[name]):
                    await q.put(msg)
            await proc.wait()
        finally:
            BUILD_RUNNING.discard(name)

    asyncio.create_task(_run_build())
    return {"ok": True}


@app.post("/api/services/{name}/clean")
async def clean_service(name: str):
    svc = _find_service(name)
    if not svc:
        return JSONResponse({"error": f"Unknown service: {name}"}, status_code=404)
    if name in BUILD_RUNNING:
        return {"ok": True, "note": "build already in progress"}

    async def _emit(line: str):
        msg = {"process": "build", "line": line}
        LOG_BUFFER[name].append(msg)
        for q in list(LOG_QUEUES[name]):
            await q.put(msg)

    async def _run_clean():
        BUILD_RUNNING.add(name)
        await _emit(f"[clean] removing .aws-sam for {name}…")
        try:
            proc = await asyncio.create_subprocess_exec(
                "make", f"clean-{name}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=str(HERE),
            )
            async for line in proc.stdout:
                text = line.decode("utf-8", errors="replace").rstrip()
                await _emit(text)
            rc = await proc.wait()
            await _emit(f"[clean] done (exit {rc})")
        finally:
            BUILD_RUNNING.discard(name)

    asyncio.create_task(_run_clean())
    return {"ok": True}


@app.post("/api/services/{name}/kill-ports")
async def kill_ports(name: str):
    svc = _find_service(name)
    if not svc:
        return JSONResponse({"error": f"Unknown service: {name}"}, status_code=404)

    sam_port = svc["sam_port"]
    proxy_port = svc["proxy_port"]

    async def _run_kill():
        try:
            proc = await asyncio.create_subprocess_exec(
                "npx", "kill-port", str(sam_port), str(proxy_port),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
        except FileNotFoundError:
            msg = {"process": "build", "line": "[kill-ports] error: npx not found on PATH"}
            LOG_BUFFER[name].append(msg)
            for q in list(LOG_QUEUES[name]):
                await q.put(msg)
            return
        async for line in proc.stdout:
            text = line.decode("utf-8", errors="replace").rstrip()
            msg = {"process": "build", "line": text}
            LOG_BUFFER[name].append(msg)
            for q in list(LOG_QUEUES[name]):
                await q.put(msg)
        await proc.wait()

    asyncio.create_task(_run_kill())
    return {"ok": True}


@app.websocket("/ws/logs/{name}")
async def ws_logs(websocket: WebSocket, name: str):
    await websocket.accept()
    q: asyncio.Queue = asyncio.Queue()
    LOG_QUEUES[name].append(q)
    try:
        # replay buffer
        for msg in list(LOG_BUFFER[name]):
            await websocket.send_json(msg)
        # stream new lines
        while True:
            msg = await q.get()
            await websocket.send_json(msg)
    except WebSocketDisconnect:
        pass
    finally:
        LOG_QUEUES[name].remove(q)


# Serve React build — must be LAST (catch-all)
if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def spa_fallback(full_path: str):
        return FileResponse(str(FRONTEND_DIST / "index.html"))
