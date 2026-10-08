import pygame
import random
import math


# Initialize Pygame
pygame.init()

# %% Defining constants and Loading sprites & fonts

# Define constants for the new larger screen size
WIDTH, HEIGHT = 1200, 800  # Screen size
FPS = 60
SHIP_RADIUS = 15
ASTEROID_RADIUS = 30
BULLET_RADIUS = 8           # Increased bullet size
ASTEROID_SPLIT_SIZE = 30    # Increased size for the smallest asteroid
SHIP_SIZE = 40
MOVE_THRESHOLD = 5          # Distance threshold for ship to move

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

# Set up the game screen
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Asteroid Game")

# Load sprites and images (relative paths)
asteroid_image = pygame.image.load("Assets/Asteroid Brown.png").convert_alpha()

ship_image = pygame.image.load("Assets/Space Ship.png").convert_alpha()
ship_image = pygame.transform.scale(ship_image, (SHIP_SIZE * 2, SHIP_SIZE * 2))

bullet_image = pygame.image.load("Assets/Bullet.png").convert_alpha()
bullet_image = pygame.transform.scale(bullet_image, (BULLET_RADIUS * 8, BULLET_RADIUS * 2))

background_image_sheet = pygame.image.load("Assets/Background.png").convert_alpha()
background_image_sheet = pygame.transform.scale(background_image_sheet, (1200, 3200))

# Fonts
font = pygame.font.Font("Assets/ARCADECLASSIC.ttf", 30)

# Set variables for lives cooldown    
startup_cooldown = 4000 # Grace period at start of game for losing lives
game_start_time = pygame.time.get_ticks() # Store time of start-up
lives_cooldown = 1500 # Set cooldown time for losing lives, milliseconds
last_hit = 0 # Initialise time since last life lost    
number_lives = 3 # Initialise number of lives

score_count = 0 # Initialise score counter
# %%


# %% Defining classes (ship, bullet, asteroid)

# Ship class (includes movement and rotation)
class Ship:
    def __init__(self, x, y, angle, speed): # Ship has x,y coordinates, angle, speed and size
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = speed
        self.size = SHIP_SIZE

    def move_towards(self, target_x, target_y): # Function that moves the ship towards target (later this will be used to follow the mouse)
        dx, dy = target_x - self.x, target_y - self.y
        distance = math.sqrt(dx**2 + dy**2)
        if distance > MOVE_THRESHOLD:  # Only move if the ship is far enough from the mouse, wrong setting may cause "vibration" effect
            dx, dy = dx / distance * self.speed, dy / distance * self.speed
            self.x += dx
            self.y += dy

    def rotate(self, direction):    # Function that rotates the ship (changes its angle)
        self.angle += direction

    def draw(self):
        ship_image_loaded = pygame.transform.rotate(ship_image,-self.angle-90) # Rotate pre-loaded sprite
        screen.blit(ship_image_loaded, ship_image_loaded.get_rect(center=(int(self.x), int(self.y))))
        
# Bullet class (handles movement)
class Bullet:    
    def __init__(self, x, y, angle):   # Bullet has x,y coordinates and an angle
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = 10  # Increased speed for visibility, should speed be defined here?
        self.dx = math.cos(math.radians(angle)) * self.speed
        self.dy = math.sin(math.radians(angle)) * self.speed

    def move(self):    # Move bullet
        self.x += self.dx
        self.y += self.dy

    def draw(self):
        bullet_image_loaded = pygame.transform.rotate(bullet_image,-self.angle) # Adjusted to have bullet at correct angle
        screen.blit(bullet_image_loaded, bullet_image_loaded.get_rect(center=(int(self.x), int(self.y))))

# Asteroid class (handles movement and splitting)
class Asteroid:
    def __init__(self, x, y, size, angle, speed):  # Asteroid has x,y coordinates, size, angle and speed
        self.x = x
        self.y = y
        self.size = size
        self.angle = angle
        self.speed = speed
        self.dx = math.cos(math.radians(angle)) * self.speed
        self.dy = math.sin(math.radians(angle)) * self.speed

    def move(self):         # Asteroids wrap around the screen, ship and bullets shouldn't, unless you think it makes the game better!
        self.x += self.dx
        self.y += self.dy
        # Wrap around the screen edges
        if self.x < 0:
            self.x = WIDTH
        elif self.x > WIDTH:
            self.x = 0
        if self.y < 0:
            self.y = HEIGHT
        elif self.y > HEIGHT:
            self.y = 0

    def draw(self): #Draw
        asteroid_image_loaded = pygame.transform.scale(asteroid_image, (self.size * 2, self.size * 2)) # Create asteroids of variable size, = 2*radius
        screen.blit(asteroid_image_loaded, asteroid_image_loaded.get_rect(center=(int(self.x), int(self.y))))

    def split(self):    #Split asteroid when hit and return two new asteroids, new asteroids should be smaller
        if self.size > ASTEROID_SPLIT_SIZE:
            new_size = self.size / 2 # Asteroid is split in half
            new_speed = random.randint(1, 3) # A new speed is randomly selected
            return [
                Asteroid(self.x, self.y, new_size, self.angle + random.randint(-45, 45), new_speed),
                Asteroid(self.x, self.y, new_size, self.angle + random.randint(-45, 45), new_speed)
            ]
        
        return []
    

