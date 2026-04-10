#!/usr/bin/env python3
"""
Cloud Chaos Healer - Inference Script

STDOUT FORMAT (strictly compliant with Meta OpenEnv Phase 2 protocols):
    [START] task=<name> env=<benchmark> model=<model_name>
    [STEP]  step=<n> action=<str> reward=<0.00> done=<true|false> error=<msg|null>
    [END]   success=<true|false> steps=<n> score=<0.00> rewards=<r1,r2,...>
"""

import asyncio
import os
import textwrap
from typing import List, Optional
import httpx
from openai import OpenAI
import sys

# Ensure local modules are discoverable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from client import CcHealerEnv
from models import CcHealerAction

# ── Environment variables────────────────────────────────
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
HF_TOKEN = os.getenv("HF_TOKEN")
# Replace this with your actual Space URL once deployed
ENV_URL = os.getenv("ENV_URL", "https://srinivasan-ai-dev-cloud-chaos-healer.hf.space")

# ── Constants ────────────────────────────────────────────────────────────────
BENCHMARK = "cc_healer"
SUCCESS_SCORE_THRESHOLD = 0.5
TEMPERATURE = 0.0  # Mandatory for reproducible baseline
MAX_TOKENS = 128   # SRE commands should be concise

SYSTEM_PROMPT = textwrap.dedent("""
    You are an expert autonomous Site Reliability Engineer (SRE).
    You will receive logs and system metrics (latency, budget, status).
    Your job is to execute exactly ONE command to heal the system.
    Commands available: restart_db, restart_api, scale_gateway, monitor.
    Respond ONLY with the command name.
""").strip()

def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)

def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    error_val = error if error else "null"
    done_val = str(done).lower()
    print(
        f"[STEP] step={step} action={action} reward={reward:.2f} done={done_val} error={error_val}",
        flush=True,
    )

def log_end(task: str, success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(
        f"[END] task={task} success={str(success).lower()} steps={steps} score={score:.2f} rewards={rewards_str}",
        flush=True,
    )

def get_model_command(client: OpenAI, logs: str, task_id: str) -> str:
    """Uses the OpenAI client to get a healing command from the LLM"""
    user_prompt = f"TASK: {task_id}\nSYSTEM LOGS:\n{logs}\n\nDecision:"

    if not HF_TOKEN:
        return "monitor" # Default safe action if token is missing during init

    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
        )
        # Extract command and clean whitespace/newlines
        command = (completion.choices[0].message.content or "monitor").strip().lower()
        # Filter for valid action space
        valid_actions = ["restart_db", "restart_api", "scale_gateway", "monitor"]
        for action in valid_actions:
            if action in command:
                return action
        return "monitor"
    except Exception:
        return "monitor"

def run_task(env_client, llm_client, task_id: str):
    log_start(task=task_id, env=BENCHMARK, model=MODEL_NAME)
    rewards = []
    success = False
    score = 0.0
    
    try:
        # Reset environment for specific SRE scenario
        result = env_client.reset(task_id=task_id)
        obs = result.observation
        
        # Determine corrective action
        command = get_model_command(llm_client, obs.logs, obs.task_id)

        # Execute healing action in the environment
        result = env_client.step(CcHealerAction(command=command))
        reward = result.reward

        rewards.append(reward)
        log_step(step=1, action=command, reward=reward, done=True, error=None)

        # Calculate final score based on grader output 
        score = round(min(max(reward, 0.01), 0.99), 2)
        success = score >= SUCCESS_SCORE_THRESHOLD
        
    except Exception as e:
        score = 0.0
    finally:
        log_end(task=task_id, success=success, steps=1, score=score, rewards=rewards)

def main() -> None:
    import time
    
    target_task = os.getenv("TASK_NAME")
    tasks_to_run = [target_task] if target_task else ["easy", "medium", "hard"]
    
    # Initialize OpenAI client with mandatory HF_TOKEN
    llm_client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN or "dummy")

    # Exponential backoff to handle HF Space wake-up times
    max_env_retries = 5
    for attempt in range(max_env_retries):
        try:
            with CcHealerEnv(base_url=ENV_URL).sync() as env:
                for t in tasks_to_run:
                    run_task(env, llm_client, t)
            break
        except Exception as e:
            if attempt < max_env_retries - 1:
                time.sleep(15)
            else:
                sys.exit(0)

if __name__ == "__main__":
    main()