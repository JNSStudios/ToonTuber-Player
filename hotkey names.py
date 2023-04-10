import pygame
import keyboard
import threading

# Initialize Pygame
pygame.init()

# Set up the display
size = (400, 300)
screen = pygame.display.set_mode(size)
pygame.display.set_caption("Hotkey Names")

# Set up the font
font = pygame.font.SysFont('Calibri', 25, True, False)

# Keep track of the keys that are currently being pressed
keys_pressed = set()

# Define a callback function to handle key presses and releases
def on_press(key):
    try:
        # Add the pressed key to the set of keys being pressed
        keys_pressed.add(key)
        print(f"Key pressed: {key}")
    except AttributeError:
        pass

def on_release(key):
    try:
        # Remove the released key from the set of keys being pressed
        keys_pressed.discard(key)
        print(f"Key released: {key}")
    except AttributeError:
        pass

def keyboard_thread():
    while True:
        event = keyboard.read_event()
        if event.event_type == "down":
            # print(f"Key pressed: {event.name}")
            on_press(event.name)
        elif event.event_type == "up":
            # print(f"Key released: {event.name}")
            on_release(event.name)

keyboard_thread = threading.Thread(target=keyboard_thread)
keyboard_thread.daemon = True
keyboard_thread.start()

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
