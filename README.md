# tract-us-dev

Local development orchestration for tract-us-backend Lambda functions.

## Prerequisites

```bash
brew install overmind cloudflared aws-sam-cli
pip install flask requests
```

Docker must be running (required for `sam build --use-container`).

## Setup

```bash
cp .overmind.env.example .overmind.env
# Edit .overmind.env if your paths differ
```

## Workflow

### 1. Build (once, or after code changes)

```bash
make build-email-bot
make build-generate-contract
make build-all   # builds all 7
```

### 2. Start services

```bash
./dev.sh email-bot                              # single lambda
./dev.sh email-bot template-handler             # multiple lambdas
./dev.sh email-bot generate-contract utils      # any combination
./dev.sh --all                                  # all 7
```

### 3. Find your tunnel URL

Each service gets a temporary `trycloudflare.com` URL printed in its tunnel process log.

```bash
overmind connect email-bot-tunnel   # see the URL — Ctrl+b d to detach
```

### 4. Manage processes

```bash
./dev.sh restart email-bot          # restart SAM + proxy + tunnel (new tunnel URL)
./dev.sh restart email-bot --sam    # restart SAM only — keeps proxy, tunnel, and tunnel URL
overmind restart email-bot-proxy    # restart a single process
overmind connect email-bot-sam      # attach to a process terminal
overmind stop                       # stop everything
```

Dashboard Restart control: primary button restarts everything; the dropdown also offers **Restart SAM only**.

## Port Reference

| Lambda                | SAM port | Proxy port |
|-----------------------|----------|------------|
| email-bot             | 3001     | 8080       |
| template-handler      | 3002     | 8081       |
| generate-contract     | 3003     | 8082       |
| send-notification     | 3004     | 8083       |
| utils                 | 3005     | 8084       |
| metal-data-processing | 3006     | 8085       |
| agent-core            | 3007     | 8086       |

## Notes

- **metal-data-processing** requires an `env.json` in `functions/metal-data-processing/` before first use. Use `FunctionImpl` as the top-level key (not `FunctionImp`).
- Tunnel URLs are ephemeral — they change every time the tunnel process restarts. Use `./dev.sh restart <service> --sam` (or **Restart SAM only** in the UI) to reload Lambda code without rotating the URL.
- `.overmind.env` is gitignored (contains absolute paths).

## Adding a new lambda

`services.json` is the source of truth. `Procfile` and `Makefile` are generated
from it, and `dev.sh` reads its service list at runtime — never hand-edit those
three.

1. Add `template.yaml` and `env.json` to the lambda in `tract-us-backend`
   (copy `.env.example.json` to `env.json` and fill in the real values;
   `env.json` is git-ignored).
2. Add an entry to `services.json`: `name`, `sam_port`, `proxy_port`,
   `function_name` (the CloudFormation logical id in that function's
   `template.yaml`), and `sam_extra_args` if the template needs parameter
   overrides to resolve — e.g. when the function resource sits behind a
   `Condition` on a parameter with no default.
3. Assign the next free port pair (SAM `300N`, proxy `808N-1`).
4. Run `python3 generate.py` to rewrite `Procfile` and `Makefile`.
5. Run `python3 -m pytest tests/test_services_config.py` to check the entry.
6. Update the Port Reference table above, plus `PORTS.md` and `AGENTS.md`
   at the workspace root.
