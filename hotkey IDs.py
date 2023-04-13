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
keys_pressed_IDs = []
keys_pressed_Names = []


# Define a callback function to handle key presses and releases
def on_press(code, key):
    try:
        # Add the pressed key to the set of keys being pressed
        if(code not in keys_pressed_IDs):
            keys_pressed_IDs.append(code)
        if(key not in keys_pressed_Names):
            keys_pressed_Names.append(key)
        print(f"Key pressed: ID: {code} Name: {key}")
    except AttributeError:
        pass

def on_release(code, key):
    try:
        # Remove the released key from the set of keys being pressed
        while(code in keys_pressed_IDs):
            keys_pressed_IDs.remove(code)
        while(key in keys_pressed_Names):
            keys_pressed_Names.remove(key)
        print(f"Key released: ID: {code} Name: {key}")
    except AttributeError:
        pass

def keyboard_thread():
    while True:
        event = keyboard.read_event()
        if event.event_type == "down":
            on_press(event.scan_code, event.name)
        elif event.event_type == "up":
            on_release(event.scan_code, event.name)

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


    keysPressedSTR = []
    keysPressedSTR.clear()
    for i in range(0, len(keys_pressed_IDs)):
        
        keysPressedSTR.append(f"\"{keys_pressed_Names[i]}\" = ID of \"{keys_pressed_IDs[i]}\"")
    i = 0
    for str in keysPressedSTR:
        text = font.render(str, True, (0, 0, 0))
        screen.blit(text, (size[0] // 2 - text.get_width() // 2, i*35))
        i += 1

    # Update the screen
    pygame.display.flip()

# Quit Pygame and stop the listener
pygame.quit()