# %%
    
    
# %% Collisions physics function

def bounce(asteroidA, asteroidB):    # Collisions physics implementation for colliding asteroids
    dx = asteroidB.x - asteroidA.x  # Find x component of separation
    dy = asteroidB.y - asteroidA.y  # Find y component of separation
    asteroid_separation = math.sqrt(dx**2 + dy**2)  # Calculate vector separation
    
    if asteroid_separation == 0:
        asteroid_separation += 1e-8 # Nudge separation to never == 0
    

    # Find vector of normal in x and y
    nx = dx / asteroid_separation
    ny = dy / asteroid_separation
    
    # Calculate relative velocity in x and y
    rvx = asteroidA.dx - asteroidB.dx
    rvy = asteroidA.dy - asteroidB.dy
    
    # Calculate velocity along vector normal
    normal_velocity = rvx*nx + rvy*ny
    
    if normal_velocity > 0:
        return
    
    # Calculate mass as proportional for area = size^2
    m1 = asteroidA.size ** 2
    m2 = asteroidB.size ** 2
    
    # Elastic impulse scalar
    j = -(1 + 1.0) * normal_velocity
    j /= (1/m1 + 1/m2)
    
    # Apply impulse
    impulse_x = j * nx
    impulse_y = j * ny
    
    asteroidA.dx += impulse_x / m1
    asteroidA.dy += impulse_y / m1
    asteroidB.dx -= impulse_x / m2
    asteroidB.dy -= impulse_y / m2
    
    # Positional correction to prevent overlap/'sticking together' - when asteroids split
    overlap = (asteroidA.size + asteroidB.size) - asteroid_separation
    correction = overlap / (1/m1 + 1/m2)

    asteroidA.x -= correction * nx / m1
    asteroidA.y -= correction * ny / m1
    asteroidB.x += correction * nx / m2
    asteroidB.y += correction * ny / m2

# %%
 

# %% Rolling background function

frame = 0 # initialise variable frame
def run_background(sheet): # Defines function that calls individual frames of the background, scrolling down by one pixel at a time
    global frame # Have 'frame' increase by one each frame
    
    frame = (frame + 1) % sheet.get_height() # Move background down 1 pixel per frame
    
    # Loop bottom and top of background image for a continuous scroll
    screen.blit(sheet,(0,frame-sheet.get_height())) 
    screen.blit(sheet,(0,frame))
    
# %%
   
# %% Initialising lists

