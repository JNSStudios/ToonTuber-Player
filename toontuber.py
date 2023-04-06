import pygame
import pyaudio
import numpy as np
import threading
import keyboard
import tkinter as tk
from tkinter import filedialog
import json
import os
import random

# helper function, comment out the "print" line to disable this function
def debugPrint(str):
    # print(str)
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
tuberFrames = []
expressionIndex = {}
cannedAnimationIndex = {}

hotkeyDictionary = {}   # key: key pressed, value: an array of strings for each animation name

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

talkThreshold = 75
peakThreshold = 95

latestUnicode = None
talkThreshText = f"{talkThreshold}"
peakThreshText = f"{peakThreshold}"
selectedBox = ""

# Define some colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)


print("Toon Tuber Player v1.0.0")

pygame.init()

debugPrint("Pygame initialized. Setting up window...")
# Set up the Pygame window
width, height = 750, 750
screen = pygame.display.set_mode((width, height))

# Set the window name
pygame.display.set_caption("Toon Tuber Player")

# Opening screen
UniFont = pygame.font.Font('freesansbold.ttf', 24)
UniFontSmaller = pygame.font.Font('freesansbold.ttf', 18)
text = UniFont.render("Toon Tuber Player", True, (255, 255, 255))
textRect = text.get_rect()
textRect.center = (width // 2, height // 2)

debugPrint("Opening screen set up.\nInitializing audio data stuff...")

# audio stuff
rms = 0
avgVol = 0
chunk_size = 256  # number of audio samples per chunk
sample_rate = 44100  # number of samples per second

volRollingAverage = []
volRollingAverageLength = 10

pa = pyaudio.PyAudio()

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

debugPrint("Audio data stuff initialized.\nInitializing keyboard reader thread...")

def pushHotKey(key):
    global latestKeyPressed, lastKeyPressed, keyHeld, currentAnimation, expressionList, cannedAnimationList, queuedAnimation, currentExpression, queuedExpression, transition, queuedAnimationType, currentAnimationType
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


            if(animName in expressionIndex 
                and ((currentExpression in expressionList[expressionIndex[animName]].requires 
                     or expressionList[expressionIndex[animName]].requires == [None]) or (queuedExpression != "" and queuedExpression in expressionList[expressionIndex[animName]].requires))
                and animName != currentExpression and currentAnimationType != "canned"):
                # print(f"queuing {animName}")
                # it's an expression and the needed anim is ready. check if the required animation is already playing
                queuedExpression = animName
                queuedAnimationType = "expression"
                break

            elif(animName in cannedAnimationIndex 
                 and (currentExpression in cannedAnimationList[cannedAnimationIndex[animName]].requires 
                      or cannedAnimationList[cannedAnimationIndex[animName]].requires == [None]) 
                 and animName != currentExpression):
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

# keyboard reading thread
def keyboard_thread():
    while True:
        event = keyboard.read_event()
        if event.event_type == "down":
            # print(f"Key pressed: {event.name}")
            pushHotKey(event.name)
        elif event.event_type == "up":
            # print(f"Key released: {event.name}")
            releaseHotKey(event.name)

keyboard_thread = threading.Thread(target=keyboard_thread)
keyboard_thread.daemon = True
keyboard_thread.start()

debugPrint("Keyboard reader thread started.\nCreating animation classes...")

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

class Animation:
    def __init__(self, frames, fps, locking):
        if(frames is None):
            self.frames = None
            self.fps = None
            self.locking = None
        else:
            self.frames = load_pngs(frames) # list of PNG images
            self.fps = fps                  # int
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
    def __init__(self, name, main, idleSet, talk, peak, trIn, trOut, requires, hotkey):
        self.name = name                # string
        self.main = main                # Animation object
        self.idleSet = idleSet          # IdleSet object
        self.talk = talk                # Animation object
        self.peak = peak                # Animation object
        self.trIn = trIn          # Animation object
        self.trOut = trOut        # Animation object
        self.requires = requires        # list of ExpressionSets
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

def update_render_thread():
    global currentFrame, framerate, image_timer, locked, transition, queuedExpression, currentExpression, talkThreshold, peakThreshold, avgVol, idleClockCounter, idleTimer, currentAnimationType, queuedAnimationType, idling, timeUntilNextIdle
    while True:
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
                if((queuedExpression != currentAnimation and queuedExpression != "") and transition == "" and currentAnimationType != "canned"):
                    transition = "out"
                    loadExpression(expressionList[expressionIndex[currentExpression]], "out")
                elif(transition == "out" and animationFinished):
                    # print("trying to transition out")
                    currentExpression = queuedExpression
                    currentAnimationType = queuedAnimationType
                    queuedExpression = ""
                    queuedAnimationType = ""
                    if(currentAnimationType == "expression"):
                        # print("expression")
                        transition = "in"
                        currentAnimationType = "expression"
                        loadExpression(expressionList[expressionIndex[currentExpression]], "in")                        
                    elif(currentAnimationType == "canned"):
                        # print("canned animation")
                        transition = ""
                        currentAnimationType = "canned"
                        loadCanned(cannedAnimationList[cannedAnimationIndex[currentExpression]])
                elif(transition == "in" and animationFinished):
                    transition = ""
                    loadExpression(expressionList[expressionIndex[currentExpression]], "main")
                elif(currentAnimationType == "canned" and animationFinished):
                    # print("canned animation ended")
                    resultingExpression = cannedAnimationList[cannedAnimationIndex[currentExpression]].getResult()
                    loadExpression(expressionList[expressionIndex[resultingExpression]], "main")
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

# Button Actions
def openPlayerSettings():
    print("Open Player Settings")

def openEditor():
    print("Open Editor")

def createNewTuber():
    global openingScreen
    openingScreen = False
    print("New Tuber")

def talkThreshSelected():
    global selectedBox, settings_options, talkThreshText
    settings_options[3].setFont(UniFont)
    selectedBox = "talk"
    talkThreshText = ""

def peakThreshSelected():
    global selectedBox, settings_options, peakThreshText
    settings_options[4].setFont(UniFont)
    selectedBox = "peak"
    peakThreshText = ""

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
    print(f"Loading animation \"{animation}{f' {idleChoiceIndex}' if animation == 'idle' else ''}\" from expression set \"{expressionSet.getName()}.\"")

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
    print(f"Loading CANNED animation \"{cannedAnimation.getName()}.\"")
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

def loadTuber():
    global openingScreen, tuberName, creator, created, modified, randomDuplicateReduction, expressionList, cannedAnimationList, tuberFrames, expressionIndex, cannedAnimationIndex, currentAnimation, currentFrame, framerate, fpsClock, idleClockCounter, currentTotalFrames, locked, randIdleMax, randIdleMin
    openingScreen = False
    # file dialog to select json file   
    root = tk.Tk()
    root.withdraw()

    file_path = filedialog.askopenfilename(
        filetypes=[("JSON files", "*.json")],
        title="Select a JSON file",
    )

    # print("Selected file:", file_path)

    # load json file
    with open(file_path) as json_file:
        data = json.load(json_file)
        # print(data)
    name = data["name"]
    creator = data["creator"]
    created = data["created"]
    modified = data["last_modified"]
    randomDuplicateReduction = data["random_duplicate_reduction"]
    # an RDR of 0 means it will NEVER try to stop the same idle from playing multiple times in a row, 
    # 1 means it will ALWAYS prevent repetition
    # decimals are allowed
    for expressionData in data["expressions"]:
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
        expressionList.append(ExpressionSet(expressionData["name"], main, idles, talking, peak, transitionIn, transitionOut, expressionData["requires"], expressionData["hotkey"]))
        expressionIndex[expressionData["name"]] = len(expressionList) - 1

        # add to hotkey dictionary
        if(expressionData["hotkey"] not in hotkeyDictionary):
            hotkeyDictionary[expressionData["hotkey"]] = [expressionData["name"]]
        else:
            hotkeyDictionary[expressionData["hotkey"]].append(expressionData["name"])

        # print(expressionDictionary)

    for cannedAnimationData in data["canned_anims"]:
        # name, animation, hotkey, requires, result
        cannedAnimationList.append(CannedAnimation(cannedAnimationData["name"], Animation(cannedAnimationData["anim"]["frames"], cannedAnimationData["anim"]["fps"], True), cannedAnimationData["hotkey"], cannedAnimationData["requires"], cannedAnimationData["result"]))
        cannedAnimationIndex[cannedAnimationData["name"]] = len(cannedAnimationList) - 1

        if(cannedAnimationData["hotkey"] not in hotkeyDictionary):
            hotkeyDictionary[cannedAnimationData["hotkey"]] = [cannedAnimationData["name"]]
        else:
            hotkeyDictionary[cannedAnimationData["hotkey"]].append(cannedAnimationData["name"])
        # print(cannedAnimationDictionary)
    
    print(hotkeyDictionary)
    loadExpression(expressionList[expressionIndex["Main"]], "main")
    print("Loaded Tuber: " + name)

debugPrint("Tuber loading functions created.\nSetting up final GUI elements and functions...")

# text_settings = UniFont.render("SETTINGS", True, BLACK)

# Define the clickable text options
settings_options = [
    ClickableText("Load ToonTuber", (0, 0), UniFont, WHITE, loadTuber),
    ClickableText("Player Settings", (0, 50), UniFont, WHITE, openPlayerSettings),
    ClickableText("Open Editor", (0, 100), UniFont, WHITE, openEditor),
    ClickableText(f"Talk Threshold: {talkThreshText}/100", (100, height-50), UniFontSmaller, WHITE, talkThreshSelected),
    ClickableText(f"Peak Threshold: {peakThreshText}/100", (100, height-100), UniFontSmaller, WHITE, peakThreshSelected)
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
def display_fps(txt, clock, heightSubtract):
    fps = txt + str(int(clock.get_fps()))
    fps_text = UniFont.render(fps, True, WHITE)
    fps_rect = fps_text.get_rect(bottomright=(width, height-heightSubtract))
    screen.blit(fps_text, fps_rect)

# Create a Pygame clock object to measure time between frames
clock = pygame.time.Clock()

debugPrint("Creating mic meter sprites...")

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

# create both threshold arrow images
talkThresholdSprite = pygame.image.load("ThresholdArrow.png").convert_alpha()
peakThresholdSprite = pygame.image.load("ThresholdArrow.png").convert_alpha()


talkThreshPos = 0
peakThreshPos = 0


# no need to scale the threshold arrows, they are already the correct size. prepare the sprites for drawing later

debugPrint("Mic meter sprites created.\nBeginning audio and render threads...")

# begin threads

# Open the stream with the callback function
stream = pa.open(format=pyaudio.paInt16,
                 channels=1,
                 rate=sample_rate,
                 input=True,
                 frames_per_buffer=chunk_size,
                 stream_callback=audio_callback)

# Start the audio stream
stream.start_stream()

render_thread = threading.Thread(target=update_render_thread)
render_thread.daemon = True

debugPrint("Audio and render threads started.\nBeginning main Pygame loop...")

# Main Pygame loop
running = True
openingScreen = True
updateFrameRunning = False

# TEMPORARY INSTANT-LOAD PROMPT
loadTuber()

while running:
    if(not updateFrameRunning and not openingScreen):
        updateFrameRunning = True
        render_thread.start()
        idleTimer_thread.start()
    # Measure the time between frames and limit the FPS to 60
    delta_time = clock.tick(60) / 1000.0

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_p and not openingScreen:
            settings_active = not settings_active
        # if the user clicks on a text option, do the action
        elif event.type == pygame.KEYDOWN and settings_active:
            # save the latest key pressed in case the user is typing a value for the mic threshold
            latestUnicode = event.unicode
            # print(latestUnicode)
            acceptableChars = "0123456789."
            if(latestUnicode in acceptableChars):
                if(selectedBox == "talk"):
                    talkThreshText += latestUnicode
                    if(talkThreshText.isnumeric()):
                        talkThreshold = int(talkThreshText)
                        if(talkThreshold > 100):
                            talkThreshold = 100
                            talkThreshText = "100"
                    settings_options[3].setText(f"Talk Threshold: {talkThreshold}/100")
                elif(selectedBox == "peak"):
                    peakThreshText += latestUnicode
                    if(peakThreshText.isnumeric()):
                        peakThreshold = int(peakThreshText)
                        if(peakThreshold > 100):
                            peakThreshold = 100
                            peakThreshText = "100"
                    settings_options[4].setText(f"Peak Threshold: {peakThreshText}/100")
            elif(event.key == pygame.K_BACKSPACE):
                if(selectedBox == "talk"):
                    talkThreshText = talkThreshText[:-1]
                    if(talkThreshText.isnumeric()):
                        talkThreshold = int(talkThreshText)
                        if(talkThreshold > 100):
                            talkThreshold = 100
                            talkThreshText = "100"
                    settings_options[3].setText(f"Talk Threshold: {talkThreshText}/100")
                elif(selectedBox == "peak"):
                    peakThreshText = peakThreshText[:-1]
                    if(peakThreshText.isnumeric()):
                        peakThreshold = int(peakThreshText)
                        if(peakThreshold > 100):
                            peakThreshold = 100
                            peakThreshText = "100"
                    settings_options[4].setText(f"Peak Threshold: {peakThreshText}/100")

        elif event.type == pygame.MOUSEBUTTONDOWN:
            mousePos = pygame.mouse.get_pos()
            selectedBox = ""
            settings_options[3].setFont(UniFontSmaller)
            settings_options[4].setFont(UniFontSmaller)
            if(peakThreshold < talkThreshold):
                peakThreshold = talkThreshold
                peakThreshText = str(talkThreshold)
                settings_options[4].setText(f"Peak Threshold: {peakThreshText}/100")


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
    else:

        

        # draw Tuber to screen
        tuber_rect = pygame.Rect(0, 0, width, height)
        # failsafe. will repeat a frame if the current frame is out of range
        if(currentFrame >= len(tuberFrames)):
            currentFrame = (currentFrame % len(tuberFrames))
        currentImage = tuberFrames[currentFrame]
        
        render = currentImage.convert_alpha()
        # scale tuber image to fill screen
        render = pygame.transform.smoothscale(render, (width, height))
        screen.blit(render, tuber_rect)

    

    # If the settings screen is active, darken the screen and draw the text options
    if settings_active:
        darken_screen()
        draw_text_options(settings_options)
        # Display the FPS counter in the bottom right corner
        display_fps("program FPS: ",clock, 0)
        display_fps("anim FPS: ", fpsClock, 50)
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

    # Update the Pygame window
    pygame.display.flip()

# Quit Pygame
pygame.quit()

stream.stop_stream()
stream.close()
pa.terminate()