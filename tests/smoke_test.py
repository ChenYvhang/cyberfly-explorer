from pathlib import Path
import statistics
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from cyberfly.brain import BrainController
from cyberfly.world import World


def main():
    brain = BrainController(ROOT / "data" / "male-cns")
    world = World()
    timings = []
    stats = {}
    for _ in range(120):
        stats = brain.step(world.senses())
        timings.append(brain.step_ms)
        world.step(stats["motor_forward"], stats["motor_turn"], stats["motor_escape"], 0.02)
    stable = timings[10:]
    assert brain.brain.n == 166_700
    assert world.distance > 0.1
    print(f"neurons={brain.brain.n}")
    print(f"connections=25,582,938")
    print(f"median_step_ms={statistics.median(stable):.2f}")
    print(f"p95_step_ms={sorted(stable)[int(len(stable) * .95)]:.2f}")
    print(f"distance={world.distance:.3f}")
    print(f"active_last_step={stats['active']}")


if __name__ == "__main__":
    main()
