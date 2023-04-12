# you'll need to use pip to get these libraries up here
import pygame
import pygame_gui
import pyaudio
import numpy as np
import keyboard
from StreamDeck.DeviceManager import DeviceManager
import imageio

# these should be built-in
import threading
import tkinter as tk
from tkinter import filedialog
import json
import os
import random
import sys
import winsound
import configparser
import datetime
import traceback

debugMode = False

version = "v1.0.0"

peakThreshold = 90
talkThreshold = 50

GREEN = (0, 255, 0)
BGCOLOR = GREEN

print(f"ToonTuber Player {version}")

# play sound when crash happens so user is alerted
def handle_exception(exc_type, exc_value, exc_traceback):
    global stream
    # Quit Pygame
    pygame.quit()

    stream.stop_stream()
    stream.close()
    pa.terminate()
    

    # Print the exception information
    print("Unhandled exception:", exc_type, exc_value)

    # Play a sound when an exception occurs
    if(not debugMode and exc_type != KeyboardInterrupt):
        winsound.PlaySound("assets\error.wav", winsound.SND_FILENAME)

    # Call the default exception handler
    sys.__excepthook__(exc_type, exc_value, exc_traceback)

    # save the exception and traceback to a file called "Player Crash Report {date and time}.txt"
    # and have the file contain the error and traceback
    errorFileID = 0
    while(os.path.isfile(f"Player Crash Report {datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S')}{f' ({errorFileID})' if errorFileID != 0 else ''}.txt")):
        errorFileID += 1

    if(exc_type != KeyboardInterrupt):
        with open(f"Player Crash Report {datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S')}{f' ({errorFileID})' if errorFileID != 0 else ''}.txt", "w") as f:
            f.write("Oops! The player crashed! Sorry about that.\nThe text below is the error report. If you don't know what this means, please send this file to the developer, along with a description of what happened (which you can type here).\n\nWhat I was doing: \n\n")
            f.write(f"Unhandled exception: {exc_type} {exc_value}")
            for line in traceback.format_tb(exc_traceback):
                f.write(line)
            f.close()
    

# Set the exception handler
sys.excepthook = handle_exception

# helper function, comment out the "print" line to disable this function
def debugPrint(str):
    if(debugMode):
        print(str)
    return

## GLOBAL VARIABLES

lastKeyPressed = ""
latestKeyPressed = ""
keyHeld = False

tuberName = "NONE"
creator = "NONE"
created = "NONE"
modified = "NONE"
randomDuplicateReduction = 0
expressionList = []
cannedAnimationList = []
tuberFrames = []            # array of frames for the current animation being played
expressionIndex = {}        # key: expression name, value: index of this animation within the expressionList array
cannedAnimationIndex = {}   # key: canned animation name, value: index of this animation within the cannedAnimationList array

hotkeyDictionary = {}   # key: key pressed, value: an array of strings for each animation name that this hotkey can trigger

currentAnimation = None
currentExpression = ""
currentFrame = 0
queuedExpression = ""
currentAnimationType = ""    # "expression" or "canned"
queuedAnimationType = ""    # "expression" or "canned

transition = ""     # blank for no transition, "out" for transition out, "in" for transition in
idling = False
framerate = 0
image_timer = 0
fpsClock = pygame.time.Clock()
idleClockCounter = pygame.time.Clock()
idleTimer = 0
randIdleMin = 0
randIdleMax = 0
timeUntilNextIdle = 10
currentTotalFrames = 0
locked = False

latestUnicode = None
selectedBox = ""

audioDeviceText = "1"
audio_device_id = 1

# Define some colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)

debugPrint("Global variables initialized.\nInitializing Pygame...")

pygame.init()

debugPrint("Pygame initialized. Setting up window...")
# Set up the Pygame window
width, height = 750, 750
screen = pygame.display.set_mode((width, height))

settings_UImanager = pygame_gui.UIManager((width, height))
audio_UImanager = pygame_gui.UIManager((width, height))

# Set the window name (NOTE: changing the caption might screw up existing Window Captures in OBS. Best not to change this.)
pygame.display.set_caption("ToonTuber Player")

