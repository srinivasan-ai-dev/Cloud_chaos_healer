# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
FastAPI application for the Cloud Chaos Healer Environment.

This module creates an HTTP server that exposes the CcHealerEnvironment
over HTTP and WebSocket endpoints, compatible with EnvClient.
"""

try:
    from openenv.core.env_server.http_server import create_app
except Exception as e:  # pragma: no cover
    raise ImportError(
        "openenv is required for the web interface. Install dependencies with '\n    uv sync\n'"
    ) from e

import sys
import os

# Aligning pathing to ensure models and environment are discoverable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from models import CcHealerAction, CcHealerObservation
    from server.cloud_chaos_healer_environment import CcHealerEnvironment
except ImportError:
    from .cloud_chaos_healer_environment import CcHealerEnvironment
    try:
        from models import CcHealerAction, CcHealerObservation
    except ImportError:
        from ..models import CcHealerAction, CcHealerObservation
    
# Create the app with web interface and WebSocket support
app = create_app(
    CcHealerEnvironment,
    CcHealerAction,
    CcHealerObservation,
    env_name="cc_healer",
    max_concurrent_envs=25,  # Supporting rigorous multi-agent scoring 
)


# ── Root landing page — required for Hugging Face Space visibility ────────────
from fastapi.responses import HTMLResponse, RedirectResponse

@app.get("/", response_class=HTMLResponse, tags=["Web UI"], include_in_schema=False)
async def landing_page():
    """Serve a polished landing page for the Hugging Face Space."""
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Cloud Chaos Healer — SRE Environment</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
<style>
  *{margin:0;padding:0;box-sizing:border-box}
  body{font-family:'Inter',sans-serif;background:#0a0e1a;color:#e0e6f0;min-height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;overflow:hidden}
  .bg{position:fixed;inset:0;background:radial-gradient(ellipse at 30% 20%,rgba(56,189,248,.08),transparent 60%),radial-gradient(ellipse at 70% 80%,rgba(168,85,247,.08),transparent 60%);z-index:0}
  .container{position:relative;z-index:1;max-width:720px;padding:2rem;text-align:center}
  .badge{display:inline-block;padding:.35rem .9rem;border-radius:999px;background:rgba(56,189,248,.12);color:#38bdf8;font-size:.75rem;font-weight:600;letter-spacing:.06em;text-transform:uppercase;margin-bottom:1.5rem;border:1px solid rgba(56,189,248,.2)}
  h1{font-size:2.5rem;font-weight:700;background:linear-gradient(135deg,#38bdf8,#a855f7);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:.75rem}
  .subtitle{color:#94a3b8;font-size:1.05rem;line-height:1.6;margin-bottom:2.5rem}
  .cards{display:grid;grid-template-columns:repeat(3,1fr);gap:1rem;margin-bottom:2.5rem}
  .card{background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.06);border-radius:12px;padding:1.25rem .75rem;transition:transform .2s,border-color .2s}
  .card:hover{transform:translateY(-3px);border-color:rgba(56,189,248,.25)}
  .card .icon{font-size:1.8rem;margin-bottom:.5rem}
  .card .label{font-weight:600;font-size:.85rem;margin-bottom:.25rem}
  .card .desc{color:#64748b;font-size:.72rem;line-height:1.4}
  .actions{display:flex;gap:.75rem;justify-content:center;flex-wrap:wrap}
  .btn{padding:.65rem 1.5rem;border-radius:8px;font-size:.85rem;font-weight:600;text-decoration:none;transition:all .2s}
  .btn-primary{background:linear-gradient(135deg,#38bdf8,#a855f7);color:#fff}
  .btn-primary:hover{opacity:.9;transform:translateY(-1px)}
  .btn-secondary{background:rgba(255,255,255,.06);color:#94a3b8;border:1px solid rgba(255,255,255,.1)}
  .btn-secondary:hover{background:rgba(255,255,255,.1);color:#e0e6f0}
  .footer{margin-top:2.5rem;color:#475569;font-size:.72rem}
  @media(max-width:600px){.cards{grid-template-columns:1fr}h1{font-size:1.8rem}}
</style>
</head>
<body>
<div class="bg"></div>
<div class="container">
  <div class="badge">OpenEnv Environment</div>
  <h1>Cloud Chaos Healer</h1>
  <p class="subtitle">An autonomous SRE simulation where AI agents monitor system metrics and execute corrective commands to resolve infrastructure chaos while managing operational budgets.</p>
  <div class="cards">
    <div class="card"><div class="icon">🟢</div><div class="label">Easy</div><div class="desc">Single-service DB failure with clear log evidence</div></div>
    <div class="card"><div class="icon">🟡</div><div class="label">Medium</div><div class="desc">Gateway latency spike with red herring dismissal</div></div>
    <div class="card"><div class="icon">🔴</div><div class="label">Hard</div><div class="desc">Cascading P0 outage requiring prioritized recovery</div></div>
  </div>
  <div class="actions">
    <a href="/docs" class="btn btn-primary">API Documentation</a>
    <a href="/tasks" class="btn btn-secondary">View Tasks</a>
    <a href="/health" class="btn btn-secondary">Health Check</a>
  </div>
  <p class="footer">Powered by OpenEnv &bull; Meta Platforms</p>
</div>
</body>
</html>"""

@app.get("/web", include_in_schema=False)
async def web_redirect():
    """Redirect /web requests to the landing page."""
    return RedirectResponse(url="/")


# ── /tasks endpoint — required by Phase 2 deep validator ─────────────────────
# This discovers your mandatory 3 tasks and identifies the programmatic graders

@app.get("/tasks", tags=["Environment Info"], summary="List all tasks with graders")
async def list_tasks():
    """Return the list of available tasks, their difficulties, and grader info."""
    return [
        {
            "id": "easy",
            "name": "Single-Service DB Failure",
            "description": "Identify a database outage from system logs and execute a targeted 'restart_db' action.",
            "difficulty": "easy",
            "time_limit_seconds": 300,
            "max_steps": 5,
            "grader": "server.graders.grade_action",
            "action_schema": {
                "command": "Strategic SRE command: restart_db, restart_api, scale_gateway, or monitor."
            },
        },
        {
            "id": "medium",
            "name": "API Gateway Latency Spike",
            "description": "Diagnose high latency in the gateway layer and scale infrastructure to prevent timeouts.",
            "difficulty": "medium",
            "time_limit_seconds": 600,
            "max_steps": 10,
            "grader": "server.graders.grade_action",
            "action_schema": {
                "command": "Strategic SRE command: restart_db, restart_api, scale_gateway, or monitor."
            },
        },
        {
            "id": "hard",
            "name": "Cascading Infrastructure Failure",
            "description": "Manage a compound outage involving both API crashes and budget friction. Prioritize the critical path.",
            "difficulty": "hard",
            "time_limit_seconds": 900,
            "max_steps": 15,
            "grader": "server.graders.grade_action",
            "action_schema": {
                "command": "Strategic SRE command: restart_db, restart_api, scale_gateway, or monitor."
            },
        },
    ]


def main(host: str = "0.0.0.0", port: int = 8000):
    """
    Entry point for direct execution. Enables running without Docker for testing.
    """
    import uvicorn
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()