# you'll need to use pip to get these libraries up here
import pygame
import pygame_gui
import pyaudio
import numpy as np
import keyboard
from StreamDeck.DeviceManager import DeviceManager
from PIL import Image
import notifypy
import noisereduce as nr

# these should be built-in
import threading
import tkinter as tk
from tkinter import filedialog
import json
import os
import random
import sys
import configparser
import datetime
import traceback
import logging

debugMode = False

version = "v1.3.0"

# OS-SPECIFIC STUFF

# macOS stuff
if sys.platform == 'darwin':
    os.environ['SDL_VIDEODRIVER'] = 'x11'


# Other helper methods and info

def compareVersions(verA, verB):
    # check if last used version is different from current version
    verA = verA.split(".")
    verB = verB.split(".")

    # remove the starting v from the first spots
    verA[0] = verA[0].replace("v", "")
    verB[0] = verB[0].replace("v", "")

    # convert to ints
    verA = [int(x) for x in verA]
    verB = [int(x) for x in verB]

    # returns -1 if A is less than B, returns 0 if equal, returns 1 if A is greater than B
    for i in range(0, len(verA)):
        if(verA[i] < verB[i]):
            return -1
        elif(verA[i] > verB[i]):
            return 1
    return 0

lastVersionINI = ""
lastVersionTUBER = ""

peakThreshold = 90
talkThreshold = 50

pa = pyaudio.PyAudio()

# get the path to the script itself, useful for finding local files
scriptPath = os.path.dirname(os.path.abspath(__file__))

# used to decide the weight reduction of animations with a met requirement when multiple animations can be selected.
nonrequiredWeight = 0.25

# rgb values for the background color (starts as green, resets later)
GREEN = (0, 255, 0)
BGCOLOR = GREEN

# play sound when crash happens so user is alerted
def handle_exception(exc_type, exc_value, exc_traceback):
    global stream

    pa.terminate()

    # Print the exception information

    print("Unhandled exception:", exc_type, exc_value)
    logging.exception(str)

    if(not debugMode and exc_type != KeyboardInterrupt):
        crashnotif = notifypy.Notify()
        crashnotif.title = "TOONTUBER PLAYER HAS CRASHED"
        crashnotif.message = "A crash report was saved. Please restart Player."
        crashnotif.icon = os.path.join(scriptPath, "assets", "crashnotificon.png")
        crashnotif.audio = os.path.join(scriptPath, "assets", "error.wav")
        crashnotif.application_name = " 🛑 ATTN! ToonTuber Player 🛑"
        crashnotif.send()

    # Call the default exception handler
    sys.__excepthook__(exc_type, exc_value, exc_traceback)

    # save the exception and traceback to a file called "Player Crash Report {date and time}.txt"
    # and have the file contain the error and traceback
    errorFileID = 0
    while(os.path.isfile(f"Player Crash Report {datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S')}{f' ({errorFileID})' if errorFileID != 0 else ''}.txt")):
        errorFileID += 1

    # get the username of the current user so we can filter it out of the file
    username = os.getlogin()

    if(exc_type != KeyboardInterrupt):
        # write the error report to a file
        with open(f"Player Crash Report {datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S')}{f' ({errorFileID})' if errorFileID != 0 else ''}.txt", "w") as f:
            # add text to the file before putting the exception details
            f.write("Oops! The player crashed! Sorry about that.\nThe text below is the error report. If you don't know what this means, please send this file to the developer, along with a description of what happened (which you can type here).\n\nWhat I was doing: \n\n")
            f.write(f"Unhandled exception: {exc_type} {exc_value}")
            for line in traceback.format_tb(exc_traceback):
                # check if the line contains the username and remove it if it's there
                if(username in line):
                    line = line.replace(username, "[username]")
                # write the line to the file
                f.write(line)
            # after all the lines are written to the file, close the file
            f.close()
    # Quit Pygame
    pygame.quit()
    # exit the whole program
    exit()

# Set the exception handler
sys.excepthook = handle_exception

