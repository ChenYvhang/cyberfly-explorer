from __future__ import annotations

import math
from pathlib import Path
import pygame


class Renderer:
    TOOLS = ["wall", "floor", "rock", "plant", "stump", "puddle", "food", "spawn"]

    def __init__(self, screen: pygame.Surface, world):
        self.screen = screen
        self.world = world
        self.w, self.h = screen.get_size()
        self.view_w = int(self.w * 0.73)
        self.font = pygame.font.SysFont("Segoe UI", 18)
        self.small = pygame.font.SysFont("Segoe UI", 14)
        asset = Path(__file__).resolve().parents[1] / "assets" / "fruit-fly-hq.png"
        self.fly_sprite = pygame.image.load(asset).convert_alpha() if asset.exists() else None
        if self.fly_sprite:
            self.fly_sprite = pygame.transform.smoothscale(self.fly_sprite, (104, 104))
        self.fly_rotations: dict[int, pygame.Surface] = {}

    def project(self, wx, wy, z=0.0):
        """World coordinates to a fly-following isometric camera."""
        f = self.world.fly
        dx, dy = wx - f.x, wy - f.y
        scale = 38.0
        return (
            self.view_w * 0.50 + (dx - dy) * scale,
            self.h * 0.57 + (dx + dy) * scale * 0.48 - z * scale,
        )

    def text(self, value, x, y, color=(220, 230, 225), font=None):
        self.screen.blit((font or self.font).render(str(value), True, color), (x, y))

    def draw_third_person(self):
        vw, h = self.view_w, self.h
        self.screen.fill((13, 18, 22))
        self.screen.set_clip(pygame.Rect(0, 0, vw, h))
        for y in range(h):
            t = y / h
            color = (int(39 + 18 * t), int(62 + 16 * t), int(75 + 9 * t))
            pygame.draw.line(self.screen, color, (0, y), (vw, y))

        # Painter's-order floor and extruded wall blocks.
        for gy in range(self.world.height):
            for gx in range(self.world.width):
                corners = [self.project(gx, gy), self.project(gx + 1, gy),
                           self.project(gx + 1, gy + 1), self.project(gx, gy + 1)]
                if max(p[0] for p in corners) < 0 or min(p[0] for p in corners) > vw:
                    continue
                if max(p[1] for p in corners) < 0 or min(p[1] for p in corners) > h:
                    continue
                if self.world.grid[gy][gx] == "#":
                    top = [self.project(gx, gy, 0.78), self.project(gx + 1, gy, 0.78),
                           self.project(gx + 1, gy + 1, 0.78), self.project(gx, gy + 1, 0.78)]
                    shadow = [(p[0] + 13, p[1] + 16) for p in corners]
                    pygame.draw.polygon(self.screen, (29, 35, 33), shadow)
                    pygame.draw.polygon(self.screen, (91, 78, 65), [corners[1], corners[2], top[2], top[1]])
                    pygame.draw.polygon(self.screen, (70, 65, 59), [corners[2], corners[3], top[3], top[2]])
                    pygame.draw.polygon(self.screen, (142, 119, 88), top)
                    pygame.draw.lines(self.screen, (52, 49, 46), True, top, 1)
                else:
                    if gy > 14:
                        base = (46, 53, 39)  # garden
                    elif gx > 16 and 8 < gy < 16:
                        base = (49, 48, 42)  # rocky court
                    elif 8 < gx < 16 and 6 < gy < 12:
                        base = (38, 52, 48)  # damp court
                    else:
                        base = (39, 47, 40)
                    delta = ((gx + gy) & 1) * 3
                    pygame.draw.polygon(self.screen, tuple(c + delta for c in base), corners)

        if len(self.world.trail) > 1:
            trail = [self.project(px, py, 0.03) for px, py in self.world.trail]
            pygame.draw.lines(self.screen, (62, 153, 124), False, trail, 3)

        for obj in sorted(self.world.decor, key=lambda o: o.x + o.y):
            px, py = self.project(obj.x, obj.y, 0.02)
            if obj.kind == "puddle":
                rx = int(obj.radius * 38)
                pygame.draw.ellipse(self.screen, (34, 76, 83), (px - rx, py - rx * .32, rx * 2, rx * .64))
                pygame.draw.arc(self.screen, (74, 129, 130), (px - rx * .7, py - rx * .2, rx * 1.4, rx * .38), 3.4, 5.8, 2)
            elif obj.kind == "rock":
                base = self.project(obj.x, obj.y, 0)
                top = self.project(obj.x, obj.y, obj.height)
                r = int(obj.radius * 32)
                pygame.draw.ellipse(self.screen, (24, 29, 28), (base[0] - r, base[1] - 3, r * 2, 10))
                poly = [(top[0] - r * .65, top[1]), (top[0] + r * .55, top[1] - 4),
                        (base[0] + r, base[1]), (base[0] - r, base[1] + 2)]
                pygame.draw.polygon(self.screen, (83, 91, 87), poly)
                pygame.draw.polygon(self.screen, (119, 128, 119),
                                    [(top[0] - r * .65, top[1]), (top[0], top[1] - r * .35),
                                     (top[0] + r * .55, top[1] - 4), (top[0], top[1] + r * .18)])
            elif obj.kind == "stump":
                base = self.project(obj.x, obj.y, 0)
                top = self.project(obj.x, obj.y, obj.height)
                r = int(obj.radius * 27)
                pygame.draw.polygon(self.screen, (94, 64, 43),
                                    [(base[0] - r, base[1]), (base[0] + r, base[1]),
                                     (top[0] + r, top[1]), (top[0] - r, top[1])])
                pygame.draw.ellipse(self.screen, (139, 103, 65), (top[0] - r, top[1] - 5, r * 2, 10))
                pygame.draw.ellipse(self.screen, (75, 55, 39), (top[0] - r * .45, top[1] - 2, r * .9, 5), 1)
            elif obj.kind == "plant":
                base = self.project(obj.x, obj.y, 0)
                top = self.project(obj.x, obj.y, obj.height)
                pygame.draw.line(self.screen, (58, 111, 65), base, top, 4)
                for n, side in enumerate((-1, 1, -1, 1, 0)):
                    t = (n + 1) / 6
                    sx = base[0] + (top[0] - base[0]) * t
                    sy = base[1] + (top[1] - base[1]) * t
                    end = (sx + side * (15 - n), sy - 7)
                    pygame.draw.line(self.screen, (73, 147 + n * 5, 78), (sx, sy), end, 5)

        for food in self.world.foods:
            px, py = self.project(food.x, food.y, 0.10)
            pygame.draw.ellipse(self.screen, (81, 65, 29), (px - 14, py + 5, 28, 10))
            banana = [(px - 14, py - 2), (px - 7, py + 8), (px + 5, py + 10),
                      (px + 15, py + 3), (px + 10, py + 12), (px - 3, py + 16),
                      (px - 14, py + 10)]
            pygame.draw.polygon(self.screen, (240, 196, 54), banana)
            pygame.draw.lines(self.screen, (255, 232, 116), False, banana[:4], 2)

        # High-resolution transparent entity asset, rotated to the projected heading.
        f = self.world.fly
        cx, cy = self.project(f.x, f.y, 0.25)
        hx, hy = math.cos(f.heading), math.sin(f.heading)
        fx, fy = self.project(f.x + hx * 0.42, f.y + hy * 0.42, 0.25)
        direction = pygame.Vector2(fx - cx, fy - cy)
        if direction.length_squared() == 0:
            direction = pygame.Vector2(1, 0)
        direction = direction.normalize()
        shadow = pygame.Surface((86, 28), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (3, 8, 7, 115), shadow.get_rect())
        self.screen.blit(shadow, shadow.get_rect(center=(cx + 7, cy + 20)))
        if self.fly_sprite:
            angle = int(round(math.degrees(math.atan2(-direction.x, -direction.y)) / 4) * 4)
            if angle not in self.fly_rotations:
                self.fly_rotations[angle] = pygame.transform.rotozoom(self.fly_sprite, angle, 1.0)
            sprite = self.fly_rotations[angle]
            bob = -2.0 + math.sin(self.world.time * 12.0) * (1.5 if f.state != "feeding" else 0.3)
            self.screen.blit(sprite, sprite.get_rect(center=(cx, cy + bob)))
        else:
            pygame.draw.circle(self.screen, (105, 72, 43), (int(cx), int(cy)), 12)
        self.screen.set_clip(None)

        # Soft separator makes the instrument panel read as a cockpit overlay.
        pygame.draw.rect(self.screen, (7, 12, 15), (vw - 2, 0, 4, h))

    def draw_minimap(self, x, y, width):
        scale = width / self.world.width
        for gy, row in enumerate(self.world.grid):
            for gx, cell in enumerate(row):
                color = (54, 58, 61) if cell == "#" else (23, 29, 31)
                pygame.draw.rect(self.screen, color, (x + gx * scale, y + gy * scale, scale + 1, scale + 1))
        if len(self.world.trail) > 1:
            pts = [(x + px * scale, y + py * scale) for px, py in self.world.trail]
            pygame.draw.lines(self.screen, (70, 148, 126), False, pts, 2)
        for food in self.world.foods:
            pygame.draw.circle(self.screen, (244, 204, 78), (int(x + food.x * scale), int(y + food.y * scale)), 4)
        for obj in self.world.decor:
            if obj.kind != "puddle":
                pygame.draw.circle(self.screen, (94, 117, 91), (int(x + obj.x * scale), int(y + obj.y * scale)), 2)
        f = self.world.fly
        pos = (int(x + f.x * scale), int(y + f.y * scale))
        pygame.draw.circle(self.screen, (110, 240, 180), pos, 5)
        pygame.draw.line(self.screen, (210, 255, 230), pos,
                         (pos[0] + math.cos(f.heading) * 12, pos[1] + math.sin(f.heading) * 12), 2)

    def draw_panel(self, stats, senses, paused, real_brain):
        x = self.view_w + 18
        self.text("CYBERFLY", x, 20, (111, 242, 185))
        self.text("MaleCNS v1.0" if real_brain else "Preview controller", x, 47, (170, 185, 180), self.small)
        self.draw_minimap(x, 82, self.w - x - 18)
        y = 370
        lines = [
            f"state        {self.world.fly.state}",
            f"brain step   {stats.get('step_ms', 0):5.1f} ms",
            f"active       {stats.get('active', 0):6d}",
            f"DNa02 L/R    {stats.get('steer_L', 0):4.1f} / {stats.get('steer_R', 0):4.1f} Hz",
            f"DNp01 escape {stats.get('escape', 0):4.1f} Hz",
            f"food range   {senses.get('food_distance', 0):4.1f}",
            f"distance     {self.world.distance:4.1f}",
            f"food found   {self.world.fly.foods_found}/5",
        ]
        for line in lines:
            self.text(line, x, y, font=self.small)
            y += 25
        self.text("E editor  SPACE pause  R reset", x, self.h - 58, (145, 158, 154), self.small)
        self.text("ESC quit", x, self.h - 34, (145, 158, 154), self.small)
        if paused:
            self.text("PAUSED", 24, 22, (255, 213, 87))

    def draw(self, stats, senses, paused, real_brain=True):
        self.draw_third_person()
        self.draw_panel(stats, senses, paused, real_brain)
        pygame.display.flip()

    def editor_geometry(self):
        cell = min(30, int((self.h - 110) / self.world.height), int((self.w - 390) / self.world.width))
        return 35, 70, max(12, cell)

    def editor_cell_at(self, pos):
        ox, oy, cell = self.editor_geometry()
        gx, gy = int((pos[0] - ox) // cell), int((pos[1] - oy) // cell)
        if 0 <= gx < self.world.width and 0 <= gy < self.world.height:
            return gx, gy
        return None

    def draw_editor(self, selected: str, notice: str = ""):
        self.screen.fill((11, 17, 20))
        self.text("WORLD EDITOR", 35, 20, (112, 240, 184))
        self.text("Left click: place   Right click: erase", 205, 24, (151, 170, 163), self.small)
        ox, oy, cell = self.editor_geometry()
        decor_cells = {(int(o.x), int(o.y)): o.kind for o in self.world.decor}
        food_cells = {(int(o.x), int(o.y)) for o in self.world.foods}
        for gy, row in enumerate(self.world.grid):
            for gx, tile in enumerate(row):
                rect = pygame.Rect(ox + gx * cell, oy + gy * cell, cell, cell)
                base = (70, 72, 70) if tile == "#" else ((38, 52, 44) if gy > 14 else (35, 43, 40))
                pygame.draw.rect(self.screen, base, rect)
                pygame.draw.rect(self.screen, (18, 25, 26), rect, 1)
                kind = decor_cells.get((gx, gy))
                center = rect.center
                if kind == "rock":
                    pygame.draw.circle(self.screen, (123, 130, 126), center, max(3, cell // 5))
                elif kind == "plant":
                    pygame.draw.line(self.screen, (77, 175, 91), (center[0], center[1] + 7), (center[0], center[1] - 7), 3)
                    pygame.draw.line(self.screen, (77, 175, 91), center, (center[0] + 7, center[1] - 4), 3)
                elif kind == "stump":
                    pygame.draw.circle(self.screen, (139, 99, 61), center, max(3, cell // 5))
                elif kind == "puddle":
                    pygame.draw.ellipse(self.screen, (44, 105, 115), rect.inflate(-5, -12))
                if (gx, gy) in food_cells:
                    pygame.draw.circle(self.screen, (245, 204, 65), center, max(3, cell // 5))
        fx = ox + self.world.fly.x * cell
        fy = oy + self.world.fly.y * cell
        pygame.draw.circle(self.screen, (103, 242, 177), (int(fx), int(fy)), max(4, cell // 4))
        pygame.draw.line(self.screen, (220, 255, 235), (fx, fy),
                         (fx + math.cos(self.world.fly.heading) * cell, fy + math.sin(self.world.fly.heading) * cell), 2)

        panel_x = ox + self.world.width * cell + 35
        self.text("PALETTE", panel_x, 70, (205, 218, 212))
        labels = {"wall": "Wall", "floor": "Erase / floor", "rock": "Rock", "plant": "Plant",
                  "stump": "Tree stump", "puddle": "Puddle", "food": "Banana", "spawn": "Fly start"}
        for i, tool in enumerate(self.TOOLS):
            rect = pygame.Rect(panel_x, 108 + i * 48, 250, 36)
            color = (49, 111, 87) if tool == selected else (29, 38, 39)
            pygame.draw.rect(self.screen, color, rect, border_radius=7)
            pygame.draw.rect(self.screen, (91, 122, 108), rect, 1, border_radius=7)
            self.text(f"{i + 1}   {labels[tool]}", rect.x + 12, rect.y + 8, font=self.small)
        self.text("S  Save map", panel_x, 510, (185, 207, 198), self.small)
        self.text("L  Reload saved map", panel_x, 536, (185, 207, 198), self.small)
        self.text("D  Restore default", panel_x, 562, (185, 207, 198), self.small)
        self.text("E  Return to simulation", panel_x, 588, (112, 240, 184), self.small)
        if notice:
            self.text(notice, panel_x, 630, (245, 206, 91), self.small)
        pygame.display.flip()
