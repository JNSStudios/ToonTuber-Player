import os
import pygame
from PIL import Image
import random

import debug
import file_reading

MISSING_IMAGE = pygame.image.load(os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "MissingImage.png"))
randomDuplicateReduction = 0
animationSFXMuted = False
animationSFXVolume = 1




def load_animation_images(paths):
    # create a list of Pygame images from the selected files
    images = []
    # loop through each provided path in the provided list
    for file_path in paths:
        singlePath = file_path
        file_path = os.path.join(file_reading.jsonPath, "frames", file_path)
        debug.debugPrint(file_path)
        if(os.path.isfile(file_path)):
            extension = os.path.splitext(file_path)[1]
            if(extension == ".png"):
                debug.debugPrint(f"Loading image {singlePath}")
                file_reading.currentlyLoadingFile = f"Loading image {singlePath}"
                image = pygame.image.load(os.path.join(file_reading.jsonPath, file_path))
                images.append(image)
            elif(extension == ".gif"):
                debug.debugPrint(f"Loading gif {singlePath}")
                # currentlyLoadingFile = f"Loading gif {singlePath}"
                gif = Image.open(os.path.join(file_reading.jsonPath, file_path))
                # .mimread(os.path.join(jsonPath, file_path))
                for frame_index in range(gif.n_frames):
                    # convert the image to a Pygame surface
                    # count the number of bytes in frame.tobytes() and print it out
                    file_reading.currentlyLoadingFile = f"Loading gif {singlePath} frames ({frame_index}/{gif.n_frames})"

                    gif.seek(frame_index)
                    frame = gif.convert("RGBA")
                    pygameFrame = pygame.image.fromstring(frame.tobytes(), frame.size, frame.mode).convert_alpha()

                    # save gif frame (with transparency) as a pygame image
                    # pygameFrame = pygame.image.fromstring(frame.tobytes(), frame.size, frame.mode).convert_alpha() 
                    # print("ABOUT OT DO THING")
                    # print("BYTES:\n", len(frame.tobytes()))
                    # print("SHAPE:\n", frame.shape[1::-1])
                    # print("MODE:\n", frame.tobytes()[0:10])
                    # print out what the frombuffer method is LOOKING FOR
                    # pygameFrame = pygame.image.frombuffer(frame.tobytes(), (frame.shape[1::-1]), 'RGBA')
                    images.append(pygameFrame)
                return images
        else:
            images.append(MISSING_IMAGE)
            debug.debugPrint(f"Image at {file_path} not found, using MissingImage.png instead.")
    return images

def playAnimationSound(soundPath):
    global animationSFXVolume, animationSFXMuted
    debug.debugPrint(f"Playing sound {soundPath}")
    soundPath = os.path.join(file_reading.jsonPath, "sounds", soundPath)
    sound = pygame.mixer.Sound(soundPath)
    sound.set_volume(animationSFXVolume if not animationSFXMuted else 0)
    sound.play(loops=0)

class Animation:
    def __init__(self, frames, fps, locking):
        if(frames is None):
            self.frames = None
            self.fps = None
            self.locking = None
        else:
            self.frames = load_animation_images(frames)
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
    def __init__(self, name, main, idleSet, talk, peak, trIn, trOut, requires, blockers, sound, instant, hotkey):
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
        self.sound = sound              # Sound object
        self.instant = instant          # bool
        if(self.requires[0] == None):
            self.requires = []
        if(self.blockers[0] == None):
            self.blockers = []

    def __str__(self):
        return f"ExpressionSet {self.name}:\nMain: {self.main}\n{self.idleSet}\nTalk: {self.talk}\nPeak: {self.peak}\nTransition In: {self.trIn}\nTransition Out: {self.trOut}\nRequires: {self.requires}\nHotkey: {self.hotkey}\nSound: {self.sound}\nInstant transition?: {self.instant}"

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

    def hasRequires(self):
        return len(self.requires) > 0
    
    def getBlockers(self):
        return self.blockers
    def addBlockers(self, newBlockers):
        self.blockers.append(newBlockers)
    def removeBlockers(self, oldBlockers):
        if(oldBlockers not in self.blockers):
            print("Blocker state not found.")
        else:
            self.blockers.remove(oldBlockers)
    def hasBlockers(self):
        return len(self.blockers) > 0
    

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

    def getSound(self):
        return None if (self.sound == "" or self.sound == None) else self.sound
    def setSound(self, sound):
        self.sound = sound

    def isInstant(self):
        return self.instant
    def setInstant(self, instant):
        self.instant = instant

class CannedAnimation:
    def __init__(self, name, animation, hotkey, requires, blockers, sound, instant, result):
        self.name = name                # string
        self.animation = animation      # Animation object
        self.hotkey = hotkey            # Hotkey object
        self.requires = requires        # list of ExpressionSets
        self.blockers = blockers        # list of ExpressionSets
        self.sound = sound              # Sound object
        self.result = result            # ExpressionSet object
        self.instant = instant          # boolean (if true, no transition is applied)
        if(self.requires[0] == None):
            self.requires = []
        if(self.blockers[0] == None):
            self.blockers = []

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
    def hasRequires(self):
        return len(self.requires) > 0

    def getResult(self):
        return self.result
    def setResult(self, result):
        self.result = result
    
    def getBlockers(self):
        return self.blockers
    def addBlockers(self, newBlockers):
        self.blockers.append(newBlockers)
    def removeBlockers(self, oldBlockers):
        if(oldBlockers not in self.blockers):
            print("Blocker state not found.")
        else:
            self.blockers.remove(oldBlockers)
    def hasBlockers(self):
        return len(self.blockers) > 0
    
    def isInstant(self):
        return self.instant
    def setInstant(self, instant):
        self.instant = instant
    
    
    def getSound(self):
        return None if (self.sound == "" or self.sound == None) else self.sound
    def setSound(self, sound):
        self.sound = sound