logging.basicConfig(filename='debug.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# helper function, comment out the "print" line to disable this function
def debugPrint(str):
    if(debugMode):
        logging.debug(str)
        print(str)
    return

# create popup to user, with optional clickable options
def popup(title, message):
    popup = tk.Tk()
    popup.title(title)
    popup.geometry("500x175")

    # Create a label with the message
    label = tk.Label(popup, text=message)
    label.pack(pady=10)

    # Create a button to close the window
    button = tk.Button(popup, text="OK", command=popup.destroy)
    button.pack()

    # Halt the program until the window is closed
    popup.mainloop()

print(f"ToonTuber Player {version}")

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

animationSFXVolume = 1
animationSFXMuted = False

mirror = False

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
keybind_UImanager = pygame_gui.UIManager((width, height))

# Set the window name (NOTE: changing the caption might screw up existing Window Captures in OBS. Might be best not to change this.)
pygame.display.set_caption("ToonTuber Player")

# Opening screen
UniFont = pygame.font.Font('freesansbold.ttf', 24)
UniFontSmaller = pygame.font.Font('freesansbold.ttf', 18)
UniFontBigger = pygame.font.Font('freesansbold.ttf', 36)
text = UniFont.render("ToonTuber Player", True, (255, 255, 255))
textRect = text.get_rect()
textRect.center = (width // 2, height // 2)

debugPrint("Window set up.\nReading from preferences.ini....")

preferenceErrors = []

# read from preferences.ini file
try:
    if(not os.path.isfile("preferences.ini")):
        raise Exception("preferences.ini does not exist")
    prefini = configparser.ConfigParser()
    prefini.read("preferences.ini")
except Exception as e:
    print(f"Error reading preferences.ini: {e}")
    preferenceErrors.append("preferences.ini not found (Might be moved or deleted.)")
    preferenceErrors.append("A new one was created with default values.")
    preferenceErrors.append("(Ignore this if you just installed the player.)")
    preferenceErrors.append("")
    print("Creating new preferences.ini file...")
    # create new blank file
    with open("preferences.ini", 'w') as f:
        pass

    prefini = configparser.ConfigParser()
    prefini["LastUsed"] = {"lastLoaded": "NONE", "lastMic": "NONE", "lastversion": version}
    prefini["Thresholds"] = {"talkThresh": "50", "peakThresh": "90"}
    prefini["Settings"] = {"settingskey": "p", "bgcolor": (0, 255, 0, 255), "antialiasing": 0, "ignorehotkey":"right ctrl", "mutekey": "right shift", "volume": 0.5, "sfxmutekey": f"\"right alt\"", "mirror": "0", "suppression": "0"}
    with open("preferences.ini", "w") as f:
        prefini.write(f)
    print("preferences.ini created with default values.")

# read from each element in preferences.ini and have failsafes for each

# last used version
try:
    lastUsedVersion = prefini["LastUsed"]["lastversion"].strip("\"")
except Exception as e:
    print(f"Error reading last used version from preferences.ini. Setting to {version}...")
    preferenceErrors.append(f"Last used version. (Reset to {version})")
    lastUsedVersion = version

# compare each part of the version number
verCompare = compareVersions(version, lastUsedVersion)
if(verCompare == -1):
    # current version is older
    popup("Preferences file from OLDER version", f"Your preferences file is from an OLDER version of ToonTuber Player ({lastUsedVersion}).\n\nPressing \'OK\" will update the preferences to THIS version ({version}),\nwhich MAY or MAY NOT result in some of your settings getting RESET.\n\nIf you have any custom settings, you may want to\nback up your preferences.ini file before continuing.")
elif(verCompare == 1):
    # current version is newer
    popup("Preferences file from NEWER version", f"Your preferences file is from a NEWER version of ToonTuber Player ({lastUsedVersion}).\n\nPressing \"OK\" will revert this file to THIS version ({version}),\nwhich MAY or MAY NOT result in some of your settings getting RESET.\n\nPlease back up your current preferences.ini file before continuing.")


# last loaded tuber
try:
    lastTuberLoaded = prefini["LastUsed"]["lastLoaded"].strip("\"")
except Exception as e:
    print("Error reading last loaded tuber from preferences.ini. Setting to NONE...")
    preferenceErrors.append("Last loaded Tuber. You'll be prompted to select a new one.")
    lastTuberLoaded = "NONE"

# last used mic
try:
    lastAudioDevice = prefini["LastUsed"]["lastMic"].strip("\"")
except Exception as e:
    print("Error reading last used mic from preferences.ini. Will be reset later...")
    preferenceErrors.append("Last used Microphone. (Will be automatically reset later.)")
    lastAudioDevice = "RESET"

# talk threshold
try:
    talkThreshold = int(prefini["Thresholds"]["talkThresh"])
except Exception as e:
    print("Error reading talk threshold from preferences.ini. Setting to 50...")
    preferenceErrors.append("Talk threshold (Reset to 50)")
    talkThreshold = 50

# peak threshold
try:
    peakThreshold = int(prefini["Thresholds"]["peakThresh"])
except Exception as e:
    print("Error reading peak threshold from preferences.ini. Setting to 90...")
    preferenceErrors.append("Peak threshold (Reset to 90)")
    peakThreshold = 90

# background color
try:
    BGCOLOR = eval(prefini["Settings"]["bgcolor"].strip("\""))
except Exception as e:
    print("Error reading background color from preferences.ini. Setting to green...")
    preferenceErrors.append("Background color (Reset to green)")
    BGCOLOR = GREEN

# smooth pixels
antialiasing = False
try:
    antialiasing = bool(int(prefini["Settings"]["antialiasing"]))
except Exception as e:
    print("Error reading antialiasing from preferences.ini. Setting to False...")
    preferenceErrors.append("Smooth pixels (Reset to No)")

# settings keybind
settingsKeybindName = "p"
try:
    settingsKeybindName = prefini["Settings"]["settingskey"].strip("\"")
except Exception as e:
    print("Error reading keybind from preferences.ini. Setting to \"p\"...")
    preferenceErrors.append("Settings keybind (Reset to \"p\")")
settingsKeybind = pygame.key.key_code(settingsKeybindName)
    
# ignore hotkey
ignoreHotkey = False
ignoreHotkeyBindName = "right ctrl"
try:
    ignoreHotkeyBindName = prefini["Settings"]["ignorehotkey"].strip("\"")
except Exception as e:
    print("Error reading ignorehotkey from preferences.ini. Setting to \"right ctrl\"...")
    preferenceErrors.append("\"Ignore\" hotkey (Reset to \"right ctrl\")")
# print(ignoreHotkeyBindName)

# mute key
muteKeyName = "-"
muted = False
try:
    muteKeyName = prefini["Settings"]["mutekey"].strip("\"")
except Exception as e:
    print("Error reading mutekey from preferences.ini. Setting to \"-\"...")
    preferenceErrors.append("Mute key (Reset to \"-\")")

# sfx mute key
sfxMuteKeyName = "right alt"
try: 
    sfxMuteKeyName = prefini["Settings"]["sfxmutekey"].strip("\"")
except Exception as e:
    print("Error reading sfxmutekey from preferences.ini. Setting to \"right alt\"...")
    preferenceErrors.append("SFX mute key (Reset to \"right alt\")")
sfxMuteKey = pygame.key.key_code(sfxMuteKeyName)

# animation sfx volume
try:
    animationSFXVolume = float(prefini["Settings"]["volume"])
except Exception as e:
    print("Error reading animationSFXVolume from preferences.ini. Setting to 0.5...")
    preferenceErrors.append("Animation SFX volume (Reset to 0.5)")
    animationSFXVolume = 0.5

# mirror setting
try:
    mirror = bool(int(prefini["Settings"]["mirror"]))
except Exception as e:
    print("Error reading mirror from preferences.ini. Setting to False...")
    preferenceErrors.append("Tuber Mirroring (Reset to Off)")

# noise suppression setting
suppression = False
try:
    suppression = bool(int(prefini["Settings"]["suppression"]))
except Exception as e:
    print("Error reading suppression from preferences.ini. Setting to False...")
    preferenceErrors.append("Noise Suppression (Reset to Off)")

# write everything back to the file to ensure no data is lost. 
# also helps with updating older versions of preferences.ini
prefini["LastUsed"] = {"lastLoaded": lastTuberLoaded, "lastmic": f"\"{lastAudioDevice}\"", "lastversion": f"\"{version}\""}
prefini["Thresholds"] = {"talkThresh": talkThreshold, "peakThresh": peakThreshold}
prefini["Settings"] = {"settingskey": f"\"{settingsKeybindName}\"", "bgcolor": BGCOLOR, "antialiasing": int(antialiasing), "ignorehotkey": f"\"{ignoreHotkeyBindName}\"", "mutekey": f"\"{muteKeyName}\"", "volume": animationSFXVolume, "sfxmutekey": f"\"{sfxMuteKeyName}\"", "mirror": f"{'1' if mirror else '0'}", "suppression": f"{'1' if suppression else '0'}"}

with open("preferences.ini", "w") as configfile:
    prefini.write(configfile)

talkThreshText = f"{talkThreshold}"
peakThreshText = f"{peakThreshold}"

debugPrint("preferences.ini read.\nInitializing audio data stuff...")

# audio stuff
rms = 0
micVolume = 0
chunk_size = 256  # number of audio samples per chunk
sample_rate = 44100  # number of samples per second

volRollingAverage = []
volRollingAverageLength = 10

audioDeviceList = {}

audioDevice_options = []

audioDeviceNames = []

deviceList = None
numdevices = 0

def getAudioDevices(initial=False):
    global deviceList, numdevices, audioDeviceList, audioDeviceNames, audio_device_id, audioDeviceText, lastAudioDevice
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
    if(lastAudioDevice not in audioDeviceNames):
        lastAudioDevice = audioDeviceNames[0]
    # debugPrint(f"\n\n\n HERE IS THE LIST OF DETECTED DEVICES: {audioDeviceNames}\n\n\n")

prefini.set("LastUsed", "lastmic", f"\"{lastAudioDevice}\"")
with open("preferences.ini", "w") as configfile:
    prefini.write(configfile)

getAudioDevices(True)

def int16_to_float(audio_data):
    return audio_data.astype(np.float32) / np.iinfo(np.int16).max



def audio_callback(in_data, frame_count, time_info, status):
    global rms, micVolume, rms, chunk_size, sample_rate

    if(muted):
        micVolume = 0
        return (None, pyaudio.paContinue)
    # convert audio data to a numpy array
    audio = np.frombuffer(in_data, dtype=np.int16)

    # convert to a bigger data type before squaring to prevent overflow
    audio = audio.astype(np.int32)

    preNR = audio[:chunk_size]
    postNR = nr.reduce_noise(y=preNR, sr=sample_rate)

    # calculate the root mean square (RMS) amplitude


    scalefactor = 250
    ogVOL = min(scalefactor * (np.sqrt(np.mean(np.square(audio)) + 1e-6)) /32767, 100)
    supVOL = min(scalefactor * (np.sqrt(np.mean(np.square(postNR)) + 1e-6)) / 32767, 100)

    # reduce it to 100 if its greater



    # calculate the root mean square (RMS) amplitude
    # rmsNEW = np.sqrt(np.mean(np.square(np.nan_to_num(audio))) + 1e-6)
    if(not np.isnan(ogVOL)):
        ogVOL = round(ogVOL)
    else:
        ogVOL = 100

    if(not np.isnan(supVOL)):
        supVOL = round(supVOL)
    else:
        supVOL = 100
    
    # print(f"B4: {ogVOL}    NR: {supVOL}")


    # volRollingAverage.append(rms)
    # if(len(volRollingAverage) > volRollingAverageLength):
    #     volRollingAverage.pop(0)
    # avgVol = sum(volRollingAverage) / len(volRollingAverage)


    micVolume = ogVOL if not suppression else supVOL
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
    global latestKeyPressed, lastKeyPressed, keyHeld, currentAnimation, expressionList, cannedAnimationList, currentExpression, queuedExpression, transition, queuedAnimationType, currentAnimationType, changingSettingsKeybind, ignoreHotkey, currentScreen, nonrequiredWeight, typingInTextEntry
    # ignore hotkeys if the user is changing a keybind, or if the user is ignoring hotkeys
    if(changingSettingsKeybind or ignoreHotkey or currentScreen == "loading" or currentScreen == "keybind" or typingInTextEntry):
        return 
    
    # print(hotkeyDictionary)
    if(key in hotkeyDictionary):
        # a hotkey was pressed. check if it needs an existing animation
        # print(f"\nPushed {key}")
        possibleAnims = list(hotkeyDictionary[key])
        debugPrint(f"After pressing {key}, the possible animations are {possibleAnims}\nRemoving the current and queued animations if they're in there...")

        # remove the current animation from the list of possible animations
        if(currentAnimationType == "expression" and currentExpression in possibleAnims):
            possibleAnims.remove(currentExpression)
        elif(currentAnimationType == "canned" and currentExpression in possibleAnims):
            possibleAnims.remove(currentExpression)

        if(queuedAnimationType == "expression" and queuedExpression in possibleAnims):
            possibleAnims.remove(queuedExpression)
        elif(queuedAnimationType == "canned" and queuedExpression in possibleAnims):
            possibleAnims.remove(queuedExpression)
        
        debugPrint(f"After removing the current and queued animations, the possible animations are {possibleAnims}\nRemoving any animations that are blocked by the current animation...")
        
        # remove any animations that are blocked by the current animation
        i = 0
        while True:
            if(i >= len(possibleAnims)):
                break
            anim = possibleAnims[i]
            if(anim in expressionIndex):
                if(not expressionList[expressionIndex[anim]].hasBlockers()):
                    i += 1
                elif currentExpression in expressionList[expressionIndex[anim]].getBlockers():
                    possibleAnims.remove(anim)
                else:
                    i += 1
            elif(anim in cannedAnimationIndex):
                if(not cannedAnimationList[cannedAnimationIndex[anim]].hasBlockers()):
                    i += 1
                elif currentExpression in cannedAnimationList[cannedAnimationIndex[anim]].getBlockers():
                    possibleAnims.remove(anim)
                else:
                    i += 1

        debugPrint(f"After removing blocked animations, the possible animations are {possibleAnims}. Getting only the ones where the current animation is a requirement...")
        
        # get only the animations where the current one is a requirement
        i=0
        while True:
            if(i >= len(possibleAnims)):
                break
            anim = possibleAnims[i]
            if(anim in expressionIndex):
                if(not expressionList[expressionIndex[anim]].hasRequires()):
                    i += 1
                elif currentExpression not in expressionList[expressionIndex[anim]].getRequires() and queuedExpression not in expressionList[expressionIndex[anim]].getRequires():
                    possibleAnims.remove(anim)
                else:
                    i += 1
            elif(anim in cannedAnimationIndex):
                if(not cannedAnimationList[cannedAnimationIndex[anim]].hasRequires()):
                    i += 1
                elif currentExpression not in cannedAnimationList[cannedAnimationIndex[anim]].getRequires() and queuedExpression not in cannedAnimationList[cannedAnimationIndex[anim]].getRequires():
                    possibleAnims.remove(anim)
                else:
                    i += 1


        # if there are no animations left, return
        if(len(possibleAnims) == 0):
            debugPrint("No animations left to choose from. Returning.")
            return
        
         # create a set of weights for the remaining animations. 
         # ones where the current animation is a requirement get a weight of 1, others get a weight of "vars".
         # this way, animations with requirements are more likely to be chosen

        # if you're looking to change the nonrequiredWeight value, it's at the top of the file. has to range from 0 to 1
        requirementWeights = [nonrequiredWeight] * len(possibleAnims)
        for i in range(len(possibleAnims)):
            anim = possibleAnims[i]
            if(anim in expressionIndex):
                if(currentExpression in expressionList[expressionIndex[anim]].getRequires()):
                    requirementWeights[i] = 1
            elif(anim in cannedAnimationIndex):
                if(currentExpression in cannedAnimationList[cannedAnimationIndex[anim]].getRequires()):
                    requirementWeights[i] = 1
                    
        # randomly select an animation from the remaining list
        debugPrint(f"Randomly selecting an animation from the remaining list of {possibleAnims} animations...")
        resultingAnim = random.choices(possibleAnims, requirementWeights)[0]
        debugPrint(f"Resulting animation: {resultingAnim}")


        # for the animation to be queued, it must mee the following:
        # 1. it must be a valid expression
        # 2. the required animation must be playing (or the required animation list is empty)
        # 3. the requested animation must not be playing
        # 4. the requested animation must not be blocked by the current animation

        
        # print(f"Blocked: {isBlocked}")

        if(resultingAnim in expressionIndex ):
            # print(f"Queuing expression {resultingAnim}")
            queuedExpression = resultingAnim
            queuedAnimationType = "expression"
            
        elif(resultingAnim in cannedAnimationIndex ):
            # print(f"Queuing canned animation {resultingAnim}")
            queuedExpression = resultingAnim
            queuedAnimationType = "canned"
        # print()
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
allKeysPressed = []

def keyboard_input_thread():
    global currentScreen, muteKeyName, settingsKeybindName, ignoreHotkeyBindName, changingAnyKeybind, ignoreHotkey, muted, animationSFXMuted, settingsText
    while True:
        event = keyboard.read_event()
        keyIDTuple = (event.name, event.scan_code)
        if event.event_type == "down":
            # add key to list if its not already there
            if(keyIDTuple not in allKeysPressed):
                allKeysPressed.append(keyIDTuple)
            
            if(event.name == ignoreHotkeyBindName):
                ignoreHotkey = not ignoreHotkey
            elif(event.name == muteKeyName):
                muted = not muted
            elif(event.name == sfxMuteKeyName):
                animationSFXMuted = not animationSFXMuted
                settingsText[6].text = f"Animation SFX Vol: {round(animationSFXVolume*100) if not animationSFXMuted else '(MUTED)'}"
            else:
                pushHotKey(event.scan_code)
        elif event.event_type == "up":
            # remove 
            if(keyIDTuple in allKeysPressed):
                allKeysPressed.remove(keyIDTuple)
            releaseHotKey(event.scan_code)
        # clear allKeysPressed if no keys are being pressed 
        # if(keyboard.)

            
keyboard_thread = threading.Thread(target=keyboard_input_thread)
keyboard_thread.daemon = True
keyboard_thread.start()

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

MISSING_IMAGE = pygame.image.load(os.path.join(scriptPath, "assets", "MissingImage.png"))

jsonPath = ""

def load_animation_images(paths):
    # create a list of Pygame images from the selected files
    global jsonPath, currentlyLoadingFile
    images = []
    # loop through each provided path in the provided list
    for file_path in paths:
        singlePath = file_path
        file_path = os.path.join(jsonPath, "frames", file_path)
        # debugPrint(file_path)
        if(os.path.isfile(file_path)):
            extension = os.path.splitext(file_path)[1]
            if(extension == ".png"):
                debugPrint(f"Loading image {singlePath}")
                currentlyLoadingFile = f"Loading image {singlePath}"
                image = pygame.image.load(os.path.join(jsonPath, file_path))
                images.append(image)
            elif(extension == ".gif"):
                debugPrint(f"Loading gif {singlePath}")
                # currentlyLoadingFile = f"Loading gif {singlePath}"
                gif = Image.open(os.path.join(jsonPath, file_path))
                # .mimread(os.path.join(jsonPath, file_path))
                for frame_index in range(gif.n_frames):
                    # convert the image to a Pygame surface
                    # count the number of bytes in frame.tobytes() and print it out
                    currentlyLoadingFile = f"Loading gif {singlePath} frames ({frame_index}/{gif.n_frames})"

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
    return images

def playAnimationSound(soundPath):
    global animationSFXVolume, animationSFXMuted
    debugPrint(f"Playing sound {soundPath}")
    soundPath = os.path.join(jsonPath, "sounds", soundPath)
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

# METHOD TO PLAY AND SWITCH ANIMATIONS
def update_render_thread():
    global currentFrame, framerate, image_timer, locked, transition, queuedExpression, currentExpression, talkThreshold, peakThreshold, micVolume, idleClockCounter, idleTimer, currentAnimationType, queuedAnimationType, idling, timeUntilNextIdle, currentScreen
    while True:
        if(currentScreen == "opening" or currentScreen == "loading" or currentScreen == "keybind"):
            continue
        timeElapsed = fpsClock.tick(framerate) / 1000.0  # Get the time passed since last frame
        image_timer += timeElapsed

        if image_timer > 1 / framerate: # time equivelent to one frame has passed
            currentFrame = currentFrame + 1
            # time to change frame! 
            animationFinished = currentFrame >= len(tuberFrames)
            idlesExist = timeUntilNextIdle != -1
            # load random idle if it's been long enough (and there are idles), and are current;y in an expression
            if(currentAnimationType == "expression" and not idling and get_idle_timer() >= timeUntilNextIdle and idlesExist):
                loadExpression(expressionList[expressionIndex[currentExpression]], "idle")
                idling = True
            # if the idle has finished, return to the main expression
            elif(currentAnimationType == "expression" and idling and animationFinished and idlesExist):
                loadExpression(expressionList[expressionIndex[currentExpression]], "main")
                idling = False
                idle_timer_reset()
            # otherwise, check if we aren't locked in the current animation and if it has finished
            elif(not locked or animationFinished):
                # can change animation. check what kind of animation we need to switch to, if we need to
                if((queuedExpression != currentExpression and queuedExpression != "") or transition != "" or (currentAnimationType == "canned")):
                    debugPrint("animation is finished and new animation is queued.")
                    # animation queued, check to see if its an expression or canned animation
                    if(currentAnimationType == "expression"):
                        # if the queued animation is an expression, load the current one's out transition
                        if(transition == ""):
                            # no transition happening, load out transition
                            if((queuedAnimationType == "expression" and expressionList[expressionIndex[queuedExpression]].isInstant()) or (queuedAnimationType == "canned" and cannedAnimationList[cannedAnimationIndex[queuedExpression]].isInstant())):
                                # if the queued animation is a canned animation and it's not instant, load the canned animation's out transition
                                currentExpression = queuedExpression
                                currentAnimationType = queuedAnimationType
                                queuedExpression = ""
                                queuedAnimationType = ""
                                if(currentAnimationType == "canned"):
                                    loadCanned(cannedAnimationList[cannedAnimationIndex[currentExpression]])
                                elif(currentAnimationType == "expression"):
                                    if(expressionList[expressionIndex[currentExpression]].getTransitionIn().exists()):
                                        transition = "in"
                                        loadExpression(expressionList[expressionIndex[currentExpression]], "in")
                                        if(expressionList[expressionIndex[currentExpression]].getSound() != None):
                                            playAnimationSound(expressionList[expressionIndex[currentExpression]].getSound())
                                    else:
                                        transition = ""
                                        loadExpression(expressionList[expressionIndex[currentExpression]], "main")
                                        if(expressionList[expressionIndex[currentExpression]].getSound() != None):
                                            playAnimationSound(expressionList[expressionIndex[currentExpression]].getSound())
                            else:
                                if(expressionList[expressionIndex[currentExpression]].getTransitionOut().exists()):
                                    transition = "out"
                                    loadExpression(expressionList[expressionIndex[currentExpression]], "out")
                                else:
                                    currentExpression = queuedExpression
                                    currentAnimationType = queuedAnimationType
                                    queuedExpression = ""
                                    queuedAnimationType = ""
                                    if(currentAnimationType == "canned"):
                                        loadCanned(cannedAnimationList[cannedAnimationIndex[currentExpression]])
                                    elif(currentAnimationType == "expression"):
                                        if(expressionList[expressionIndex[currentExpression]].getTransitionIn().exists()):
                                            transition = "in"
                                            loadExpression(expressionList[expressionIndex[currentExpression]], "in")
                                            if(expressionList[expressionIndex[currentExpression]].getSound() != None):
                                                playAnimationSound(expressionList[expressionIndex[currentExpression]].getSound())
                                        else:
                                            transition = ""
                                            loadExpression(expressionList[expressionIndex[currentExpression]], "main")
                                            if(expressionList[expressionIndex[currentExpression]].getSound() != None):
                                                playAnimationSound(expressionList[expressionIndex[currentExpression]].getSound())

                        elif(transition == "out"):
                            # transition out finished, load queued animation
                            currentExpression = queuedExpression
                            currentAnimationType = queuedAnimationType
                            queuedExpression = ""
                            queuedAnimationType = ""
                            if(currentAnimationType == "expression"):
                                # if the queued animation is an expression
                                if(expressionList[expressionIndex[currentExpression]].getTransitionIn().exists()):
                                    transition = "in"
                                    loadExpression(expressionList[expressionIndex[currentExpression]], "in")
                                    debugPrint(expressionList[expressionIndex[currentExpression]].getSound())
                                    if(expressionList[expressionIndex[currentExpression]].getSound() != None):
                                        playAnimationSound(expressionList[expressionIndex[currentExpression]].getSound())
                                else:
                                    transition = ""
                                    loadExpression(expressionList[expressionIndex[currentExpression]], "main")
                                    debugPrint(expressionList[expressionIndex[currentExpression]].getSound())
                                    if(expressionList[expressionIndex[currentExpression]].getSound() != None):
                                        playAnimationSound(expressionList[expressionIndex[currentExpression]].getSound())
                            elif(currentAnimationType == "canned"):
                                # if the queued animation is a canned animation
                                transition = ""
                                loadCanned(cannedAnimationList[cannedAnimationIndex[currentExpression]])
                        elif(transition == "in"):
                            # transition in finished, load main
                            transition = ""
                            loadExpression(expressionList[expressionIndex[currentExpression]], "main")
                    # queued expression and transitions
                    elif(currentAnimationType == "canned"):
                        debugPrint("Canned animation completed. Loading resulting expression...")
                        # if we're in a canned animation, and it's finished
                        resultingExpression = cannedAnimationList[cannedAnimationIndex[currentExpression]].getResult()

                        if(resultingExpression in expressionIndex):
                            loadExpression(expressionList[expressionIndex[resultingExpression]], "main")
                        elif(resultingExpression in cannedAnimationIndex):
                            loadCanned(cannedAnimationList[cannedAnimationIndex[resultingExpression]])
                        else:
                            # no expression or canned animation found, try to load the queued animation
                            if(queuedAnimationType == "expression"):
                                currentExpression = queuedExpression
                                currentAnimationType = queuedAnimationType
                                queuedExpression = ""
                                queuedAnimationType = ""
                                transition = "in"
                                loadExpression(expressionList[expressionIndex[currentExpression]], "in")
                            elif(queuedAnimationType == "canned"):
                                currentExpression = queuedExpression
                                currentAnimationType = queuedAnimationType
                                queuedExpression = ""
                                queuedAnimationType = ""
                                loadCanned(cannedAnimationList[cannedAnimationIndex[currentExpression]])
                # peak and talk\
                elif(currentAnimationType == "expression"):
                    if(micVolume >= peakThreshold 
                        and expressionList[expressionIndex[currentExpression]].getPeak().exists() 
                        and currentAnimation is not expressionList[expressionIndex[currentExpression]].getPeak()):
                        # peak animation is set, and we're not locked
                        loadExpression(expressionList[expressionIndex[currentExpression]], "peak")
                    elif(micVolume >= talkThreshold 
                        and expressionList[expressionIndex[currentExpression]].getTalk().exists() 
                        and currentAnimation is not expressionList[expressionIndex[currentExpression]].getTalk() 
                        and currentAnimation is not expressionList[expressionIndex[currentExpression]].getPeak()):
                        # talk animation is set, and we're not locked
                        loadExpression(expressionList[expressionIndex[currentExpression]], "talk")
                    elif( micVolume < talkThreshold 
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

def openTuber():
    print("Open Tuber")
    loadTuberThread(None)

def createNewTuber():
    global currentScreen
    print("New Tuber")

changingSettingsKeybind = False
changingHotKeybind = False
changingMuteKeybind = False
changingSFXMuteKeybind = False

def openKeybindScreen():
    global currentScreen
    currentScreen = "keybind"
    enableHotkeyButtons()
    disableHotkeyButtons()

def leaveHotkeyScreen():
    global currentScreen, changingSettingsKeybind, changingHotKeybind, changingMuteKeybind, changingSFXMuteKeybind
    currentScreen = "settings"
    changingSettingsKeybind = False
    changingHotKeybind = False
    changingMuteKeybind = False
    changingSFXMuteKeybind = False
    disableHotkeyButtons()
    enableSettingsButtons()

def beginKeybindChange():
    global changingSettingsKeybind
    changingSettingsKeybind = True

def beginHotKeybindChange():
    global changingHotKeybind
    changingHotKeybind = True

def beginMuteKeybindChange():
    global changingMuteKeybind
    changingMuteKeybind = True

def beginSFXMuteKeybindChange():
    global changingSFXMuteKeybind
    changingSFXMuteKeybind = True

colorPickerGUI = None

def changeBGColor():
    global BGCOLOR, colorPickerGUI
    colorPickerGUI = pygame_gui.windows.UIColourPickerDialog(pygame.Rect(160,50,420,400), settings_UImanager, window_title="Choose Background Color", initial_colour=pygame.Color(BGCOLOR[0], BGCOLOR[1], BGCOLOR[2]))
    changeBGColorButton.disable()

def toggleAntiAliasing():
    global antialiasing, smoothPixelsButton, prefini
    antialiasing = not antialiasing
    smoothPixelsButton.set_text(f"Smooth Pixels ({'Yes' if antialiasing else 'No'})")
    prefini.set("Settings", "antialiasing", f"{'1' if antialiasing else '0'}")
    with open("preferences.ini", "w") as f:
        prefini.write(f)

def toggleMirroring():
    global mirror, mirrorButton, prefini
    mirror = not mirror
    mirrorButton.set_text(f"Mirror Tuber ({'ON' if mirror else 'Off'})")
    prefini.set("Settings", "mirror", f"{'1' if mirror else '0'}")
    with open("preferences.ini", "w") as f: 
        prefini.write(f)

def toggleSuppression():
    global suppression, prefini, noiseSuppressionButton
    suppression = not suppression
    noiseSuppressionButton.set_text(f"Noise Suppression ({'ON' if suppression else 'Off'})")
    prefini.set("Settings", "suppression", f"{'1' if suppression else '0'}")
    with open("preferences.ini", "w") as f:
        prefini.write(f)

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
        print(f"ExpressionSet \"{expressionSet.getName()}\" does not have \"{animation}\" animation.")
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
    global currentAnimation, tuberFrames, framerate, fpsClock, idleClockCounter, currentTotalFrames, locked, currentFrame, currentExpression, idling, randIdleMin, randIdleMax, timeUntilNextIdle, currentAnimationType, newSoundPath
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
    locked = True
    fpsClock = pygame.time.Clock()
    currentExpression = cannedAnimation.getName()
    if(cannedAnimation.getSound() != None):
        playAnimationSound(cannedAnimation.getSound())
    
load_thread = None

def selectJSON():
    global jsonPath
    debugPrint("Prompting for new JSON file...")
    root = tk.Tk()
    root.withdraw()

    file_path = filedialog.askopenfilename(
        filetypes=[("JSON files", "*.json")],
        title="Select a JSON file",
    )

    root.destroy()  # close the root window

    if(file_path is None or file_path == ""):
        print("No file selected.")
        return

    (jsonPath, filename) = os.path.split(file_path)

    return file_path

totalLoadStages = 1
currentLoadProgress = 0
progressText = "Loading JSON file..."
currentlyLoadingFile = "Reading "

def loadTuber(path):
    global currentScreen, tuberName, creator, created, modified, randomDuplicateReduction, expressionList, cannedAnimationList, tuberFrames, expressionIndex, cannedAnimationIndex, currentAnimation, currentFrame, framerate, fpsClock, idleClockCounter, currentTotalFrames, locked, randIdleMax, randIdleMin, settingsText, screen, load_thread, totalLoadStages, currentLoadProgress, progressText, hotkeyDictionary, idleChoiceIndex, jsonPath
    if(path is None or path == ""):
        print("No file selected.")
        return

    (jsonPath, filename) = os.path.split(path)
    currentScreen = "loading"
    with open(path) as json_file:
        data = json.load(json_file)

    # reset all of the tuber variables
    tuberName = ""
    creator = ""
    created = ""
    modified = ""
    randomDuplicateReduction = 0
    expressionList = []
    cannedAnimationList = []
    hotkeyDictionary = {}
    expressionIndex = {}
    cannedAnimationIndex = {}
    idleChoiceIndex = -1

    # check the version this tuber is made for
    tuberName = data["name"]
    tuberVersion = data["player_version"]
    comp = compareVersions(tuberVersion, version)

    if(comp != 0):
        popup("Tuber Version Warning", f"The Toontuber \"{tuberName}\" is intended for version {tuberVersion} of ToonTuber Player,\nbut you are running version {version}. \n\nThis may result in unexpected behavior and/or crashing.\nConsult {version}'s README for information on how that version's JSONs should look.\n\nPress \"OK\" to continue loading the ToonTuber anyway.")


    # save last loaded tuber data
    prefini.set("LastUsed", "lastloaded", f"\"{path}\"")
    with open("preferences.ini", "w") as configfile:
        prefini.write(configfile)

    debugPrint(f"Loading {data['name']}...")
    # print(data)
    # print("Loading tuber: " + data["name"])

    # loading screen info colelction
    expressionCount = len(data["expressions"])
    cannedCount = len(data["canned_anims"])
    totalLoadStages = expressionCount + cannedCount + 1
    currentLoadProgress = 0
    progressText = "Loading initial data..."

    # load the tuber's data
    creator = data["creator"]
    created = data["created"]
    modified = data["last_modified"]
    randomDuplicateReduction = data["random_duplicate_reduction"]
    # an RDR of 0 means it will NEVER try to stop the same idle from playing multiple times in a row, 
    # 1 means it will ALWAYS prevent repetition
    # decimals are allowed

    name1 = ""
    debugPrint(f"Loading {expressionCount} expressions and {cannedCount} canned animations...")
    expDone = 0
    for expressionData in data["expressions"]:
        currentLoadProgress += 1
        expDone += 1
        progressText = f"Loading expression \"{expressionData['name']}\" ({expDone}/{expressionCount})..."
        debugPrint(progressText)
        
        if name1 == "":
            name1 = expressionData["name"]
        # print("Loading expression: " + expressionData["name"])
        # expression set requires a main animation, an idle set, and loop animations

        # main animation        REQUIRED
        main = Animation(expressionData["anims"]["Main"]["frames"], expressionData["anims"]["Main"]["fps"], expressionData["anims"]["Main"]["locking"])
        debugPrint("main animation loaded. loading idles...")

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
        debugPrint("idles loaded. loading talking...")

        # talking
        if(not expressionData["anims"]["Talk"]):
            # print("No talking animation found.")
            talking = Animation(None, None, None)
        else:
            talking = Animation(expressionData["anims"]["Talk"]["frames"], expressionData["anims"]["Talk"]["fps"], expressionData["anims"]["Talk"]["locking"])

        debugPrint("talking loaded. loading peak...")
        # peak
        if(not expressionData["anims"]["Peak"]):
            # print("No peak animation found.")
            peak = Animation(None, None, None)
        else:
            peak = Animation(expressionData["anims"]["Peak"]["frames"], expressionData["anims"]["Peak"]["fps"], expressionData["anims"]["Peak"]["locking"])

        debugPrint("peak loaded. loading transition in...")

        # transition in
        if(not expressionData["anims"]["TransitionIN"]):
            # print("No transition in animation found.")
            transitionIn = Animation(None, None, None)
        else:
            transitionIn = Animation(expressionData["anims"]["TransitionIN"]["frames"], expressionData["anims"]["TransitionIN"]["fps"], True)

        debugPrint("transition in loaded. loading transition out...")

        # transition out
        if(not expressionData["anims"]["TransitionOUT"]):
            # print("No transition out animation found.")
            transitionOut = Animation(None, None, None)
        else:
            transitionOut = Animation(expressionData["anims"]["TransitionOUT"]["frames"], expressionData["anims"]["TransitionOUT"]["fps"], True)

        debugPrint("transition out loaded. creating expression set...")
        # create ExpressionSet
        expressionList.append(ExpressionSet(expressionData["name"], main, idles, talking, peak, transitionIn, transitionOut, expressionData["requires"], expressionData["blockers"], expressionData['sound'], expressionData['instant'], expressionData["hotkeys"]))
        expressionIndex[expressionData["name"]] = len(expressionList) - 1

        debugPrint("expression set created. adding to hotkey dictionary...")

        for key in expressionData["hotkeys"]:
            # add to hotkey dictionary
            if(key is None):
                continue
            if(key not in hotkeyDictionary):
                hotkeyDictionary[key] = [expressionData["name"]]
            else:
                hotkeyDictionary[key].append(expressionData["name"])

        # print(expressionDictionary)
    debugPrint("all expressions loaded. loading canned animations...")
    canDone = 0
    for cannedAnimationData in data["canned_anims"]:
        currentLoadProgress += 1
        canDone += 1
        progressText = f"Loading canned animation \"{cannedAnimationData['name']}\" ({canDone}/{cannedCount})..."
        debugPrint(progressText)

        # name, animation, hotkey, requires, result
        cannedAnimationList.append(CannedAnimation(cannedAnimationData["name"], Animation(cannedAnimationData["anim"]["frames"], cannedAnimationData["anim"]["fps"], True), cannedAnimationData["hotkeys"], cannedAnimationData["requires"], cannedAnimationData["blockers"], cannedAnimationData["sound"].replace('\\', '/') if cannedAnimationData["sound"] != None else None, cannedAnimationData["instant"], cannedAnimationData["result"]))
        cannedAnimationIndex[cannedAnimationData["name"]] = len(cannedAnimationList) - 1
        debugPrint("canned animation loaded. adding to hotkey dictionary...")

        for key in cannedAnimationData["hotkeys"]:
            if(key not in hotkeyDictionary):
                hotkeyDictionary[key] = [cannedAnimationData["name"]]
            else:
                hotkeyDictionary[key].append(cannedAnimationData["name"])
    
    debugPrint("all canned animations loaded. loading expressions...")
    # print(hotkeyDictionary)
    loadExpression(expressionList[expressionIndex[name1]], "main")
    # print(f"Path = {path}")


    settingsText[2].setText(f"Current Tuber: {tuberName} by {creator}")
    currentScreen = "tuber"
    print("Loaded Tuber: " + tuberName)
    return

#create thread for loadTuber
def loadTuberThread(path=None):
    if(path is None):
        path = selectJSON()
    load_thread = threading.Thread(target=loadTuber, args=(path,))
    load_thread.daemon = True
    load_thread.start()

def toggleDebug():
    global settingsText, debugMode
    if(debugMode):
        debugPrint("=== Debug mode disabled. ===")
    debugMode = not debugMode
    if(debugMode):
        debugPrint("=== Debug mode ENABLED. ===")
    settingsText[7].setText(f"{'DEBUG MODE ENABLED' if debugMode else 'Debug Mode disabled'}")
    

# Define the clickable text options
settingsText = [
    ClickableText(f"Talk Threshold: ", (100, height-50), UniFontSmaller, WHITE, None),
    ClickableText(f"Peak Threshold: ", (100, height-100), UniFontSmaller, WHITE, None),
    ClickableText(f"Current Tuber: {tuberName} by {creator}", (0, 0), UniFontBigger, WHITE, None),
    ClickableText(f"ToonTuber Player {version}", (0, 40), UniFontSmaller, WHITE, None),
    ClickableText("program by JNS", (0, 60), UniFontSmaller, WHITE, None),
    ClickableText("original idea by ScottFalco", (0, 80), UniFontSmaller, WHITE, None),
    ClickableText(f"Animation SFX Vol: {round(animationSFXVolume*100) if not animationSFXMuted else '(MUTED)'}", (0, height-175), UniFontSmaller, WHITE, None),
    ClickableText(f"{'DEBUG MODE ENABLED' if debugMode else 'Debug Mode disabled'}", (0, 100), UniFontSmaller, WHITE, toggleDebug),
]

opening_options = [
    ClickableText("New Tuber", (width/3, 75), UniFont, WHITE, createNewTuber),
    ClickableText("Load Tuber", (width/3, 125), UniFont, WHITE, openTuber)
]

debugPrint("Tuber loading functions created.\nSetting up final GUI elements and functions...")

loadToonTuberButton = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((0, 125), (200, 50)),
                                             text='Load ToonTuber',
                                             manager=settings_UImanager)

changeBGColorButton = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((0, 175), (225, 50)),
                                                text='Change Background Color',
                                                manager=settings_UImanager)

smoothPixelsButton = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((0, 225), (200, 50)),
                                                text=f"Smooth Pixels ({'Yes' if antialiasing else 'No'})",
                                                manager=settings_UImanager)

