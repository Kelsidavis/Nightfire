import pygame
import sys
import math
import random

pygame.init()

WIDTH, HEIGHT = 800, 600
FPS = 60
STAR_COUNT = 200
THRUST = 0.1
FRICTION = 0.99
ROTATE_SPEED = 3
LASER_SPEED = 10
ENEMY_LASER_SPEED = 4
ENEMY_FIRE_INTERVAL = 90
SPRITE_OFFSET = 90
STARTING_HP = 20
DAMAGE_PER_HIT = 3

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Nightfire: The Last Command")
clock = pygame.time.Clock()
font = pygame.font.SysFont("consolas", 24)

ship_orig = pygame.image.load("assets/ship.png").convert_alpha()
ship_orig = pygame.transform.scale(ship_orig, (60, 60))
enemy_scale = (25, 25)
ywing_img = pygame.transform.scale(pygame.image.load("assets/ywing.png").convert_alpha(), enemy_scale)
xwing_img = pygame.transform.scale(pygame.image.load("assets/xwing.png").convert_alpha(), enemy_scale)
awing_img = pygame.transform.scale(pygame.image.load("assets/awing.png").convert_alpha(), enemy_scale)

ywing_img = pygame.transform.rotate(ywing_img, 180)
xwing_img = pygame.transform.rotate(xwing_img, 180)
awing_img = pygame.transform.rotate(awing_img, 180)
enemy_ships = [ywing_img, xwing_img, awing_img]

ship_world_x, ship_world_y = 0, 0
ship_angle = 0
vel_x, vel_y = 0, 0
score = 0
hp = STARTING_HP

stars = [(random.randint(-2000, 2000), random.randint(-2000, 2000)) for _ in range(STAR_COUNT)]

lasers = []
enemy_lasers = []
enemies = []
enemy_spawn_timer = 0

