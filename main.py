import pygame
import math, json, os
from pprint import pprint
import logging

WIDTH, HEIGHT = 900, 800
BANNER_HEIGHT = 200
FPS = 60

# create logger
logger = logging.getLogger("shooting_game")
logger.setLevel(logging.DEBUG)
# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
# create formatter
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
# add formatter to ch
ch.setFormatter(formatter)
# add ch to logger
logger.addHandler(ch)

# initialise enemy coordinates
def initialise_enemy(targets_type):
    enemy_coordinates = {f"level_{i+1}": [[] for _ in range(len(targets_type[i + 1]))] for i in range(3)}
    for k, (name_coord, coord_list) in enumerate(enemy_coordinates.items()):
        for i in range(len(coord_list)):
            for j in range(targets_type[k + 1][i]):
                # TODO rework coordinates so it takes into account the number of enemy types (3 or 4)
                coord_list[i].append((WIDTH // targets_type[k + 1][i] * j, 300 - i * 100 + 30 * (j % 2)))
    return enemy_coordinates


def reset_stats():
    global menu, time_elapsed, total_shot, good_shots, ammo, total_ammo, time_remaining, score, counter, targets_type, enemy_coordinates
    good_shots, total_shot, ammo, total_ammo = 0, 0, 5, 5 # TODO change back to 81
    time_remaining, time_elapsed, score, counter = 10, 0, 0, 1 # TODO change time remaining
    enemy_coordinates = initialise_enemy(targets_type)


def initialise_sounds():
    global plate_sound, bird_sound,laser_sound
    pygame.mixer.init()
    pygame.mixer.music.load("assets/sounds/bg_music.mp3")
    plate_sound = pygame.mixer.Sound("assets/sounds/Broken plates.wav")
    plate_sound.set_volume(.2)
    bird_sound = pygame.mixer.Sound("assets/sounds/Drill Gear.mp3")
    bird_sound.set_volume(.2)
    laser_sound = pygame.mixer.Sound("assets/sounds/Laser gun.wav")
    laser_sound.set_volume(.3)
    pygame.mixer.music.play()

pygame.init()
timer = pygame.time.Clock()
font = pygame.font.Font("assets/font/myFont.ttf", 32)
big_font = pygame.font.Font("assets/font/myFont.ttf", 72)
screen = pygame.display.set_mode([WIDTH, HEIGHT])

initialise_sounds()



background, banners, guns, targets = [], [], [], [[], [], []]
# targets_type = {1: [2, 1, 1], 2: [2, 1, 1], 3: [2, 1, 1, 1]}
targets_type = {1: [10, 5, 3], 2: [12, 8, 5], 3: [15, 12, 8, 3]}
level = 0
shot = False
# 0-Freeplay, 1-Accuracy, 2-timed
mode = 0
reset_stats()
menu, game_over, pause, clicked = True, False, True, False
if os.path.exists("best_score.json"):
    with open("best_score.json", "r") as json_file:
        best_score = json.load(json_file)
else:
    best_score = {"freeplay": 0, "timed": 0, "accuracy": 0}
menu_img = pygame.image.load(f"assets/menus/mainMenu.png")
game_over_img = pygame.image.load(f"assets/menus/gameOver.png")
pause_img = pygame.image.load(f"assets/menus/pause.png")

for i in range(3):
    background.append(pygame.image.load(f"assets/bgs/{i+1}.png"))
    banners.append(pygame.image.load(f"assets/banners/{i+1}.png"))
    guns.append(pygame.transform.scale(pygame.image.load(f"assets/guns/{i+1}.png"), (100, 100)))
    for j in range(len(targets_type[i + 1])):
        targets[i].append(
            pygame.transform.scale(pygame.image.load(f"assets/targets/{i+1}/{j+1}.png"), (102 - j * 18, 68 - j * 12))
        )
logger.debug(f"{targets}")


def draw_gun():
    mouse_pos = pygame.mouse.get_pos()
    gun_point = (WIDTH / 2, HEIGHT - BANNER_HEIGHT)
    lasers = ["red", "purple", "green"]
    clicks = pygame.mouse.get_pressed()
    if mouse_pos[0] != gun_point[0]:
        slope = (mouse_pos[1] - gun_point[1]) / (mouse_pos[0] - gun_point[0])
    else:
        slope = -1_000_000
    angle = math.atan(slope)
    rotation = math.degrees(angle)
    if mouse_pos[0] < WIDTH / 2:
        gun = pygame.transform.flip(guns[level - 1], True, False)
        if mouse_pos[1] < HEIGHT - BANNER_HEIGHT:
            screen.blit(pygame.transform.rotate(gun, 90 - rotation), (WIDTH / 2 - 90, HEIGHT - 250))
            if clicks[0]:
                pygame.draw.circle(screen, lasers[level - 1], mouse_pos, 5)
    else:
        gun = guns[level - 1]
        if mouse_pos[1] < HEIGHT - BANNER_HEIGHT:
            screen.blit(pygame.transform.rotate(gun, 270 - rotation), (WIDTH / 2 - 30, HEIGHT - 250))
            if clicks[0]:
                pygame.draw.circle(screen, lasers[level - 1], mouse_pos, 5)


def draw_level(coords):
    target_rects = [[] for _ in range(len(targets_type[level]))]
    for i in range(len(coords)):
        for j in range(len(coords[i])):
            target_rects[i].append(pygame.rect.Rect(coords[i][j][0] + 20, coords[i][j][1], 60 - i * 12, 60 - i * 12))
            screen.blit(targets[level - 1][i], coords[i][j])
    return target_rects


def move_level(coords):
    for i in range(len(coords)):
        for j in range(len(coords[i])):
            my_coords = coords[i][j]
            coords[i][j] = (((my_coords[0] + 150 - 2 ** i) % (WIDTH + 150) - 150), my_coords[1])
    return coords


def check_shot(targets, coords):
    global score
    mouse_pos = pygame.mouse.get_pos()
    hit_target = False
    for i in range(len(targets)):
        for j, target in enumerate(targets[i]):
            if target.collidepoint(mouse_pos):
                coords[i].pop(j)
                score += 10 * (i ** 2 + 1)
                hit_target = True
                if level == 1:
                    bird_sound.play()
                elif level == 2:
                    plate_sound.play()
                elif level ==3:
                    laser_sound.play()
    return coords, hit_target


def draw_score():
    score_text = font.render(f"Points: {score}", True, "black")
    screen.blit(score_text, (320, 660))
    shots_text = font.render(f"Shots: {good_shots}/{total_shot}", True, "black")
    screen.blit(shots_text, (320, 687))
    time_text = font.render(f"Time Elapsed: {time_elapsed}", True, "black")
    screen.blit(time_text, (320, 714))
    if mode == 0:
        mode_text = font.render(f"Freeplay", True, "black")
    elif mode == 1:
        mode_text = font.render(f"Ammo: {ammo}/{total_ammo}", True, "black")
    elif mode == 2:
        mode_text = font.render(f"Time Remaining: {time_remaining}", True, "black")
    screen.blit(mode_text, (320, 741))


def draw_menu():
    global game_over, pause, mode, level, menu, time_elapsed, total_shot, good_shots, best_score, clicked
    game_over = False
    pause = False
    screen.blit(menu_img, (0, 0))
    mouse_pos = pygame.mouse.get_pos()
    clicks = pygame.mouse.get_pressed()
    freeplay_button = pygame.rect.Rect((170, 524), (260, 100))
    ammo_button = pygame.rect.Rect((475, 524), (260, 100))
    timed_button = pygame.rect.Rect((170, 661), (260, 100))
    reset_button = pygame.rect.Rect((475, 661), (260, 100))
    screen.blit(font.render(f'{best_score["freeplay"]}', True, "black"), (340, 580))
    screen.blit(font.render(f'{best_score["accuracy"]}', True, "black"), (650, 580))
    screen.blit(font.render(f'{best_score["timed"]}', True, "black"), (350, 710))
    if freeplay_button.collidepoint(mouse_pos) and clicks[0] and not clicked:
        mode = 0
        reset_game()
    if ammo_button.collidepoint(mouse_pos) and clicks[0] and not clicked:
        mode = 1
        reset_game()
    if timed_button.collidepoint(mouse_pos) and clicks[0] and not clicked:
        mode = 2
        reset_game()
    if reset_button.collidepoint(mouse_pos) and clicks[0] and not clicked:
        best_score = {"freeplay": 0, "timed": 0, "accuracy": 0}
        clicked = True


def reset_game():
    global level, menu, clicked
    level = 1
    menu = False
    clicked = True
    # TODO check if OK for the reset
    reset_stats()


def draw_game_over():
    global clicked, run, menu, pause
    screen.blit(game_over_img, (0, 0))
    if mode == 0: 
        display_score = time_elapsed
    else:
        display_score = score
    mouse_pos = pygame.mouse.get_pos()
    clicks = pygame.mouse.get_pressed()
    exit_button = pygame.rect.Rect((170, 661), (260, 100))
    menu_button = pygame.rect.Rect((475, 661), (260, 100))
    screen.blit(big_font.render(f'{display_score}', True,'black'), (650, 578))
    if menu_button.collidepoint(mouse_pos) and clicks[0] and not clicked:
        menu = True
        pause = False
        clicked = True
    if exit_button.collidepoint(mouse_pos) and clicks[0] and not clicked:
        run = False
    


def draw_pause():
    global level, pause, clicked, resume_level, menu
    screen.blit(pause_img, (0, 0))
    mouse_pos = pygame.mouse.get_pos()
    clicks = pygame.mouse.get_pressed()
    resume_button = pygame.rect.Rect((170, 661), (260, 100))
    menu_button = pygame.rect.Rect((475, 661), (260, 100))
    if resume_button.collidepoint(mouse_pos) and clicks[0] and not clicked:
        level = resume_level
        pause = False
        clicked = True
    if menu_button.collidepoint(mouse_pos) and clicks[0] and not clicked:
        menu = True
        pause = False
        clicked = True


run = True
def write_score_to_file(best_score):
    # Serializing json
    json_object = json.dumps(best_score, indent=4)
            # Writing to best_score.json
    with open("best_score.json", "w") as outfile:
        outfile.write(json_object)

while run:
    timer.tick(FPS)

    screen.fill("black")
    screen.blit(background[level - 1], (0, 0))
    screen.blit(banners[level - 1], (0, HEIGHT - BANNER_HEIGHT))
    if menu:
        level = 0
        draw_menu()
    if game_over:
        level = 0
        draw_game_over()
    if pause:
        level = 0
        draw_pause()

    if level > 0:
        if counter < 60:
            counter += 1
        else:
            counter = 1
            time_elapsed += 1
            if mode == 2:
                time_remaining -= 1
        draw_gun()
        draw_score()
        target_boxes = draw_level(enemy_coordinates[f"level_{level}"])
        enemy_coordinates[f"level_{level}"] = move_level(enemy_coordinates[f"level_{level}"])
        if shot:
            enemy_coordinates[f"level_{level}"], hit_target = check_shot(
                target_boxes, enemy_coordinates[f"level_{level}"]
            )
            shot = False
            if hit_target:
                good_shots += 1

        if not any(target_boxes) and level < 3:
            level += 1
        elif (
            (not any(target_boxes) and level == 3) or (mode == 1 and ammo == 0) or (mode == 2 and time_remaining <= 0)
        ):
            draw_game_over()
            game_over = True
            if mode == 0 and (time_elapsed < best_score["freeplay"] or best_score["freeplay"] == 0):
                best_score["freeplay"] = time_elapsed
            if mode == 1 and score > best_score["accuracy"]:
                best_score["accuracy"] = score
            if mode == 2 and score > best_score["timed"]:
                best_score["timed"] = score
            

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
            write_score_to_file(best_score)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_position = pygame.mouse.get_pos()
            if (0 < mouse_position[0] < WIDTH) and (0 < mouse_position[1] < HEIGHT - BANNER_HEIGHT):
                shot = True
                total_shot += 1
                if mode == 1:
                    ammo -= 1
            if (670 < mouse_position[0] < 860) and (660 < mouse_position[1] < 715):
                resume_level = level
                pause = True
                clicked = True
            if (670 < mouse_position[0] < 860) and (715 < mouse_position[1] < 760):
                menu = True
                clicked = True

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1 and clicked:
            clicked = False

    pygame.display.flip()

pygame.quit()