# Initialize the ship, bullets lists, and asteroids list
ship = Ship(WIDTH // 2, HEIGHT // 2, 0, 10)
bullets = []
asteroids = []
for _ in range(5):
    asteroids.append(Asteroid(random.randint(0, WIDTH), random.randint(0, HEIGHT),
                         random.randint(30, 60), random.randint(0, 360),
                         random.randint(1, 3)))
                
# %%

# %% The main game

# Main game loop
clock = pygame.time.Clock()
running = True
shooting = False
pygame.mouse.set_visible(False) # Hide the cursor and create a custom red dot cursor

while running:
        
# %%% Set up screen
    screen.fill(BLACK)  # Background screen color
    
    # Display background image    
    run_background(background_image_sheet) 
    
    # Display lives and score
    score_text = font.render(f"Score {score_count}", True, WHITE)
    lives_text = font.render(f"Lives {number_lives}", True, WHITE)
    
    screen.blit(score_text, (10, 40))
    screen.blit(lives_text, (10, 10))
    
    game_over = False
# %%%
    
# %%% Events
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        # esc to quit
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            # Reset everything
            running = False
            pygame.QUIT
            
        # r to restart
        if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
            # Reset everything
            number_lives = 3
            score_count = 0
            bullets = []
            asteroids = []
            for _ in range(5):
                asteroids.append(Asteroid(random.randint(0, WIDTH), random.randint(0, HEIGHT),
                                     random.randint(30, 60), random.randint(0, 360),
                                     random.randint(1, 3)))

            ship.x, ship.y = WIDTH // 2, HEIGHT // 2
            ship.angle = 0
            last_hit = 0
            game_start_time = pygame.time.get_ticks()
            game_over = False
            continue # Jumps back to start of loop
            
        # Shoot on left click (only one bullet at a time)
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: # Left-click
                if not shooting: # Prevent multiple bullets per click
                    bullets.append(Bullet(ship.x, ship.y, ship.angle))
                    shooting = True
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1: # Left-click
                shooting = False
# %%%
       

# %%% Moving and shooting
    # Get mouse position
    mouse_x, mouse_y = pygame.mouse.get_pos()

    # Move the ship towards the mouse
    ship.move_towards(mouse_x, mouse_y)

    # Handle ship rotation (Q and E keys)
    keys = pygame.key.get_pressed()
    if keys[pygame.K_q]:
        ship.rotate(-5)  # Rotate counterclockwise
    if keys[pygame.K_e]:
        ship.rotate(5)  # Rotate clockwise

    # Move and draw bullets
    for bullet in bullets:
        bullet.move()
        bullet.draw()
        if bullet.x < 0 or bullet.x > WIDTH or bullet.y < 0 or bullet.y > HEIGHT:
            bullets.remove(bullet)
# %%%

# %%% Asteroids and collisions
    # Move and draw asteroids

    asteroids_to_remove = []  # List of asteroids to remove
    new_asteroids = []  # List of new asteroids to add
    big_asteroids = [] # Keep track of asteroids that are big/haven't been hit yet

    for asteroidA in asteroids:
        asteroidA.move()
        asteroidA.draw()
        # Check for collisions with other asteroids
        for asteroidB in asteroids:
            if asteroidA != asteroidB: # Ensure asteroid isn't 'colliding' with itself
                asteroid_separation = math.sqrt((asteroidA.x - asteroidB.x)**2+(asteroidA.y - asteroidB.y)**2) # Calculate distance between asteroids
                if asteroid_separation < asteroidA.size + asteroidB.size: # Decides if asteroids are colliding with eachother 
                    # Have colliding asteroids 'bounce' off of eachother, following laws of momentum conservation
                    bounce(asteroidA,asteroidB)
        # Check for collisions with ship & update lives counter
        ship_separation = math.sqrt((asteroidA.x - ship.x)**2+(asteroidA.y - ship.y)**2) # Calculate distance between ship and any asteroid
        # Don't let player lose lives within first 4 seconds of game start
        current_time = pygame.time.get_ticks()
        if current_time - game_start_time < startup_cooldown:
            invulnerable = True
        else:
            invulnerable = False
        if invulnerable == False:
            if number_lives <= 0:
                # Game over if lives drop to zero
                game_over_text = font.render('Game Over!',True,(WHITE))
                screen.blit(game_over_text,(game_over_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 10))))   
                # Give player option to restart game
                restart_text = font.render('Press R to Restart',True,(WHITE))
                screen.blit(restart_text,(restart_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 30))))
                game_over = True
                # Detect restart input
            if game_over == False: # Check if game is still running
            # Check for collisions with ship
                if ship_separation <= ship.size + asteroidA.size:
                    # Lose a life if a life hasn't been lost is last 2 seconds
                    if current_time - last_hit > lives_cooldown:
                        number_lives -= 1
                        pygame.display.flip()
                        last_hit = current_time # Update time of last hit
        
        if game_over == False:
            for bullet in bullets:
                if math.sqrt((asteroidA.x - bullet.x)**2+(asteroidA.y - bullet.y)**2) < asteroidA.size + BULLET_RADIUS:
                    # Mark the asteroid for removal and split it into new asteroids
                    score_count += round(1000 / asteroidA.size) # Increase score by bigger number for smaller asteroids (more difficult target)
                    pygame.display.flip()
                    asteroids_to_remove.append(asteroidA)
                    bullets.remove(bullet)
                    new_asteroids.extend(asteroidA.split())
        
                   
    # After the loop, remove destroyed asteroids and add new ones from splitting
    for asteroid in asteroids_to_remove:
        if asteroid in asteroids:
            asteroids.remove(asteroid)
    asteroids.extend(new_asteroids)
    
    # Ensure asteroids keep being generated, for small number of asteroids or if too many asteroids are tiny
    big_asteroids = []
    new_asteroid = Asteroid(random.randint(0, WIDTH), random.randint(0, HEIGHT),
                         random.randint(30, 60), random.randint(0, 360),
                         random.randint(1, 3))
    # Measure how many asteroids are 'big'
    for asteroid in asteroids:
        if asteroid.size > 30:
            big_asteroids.append(asteroid)
    # Add new asteroid until there are enough big asteroids
    while len(big_asteroids) < 3:
        asteroids.append(new_asteroid)
        big_asteroids.append(new_asteroid)
# %%%
                 
    # Draw the ship
    ship.draw()
    # Draw the custom cursor (red dot)
    pygame.draw.circle(screen, RED, (mouse_x, mouse_y), 1)  # Custom cursor size set to 5
    # Update the display
    pygame.display.update()
    # Limit the frame rate
    clock.tick(FPS)
    
# Quit the game
pygame.quit()

# %%