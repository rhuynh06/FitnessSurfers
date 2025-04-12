import serial
import pygame
import random
import serial.tools.list_ports
import serial.serialutil

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
LANES = [120, 280]  # Only 2 lanes: left and right
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("ESP32 Motion-Controlled Game")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 36)

# ----------------- LOAD SPRITES -----------------
player_img = pygame.image.load("images/player.png").convert_alpha()
player_img = pygame.transform.scale(player_img, (100, 100))

obstacle_img = pygame.image.load("images/obstacle.png").convert_alpha()
obstacle_img = pygame.transform.scale(obstacle_img, (40, 40))

# ----------------- COLORS -----------------
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 50, 50)

# ----------------- FUNCTIONS -----------------
def read_serial():
    global motion_value
    try:
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
    screen.fill(WHITE)

    # Draw lanes
    for lane_x in LANES:
        pygame.draw.line(screen, (220, 220, 220), (lane_x, 0), (lane_x, HEIGHT), 2)

    # Draw player
    screen.blit(player_img, player_rect)

    # Draw obstacles
    for obs in obstacles:
        screen.blit(obstacle_img, obs)

    # Draw score
    score_surf = font.render(f"Score: {score}", True, BLACK)
    screen.blit(score_surf, (10, 10))

    pygame.display.flip()

def game_loop():
    global motion_value
    player_lane = 0  # Start in left lane
    player_rect = pygame.Rect(LANES[player_lane] - 20, HEIGHT - 100, 40, 40)
    
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

        # PIR-controlled movement
        if motion_value == "left":
            player_lane = max(0, player_lane - 1)
            player_rect.x = LANES[player_lane] - 20
            motion_value = None
        elif motion_value == "right":
            player_lane = min(1, player_lane + 1)
            player_rect.x = LANES[player_lane] - 20
            motion_value = None

        # Spawn obstacle
        if current_time - obstacle_timer > obstacle_interval:
            lane = random.choice([0, 1])
            obs = pygame.Rect(LANES[lane] - 20, -40, 40, 40)
            obstacles.append(obs)
            obstacle_timer = current_time

        # Move obstacles
        for obs in obstacles:
            obs.y += speed

        # Remove off-screen
        obstacles = [obs for obs in obstacles if obs.y < HEIGHT]

        # Collision check
        for obs in obstacles:
            if player_rect.colliderect(obs):
                return score

        # Score and difficulty
        score = (current_time - start_time) // 100
        speed = 5 + score // 20
        obstacle_interval = max(400, 1500 - score * 5)

        draw(player_rect, obstacles, score)
        clock.tick(30)

def show_game_over(score):
    screen.fill(WHITE)
    msg = font.render("Game Over!", True, RED)
    score_msg = font.render(f"Final Score: {score}", True, BLACK)
    restart_msg = font.render("Press R to Restart or Q to Quit", True, BLACK)
    screen.blit(msg, (WIDTH // 2 - msg.get_width() // 2, 200))
    screen.blit(score_msg, (WIDTH // 2 - score_msg.get_width() // 2, 250))
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

# ----------------- MAIN LOOP -----------------
while True:
    final_score = game_loop()
    if not show_game_over(final_score):
        break
