---
title: Cloud Chaos Healer
emoji: "☁️"
colorFrom: blue
colorTo: gray
sdk: docker
app_port: 7860
license: mit
base_path: /web
tags:
  - openenv
  - sre
  - chaos-engineering
  - reinforcement-learning
  - real-world
short_description: Active SRE Healing & Infrastructure Remediation Env
---

> [!NOTE]
> This is a verified Phase 2 deep-validation submission for the **Meta × HuggingFace × Scaler OpenEnv Hackathon 2026**.

> [!TIP]
> A live deployed version of this environment is available at: **https://srinivasan-ai-dev-cloud-chaos-healer.hf.space**

# ☁️ Cloud Chaos Healer (CCH)

An autonomous Site Reliability Engineering (SRE) Reinforcement Learning environment where AI agents don't just "talk" about outages—they resolve them.

```mermaid
xychart-beta
    title "SRE Healing Success Leaderboard (Action-Based)"
    x-axis ["Llama-3.3-70B", "Qwen-72B", "Gemma-2-27B", "Hermes-3-8B", "Mistral-Nemo"]
    y-axis "Healing Success Rate" 0.00 --> 1.00
    bar [0.88, 0.81, 0.45, 0.30, 0.22]
```

Production downtime costs organizations millions. Cloud Chaos Healer evaluates if an LLM can act as a Staff SRE by monitoring system metrics (latency, budget) and executing critical commands like `restart_db` or `scale_gateway` to restore system health in real-time.

## Quick Start

The simplest way to interact with the healing environment via python:

```python
import asyncio
from client import CcHealerEnv
from models import CcHealerAction

async def main():
    try:
        # Connect to the live Cloud Chaos Healer Space
        env = await CcHealerEnv(base_url="[https://srinivasan-ai-dev-cloud-chaos-healer.hf.space](https://srinivasan-ai-dev-cloud-chaos-healer.hf.space)")

        # Reset the environment to an active outage scenario
        result = await env.reset(task_id="medium")
        obs = result.observation
        
        print(f"STATUS: {obs.system_status} | LATENCY: {obs.latency}ms")
        print(f"LOGS: {obs.logs}")

        # Step — Execute a corrective SRE command
        action = CcHealerAction(command="scale_gateway")
        result = await env.step(action)
        
        print(f"\nAction: scale_gateway | Reward: {result.reward:.2f}")
        print(f"New Budget: {result.observation.remaining_budget}")

    finally:
        await env.close()

asyncio.run(main())
```

---

## 💡 Why This Problem?
Standard LLM benchmarks focus on static triage. Cloud Chaos Healer moves to **Agentic Execution**:
- **Resource Constraints** — Agents must resolve chaos while managing a strictly limited **Operational Budget**.
- **Latency Management** — Rewards are tied to keeping response times below 100ms, simulating real-world user experience.
- **Active State Change** — Every action (`restart`, `scale`) directly modifies the environment's health status.

---

## 🚀 Try It Now (No Setup Required)
CCH exposes standard OpenEnv endpoints natively on HuggingFace Spaces.

```bash
# Health check
curl -X GET [https://srinivasan-ai-dev-cloud-chaos-healer.hf.space/health](https://srinivasan-ai-dev-cloud-chaos-healer.hf.space/health)

# Discover available SRE tasks
curl -X GET [https://srinivasan-ai-dev-cloud-chaos-healer.hf.space/tasks](https://srinivasan-ai-dev-cloud-chaos-healer.hf.space/tasks)

# Start a specific Chaos Scenario
curl -X POST [https://srinivasan-ai-dev-cloud-chaos-healer.hf.space/reset](https://srinivasan-ai-dev-cloud-chaos-healer.hf.space/reset) \
     -H "Content-Type: application/json" \
     -d '{"task_id": "medium"}'

# Execute a Healing Action
curl -X POST [https://srinivasan-ai-dev-cloud-chaos-healer.hf.space/step](https://srinivasan-ai-dev-cloud-chaos-healer.hf.space/step) \
     -H "Content-Type: application/json" \
     -d '{"action": {"command": "restart_db"}}'
```

---

## Agent Loop Architecture