class EnemyShip:
    def __init__(self):
        self.image = random.choice(enemy_ships)
        self.x = ship_world_x + random.randint(-WIDTH//2, WIDTH//2)
        self.y = ship_world_y - HEIGHT - random.randint(60, 300)
        self.speed = random.uniform(1, 2)
        self.exploding = False
        self.timer = 0
        self.fire_timer = random.randint(30, ENEMY_FIRE_INTERVAL)

    def update(self):
        if self.exploding:
            self.timer -= 1
            return self.timer > 0
        else:
            self.y += self.speed
            self.fire_timer -= 1
            if self.fire_timer <= 0:
                self.fire()
                self.fire_timer = ENEMY_FIRE_INTERVAL
            return abs(self.y - ship_world_y) < HEIGHT + 100

    def fire(self):
        aim_at_player = random.random() < 0.3
        if aim_at_player:
            dx = ship_world_x - self.x
            dy = ship_world_y - self.y
            angle = math.atan2(dy, dx)
        else:
            angle = math.radians(90)
        enemy_lasers.append({
            "x": self.x + self.image.get_width() // 2,
            "y": self.y + self.image.get_height(),
            "angle": angle
        })

    def draw(self, surface, offset_x, offset_y):
        if self.exploding:
            cx = int(self.x - offset_x)
            cy = int(self.y - offset_y)
            pygame.draw.circle(surface, (255, 0, 0), (cx, cy), 20)
        else:
            surface.blit(self.image, (self.x - offset_x, self.y - offset_y))
def run_game():
    paused = False
    pygame.mixer.music.stop()
    pygame.mixer.music.load('assets/saphire.mp3')
    pygame.mixer.music.play(-1)
    global ship_world_x, ship_world_y, vel_x, vel_y, ship_angle, score, hp, enemy_spawn_timer
    running = True

    while running:
        dt = clock.tick(FPS)
        screen.fill((0, 0, 10))

        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN and event.key == pygame.K_p:
                paused = not paused
            if event.type == pygame.QUIT:
                running = False

        if paused:
            pause_text = font.render('PAUSED', True, (255, 255, 0))
            screen.blit(pause_text, (WIDTH // 2 - 40, HEIGHT // 2))
            pygame.display.flip()
            continue

        keys = pygame.key.get_pressed()
        thrusting = keys[pygame.K_UP]
        if keys[pygame.K_LEFT]:
            ship_angle = (ship_angle - ROTATE_SPEED) % 360
        if keys[pygame.K_RIGHT]:
            ship_angle = (ship_angle + ROTATE_SPEED) % 360
        if thrusting:
            angle_rad = math.radians(ship_angle + SPRITE_OFFSET)
            vel_x += math.cos(angle_rad) * THRUST
            vel_y += math.sin(angle_rad) * THRUST

        if keys[pygame.K_SPACE] and len(lasers) < 10:
            for offset in [-15, 15]:
                angle_rad = math.radians(ship_angle + SPRITE_OFFSET)
                lx = ship_world_x + math.cos(angle_rad) * offset
                ly = ship_world_y + math.sin(angle_rad) * offset
                lasers.append({'x': lx, 'y': ly, 'angle': ship_angle + SPRITE_OFFSET})

        vel_x *= FRICTION
        vel_y *= FRICTION
        ship_world_x += vel_x
        ship_world_y += vel_y

        offset_x = ship_world_x - WIDTH // 2
        offset_y = ship_world_y - HEIGHT // 2

        for sx, sy in stars:
            star_x = (sx - offset_x) % (WIDTH * 2) - WIDTH
            star_y = (sy - offset_y) % (HEIGHT * 2) - HEIGHT
            pygame.draw.circle(screen, (255, 255, 255), (int(star_x), int(star_y)), 1)

        if thrusting:
            glow_dist = 30
            angle_rad = math.radians(ship_angle + SPRITE_OFFSET)
            glow_x = WIDTH // 2 - math.cos(angle_rad) * glow_dist
            glow_y = HEIGHT // 2 - math.sin(angle_rad) * glow_dist
            pygame.draw.ellipse(screen, (0, 100, 255), (glow_x - 8, glow_y - 4, 16, 8))

        rotated = pygame.transform.rotate(ship_orig, -(ship_angle + SPRITE_OFFSET - 90))
        rect = rotated.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        screen.blit(rotated, rect.topleft)

        for laser in lasers[:]:
            laser['x'] += math.cos(math.radians(laser['angle'])) * LASER_SPEED
            laser['y'] += math.sin(math.radians(laser['angle'])) * LASER_SPEED
            lx = laser['x'] - offset_x
            ly = laser['y'] - offset_y
            if not (0 <= lx <= WIDTH and 0 <= ly <= HEIGHT):
                lasers.remove(laser)
            else:
                pygame.draw.circle(screen, (0, 255, 0), (int(lx), int(ly)), 4)

        for blaster in enemy_lasers[:]:
            blaster['x'] += math.cos(blaster['angle']) * ENEMY_LASER_SPEED
            blaster['y'] += math.sin(blaster['angle']) * ENEMY_LASER_SPEED
            sx = blaster['x'] - offset_x
            sy = blaster['y'] - offset_y
            if not (0 <= sx <= WIDTH and 0 <= sy <= HEIGHT):
                enemy_lasers.remove(blaster)
            else:
                pygame.draw.circle(screen, (255, 50, 50), (int(sx), int(sy)), 3)
                if abs(blaster['x'] - ship_world_x) < 15 and abs(blaster['y'] - ship_world_y) < 15:
                    hp = max(0, hp - DAMAGE_PER_HIT)
                    enemy_lasers.remove(blaster)

        non_exploding_enemies = [e for e in enemies if not e.exploding]
        current_max_enemies = max(5, 5 * (2 ** (score // 10)))
        enemy_spawn_timer += 1
        if enemy_spawn_timer > 60 and len(non_exploding_enemies) < current_max_enemies:
            enemies.append(EnemyShip())
            enemy_spawn_timer = 0

        for enemy in enemies[:]:
            if not enemy.update():
                enemies.remove(enemy)
                continue
            ex = enemy.x
            ey = enemy.y
            for laser in lasers[:]:
                dx = laser['x'] - ex
                dy = laser['y'] - ey
                if math.hypot(dx, dy) < 20 and not enemy.exploding:
                    enemy.exploding = True
                    enemy.timer = 30
                    lasers.remove(laser)
                    score += 1
                    break
            enemy.draw(screen, offset_x, offset_y)

        score_text = font.render(f'Rebel Scum Destroyed: {score}', True, (255, 255, 0))
        hp_text = font.render(f'HP: {hp}', True, (0, 255, 0))
        screen.blit(score_text, (10, 10))
        screen.blit(hp_text, (10, HEIGHT - 30))

        pygame.display.flip()

        if hp <= 0:
            show_game_over(score)
            return

def show_game_over(score):
    initials = ""
    game_over = True
    while game_over:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_p:
                continue  # Pausing not needed here
            if event.type == pygame.KEYDOWN and len(initials) < 3:
                if event.key == pygame.K_BACKSPACE:
                    initials = initials[:-1]
                elif event.unicode.isalpha():
                    initials += event.unicode.upper()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN and len(initials) == 3:
                with open("highscores.txt", "a") as f:
                    f.write(f"{initials}: {score}\n")
                return

        screen.fill((0, 0, 0))
        over_text = font.render("GAME OVER", True, (255, 0, 0))
        prompt = font.render("Enter 3-letter initials:", True, (255, 255, 255))
        entry = font.render(initials, True, (0, 255, 0))
        screen.blit(over_text, (WIDTH // 2 - 80, HEIGHT // 2 - 60))
        screen.blit(prompt, (WIDTH // 2 - 140, HEIGHT // 2 - 20))
        screen.blit(entry, (WIDTH // 2 - 20, HEIGHT // 2 + 20))
        pygame.display.flip()
def show_title_screen():
    pygame.font.init()
    font = pygame.font.SysFont("consolas", 20)
    title_font = pygame.font.SysFont("consolas", 36)
    score_font = pygame.font.SysFont("consolas", 18)
    scroll_y = HEIGHT
    scroll_speed = 0.5

    storyline = [
        "You are the commander of one of the last surviving Imperial",
        "Star Destroyers.",
        "After the fall of the Empire, chaos reigns across the galaxy.",
        "Rebel factions swarm the outer rim.",
        "Your loyal crew, defying tradition, name your ship the NIGHTFIRE.",
        "Your mission: hold the line, reclaim order,",
        "and remind them... the Empire never truly dies.",
        "",
        "Press ENTER to begin."
    ]

    def load_scores():
        try:
            with open("highscores.txt", "r") as f:
                lines = [line.strip() for line in f.readlines()][-5:]
        except:
            lines = []
        return lines[::-1]

    pygame.mixer.music.load('assets/saphire.mp3')
    pygame.mixer.music.play(-1)

    clock = pygame.time.Clock()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                return

        screen.fill((0, 0, 0))

        nf_text = title_font.render("Nightfire:", True, (180, 0, 255))
        cmd_text = title_font.render("The Last Command", True, (255, 255, 0))
        screen.blit(nf_text, (WIDTH // 2 - (nf_text.get_width() + cmd_text.get_width() + 10) // 2, 20))
        screen.blit(cmd_text, (WIDTH // 2 - (nf_text.get_width() + cmd_text.get_width() + 10) // 2 + nf_text.get_width() + 10, 20))

        y = scroll_y
        for line in storyline:
            text = font.render(line, True, (255, 255, 0))
            screen.blit(text, (50, int(y)))
            y += 30
        if scroll_y > 100:
            scroll_y -= scroll_speed

        scores = load_scores()
        screen.blit(score_font.render("Top Scores", True, (180, 0, 255)), (WIDTH - 200, HEIGHT - 160))
        for i, score_line in enumerate(scores):
            s_text = score_font.render(score_line, True, (180, 0, 255))
            screen.blit(s_text, (WIDTH - 200, HEIGHT - 130 + i * 25))

        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    show_title_screen()
    run_game()