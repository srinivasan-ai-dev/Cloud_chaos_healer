# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
Pure-Python grader logic and SRE scenario definitions for Cloud Chaos Healer.
Zero external dependencies for instant import and deterministic testing.
"""

from typing import List, Dict

# ── Easy Scenarios: Single-System Failure ────────────────────────────────────

EASY_SCENARIOS: List[dict] = [
    {
        "id": "easy_db",
        "logs": "[ERROR] DatabaseConnectionPool: Pool exhausted (max_connections=100)\n[WARN] PaymentService: Upstream dependency unavailable",
        "expected_command": "restart_db",
        "keywords": ["database", "db", "pool", "exhausted", "restart"],
        "cost_penalty": 150.0
    },
    {
        "id": "easy_api",
        "logs": "[ERROR] APIService: JVM crashed (OutOfMemoryError)\n[WARN] Gateway: APIService returning 502 Bad Gateway",
        "expected_command": "restart_api",
        "keywords": ["api", "jvm", "memory", "oom", "restart"],
        "cost_penalty": 100.0
    }
]

# ── Medium Scenarios: Latency & Red Herrings ──────────────────────────────────

MEDIUM_SCENARIOS: List[dict] = [
    {
        "id": "medium_latency",
        "logs": "Signal A: Gateway Latency 8500ms\nSignal B: Network Load Normal (RED HERRING)\nSignal C: Gateway throughput at 95% limit",
        "expected_command": "scale_gateway",
        "root_cause_keywords": ["gateway", "throughput", "limit", "capacity", "scale"],
        "red_herring_keywords": ["network", "load", "bandwidth", "not the cause"],
        "cost_penalty": 50.0
    }
]

# ── Hard Scenarios: Cascading Outages ─────────────────────────────────────────

HARD_SCENARIOS: List[dict] = [
    {
        "id": "hard_cascade",
        "logs": "[FATAL] API V2: Auth Secret Mismatch\n[ERROR] DB: Deadlock due to API retry storm\n[WARN] Notification: Queue backlog 50k",
        "recovery_sequence": ["restart_api", "restart_db", "monitor"],
        "first_priority": "restart_api",
        "budget_limit": 1000.0
    }
]

# ── Grader Logic ─────────────────────────────────────────────────────────────

def safe_reward(raw: float) -> float:
    """Clamp reward between 0.01 and 0.99 for OpenEnv compliance"""
    return round(min(max(float(raw), 0.01), 0.99), 2)

def grade_action(task_id: str, action_command: str, scenario_data: Dict) -> float:
    """
    Primary programmatic grader for Cloud Chaos Healer actions.
    Evaluates command precision and SRE reasoning.
    """
    command = action_command.lower()
    score = 0.0

    if task_id == "easy":
        # Binary success: Did they use the right command?
        if command == scenario_data["expected_command"]:
            score = 0.90
        elif "monitor" in command:
            score = 0.20 # Small reward for telemetry
        
    elif task_id == "medium":
        # Precision + Red Herring avoidance
        if command == scenario_data["expected_command"]:
            score = 0.75
        elif "restart" in command:
            score = 0.10 # Penalty for over-reacting to symptoms
            
    elif task_id == "hard":
        # Recovery sequence prioritization
        if command == scenario_data["first_priority"]:
            score = 0.60 # Partial credit for the first critical step
        elif command == "monitor":
            score = 0.15
            
    return safe_reward(score)

# Fallback functions to match the structural imports in your app.py
def grade_easy(action_str: str, scenario: dict) -> float:
    return grade_action("easy", action_str, scenario)

def grade_medium(action_str: str, scenario: dict) -> float:
    return grade_action("medium", action_str, scenario)

def grade_hard(action_str: str, scenario: dict) -> float:
    return grade_action("hard", action_str, scenario)