import asyncio
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

def test_get_services_returns_list(tmp_path, monkeypatch):
    services_data = {
        "services": [
            {"name": "email-bot", "sam_port": 3001, "proxy_port": 8080, "function_name": "FunctionImp"},
            {"name": "utils", "sam_port": 3005, "proxy_port": 8084, "function_name": "FunctionImp"},
        ]
    }
    svc_file = tmp_path / "services.json"
    svc_file.write_text(json.dumps(services_data))

    env_file = tmp_path / ".overmind.env"
    env_file.write_text("BACKEND_PATH=/tmp/backend\nDEV_PATH=/tmp/dev\n")

    monkeypatch.chdir(tmp_path)
    import importlib, sys
    sys.modules.pop("server", None)
    import server
    importlib.reload(server)

    client = TestClient(server.app)
    resp = client.get("/api/services")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert data[0]["name"] == "email-bot"
    assert data[0]["sam_port"] == 3001
    assert data[0]["proxy_port"] == 8080
    assert data[0]["status"] == "stopped"
    assert data[0]["tunnel_url"] is None


def _setup_files(tmp_path, monkeypatch):
    services_data = {
        "services": [
            {"name": "email-bot", "sam_port": 3001, "proxy_port": 8080, "function_name": "FunctionImp"},
        ]
    }
    (tmp_path / "services.json").write_text(json.dumps(services_data))
    (tmp_path / ".overmind.env").write_text("BACKEND_PATH=/tmp/b\nDEV_PATH=/tmp/d\n")
    monkeypatch.chdir(tmp_path)


def test_stop_unknown_service_returns_404(monkeypatch, tmp_path):
    _setup_files(tmp_path, monkeypatch)
    import importlib, sys
    sys.modules.pop("server", None)
    import server
    importlib.reload(server)
    client = TestClient(server.app)
    resp = client.post("/api/services/nonexistent/stop")
    assert resp.status_code == 404


def test_start_unknown_service_returns_404(monkeypatch, tmp_path):
    _setup_files(tmp_path, monkeypatch)
    import importlib, sys
    sys.modules.pop("server", None)
    import server
    importlib.reload(server)
    client = TestClient(server.app)
    resp = client.post("/api/services/nonexistent/start")
    assert resp.status_code == 404


def test_build_unknown_service_returns_404(monkeypatch, tmp_path):
    _setup_files(tmp_path, monkeypatch)
    import importlib, sys
    sys.modules.pop("server", None)
    import server
    importlib.reload(server)
    client = TestClient(server.app)
    resp = client.post("/api/services/nonexistent/build")
    assert resp.status_code == 404

def test_websocket_log_replay(monkeypatch, tmp_path):
    _setup_files(tmp_path, monkeypatch)
    import importlib, sys
    sys.modules.pop("server", None)
    import server
    importlib.reload(server)
    # seed the buffer
    server.LOG_BUFFER["email-bot"].append({"process": "sam", "line": "hello"})
    client = TestClient(server.app)
    with client.websocket_connect("/ws/logs/email-bot") as ws:
        msg = ws.receive_json()
        assert msg == {"process": "sam", "line": "hello"}


def test_kill_ports_unknown_service_returns_404(monkeypatch, tmp_path):
    _setup_files(tmp_path, monkeypatch)
    import importlib, sys
    sys.modules.pop("server", None)
    import server
    importlib.reload(server)
    client = TestClient(server.app)
    resp = client.post("/api/services/nonexistent/kill-ports")
    assert resp.status_code == 404


def test_kill_ports_known_service_returns_ok(monkeypatch, tmp_path):
    _setup_files(tmp_path, monkeypatch)
    import importlib, sys
    sys.modules.pop("server", None)
    import server
    importlib.reload(server)

    async def async_lines():
        yield b"killed port 3001 8080\n"

    async def fake_exec(*args, **kwargs):
        mock_proc = AsyncMock()
        mock_proc.stdout = async_lines()
        mock_proc.wait = AsyncMock(return_value=0)
        return mock_proc

    with patch("asyncio.create_subprocess_exec", side_effect=fake_exec):
        client = TestClient(server.app)
        resp = client.post("/api/services/email-bot/kill-ports")
    assert resp.status_code == 200
    assert resp.json()["ok"] is True


