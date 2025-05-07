import pygame
import sys
import math
import random

pygame.init()

volume = .5

WIDTH, HEIGHT = 800, 600
FPS = 60
STAR_COUNT = 200
THRUST = 0.1
FRICTION = 0.99
ROTATE_SPEED = 3
LASER_SPEED = 15
SPRITE_OFFSET = 90
STARTING_HP = 20
# How many points to get repairs
REPAIRS_POINTS = 10
# How many HP each repair cycle
REPAIRS_HEALTH = 10
# How many points before capital ships spawn in
CAPITAL_SPAWN_SCORE = 20

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Nightfire: The Last Command")
clock = pygame.time.Clock()
font = pygame.font.SysFont("consolas", 24)

ship_orig = pygame.image.load("assets/ship.png").convert_alpha()
ship_orig = pygame.transform.scale(ship_orig, (60, 60))
enemy_scale = (25, 25)
corvette_scale = (40,40)
frigate_scale = (50,50)
cruiser_scale = (75,75)

awing_img = pygame.transform.scale(pygame.image.load("assets/awing.png").convert_alpha(), enemy_scale)
xwing_img = pygame.transform.scale(pygame.image.load("assets/xwing.png").convert_alpha(), enemy_scale)
ywing_img = pygame.transform.scale(pygame.image.load("assets/ywing.png").convert_alpha(), enemy_scale)
corvette_img = pygame.transform.scale(pygame.image.load("assets/corvette.png").convert_alpha(), corvette_scale)
frigate_img  = pygame.transform.scale(pygame.image.load("assets/frigate.png").convert_alpha(), frigate_scale)
cruiser_img  = pygame.transform.scale(pygame.image.load("assets/cruiser.png").convert_alpha(), cruiser_scale)

awing_img = pygame.transform.rotate(awing_img, 180)
xwing_img = pygame.transform.rotate(xwing_img, 180)
ywing_img = pygame.transform.rotate(ywing_img, 180)
corvette_img = pygame.transform.rotate(corvette_img, 180)
frigate_img  = pygame.transform.rotate( frigate_img, 180)
cruiser_img  = pygame.transform.rotate( cruiser_img, 180)


A_WING = 0
X_WING = 1
Y_WING = 2
enemy_types =         [A_WING, X_WING, Y_WING]
enemy_scale =         [enemy_scale,enemy_scale,enemy_scale]
enemy_minspeed =      [  2.25,      1,     .5]
enemy_maxspeed =      [   3.5,      2,      1]
enemy_fire_interval = [    60,     45,     90]
enemy_laser_speed =   [    12,      6,      4]
enemy_laser_damage =  [     2,      4,      8]
enemy_squadrons    =   [['Blue'],  ['Red'], ['Gold']]
enemy_pilots = [' Leader, no!', ' One under fire!', ' Two losing integrity!', ' Three watch those turbolasers!', ' Four Ahehghghehhgh!', ' Five they came from behind!']
enemy_laser_color =   [(255,255,50), (255,50,50), (150, 150, 255)]
enemy_img = [awing_img, xwing_img, ywing_img]

CORVETTE = 0
FRIGATE  = 1
CRUISER  = 2
capital_types =         [ CORVETTE,  FRIGATE, CRUISER]
capital_scale =         [corvette_scale,frigate_scale,cruiser_scale]
capital_health =        [        3,        6,      12]
capital_minspeed =      [      1.1,      .75,     .25]
capital_maxspeed =      [      2.2,      1.5,     1.0]
capital_fire_interval = [       30,       45,      60]
capital_laser_speed   = [        8,        6,       4]
capital_laser_damage  = [        2,        4,       8]
capital_squadrons     = [['TANTIVE IV', 'LIBERATOR', 'CANDOR', 'THUNDERSTRIKE'], ['VANGUARD', 'REDEMPTION', 'OPPORTUNITY', 'REMEMBRANCE'], ['LIBERTY', 'HOME ONE', 'RADDUS', 'PURGILL']]
capital_pilots = [' taking severe damage!', ' under heavy fire!', ' venting atmosphere!', ' have lost main engines!', ' shields are down!', ' lost manuvering thrusters!', ' bridge has been destroyed!']
capital_laser_color =   [(255,255,50), (255,50,50), (150, 150, 255)]
capital_img = [corvette_img, frigate_img, cruiser_img]

