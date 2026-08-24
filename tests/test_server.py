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
        for _ in range(100):
            if any(msg["line"] == "killed port 3001 8080" for msg in server.LOG_BUFFER["email-bot"]):
                break
            await asyncio.sleep(0.01)
    assert resp.status_code == 200


def test_restart_sam_nonexistent_service(monkeypatch, tmp_path):
    _setup_files(tmp_path, monkeypatch)
    import importlib, sys
    sys.modules.pop("server", None)
    import server
    importlib.reload(server)
    
    client = TestClient(server.app)
    resp = client.post("/services/nonexistent/restart-sam")
    assert resp.status_code == 404


def test_restart_sam_service_not_running(monkeypatch, tmp_path):
    _setup_files(tmp_path, monkeypatch)
    import importlib, sys
    sys.modules.pop("server", None)
    import server
    importlib.reload(server)
    
    client = TestClient(server.app)
    resp = client.post("/services/email-bot/restart-sam")
    assert resp.status_code == 400
    assert "not running" in resp.json()["error"]


@pytest.mark.anyio
async def test_restart_sam_successful(monkeypatch, tmp_path):
    _setup_files(tmp_path, monkeypatch)
    import importlib, sys
    sys.modules.pop("server", None)
    import server
    importlib.reload(server)

    # 1. Setup mock processes
    mock_sam_proc = AsyncMock()
    mock_sam_proc.returncode = None
    mock_sam_proc.wait = AsyncMock(return_value=0)
    mock_sam_proc.terminate = MagicMock()
    mock_sam_proc.kill = MagicMock()

    mock_proxy_proc = AsyncMock()
    mock_proxy_proc.returncode = None
    mock_proxy_proc.wait = AsyncMock(return_value=0)

    mock_tunnel_proc = AsyncMock()
    mock_tunnel_proc.returncode = None
    mock_tunnel_proc.wait = AsyncMock(return_value=0)

    # Store them in server.PROCS
    server.PROCS["email-bot"] = {
        "sam": mock_sam_proc,
        "proxy": mock_proxy_proc,
        "tunnel": mock_tunnel_proc,
    }
    server.TUNNEL_URLS["email-bot"] = "https://example-tunnel.trycloudflare.com"

    # 2. Mock create_subprocess_exec to return a new mock SAM process when restarted
    new_mock_sam_proc = AsyncMock()
    new_mock_sam_proc.returncode = None
    new_mock_sam_proc.stdout = AsyncMock()
    # To support readline in stream reader, we mock stdout
    async def fake_readline():
        return b""
    new_mock_sam_proc.stdout.readline = AsyncMock(side_effect=fake_readline)

    async def fake_exec(*args, **kwargs):
        return new_mock_sam_proc

    with patch("asyncio.create_subprocess_exec", side_effect=fake_exec) as mock_exec:
        async with AsyncClient(transport=ASGITransport(app=server.app), base_url="http://test") as ac:
            resp = await ac.post("/services/email-bot/restart-sam")
            
        assert resp.status_code == 200
        assert resp.json()["ok"] is True

        # Verify old SAM process was terminated/waited on
        mock_sam_proc.terminate.assert_called_once()
        mock_sam_proc.wait.assert_called_once()

        # Verify new SAM process was created and updated in server.PROCS
        assert server.PROCS["email-bot"]["sam"] is new_mock_sam_proc
        # Verify proxy and tunnel processes are unchanged (same mock objects)
        assert server.PROCS["email-bot"]["proxy"] is mock_proxy_proc
        assert server.PROCS["email-bot"]["tunnel"] is mock_tunnel_proc
        # Verify tunnel URL is still intact
        assert server.TUNNEL_URLS["email-bot"] == "https://example-tunnel.trycloudflare.com"
        
        # Verify create_subprocess_exec was called with 'sam' command
        called_args = mock_exec.call_args[0]
        assert "sam" in called_args


@pytest.mark.anyio
async def test_restart_sam_api_endpoint(monkeypatch, tmp_path):
    _setup_files(tmp_path, monkeypatch)
    import importlib, sys
    sys.modules.pop("server", None)
    import server
    importlib.reload(server)

    mock_sam_proc = AsyncMock()
    mock_sam_proc.returncode = None
    mock_sam_proc.wait = AsyncMock(return_value=0)
    mock_sam_proc.terminate = MagicMock()

    mock_proxy_proc = AsyncMock()
    mock_proxy_proc.returncode = None

    mock_tunnel_proc = AsyncMock()
    mock_tunnel_proc.returncode = None

    server.PROCS["email-bot"] = {
        "sam": mock_sam_proc,
        "proxy": mock_proxy_proc,
        "tunnel": mock_tunnel_proc,
    }
    server.TUNNEL_URLS["email-bot"] = "https://example-tunnel.trycloudflare.com"

    new_mock_sam_proc = AsyncMock()
    new_mock_sam_proc.returncode = None
    new_mock_sam_proc.stdout = AsyncMock()
    async def fake_readline():
        return b""
    new_mock_sam_proc.stdout.readline = AsyncMock(side_effect=fake_readline)

    async def fake_exec(*args, **kwargs):
        return new_mock_sam_proc

    with patch("asyncio.create_subprocess_exec", side_effect=fake_exec):
        async with AsyncClient(transport=ASGITransport(app=server.app), base_url="http://test") as ac:
            resp = await ac.post("/api/services/email-bot/restart-sam")
            
        assert resp.status_code == 200
        assert resp.json()["ok"] is True
        assert server.PROCS["email-bot"]["sam"] is new_mock_sam_proc


