import pygame

pygame.init()

# Set up the window
size = (750, 750)
screen = pygame.display.set_mode(size)
pygame.display.set_caption("My Game")

# Define some colors
GREEN = (0, 255, 0)
BLACK = (0, 0, 0)

# Set up the font
font = pygame.font.SysFont(None, 48)

# Set up the text to be displayed
text = font.render("Hello, world!", True, BLACK)

# Flag to determine if the P key has been pressed
show_text = False

# Main game loop
done = False
while not done:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            done = True
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p:
                # Toggle the flag to show the text
                show_text = not show_text

    # Fill the background with green
    screen.fill(GREEN)

    # If the P key has been pressed, darken the screen and display the text
    if show_text:
        # Create a surface to darken the screen
        darken_surface = pygame.Surface(size)
        darken_surface.fill(BLACK)
        darken_surface.set_alpha(128)
        screen.blit(darken_surface, (0, 0))

        # Display the text on top of the darkened screen
        screen.blit(text, (size[0] // 2 - text.get_width() // 2, size[1] // 2 - text.get_height() // 2))

    # Update the screen
    pygame.display.flip()

# Quit the game
pygame.quit()
