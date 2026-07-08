"""
Subprocess wrapper for `claude -p` (Claude Code CLI non-interactive mode).

Replaces the prior OpenCode HTTP client. Each call invokes the local Claude
Code CLI synchronously: it returns when the agent has finished. There is no
session, no polling, no auth token to manage — the CLI handles all of that.

Environment variables (loaded from periodic_jobs/ai_heartbeat/.env first,
then project-root .env):
    CLAUDE_BIN              Path to claude binary. Default: "claude".
    CLAUDE_DEFAULT_MODEL    Main-loop model id. Default: "claude-fable-5".
    CLAUDE_SUBAGENT_MODEL   Model for subagents spawned inside the claude
                            session (exported as CLAUDE_CODE_SUBAGENT_MODEL).
                            Default: "claude-opus-4-8".
    CLAUDE_PROJECT_ROOT     Working directory passed to claude. Default:
                            the repo root (4 levels above this file).
    CLAUDE_RUN_TIMEOUT      Subprocess timeout in seconds. Default: 7200.
    CLAUDE_SKIP_PERMISSIONS "1" to add --dangerously-skip-permissions (needed
                            for headless cron use). Default: "1".

For cron use, set absolute `CLAUDE_BIN` in the crontab env or in
periodic_jobs/ai_heartbeat/.env. `which claude` gives the path.
"""

import os
import subprocess
from pathlib import Path
from typing import Optional

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

_module_dir = Path(__file__).resolve().parent
_local_env = _module_dir.parents[1] / ".env"
_repo_env = _module_dir.parents[3] / ".env"
if load_dotenv is not None:
    if _repo_env.exists():
        load_dotenv(_repo_env)
    if _local_env.exists():
        load_dotenv(_local_env, override=True)

DEFAULT_BIN = os.getenv("CLAUDE_BIN", "claude")
DEFAULT_MODEL = os.getenv("CLAUDE_DEFAULT_MODEL", "claude-fable-5")
DEFAULT_SUBAGENT_MODEL = os.getenv("CLAUDE_SUBAGENT_MODEL", "claude-opus-4-8")
DEFAULT_CWD = os.getenv("CLAUDE_PROJECT_ROOT") or str(_module_dir.parents[3])
DEFAULT_TIMEOUT = int(os.getenv("CLAUDE_RUN_TIMEOUT", "7200"))
SKIP_PERMISSIONS = os.getenv("CLAUDE_SKIP_PERMISSIONS", "1") == "1"


def _normalize_model(model_id: str) -> str:
    # OpenCode used 'anthropic/claude-opus-4-6'; claude CLI takes the bare id.
    if "/" in model_id:
        return model_id.split("/", 1)[1]
    return model_id


def run_claude(
    prompt: str,
    model_id: str = DEFAULT_MODEL,
    cwd: Optional[str] = None,
    timeout: int = DEFAULT_TIMEOUT,
    skip_permissions: bool = SKIP_PERMISSIONS,
    extra_args: Optional[list] = None,
) -> Optional[str]:
    """Run `claude -p PROMPT --model MODEL` synchronously.

    Returns stdout text on success, None on failure (timeout, non-zero exit,
    binary not found). The caller is responsible for logging / retry policy.
    """
    model = _normalize_model(model_id)
    cmd = [DEFAULT_BIN, "-p", prompt, "--model", model]
    if skip_permissions:
        cmd.append("--dangerously-skip-permissions")
    if extra_args:
        cmd.extend(extra_args)

    env = os.environ.copy()
    env.setdefault("CLAUDE_CODE_SUBAGENT_MODEL", DEFAULT_SUBAGENT_MODEL)

    try:
        proc = subprocess.run(
            cmd,
            cwd=cwd or DEFAULT_CWD,
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except FileNotFoundError:
        print(f"claude CLI not found at {DEFAULT_BIN!r}. Install it or set CLAUDE_BIN.")
        return None
    except subprocess.TimeoutExpired:
        print(f"claude -p timed out after {timeout}s.")
        return None

    if proc.returncode != 0:
        print(f"claude -p exited with code {proc.returncode}.")
        if proc.stderr:
            print(f"stderr: {proc.stderr[:1000]}")
        return None
    return proc.stdout