mirrorButton = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((0, 275), (200, 50)),
                                                text=f"Mirror Tuber ({'ON' if mirror else 'Off'})",
                                                manager=settings_UImanager)


changeKeybindButton = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((0, 325), (200, 50)),
                                                   text='Keybind Settings',
                                                   manager=settings_UImanager)

noiseSuppressionButton = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((200, height-160), (210, 40)),
                                                   text=f"Noise Suppression ({'On' if suppression else 'Off'})",
                                                   manager=settings_UImanager)

# debugPrint(f"\n\n\n AUDIO DROPDOWN BEING CREATED NOW (using this {audioDeviceNames}\n also this as the last device {lastAudioDevice}).\n\n\n")

dropdownPos = pygame.Rect((0, 375), (325, 50))
audioDeviceDropdown = pygame_gui.elements.UIDropDownMenu(options_list=audioDeviceNames,
                                                        starting_option=lastAudioDevice,
                                                        relative_rect=dropdownPos,
                                                        manager=settings_UImanager)


volumeSlider = pygame_gui.elements.UIHorizontalSlider(relative_rect=pygame.Rect((0, height - 150), (150, 25)),
                                                                          start_value=animationSFXVolume,
                                                                          value_range=(0, 1),
                                                                          manager=settings_UImanager)


