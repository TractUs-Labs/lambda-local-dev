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
make build-all   # builds all 6
```

### 2. Start services

```bash
./dev.sh email-bot                              # single lambda
./dev.sh email-bot template-handler             # multiple lambdas
./dev.sh email-bot generate-contract utils      # any combination
./dev.sh --all                                  # all 6
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

## Notes

- **metal-data-processing** requires an `env.json` in `functions/metal-data-processing/` before first use. Use `FunctionImpl` as the top-level key (not `FunctionImp`).
- Tunnel URLs are ephemeral — they change every time the tunnel process restarts. Use `./dev.sh restart <service> --sam` (or **Restart SAM only** in the UI) to reload Lambda code without rotating the URL.
- `.overmind.env` is gitignored (contains absolute paths).

## Adding a new lambda

1. Add `template.yaml` and `env.json` to the lambda in tract-us-backend
2. Add 3 entries to `Procfile` following the naming pattern
3. Add `build-<name>` target to `Makefile`
4. Register the service name in `dev.sh`'s `VALID_SERVICES` list
5. Assign the next available port pair (SAM: 300N, proxy: 808N-1)
