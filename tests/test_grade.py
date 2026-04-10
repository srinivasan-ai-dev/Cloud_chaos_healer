import pytest
import sys
import os

# Ensure the 'server' and 'tasks' packages are discoverable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tasks.graders import (
    grade_easy,
    grade_medium,
    grade_hard,
    EASY_SCENARIOS,
    MEDIUM_SCENARIOS,
    HARD_SCENARIOS,
)

def test_grade_easy():
    """Tests command precision for single-service failures."""
    scenario = EASY_SCENARIOS[0]  # db_failure scenario

    # 1. Correct Command Hit (restart_db)
    # The agent executes the specific healing action
    score1 = grade_easy("restart_db", scenario)
    assert score1 >= 0.90

    # 2. Irrelevant Action
    # Scaling the gateway doesn't fix a dead database pool
    score2 = grade_easy("scale_gateway", scenario)
    assert score2 < 0.20


def test_grade_medium():
    """Tests red-herring dismissal and throughput scaling."""
    scenario = MEDIUM_SCENARIOS[0]  # medium_latency scenario

    # 1. Correct Action (scaling capacity while ignoring network logs)
    score = grade_medium("scale_gateway", scenario)
    assert score >= 0.75

    # 2. Wrong Action (restarting API in response to gateway latency)
    score_wrong = grade_medium("restart_api", scenario)
    assert score_wrong <= 0.10


def test_grade_hard():
    """Tests critical path prioritization for cascading failures."""
    scenario = HARD_SCENARIOS[0]  # hard_cascade scenario

    # 1. Perfect Priority (restart_api is the first step in the cascade)
    score = grade_hard("restart_api", scenario)
    assert score >= 0.60

    # 2. Baseline Action (monitoring doesn't fix the crash but earns minimal points)
    score_min = grade_hard("monitor", scenario)
    assert 0.10 <= score_min <= 0.20