# openEditorButton = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((0, 425), (200, 50)),
#                                              text='Open Editor',
#                                              manager=settings_UImanager)


changeSettingsKeybindButton = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((0, 50), (400, 50)),
                                                text=f'Settings Keybind (\"{settingsKeybindName}\")',
                                                manager=keybind_UImanager)

changeHotkeyButton = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((0, 100), (400, 50)),
                                                text=f'Hotkey Ignore Keybind (\"{ignoreHotkeyBindName}\")',
                                                manager=keybind_UImanager)

changeMuteKeybindButton = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((0, 150), (400, 50)),
                                                text=f'Mute Keybind (\"{muteKeyName}\")',
                                                manager=keybind_UImanager)

sfxMuteKeybindButton = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((0, 200), (400, 50)),
                                                text=f'Animation SFX Mute Keybind (\"{sfxMuteKeyName}\")',
                                                manager=keybind_UImanager)

leaveHotkeyButton = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((0, height-100), (200, 50)),
                                                text='Back',
                                                manager=keybind_UImanager)


settingsButtonsEnabled = True
hotkeyButtonsEnabled = True

def enableSettingsButtons():
    global loadToonTuberButton, changeBGColorButton, smoothPixelsButton, changeKeybindButton, audioDeviceDropdown, settingsButtonsEnabled, volumeSlider, mirrorButton, noiseSuppressionButton
    loadToonTuberButton.enable()
    changeBGColorButton.enable()
    smoothPixelsButton.enable()
    changeKeybindButton.enable()
    audioDeviceDropdown.enable()
    volumeSlider.enable()
    mirrorButton.enable()
    noiseSuppressionButton.enable()
    settingsButtonsEnabled = True

