# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""Cloud Chaos Healer Environment Client."""

from typing import Dict

from openenv.core import EnvClient
from openenv.core.client_types import StepResult
from openenv.core.env_server.types import State

try:
    # Standard package import structure
    from .models import CcHealerAction, CcHealerObservation
except ImportError:
    # Fallback for direct script execution/validation 
    from models import CcHealerAction, CcHealerObservation


class CcHealerEnv(
    EnvClient[CcHealerAction, CcHealerObservation, State]
):
    """
    Client for the Cloud Chaos Healer Environment.

    Connects via WebSocket to the environment server to facilitate 
    low-latency SRE action loops . The agent monitors system 
    metrics and executes corrective commands to maintain uptime .

    Example:
        >>> with CcHealerEnv(base_url="http://localhost:8000") as client:
        ...     result = client.reset(task_id="medium")
        ...     print(result.observation.logs)
        ...     result = client.step(CcHealerAction(command="scale_gateway"))
        ...     print(f"Current Latency: {result.observation.latency}ms")
    """

    def _step_payload(self, action: CcHealerAction) -> Dict:
        """
        Convert CcHealerAction to JSON payload.
        Ensures the command field is correctly serialized for the server
        """
        return {
            "command": action.command,
        }

    def _parse_result(self, payload: Dict) -> StepResult[CcHealerObservation]:
        """
        Parse server response into CcHealerObservation.
        Maps real-world SRE metrics including budget and latency .
        """
        obs_data = payload.get("observation", {})
        observation = CcHealerObservation(
            logs=obs_data.get("logs", ""),
            system_status=obs_data.get("system_status", "UNKNOWN"),
            latency=obs_data.get("latency", 0.0),
            remaining_budget=obs_data.get("remaining_budget", 1000.0),
            task_id=obs_data.get("task_id", ""),
            done=payload.get("done", False),
            reward=payload.get("reward", 0.0),
        )
        return StepResult(
            observation=observation,
            reward=payload.get("reward", 0.0),
            done=payload.get("done", False),
        )

    def _parse_state(self, payload: Dict) -> State:
        """
        Parse server response into OpenEnv State.
        Tracks the episode progress across the 25 concurrent sessions allowed.
        """
        return State(
            episode_id=payload.get("episode_id"),
            step_count=payload.get("step_count", 0),
        )