# Opening screen
UniFont = pygame.font.Font('freesansbold.ttf', 24)
UniFontSmaller = pygame.font.Font('freesansbold.ttf', 18)
UniFontBigger = pygame.font.Font('freesansbold.ttf', 36)
text = UniFont.render("Toon Tuber Player", True, (255, 255, 255))
textRect = text.get_rect()
textRect.center = (width // 2, height // 2)

debugPrint("PyGame set up.\nReading from preferences.ini....")

# read from preferences.ini file
try:
    if(not os.path.isfile("preferences.ini")):
        raise Exception("preferences.ini does not exist")
    prefini = configparser.ConfigParser()
    prefini.read("preferences.ini")
except Exception as e:
    print(f"Error reading preferences.ini: {e}")
    print("Creating new preferences.ini file...")
    # create new blank file
    with open("preferences.ini", 'w') as f:
        pass

    prefini = configparser.ConfigParser()
    prefini["LastUsed"] = {"lastLoaded": "NONE", "lastMic": "NONE"}
    prefini["Thresholds"] = {"talkThresh": "50", "peakThresh": "90"}
    prefini["Settings"] = {"keybind": "p", "bgcolor": (0, 255, 0, 255)}
    with open("preferences.ini", "w") as f:
        prefini.write(f)
    print("preferences.ini created with default values.")

# read from each element in preferences.ini and have failsafes for each
try:
    lastTuberLoaded = prefini["LastUsed"]["lastLoaded"].strip("\"")
except Exception as e:
    print("Error reading last loaded tuber from preferences.ini. Setting to NONE...")
    lastTuberLoaded = "NONE"

try:
    lastAudioDevice = prefini["LastUsed"]["lastMic"].strip("\"")
except Exception as e:
    print("Error reading last used mic from preferences.ini. Setting to NONE...")
    lastAudioDevice = "NONE"

try:
    talkThreshold = int(prefini["Thresholds"]["talkThresh"])
except Exception as e:
    print("Error reading talk threshold from preferences.ini. Setting to 50...")
    talkThreshold = 50

try:
    peakThreshold = int(prefini["Thresholds"]["peakThresh"])
except Exception as e:
    print("Error reading peak threshold from preferences.ini. Setting to 90...")
    peakThreshold = 90

try:
    settingsKeybindName = prefini["Settings"]["keybind"].strip("\"")
except Exception as e:
    print("Error reading keybind from preferences.ini. Setting to \"p\"...")
    settingsKeybindName = pygame.key.key_code("p")
    
settingsKeybind = pygame.key.key_code(settingsKeybindName)
try:
    BGCOLOR = eval(prefini["Settings"]["bgcolor"].strip("\""))
except Exception as e:
    print("Error reading background color from preferences.ini. Setting to green...")
    BGCOLOR = GREEN


talkThreshText = f"{talkThreshold}"
peakThreshText = f"{peakThreshold}"

debugPrint("preferences.ini read.\Initializing audio data stuff...")

# audio stuff
rms = 0
avgVol = 0
chunk_size = 256  # number of audio samples per chunk
sample_rate = 44100  # number of samples per second

volRollingAverage = []
volRollingAverageLength = 10

pa = pyaudio.PyAudio()

audioDeviceList = {}

audioDevice_options = []

audioDeviceNames = []

deviceList = None
numdevices = 0

def getAudioDevices(initial=False):
    global deviceList, numdevices, audioDeviceList, audioDeviceNames, audio_device_id, audioDeviceText
    deviceList = pa.get_host_api_info_by_index(0)
    numdevices = deviceList.get('deviceCount')
    audioDeviceList.clear()
    audioDeviceNames.clear()
    for i in range(0, numdevices):
        if (pa.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
            deviceName = pa.get_device_info_by_host_api_device_index(0, i).get('name')             
            if(deviceName == lastAudioDevice and initial):
                audio_device_id = i
                audioDeviceText = str(i)
            audioDeviceList[deviceName] = i
            audioDeviceNames.append(deviceName)

getAudioDevices(True)

def audio_callback(in_data, frame_count, time_info, status):
    global rms, avgVol
    # convert audio data to a numpy array
    audio = np.frombuffer(in_data, dtype=np.int16)

    # calculate the root mean square (RMS) amplitude
    rmsNEW = np.sqrt(np.mean(np.square(np.nan_to_num(audio))) + 1e-6)
    if(not np.isnan(rmsNEW)):
        rms = round(rmsNEW)
    else:
        rms = 100
    
    volRollingAverage.append(rms)
    if(len(volRollingAverage) > volRollingAverageLength):
        volRollingAverage.pop(0)
    avgVol = sum(volRollingAverage) / len(volRollingAverage)
    # print(avgVol)
    
    # return None and continue streaming
    return (None, pyaudio.paContinue)

# Open the stream with the callback function
stream = pa.open(format=pyaudio.paInt16,
                 channels=1,
                 rate=sample_rate,
                 input=True,
                 frames_per_buffer=chunk_size,
                 input_device_index=audio_device_id,
                 stream_callback=audio_callback)

# Start the audio stream
stream.start_stream()

# Prompts user to select a new input device
def select_audio_device(id):
    global stream
    # info = pa.get_host_api_info_by_index(0)
    # numdevices = info.get('deviceCount')
    # print("Available input devices:")
    # for i in range(0, numdevices):
    #     if (pa.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
    #         print("ID:", i, "- Name:", pa.get_device_info_by_host_api_device_index(0, i).get('name'))
    print("Stopping audio stream...")
    stream.stop_stream()
    print("Closing audio stream...")
    stream.close()
    print("Reopening audio stream...")
    stream = pa.open(format=pyaudio.paInt16,
                 channels=1,
                 rate=sample_rate,
                 input=True,
                 frames_per_buffer=chunk_size,
                 input_device_index=id,
                 stream_callback=audio_callback)
    print("Starting audio stream...")
    stream.start_stream()
    print("Audio stream restarted.")

debugPrint("Audio data stuff initialized.\nInitializing input reader thread...")

def pushHotKey(key):
    global latestKeyPressed, lastKeyPressed, keyHeld, currentAnimation, expressionList, cannedAnimationList, queuedAnimation, currentExpression, queuedExpression, transition, queuedAnimationType, currentAnimationType, changingKeybind
    if(changingKeybind):
        return 
   
    # print(hotkeyDictionary)
    if(key in hotkeyDictionary):
        # print(f"Hotkey pressed: {key}")
        # a hotkey was pressed. check if it needs an existing animation
        for animName in hotkeyDictionary[key]:
            if(animName == queuedExpression):
                # skip itself if its already queued
                continue
            # print(f"Checking animation: {animName}")
            # print(f"name is {'' if animName in expressionIndex else 'NOT '}in the expression set" )
            # print(f"current anim is {'' if currentExpression in expressionList[expressionIndex[animName]].requires else 'NOT '}in the required set {'(EMPTY)' if expressionList[expressionIndex[animName]].requires == [None] else ''}" )
            # print(f"requested anim is {'NOT ' if animName != currentExpression else ''}already playing.")

            # for the animation to be queued, it must mee the following:
            # 1. it must be a valid expression
            # 2. the required animation must be playing (or the required animation list is empty)
            # 3. the requested animation must not be playing
            # print(cannedAnimationList[cannedAnimationIndex[animName]].requires, "     current: ", currentExpression.name)
            isBlocked = False
            # print(f"Checking blockers for {animName}...")
            if(animName in expressionIndex):
                if currentExpression in expressionList[expressionIndex[animName]].getBlockers():
                    isBlocked = True
            elif(animName in cannedAnimationIndex):
                if currentExpression in cannedAnimationList[cannedAnimationIndex[animName]].getBlockers():
                    isBlocked = True
            # print(f"Blocked: {isBlocked}")

            if(animName in expressionIndex 
                and ((currentExpression in expressionList[expressionIndex[animName]].requires 
                     or expressionList[expressionIndex[animName]].requires == [None]) or (queuedExpression != "" and queuedExpression in expressionList[expressionIndex[animName]].requires))
                and animName != currentExpression and currentAnimationType != "canned"
                and not isBlocked):
                # it's an expression and the needed anim is ready. check if the required animation is already playing
                queuedExpression = animName
                queuedAnimationType = "expression"
                break

            elif(animName in cannedAnimationIndex 
                 and (currentExpression in cannedAnimationList[cannedAnimationIndex[animName]].requires 
                      or cannedAnimationList[cannedAnimationIndex[animName]].requires == [None]) 
                 and animName != currentExpression
                 and not isBlocked):
                # it's a canned animation. check if the required animation is already playing
                queuedExpression = animName
                queuedAnimationType = "canned"
                break

    lastKeyPressed = latestKeyPressed
    latestKeyPressed = key
    keyHeld = True

def releaseHotKey(key):
    global keyHeld
    keyHeld = False

# stream deck input reading (UNTESTED, I DON'T HAVE A STREAM DECK TO PROVE THAT THIS WORKS)
def streamdeck_key_press_callback(deck, key, state):
    if state:
        debugPrint(f"Stream Deck Key {key} was pressed")
        pushHotKey(f"SD_{deck.id()}_{key}")
        # format for StreamDeck hotkeys: SD_<deck id>_<key number>

debugPrint("Checking for connected StreamDecks...")

streamdecks = None
try:
    streamdecks = DeviceManager().enumerate()   # ERROR HERE
    for deck in streamdecks:
        deck.open()
        deck.reset()
        deck.set_key_callback(streamdeck_key_press_callback)
    debugPrint(f"({len(streamdecks)}) StreamDeck found.")
except Exception as e:
    debugPrint("NO StreamDecks were found.")

# keyboard reading thread
def keyboard_input_thread():
    while True:
        event = keyboard.read_event()
        if event.event_type == "down":
            # print(f"Key pressed: {event.name}")
            pushHotKey(event.name)
        elif event.event_type == "up":
            # print(f"Key released: {event.name}")
            releaseHotKey(event.name)

keyboard_input_thread = threading.Thread(target=keyboard_input_thread)
keyboard_input_thread.daemon = True
keyboard_input_thread.start()

debugPrint("Input reader thread started.\nCreating animation classes...")

resetIdleTimer = threading.Event()

def idle_timer_thread():
    global idleClockCounter, timeUntilNextIdle, idleTimer
    while True:
        resetIdleTimer.wait()
        # Reset the idle timer
        idleTimer = 0
        # Clear the event
        resetIdleTimer.clear()
        while True:
            # Update the idle timer
            idleTimer += idleClockCounter.tick(60)
            # Check if the event is set
            if resetIdleTimer.is_set():
                # If the event is set, exit the inner loop and reset the timer
                break

def idle_timer_reset():
    global idleTimer
    resetIdleTimer.set()

def get_idle_timer():
    global idleTimer
    return idleTimer / 1000

idleTimer_thread = threading.Thread(target=idle_timer_thread)
idleTimer_thread.daemon = True

# TUBER STUFF

MISSING_IMAGE = pygame.image.load("assets\MissingImage.png")

def load_animation_images(paths, fps):
    # create a list of Pygame images from the selected files
    images = []
    for file_path in paths:
        if(os.path.isfile(file_path)):
            extension = os.path.splitext(file_path)[1]
            if(extension == ".png"):
                image = pygame.image.load(file_path)
                images.append(image)
            elif(extension == ".gif"):
                gif = imageio.mimread(file_path)
                for frame in gif:
                    # convert the image to a Pygame surface
                    # count the number of bytes in frame.tobytes() and print it out
                    try:
                        pygameFrame = pygame.image.frombuffer(frame.tobytes(), frame.shape[1::-1], "RGBA")
                    except Exception as e:
                        print(e)
                        exit()
                    images.append(pygameFrame)
                if('fps' in gif[0].meta):
                    fps = gif[0].meta['fps']
                elif('duration' in gif[0].meta):
                    fps = 1000 / gif[0].meta['duration']
                return (images, fps)
        else:
            images.append(MISSING_IMAGE)
    return (images, fps)

class Animation:
    def __init__(self, frames, fps, locking):
        if(frames is None):
            self.frames = None
            self.fps = None
            self.locking = None
        else:
            (self.frames, self.fps) = load_animation_images(frames, fps)
            self.locking = locking          # bool

    def __str__(self):
        return f"Animation with {len(self.frames) if self.frames != None else None} frames at {self.fps} fps. Locking: {self.locking}"

    def exists(self):
        return self.frames != None

    def getFrames(self):
        return self.frames
    def countFrames(self):
        return len(self.frames)

    def getFPS(self):
        return self.fps
    def setFPS(self, fps):
        self.fps = fps

    def isLocking(self):
        return self.locking
    def setLocking(self, locking):
        self.locking = locking

idleChoiceIndex = -1

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

    def __str__(self):
        return f"IdleSet with {self.count} animations. Min: {self.minSec} Max: {self.maxSec}"
    
    def exists(self):
        return self.animations != None

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


    def getRandomIdle(self):
        global idleChoiceIndex, randomDuplicateReduction
        if(idleChoiceIndex == -1):
            randAnim = random.choice(self.animations)
        elif(len(self.animations) == 1):
                return self.animations[0]
        else:
            weighted = []
            for i, animation in enumerate(self.animations):
                if i == idleChoiceIndex:
                    weight = 1 - randomDuplicateReduction
                else:
                    weight = 1
                weighted.append(weight)
            randAnim = random.choices(self.animations, weights=weighted, k=1)[0]

        idleChoiceIndex = self.animations.index(randAnim)
        return randAnim

class ExpressionSet:
    def __init__(self, name, main, idleSet, talk, peak, trIn, trOut, requires, blockers, hotkey):
        self.name = name                # string
        self.main = main                # Animation object
        self.idleSet = idleSet          # IdleSet object
        self.talk = talk                # Animation object
        self.peak = peak                # Animation object
        self.trIn = trIn          # Animation object
        self.trOut = trOut        # Animation object
        self.requires = requires        # list of ExpressionSets
        self.blockers = blockers        # list of ExpressionSets
        self.hotkey = hotkey            # Hotkey object

    def __str__(self):
        return f"ExpressionSet {self.name}:\nMain: {self.main}\n{self.idleSet}\nTalk: {self.talk}\nPeak: {self.peak}\nTransition In: {self.trIn}\nTransition Out: {self.trOut}\nRequires: {self.requires}\nHotkey: {self.hotkey}"

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
    
    def getBlockers(self):
        return self.blockers
    def addBlockers(self, newBlockers):
        self.blockers.append(newBlockers)

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
    def __init__(self, name, animation, hotkey, requires, blockers, result):
        self.name = name                # string
        self.animation = animation      # Animation object
        self.hotkey = hotkey            # Hotkey object
        self.requires = requires        # list of ExpressionSets
        self.blockers = blockers        # list of ExpressionSets
        self.result = result            # ExpressionSet object

    def __str__(self):
        return f"CannedAnimation {self.name}:\nAnimation: {self.animation}\nHotkey: {self.hotkey}\nRequires: {self.requires}\nResult: {self.result}"
    
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
    def addHotkey(self, newHotkey, required):
        self.hotkey = newHotkey
        self.requires.append(required)
    def removeHotkey(self, oldHotkey):
        if(oldHotkey not in self.hotkey):
            print("Hotkey not found.")
        else:
            self.hotkey = None
            
    def getRequires(self):
        return self.requires
    def addRequires(self, newRequires):
        self.requires.append(newRequires)
    def removeRequires(self, oldRequires):
        if(oldRequires not in self.requires):
            print("Required state not found.")
        else:
            self.requires.remove(oldRequires)

    def getResult(self):
        return self.result
    def setResult(self, result):
        self.result = result
    
    def getBlockers(self):
        return self.blockers
    def addBlockers(self, newBlockers):
        self.blockers.append(newBlockers)

def update_render_thread():
    global currentFrame, framerate, image_timer, locked, transition, queuedExpression, currentExpression, talkThreshold, peakThreshold, avgVol, idleClockCounter, idleTimer, currentAnimationType, queuedAnimationType, idling, timeUntilNextIdle, currentScreen
    while True:
        if(currentScreen == "opening" or currentScreen == "audio"):
            continue
        timeElapsed = fpsClock.tick(framerate) / 1000.0  # Get the time passed since last frame
        # print(get_idle_timer())
        image_timer += timeElapsed
        # print(timeElapsed, "  ", image_timer)
        if image_timer > 1 / framerate: # time equivelent to one frame has passed
            currentFrame = currentFrame + 1
            # print("queued:", queuedExpression, "   current:", currentExpression)
            # time to change frame! 
            # print(expressionList[expressionIndex[currentExpression]].getTalk())
            animationFinished = currentFrame >= len(tuberFrames)
            idlesExist = timeUntilNextIdle != -1
            if(currentAnimationType == "expression" and not idling and get_idle_timer() >= timeUntilNextIdle and idlesExist):
                # print("idling")
                loadExpression(expressionList[expressionIndex[currentExpression]], "idle")
                idling = True
            elif(currentAnimationType == "expression" and idling and animationFinished and idlesExist):
                # print("ending idle")
                loadExpression(expressionList[expressionIndex[currentExpression]], "main")
                idling = False
                idle_timer_reset()
                # print(get_idle_timer())
            elif(not locked or animationFinished):
                # can change animation. check what kind of animation we need to switch to, if we need to

                # queued expression and transitions
                if((queuedExpression != currentExpression and queuedExpression != "") and transition == "" and currentAnimationType != "canned"):
                    # animation queued, no transition happening, not in canned animation
                    transition = "out"
                    loadExpression(expressionList[expressionIndex[currentExpression]], "out")
                elif(transition == "out" and animationFinished):
                    # transition out finished, load queued animation
                    currentExpression = queuedExpression
                    currentAnimationType = queuedAnimationType
                    queuedExpression = ""
                    queuedAnimationType = ""
                    if(currentAnimationType == "expression"):
                        # if the queued animation is an expression
                        transition = "in"
                        currentAnimationType = "expression"
                        loadExpression(expressionList[expressionIndex[currentExpression]], "in")                        
                    elif(currentAnimationType == "canned"):
                        # if the queued animation is a canned animation
                        transition = ""
                        currentAnimationType = "canned"
                        loadCanned(cannedAnimationList[cannedAnimationIndex[currentExpression]])
                elif(transition == "in" and animationFinished):
                    # transition in finished, load main animation
                    transition = ""
                    loadExpression(expressionList[expressionIndex[currentExpression]], "main")
                elif(currentAnimationType == "canned" and animationFinished):
                    # if we're in a canned animation, and it's finished
                    resultingExpression = cannedAnimationList[cannedAnimationIndex[currentExpression]].getResult()
                    if(resultingExpression in expressionIndex):
                        loadExpression(expressionList[expressionIndex[resultingExpression]], "main")
                    elif(resultingExpression in cannedAnimationIndex):
                        loadCanned(cannedAnimationList[cannedAnimationIndex[resultingExpression]])
                # peak and talk
                elif(avgVol >= peakThreshold 
                     and expressionList[expressionIndex[currentExpression]].getPeak().exists() 
                     and currentAnimation is not expressionList[expressionIndex[currentExpression]].getPeak()):
                    # peak animation is set, and we're not locked
                    # print("peak")
                    loadExpression(expressionList[expressionIndex[currentExpression]], "peak")
                elif(avgVol >= talkThreshold 
                     and expressionList[expressionIndex[currentExpression]].getTalk().exists() 
                     and currentAnimation is not expressionList[expressionIndex[currentExpression]].getTalk() 
                     and currentAnimation is not expressionList[expressionIndex[currentExpression]].getPeak()):
                    # talk animation is set, and we're not locked
                    # print("talk")
                    loadExpression(expressionList[expressionIndex[currentExpression]], "talk")
                elif( avgVol < talkThreshold 
                     and (currentAnimation is expressionList[expressionIndex[currentExpression]].getTalk() 
                          or currentAnimation is expressionList[expressionIndex[currentExpression]].getPeak())):
                    loadExpression(expressionList[expressionIndex[currentExpression]], "main")
                else:
                    # no transition, just update the animation
                    currentFrame = (currentFrame) % len(tuberFrames)   
            else:                
                currentFrame = (currentFrame) % len(tuberFrames)
                # print("Updating render. ", currentFrame)
            image_timer -= 1.0 / framerate

debugPrint("Animation classes created.\nCreating GUI classes and button actions...")

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

    def setFont(self, font):
        self.font = font
    def getFont(self):
        return self.font

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

currentScreen = "opening"
# can be "opening", "settings", "audio", and "tuber"

updateFrameRunning = False

# Button Actions
def openEditor():
    print("Open Editor")

audioDeviceScreenText = [
    ClickableText("Audio Device", (30, 15), UniFont, (255, 255, 255)),
    ClickableText("Type the number of the audio device and hit Enter", (30, 90), UniFontSmaller, (255, 255, 255)),
]

audioDevice_selected = [
    ClickableText(f"Selected Audio Device: {audioDeviceText}", (30, height - 50), UniFont, (255, 255, 255))
]

def openTuber():
    print("Open Tuber")
    loadTuber(None)

def createNewTuber():
    global currentScreen
    currentScreen = "tuber"
    print("New Tuber")

changingKeybind = False

def beginKeybindChange():
    global changingKeybind
    changingKeybind = True

colorPickerGUI = None

def changeBGColor():
    global BGCOLOR, colorPickerGUI
    colorPickerGUI = pygame_gui.windows.UIColourPickerDialog(pygame.Rect(160,50,420,400), settings_UImanager, window_title="Choose Background Color", initial_colour=pygame.Color(BGCOLOR[0], BGCOLOR[1], BGCOLOR[2]))
    changeBGColorButton.disable()

debugPrint("GUI classes created.\nCreating Tuber loading functions...")

# tuber loading definitions
def loadExpression(expressionSet, animation):
    global currentAnimation, tuberFrames, framerate, fpsClock, idleClockCounter, currentTotalFrames, locked, currentFrame, currentExpression, idling, randIdleMin, randIdleMax, timeUntilNextIdle, currentAnimationType, idleChoiceIndex
    idling = False
    idle_timer_reset()
    randIdleMin = -1
    randIdleMax = -1
    timeUntilNextIdle = -1
    if(animation == "main" and expressionSet.getMain().exists()):
        currentAnimation = expressionSet.getMain()
    elif(animation == "in" and expressionSet.getTransitionIn().exists()):
        currentAnimation = expressionSet.getTransitionIn()
    elif(animation == "out" and expressionSet.getTransitionOut().exists()):
        currentAnimation = expressionSet.getTransitionOut()
    elif(animation == "idle" and expressionSet.getIdleSet().exists()):
        currentAnimation = expressionSet.getIdleSet().getRandomIdle()
        timeUntilNextIdle = random.randint(randIdleMin, randIdleMax)
    elif(animation == "talk" and expressionSet.getTalk().exists()):
        currentAnimation = expressionSet.getTalk()
    elif(animation == "peak" and expressionSet.getPeak().exists()):
        currentAnimation = expressionSet.getPeak()
    else:
        print("Animation does not exist.")
        return
    currentAnimationType = "expression"
    debugPrint(f"Loading animation \"{animation}{f' {idleChoiceIndex}' if animation == 'idle' else ''}\" from expression set \"{expressionSet.getName()}.\"")

    tuberFrames = currentAnimation.frames
    # print(currentAnimation.frames)
    framerate = currentAnimation.fps
    currentTotalFrames = len(tuberFrames)
    currentFrame = 0
    if(expressionSet.getIdleSet().exists()):
        randIdleMin = expressionSet.getIdleSet().getMinSec()
        randIdleMax = expressionSet.getIdleSet().getMaxSec()
        timeUntilNextIdle = random.randint(randIdleMin, randIdleMax)
    locked = currentAnimation.locking
    fpsClock = pygame.time.Clock()
    currentExpression = expressionSet.getName()

def loadCanned(cannedAnimation):
    global currentAnimation, tuberFrames, framerate, fpsClock, idleClockCounter, currentTotalFrames, locked, currentFrame, currentExpression, idling, randIdleMin, randIdleMax, timeUntilNextIdle, currentAnimationType
    debugPrint(f"Loading CANNED animation \"{cannedAnimation.getName()}.\"")
    idling = False
    idle_timer_reset()
    randIdleMin = -1
    randIdleMax = -1
    timeUntilNextIdle = -1
    currentAnimationType = "canned"
    currentAnimation = cannedAnimation.getAnimation()
    
    tuberFrames = currentAnimation.frames
    framerate = currentAnimation.fps
    currentTotalFrames = len(tuberFrames)
    currentFrame = 0
    locked = currentAnimation.locking
    fpsClock = pygame.time.Clock()
    currentExpression = cannedAnimation.getName()

def loadTuber(path):
    global currentScreen, tuberName, creator, created, modified, randomDuplicateReduction, expressionList, cannedAnimationList, tuberFrames, expressionIndex, cannedAnimationIndex, currentAnimation, currentFrame, framerate, fpsClock, idleClockCounter, currentTotalFrames, locked, randIdleMax, randIdleMin, settings_options
    currentScreen = "tuber"

    if(path == None):
        # file dialog to select json file   
        root = tk.Tk()
        root.withdraw()

        file_path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json")],
            title="Select a JSON file",
        )

        # print("Selected file:", file_path)
        path = file_path
        # load json file
        with open(file_path) as json_file:
            data = json.load(json_file)
    else:
        with open(path) as json_file:
            data = json.load(json_file)
        # print(data)
    # print("Loading tuber: " + data["name"])
    tuberName = data["name"]
    creator = data["creator"]
    created = data["created"]
    modified = data["last_modified"]
    randomDuplicateReduction = data["random_duplicate_reduction"]
    # an RDR of 0 means it will NEVER try to stop the same idle from playing multiple times in a row, 
    # 1 means it will ALWAYS prevent repetition
    # decimals are allowed
    name1 = ""
    for expressionData in data["expressions"]:
        if name1 == "":
            name1 = expressionData["name"]
        # print("Loading expression: " + expressionData["name"])
        # expression set requires a main animation, an idle set, and loop animations

        # main animation        REQUIRED
        main = Animation(expressionData["anims"]["Main"]["frames"], expressionData["anims"]["Main"]["fps"], expressionData["anims"]["Main"]["locking"])

        # idle set
        idleList = []
        if(not expressionData["anims"]["Idles"]):
            # print("No idles found.")
            idles = IdleSet(None, None, None)
            randIdleMax = -1
            randIdleMin = -1
        else:
            for idle in expressionData["anims"]["Idles"]["idleAnims"]:
                idleList.append(Animation(idle["frames"], idle["fps"], idle["locking"]))
            idles = IdleSet(idleList, expressionData["anims"]["Idles"]["randomSecMin"], expressionData["anims"]["Idles"]["randomSecMax"])
        # print(f"all idles for {expressionData['name']}:\n {idleList}")


        # talking
        if(not expressionData["anims"]["Talk"]):
            # print("No talking animation found.")
            talking = Animation(None, None, None)
        else:
            talking = Animation(expressionData["anims"]["Talk"]["frames"], expressionData["anims"]["Talk"]["fps"], expressionData["anims"]["Talk"]["locking"])

        # peak
        if(not expressionData["anims"]["Peak"]):
            # print("No peak animation found.")
            peak = Animation(None, None, None)
        else:
            peak = Animation(expressionData["anims"]["Peak"]["frames"], expressionData["anims"]["Peak"]["fps"], expressionData["anims"]["Peak"]["locking"])

        # transition in
        transitionIn = Animation(expressionData["anims"]["TransitionIN"]["frames"], expressionData["anims"]["TransitionIN"]["fps"], expressionData["anims"]["TransitionIN"]["locking"])

        # transition out
        transitionOut = Animation(expressionData["anims"]["TransitionOUT"]["frames"], expressionData["anims"]["TransitionOUT"]["fps"], expressionData["anims"]["TransitionOUT"]["locking"])

        # create ExpressionSet
        expressionList.append(ExpressionSet(expressionData["name"], main, idles, talking, peak, transitionIn, transitionOut, expressionData["requires"], expressionData["blockers"], expressionData["hotkeys"]))
        expressionIndex[expressionData["name"]] = len(expressionList) - 1

        for key in expressionData["hotkeys"]:
            # add to hotkey dictionary
            if(key is None):
                continue
            if(key not in hotkeyDictionary):
                hotkeyDictionary[key] = [expressionData["name"]]
            else:
                hotkeyDictionary[key].append(expressionData["name"])

        # print(expressionDictionary)

    for cannedAnimationData in data["canned_anims"]:
        # name, animation, hotkey, requires, result
        cannedAnimationList.append(CannedAnimation(cannedAnimationData["name"], Animation(cannedAnimationData["anim"]["frames"], cannedAnimationData["anim"]["fps"], True), cannedAnimationData["hotkeys"], cannedAnimationData["requires"], cannedAnimationData["blockers"], cannedAnimationData["result"]))
        cannedAnimationIndex[cannedAnimationData["name"]] = len(cannedAnimationList) - 1

        for key in cannedAnimationData["hotkeys"]:
            if(key not in hotkeyDictionary):
                hotkeyDictionary[key] = [cannedAnimationData["name"]]
            else:
                hotkeyDictionary[key].append(cannedAnimationData["name"])
    
    # print(hotkeyDictionary)
    loadExpression(expressionList[expressionIndex[name1]], "main")
    # print(f"Path = {path}")
    prefini.set("LastUsed", "lastloaded", "\"" + str(path) + "\"")
    settings_options[2].setText(f"Current Tuber: {tuberName} by {creator}")
    with open("preferences.ini", "w") as configfile:
        prefini.write(configfile)

    print("Loaded Tuber: " + tuberName)

# Define the clickable text options
settings_options = [
    ClickableText(f"Talk Threshold: ", (100, height-50), UniFontSmaller, WHITE, None),
    ClickableText(f"Peak Threshold: ", (100, height-100), UniFontSmaller, WHITE, None),
    ClickableText(f"Current Tuber: {tuberName} by {creator}", (0, 0), UniFontBigger, WHITE, None),
    ClickableText(f"ToonTuber Player {version}", (0, 40), UniFontSmaller, WHITE, None),
    ClickableText("program by JNS", (0, 60), UniFontSmaller, WHITE, None),
    ClickableText("original idea by ScottFalco", (0, 80), UniFontSmaller, WHITE, None)
    
]

opening_options = [
    ClickableText("New Tuber", (width/3, 75), UniFont, WHITE, createNewTuber),
    ClickableText("Load Tuber", (width/3, 125), UniFont, WHITE, openTuber)
]

debugPrint("Tuber loading functions created.\nSetting up final GUI elements and functions...")

loadToonTuberButton = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((0, 125), (200, 50)),
                                             text='Load ToonTuber',
                                             manager=settings_UImanager)