def disableSettingsButtons():
    global loadToonTuberButton, changeBGColorButton, smoothPixelsButton, changeKeybindButton, audioDeviceDropdown, settingsButtonsEnabled, volumeSlider, mirrorButton, noiseSuppressionButton
    loadToonTuberButton.disable()
    changeBGColorButton.disable()
    smoothPixelsButton.disable()
    changeKeybindButton.disable()
    audioDeviceDropdown.disable()
    volumeSlider.disable()
    mirrorButton.disable()
    noiseSuppressionButton.disable()
    settingsButtonsEnabled = False

def enableHotkeyButtons():
    global changeSettingsKeybindButton, changeHotkeyButton, changeMuteKeybindButton, hotkeyButtonsEnabled, leaveHotkeyButton, sfxMuteKeybindButton
    changeSettingsKeybindButton.enable()
    changeHotkeyButton.enable()
    changeMuteKeybindButton.enable()
    leaveHotkeyButton.enable()
    sfxMuteKeybindButton.enable()
    hotkeyButtonsEnabled = True

def disableHotkeyButtons():
    global changeSettingsKeybindButton, changeHotkeyButton, changeMuteKeybindButton, hotkeyButtonsEnabled, leaveHotkeyButton, sfxMuteKeybindButton
    changeSettingsKeybindButton.disable()
    changeHotkeyButton.disable()
    changeMuteKeybindButton.disable()
    leaveHotkeyButton.disable()
    sfxMuteKeybindButton.disable()
    hotkeyButtonsEnabled = False

