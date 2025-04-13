import serial
import pygame
import random
import serial.tools.list_ports
import serial.serialutil
from PIL import Image
import os
from ai import generate_game_over_text

# ----------------- SERIAL SETUP -----------------
ports = serial.tools.list_ports.comports()
serialInst = serial.Serial()
serialInst.baudrate = 115200
serialInst.port = '/dev/cu.usbserial-110'  # <-- Change if needed
serialInst.open()
motion_value = None  # None = no new motion

# ----------------- GAME SETUP -----------------
pygame.init()
WIDTH, HEIGHT = 400, 600
LANES = [100, 200, 300]  # Three lanes: left, middle, and right
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("ESP32 Motion-Controlled Game")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Impact", 25)

# ----------------- ASSET PATH -----------------
ASSETS = "assets"

# ----------------- LOAD GIF FRAMES -----------------
def load_gif_frames(path, scale=(100, 100)):
    gif = Image.open(path)
    frames = []
    try:
        while True:
            frame = gif.convert("RGBA")
            mode = frame.mode
            size = frame.size
            data = frame.tobytes()

            surface = pygame.image.fromstring(data, size, mode)
            surface = pygame.transform.scale(surface, scale)
            frames.append(surface)
            gif.seek(gif.tell() + 1)
    except EOFError:
        pass
    return frames

# Load animated character.gif frames
gif_path = os.path.join(ASSETS, "character.gif")
player_frames = load_gif_frames(gif_path)
player_frame_index = 0
player_frame_timer = 0
player_frame_delay = 100

# ----------------- LOAD OTHER ASSETS -----------------
background_img = pygame.image.load(os.path.join(ASSETS, "background.png"))
background_img = pygame.transform.scale(background_img, (WIDTH, HEIGHT))

obstacle1_img = pygame.image.load(os.path.join(ASSETS, "obstacle1.jpg")).convert_alpha()
obstacle2_img = pygame.image.load(os.path.join(ASSETS, "obstacle2.jpg")).convert_alpha()

obstacle1_img = pygame.transform.scale(obstacle1_img, (100, 100))
obstacle2_img = pygame.transform.scale(obstacle2_img, (100, 100))

# ----------------- COLORS -----------------
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 50, 50)

# ----------------- SOUNDS -----------------
bg_music = pygame.mixer.Sound(os.path.join(ASSETS, "bg_music.mp3"))
hit_sound = pygame.mixer.Sound(os.path.join(ASSETS, "hit.mp3"))

bg_music.play(-1, 0, 5000)

# ----------------- FUNCTIONS -----------------
def read_serial():
    global motion_value
    try:
        if serialInst.in_waiting:
            packet = serialInst.readline()
            move = packet.decode('utf-8').strip().lower()
            print(f"Received packet: {move}")
            if "1" in move:
                motion_value = "left"
            elif "3" in move:
                motion_value = "right"
            elif "2" in move:
                motion_value = "mid"
            else:
                motion_value = None
    except serial.serialutil.SerialException:
        print("Serial error")

def draw(player_rect, obstacles, score, motion_display_text):
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

    # Draw obstacles (only scale the visual representation)
    for obs in obstacles:
        screen.blit(obs['image'], obs['rect'])

    # Draw score
    score_surf = font.render(f"Score: {score}", True, WHITE)
    screen.blit(score_surf, (10, 10))

    # Draw motion detection status
    motion_text = font.render(f"Motion: {motion_display_text}", True, RED)
    screen.blit(motion_text, (WIDTH // 2 - motion_text.get_width() // 2, HEIGHT - 50))

    pygame.display.flip()

def game_loop():
    global motion_value
    bg_music.play(-1, 0, 5000)
    player_lane = 1  # Start in the middle lane
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
                elif event.key == pygame.K_DOWN:
                    motion_value = "mid"

        if motion_value == "left":
            player_lane = max(0, player_lane - 1)
            player_rect.x = LANES[player_lane] - 50
            # motion_value = None
        elif motion_value == "right":
            player_lane = min(2, player_lane + 1)
            player_rect.x = LANES[player_lane] - 50
            # motion_value = None
        elif motion_value == "mid":
            player_lane = 1  # Center lane
            player_rect.x = LANES[player_lane] - 50
            # motion_value = None

        if current_time - obstacle_timer > obstacle_interval:
            lane = random.choice([0, 1, 2])
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

        obstacles = [obs for obs in obstacles if obs['rect'].y < HEIGHT]

        for obs in obstacles:
            if player_rect.colliderect(obs['rect']):
                pygame.mixer.stop()
                hit_sound.play()
                return score

        score = (current_time - start_time) // 200
        speed = 2 + score // 40
        obstacle_interval = max(1000, 3000 - score * 2)

        motion_display_text = "No Motion"
        if motion_value == "left":
            motion_display_text = "Left"
        elif motion_value == "right":
            motion_display_text = "Right"
        elif motion_value == "mid":
            motion_display_text = "Middle"

        draw(player_rect, obstacles, score, motion_display_text)
        clock.tick(30)

def wrap_text(text, font, max_width):
    words = text.split()
    lines = []
    current_line = ""
    
    for word in words:
        test_line = current_line + " " + word if current_line else word
        if font.size(test_line)[0] <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    
    return lines

def show_game_over(score):
    pygame.mixer.stop()
    game_over_sound = pygame.mixer.Sound(os.path.join(ASSETS, "hit.mp3"))
    game_over_sound.play(loops=-1)

    flicker_colors = [(200, 0, 0), (30, 0, 0), (100, 0, 0)]
    flicker_index = 0
    flicker_timer = pygame.time.get_ticks()

    big_font = pygame.font.SysFont("Impact", 60)
    font = pygame.font.SysFont("Impact", 25)

    # Get the AI game over message
    try:
        ai_msg_text = generate_game_over_text()
    except Exception as e:
        print("AI error:", e)
        ai_msg_text = "Better luck next time!"

    msg = big_font.render("GAME OVER!", True, RED)

    try:
        ai_msg_text = generate_game_over_text()
    except Exception as e:
        print("AI error:", e)
        ai_msg_text = "Better luck next time!"

    ai_msg_lines = wrap_text(ai_msg_text, font, WIDTH - 40)
    score_msg = font.render(f"Final Score: {score}", True, (255, 255, 0))
    restart_msg = font.render("Press R to Restart or Q to Quit", True, (0, 255, 255))

    flash_duration = 2000
    flash_start = pygame.time.get_ticks()

    while True:
        current = pygame.time.get_ticks()
        if current - flicker_timer > 150:
            flicker_index = (flicker_index + 1) % len(flicker_colors)
            flicker_timer = current

        screen.fill(flicker_colors[flicker_index])
        screen.blit(msg, (WIDTH // 2 - msg.get_width() // 2, 180))
        screen.blit(score_msg, (WIDTH // 2 - score_msg.get_width() // 2, 240))
        for i, line in enumerate(ai_msg_lines):
            line_surf = font.render(line, True, (255, 100, 255))
            screen.blit(line_surf, (WIDTH // 2 - line_surf.get_width() // 2, 270 + i * 30))
        restart_y = 270 + len(ai_msg_lines) * 30 + 20  # 30px per line, +20 padding
        screen.blit(restart_msg, (WIDTH // 2 - restart_msg.get_width() // 2, restart_y))

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
                    pygame.mixer.stop()
                    return True
                elif event.key == pygame.K_q:
                    return False

# ----------------- MAIN LOOP -----------------
while True:
    final_score = game_loop()
    if not show_game_over(final_score):
        break
