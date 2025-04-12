import serial
import pygame
import random
import serial.tools.list_ports
import serial.serialutil

# --- SERIAL SETUP ---
serialInst = serial.Serial()
serialInst.baudrate = 115200
serialInst.port = '/dev/cu.usbserial-110'  # Change to your port
serialInst.open()
motion_value = None  # Shared variable updated by serial

def read_serial():
    global motion_value
    try:
        if serialInst.in_waiting:
            packet = serialInst.readline()
            move = packet.decode('utf-8').strip()
            if 'right' in move:
                motion_value = 0
            elif 'left' in move:
                motion_value = 1
            print("Serial:", move)
    except serial.serialutil.SerialException:
        print('Serial read error')

# --- GAME CONFIG ---
WIDTH, HEIGHT = 400, 600
LANES = [120, 280]  # Only 2 lanes

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 36)

# --- COLORS ---
WHITE = (255, 255, 255)
BLUE = (50, 150, 255)
BLACK = (0, 0, 0)
RED = (255, 50, 50)

# --- FUNCTIONS ---
def draw(player_rect, obstacles, score):
    screen.fill(WHITE)

    for lane_x in LANES:
        pygame.draw.line(screen, (220, 220, 220), (lane_x, 0), (lane_x, HEIGHT), 2)

    pygame.draw.rect(screen, BLUE, player_rect)

    for obs in obstacles:
        pygame.draw.rect(screen, RED, obs)

    score_surf = font.render(f"Score: {score}", True, BLACK)
    screen.blit(score_surf, (10, 10))

    pygame.display.flip()

def game_loop():
    global motion_value
    player_lane = 0
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

        if motion_value is not None:
            if motion_value == 1:
                player_lane = max(0, player_lane - 1)
            elif motion_value == 0:
                player_lane = min(1, player_lane + 1)
            player_rect.x = LANES[player_lane] - 20
            motion_value = None  # Reset after move

        # Create new obstacles
        if current_time - obstacle_timer > obstacle_interval:
            lane = random.choice([0, 1])
            obs = pygame.Rect(LANES[lane] - 20, -40, 40, 40)
            obstacles.append(obs)
            obstacle_timer = current_time

        for obs in obstacles:
            obs.y += speed

        obstacles = [obs for obs in obstacles if obs.y < HEIGHT]

        for obs in obstacles:
            if player_rect.colliderect(obs):
                return score

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

# --- MAIN LOOP ---
while True:
    final_score = game_loop()
    if not show_game_over(final_score):
        break