changeSettingsKeybindButton = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((0, 175), (300, 50)),
                                                text=f'Change Settings Keybind (\"{settingsKeybindName}\")',
                                                manager=settings_UImanager)

changeBGColorButton = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((0, 225), (225, 50)),
                                                text='Change Background Color',
                                                manager=settings_UImanager)

audioDeviceDropdown = pygame_gui.elements.UIDropDownMenu(options_list=audioDeviceNames,
                                                        starting_option=lastAudioDevice,
                                                        relative_rect=pygame.Rect((0, 275), (325, 50)),
                                                        manager=settings_UImanager)

openEditorButton = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((0, 325), (200, 50)),
                                             text='Open Editor',
                                             manager=settings_UImanager)


talk_textEntry = pygame_gui.elements.UITextEntryLine(
    pygame.Rect((250, height-55), (50, 25)),
    manager=settings_UImanager
)

talk_textEntry.set_allowed_characters('numbers')
talk_textEntry.set_text(str(talkThreshold))

peak_textEntry = pygame_gui.elements.UITextEntryLine(
    pygame.Rect((250, height-105), (50, 25)),
    manager=settings_UImanager
)

peak_textEntry.set_allowed_characters('numbers')
peak_textEntry.set_text(str(peakThreshold))



# text_settings = UniFont.render("SETTINGS", True, BLACK)

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
def display_fps(txt, clock, heightSubtract):
    fps = txt + str(int(clock.get_fps()))
    fps_text = UniFont.render(fps, True, WHITE)
    fps_rect = fps_text.get_rect(bottomright=(width, height-heightSubtract))
    screen.blit(fps_text, fps_rect)

