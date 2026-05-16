import math
import random
from dataclasses import dataclass

import pygame


WIDTH, HEIGHT = 960, 640
FPS = 60


@dataclass
class WeaponConfig:
    name: str
    cooldown: int
    bullet_speed: float
    damage: int
    spread: int = 1
    color: tuple[int, int, int] = (255, 255, 255)
    pierce: bool = False


WEAPONS = [
    WeaponConfig("迅影机炮", cooldown=8, bullet_speed=12, damage=8, spread=1, color=(120, 230, 255)),
    WeaponConfig("霰爆脉冲", cooldown=20, bullet_speed=10, damage=7, spread=5, color=(255, 220, 120)),
    WeaponConfig("穿甲激光", cooldown=26, bullet_speed=18, damage=22, spread=1, color=(255, 90, 90), pierce=True),
]


class StarField:
    def __init__(self, amount: int):
        self.stars = []
        for _ in range(amount):
            self.stars.append([
                random.uniform(0, WIDTH),
                random.uniform(0, HEIGHT),
                random.uniform(0.8, 4.8),
                random.uniform(1, 3),
            ])

    def update(self):
        for star in self.stars:
            star[1] += star[2]
            if star[1] > HEIGHT:
                star[0] = random.uniform(0, WIDTH)
                star[1] = random.uniform(-40, -5)

    def draw(self, screen: pygame.Surface):
        for x, y, speed, size in self.stars:
            alpha = max(80, min(255, int(speed * 50)))
            color = (alpha, alpha, 255)
            pygame.draw.circle(screen, color, (int(x), int(y)), int(size))


class Bullet:
    def __init__(self, x, y, vx, vy, damage, color, pierce=False, friendly=True):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.damage = damage
        self.color = color
        self.pierce = pierce
        self.friendly = friendly
        self.radius = 4 if friendly else 5
        self.alive = True

    def update(self):
        self.x += self.vx
        self.y += self.vy
        if self.x < -20 or self.x > WIDTH + 20 or self.y < -20 or self.y > HEIGHT + 20:
            self.alive = False

    def draw(self, screen: pygame.Surface):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
        if self.friendly:
            pygame.draw.circle(screen, (255, 255, 255), (int(self.x), int(self.y)), self.radius + 2, 1)

    def rect(self):
        return pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius * 2, self.radius * 2)


class Enemy:
    def __init__(self, level: int):
        self.level = level
        self.x = random.randint(50, WIDTH - 50)
        self.y = random.randint(-240, -50)
        self.vx = random.choice([-1.5, -1.0, 1.0, 1.5]) * (1 + level * 0.08)
        self.vy = random.uniform(1.5, 3.0) * (1 + level * 0.12)
        self.hp = 20 + level * 5
        self.max_hp = self.hp
        self.radius = 18
        self.cooldown = random.randint(40, 90)
        self.alive = True

    def update(self):
        self.x += self.vx
        self.y += self.vy
        if self.x < 25 or self.x > WIDTH - 25:
            self.vx *= -1
        if self.y > HEIGHT + 50:
            self.alive = False

    def shoot(self):
        self.cooldown -= 1
        if self.cooldown <= 0:
            self.cooldown = random.randint(55, 95)
            return Bullet(self.x, self.y + 10, 0, 5.5, damage=10, color=(255, 110, 110), friendly=False)
        return None

    def draw(self, screen: pygame.Surface):
        body = pygame.Rect(int(self.x - 20), int(self.y - 16), 40, 32)
        pygame.draw.rect(screen, (100, 80, 200), body, border_radius=8)
        pygame.draw.rect(screen, (205, 180, 255), body, width=2, border_radius=8)
        hp_ratio = max(0, self.hp / self.max_hp)
        pygame.draw.rect(screen, (70, 50, 80), (self.x - 20, self.y - 26, 40, 5), border_radius=2)
        pygame.draw.rect(screen, (255, 130, 230), (self.x - 20, self.y - 26, 40 * hp_ratio, 5), border_radius=2)

    def rect(self):
        return pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius * 2, self.radius * 2)


