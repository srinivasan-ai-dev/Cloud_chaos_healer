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