# Create a Pygame clock object to measure time between frames
clock = pygame.time.Clock()

debugPrint("Creating mic meter sprites...")

# Load the sprites
mic_feedback = pygame.image.load("assets\micLevel.png").convert_alpha()
mic_range = pygame.image.load("assets\micRange.png").convert_alpha()

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

# create both threshold arrow images
talkThresholdSprite = pygame.image.load("assets\ThresholdArrow.png").convert_alpha()
peakThresholdSprite = pygame.image.load("assets\ThresholdArrow.png").convert_alpha()

talkThreshPos = 0
peakThreshPos = 0

# no need to scale the threshold arrows, they are already the correct size. prepare the sprites for drawing later

debugPrint("Mic meter sprites created.\nBeginning audio and render threads...")

# begin threads
render_thread = threading.Thread(target=update_render_thread)
render_thread.daemon = True

debugPrint("Audio and render threads started.\nBeginning main Pygame loop...")

# load the tuber from the preferences file if it exists
if(os.path.exists(lastTuberLoaded)):
    loadTuber(lastTuberLoaded)

newAudioDevice = ""

# Main Pygame loop
running = True
while running:
    if(not updateFrameRunning and currentScreen != "opening"):
        updateFrameRunning = True
        render_thread.start()
        idleTimer_thread.start()
    # Measure the time between frames and limit the FPS to 60
    delta_time = clock.tick(60) / 1000.0
    talkNotBlank = talk_textEntry.get_text() != "" 
    peakNotBlank = peak_textEntry.get_text() != ""

    
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN and (event.key == settingsKeybind and not changingKeybind) and (currentScreen == "tuber" or currentScreen == "settings"):
            # print("toggling settings")
            currentScreen = "tuber" if currentScreen == "settings" else "settings"
        # key pressed during settings        
        elif event.type == pygame.KEYDOWN and currentScreen == "settings":
            if(changingKeybind):
                # print(event.key)
                settingsKeybind = event.key
                settingsKeybindName = pygame.key.name(event.key)
                # print("keybind changed to " + settingsKeybindName)

                changeSettingsKeybindButton.text = f'Change Settings Keybind (\"{settingsKeybindName}\")'
                changeSettingsKeybindButton.rebuild()

                prefini.set("Settings", "keybind", "\"" + str(settingsKeybindName) + "\"" )
                with open("preferences.ini", "w") as configfile:
                    prefini.write(configfile)
                changingKeybind = False
            # print("key pressed and settings is active")
            # save the latest key pressed in case the user is typing a value for the mic threshold
            latestUnicode = event.unicode
            # print(latestUnicode)
            acceptableChars = "0123456789."
            
            

        # if the user clicks on a text option, do the action
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mousePos = pygame.mouse.get_pos()

            if(talkNotBlank and int(talk_textEntry.get_text()) > 100):
                talk_textEntry.set_text("100")
            if(peakNotBlank and int(peak_textEntry.get_text()) > 100):
                peak_textEntry.set_text("100")
            if(peakNotBlank and talkNotBlank and int(peak_textEntry.get_text()) < int(talk_textEntry.get_text())):
                peak_textEntry.set_text(talk_textEntry.get_text())

            if(talkNotBlank):
                talkThreshold = int(talk_textEntry.get_text())
            if(peakNotBlank):
                peakThreshold = int(peak_textEntry.get_text())
            
            # print("mouse clicked")
            prefini.set("Thresholds", "talkthresh", str(talkThreshold))
            prefini.set("Thresholds", "peakthresh", str(peakThreshold))
            with open("preferences.ini", "w") as ini:
                prefini.write(ini)


            if currentScreen == "opening":
                for option in opening_options:
                    if option.isClicked(mousePos):
                        option.doAction()
            if currentScreen == "settings":
                for option in settings_options:
                    if option.isClicked(mousePos):
                        option.doAction()

        elif event.type == pygame_gui.UI_COLOUR_PICKER_COLOUR_PICKED:
            BGCOLOR = event.colour
            prefini.set("Settings", "bgcolor", str(BGCOLOR))
            with open("preferences.ini", "w") as ini:
                prefini.write(ini)
            changeBGColorButton.enable()
        
        elif event.type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED:
            # print("dropdown changed")
            getAudioDevices()
            audioDeviceDropdown.options_list = audioDeviceNames
            audioDeviceDropdown.kill()
            audioDeviceDropdown = pygame_gui.elements.UIDropDownMenu(options_list=audioDeviceNames,
                                                                    starting_option=lastAudioDevice,
                                                                    relative_rect=pygame.Rect((0, 275), (325, 50)),
                                                                    manager=settings_UImanager)
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == loadToonTuberButton:
                loadTuber(None)
            elif(event.ui_element == openEditorButton):
                openEditor()
            elif(event.ui_element == changeSettingsKeybindButton):
                beginKeybindChange()
            elif(event.ui_element == changeBGColorButton):
                changeBGColor()

        settings_UImanager.process_events(event)
    settings_UImanager.update(delta_time)

    if(audioDeviceDropdown.selected_option != lastAudioDevice):
        # get the ID of the selected option in the audio device list
        newAudioDevice = audioDeviceDropdown.selected_option
        lastAudioDevice = newAudioDevice
        prefini.set("LastUsed", "lastmic", "\"" + str(lastAudioDevice) + "\"")
        with open("preferences.ini", "w") as ini:
            prefini.write(ini)
        audio_device_id = audioDeviceList[newAudioDevice]
        select_audio_device(audio_device_id)

    # Draw the green background
    screen.fill(BGCOLOR)

    # draw Tuber to screen
    if(currentScreen == "tuber" or currentScreen == "settings"):
        tuber_rect = pygame.Rect(0, 0, width, height)
        # failsafe. will repeat a frame if the current frame is out of range
        if(currentFrame >= len(tuberFrames)):
            currentFrame = (currentFrame % len(tuberFrames))
        currentImage = tuberFrames[currentFrame]
        
        render = currentImage.convert_alpha()
        # scale tuber image to fill screen
        render = pygame.transform.smoothscale(render, (width, height))
        screen.blit(render, tuber_rect)

    # if on the opening screen, prompt user if they want to open an existing tuber or make a new one
    if currentScreen == "opening":
        # print("opening screen")
        darken_screen()
        draw_text_options(opening_options)
        # if user clicks on "Open ToonTuber", open the file explorer and allow them to select a tuber
        # if user clicks on "New ToonTuber", open the editor
    elif currentScreen == "audio":
        darken_screen()
        draw_text_options(audioDeviceScreenText)
        draw_text_options(audioDevice_options)
        draw_text_options(audioDevice_selected)

    elif currentScreen == "settings":
        darken_screen()
        draw_text_options(settings_options)
        # Display the FPS counter in the bottom right corner
        display_fps("program FPS: ",clock, 0)
        display_fps("anim FPS: ", fpsClock, 50)

        if(changingKeybind):
            # print("changing keybind")
            draw_text_options([ClickableText("Press a key to change keybind", (0, 400), UniFont, WHITE, None)])

        # these values assume that the top left corner of the sprite is 0,0
        # therefore, the bottom right of the sprite is the width and height
        
        micFill_clipHeight = round((mic_feedback.get_height() * (avgVol/100)))
        clip_rect = pygame.Rect(0, mic_feedback.get_height() - micFill_clipHeight, mic_feedback.get_width(), micFill_clipHeight)
        mic_fill_clipped = pygame.Surface((clip_rect.width, clip_rect.height), pygame.SRCALPHA)
        mic_fill_clipped.blit(mic_feedback, (0, 0), clip_rect)
        screen.blit(mic_fill_clipped, (0, height - mic_fill_clipped.get_height()))

        # draw mic range sprite a little next to the mic fill sprite
        screen.blit(mic_range, (mic_fill_clipped.get_width()/3, height - mic_range.get_height()))

        # get the vertical center of the threshold arrow sprite
        arrowCenter = talkThresholdSprite.get_height()/2

        # update the mic threshold arrow positions based on the talkThreshold and peakThreshold values over the range of the top of the mic fill sprite to the bottom
        talkThreshPos = (0, height-((talkThreshold * (mic_range.get_height() / 100)) + arrowCenter))
        peakThreshPos = (0, height-((peakThreshold * (mic_range.get_height() / 100)) + arrowCenter))

        # draw talk threshold arrow
        screen.blit(talkThresholdSprite, talkThreshPos)
        screen.blit(peakThresholdSprite, peakThreshPos)
    
    if(currentScreen == "settings"):
        settings_UImanager.draw_ui(screen)

    # Update the Pygame window
    pygame.display.flip()

# Quit Pygame
pygame.quit()

stream.stop_stream()
stream.close()
pa.terminate()