ship_world_x, ship_world_y = 0, 0
ship_angle = 0
vel_x, vel_y = 0, 0
score = 0
hp = STARTING_HP

stars = [(random.randint(-2000, 2000), random.randint(-2000, 2000)) for _ in range(STAR_COUNT)]

lasers = []
enemy_lasers = []
enemies = []
# Start with some enemies right off
enemy_spawn_timer = 300
capital_spawn_timer = 0

class EnemyShip:
    def __init__(self):
        self.type = random.choice(enemy_types)
        self.scale = enemy_scale[self.type]
        self.hitbox = .5*(self.scale[0]**2 + self.scale[1]**2)**.5
        squadron = random.choice(enemy_squadrons[self.type])
        pilot = random.choice(enemy_pilots)
        self.name = squadron + pilot
        self.image = enemy_img[self.type]
        self.x = ship_world_x + random.randint(-WIDTH//2, WIDTH//2)
        self.y = ship_world_y - HEIGHT - random.randint(60, 300)
        self.speed = random.uniform(enemy_minspeed[self.type], enemy_maxspeed[self.type])
        self.exploding = False
        self.damaged = False
        self.damaged_x = 0
        self.damaged_y = 0
        self.timer = 0
        self.fire_timer = random.randint(30, enemy_fire_interval[self.type])
        self.laser_speed = enemy_laser_speed
        self.laser_color = enemy_laser_color
        self.laser_damage = enemy_laser_damage
        self.health = 1

    def update(self):
        if self.exploding:
            self.timer -= 1
            return self.timer > 0
        else:
            if self.damaged:
                self.timer_damaged -= 1
                if self.timer_damaged < 0:
                    self.damaged = False
            self.y += self.speed
            self.fire_timer -= 1
            if self.fire_timer <= 0:
                self.fire()
                self.fire_timer = enemy_fire_interval[self.type]
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
            "angle": angle,
            "laser_speed": self.laser_speed[self.type],
            "color" : self.laser_color[self.type],
            "damage" : self.laser_damage[self.type],
        })

    def draw(self, surface, offset_x, offset_y):
        cx = int(self.x - offset_x)
        cy = int(self.y - offset_y)
        if self.exploding:
            pygame.draw.circle(surface, (255, 0, 0), (cx + self.scale[0]/2, cy + self.scale[1]/2), self.hitbox*.75)
        else:
            surface.blit(self.image, (self.x - offset_x, self.y - offset_y))
            if self.damaged:
                pygame.draw.circle(surface, (255, 255, 0), (cx + self.damaged_x + self.scale[0]/2, cy + self.damaged_y + self.scale[1]/2), 10)
            # pygame.draw.circle(surface, (0,255,0), (cx, cy), 5) # debug, top left of sprite
            # pygame.draw.circle(surface, (0,0,255), (cx + self.scale[0]/2, cy + self.scale[1]/2), 5) # debug, center of sprite