talk_textEntry = pygame_gui.elements.UITextEntryLine(
    pygame.Rect((250, height-55), (50, 25)),
    manager=settings_UImanager
)
peak_textEntry = pygame_gui.elements.UITextEntryLine(
    pygame.Rect((250, height-105), (50, 25)),
    manager=settings_UImanager
)

talk_textEntry.set_allowed_characters('numbers')
talk_textEntry.set_text(str(talkThreshold))

peak_textEntry.set_allowed_characters('numbers')
peak_textEntry.set_text(str(peakThreshold))

# make variable to check if the user is typing in the text entry
typingInTextEntry = False

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
mic_feedback = pygame.image.load(os.path.join(scriptPath, "assets", "micLevel.png")).convert_alpha()
mic_range = pygame.image.load(os.path.join(scriptPath, "assets", "micRange.png")).convert_alpha()

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
talkThresholdSprite = pygame.image.load(os.path.join(scriptPath, "assets", "ThresholdArrow.png")).convert_alpha()
peakThresholdSprite = pygame.image.load(os.path.join(scriptPath, "assets", "ThresholdArrow.png")).convert_alpha()

talkThreshPos = 0
peakThreshPos = 0

# create sprite for mic mute
micMuteSprite = pygame.image.load(os.path.join(scriptPath, "assets", "micmuted.png")).convert_alpha()

