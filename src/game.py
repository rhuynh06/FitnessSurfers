import serial
import pygame
import random
import serial.tools.list_ports
import serial.serialutil
import os

# SERIAL SETUP
ports = serial.tools.list_ports.comports()
serialInst = serial.Serial()
serialInst.baudrate = 115200
serialInst.port = '/dev/cu.usbserial-110'
serialInst.open()
motion_value = None

# GAME SETUP
pygame.init()
WIDTH, HEIGHT = 400, 600
LANES = [80, 220]  # 2 colorful lanes
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("💥 MEME MOTION MADNESS 💥")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Comic Sans MS", 32)

# COLORS
RAINBOW = [(255,0,0),(255,127,0),(255,255,0),(0,255,0),(0,0,255),(75,0,130),(148,0,211)]
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# LOAD ASSETS
asset = lambda f: os.path.join("assets", f)

player_img = pygame.image.load(asset("player.png")).convert_alpha()
player_img = pygame.transform.scale(player_img, (120, 120))

obstacle_img = pygame.image.load(asset("obstacle.png")).convert_alpha()
obstacle_img = pygame.transform.scale(obstacle_img, (100, 100))

pygame.mixer.music.load(asset("bg_music.mp3"))
pygame.mixer.music.set_volume(0.4)
pygame.mixer.music.play(-1)

sfx_hit = pygame.mixer.Sound(asset("hit.wav"))
sfx_jump = pygame.mixer.Sound(asset("jump.wav"))

# SERIAL READER
def read_serial():
    global motion_value
    try:
        if serialInst.in_waiting:
            move = serialInst.readline().decode('utf-8').strip().lower()
            if "left" in move:
                motion_value = "left"
            elif "right" in move:
                motion_value = "right"
            else:
                motion_value = None
    except serial.serialutil.SerialException:
        print("Serial error")

# DRAW EVERYTHING
def draw(player_rect, obstacles, score, color_index):
    screen.fill(RAINBOW[color_index % len(RAINBOW)])

    for x in LANES:
        pygame.draw.line(screen, BLACK, (x + 60, 0), (x + 60, HEIGHT), 6)

    screen.blit(player_img, player_rect)
    for obs in obstacles:
        screen.blit(obstacle_img, obs)

    text = font.render(f"Score: {score}", True, WHITE)
    screen.blit(text, (10, 10))
    pygame.display.flip()

# GAME LOOP
def game_loop():
    global motion_value
    player_lane = 0
    player_rect = pygame.Rect(LANES[player_lane], HEIGHT - 140, 100, 100)

    obstacles = []
    obstacle_timer = 0
    obstacle_interval = 1500

    score = 0
    start_time = pygame.time.get_ticks()
    speed = 5
    color_index = 0

    running = True
    while running:
        read_serial()
        current_time = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

        if motion_value == "left":
            if player_lane > 0:
                player_lane -= 1
                sfx_jump.play()
            motion_value = None
        elif motion_value == "right":
            if player_lane < 1:
                player_lane += 1
                sfx_jump.play()
            motion_value = None

        player_rect.x = LANES[player_lane]

        if current_time - obstacle_timer > obstacle_interval:
            lane = random.choice([0, 1])
            obs = pygame.Rect(LANES[lane], -120, 100, 100)
            obstacles.append(obs)
            obstacle_timer = current_time

        for obs in obstacles:
            obs.y += speed

        obstacles = [obs for obs in obstacles if obs.y < HEIGHT]

        for obs in obstacles:
            if player_rect.colliderect(obs):
                sfx_hit.play()
                return score

        score = (current_time - start_time) // 100
        speed = 5 + score // 20
        obstacle_interval = max(500, 1500 - score * 4)

        color_index += 1
        draw(player_rect, obstacles, score, color_index)
        clock.tick(30)

# GAME OVER SCREEN
def show_game_over(score):
    screen.fill(BLACK)
    msg = font.render("💀 You got MEMED 💀", True, WHITE)
    score_msg = font.render(f"Score: {score}", True, WHITE)
    restart_msg = font.render("R = Retry  |  Q = Quit", True, WHITE)
    screen.blit(msg, (WIDTH // 2 - msg.get_width() // 2, 180))
    screen.blit(score_msg, (WIDTH // 2 - score_msg.get_width() // 2, 240))
    screen.blit(restart_msg, (WIDTH // 2 - restart_msg.get_width() // 2, 300))
    pygame.display.flip()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    return True
                elif event.key == pygame.K_q:
                    return False

# MAIN LOOP
while True:
    final_score = game_loop()
    if not show_game_over(final_score):
        break
