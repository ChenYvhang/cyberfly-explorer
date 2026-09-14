from __future__ import annotations

import argparse
import math
from pathlib import Path
import random
import sys
import threading
import time

import pygame

from cyberfly.world import World
from cyberfly.render import Renderer


class PreviewBrain:
    """Fast visual preview; --brain switches to the complete MaleCNS model."""
    def __init__(self):
        self.phase = 0.0
        self.step_ms = 0.0

    def reset(self):
        self.phase = 0.0

    def step(self, senses):
        self.phase += 0.08
        avoidance = senses["wall_right"] - senses["wall_left"]
        target = senses["food_right"] - senses["food_left"]
        turn = target * 1.6 + avoidance * 2.2 + math.sin(self.phase) * 0.11
        return {"steer_L": max(0.0, -turn * 5), "steer_R": max(0.0, turn * 5),
                "forward": 2.0, "backward": 0.0, "escape": senses["loom"] * 12,
                "motor_forward": 0.55, "motor_turn": turn, "motor_escape": senses["loom"],
                "active": random.randint(300, 900)}


class BrainWorker:
    """Runs the expensive full-connectome step away from the render loop."""
    def __init__(self, controller, senses):
        self.controller = controller
        self._senses = dict(senses)
        self._stats = {"active": 0, "motor_forward": 0.32, "motor_turn": 0.0,
                       "motor_escape": 0.0, "step_ms": 0.0}
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._reset = threading.Event()
        self.thread = threading.Thread(target=self._run, name="MaleCNS", daemon=True)
        self.thread.start()

    def _run(self):
        deadline = time.perf_counter()
        while not self._stop.is_set():
            if self._reset.is_set():
                self.controller.reset()
                self._reset.clear()
            with self._lock:
                senses = dict(self._senses)
            stats = self.controller.step(senses)
            stats["step_ms"] = self.controller.step_ms
            with self._lock:
                self._stats = stats
            deadline += 0.02
            self._stop.wait(max(0.0, deadline - time.perf_counter()))
            if time.perf_counter() - deadline > 0.2:
                deadline = time.perf_counter()

    def update_senses(self, senses):
        with self._lock:
            self._senses = dict(senses)

    def stats(self):
        with self._lock:
            return dict(self._stats)

    def reset(self):
        self._reset.set()

    def close(self):
        self._stop.set()
        self.thread.join(timeout=2.0)


def main():
    parser = argparse.ArgumentParser(description="A MaleCNS cyberfly explores a lightweight 3D world")
    parser.add_argument("--brain", action="store_true", help="run the complete 166,700-neuron MaleCNS brain")
    parser.add_argument("--data", type=Path, default=Path(__file__).parent / "data" / "male-cns")
    args = parser.parse_args()

    pygame.init()
    screen = pygame.display.set_mode((1180, 700))
    pygame.display.set_caption("Cyberfly Explorer")
    world = World()
    map_path = Path(__file__).parent / "maps" / "custom_map.json"
    if map_path.exists():
        try:
            world.load(map_path)
        except (OSError, ValueError, KeyError):
            pass
    renderer = Renderer(screen, world)
    if args.brain:
        from cyberfly.brain import BrainController
        brain = BrainController(args.data)
        worker = BrainWorker(brain, world.senses())
    else:
        brain = PreviewBrain()
        worker = None

    clock = pygame.time.Clock()
    paused = False
    edit_mode = False
    editor_tool = "wall"
    editor_notice = ""
    editor_notice_until = 0.0
    stats = {"active": 0}
    running = True
    last = time.perf_counter()
    while running:
        now = time.perf_counter()
        frame_dt = min(0.08, now - last)
        last = now
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                if not edit_mode:
                    paused = not paused
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                if not edit_mode:
                    world.reset()
                    (worker or brain).reset()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_e:
                edit_mode = not edit_mode
                paused = edit_mode
                editor_notice = "Editing paused the simulation" if edit_mode else ""
            elif edit_mode and event.type == pygame.KEYDOWN and pygame.K_1 <= event.key <= pygame.K_8:
                editor_tool = renderer.TOOLS[event.key - pygame.K_1]
            elif edit_mode and event.type == pygame.KEYDOWN and event.key == pygame.K_s:
                world.save(map_path)
                editor_notice, editor_notice_until = "Saved: maps/custom_map.json", time.time() + 3
            elif edit_mode and event.type == pygame.KEYDOWN and event.key == pygame.K_l:
                if map_path.exists():
                    try:
                        world.load(map_path)
                        editor_notice = "Saved map reloaded"
                    except (OSError, ValueError, KeyError) as exc:
                        editor_notice = f"Could not load map: {exc}"
                else:
                    editor_notice = "No saved map yet"
                editor_notice_until = time.time() + 3
            elif edit_mode and event.type == pygame.KEYDOWN and event.key == pygame.K_d:
                world.reset()
                editor_notice, editor_notice_until = "Default map restored (not saved)", time.time() + 3
            elif edit_mode and event.type == pygame.MOUSEBUTTONDOWN:
                cell = renderer.editor_cell_at(event.pos)
                if cell:
                    world.paint(*cell, editor_tool if event.button == 1 else "floor")
        senses = world.senses()
        if not paused and not edit_mode:
            if worker:
                worker.update_senses(senses)
                stats = worker.stats()
                world.step(stats["motor_forward"], stats["motor_turn"], stats["motor_escape"], frame_dt)
            else:
                stats = brain.step(senses)
                stats["step_ms"] = brain.step_ms
                world.step(stats["motor_forward"], stats["motor_turn"], stats["motor_escape"], frame_dt)
            senses = world.senses()
        if edit_mode:
            if editor_notice_until and time.time() > editor_notice_until:
                editor_notice = ""
            renderer.draw_editor(editor_tool, editor_notice)
        else:
            renderer.draw(stats, senses, paused, args.brain)
        clock.tick(60)
    if worker:
        worker.close()
    pygame.quit()
    return 0


if __name__ == "__main__":
    sys.exit(main())
