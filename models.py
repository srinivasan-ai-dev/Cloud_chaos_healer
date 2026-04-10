# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
Data models for the Cloud Chaos Healer Environment.

An AI agent acts as a Staff SRE, receiving system logs and metrics.
The agent must execute specific healing commands to resolve outages 
while maintaining a strict operational budget.
"""

from typing import Optional, Dict, Any
from openenv.core.env_server.types import Action, Observation
from pydantic import Field


class CcHealerAction(Action):
    """
    The SRE command sent by the agent to heal the infrastructure [cite: 107-108].
    """

    command: str = Field(
        default="monitor", 
        description="SRE command: restart_db, restart_api, scale_gateway, or monitor"
    )


class CcHealerObservation(Observation):
    """
    The telemetry and system state provided to the AI agent [cite: 108-109].
    """

    logs: str = Field(
        default="", description="Real-time system logs and incident telemetry"
    )
    task_id: str = Field(
        default="", description="Current difficulty tier (easy/medium/hard)"
    )
    system_status: str = Field(
        default="OK", description="Current health status (OK/WARNING/CRITICAL)"
    )
    latency: float = Field(
        default=0.0, description="Measured system response time in milliseconds"
    )
    remaining_budget: float = Field(
        default=1000.0, description="Remaining credits for operational actions"
    )
    done: bool = Field(
        default=False, description="Whether the current chaos scenario is resolved"
    )
    reward: float = Field(
        default=0.0, description="Incremental reward for the last healing action"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional environment telemetry"
    )