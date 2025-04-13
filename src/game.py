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
WIDTH, HEIGHT = 400, 600
LANES = [120, 280]  # Only 2 lanes: left and right
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
            packet = serialInst.readline()
            move = packet.decode('utf-8').strip().lower()
            if "left" in move:
                motion_value = "left"
            elif "right" in move:
                motion_value = "right"
            else:
                motion_value = None
    except serial.serialutil.SerialException:
        print("Serial error")

def draw(player_rect, obstacles, score):
    screen.blit(background_img, (0, 0))

    # Draw lanes
    for lane_x in LANES:
        pygame.draw.line(screen, (220, 220, 220), (lane_x, 0), (lane_x, HEIGHT), 2)

    # Animate player
    global player_frame_index, player_frame_timer
    now = pygame.time.get_ticks()
    if now - player_frame_timer > player_frame_delay:
        player_frame_index = (player_frame_index + 1) % len(player_frames)
        player_frame_timer = now
    screen.blit(player_frames[player_frame_index], player_rect)

    # Draw obstacles
    for obs in obstacles:
        screen.blit(obs['image'], obs['rect'])

    # Draw score
    score_surf = font.render(f"Score: {score}", True, WHITE)
    screen.blit(score_surf, (10, 10))

    pygame.display.flip()

def game_loop():
    global motion_value
    player_lane = 0
    player_rect = pygame.Rect(LANES[player_lane] - 50, HEIGHT - 100, 100, 100)

    obstacles = []
    obstacle_timer = 0
    obstacle_interval = 1500

    score = 0
    start_time = pygame.time.get_ticks()
    speed = 5

    running = True
    while running:
        read_serial()
        current_time = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    motion_value = "left"
                elif event.key == pygame.K_RIGHT:
                    motion_value = "right"

        if motion_value == "left":
            player_lane = max(0, player_lane - 1)
            player_rect.x = LANES[player_lane] - 50
            motion_value = None
        elif motion_value == "right":
            player_lane = min(1, player_lane + 1)
            player_rect.x = LANES[player_lane] - 50
            motion_value = None

        if current_time - obstacle_timer > obstacle_interval:
            lane = random.choice([0, 1])
            obstacle_type = random.choice([obstacle1_img, obstacle2_img])
            obs_rect = pygame.Rect(LANES[lane] - 50, -40, 100, 100)
            obstacles.append({
                'rect': obs_rect,
                'base_image': obstacle_type,
                'image': obstacle_type,
                'lane': lane
            })
            obstacle_timer = current_time

        for obs in obstacles:
            obs['rect'].y += speed

            depth = obs['rect'].y / HEIGHT
            scale = max(0.4, min(1.0, depth))

            base_img = obs['base_image']
            new_width = int(100 * scale)
            new_height = int(100 * scale)
            obs['image'] = pygame.transform.scale(base_img, (new_width, new_height))

            lane_center = LANES[obs['lane']]
            obs['rect'].width = new_width
            obs['rect'].height = new_height
            obs['rect'].centerx = lane_center

        obstacles = [obs for obs in obstacles if obs['rect'].y < HEIGHT]

        for obs in obstacles:
            obs_rect = pygame.Rect(obs[0], obs[1], OBSTACLE_WIDTH, OBSTACLE_HEIGHT)
            if char_rect.colliderect(obs_rect):
                game_over = True
                bg_music.stop()
                hit_sound.play()
                return score

        score = (current_time - start_time) // 100
        speed = 5 + score // 20
        obstacle_interval = max(400, 1500 - score * 5)

        draw(player_rect, obstacles, score)
        clock.tick(30)

def show_game_over(score):
    pygame.mixer.stop()  # Stop all sounds
    game_over_sound = pygame.mixer.Sound(os.path.join(ASSETS, "hit.mp3"))
    game_over_sound.play(loops=-1)

    # Dramatic red-black flickering background
    flicker_colors = [(200, 0, 0), (30, 0, 0), (100, 0, 0)]
    flicker_index = 0
    flicker_timer = pygame.time.get_ticks()

    # Fonts
    big_font = pygame.font.SysFont("impact", 60)
    msg = big_font.render("GAME OVER!", True, RED)
    score_msg = font.render(f"Final Score: {score}", True, (255, 255, 0))
    restart_msg = font.render("Press R to Restart or Q to Quit", True, (0, 255, 255))

    # Flashing loop
    flash_duration = 2000  # ms
    flash_start = pygame.time.get_ticks()

    while True:
        current = pygame.time.get_ticks()

        if current - flicker_timer > 150:
            flicker_index = (flicker_index + 1) % len(flicker_colors)
            flicker_timer = current

        screen.fill(flicker_colors[flicker_index])
        screen.blit(msg, (WIDTH // 2 - msg.get_width() // 2, 180))
        screen.blit(score_msg, (WIDTH // 2 - score_msg.get_width() // 2, 260))
        screen.blit(restart_msg, (WIDTH // 2 - restart_msg.get_width() // 2, 320))

        # Optional: glitch effect
        if current - flash_start < flash_duration:
            for _ in range(3):
                x_offset = random.randint(-5, 5)
                y_offset = random.randint(-5, 5)
                screen.blit(msg, (WIDTH // 2 - msg.get_width() // 2 + x_offset, 180 + y_offset))

    pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    return True
                elif event.key == pygame.K_q:
                    return False


# ----------------- MAIN LOOP -----------------
while True:
    final_score = game_loop()
    if not show_game_over(final_score):
        break