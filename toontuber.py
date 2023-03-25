# just an FYI a lot of this was done by chatgpt lol

import pygame

pygame.init()

# Set up the Pygame window
width, height = 750, 750
screen = pygame.display.set_mode((width, height))

# Define some colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)

# Define the font for the text options
font = pygame.font.Font(None, 50)

text_settings = font.render("SETTINGS", True, BLACK)

# Define the clickable text options
text_options = [
    {"text": "New", "position": (0, 50)},
    {"text": "Open", "position": (0, 100)},
    {"text": "Edit", "position": (0, 150)}
]

# Define a variable to keep track of whether the settings screen is active
settings_active = False

# Define a function to draw the text options on the screen
def draw_text_options():
    for option in text_options:
        text = font.render(option["text"], True, WHITE)
        text_rect = text.get_rect(left=option["position"][0], centery=option["position"][1])
        screen.blit(text_settings, (0, 0))
        screen.blit(text, text_rect)

# Define a function to darken the screen
def darken_screen():
    darken_surface = pygame.Surface((width, height))
    darken_surface.fill(BLACK)
    darken_surface.set_alpha(128)
    screen.blit(darken_surface, (0, 0))

# Define a function to display the FPS counter
def display_fps(clock):
    fps = str(int(clock.get_fps()))
    fps_text = font.render(fps, True, WHITE)
    fps_rect = fps_text.get_rect(bottomright=(width, height))
    screen.blit(fps_text, fps_rect)

# Create a Pygame clock object to measure time between frames
clock = pygame.time.Clock()

# Main Pygame loop
running = True
while running:
    # Measure the time between frames and limit the FPS to 60
    delta_time = clock.tick(60) / 1000.0

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_p:
            settings_active = not settings_active

    # Draw the green background
    screen.fill(GREEN)

    # If the settings screen is active, darken the screen and draw the text options
    if settings_active:
        darken_screen()
        draw_text_options()
        # Display the FPS counter in the bottom right corner
        display_fps(clock)

    # Update the Pygame window
    pygame.display.flip()

# Quit Pygame
pygame.quit()
