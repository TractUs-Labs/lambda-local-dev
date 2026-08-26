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


def test_restart_sam_unknown_service_returns_404(monkeypatch, tmp_path):
    _setup_files(tmp_path, monkeypatch)
    import importlib, sys
    sys.modules.pop("server", None)
    import server
    importlib.reload(server)
    client = TestClient(server.app)
    resp = client.post("/api/services/nonexistent/restart-sam")
    assert resp.status_code == 404


@pytest.mark.anyio
async def test_restart_sam_only_preserves_tunnel_url(monkeypatch, tmp_path):
    _setup_files(tmp_path, monkeypatch)
    import importlib, sys
    sys.modules.pop("server", None)
    import server
    importlib.reload(server)

    class DummyProc:
        def __init__(self):
            self.returncode = None
            self.stdout = asyncio.StreamReader()

        def terminate(self):
            self.returncode = 0

        def kill(self):
            self.returncode = -9

        async def wait(self):
            return self.returncode

    old_sam = DummyProc()
    proxy = DummyProc()
    tunnel = DummyProc()
    server.PROCS["email-bot"] = {"sam": old_sam, "proxy": proxy, "tunnel": tunnel}
    server.TUNNEL_URLS["email-bot"] = "https://fixed.trycloudflare.com"

    new_sam = DummyProc()
    with patch("asyncio.create_subprocess_exec", new=AsyncMock(return_value=new_sam)):
        async with AsyncClient(transport=ASGITransport(app=server.app), base_url="http://test") as ac:
            resp = await ac.post("/api/services/email-bot/restart-sam")

    assert resp.status_code == 200
    assert resp.json()["ok"] is True
    assert server.PROCS["email-bot"]["sam"] is new_sam
    assert server.PROCS["email-bot"]["proxy"] is proxy
    assert server.PROCS["email-bot"]["tunnel"] is tunnel
    assert server.TUNNEL_URLS["email-bot"] == "https://fixed.trycloudflare.com"


@pytest.mark.anyio
async def test_restart_sam_only_falls_back_to_full_start(monkeypatch, tmp_path):
    _setup_files(tmp_path, monkeypatch)
    import importlib, sys
    sys.modules.pop("server", None)
    import server
    importlib.reload(server)

    with patch.object(server, "_stop_service", new=AsyncMock()) as stop_mock, patch.object(server, "_start_service", new=AsyncMock()) as start_mock:
        async with AsyncClient(transport=ASGITransport(app=server.app), base_url="http://test") as ac:
            resp = await ac.post("/api/services/email-bot/restart-sam")

    assert resp.status_code == 200
    assert resp.json()["ok"] is True
    assert "note" in resp.json()
    stop_mock.assert_awaited_once_with("email-bot")
    assert start_mock.await_count == 1

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
