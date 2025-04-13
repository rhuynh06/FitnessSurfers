# game.py
import pygame
import random
import time
import threading
import serial.tools.list_ports

# Setup serial port
def setup_serial():
    ports = serial.tools.list_ports.comports()
    for port in ports:
        if "usbserial" in port.device or "USB" in port.device:
            return serial.Serial(port.device, 115200, timeout=1)
    print("No suitable serial port found.")
    exit()

serialInst = setup_serial()
time.sleep(2)
serialInst.reset_input_buffer()

# Game constants
WIDTH, HEIGHT = 800, 600
LANES = [WIDTH // 4, WIDTH // 2, 3 * WIDTH // 4]
CHARACTER_WIDTH = 80
OBSTACLE_WIDTH = 80
OBSTACLE_HEIGHT = 80
FPS = 60

# Initialize pygame
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("ESP32 Controlled Game")
clock = pygame.time.Clock()

# Load assets
bg = pygame.transform.scale(pygame.image.load("assets/bg.jpg"), (WIDTH, HEIGHT))
character = pygame.transform.scale(pygame.image.load("assets/character.png"), (CHARACTER_WIDTH, CHARACTER_WIDTH))
obstacle_img = pygame.transform.scale(pygame.image.load("assets/obstacle1.jpg"), (OBSTACLE_WIDTH, OBSTACLE_HEIGHT))

# Load sounds
bg_music = pygame.mixer.Sound("assets/bg_music.mp3")
hit_sound = pygame.mixer.Sound("assets/hit.mp3")

bg_music.play(-1)  # Loop background music

# Game state
char_lane = 1
obstacles = []
obstacle_timer = 0
score = 0
game_over = False
motion_value = None
motion_lock = threading.Lock()
last_move_time = 0
move_cooldown = 300  # milliseconds

# Thread to read serial data
def read_serial():
    global motion_value
    while True:
        if serialInst.in_waiting:
            try:
                line = serialInst.readline().decode('utf-8').strip()
                if line in ['1', '2', '3']:
                    with motion_lock:
                        motion_value = int(line)
            except:
                continue

serial_thread = threading.Thread(target=read_serial, daemon=True)
serial_thread.start()

def get_motion_command():
    global motion_value, last_move_time
    now = pygame.time.get_ticks()
    with motion_lock:
        mv = motion_value
        if mv is not None and now - last_move_time > move_cooldown:
            last_move_time = now
            motion_value = None
            return mv
    return None

# Main loop
running = True
while running:
    clock.tick(FPS)
    screen.blit(bg, (0, 0))

    if not game_over:
        # Handle input
        mv = get_motion_command()
        if mv == 1:
            char_lane = max(0, char_lane - 1)
        elif mv == 3:
            char_lane = min(2, char_lane + 1)

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            char_lane = max(0, char_lane - 1)
        if keys[pygame.K_RIGHT]:
            char_lane = min(2, char_lane + 1)

        # Generate obstacles
        obstacle_timer += 1
        if obstacle_timer > 60:
            obstacle_lane = random.randint(0, 2)
            obstacles.append([LANES[obstacle_lane] - OBSTACLE_WIDTH // 2, -OBSTACLE_HEIGHT])
            obstacle_timer = 0

        # Move obstacles
        for obs in obstacles:
            obs[1] += 7

        # Check collisions
        char_x = LANES[char_lane] - CHARACTER_WIDTH // 2
        char_y = HEIGHT - CHARACTER_WIDTH - 20
        char_rect = pygame.Rect(char_x, char_y, CHARACTER_WIDTH, CHARACTER_WIDTH)

        for obs in obstacles:
            obs_rect = pygame.Rect(obs[0], obs[1], OBSTACLE_WIDTH, OBSTACLE_HEIGHT)
            if char_rect.colliderect(obs_rect):
                game_over = True
                bg_music.stop()
                hit_sound.play()
                break

        # Draw character
        screen.blit(character, (char_x, char_y))

        # Draw obstacles
        for obs in obstacles:
            screen.blit(obstacle_img, obs)

        # Update score
        score += 1
        font = pygame.font.SysFont(None, 36)
        score_text = font.render(f"Score: {score}", True, (255, 255, 255))
        screen.blit(score_text, (10, 10))
    else:
        font = pygame.font.SysFont(None, 72)
        text = font.render("Game Over!", True, (255, 0, 0))
        screen.blit(text, (WIDTH // 2 - 150, HEIGHT // 2 - 50))

    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    pygame.display.flip()

pygame.quit()
serialInst.close()