@pytest.mark.anyio
async def test_restart_sam_integration_pids_and_tunnel(monkeypatch, tmp_path):
    """
    Integration test proving that an HTTP POST to /services/{service_id}/restart-sam:
    1. Starts a service.
    2. Records the initial tunnel URL and PIDs of the 'sam' and 'proxy' processes.
    3. Calls the new /services/{service_id}/restart-sam endpoint.
    4. Asserts that the SAM process's PID changes, while the service's tunnel URL
       and proxy process PID remain unchanged.
    """
    _setup_files(tmp_path, monkeypatch)
    import importlib, sys
    sys.modules.pop("server", None)
    import server
    importlib.reload(server)

    mock_sam = AsyncMock()
    mock_sam.pid = 1234
    mock_sam.returncode = None
    mock_sam.stdout = AsyncMock()
    async def sam_readline():
        return b""
    mock_sam.stdout.readline = AsyncMock(side_effect=sam_readline)
    mock_sam.wait = AsyncMock(return_value=0)
    mock_sam.terminate = MagicMock()
    mock_sam.kill = MagicMock()

    mock_proxy = AsyncMock()
    mock_proxy.pid = 5678
    mock_proxy.returncode = None
    mock_proxy.stdout = AsyncMock()
    async def proxy_readline():
        return b""
    mock_proxy.stdout.readline = AsyncMock(side_effect=proxy_readline)
    mock_proxy.wait = AsyncMock(return_value=0)

    mock_tunnel = AsyncMock()
    mock_tunnel.pid = 9012
    mock_tunnel.returncode = None
    mock_tunnel.stdout = AsyncMock()
    tunnel_called = False
    async def tunnel_readline():
        nonlocal tunnel_called
        if not tunnel_called:
            tunnel_called = True
            return b"https://tunnel-xyz.trycloudflare.com\n"
        return b""
    mock_tunnel.stdout.readline = AsyncMock(side_effect=tunnel_readline)
    mock_tunnel.wait = AsyncMock(return_value=0)

    mock_sam_new = AsyncMock()
    mock_sam_new.pid = 9999
    mock_sam_new.returncode = None
    mock_sam_new.stdout = AsyncMock()
    async def sam_new_readline():
        return b""
    mock_sam_new.stdout.readline = AsyncMock(side_effect=sam_new_readline)
    mock_sam_new.wait = AsyncMock(return_value=0)
    mock_sam_new.terminate = MagicMock()
    mock_sam_new.kill = MagicMock()

    sam_count = 0
    async def fake_exec(*args, **kwargs):
        nonlocal sam_count
        cmd = args[0]
        if cmd == "sam":
            if sam_count == 0:
                sam_count += 1
                return mock_sam
            else:
                return mock_sam_new
        elif cmd == "python3":
            return mock_proxy
        elif cmd == "cloudflared":
            return mock_tunnel
        else:
            raise ValueError(f"Unexpected subprocess executable: {cmd}")

    with patch("asyncio.create_subprocess_exec", side_effect=fake_exec):
        async with AsyncClient(transport=ASGITransport(app=server.app), base_url="http://test") as ac:
            # 1. Start the service
            start_resp = await ac.post("/api/services/email-bot/start")
            assert start_resp.status_code == 200
            
            # Drain background tasks to allow tunnel stream reader to extract tunnel URL
            for _ in range(200):
                if server.TUNNEL_URLS.get("email-bot"):
                    break
                await asyncio.sleep(0.01)
            
            # 2. Record initial tunnel URL and PIDs
            initial_sam_pid = server.PROCS["email-bot"]["sam"].pid
            initial_proxy_pid = server.PROCS["email-bot"]["proxy"].pid
            initial_tunnel_url = server.TUNNEL_URLS.get("email-bot")
            
            assert initial_sam_pid == 1234
            assert initial_proxy_pid == 5678
            assert initial_tunnel_url == "https://tunnel-xyz.trycloudflare.com"

            # 3. Call the restart-sam endpoint
            restart_resp = await ac.post("/services/email-bot/restart-sam")
            assert restart_resp.status_code == 200
            assert restart_resp.json()["ok"] is True
            
            # Drain tasks
            await asyncio.sleep(0.01)
            
            # 4. Assert PIDs and tunnel URL behavior
            new_sam_pid = server.PROCS["email-bot"]["sam"].pid
            new_proxy_pid = server.PROCS["email-bot"]["proxy"].pid
            new_tunnel_url = server.TUNNEL_URLS.get("email-bot")
            
            assert new_sam_pid != initial_sam_pid
            assert new_sam_pid == 9999
            
            assert new_proxy_pid == initial_proxy_pid
            assert new_proxy_pid == 5678
            
            assert new_tunnel_url == initial_tunnel_url
            assert new_tunnel_url == "https://tunnel-xyz.trycloudflare.com"

            # Verify terminate was called on the old SAM process
            mock_sam.terminate.assert_called_once()
