import pygame
import math
import pyaudio
import numpy as np
import threading
import time
import sys
import select
import keyboard
import tkinter as tk
from tkinter import filedialog

pygame.init()

# Set up the Pygame window
width, height = 750, 750
screen = pygame.display.set_mode((width, height))
rms = 0

# Set the window name
pygame.display.set_caption("Toon Tuber Player")


# audio stuff
chunk_size = 256  # number of audio samples per chunk
sample_rate = 44100  # number of samples per second

pa = pyaudio.PyAudio()

def audio_callback(in_data, frame_count, time_info, status):
    global rms
    # convert audio data to a numpy array
    audio = np.frombuffer(in_data, dtype=np.int16)

    # calculate the root mean square (RMS) amplitude
    rmsNEW = np.sqrt(np.mean(np.square(audio)))
    if(not np.isnan(rmsNEW)):
        rms = round(rmsNEW)
    else:
        rms = 100
    # print(rms)
    
    # return None and continue streaming
    return (None, pyaudio.paContinue)

# Open the stream with the callback function
stream = pa.open(format=pyaudio.paInt16,
                 channels=1,
                 rate=sample_rate,
                 input=True,
                 frames_per_buffer=chunk_size,
                 stream_callback=audio_callback)


# create a separate thread for audio input
audio_thread = threading.Thread(target=audio_callback)
audio_thread.daemon = True
audio_thread.start()

# keyboard reading thread
def keyboard_thread():
    while True:
        event = keyboard.read_event()
        if event.event_type == "down":
            print(f"Key pressed: {event.name}")
        elif event.event_type == "up":
            print(f"Key released: {event.name}")

keyboard_thread = threading.Thread(target=keyboard_thread)
keyboard_thread.daemon = True
keyboard_thread.start()

# TUBER STUFF

def open_png_files():
    # create a Tkinter root window to use for the file dialog
    root = tk.Tk()
    root.withdraw()

    # open the file dialog and allow the user to select one or more PNG files
    file_paths = filedialog.askopenfilenames(
        filetypes=[("PNG files", "*.png")],
        title="Select PNG files",
        multiple=True
    )

    # return the list of selected file paths
    return file_paths

class Animation:
    def __init__(self, name, frames, fps, requires, enables, hotkey):
        self.name = name
        self.frames = frames
        self.fps = fps
        self.requires = requires
        self.enables = enables
        self.hotkey = hotkey
    
    def getName(self):
        return self.name
    def setName(self, name):
        self.name = name
    
    def getFrames(self):
        return self.frames
    def setFrames(self):
        newFrames = open_png_files()
        self.frames = newFrames
    
    def getFPS(self):
        return self.fps
    def setFPS(self, fps):
        self.fps = fps

    def getRequires(self):
        return self.requires
    def setRequires(self, requires):
        self.requires = requires

    def getEnables(self):
        return self.enables
    def setEnables(self, enables):
        self.enables = enables
    
    def getHotkey(self):
        return self.hotkey
    def setHotkey(self, hotkey):
        self.hotkey = hotkey

        

        



class AnimationSet:


class Tuber:
    def __init__(self, animations):
        self.animations = animations
    
        




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
    {"text": "Open ToonTuber", "position": (0, 75)},
    {"text": "Player Settings", "position": (0, 125)},
    {"text": "Open Editor", "position": (0, 175)}
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

stream.stop_stream()
stream.close()
pa.terminate()