```mermaid
flowchart TD
    classDef config fill:#1f2937,stroke:#6b7280,color:#f9fafb
    classDef env   fill:#064e3b,stroke:#059669,color:#ecfdf5
    classDef obs   fill:#1e3a5f,stroke:#3b82f6,color:#dbeafe
    classDef agent fill:#3b0764,stroke:#9333ea,color:#f3e8ff
    classDef step  fill:#78350f,stroke:#f59e0b,color:#fef3c7
    classDef score fill:#14532d,stroke:#4ade80,color:#bbf7d0

    CFG["⚙️ Task Config\ntask_id = easy | med | hard"]:::config
    CFG -->|"env.reset()"| ENV["⚡ CcHealerEnvironment\nActive State Simulation"]:::env
    ENV --> OBS["📡 Observation\n• Status (OK/CRITICAL)\n• Latency Metric\n• Budget State"]:::obs
    OBS -->|"system_logs"| AGT["🤖 Agentic LLM\n(Autonomous SRE)"]:::agent
    AGT -->|"CcHealerAction"| STEP["⚡ Action → env.step()\nCommand: scale | restart | monitor"]:::step
    STEP --> SCORE["🏁 State-Based Grader\nReward based on Budget & Health"]:::score
```

---

## Tasks & Scenarios

The environment evaluates agents across 3 tiers, with rotating failure scenarios to prevent hard-coding.

| Task ID | Difficulty | Active Challenge | Core Competency Evaluated |
|---------|------------|------------------|---------------------------|
| `easy` | 🟢 P2 Incident | DB Failure | Identifying explicit failures and executing targeted restarts. |
| `medium` | 🟡 P1 Incident | Latency Spike | Managing gateway throughput while ignoring red-herring network logs. |
| `hard` | 🔴 P0 Outage | Cascading Crash | Resolving auth-driven cascading failures under tight budget constraints. |

---

## Action & Observation Spaces

### Action: `CcHealerAction`

| Field | Type | Description |
|-------|------|-------------|
| `command` | `str` | The SRE command to execute (`restart_db`, `restart_api`, `scale_gateway`, `monitor`). |

###Observation: `CcHealerObservation`

| Field | Type | Description |
|-------|------|-------------|
| `logs` | `str` | Real-time system logs and incident telemetry. |
| `system_status`| `str` | Health status (OK, WARNING, CRITICAL). |
| `latency` | `float` | Current response time in ms. |
| `remaining_budget`| `float` | Credits left for operational actions. |
| `reward` | `float` | Normalized reward score (`0.00` – `1.00`). |

---

## Reward Evaluation (State-Based Logic)

Grading is strictly deterministic, rewarding system recovery while penalizing resource waste.

- **Accuracy**: Correct healing commands receive high baseline rewards (0.80+).
- **Efficiency**: Every action deducts from the 1000.0 budget. Agents that "spam" restarts are penalized.
- **Stability**: Maintaining "OK" status throughout the episode generates incremental rewards.

---

## Baseline Inference Scores

Evaluation executed via `evaluate_models.py` using `Llama-3.3-70B` and `Qwen2.5-72B`.

| Tier | Task | Max Steps | Mean Score | Max |
|---|---|---|---|---|
| **Easy** | `easy` | 5 | 0.95 | 0.95 |
| **Medium** | `medium` | 10 | 0.65 | 0.85 |
| **Hard** | `hard` | 15 | 0.45 | 0.70 |
| **OVERALL** | — | — | **0.68** | **0.83** |

```bash
# Run the automated baseline check
python evaluate_models.py
```

---

## Deployment & Setup

### Local Run
```bash
git clone [https://github.com/Srinivasan-V/Cloud-Chaos-Healer.git](https://github.com/Srinivasan-V/Cloud-Chaos-Healer.git)
cd Cloud-Chaos-Healer
uv sync
uvicorn server.app:app --reload --host 0.0.0.0 --port 7860
```

### Docker
```bash
docker build -t cc_healer:latest .
docker run -p 7860:7860 cc_healer:latest
```

---

## Citation

```bibtex
@software{cchealer2026,
  title   = {Cloud Chaos Healer: Autonomous Infrastructure Remediation Environment},
  author  = {Srinivasan V},
  year    = {2026},
  url     = {[https://huggingface.co/spaces/srinivasan-ai-dev/cloud-chaos-healer](https://huggingface.co/spaces/srinivasan-ai-dev/cloud-chaos-healer)},
  note    = {Action-based RL environment for automated SRE operations}
}
```
```
