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
import json
import os

pygame.init()

# Set up the Pygame window
width, height = 750, 750
screen = pygame.display.set_mode((width, height))
rms = 0

# Set the window name
pygame.display.set_caption("Toon Tuber Player")

# Opening screen
UniFont = pygame.font.Font('freesansbold.ttf', 64)
text = UniFont.render("Toon Tuber Player", True, (255, 255, 255))
textRect = text.get_rect()
textRect.center = (width // 2, height // 2)

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

lastKeyPressed = ""
latestKeyPressed = ""
keyHeld = False

def pushHotKey(key):
    global latestKeyPressed, lastKeyPressed
    lastKeyPressed = latestKeyPressed
    latestKeyPressed = key
    keyHeld = True

def releaseHotKey(key):
    global latestKeyPressed, lastKeyPressed
    lastKeyPressed = latestKeyPressed
    latestKeyPressed = ""
    keyHeld = False

# keyboard reading thread
def keyboard_thread():
    while True:
        event = keyboard.read_event()
        if event.event_type == "down":
            print(f"Key pressed: {event.name}")
            pushHotKey(event.name)
        elif event.event_type == "up":
            print(f"Key released: {event.name}")
            releaseHotKey(event.name)

keyboard_thread = threading.Thread(target=keyboard_thread)
keyboard_thread.daemon = True
keyboard_thread.start()

# TUBER STUFF

MISSING_IMAGE = pygame.image.load("MissingImage.png")

def load_pngs(paths):
    # create a list of Pygame images from the selected files
    images = []
    for file_path in paths:
        if(os.path.isfile(file_path)):
            image = pygame.image.load(file_path)
            images.append(image)
        else:
            images.append(MISSING_IMAGE)
        
    return images

class HotKey:
    def __init__(self, key, requires):
        self.key = key              # string
        self.requires = requires    # list of ExpressionSets

    def getKey(self):
        return self.key
    def setKey(self, key):
        self.key = key

    def getRequires(self):
        return self.requires
    def addRequires(self, newRequires):
        self.requires.append(newRequires)
    def removeRequires(self, oldRequires):
        if(oldRequires not in self.requires):
            print("Required state not found.")
        else:
            self.requires.remove(oldRequires)

class Animation:
    def __init__(self, frames, fps):
        if(frames is None):
            self.frames = None
            self.fps = None
        else:
            self.frames = load_pngs(frames) # list of PNG images
            self.fps = fps                  # int

    def getFrames(self):
        return self.frames
    def countFrames(self):
        return len(self.frames)

    def getFPS(self):
        return self.fps
    def setFPS(self, fps):
        self.fps = fps

class IdleSet:
    def __init__(self, animations, minSec, maxSec):
        if(animations is None):
            # null object
            self.animations = None
            self.count = None
            self.minSec = None
            self.maxSec = None
        else:
            self.animations = animations    # list of Animation objects
            self.count = len(animations)              # int
            self.minSec = minSec          # int
            self.maxSec = maxSec          # int
    
    def getAnimations(self):
        return self.animations
    def addAnimation(self, newAnimation):
        self.animations.append(newAnimation)
    def removeAnimation(self, oldAnimation):
        if(oldAnimation not in self.animations):
            print("Animation not found.")
        else:
            self.animations.remove(oldAnimation)  

    def getCount(self):
        return self.count

    def getMinSec(self):
        return self.minSec
    def setMinSec(self, minSec):
        self.minSec = minSec

    def getMaxSec(self):
        return self.maxSec
    def setMaxSec(self, maxSec):
        self.maxSec = maxSec

class ExpressionSet:
    def __init__(self, name, main, idleSet, talk, peak, trIn, trOut, requires, enables, hotkey):
        self.name = name                # string
        self.main = main                # Animation object
        self.idleSet = idleSet          # IdleSet object
        self.talk = talk                # Animation object
        self.peak = peak                # Animation object
        self.trIn = trIn          # Animation object
        self.trOut = trOut        # Animation object
        self.requires = requires        # list of ExpressionSets
        self.enables = enables          # list of ExpressionSets
        self.hotkey = hotkey            # Hotkey object

    def getName(self):
        return self.name
    def setName(self, name):
        self.name = name

    def getMain(self):
        return self.main
    def setMain(self, main):
        self.main = main

    def getIdleSet(self):
        return self.idleSet
    def setIdleSet(self, idleSet):
        self.idleSet = idleSet

    def getTalk(self):
        return self.talk
    def setTalk(self, talk):
        self.talk = talk

    def getPeak(self):
        return self.peak
    def setPeak(self, peak):
        self.peak = peak

    def getTransitionIn(self):
        return self.trIn
    def setTransitionIn(self, trIn):
        self.trIn = trIn

    def getTransitionOut(self):
        return self.trOut
    def setTransitionOut(self, trOut):
        self.trOut = trOut

    def getRequires(self):
        return self.requires
    def addRequires(self, newRequires):
        self.requires.append(newRequires)
    def removeRequires(self, oldRequires):
        if(oldRequires not in self.requires):
            print("Required state not found.")
        else:
            self.requires.remove(oldRequires)

    def getEnables(self):
        return self.enables
    def addEnables(self, newEnables):
        self.enables.append(newEnables)
    def removeEnables(self, oldEnables):
        if(oldEnables not in self.enables):
            print("Enabled state not found.")
        else:
            self.enables.remove(oldEnables)

    def getHotkey(self):
        return self.hotkey
    def addHotkey(self, newHotkey, required):
        self.hotkey = newHotkey
        self.requires.append(required)
    def removeHotkey(self, oldHotkey):
        if(oldHotkey not in self.hotkey):
            print("Hotkey not found.")
        else:
            self.hotkey = None

class CannedAnimation:
    def __init__(self, name, animation, hotkey, requires, result):
        self.name = name                # string
        self.animation = animation      # Animation object
        self.hotkey = hotkey            # Hotkey object
        self.requires = requires        # list of ExpressionSets
        self.result = result            # ExpressionSet object
    
    def getName(self):
        return self.name
    def setName(self, name):
        self.name = name
    
    def getAnimation(self):
        return self.animation
    def setAnimation(self, animation):
        self.animation = animation

    def getHotkey(self):
        return self.hotkey
    def addHotkey(self, newHotkey, requiredState):
        self.hotkey.append(HotKey(newHotkey, requiredState))
        if(requiredState is not None):
            self.addRequires(requiredState)

    def removeHotkey(self, oldHotkey):
        if(oldHotkey not in self.hotkey):
            print("Hotkey not found.")
        else:
            self.hotkey.remove(oldHotkey)
            
    def getRequires(self):
        return self.requires
    def addRequires(self, newRequires):
        self.requires.append(newRequires)
    def removeRequires(self, oldRequires):
        if(oldRequires not in self.requires):
            print("Required state not found.")
        else:
            self.requires.remove(oldRequires)

# tuber info
tuberName = "NONE"
creator = "NONE"
created = "NONE"
modified = "NONE"
randomDuplicateReduction = 0.5
folderPath = "NONE"
expressionList = []
cannedAnimationList = []
tuberFrames = []

currentAnimation = None
currentFrame = 0
framerate = 0
fpsClock = pygame.time.Clock()
fpsTimeBtwnFrames = 0
randIntervalClock = pygame.time.Clock()
currentAnimMinID = 0
currentAnimMaxID = 0
lockedInAnimation = False


# GUI stuff

class ClickableText:
    def __init__(self, text, position, font, color, action=None):
        self.text = text
        self.position = position
        self.font = font
        self.color = color
        self.action = action
    
    def setText(self, text):
        self.text = text
    def getPosition(self):
        return self.position
    def setPosition(self, position):
        self.position = position

    def draw(self, screen):
        text = self.font.render(self.text, True, self.color)
        screen.blit(text, self.position)

    def isClicked(self, mousePos):
        text = self.font.render(self.text, True, self.color)
        textRect = text.get_rect()
        textRect.topleft = self.position
        if(textRect.collidepoint(mousePos)):
            return True
        else:
            return False
        
    def doAction(self):
        if(self.action is not None):
            self.action()

# Button Actions
def openToonTuber():
    print("Open ToonTuber")

def openPlayerSettings():
    print("Open Player Settings")

def openEditor():
    print("Open Editor")

def createNewTuber():
    global openingScreen
    openingScreen = False
    print("New Tuber")

def loadTuber():
    global openingScreen, tuberName, creator, created, modified, randomDuplicateReduction, expressionList, cannedAnimationList, tuberFrames
    openingScreen = False
    # file dialog to select json file   
    root = tk.Tk()
    root.withdraw()

    file_path = filedialog.askopenfilename(
        filetypes=[("JSON files", "*.json")],
        title="Select a JSON file",
    )

    print("Selected file:", file_path)

    # load json file
    with open(file_path) as json_file:
        data = json.load(json_file)
        # print(data)
    name = data["name"]
    creator = data["creator"]
    created = data["created"]
    modified = data["last_modified"]
    randomDuplicateReduction = data["random_duplicate_reduction"]
    for expressionData in data["loop_anims"]:
        print("Loading expression: " + expressionData["name"])
        # expression set requires a main animation, an idle set, and loop animations

        # main animation        REQUIRED
        main = Animation(expressionData["anims"]["Main"]["frames"], expressionData["anims"]["Main"]["fps"])

        # idle set
        idleList = [Animation(None, None)]
        if(not expressionData["anims"]["Idles"]):
            print("No idles found.")
            idles = IdleSet(None, None, None)
        else:
            for idle in expressionData["anims"]["Idles"]["idleAnims"]:
                idleList.append(Animation(idle["frames"], idle["fps"]))
            idles = IdleSet(idleList, expressionData["anims"]["Idles"]["randomSecMin"], expressionData["anims"]["Idles"]["randomSecMax"])


        # talking
        if(not expressionData["anims"]["Talk"]):
            print("No talking animation found.")
            talking = Animation(None, None)
        else:
            talking = Animation(expressionData["anims"]["Talk"]["frames"], expressionData["anims"]["Talk"]["fps"])

        # peak
        if(not expressionData["anims"]["Peak"]):
            print("No peak animation found.")
            peak = Animation(None, None)
        else:
            peak = Animation(expressionData["anims"]["Peak"]["frames"], expressionData["anims"]["Peak"]["fps"])

        # transition in
        transitionIn = Animation(expressionData["anims"]["TransitionIN"]["frames"], expressionData["anims"]["TransitionIN"]["fps"])

        # transition out
        transitionOut = Animation(expressionData["anims"]["TransitionOUT"]["frames"], expressionData["anims"]["TransitionOUT"]["fps"])

        # create ExpressionSet
        expressionList.append(ExpressionSet(expressionData["name"], main, idles, talking, peak, transitionIn, transitionOut, expressionData["requires"], expressionData["enables"], expressionData["hotkey"]))

    for cannedAnimationData in data["canned_anims"]:
        # name, animation, hotkey, requires, result
        cannedAnimationList.append(CannedAnimation(cannedAnimationData["name"], Animation(cannedAnimationData["anim"]["frames"], cannedAnimationData["anim"]["fps"]), cannedAnimationData["hotkey"], cannedAnimationData["requires"], cannedAnimationData["result"]))

# Define some colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)

# Define the font for the text options
UniFont = pygame.font.Font(None, 50)

# text_settings = UniFont.render("SETTINGS", True, BLACK)

# Define the clickable text options
settings_options = [
    ClickableText("Open ToonTuber", (0, 0), UniFont, WHITE, openToonTuber),
    ClickableText("Player Settings", (0, 50), UniFont, WHITE, openPlayerSettings),
    ClickableText("Open Editor", (0, 100), UniFont, WHITE, openEditor)
]

opening_options = [
    ClickableText("New Tuber", (width/3, 75), UniFont, WHITE, createNewTuber),
    ClickableText("Load Tuber", (width/3, 125), UniFont, WHITE, loadTuber)
]

# Define a variable to keep track of whether the settings screen is active
settings_active = False

# Define a function to draw the text options on the screen
def draw_text_options(text):
    for option in text:
        option.draw(screen)

# Define a function to darken the screen
def darken_screen():
    darken_surface = pygame.Surface((width, height))
    darken_surface.fill(BLACK)
    darken_surface.set_alpha(128)
    screen.blit(darken_surface, (0, 0))

# Define a function to display the FPS counter
def display_fps(clock):
    fps = str(int(clock.get_fps()))
    fps_text = UniFont.render(fps, True, WHITE)
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
openingScreen = True
while running:
    # Measure the time between frames and limit the FPS to 60
    delta_time = clock.tick(60) / 1000.0

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_p and not openingScreen:
            settings_active = not settings_active
        # if the user clicks on a text option, do the action
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mousePos = pygame.mouse.get_pos()
            if openingScreen:
                for option in opening_options:
                    if option.isClicked(mousePos):
                        option.doAction()
            if settings_active:
                for option in settings_options:
                    if option.isClicked(mousePos):
                        option.doAction()

    # Draw the green background
    screen.fill(GREEN)

    # if on the opening screen, prompt user if they want to open an existing tuber or make a new one
    if openingScreen:
        # print("opening screen")
        darken_screen()
        draw_text_options(opening_options)
        # if user clicks on "Open ToonTuber", open the file explorer and allow them to select a tuber
        # if user clicks on "New ToonTuber", open the editor

    # draw Tuber to screen
    
    # if(keyHeld is True and latestKeyPressed is not None):


    # If the settings screen is active, darken the screen and draw the text options
    if settings_active:
        darken_screen()
        draw_text_options(settings_options)
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