@pytest.mark.anyio
async def test_kill_ports_logs_emitted(monkeypatch, tmp_path):
    _setup_files(tmp_path, monkeypatch)
    import importlib, sys
    sys.modules.pop("server", None)
    import server
    importlib.reload(server)

    async def async_lines():
        yield b"killed port 3001 8080\n"

    async def fake_exec(*args, **kwargs):
        mock_proc = AsyncMock()
        mock_proc.stdout = async_lines()
        mock_proc.wait = AsyncMock(return_value=0)
        return mock_proc

    with patch("asyncio.create_subprocess_exec", side_effect=fake_exec):
        async with AsyncClient(transport=ASGITransport(app=server.app), base_url="http://test") as ac:
            resp = await ac.post("/api/services/email-bot/kill-ports")
        await asyncio.sleep(0)  # drain inside the patch so the background task runs with the mock
    assert resp.status_code == 200
    assert {"process": "build", "line": "killed port 3001 8080"} in list(server.LOG_BUFFER["email-bot"])


def _reload_server(tmp_path, monkeypatch):
    _setup_files(tmp_path, monkeypatch)
    import importlib, sys
    sys.modules.pop("server", None)
    import server
    importlib.reload(server)
    return server


def test_restart_unknown_service_returns_404(monkeypatch, tmp_path):
    server = _reload_server(tmp_path, monkeypatch)
    client = TestClient(server.app)
    resp = client.post("/api/services/nonexistent/restart")
    assert resp.status_code == 404


def test_restart_invalid_scope_returns_400(monkeypatch, tmp_path):
    server = _reload_server(tmp_path, monkeypatch)
    client = TestClient(server.app)
    resp = client.post("/api/services/email-bot/restart?scope=proxy")
    assert resp.status_code == 400
    assert "Invalid scope" in resp.json()["error"]


def test_restart_sam_when_not_running_returns_409(monkeypatch, tmp_path):
    server = _reload_server(tmp_path, monkeypatch)
    client = TestClient(server.app)
    resp = client.post("/api/services/email-bot/restart?scope=sam")
    assert resp.status_code == 409
    assert "not running" in resp.json()["error"]


@pytest.mark.anyio
async def test_restart_all_default_scope(monkeypatch, tmp_path):
    server = _reload_server(tmp_path, monkeypatch)
    stop = AsyncMock()
    start = AsyncMock()
    monkeypatch.setattr(server, "_stop_service", stop)
    monkeypatch.setattr(server, "_start_service", start)

    async with AsyncClient(transport=ASGITransport(app=server.app), base_url="http://test") as ac:
        resp = await ac.post("/api/services/email-bot/restart")
    assert resp.status_code == 200
    assert resp.json() == {"ok": True, "scope": "all"}
    stop.assert_awaited_once_with("email-bot")
    start.assert_awaited_once()


@pytest.mark.anyio
async def test_restart_sam_preserves_tunnel_url(monkeypatch, tmp_path):
    server = _reload_server(tmp_path, monkeypatch)

    old_sam = MagicMock()
    old_sam.returncode = None
    old_sam.terminate = MagicMock()
    old_sam.wait = AsyncMock(return_value=0)
    old_sam.kill = MagicMock()

    proxy = MagicMock()
    proxy.returncode = None
    tunnel = MagicMock()
    tunnel.returncode = None

    server.PROCS["email-bot"] = {"sam": old_sam, "proxy": proxy, "tunnel": tunnel}
    server.TUNNEL_URLS["email-bot"] = "https://abc.trycloudflare.com"

    new_sam = MagicMock()
    new_sam.stdout = MagicMock()
    new_sam.stdout.readline = AsyncMock(return_value=b"")
    spawn = AsyncMock(return_value=new_sam)
    monkeypatch.setattr(server, "_spawn_sam", spawn)
    monkeypatch.setattr(server, "_stop_proc", AsyncMock())

    async with AsyncClient(transport=ASGITransport(app=server.app), base_url="http://test") as ac:
        resp = await ac.post("/api/services/email-bot/restart?scope=sam")
        await asyncio.sleep(0)

    assert resp.status_code == 200
    assert resp.json() == {"ok": True, "scope": "sam"}
    assert server.TUNNEL_URLS["email-bot"] == "https://abc.trycloudflare.com"
    assert server.PROCS["email-bot"]["proxy"] is proxy
    assert server.PROCS["email-bot"]["tunnel"] is tunnel
    assert server.PROCS["email-bot"]["sam"] is new_sam
    spawn.assert_awaited_once()
