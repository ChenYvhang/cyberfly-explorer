from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from cyberfly.world import World


def main():
    world = World()
    peak = 0.0
    modes = set()
    for _ in range(800):
        _, _, bearing = world.nearest_food()
        world.step(0.72, max(-0.72, min(0.72, bearing * 0.85)), 0.0, 0.02)
        peak = max(peak, world.fly.altitude)
        modes.add(world.fly.flight_mode)

    assert peak > 1.4
    assert "takeoff" in modes and "cruise" in modes
    assert world.trail and len(world.trail[-1]) == 3
    print(f"peak_altitude={peak:.3f}")
    print(f"flight_modes={','.join(sorted(modes))}")
    print(f"trail_points={len(world.trail)}")


if __name__ == "__main__":
    main()
