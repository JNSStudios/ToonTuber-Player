import pygame
import math
import pyaudio
import numpy as np
import threading
import time
import sys
import select

pygame.init()

# Set up the Pygame window
width, height = 750, 750
screen = pygame.display.set_mode((width, height))
rms = 0

# audio stuff

chunk_size = 256  # number of audio samples per chunk
sample_rate = 44100  # number of samples per second

pa = pyaudio.PyAudio()

def callback(in_data, frame_count, time_info, status):
    global rms
    # convert audio data to a numpy array
    audio = np.frombuffer(in_data, dtype=np.int16)
    
    # calculate the root mean square (RMS) amplitude
    rmsNEW = np.sqrt(np.mean(np.square(audio)))
    if(not np.isnan(rmsNEW)):
        rms = rmsNEW
    else:
        rms = 100
    print(rms)
    
    # return None and continue streaming
    return (None, pyaudio.paContinue)

# Open the stream with the callback function
stream = pa.open(format=pyaudio.paInt16,
                 channels=1,
                 rate=sample_rate,
                 input=True,
                 frames_per_buffer=chunk_size,
                 stream_callback=callback)


# def audio_input():
#     global rms
#     while True:

#         if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
#             # process the window event
#             event = input()
#             if event == 'quit':
#                 break
#             else:
#                 print(event)

#         # try to read audio data from the stream
#         try:
#             data = stream.read(chunk_size, exception_on_overflow=False)
#         except IOError:
#             # ignore overflow errors
#             continue
        
#         # convert audio data to a numpy array
#         audio = np.frombuffer(data, dtype=np.int16)
        
#         # calculate the root mean square (RMS) amplitude
#         rmsNEW = np.sqrt(np.mean(np.square(audio)))

#         if(not np.isnan(rmsNEW)):
#             rms = rmsNEW
#         else:
#             rms = 100
#         print(rms)
        

# create a separate thread for audio input
audio_thread = threading.Thread(target=callback)
audio_thread.daemon = True
audio_thread.start()


# Define some colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)

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

# Load the sprites
mic_feedback = pygame.image.load("micLevel.png").convert_alpha()
mic_range = pygame.image.load("micRange.png").convert_alpha()

#get original size of both sprites
mic_feed_orig = mic_feedback.get_size()

# find the new height for the sprites, 7% of the screen height, and the width based on the ratio and that height
mic_newHeight = int(0.07*height)
mic_newWidth = int(mic_newHeight * (mic_feed_orig[0] / mic_feed_orig[1]))


# Resize the sprites
mic_feedback = pygame.transform.smoothscale(mic_feedback, (mic_newWidth, mic_newHeight))
mic_range = pygame.transform.smoothscale(mic_range, (mic_newWidth, mic_newHeight))

# Get the original height of the mic_fill sprite
mic_fill_height_orig = mic_feedback.get_height()



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
        # these values assume that the top left corner of the sprite is 0,0
        # therefore, the bottom right of the sprite is the width and height
        
        
        micFill_clipHeight = round((mic_feedback.get_height() * (rms/100)))
        clip_rect = pygame.Rect(0, mic_feedback.get_height() - micFill_clipHeight, mic_feedback.get_width(), micFill_clipHeight)
        mic_fill_clipped = pygame.Surface((clip_rect.width, clip_rect.height), pygame.SRCALPHA)
        mic_fill_clipped.blit(mic_feedback, (0, 0), clip_rect)
        screen.blit(mic_fill_clipped, (0, height - mic_fill_clipped.get_height()))

        # draw mic range sprite a little next to the mic fill sprite
        screen.blit(mic_range, (mic_fill_clipped.get_width()/3, height - mic_range.get_height()))

    # Update the Pygame window
    pygame.display.flip()

# Quit Pygame
pygame.quit()
