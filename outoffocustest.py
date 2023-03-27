import pygame
from pynput import keyboard

# Initialize Pygame
pygame.init()

# Set up the display
size = (400, 300)
screen = pygame.display.set_mode(size)
pygame.display.set_caption("Displaying Keys Pressed")

# Set up the font
font = pygame.font.SysFont('Calibri', 25, True, False)

# Keep track of the keys that are currently being pressed
keys_pressed = set()

# Define a callback function to handle key presses and releases
def on_press(key):
    try:
        # Add the pressed key to the set of keys being pressed
        keys_pressed.add(key.char)
        print(f"Key pressed: {key.char}")
    except AttributeError:
        pass

def on_release(key):
    try:
        # Remove the released key from the set of keys being pressed
        released_key = key.char
        keys_pressed.discard(released_key)
        print(f"Key released: {released_key}")
    except AttributeError:
        pass

# Set up a listener for key presses and releases
listener = keyboard.Listener(on_press=on_press, on_release=on_release)
listener.start()

# Main game loop
done = False
while not done:
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            done = True

    # Clear the screen
    screen.fill((255, 255, 255))

    # Draw the keys being pressed on the screen
    for key in keys_pressed:
        text = font.render(key, True, (0, 0, 0))
        screen.blit(text, (size[0] // 2 - text.get_width() // 2, size[1] // 2 - text.get_height() // 2))

    # Update the screen
    pygame.display.flip()

# Quit Pygame and stop the listener
pygame.quit()
listener.stop()