class Boss:
    def __init__(self):
        self.x = WIDTH // 2
        self.y = -140
        self.hp = 900
        self.max_hp = self.hp
        self.phase = 0
        self.alive = True
        self.direction = 1
        self.attack_tick = 0

    def update(self):
        if self.y < 120:
            self.y += 1.3
        else:
            self.x += self.direction * 2.4
            if self.x < 140 or self.x > WIDTH - 140:
                self.direction *= -1

    def shoot_pattern(self):
        self.attack_tick += 1
        bullets = []
        if self.attack_tick % 16 == 0:
            for angle in (-35, -18, 0, 18, 35):
                rad = math.radians(angle)
                bullets.append(Bullet(self.x, self.y + 40, math.sin(rad) * 3.5, math.cos(rad) * 5.5, 14, (255, 80, 120), friendly=False))
        if self.attack_tick % 95 == 0:
            for i in range(20):
                a = (math.tau / 20) * i
                bullets.append(Bullet(self.x, self.y + 10, math.cos(a) * 3, math.sin(a) * 3, 12, (255, 160, 80), friendly=False))
        return bullets

    def draw(self, screen: pygame.Surface):
        hull = pygame.Rect(int(self.x - 110), int(self.y - 46), 220, 92)
        pygame.draw.rect(screen, (180, 40, 70), hull, border_radius=18)
        pygame.draw.rect(screen, (255, 170, 200), hull, width=3, border_radius=18)
        core_r = 18 + int(3 * math.sin(pygame.time.get_ticks() * 0.008))
        pygame.draw.circle(screen, (255, 230, 100), (int(self.x), int(self.y)), core_r)
        ratio = max(0, self.hp / self.max_hp)
        pygame.draw.rect(screen, (80, 20, 20), (WIDTH // 2 - 220, 20, 440, 18), border_radius=6)
        pygame.draw.rect(screen, (255, 70, 90), (WIDTH // 2 - 220, 20, 440 * ratio, 18), border_radius=6)

    def rect(self):
        return pygame.Rect(self.x - 110, self.y - 46, 220, 92)


class Player:
    def __init__(self):
        self.x = WIDTH // 2
        self.y = HEIGHT - 80
        self.speed = 6.5
        self.hp = 100
        self.max_hp = 100
        self.weapon_idx = 0
        self.cooldown = 0
        self.invincible_tick = 0

    @property
    def weapon(self):
        return WEAPONS[self.weapon_idx]

    def update(self, keys):
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.x -= self.speed
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.x += self.speed
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            self.y -= self.speed
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            self.y += self.speed
        self.x = max(30, min(WIDTH - 30, self.x))
        self.y = max(50, min(HEIGHT - 30, self.y))
        if self.cooldown > 0:
            self.cooldown -= 1
        if self.invincible_tick > 0:
            self.invincible_tick -= 1

    def shoot(self):
        if self.cooldown > 0:
            return []
        cfg = self.weapon
        self.cooldown = cfg.cooldown
        bullets = []
        if cfg.spread == 1:
            bullets.append(Bullet(self.x, self.y - 20, 0, -cfg.bullet_speed, cfg.damage, cfg.color, cfg.pierce, friendly=True))
        else:
            arc = 26
            for i in range(cfg.spread):
                shift = -arc / 2 + arc * (i / (cfg.spread - 1))
                rad = math.radians(shift)
                vx = math.sin(rad) * 2.5
                vy = -cfg.bullet_speed * math.cos(rad)
                bullets.append(Bullet(self.x + shift * 0.4, self.y - 12, vx, vy, cfg.damage, cfg.color, cfg.pierce, friendly=True))
        return bullets

    def draw(self, screen: pygame.Surface):
        blink = self.invincible_tick > 0 and (self.invincible_tick // 4) % 2 == 0
        if blink:
            return
        points = [(self.x, self.y - 24), (self.x - 16, self.y + 14), (self.x, self.y + 6), (self.x + 16, self.y + 14)]
        pygame.draw.polygon(screen, (80, 220, 255), points)
        pygame.draw.polygon(screen, (220, 250, 255), points, width=2)
        pygame.draw.circle(screen, (255, 220, 120), (int(self.x), int(self.y - 8)), 4)

    def rect(self):
        return pygame.Rect(self.x - 16, self.y - 22, 32, 36)


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("苍穹裂隙：Space Jet Assault")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("microsoftyahei", 24)
        self.big_font = pygame.font.SysFont("microsoftyahei", 40, bold=True)
        self.starfield = StarField(140)
        self.player = Player()
        self.player_bullets = []
        self.enemy_bullets = []
        self.enemies = []
        self.boss = None
        self.score = 0
        self.level = 1
        self.stage_state = "intro"
        self.stage_tick = 120
        self.spawn_timer = 0
        self.killed_this_stage = 0
        self.target_kills = {1: 12, 2: 18, 3: 24}
        self.running = True

    def spawn_enemy(self):
        self.enemies.append(Enemy(self.level))

    def next_stage(self):
        if self.level < 3:
            self.level += 1
            self.killed_this_stage = 0
            self.stage_state = "intro"
            self.stage_tick = 140
        else:
            self.stage_state = "boss_intro"
            self.stage_tick = 180
            self.boss = Boss()

    def handle_collisions(self):
        for bullet in self.player_bullets:
            if not bullet.alive:
                continue
            for enemy in self.enemies:
                if enemy.alive and bullet.rect().colliderect(enemy.rect()):
                    enemy.hp -= bullet.damage
                    if not bullet.pierce:
                        bullet.alive = False
                    if enemy.hp <= 0:
                        enemy.alive = False
                        self.score += 120
                        self.killed_this_stage += 1
            if self.boss and self.boss.alive and bullet.alive and bullet.rect().colliderect(self.boss.rect()):
                self.boss.hp -= bullet.damage
                if not bullet.pierce:
                    bullet.alive = False
                if self.boss.hp <= 0:
                    self.boss.alive = False
                    self.stage_state = "win"

        if self.player.invincible_tick == 0:
            for bullet in self.enemy_bullets:
                if bullet.alive and bullet.rect().colliderect(self.player.rect()):
                    bullet.alive = False
                    self.player.hp -= bullet.damage
                    self.player.invincible_tick = 45
                    if self.player.hp <= 0:
                        self.stage_state = "gameover"

            for enemy in self.enemies:
                if enemy.alive and enemy.rect().colliderect(self.player.rect()):
                    enemy.alive = False
                    self.player.hp -= 20
                    self.player.invincible_tick = 45
                    if self.player.hp <= 0:
                        self.stage_state = "gameover"

    def update(self):
        keys = pygame.key.get_pressed()
        if self.stage_state in {"gameover", "win"}:
            if keys[pygame.K_r]:
                self.__init__()
            return

        self.starfield.update()
        self.player.update(keys)

        if keys[pygame.K_1]:
            self.player.weapon_idx = 0
        elif keys[pygame.K_2]:
            self.player.weapon_idx = 1
        elif keys[pygame.K_3]:
            self.player.weapon_idx = 2

        if keys[pygame.K_SPACE]:
            self.player_bullets.extend(self.player.shoot())

        if self.stage_state == "intro":
            self.stage_tick -= 1
            if self.stage_tick <= 0:
                self.stage_state = "battle"
        elif self.stage_state == "battle":
            self.spawn_timer -= 1
            spawn_gap = max(28, 65 - self.level * 10)
            if self.spawn_timer <= 0:
                self.spawn_enemy()
                self.spawn_timer = random.randint(spawn_gap, spawn_gap + 25)
            if self.killed_this_stage >= self.target_kills[self.level]:
                self.stage_state = "transition"
                self.stage_tick = 150
        elif self.stage_state == "transition":
            self.stage_tick -= 1
            if self.stage_tick <= 0:
                self.next_stage()
        elif self.stage_state == "boss_intro":
            self.stage_tick -= 1
            if self.stage_tick <= 0:
                self.stage_state = "boss"
        elif self.stage_state == "boss" and self.boss:
            self.boss.update()
            self.enemy_bullets.extend(self.boss.shoot_pattern())

        for enemy in self.enemies:
            enemy.update()
            shot = enemy.shoot()
            if shot:
                self.enemy_bullets.append(shot)

        for bullet in self.player_bullets + self.enemy_bullets:
            bullet.update()

        self.handle_collisions()
        self.enemies = [e for e in self.enemies if e.alive]
        self.player_bullets = [b for b in self.player_bullets if b.alive]
        self.enemy_bullets = [b for b in self.enemy_bullets if b.alive]

    def draw_ui(self):
        hp_text = self.font.render(f"HP: {self.player.hp}/{self.player.max_hp}", True, (220, 245, 255))
        score_text = self.font.render(f"SCORE: {self.score}", True, (220, 245, 255))
        level_name = "BOSS关" if self.stage_state in {"boss", "boss_intro"} else f"第{self.level}关"
        stage_text = self.font.render(level_name, True, (255, 220, 160))
        weapon = self.player.weapon
        weapon_text = self.font.render(f"武器[{self.player.weapon_idx + 1}]: {weapon.name}", True, weapon.color)

        self.screen.blit(hp_text, (20, 18))
        self.screen.blit(score_text, (20, 46))
        self.screen.blit(stage_text, (WIDTH - 140, 18))
        self.screen.blit(weapon_text, (20, HEIGHT - 40))

        if self.stage_state == "battle":
            target = self.target_kills[self.level]
            progress = self.font.render(f"歼灭进度: {self.killed_this_stage}/{target}", True, (200, 220, 255))
            self.screen.blit(progress, (WIDTH - 230, 46))

        hint = self.font.render("移动: WASD/方向键  射击: SPACE  切换武器: 1/2/3", True, (130, 170, 220))
        self.screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT - 32))

    def draw_overlay(self):
        messages = {
            "intro": f"第 {self.level} 关 - 清空敌军舰队",
            "transition": "跃迁通道开启，准备进入下一关...",
            "boss_intro": "警报！旗舰级BOSS正在接近！",
            "gameover": "任务失败 - 按 R 重开",
            "win": "BOSS已击坠，胜利！按 R 再战",
        }
        if self.stage_state in messages:
            text = self.big_font.render(messages[self.stage_state], True, (255, 230, 190))
            self.screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 - 20))

    def draw(self):
        self.screen.fill((10, 15, 35))
        self.starfield.draw(self.screen)

        for bullet in self.player_bullets:
            bullet.draw(self.screen)
        for bullet in self.enemy_bullets:
            bullet.draw(self.screen)
        for enemy in self.enemies:
            enemy.draw(self.screen)
        if self.boss and self.boss.alive:
            self.boss.draw(self.screen)

        self.player.draw(self.screen)
        self.draw_ui()
        self.draw_overlay()

        pygame.display.flip()

    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

            self.update()
            self.draw()
            self.clock.tick(FPS)

        pygame.quit()


if __name__ == "__main__":
    Game().run()
