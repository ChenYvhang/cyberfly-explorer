from __future__ import annotations

import math
import json
from dataclasses import dataclass
from pathlib import Path


MAP = (
    "########################",
    "#......................#",
    "#..####..........###...#",
    "#..#.............#.....#",
    "#..#....####.....#.....#",
    "#.......#........#.....#",
    "#.......#..............#",
    "#.####..#....#####.....#",
    "#.......#..............#",
    "#............###.......#",
    "#..#####...............#",
    "#..............####....#",
    "#......###.............#",
    "#......#...............#",
    "#..##..#....#####......#",
    "#..##..................#",
    "#..........###.........#",
    "#......................#",
    "#......................#",
    "########################",
)


@dataclass
class Food:
    x: float
    y: float
    radius: float = 0.28


@dataclass
class Decor:
    kind: str
    x: float
    y: float
    radius: float
    height: float = 0.5
    solid: bool = True


@dataclass
class Fly:
    x: float = 2.5
    y: float = 2.5
    heading: float = 0.25
    speed: float = 0.0
    energy: float = 1.0
    foods_found: int = 0
    state: str = "exploring"
    feeding_time: float = 0.0
    altitude: float = 0.0
    vertical_speed: float = 0.0
    pitch: float = 0.0
    roll: float = 0.0
    flight_mode: str = "ground"
    flight_enabled: bool = True
    flight_time: float = 0.0


