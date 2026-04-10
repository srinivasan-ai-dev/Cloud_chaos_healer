# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.

"""
Cloud Chaos Healer Environment Implementation.

An AI agent acts as a Staff SRE to resolve infrastructure chaos.
Instead of just analyzing reports, the agent executes commands (actions)
that modify the state of a simulated microservice architecture.
3 tasks: easy -> medium -> hard.
"""

import random
import os
from uuid import uuid4
from typing import List, Optional, Dict
from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State

# Import pure-Python graders and scenarios (zero framework deps)
try:
    from .graders import (
        EASY_SCENARIOS, MEDIUM_SCENARIOS, HARD_SCENARIOS,
        grade_action
    )
except ImportError:
    from graders import (
        EASY_SCENARIOS, MEDIUM_SCENARIOS, HARD_SCENARIOS,
        grade_action
    )

try:
    from ..models import CcHealerAction, CcHealerObservation
except ImportError:
    from models import CcHealerAction, CcHealerObservation

# ── Environment Configuration ────────────────────────────────────────────────

TASK_ORDER = ["easy", "medium", "hard"]

class CcHealerEnvironment(Environment):
    """
    Cloud Chaos Healer Environment.
    Agents manage system health, latency, and operational budgets.
    """

    SUPPORTS_CONCURRENT_SESSIONS: bool = True

    def __init__(self):
        self._state = State(episode_id=str(uuid4()), step_count=0)
        self._total_reward = 0.0
        self._remaining_budget = 1000.0
        self._pick_scenarios()
        
        target_task = os.getenv("TASK_NAME")
        if target_task in TASK_ORDER:
            self._current_task_index = TASK_ORDER.index(target_task)
            self._is_single_task = True
        else:
            self._current_task_index = 0
            self._is_single_task = False

    def _pick_scenarios(self):
        """Pick random SRE failure scenarios for this episode."""
        self._scenarios = {
            "easy": random.choice(EASY_SCENARIOS),
            "medium": random.choice(MEDIUM_SCENARIOS),
            "hard": random.choice(HARD_SCENARIOS),
        }

    def reset(self, seed: Optional[int] = None, episode_id: Optional[str] = None, **kwargs) -> CcHealerObservation:
        self._state = State(episode_id=str(uuid4()), step_count=0)
        self._total_reward = 0.0
        self._remaining_budget = 1000.0
        self._pick_scenarios()

        # Phase 2 Strict Validator Support: Extract task_id from multiple possible entry points 
        target_task = os.getenv("TASK_NAME")
        options = kwargs.get("options", {})
        
        if options and isinstance(options, dict) and "task_name" in options:
            target_task = options["task_name"]
        elif "task_name" in kwargs:
            target_task = kwargs["task_name"]
        elif "task_id" in kwargs:
            target_task = kwargs["task_id"]

        if target_task in TASK_ORDER:
            self._current_task_index = TASK_ORDER.index(target_task)
            self._is_single_task = True
        else:
            self._current_task_index = 0
            self._is_single_task = False

        task_id = TASK_ORDER[self._current_task_index]
        scenario = self._scenarios[task_id]

        return CcHealerObservation(
            logs=scenario["logs"],
            system_status="CRITICAL" if task_id != "medium" else "WARNING",
            latency=scenario.get("latency", 25.0),
            remaining_budget=self._remaining_budget,
            task_id=task_id,
            done=False,
            reward=0.0,
        )

    def step(self, action: CcHealerAction) -> CcHealerObservation:
        if self._current_task_index >= len(TASK_ORDER):
            return self._empty_observation(True, "All systems operational.")

        self._state.step_count += 1
        current_task_id = TASK_ORDER[self._current_task_index]
        scenario = self._scenarios[current_task_id]

        # 1. Budget Logic: Every action has a cost 
        costs = {"restart_db": 150.0, "restart_api": 100.0, "scale_gateway": 50.0, "monitor": 5.0}
        self._remaining_budget -= costs.get(action.command, 10.0)

        # 2. Grading: Grade based on command precision
        reward = grade_action(current_task_id, action.command, scenario)
        self._total_reward += reward

        # 3. Termination Logic
        if self._is_single_task or self._remaining_budget <= 0:
            done = True
        else:
            self._current_task_index += 1
            done = self._current_task_index >= len(TASK_ORDER)

        if not done:
            next_task_id = TASK_ORDER[self._current_task_index]
            next_scenario = self._scenarios[next_task_id]
            return CcHealerObservation(
                logs=next_scenario["logs"],
                system_status="OK" if reward > 0.5 else "CRITICAL",
                latency=next_scenario.get("latency", 30.0),
                remaining_budget=self._remaining_budget,
                task_id=next_task_id,
                done=False,
                reward=reward,
            )
        else:
            return self._empty_observation(True, f"Evaluation complete. Budget: {self._remaining_budget}", reward)

    def _empty_observation(self, done: bool, feedback: str, reward: float = 0.0) -> CcHealerObservation:
        return CcHealerObservation(
            logs=feedback,
            system_status="OK",
            latency=0.0,
            remaining_budget=self._remaining_budget,
            task_id="complete",
            done=done,
            reward=reward,
        )

    @property
    def state(self) -> State:
        return self._state