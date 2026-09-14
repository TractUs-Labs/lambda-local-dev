"""Guards the real checked-in services.json (not a fixture).

services.json is the single source of truth: generate.py derives Procfile and
Makefile from it, dev.sh derives VALID_SERVICES from it, and server.py reads it
per-request. A malformed entry or a duplicated port breaks all three at once.
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
SERVICES_FILE = REPO_ROOT / "services.json"
REQUIRED_KEYS = {"name", "sam_port", "proxy_port", "function_name"}


def _services():
    return json.loads(SERVICES_FILE.read_text())["services"]


def test_every_service_has_required_keys():
    for svc in _services():
        missing = REQUIRED_KEYS - svc.keys()
        assert not missing, f"{svc.get('name', '<unnamed>')} is missing {missing}"


def test_sam_ports_are_unique():
    ports = [svc["sam_port"] for svc in _services()]
    assert len(ports) == len(set(ports)), f"duplicate sam_port in {ports}"


def test_proxy_ports_are_unique():
    ports = [svc["proxy_port"] for svc in _services()]
    assert len(ports) == len(set(ports)), f"duplicate proxy_port in {ports}"


def test_service_names_are_unique():
    names = [svc["name"] for svc in _services()]
    assert len(names) == len(set(names)), f"duplicate name in {names}"


def test_agent_core_is_registered():
    svc = next((s for s in _services() if s["name"] == "agent-core"), None)
    assert svc is not None, "agent-core is not registered in services.json"
    assert svc["sam_port"] == 3007
    assert svc["proxy_port"] == 8086
    assert svc["function_name"] == "FunctionImp"


def test_agent_core_forces_envtype_dev():
    """template.yaml gates the dev function on `Condition: IsDev`, and EnvType
    has no Default. Without this override the function does not exist locally.
    """
    svc = next(s for s in _services() if s["name"] == "agent-core")
    assert svc.get("sam_extra_args") == "--parameter-overrides EnvType=dev"


def test_ports_are_ints_in_valid_range():
    for svc in _services():
        for key in ("sam_port", "proxy_port"):
            port = svc[key]
            assert isinstance(port, int) and not isinstance(port, bool), (
                f"{svc['name']}.{key} must be an int, got {type(port).__name__} ({port!r})"
            )
            assert 1024 <= port <= 65535, (
                f"{svc['name']}.{key} = {port} is outside the valid port range 1024-65535"
            )


def test_generated_files_match_services_json(tmp_path):
    """Procfile and Makefile are generated from services.json by generate.py.

    Regenerates both files in a scratch copy of the repo and byte-compares
    them against what's checked in. If this fails, services.json was edited
    without regenerating the derived files -- run `python3 generate.py` from
    the repo root and commit the results.
    """
    shutil.copy(REPO_ROOT / "generate.py", tmp_path / "generate.py")
    shutil.copy(SERVICES_FILE, tmp_path / "services.json")

    result = subprocess.run(
        [sys.executable, "generate.py"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"generate.py failed: {result.stdout}\n{result.stderr}"

    for filename in ("Procfile", "Makefile"):
        generated = (tmp_path / filename).read_bytes()
        checked_in = (REPO_ROOT / filename).read_bytes()
        assert generated == checked_in, (
            f"{filename} is out of sync with services.json. "
            f"Run `python3 generate.py` from the repo root and commit the result."
        )
