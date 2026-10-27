"""Load test (Phase 7, decision D10): many people taking the age check at once.

The design's target (NFR-05): with 50 people sending face attempts concurrently, the server answers each attempt within
1.5 seconds at the 95th percentile, on 4 CPU cores. Each simulated person does what the verify page does: the shop's
server creates a session, the page starts the flow and asks for a challenge, then sends one face attempt of 8 frames.

Run it with `uv run tasks.py load` (see that task for the servers' settings); Locust prints and saves the timings.
"""

from __future__ import annotations

import json
import os
import uuid
from pathlib import Path

import requests
from locust import HttpUser, between, events, task
from locust.env import Environment

KEY = os.environ["DWARPAL_API_KEY"]
# A photo of a person (NASA's public-domain astronaut portrait, also used by the API's tests). The same image as every
# frame: the decision will likely ask for another try, but every step of the work is done, which is what is timed.
PORTRAIT = (Path(__file__).resolve().parents[2] / "libs/vision/tests/fixtures/astronaut.jpg").read_bytes()
FRAMES = 8
# The policy every check follows: 18+, at the risk budget the current age model is calibrated for (0.075). The presets
# ask for 0.02, which this model can't yet promise, so the API would refuse them.
POLICY = {"name": "loadtest_18", "min_age": 18, "risk_budget": 0.075}


@events.test_start.add_listener
def add_the_policy(environment: Environment, **_: object) -> None:
    """Once, before anyone starts: add (a new version of) the test's policy, as the website would."""
    response = requests.post(
        f"{environment.host}/v1/policies", json=POLICY, headers={"Authorization": f"Bearer {KEY}"}, timeout=10
    )
    response.raise_for_status()


class Person(HttpUser):
    """One person taking the check, again and again, with a pause of 1 to 3 seconds between checks."""

    wait_time = between(1, 3)

    @task
    def take_the_check(self) -> None:
        website = {"Authorization": f"Bearer {KEY}"}
        created = self.client.post(
            "/v1/verification-sessions", json={"policy": POLICY["name"]}, headers=website, name="1 create session"
        ).json()
        session = created["id"]
        # A fresh device ID per check, as a new visitor would have: the per-device budget is not what is tested here.
        device = {"X-Dwarpal-Device": uuid.uuid4().hex}
        started = self.client.post(
            f"/v1/flow/sessions/{session}/start",
            json={"client_secret": created["client_secret"]},
            headers=device,
            name="2 start flow",
        ).json()
        flow = {"Authorization": f"Bearer {started['flow_token']}", **device}
        challenge = self.client.post(f"/v1/flow/sessions/{session}/challenge", headers=flow, name="3 challenge").json()
        phases = ["baseline"] * (FRAMES - len(challenge["poses"])) + challenge["poses"]
        meta = {"frames": [{"index": i, "t_ms": i * 120.0, "phase": phase} for i, phase in enumerate(phases)]}
        files = {f"frame_{i}": (f"frame_{i}.jpg", PORTRAIT, "image/jpeg") for i in range(FRAMES)}
        form = {"meta": json.dumps(meta), "challenge_id": challenge["challenge_id"]}
        # An attempt only counts if it was really analysed. When the inference service is full it says so at once, and
        # the API fails safe ("analysis_unavailable", never a pass) — quick, but not a success.
        with self.client.post(
            f"/v1/flow/sessions/{session}/face-attempts",
            data=form,
            files=files,
            headers=flow,
            name="4 face attempt",
            catch_response=True,
        ) as response:
            if "analysis_unavailable" in response.json().get("reasons", []):
                response.failure("no analysis: the inference service was full")
