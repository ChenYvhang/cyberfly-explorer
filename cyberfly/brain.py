from __future__ import annotations

from collections import deque
from pathlib import Path
import time

import numpy as np


class BrainController:
    """Adapter between world-scale sensor values and named MaleCNS neurons.

    The connectome is unchanged. Encoders and motor decoding are explicit model
    assumptions, kept here so experiments can audit or replace them.
    """

    def __init__(self, data_dir: Path):
        from flybrain import FlyBrain

        started = time.perf_counter()
        self.brain = FlyBrain(data=data_dir, device="cpu", sensory_input=False, seed=258)
        self.load_seconds = time.perf_counter() - started
        b = self.brain
        self.inputs = {
            "loom": b.cells(["LC4", "LPLC2"]),
            "target_L": b.cells(["LC10a"], side="L"),
            "target_R": b.cells(["LC10a"], side="R"),
            "food": b.cells(["ORN_DM1", "ORN_DM2"]),
        }
        self.outputs = {
            "steer_L": b.groups["steer_L"],
            "steer_R": b.groups["steer_R"],
            "forward": np.concatenate([b.groups["forward_L"], b.groups["forward_R"]]),
            "escape": np.concatenate([b.groups["escape_L"], b.groups["escape_R"]]),
            "backward": np.concatenate([b.groups["backward_L"], b.groups["backward_R"]]),
        }
        self.history = {name: deque([0] * 18, maxlen=18) for name in self.outputs}
        self.step_ms = 0.0

    def reset(self):
        self.brain.reset(seed=258)
        for hist in self.history.values():
            hist.clear()
            hist.extend([0] * 18)

    def step(self, senses: dict[str, float]) -> dict[str, float]:
        inject = []
        if senses["loom"] > 0.05:
            inject.append((self.inputs["loom"], 0.35 + 0.65 * senses["loom"]))
        # LC10a is used as the biologically named target-tracking channel.
        inject.append((self.inputs["target_L"], 0.18 + 0.72 * senses["food_left"]))
        inject.append((self.inputs["target_R"], 0.18 + 0.72 * senses["food_right"]))
        if senses["food_center"] > 0.08:
            inject.append((self.inputs["food"], 0.25 + 0.55 * senses["food_center"]))

        started = time.perf_counter()
        fired = self.brain.step(inject=inject)
        self.step_ms = (time.perf_counter() - started) * 1000
        fired_set = set(fired.tolist())
        for name, group in self.outputs.items():
            self.history[name].append(sum(int(i) in fired_set for i in group))

        rates = {name: sum(hist) / (len(hist) * self.brain.dt * max(1, len(self.outputs[name])))
                 for name, hist in self.history.items()}
        steer = np.clip((rates["steer_R"] - rates["steer_L"]) / 8.0, -1.0, 1.0)
        # Known connectome pathways reliably steer, but do not reliably initiate
        # DNg100 walking. A small documented locomotor drive keeps embodiment closed.
        forward = 0.32 + np.clip((rates["forward"] - rates["backward"]) / 10.0, -0.2, 0.68)
        escape = np.clip(rates["escape"] / 12.0, 0.0, 1.0)
        return {**rates, "motor_forward": float(forward), "motor_turn": float(steer),
                "motor_escape": float(escape), "active": len(fired)}