# scale sprite to fit height of mic meter
micMuteSprite = pygame.transform.smoothscale(micMuteSprite, (mic_newWidth, mic_newHeight))

# no need to scale the threshold arrows, they are already the correct size. prepare the sprites for drawing later

debugPrint("Mic meter sprites created.\nBeginning audio and render threads...")

# begin threads
render_thread = threading.Thread(target=update_render_thread)
render_thread.daemon = True

debugPrint("Audio and render threads started.\nBeginning main Pygame loop...")

# load the tuber from the preferences file if it exists

newAudioDevice = ""

disableHotkeyButtons()
disableSettingsButtons()

if(preferenceErrors != []):
        currentScreen = "preferror"

errortexts = [
    ClickableText("The follwing errors occurred when loading preferences:", (25, 25), UniFont, WHITE, None),
]
i = 0
for error in preferenceErrors:
    errortexts.append(ClickableText(error, (25, 75 + (i*25)), UniFontSmaller, WHITE, None))
    i += 1
errortexts.append(ClickableText("Press any key or click to continue.", (25, 100 + (i*25)), UniFont, WHITE, None))

# Main Pygame loop
running = True
while running:
    if(currentScreen == "opening" and os.path.exists(lastTuberLoaded)):
        loadTuberThread(lastTuberLoaded)
    if(not updateFrameRunning and (currentScreen != "opening" and currentScreen != "loading" and currentScreen != "preferror")):
        updateFrameRunning = True
        render_thread.start()
        idleTimer_thread.start()
        
    # Measure the time between frames and limit the FPS to 60
    delta_time = clock.tick(60) / 1000.0
    talkNotBlank = talk_textEntry.get_text() != "" 
    peakNotBlank = peak_textEntry.get_text() != ""

    typingInTextEntry = talk_textEntry.is_focused or peak_textEntry.is_focused
 
    changingAnyKeybind = changingSettingsKeybind or changingHotKeybind or changingMuteKeybind or changingSFXMuteKeybind

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN and (event.key == settingsKeybind and not changingAnyKeybind) and (currentScreen == "tuber" or currentScreen == "settings"):
            # print("toggling settings")
            currentScreen = "tuber" if currentScreen == "settings" else "settings"
        elif event.type == pygame.KEYDOWN and currentScreen == "keybind":
            # print("keybind pressed on keybind screen")
            if(changingSettingsKeybind):
                # print(event.key)
                settingsKeybind = event.key
                settingsKeybindName = pygame.key.name(event.key)
                # print("keybind changed to " + settingsKeybindName)

                changeSettingsKeybindButton.text = f'Settings Keybind (\"{settingsKeybindName}\")'
                changeSettingsKeybindButton.rebuild()

                prefini.set("Settings", "settingskey", f"\"{settingsKeybindName}\"" )
                with open("preferences.ini", "w") as configfile:
                    prefini.write(configfile)
                changingSettingsKeybind = False

            elif(changingHotKeybind):
                # print(event.key)
                ignoreHotkeyBindName = pygame.key.name(event.key)
                # print("keybind changed to " + hotKeybindName)

                changeHotkeyButton.text = f'HotkeyIgnore Keybind (\"{ignoreHotkeyBindName}\")'
                changeHotkeyButton.rebuild()

                prefini.set("Settings", "ignorehotkey", f"\"{ignoreHotkeyBindName}\"" )
                with open("preferences.ini", "w") as configfile:
                    prefini.write(configfile)
                changingHotKeybind = False
            # print("key pressed and settings is active")        
            elif(changingMuteKeybind):
                # print(event.key)
                muteKeyName = pygame.key.name(event.key)
                # print("keybind changed to " + muteKeyName)

                changeMuteKeybindButton.text = f'Mute Keybind (\"{muteKeyName}\")'
                changeMuteKeybindButton.rebuild()

                prefini.set("Settings", "mutekey", f"\"{muteKeyName}\"" )
                with open("preferences.ini", "w") as configfile:
                    prefini.write(configfile)
                changingMuteKeybind = False
            elif(changingSFXMuteKeybind):
                sfxMuteKeyName = pygame.key.name(event.key)

                sfxMuteKeybindButton.text = f'Animation SFX Mute Keybind (\"{sfxMuteKeyName}\")'
                sfxMuteKeybindButton.rebuild()

                prefini.set("Settings", "sfxmutekey", f"\"{sfxMuteKeyName}\"" )
                with open("preferences.ini", "w") as configfile:
                    prefini.write(configfile)
                changingSFXMuteKeybind = False

        elif (event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN) and currentScreen == "preferror":
            # if last tuber loaded couldnt be found, prompt user to select json
            if(not os.path.exists(lastTuberLoaded)):
                # print("last tuber loaded not found")
                # print("prompting user to select tuber json")
                # print("current dir: " + os.getcwd())
                tuberJson = filedialog.askopenfilename(initialdir = os.getcwd(),title = "Select Tuber JSON",filetypes = (("JSON files","*.json"),("all files","*.*")))
                # print("tuber json selected: " + tuberJson)
                if(tuberJson != ""):
                    loadTuberThread(tuberJson)
                    currentScreen = "loading"
            else:
                currentScreen = "opening"

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
                for option in settingsText:
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
            # debugPrint(f"\n\n\n ABOUT TO UPDATE THE MENU (using this {audioDeviceNames}).\n\n\n")
            audioDeviceDropdown.options_list = audioDeviceNames
            audioDeviceDropdown.kill()
            audioDeviceDropdown = pygame_gui.elements.UIDropDownMenu(options_list=audioDeviceNames,
                                                                    starting_option=lastAudioDevice,
                                                                    relative_rect=dropdownPos,
                                                                    manager=settings_UImanager)
            
        elif event.type == pygame_gui.UI_HORIZONTAL_SLIDER_MOVED:
            animationSFXVolume = volumeSlider.get_current_value()
            settingsText[6].text = f"Animation SFX Vol: {round(animationSFXVolume*100) if not animationSFXMuted else '(MUTED)'}"
            prefini.set("Settings", "volume", str(animationSFXVolume))
            with open("preferences.ini", "w") as ini:
                prefini.write(ini)

        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == loadToonTuberButton:
                loadTuberThread(None)
            # elif(event.ui_element == openEditorButton):
            #     openEditor()
            elif(event.ui_element == changeSettingsKeybindButton):
                beginKeybindChange()
            elif(event.ui_element == changeBGColorButton):
                changeBGColor()
            elif(event.ui_element == smoothPixelsButton):
                toggleAntiAliasing()
            elif(event.ui_element == changeHotkeyButton):
                beginHotKeybindChange()
            elif(event.ui_element == changeMuteKeybindButton):
                beginMuteKeybindChange()
            elif(event.ui_element == sfxMuteKeybindButton):
                beginSFXMuteKeybindChange()
            elif(event.ui_element == changeKeybindButton):
                openKeybindScreen()
            elif(event.ui_element == leaveHotkeyButton):
                leaveHotkeyScreen()
            elif(event.ui_element == mirrorButton):
                toggleMirroring()
            elif(event.ui_element == noiseSuppressionButton):
                toggleSuppression()


        settings_UImanager.process_events(event)
        keybind_UImanager.process_events(event)
    settings_UImanager.update(delta_time)
    keybind_UImanager.update(delta_time)

    if(audioDeviceDropdown.selected_option != lastAudioDevice):
        # get the ID of the selected option in the audio device list
        # debugPrint(f"\n\n\n UPDATING AUDIO DEVICE (using this {audioDeviceNames}).\n\n\n")
        newAudioDevice = audioDeviceDropdown.selected_option
        lastAudioDevice = newAudioDevice
        prefini.set("LastUsed", "lastmic", f"\"{lastAudioDevice}\"")
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

        if(mirror):
            currentImage = pygame.transform.flip(currentImage, True, False)
        
        render = currentImage.convert_alpha()
        # scale tuber image to fill screen
        if(antialiasing):
            render = pygame.transform.smoothscale(render, (width, height))
        else:
            render = pygame.transform.scale(render, (width, height))
        screen.blit(render, tuber_rect)

    # if on the opening screen, prompt user if they want to open an existing tuber or make a new one
    if currentScreen == "opening":
        if(settingsButtonsEnabled or hotkeyButtonsEnabled):
            disableSettingsButtons()
            disableHotkeyButtons()
        # print("opening screen")
        darken_screen()
        draw_text_options(opening_options)
        # if user clicks on "Open ToonTuber", open the file explorer and allow them to select a tuber
        # if user clicks on "New ToonTuber", open the editor

    elif currentScreen == "settings":
        if(not settingsButtonsEnabled):
            enableSettingsButtons()
        if(hotkeyButtonsEnabled):
            disableHotkeyButtons()
        darken_screen()
        draw_text_options(settingsText)

        # Display the FPS counter in the bottom right corner
        display_fps("program FPS: ",clock, 0)
        display_fps("anim FPS: ", fpsClock, 50)
        draw_text_options([ClickableText(f"Ignoring Hotkeys: {'ON' if ignoreHotkey else 'OFF'}", (width-300, height-150), UniFont, WHITE, None)])


        # these values assume that the top left corner of the sprite is 0,0
        # therefore, the bottom right of the sprite is the width and height
        
        micFill_clipHeight = round((mic_feedback.get_height() * (micVolume/100)))
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

        # draw mic muted sprite over the mic fill sprite if the mic is muted
        if(muted):
            screen.blit(micMuteSprite, (0, height - micMuteSprite.get_height()))

        settings_UImanager.draw_ui(screen)

    elif currentScreen == "loading":
        darken_screen()
        if(settingsButtonsEnabled or hotkeyButtonsEnabled):
            disableSettingsButtons()
            disableHotkeyButtons()
        # draw full dark progress bar
        baseBar = pygame.Rect(15, 155, width-22, 52)

        # draw progress bar
        percent = (currentLoadProgress / totalLoadStages)
        # range is 0 to width-28
        loadLen = (width-28) * percent
        loadBar = pygame.Rect(20, 160, loadLen, 42)
        # draw bars to screen
        pygame.draw.rect(screen, BLACK, baseBar)
        pygame.draw.rect(screen, WHITE, loadBar)

        # draw text in center
        draw_text_options([ClickableText("Loading tuber, please wait...", (50, 50), UniFont, WHITE, None),
                           ClickableText(progressText, (50, 100), UniFont, WHITE, None),
                           ClickableText(currentlyLoadingFile, (50, 250), UniFont, WHITE, None)])
        
    elif currentScreen == "keybind":
        darken_screen()
        if(not hotkeyButtonsEnabled):
            enableHotkeyButtons()
        if(settingsButtonsEnabled):
            disableSettingsButtons()
        draw_text_options([ClickableText("Change player keybind", (10, 10), UniFont, WHITE, None), 
                           ClickableText("Key IDs:", (10, 260), UniFont, WHITE, None)])
        
        # print out the keys and their IDs below the "key id" text
        if(allKeysPressed is not None):
            keyIDTextHeight = 300
            txtPrint = []
            for keyTuple in allKeysPressed:
                key, id = keyTuple
                txtPrint.append(ClickableText(f"Key \"{key}\" has an ID of {id}", (10, keyIDTextHeight), UniFont, WHITE, None))
                keyIDTextHeight += 25
            draw_text_options(txtPrint)


        changingTxt = ""
        if(changingSettingsKeybind):
            changingTxt = "Press a key to change \"SETTINGS\" keybind"
        elif(changingHotKeybind):
            changingTxt = "Press a key to change \"HOTKEY IGNORE\" keybind"
        elif(changingMuteKeybind):
            changingTxt = "Press a key to change \"MIC MUTE\" keybind"
        elif(changingSFXMuteKeybind):
            changingTxt = "Press a key to change \"SFX MUTE\" keybind"

        draw_text_options([ClickableText(changingTxt, (0, height-200), UniFont, WHITE, None)])

        keybind_UImanager.draw_ui(screen)

    elif(currentScreen == "preferror"):
        darken_screen()
        draw_text_options(errortexts)
        

    # Update the Pygame window
    pygame.display.flip()

# Quit Pygame
pygame.quit()

stream.stop_stream()
stream.close()
pa.terminate()
# end all threads