class CapitalShip(EnemyShip):
    def __init__(self):        
        self.type = random.choice(capital_types)
        self.scale = capital_scale[self.type]
        self.hitbox = .45 * (self.scale[0]**2 + self.scale[1]**2)**.5        
        squadron = random.choice(capital_squadrons[self.type])
        pilot = random.choice(capital_pilots)
        self.name = squadron + pilot
        self.image = capital_img[self.type]
        self.x = ship_world_x + random.randint(-WIDTH//2, WIDTH//2)
        self.y = ship_world_y - HEIGHT - random.randint(60, 300)
        self.speed = random.uniform(capital_minspeed[self.type], capital_maxspeed[self.type])
        self.exploding = False
        self.damaged = False
        self.damaged_x = 0
        self.damaged_y = 0        
        self.timer = 0
        self.timer_damaged = 0
        self.fire_timer = random.randint(30, capital_fire_interval[self.type])
        self.laser_speed = capital_laser_speed
        self.laser_color = capital_laser_color
        self.laser_damage = capital_laser_damage
        self.health = capital_health[self.type]

def laser_turrets(hp):
    if hp < 15:
        return 1
    if hp < 50:
        return 3
    if hp < 70:
        return 5
    if hp < 101:
        return 7

def laser_accuracy(hp):
    if hp < 35:
        return random.choice((-15,-10,-5,0,5,10,15))
    if hp < 65:
        return random.choice((-10,-5,0,0,0,5,10))
    if hp < 101:
        return 0

def laser_recycle(hp):
    if hp < 20:
        return 60
    if hp < 40:
        return 45
    if hp < 60:
        return 30
    if hp < 80:
        return 20
    if hp < 101:
        return 15

def run_game():
    paused = False
    global ship_world_x, ship_world_y, vel_x, vel_y, ship_angle, score, hp, enemy_spawn_timer, capital_spawn_timer
    running = True
    radio_call = ''
    radio_call_timer = 0
    repairs_counter = 0
    repairs_timer = 0
    repairs_report = ''
    laser_delay = 0

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
        if keys[pygame.K_MINUS]:
            volume = volume - .05
            if volume < 0:
                volume = 0
            pygame.mixer.music.set_volume(volume)
        if keys[pygame.K_PLUS]:
            volume = volume + .05
            if volume > 1:
                volume = 1
            pygame.mixer.music.set_volume(volume)

        if laser_delay > 0:
            laser_delay -= 1
        if laser_delay == 0:
            laser_status = (50, 255, 50)
        elif laser_delay < (laser_recycle(hp) * .25):
            laser_status = (255,255, 50)
        else:
            laser_status = (255, 50, 50)

        if keys[pygame.K_SPACE] and len(lasers) < laser_turrets(hp):
            if laser_delay == 0:
                laser_delay = laser_recycle(hp)
                for offset in [-10, 10]:
                    angle_rad = -math.radians(ship_angle + SPRITE_OFFSET)
                    lx = ship_world_x + math.sin(angle_rad) * offset
                    ly = ship_world_y + math.cos(angle_rad) * offset
                    lasers.append({'x': lx, 'y': ly, 'angle': ship_angle + SPRITE_OFFSET + laser_accuracy(hp)})

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
            blaster['x'] += math.cos(blaster['angle']) * blaster['laser_speed']
            blaster['y'] += math.sin(blaster['angle']) * blaster['laser_speed']
            sx = blaster['x'] - offset_x
            sy = blaster['y'] - offset_y
            if not (0 <= sx <= WIDTH and 0 <= sy <= HEIGHT):
                enemy_lasers.remove(blaster)
            else:
                pygame.draw.circle(screen, blaster['color'], (int(sx), int(sy)), 3)
                if abs(blaster['x'] - ship_world_x) < 15 and abs(blaster['y'] - ship_world_y) < 15:
                    hp = max(0, hp - blaster['damage'])
                    enemy_lasers.remove(blaster)

        non_exploding_enemies = [e for e in enemies if not e.exploding]
        current_max_enemies = max(5, 5 * (2 ** (score // 10)))
        # Enemies spawn every 30 ticks until the first 20 are killed, then they spawn faster and faster
        current_enemy_timer = min(30, 60 * (2 ** ( (0-current_max_enemies)/20)))
        current_capital_timer = min(120, 480 * (2 ** ( (0-current_max_enemies)/10)))
        # but no faster than every 5 ticks (about 70 kills), 10 ticks for capitals
        current_enemy_timer = max(current_enemy_timer, 5)
        current_capital_timer = max(current_capital_timer, 10)
        enemy_spawn_timer += 1
        if score > CAPITAL_SPAWN_SCORE:
            capital_spawn_timer += 1
        if enemy_spawn_timer > current_enemy_timer and len(non_exploding_enemies) < current_max_enemies:
            enemies.append(EnemyShip())
            enemy_spawn_timer = enemy_spawn_timer - current_enemy_timer
        if capital_spawn_timer > current_capital_timer and len(non_exploding_enemies) < (current_max_enemies + 5):
            enemies.append(CapitalShip())
            capital_spawn_timer = capital_spawn_timer - current_capital_timer

        for enemy in enemies[:]:
            if not enemy.update():
                enemies.remove(enemy)
                continue
            # Offset for center of sprite
            ex = enemy.x + (enemy.scale[0]/2)
            ey = enemy.y + (enemy.scale[1]/2)

            for laser in lasers[:]:
                dx = laser['x'] - ex
                dy = laser['y'] - ey
                if math.hypot(dx, dy) < enemy.hitbox and not enemy.exploding:
                    enemy.health -= 1
                    enemy.damaged = True
                    enemy.timer_damaged = 20
                    enemy.damaged_x = dx
                    enemy.damaged_y = dy
                    lasers.remove(laser)
                    score += 1
                    repairs_counter += 1
                    if enemy.health == 0:
                        enemy.damaged = False
                        enemy.timer_damaged = 0
                        enemy.exploding = True
                        enemy.timer = 30
                        radio_call = enemy.name
                        radio_call_timer = 90
                        break
            enemy.draw(screen, offset_x, offset_y)
        if radio_call_timer > 0:
            radio_call_timer -= 1
        else:
            radio_call = ''

        if repairs_counter >= REPAIRS_POINTS:
            repairs_counter -= REPAIRS_POINTS
            repairs_timer = 90
            hp = hp + REPAIRS_HEALTH
            repairs_report = "Repairs completed!"
            if hp > 100:
                hp = 100
        if repairs_timer > 0:
            repairs_timer -= 1
        else:
            repairs_report = ''
        
        if hp < 20:
            hp_color = (255,0,0)
        elif hp < 50:
            hp_color = (255,255,0)
        elif hp < 75:
            hp_color = (255,255,255)
        elif hp < 101:
            hp_color = (0, 255, 0)

        score_text = font.render(f'Rebel Scum Destroyed: {score}', True, (255, 255, 0))
        hp_text = font.render(f'HP: {hp}', True, hp_color)
        laser_text = font.render( "Turbolasers", True, laser_status)
        radio_text = font.render(radio_call, True, (0, 255, 255))
        repairs_text = font.render(repairs_report, True, (200, 200, 200))

        screen.blit(score_text, (10, 10))
        screen.blit(hp_text, (10, HEIGHT - 30))
        screen.blit(repairs_text, (10, HEIGHT - 50))
        screen.blit(laser_text, (10, HEIGHT - 70))
        screen.blit(radio_text, (10,40) )

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
    global volume
    pygame.font.init()
    font = pygame.font.SysFont("consolas", 20)
    title_font = pygame.font.SysFont("consolas", 36)
    score_font = pygame.font.SysFont("consolas", 18)
    scroll_y = HEIGHT
    scroll_speed = 0.5

    storyline = [
        "You are the commander of one of the last",
        "surviving Imperial Star Destroyers.",
        "After the fall of the Empire, chaos reigns",
        "across the galaxy.",
        "Rebel factions swarm the outer rim.",
        "Your loyal crew, defying tradition, name your ship",
        "",
        "     THE NIGHTFIRE",
        "",
        "Your mission: hold the line, reclaim order,",
        "and remind them... the Empire never truly dies.",
        "",
        "Press ENTER to begin.",
        "P to Pause.",
        "- to Lower volume. = to Raise volume.",
        "ALT-F4 to Quit.",
        "Every " + str(REPAIRS_POINTS) + " kills heals " + str(REPAIRS_HEALTH) + " hp",
        "and will improve ship performance ",

    ]

    def load_scores():
        try:
            with open("highscores.txt", "r") as f:
                lines = [line.strip() for line in f.readlines()][-5:]
        except:
            lines = []
        return lines[::-1]

    pygame.mixer.music.load('assets/saphire.mp3')
    pygame.mixer.music.set_volume(volume)
    pygame.mixer.music.play(-1)

    clock = pygame.time.Clock()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_MINUS:
                volume = volume - .05
                if volume < 0:
                    volume = 0
                pygame.mixer.music.set_volume(volume)
            if event.type == pygame.KEYDOWN and event.key == pygame.K_EQUALS:
                volume = volume + .05
                if volume > 1:
                    volume = 1
                pygame.mixer.music.set_volume(volume)
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
            y += 28
        if scroll_y > 80:
            scroll_y -= scroll_speed

        scores = load_scores()
        screen.blit(score_font.render("Top Scores", True, (180, 0, 255)), (WIDTH - 120, HEIGHT - 160))
        for i, score_line in enumerate(scores):
            s_text = score_font.render(score_line, True, (180, 0, 255))
            screen.blit(s_text, (WIDTH - 120, HEIGHT - 130 + i * 25))

        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    show_title_screen()
    run_game()