class World:
    def __init__(self):
        self.grid = [list(row) for row in MAP]
        self.width = len(MAP[0])
        self.height = len(MAP)
        self.fly = Fly()
        self.foods = [Food(21.0, 2.0), Food(13.5, 6.0), Food(20.5, 14.0),
                      Food(4.5, 17.2), Food(11.2, 17.0)]
        self.decor = [
            Decor("rock", 6.2, 2.4, 0.34, 0.46), Decor("rock", 18.7, 5.4, 0.42, 0.60),
            Decor("rock", 12.4, 10.5, 0.30, 0.38), Decor("rock", 5.2, 13.0, 0.40, 0.52),
            Decor("stump", 10.3, 3.2, 0.34, 0.60), Decor("stump", 18.0, 16.2, 0.38, 0.68),
            Decor("plant", 2.0, 6.0, 0.27, 0.72), Decor("plant", 14.5, 3.0, 0.27, 0.82),
            Decor("plant", 21.2, 8.4, 0.28, 0.76), Decor("plant", 8.8, 15.2, 0.27, 0.78),
            Decor("plant", 15.5, 17.3, 0.26, 0.72),
            Decor("puddle", 10.8, 8.4, 0.70, 0.01, False),
            Decor("puddle", 19.0, 11.0, 0.82, 0.01, False),
            Decor("puddle", 3.3, 16.8, 0.58, 0.01, False),
        ]
        self.trail: list[tuple[float, float, float]] = []
        self.distance = 0.0
        self.time = 0.0

    def reset(self):
        self.__init__()

    def clear_cell(self, gx: int, gy: int):
        self.decor = [o for o in self.decor if int(o.x) != gx or int(o.y) != gy]
        self.foods = [o for o in self.foods if int(o.x) != gx or int(o.y) != gy]

    def paint(self, gx: int, gy: int, tool: str):
        if not (0 <= gx < self.width and 0 <= gy < self.height):
            return
        if gx in (0, self.width - 1) or gy in (0, self.height - 1):
            return
        if int(self.fly.x) == gx and int(self.fly.y) == gy and tool not in ("spawn", "floor"):
            return
        self.clear_cell(gx, gy)
        cx, cy = gx + 0.5, gy + 0.5
        if tool == "wall":
            self.grid[gy][gx] = "#"
        else:
            self.grid[gy][gx] = "."
        specs = {
            "rock": (0.34, 0.48, True), "plant": (0.27, 0.76, True),
            "stump": (0.34, 0.62, True), "puddle": (0.65, 0.01, False),
        }
        if tool in specs:
            radius, height, solid = specs[tool]
            self.decor.append(Decor(tool, cx, cy, radius, height, solid))
        elif tool == "food":
            self.foods.append(Food(cx, cy))
        elif tool == "spawn":
            self.fly.x, self.fly.y = cx, cy
            self.trail.clear()

    def save(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "grid": ["".join(row) for row in self.grid],
            "spawn": [self.fly.x, self.fly.y, self.fly.heading],
            "foods": [vars(x) for x in self.foods],
            "decor": [vars(x) for x in self.decor],
        }
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def load(self, path: Path):
        payload = json.loads(path.read_text(encoding="utf-8"))
        rows = payload["grid"]
        if len(rows) < 5 or len({len(row) for row in rows}) != 1:
            raise ValueError("invalid map dimensions")
        self.grid = [list(row) for row in rows]
        self.height, self.width = len(self.grid), len(self.grid[0])
        sx, sy, heading = payload["spawn"]
        self.fly = Fly(float(sx), float(sy), float(heading))
        self.foods = [Food(**item) for item in payload.get("foods", [])]
        self.decor = [Decor(**item) for item in payload.get("decor", [])]
        self.trail.clear()
        self.distance = self.time = 0.0

    def grid_wall(self, x: float, y: float) -> bool:
        ix, iy = int(x), int(y)
        return iy < 0 or iy >= self.height or ix < 0 or ix >= self.width or self.grid[iy][ix] == "#"

    def wall(self, x: float, y: float) -> bool:
        if self.grid_wall(x, y):
            return True
        return any(obj.solid and math.hypot(x - obj.x, y - obj.y) < obj.radius for obj in self.decor)

    def air_obstacle(self, x: float, y: float, altitude: float) -> bool:
        ix, iy = int(x), int(y)
        if iy < 0 or iy >= self.height or ix < 0 or ix >= self.width:
            return True
        if self.grid[iy][ix] == "#" and altitude < 0.65:
            return True
        return any(
            obj.solid and altitude < obj.height + 0.28
            and math.hypot(x - obj.x, y - obj.y) < obj.radius + 0.18
            for obj in self.decor
        )

    def ray_distance(self, angle: float, max_distance: float = 6.0) -> float:
        step = 0.045
        d = 0.08
        while d < max_distance:
            if self.wall(self.fly.x + math.cos(angle) * d, self.fly.y + math.sin(angle) * d):
                return d
            d += step
        return max_distance

    def nearest_food(self) -> tuple[Food | None, float, float]:
        if not self.foods:
            return None, 99.0, 0.0
        food = min(self.foods, key=lambda f: math.hypot(f.x - self.fly.x, f.y - self.fly.y))
        dist = math.hypot(food.x - self.fly.x, food.y - self.fly.y)
        bearing = math.atan2(food.y - self.fly.y, food.x - self.fly.x) - self.fly.heading
        bearing = (bearing + math.pi) % (2 * math.pi) - math.pi
        return food, dist, bearing

    def senses(self) -> dict[str, float]:
        front = self.ray_distance(self.fly.heading, 3.0)
        left = self.ray_distance(self.fly.heading - 0.42, 3.0)
        right = self.ray_distance(self.fly.heading + 0.42, 3.0)
        _, food_dist, bearing = self.nearest_food()
        smell = math.exp(-food_dist / 3.2)
        visible = abs(bearing) < 0.72 and food_dist < 6.0
        return {
            "loom": max(0.0, 1.0 - front / 1.05),
            "wall_left": max(0.0, 1.0 - left / 1.2),
            "wall_right": max(0.0, 1.0 - right / 1.2),
            "food_left": smell * (1.0 if bearing < -0.05 else 0.15) * (1.0 if visible else 0.45),
            "food_right": smell * (1.0 if bearing > 0.05 else 0.15) * (1.0 if visible else 0.45),
            "food_center": smell * max(0.0, 1.0 - abs(bearing) / math.pi),
            "food_distance": food_dist,
            "altitude": self.fly.altitude,
            "airborne": 0.0 if self.fly.flight_mode == "ground" else 1.0,
        }

    def step(self, forward: float, turn: float, escape: float, dt: float):
        fly = self.fly
        food, food_distance, _ = self.nearest_food()
        feeding = food is not None and food_distance < 0.48 and fly.altitude < 0.10
        if fly.flight_enabled and fly.flight_mode == "ground" and food_distance > 1.8 and self.time > 0.8:
            fly.flight_mode = "takeoff"
            fly.flight_time = 0.0
        if fly.flight_mode != "ground":
            fly.flight_time += dt
        if fly.flight_mode == "cruise" and fly.flight_time > 2.8 and food_distance < 1.15:
            fly.flight_mode = "landing"
        if not fly.flight_enabled and fly.flight_mode not in ("ground", "landing"):
            fly.flight_mode = "landing"
        if feeding:
            fly.state = "feeding"
            fly.feeding_time += dt
        elif escape > 0.18:
            fly.state = "escaping"
            fly.feeding_time = 0.0
        elif self.ray_distance(fly.heading, 0.9) < 0.65:
            fly.state = "avoiding"
            fly.feeding_time = 0.0
        elif food_distance < 5.0:
            fly.state = "tracking food"
            fly.feeding_time = 0.0
        else:
            fly.state = "exploring"
            fly.feeding_time = 0.0
        if fly.flight_mode == "takeoff":
            fly.state = "taking off"
        elif fly.flight_mode == "landing":
            fly.state = "landing"
        elif fly.flight_mode == "cruise":
            ahead_x = fly.x + math.cos(fly.heading) * 0.8
            ahead_y = fly.y + math.sin(fly.heading) * 0.8
            fly.state = "air avoiding" if self.air_obstacle(ahead_x, ahead_y, fly.altitude) else "flying"
        airborne = fly.flight_mode != "ground"
        turn_rate = 2.8 if airborne else 2.2
        fly.heading = (fly.heading + max(-1.0, min(1.0, turn)) * turn_rate * dt) % (2 * math.pi)
        target_speed = (1.25 + 1.0 * max(0.0, forward)) if airborne else (0.03 if feeding else 0.25 + 0.9 * max(0.0, forward) + 0.8 * max(0.0, escape))
        fly.speed += (target_speed - fly.speed) * min(1.0, dt * 5.0)
        target_altitude = 0.0
        if fly.flight_mode == "takeoff":
            target_altitude = 1.8
            if fly.altitude > 1.5:
                fly.flight_mode = "cruise"
        elif fly.flight_mode == "cruise":
            target_altitude = 1.75 + 0.28 * math.sin(self.time * 0.8)
        fly.vertical_speed += ((target_altitude - fly.altitude) * 3.0 - fly.vertical_speed * 2.4) * dt
        fly.vertical_speed = max(-1.35, min(1.35, fly.vertical_speed))
        fly.altitude = max(0.0, fly.altitude + fly.vertical_speed * dt)
        if fly.flight_mode == "landing" and fly.altitude <= 0.035:
            fly.altitude = fly.vertical_speed = 0.0
            fly.flight_mode = "ground"
            fly.flight_time = 0.0
        fly.pitch += (max(-0.24, min(0.24, fly.vertical_speed * 0.18)) - fly.pitch) * min(1.0, dt * 5.0)
        fly.roll += (max(-0.38, min(0.38, -turn * 0.34)) - fly.roll) * min(1.0, dt * 6.0)
        dx = math.cos(fly.heading) * fly.speed * dt
        dy = math.sin(fly.heading) * fly.speed * dt
        nx, ny = fly.x + dx, fly.y + dy
        radius = 0.16
        blocked_x = self.air_obstacle(nx + math.copysign(radius, dx or 1), fly.y, fly.altitude) if airborne else self.wall(nx + math.copysign(radius, dx or 1), fly.y)
        if not blocked_x:
            fly.x = nx
        else:
            fly.heading += 0.55
        blocked_y = self.air_obstacle(fly.x, ny + math.copysign(radius, dy or 1), fly.altitude) if airborne else self.wall(fly.x, ny + math.copysign(radius, dy or 1))
        if not blocked_y:
            fly.y = ny
        else:
            fly.heading -= 0.55
        moved = math.sqrt(dx * dx + dy * dy + (fly.vertical_speed * dt) ** 2)
        self.distance += moved
        self.time += dt
        fly.energy = max(0.0, fly.energy - moved * 0.002)
        for food in list(self.foods):
            if math.hypot(food.x - fly.x, food.y - fly.y) < food.radius + 0.22 and fly.feeding_time > 1.0:
                self.foods.remove(food)
                fly.foods_found += 1
                fly.energy = min(1.0, fly.energy + 0.3)
                fly.feeding_time = 0.0
        if not self.trail or math.sqrt((fly.x - self.trail[-1][0]) ** 2 + (fly.altitude - self.trail[-1][1]) ** 2 + (fly.y - self.trail[-1][2]) ** 2) > 0.06:
            self.trail.append((fly.x, fly.altitude, fly.y))
            self.trail = self.trail[-1200:]
